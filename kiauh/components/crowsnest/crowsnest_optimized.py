# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
"""
优化的 Crowsnest 安装模块
根据实测安装文档优化，解决常见的依赖和 repo 问题
"""
from __future__ import annotations

import re
from pathlib import Path
from subprocess import CalledProcessError, run, PIPE, DEVNULL
from typing import List

from components.crowsnest import (
    CROWSNEST_DIR,
    CROWSNEST_REPO,
)
from components.klipper.klipper import Klipper
from core.logger import DialogType, Logger
from utils.git_utils import git_clone_wrapper
from utils.input_utils import get_confirm
from utils.instance_utils import get_instances


# Crowsnest 必需的系统依赖
CROWSNEST_REQUIRED_PACKAGES = [
    "make",
    "crudini",
    "libbsd-dev",
    "libevent-core-2.1-7",
    "libevent-dev",
    "libevent-extra-2.1-7",
    "libevent-openssl-2.1-7",
    "libevent-pthreads-2.1-7",
    "libmd-dev",
    "python3-iniparse",
    "v4l-utils",
]


def check_apt_sources_validity() -> bool:
    """
    检查 apt sources 配置是否有效
    :return: True if valid, False if needs fixing
    """
    Logger.print_status("Checking apt sources configuration ...")

    try:
        result = run(
            ["sudo", "apt-get", "update"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # 检查是否有 repo 错误
        error_patterns = [
            r"does not have a Release file",
            r"There is a problem with your apt sources",
            r"Failed to fetch",
            r"Err:\d+",
        ]

        has_errors = any(
            re.search(pattern, result.stderr, re.IGNORECASE)
            for pattern in error_patterns
        )

        if has_errors:
            Logger.print_warn("Detected apt sources issues!")
            return False

        Logger.print_ok("Apt sources configuration is valid.")
        return True

    except Exception as e:
        Logger.print_error(f"Error checking apt sources: {e}")
        return False


def fix_apt_sources_interactive() -> bool:
    """
    交互式修复 apt sources 配置
    :return: True if user wants to continue, False to abort
    """
    Logger.print_dialog(
        DialogType.WARNING,
        [
            "Your apt sources configuration has issues!",
            "\n\n",
            "Common problems:",
            "● Unreachable mirror repositories",
            "● Missing Release files for backports",
            "\n\n",
            "Recommendations:",
            "1. Check /etc/apt/sources.list",
            "2. Comment out (#) problematic backports repos",
            "3. Use reliable mirrors (e.g., tsinghua, aliyun)",
            "\n\n",
            "Example for Debian 11 Bullseye:",
            "  deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bullseye main contrib non-free",
            "  #deb http://deb.debian.org/debian bullseye-backports main contrib non-free",
        ],
    )

    return get_confirm(
        "Do you want to continue installation? (Fix sources first if needed)",
        default_choice=False,
    )


def unhold_v4l_utils() -> bool:
    """
    解除 v4l-utils 包的 hold 状态
    :return: True if successful or not held
    """
    try:
        Logger.print_status("Checking v4l-utils hold status ...")

        # 检查是否被 hold
        result = run(
            ["apt-mark", "showhold"],
            capture_output=True,
            text=True,
        )

        if "v4l-utils" in result.stdout:
            Logger.print_status("Unholding v4l-utils package ...")
            run(
                ["sudo", "apt-mark", "unhold", "v4l-utils"],
                check=True,
                stderr=PIPE,
            )
            Logger.print_ok("v4l-utils unhold successful!")
        else:
            Logger.print_ok("v4l-utils is not on hold.")

        return True

    except CalledProcessError as e:
        Logger.print_error(f"Error unholding v4l-utils: {e}")
        return False


def install_crowsnest_dependencies() -> bool:
    """
    智能安装 crowsnest 依赖，包含错误处理
    :return: True if successful
    """
    try:
        Logger.print_status("Installing crowsnest dependencies ...")

        # 1. 解除 v4l-utils hold
        if not unhold_v4l_utils():
            Logger.print_warn("Could not unhold v4l-utils, trying to continue...")

        # 2. 更新包列表（带 allow-releaseinfo-change）
        Logger.print_status("Updating package lists ...")
        run(
            ["sudo", "apt-get", "update", "--allow-releaseinfo-change"],
            check=True,
            stderr=PIPE,
        )

        # 3. 尝试升级 held packages
        Logger.print_status("Upgrading held packages if needed ...")
        run(
            ["sudo", "apt-get", "upgrade", "-y", "--allow-change-held-packages"],
            check=True,
            stderr=PIPE,
        )

        # 4. 安装依赖包
        Logger.print_status(f"Installing {len(CROWSNEST_REQUIRED_PACKAGES)} packages ...")
        cmd = ["sudo", "apt-get", "install", "-y"] + CROWSNEST_REQUIRED_PACKAGES

        result = run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            # 尝试单独安装每个包，识别问题包
            Logger.print_warn("Batch installation failed, trying individual packages...")
            failed_packages = []

            for pkg in CROWSNEST_REQUIRED_PACKAGES:
                try:
                    run(
                        ["sudo", "apt-get", "install", "-y", pkg],
                        check=True,
                        stderr=DEVNULL,
                        stdout=DEVNULL,
                    )
                    Logger.print_ok(f"Installed: {pkg}")
                except CalledProcessError:
                    failed_packages.append(pkg)
                    Logger.print_warn(f"Failed to install: {pkg}")

            if failed_packages:
                Logger.print_error(
                    f"Could not install: {', '.join(failed_packages)}"
                )
                return False

        Logger.print_ok("All crowsnest dependencies installed successfully!")
        return True

    except CalledProcessError as e:
        Logger.print_error(f"Error installing dependencies: {e}")
        return False


def run_crowsnest_makefile_install() -> bool:
    """
    执行 crowsnest Makefile 安装流程
    :return: True if successful
    """
    try:
        # Step 1: make config
        Logger.print_status("Running 'sudo make config' ...")
        Logger.print_info("This may prompt for sudo password...")

        run(
            ["sudo", "make", "config"],
            cwd=CROWSNEST_DIR,
            check=True,
        )
        Logger.print_ok("Configuration successful!")

        # Step 2: make install
        Logger.print_status("Running 'sudo make install' ...")
        Logger.print_info("This may take a while...")

        result = run(
            ["sudo", "make", "install"],
            cwd=CROWSNEST_DIR,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            Logger.print_error("Installation failed!")
            Logger.print_error(result.stderr)
            return False

        Logger.print_ok("Crowsnest installation successful!")
        return True

    except CalledProcessError as e:
        Logger.print_error(f"Error during Makefile installation: {e}")
        return False


def print_multi_instance_warning_optimized(instances: List[Klipper]) -> None:
    """优化的多实例警告"""
    Logger.print_dialog(
        DialogType.INFO,
        [
            "Multi-instance setup detected!",
            "\n\n",
            "Crowsnest does NOT natively support multi-instances.",
            "Workaround: Choose the primary instance for camera configuration.",
            "\n\n",
            "Found instances:",
            *[f"● {instance.data_dir.name}" for instance in instances],
            "\n\n",
            "The installation will continue with default configuration.",
            "You can configure crowsnest.conf manually after installation.",
        ],
    )


def install_crowsnest_optimized() -> bool:
    """
    优化的 crowsnest 安装流程
    解决常见的 apt repo 和依赖问题
    :return: True if successful
    """
    Logger.print_status("Installing Crowsnest (Optimized) ...")

    # Step 1: 检查多实例情况
    instances: List[Klipper] = get_instances(Klipper)
    if len(instances) > 1:
        print_multi_instance_warning_optimized(instances)
        if not get_confirm("Continue with installation?"):
            Logger.print_info("Crowsnest installation aborted.")
            return False

    # Step 2: 检查并修复 apt sources
    if not check_apt_sources_validity():
        if not fix_apt_sources_interactive():
            Logger.print_info("Crowsnest installation aborted.")
            return False

    # Step 3: Clone repository (使用浅克隆优化)
    Logger.print_status("Cloning crowsnest repository ...")
    try:
        git_clone_wrapper(
            CROWSNEST_REPO,
            CROWSNEST_DIR,
            "master",
        )
    except Exception as e:
        Logger.print_error(f"Failed to clone repository: {e}")
        return False

    # Step 4: 安装依赖
    if not install_crowsnest_dependencies():
        Logger.print_error("Failed to install dependencies!")
        Logger.print_info(
            "Please check your apt sources and try again.\n"
            "See: /etc/apt/sources.list"
        )
        return False

    # Step 5: 执行 Makefile 安装
    if not run_crowsnest_makefile_install():
        return False

    # Step 6: 提示重启
    Logger.print_dialog(
        DialogType.CUSTOM,
        custom_title="Crowsnest Installation Complete!",
        custom_color="green",
        content=[
            "Crowsnest has been successfully installed.",
            "\n\n",
            "Next steps:",
            "● Configure crowsnest.conf in ~/printer_data/config/",
            "● Check video devices: ls -la /dev/video*",
            "● Check device info: sudo v4l2-ctl --device=/dev/video0 --info",
            "● Reboot system to ensure all changes take effect",
            "\n\n",
            "Run 'sudo systemctl status crowsnest' to check service status.",
        ],
    )

    if get_confirm("Reboot system now?", default_choice=False):
        Logger.print_status("Rebooting system ...")
        run(["sudo", "reboot"], check=False)

    return True


def verify_crowsnest_installation() -> bool:
    """
    验证 crowsnest 安装是否成功
    :return: True if installation is valid
    """
    checks = []

    # 检查 crowsnest 目录
    checks.append(("Directory", CROWSNEST_DIR.exists()))

    # 检查 systemd 服务
    try:
        result = run(
            ["systemctl", "is-active", "crowsnest"],
            capture_output=True,
            text=True,
        )
        checks.append(("Service", result.returncode == 0))
    except Exception:
        checks.append(("Service", False))

    # 检查 video 设备
    video_devices = list(Path("/dev").glob("video*"))
    checks.append(("Video Devices", len(video_devices) > 0))

    # 打印验证结果
    Logger.print_status("Installation verification:")
    for name, status in checks:
        if status:
            Logger.print_ok(f"  ✓ {name}")
        else:
            Logger.print_error(f"  ✗ {name}")

    return all(status for _, status in checks)

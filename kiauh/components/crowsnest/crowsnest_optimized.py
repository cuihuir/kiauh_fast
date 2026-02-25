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
from subprocess import DEVNULL, PIPE, CalledProcessError, run
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
            Logger.print_status("v4l-utils is on hold, unholding ...")
            result = run(
                ["sudo", "apt-mark", "unhold", "v4l-utils"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                Logger.print_ok("v4l-utils unhold successful!")
            else:
                Logger.print_warn(f"Failed to unhold v4l-utils: {result.stderr}")
                return False
        else:
            Logger.print_ok("v4l-utils is not on hold.")

        return True

    except CalledProcessError as e:
        Logger.print_error(f"Error checking/unholding v4l-utils: {e}")
        return False
    except Exception as e:
        Logger.print_warn(f"Unexpected error with v4l-utils hold check: {e}")
        return True  # 继续安装


def unhold_crowsnest_packages() -> bool:
    """
    只 unhold Crowsnest 需要的包（避免影响系统其他 held packages）
    :return: True if successful or user chooses to continue
    """
    try:
        Logger.print_status("Checking for held packages that may block crowsnest...")

        # 获取所有 held packages
        result = run(["apt-mark", "showhold"], capture_output=True, text=True)
        all_held = set(line.strip() for line in result.stdout.split("\n") if line.strip())

        if not all_held:
            Logger.print_ok("No held packages found.")
            return True

        # Crowsnest 相关的包（只检查这些）
        crowsnest_related = set([
            "v4l-utils",
            "libv4l-0",
            "libv4l-dev",
            "libv4l2rds0",
            "libv4lconvert0",
            "libv4l-rkmpp",  # Rockchip specific
        ])

        # 找出需要 unhold 的包（交集）
        packages_to_unhold = all_held & crowsnest_related

        if not packages_to_unhold:
            Logger.print_ok("No crowsnest-related packages are held.")
            Logger.print_info(f"System has {len(all_held)} held packages, but none affect crowsnest.")
            return True

        Logger.print_warn(f"Found {len(packages_to_unhold)} crowsnest-related held package(s):")
        for pkg in sorted(packages_to_unhold):
            Logger.print_info(f"  - {pkg}")

        Logger.print_info(
            f"\nNote: System has {len(all_held)} total held packages."
        )
        Logger.print_info(
            "Only the packages listed above will be unhold (safe for crowsnest)."
        )

        # 询问是否 unhold
        if not get_confirm(
            "Unhold these crowsnest-related packages?", default_choice=True
        ):
            Logger.print_info("Installation aborted by user.")
            return False

        # 只 Unhold crowsnest 需要的包
        Logger.print_status("Unholding crowsnest-related packages...")
        for pkg in sorted(packages_to_unhold):
            try:
                run(
                    ["sudo", "apt-mark", "unhold", pkg],
                    check=True,
                    capture_output=True,
                )
                Logger.print_ok(f"Unhold: {pkg}")
            except CalledProcessError as e:
                Logger.print_warn(f"Failed to unhold {pkg}: {e}")

        Logger.print_ok("Crowsnest-related packages have been unhold!")
        return True

    except CalledProcessError as e:
        Logger.print_error(f"Error checking held packages: {e}")
        return True  # 继续安装，即使检查失败
    except Exception as e:
        Logger.print_warn(f"Unexpected error checking held packages: {e}")
        return True  # 继续安装


def install_crowsnest_dependencies() -> bool:
    """
    智能安装 crowsnest 依赖，包含错误处理
    :return: True if successful
    """
    try:
        Logger.print_status("Installing crowsnest dependencies ...")

        # 1. 更新包列表（带 allow-releaseinfo-change）
        Logger.print_status("Updating package lists ...")
        run(
            ["sudo", "apt-get", "update", "--allow-releaseinfo-change"],
            check=True,
            stderr=PIPE,
        )

        # 2. 尝试升级 held packages
        Logger.print_status("Upgrading held packages if needed ...")
        run(
            ["sudo", "apt-get", "upgrade", "-y", "--allow-change-held-packages"],
            check=True,
            stderr=PIPE,
        )

        # 3. 预设 iperf3 debconf 答案，避免交互式弹窗
        run(
            ["sudo", "bash", "-c",
             "echo 'iperf3 iperf3/start_daemon boolean false' | debconf-set-selections"],
            check=False,
        )

        # 4. 安装依赖包
        Logger.print_status(f"Installing {len(CROWSNEST_REQUIRED_PACKAGES)} packages ...")
        cmd = ["sudo", "-E", "apt-get", "install", "-y"] + CROWSNEST_REQUIRED_PACKAGES
        env = {**__import__("os").environ, "DEBIAN_FRONTEND": "noninteractive"}
        result = run(cmd, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            # 尝试单独安装每个包，识别问题包
            Logger.print_warn("Batch installation failed, trying individual packages...")
            failed_packages = []

            for pkg in CROWSNEST_REQUIRED_PACKAGES:
                try:
                    run(
                        ["sudo", "-E", "apt-get", "install", "-y", pkg],
                        check=True,
                        stderr=DEVNULL,
                        stdout=DEVNULL,
                        env=env,
                    )
                    Logger.print_ok(f"Installed: {pkg}")
                except CalledProcessError:
                    failed_packages.append(pkg)
                    Logger.print_warn(f"Failed to install: {pkg}")

            if failed_packages:
                Logger.print_error(
                    f"Could not install: {', '.join(failed_packages)}"
                )
                Logger.print_warn("Failed to install dependencies!")
                Logger.print_info("Please check your apt sources and try again.")
                Logger.print_info("See: /etc/apt/sources.list")

                # 检查是否有关键包失败
                critical_packages = ["make", "crudini", "python3-iniparse"]
                critical_failed = [p for p in failed_packages if p in critical_packages]

                if critical_failed:
                    Logger.print_error(
                        f"Critical packages failed: {', '.join(critical_failed)}"
                    )
                    return False

                # 非关键包失败，询问是否继续
                from utils.input_utils import get_confirm

                Logger.print_warn(
                    f"\nNon-critical packages failed: {', '.join(failed_packages)}"
                )
                Logger.print_info(
                    "Crowsnest may work without these packages, but some features may be limited."
                )

                if not get_confirm("Continue installation anyway?", default_choice=True):
                    Logger.print_info("Installation aborted by user.")
                    return False

                Logger.print_warn("Continuing installation without failed packages...")

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
        Logger.print_info("This may take 5-10 minutes (compiling ustreamer)...")
        Logger.print_info("Showing compilation output (you can see progress):")
        print()  # 空行

        # 直接运行，显示实时输出（不用 Spinner）
        result = run(
            ["sudo", "make", "install"],
            cwd=CROWSNEST_DIR,
            check=False,  # 不自动抛异常，手动检查
        )
        returncode = result.returncode
        stdout = ""
        stderr = ""

        print()  # 空行
        if returncode != 0:
            Logger.print_error("Installation failed!")
            if stderr:
                Logger.print_error(stderr)

            # 检查是否是 held packages 问题
            error_text = (stderr + stdout).lower()
            if "held packages" in error_text or "pkgproblemresolver" in error_text:
                Logger.print_dialog(
                    DialogType.ERROR,
                    [
                        "Installation failed due to package conflicts!",
                        "",
                        "Possible causes:",
                        "1. System has held packages blocking installation",
                        "2. Conflicting apt sources",
                        "",
                        "Try these manual fixes:",
                        "1. Run: sudo apt-mark showhold",
                        "2. Run: sudo apt-mark unhold <package-name>",
                        "3. Run: sudo apt-get update",
                        "4. Run: sudo apt-get upgrade -y --allow-change-held-packages",
                        "5. Try installation again",
                        "",
                        "Or check your apt sources:",
                        "- Edit: /etc/apt/sources.list",
                        "- Comment out problematic repos",
                    ],
                )
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

    # Step 2.5: Unhold crowsnest-related packages (before any apt operations)
    if not unhold_crowsnest_packages():
        Logger.print_info("Crowsnest installation aborted.")
        return False

    # Step 3: Clone repository (处理权限问题 + 使用浅克隆优化)
    Logger.print_status("Cloning crowsnest repository ...")

    # 如果目录存在，用 sudo 删除（避免权限问题）
    if CROWSNEST_DIR.exists():
        Logger.print_warn(f"'{CROWSNEST_DIR}' already exists.")
        if get_confirm("Remove existing directory and re-clone?", default_choice=True):
            Logger.print_status("Removing existing crowsnest directory...")
            try:
                run(
                    ["sudo", "rm", "-rf", str(CROWSNEST_DIR)],
                    check=True,
                    capture_output=True,
                )
                Logger.print_ok("Existing directory removed.")
            except CalledProcessError as e:
                Logger.print_error(f"Failed to remove existing directory: {e}")
                return False
        else:
            Logger.print_info("Crowsnest installation aborted.")
            return False

    try:
        git_clone_wrapper(
            CROWSNEST_REPO,
            CROWSNEST_DIR,
            "master",
            force=True,  # 已经手动处理了，强制克隆
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

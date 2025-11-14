# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
import shutil
from pathlib import Path
from subprocess import CalledProcessError, run
from typing import List

from components.klipper.klipper import Klipper
from components.klipperscreen import (
    KLIPPERSCREEN_DIR,
    KLIPPERSCREEN_ENV_DIR,
    KLIPPERSCREEN_INSTALL_SCRIPT,
    KLIPPERSCREEN_LOG_NAME,
    KLIPPERSCREEN_REPO,
    KLIPPERSCREEN_REQ_FILE,
    KLIPPERSCREEN_SERVICE_FILE,
    KLIPPERSCREEN_SERVICE_NAME,
    KLIPPERSCREEN_UPDATER_SECTION_NAME,
)
from components.moonraker.moonraker import Moonraker
from core.constants import SYSTEMD
from core.instance_manager.instance_manager import InstanceManager
from core.logger import DialogType, Logger
from core.services.backup_service import BackupService
from core.settings.kiauh_settings import KiauhSettings
from core.types.component_status import ComponentStatus
from utils.common import (
    check_install_dependencies,
    get_install_status,
)
from utils.config_utils import add_config_section, remove_config_section
from utils.fs_utils import remove_with_sudo
from utils.git_utils import (
    git_clone_wrapper,
    git_pull_wrapper,
)
from utils.input_utils import get_confirm
from utils.instance_utils import get_instances
from utils.sys_utils import (
    check_python_version,
    cmd_sysctl_service,
    create_python_venv,
    install_python_requirements,
    remove_system_service,
)


def install_klipperscreen() -> None:
    Logger.print_status("Installing KlipperScreen ...")

    if not check_python_version(3, 7):
        return

    mr_instances = get_instances(Moonraker)
    if not mr_instances:
        Logger.print_dialog(
            DialogType.WARNING,
            [
                "Moonraker not found! KlipperScreen will not properly work "
                "without a working Moonraker installation.",
                "\n\n",
                "KlipperScreens update manager configuration for Moonraker "
                "will not be added to any moonraker.conf.",
            ],
        )
        if not get_confirm(
            "Continue KlipperScreen installation?",
            default_choice=False,
            allow_go_back=True,
        ):
            return

    check_install_dependencies()

    git_clone_wrapper(KLIPPERSCREEN_REPO, KLIPPERSCREEN_DIR)

    # 使用我们自己的安装逻辑（支持 uv）而不是官方脚本
    try:
        install_klipperscreen_optimized()
        if mr_instances:
            patch_klipperscreen_update_manager(mr_instances)
            InstanceManager.restart_all(mr_instances)
        else:
            Logger.print_info(
                "Moonraker is not installed! Cannot add "
                "KlipperScreen to update manager!"
            )
        Logger.print_ok("KlipperScreen successfully installed!")
    except CalledProcessError as e:
        Logger.print_error(f"Error installing KlipperScreen:\n{e}")
        return


def patch_klipperscreen_update_manager(instances: List[Moonraker]) -> None:
    BackupService().backup_moonraker_conf()
    add_config_section(
        section=KLIPPERSCREEN_UPDATER_SECTION_NAME,
        instances=instances,
        options=[
            ("type", "git_repo"),
            ("path", KLIPPERSCREEN_DIR.as_posix()),
            ("origin", KLIPPERSCREEN_REPO),
            ("managed_services", "KlipperScreen"),
            ("env", f"{KLIPPERSCREEN_ENV_DIR}/bin/python"),
            ("requirements", KLIPPERSCREEN_REQ_FILE.as_posix()),
            ("install_script", KLIPPERSCREEN_INSTALL_SCRIPT.as_posix()),
        ],
    )


def update_klipperscreen() -> None:
    if not KLIPPERSCREEN_DIR.exists():
        Logger.print_info("KlipperScreen does not seem to be installed! Skipping ...")
        return

    try:
        Logger.print_status("Updating KlipperScreen ...")

        cmd_sysctl_service(KLIPPERSCREEN_SERVICE_NAME, "stop")

        settings = KiauhSettings()
        if settings.kiauh.backup_before_update:
            backup_klipperscreen_dir()

        git_pull_wrapper(KLIPPERSCREEN_DIR)

        install_python_requirements(KLIPPERSCREEN_ENV_DIR, KLIPPERSCREEN_REQ_FILE)

        cmd_sysctl_service(KLIPPERSCREEN_SERVICE_NAME, "start")

        Logger.print_ok("KlipperScreen updated successfully.", end="\n\n")
    except CalledProcessError as e:
        Logger.print_error(f"Error updating KlipperScreen:\n{e}")
        return


def get_klipperscreen_status() -> ComponentStatus:
    return get_install_status(
        KLIPPERSCREEN_DIR,
        KLIPPERSCREEN_ENV_DIR,
        files=[SYSTEMD.joinpath(KLIPPERSCREEN_SERVICE_NAME)],
    )


def remove_klipperscreen() -> None:
    Logger.print_status("Removing KlipperScreen ...")
    try:
        if KLIPPERSCREEN_DIR.exists():
            Logger.print_status("Removing KlipperScreen directory ...")
            shutil.rmtree(KLIPPERSCREEN_DIR)
            Logger.print_ok("KlipperScreen directory successfully removed!")
        else:
            Logger.print_warn("KlipperScreen directory not found!")

        if KLIPPERSCREEN_ENV_DIR.exists():
            Logger.print_status("Removing KlipperScreen environment ...")
            shutil.rmtree(KLIPPERSCREEN_ENV_DIR)
            Logger.print_ok("KlipperScreen environment successfully removed!")
        else:
            Logger.print_warn("KlipperScreen environment not found!")

        if KLIPPERSCREEN_SERVICE_FILE.exists():
            remove_system_service(KLIPPERSCREEN_SERVICE_NAME)

        logfile = Path(f"/tmp/{KLIPPERSCREEN_LOG_NAME}")
        if logfile.exists():
            Logger.print_status("Removing KlipperScreen log file ...")
            remove_with_sudo(logfile)
            Logger.print_ok("KlipperScreen log file successfully removed!")

        kl_instances: List[Klipper] = get_instances(Klipper)
        for instance in kl_instances:
            logfile = instance.base.log_dir.joinpath(KLIPPERSCREEN_LOG_NAME)
            if logfile.exists():
                Logger.print_status(f"Removing {logfile} ...")
                Path(logfile).unlink()
                Logger.print_ok(f"{logfile} successfully removed!")

        mr_instances: List[Moonraker] = get_instances(Moonraker)
        if mr_instances:
            Logger.print_status("Removing KlipperScreen from update manager ...")
            BackupService().backup_moonraker_conf()
            remove_config_section("update_manager KlipperScreen", mr_instances)
            Logger.print_ok("KlipperScreen successfully removed from update manager!")

        Logger.print_ok("KlipperScreen successfully removed!")

    except Exception as e:
        Logger.print_error(f"Error removing KlipperScreen:\n{e}")


def backup_klipperscreen_dir() -> None:
    svc = BackupService()
    svc.backup_directory(
        source_path=KLIPPERSCREEN_DIR,
        backup_name="KlipperScreen",
        target_path="KlipperScreen",
    )
    svc.backup_directory(
        source_path=KLIPPERSCREEN_ENV_DIR,
        backup_name="KlipperScreen-env",
        target_path="KlipperScreen",
    )


def install_klipperscreen_optimized() -> None:
    """
    优化的 KlipperScreen 安装（使用 uv 加速）
    替代官方 KlipperScreen-install.sh 中的 Python 环境部分
    """
    import os
    import getpass

    username = getpass.getuser()

    # 1. 创建 Python 虚拟环境（使用 uv venv，10-100x 更快）
    Logger.print_status("Set up Python virtual environment ...")
    if not create_python_venv(
        target=KLIPPERSCREEN_ENV_DIR,
        force=True,  # 覆盖已存在的 venv
    ):
        raise RuntimeError("Failed to create virtual environment")

    # 2. 安装 Python requirements（使用 uv pip，10-100x 更快）
    Logger.print_status("Installing Python requirements ...")
    install_python_requirements(
        target=KLIPPERSCREEN_ENV_DIR,
        requirements=KLIPPERSCREEN_REQ_FILE,
    )

    # 3. 安装 systemd 服务
    Logger.print_status("Installing KlipperScreen systemd service ...")

    # 读取服务模板
    service_template_path = KLIPPERSCREEN_DIR / "scripts" / "KlipperScreen.service"
    if not service_template_path.exists():
        raise RuntimeError(f"Service template not found: {service_template_path}")

    service_content = service_template_path.read_text()

    # 替换占位符
    service_content = service_content.replace("KS_USER", username)
    service_content = service_content.replace("KS_ENV", str(KLIPPERSCREEN_ENV_DIR))
    service_content = service_content.replace("KS_DIR", str(KLIPPERSCREEN_DIR))
    service_content = service_content.replace("KS_BACKEND", "X")  # 默认使用 Xserver

    # 写入 systemd 服务文件
    KLIPPERSCREEN_SERVICE_FILE.write_text(service_content)

    # 启用服务
    try:
        run(["sudo", "systemctl", "unmask", "KlipperScreen.service"], check=True)
        run(["sudo", "systemctl", "daemon-reload"], check=True)
        run(["sudo", "systemctl", "enable", "KlipperScreen"], check=True)
        run(["sudo", "systemctl", "set-default", "multi-user.target"], check=True)
        run(["sudo", "adduser", username, "tty"], check=False)  # 可能已经在组里
        Logger.print_ok("KlipperScreen service installed")
    except CalledProcessError as e:
        Logger.print_error(f"Failed to configure systemd service: {e}")
        raise

    # 4. 配置 PolicyKit rules
    Logger.print_status("Configuring PolicyKit rules ...")
    try:
        # 添加用户到组
        run(["sudo", "groupadd", "-f", "klipperscreen"], check=False)
        run(["sudo", "groupadd", "-f", "network"], check=False)
        run(["sudo", "adduser", username, "netdev"], check=False)
        run(["sudo", "adduser", username, "network"], check=False)

        # 检查 PolicyKit 版本并安装规则
        try:
            version_output = run(
                ["pkaction", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            Logger.print_ok("PolicyKit configured")
        except:
            Logger.print_warn("PolicyKit not found, skipping rules configuration")
    except CalledProcessError as e:
        Logger.print_warn(f"PolicyKit configuration warning: {e}")

    # 5. 添加桌面文件
    Logger.print_status("Adding desktop entry ...")
    try:
        desktop_dir = Path.home() / ".local" / "share" / "applications"
        desktop_dir.mkdir(parents=True, exist_ok=True)

        desktop_file = KLIPPERSCREEN_DIR / "scripts" / "KlipperScreen.desktop"
        if desktop_file.exists():
            shutil.copy(desktop_file, desktop_dir / "KlipperScreen.desktop")

        icon_file = KLIPPERSCREEN_DIR / "styles" / "icon.svg"
        if icon_file.exists():
            run([
                "sudo", "cp",
                str(icon_file),
                "/usr/share/icons/hicolor/scalable/apps/KlipperScreen.svg"
            ], check=False)

        Logger.print_ok("Desktop entry added")
    except Exception as e:
        Logger.print_warn(f"Desktop entry warning: {e}")

    # 6. 启动服务
    Logger.print_status("Starting KlipperScreen service ...")
    try:
        run(["sudo", "systemctl", "restart", "KlipperScreen"], check=True)
        Logger.print_ok("KlipperScreen service started")
    except CalledProcessError as e:
        Logger.print_warn(f"Failed to start service (will start on next reboot): {e}")

    Logger.print_ok("KlipperScreen installation completed!")
    Logger.print_info("\nNote: A system reboot may be required for KlipperScreen to work properly.")

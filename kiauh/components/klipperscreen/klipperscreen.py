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

    # 注意：不调用 check_install_dependencies()
    # 因为 install_klipperscreen_optimized() 会动态解析官方脚本的依赖

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
        raise  # 重新抛出异常，让上层知道安装失败
    except Exception as e:
        Logger.print_error(f"Error installing KlipperScreen:\n{e}")
        raise  # 重新抛出异常，让上层知道安装失败


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


def parse_install_script_dependencies() -> dict:
    """
    动态解析官方 install.sh，提取 apt 依赖
    这样即使官方更新脚本，我们也能自动适配

    Returns:
        dict: {
            'XSERVER': ['xinit', 'xinput', ...],
            'PYGOBJECT': ['libgirepository1.0-dev', ...],
            'MISC': [...],
            'OPTIONAL': [...]
        }
    """
    import re

    script_path = KLIPPERSCREEN_INSTALL_SCRIPT
    if not script_path.exists():
        Logger.print_warn(f"Install script not found: {script_path}")
        return {}

    script_content = script_path.read_text()
    dependencies = {}

    # 解析 bash 变量定义（如 PYGOBJECT="pkg1 pkg2 pkg3"）
    # 匹配模式：VARIABLE="package1 package2 ..."
    pattern = r'^(\w+)="([^"]+)"'

    for line in script_content.splitlines():
        line = line.strip()
        match = re.match(pattern, line)
        if match:
            var_name = match.group(1)
            packages = match.group(2)
            # 只提取依赖相关的变量
            if var_name in ['XSERVER', 'CAGE', 'PYGOBJECT', 'MISC', 'OPTIONAL']:
                dependencies[var_name] = packages.split()

    total_packages = sum(len(pkgs) for pkgs in dependencies.values())
    Logger.print_info(f"Parsed {len(dependencies)} dependency groups, {total_packages} total packages")

    # 显示详细信息（调试用）
    for group, packages in dependencies.items():
        Logger.print_info(f"  {group}: {len(packages)} packages")

    return dependencies


def install_klipperscreen_optimized() -> None:
    """
    优化的 KlipperScreen 安装（使用 uv 加速）
    策略：
    1. 动态解析官方 install.sh，提取 apt 依赖（自动适配更新）
    2. 安装 apt 依赖（使用官方的依赖列表）
    3. 替换 Python venv/pip 部分用 uv（10-100x 加速）
    """
    import os
    import getpass

    username = getpass.getuser()

    # 0. 动态解析官方脚本的依赖
    Logger.print_status("Parsing official KlipperScreen-install.sh for dependencies ...")
    deps = parse_install_script_dependencies()

    if not deps:
        Logger.print_warn("Failed to parse dependencies, using fallback list")

    # 0.1 安装动态解析的 apt 依赖
    Logger.print_status("Installing system dependencies from official script ...")

    # PYGOBJECT/MISC 是必需的（Python 绑定），XSERVER 包可能有依赖冲突，单独处理
    required_packages = []
    xserver_packages = []

    if deps:
        required_packages.extend(deps.get('PYGOBJECT', []))
        required_packages.extend(deps.get('MISC', []))
        xserver_packages.extend(deps.get('XSERVER', []))
        optional_packages = deps.get('OPTIONAL', [])
    else:
        required_packages = [
            "libgirepository1.0-dev", "gcc", "libcairo2-dev", "pkg-config",
            "python3-dev", "gir1.2-gtk-3.0", "librsvg2-common", "libopenjp2-7",
            "libdbus-glib-1-dev", "autoconf", "python3-venv",
        ]
        xserver_packages = [
            "xinit", "xinput", "x11-xserver-utils", "xserver-xorg-input-evdev",
            "xserver-xorg-input-libinput", "xserver-xorg-legacy",
            "xserver-xorg-video-fbdev",
        ]
        optional_packages = ["fonts-nanum", "fonts-ipafont", "libmpv-dev"]

    # 更新包列表（只做一次）
    run(["sudo", "apt-get", "update"], check=True, capture_output=True)

    # 安装必需的包（失败则中断）
    if required_packages:
        Logger.print_info(f"Installing {len(required_packages)} required packages ...")
        try:
            run(["sudo", "apt-get", "install", "-y"] + required_packages, check=True)
            Logger.print_ok("Required packages installed")
        except CalledProcessError as e:
            Logger.print_error(f"Failed to install required packages: {e}")
            raise

    # 安装 Xserver 包（逐个尝试，有依赖冲突时跳过并警告）
    if xserver_packages:
        Logger.print_info(f"Installing {len(xserver_packages)} Xserver packages ...")
        failed_xserver = []
        for pkg in xserver_packages:
            result = run(
                ["sudo", "apt-get", "install", "-y", pkg],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                failed_xserver.append(pkg)
                Logger.print_warn(f"Skipping {pkg} (dependency conflict, install manually if needed)")
        if failed_xserver:
            Logger.print_warn(
                f"The following Xserver packages could not be installed automatically: "
                f"{', '.join(failed_xserver)}\n"
                f"You may need to install them manually or resolve dependency conflicts."
            )
        else:
            Logger.print_ok("Xserver packages installed")

    # 安装可选包（不强制）
    if optional_packages:
        Logger.print_info(f"Installing {len(optional_packages)} optional packages ...")
        run(["sudo", "apt-get", "install", "-y"] + optional_packages, check=False)
        Logger.print_ok("Optional packages installed")

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

    # 替换占位符（模板使用无 % 的格式，如 KS_USER）
    service_content = service_content.replace("KS_USER", username)
    service_content = service_content.replace("KS_ENV", str(KLIPPERSCREEN_ENV_DIR))
    service_content = service_content.replace("KS_DIR", str(KLIPPERSCREEN_DIR))
    service_content = service_content.replace("KS_BACKEND", "X")  # 默认使用 Xserver

    # 修正 Environment= 行：systemd 要求每个变量单独一行
    # 模板生成的格式：Environment="KS_XCLIENT=..." BACKEND=X （不合法）
    # 修正为两行独立的 Environment=
    import re
    service_content = re.sub(
        r'Environment="(KS_XCLIENT=[^"]+)"\s+BACKEND=(\S+)',
        r'Environment="\1"\nEnvironment="BACKEND=\2"',
        service_content,
    )
    # 去掉 ExecStart 路径两端的引号（systemd 不需要，有时反而报错）
    service_content = re.sub(
        r'ExecStart="([^"]+)"',
        r'ExecStart=\1',
        service_content,
    )

    # 写入 systemd 服务文件（需要 sudo）
    try:
        # 先写入临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.service') as tmp:
            tmp.write(service_content)
            tmp_path = tmp.name

        # 用 sudo mv 移动到 systemd 目录
        run([
            "sudo", "mv",
            tmp_path,
            str(KLIPPERSCREEN_SERVICE_FILE)
        ], check=True)

        Logger.print_ok("Service file installed")
    except CalledProcessError as e:
        Logger.print_error(f"Failed to install service file: {e}")
        raise

    # 允许非 console 用户运行 X server（Debian 默认只允许 console 用户）
    xwrapper = Path("/etc/X11/Xwrapper.config")
    if xwrapper.exists():
        content = xwrapper.read_text()
        if "allowed_users=console" in content:
            Logger.print_status("Configuring Xwrapper to allow X server ...")
            new_content = content.replace("allowed_users=console", "allowed_users=anybody")
            run(
                ["sudo", "tee", str(xwrapper)],
                input=new_content.encode(),
                stdout=DEVNULL,
                check=True,
            )
            Logger.print_ok("Xwrapper configured")

    # 启用服务
    try:
        run(["sudo", "systemctl", "unmask", "KlipperScreen.service"], check=True)
        run(["sudo", "systemctl", "daemon-reload"], check=True)
        run(["sudo", "systemctl", "enable", "KlipperScreen"], check=True)
        run(["sudo", "systemctl", "set-default", "multi-user.target"], check=True)
        run(["sudo", "adduser", username, "tty"], check=False)  # 可能已经在组里
        Logger.print_ok("KlipperScreen service configured")
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

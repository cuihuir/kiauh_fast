"""Klipper 5-axis component - Standalone service installer."""
from __future__ import annotations

import shutil
from pathlib import Path
from subprocess import DEVNULL, CalledProcessError, run

from components.klipper_5axis import (
    KLIPPER_5AXIS_CFG_NAME,
    KLIPPER_5AXIS_DIR,
    KLIPPER_5AXIS_ENV_DIR,
    KLIPPER_5AXIS_ENV_FILE_NAME,
    KLIPPER_5AXIS_ENV_FILE_TEMPLATE,
    KLIPPER_5AXIS_LOG_NAME,
    KLIPPER_5AXIS_REPO_URL,
    KLIPPER_5AXIS_REQ_FILE,
    KLIPPER_5AXIS_SERIAL_NAME,
    KLIPPER_5AXIS_SERVICE_NAME,
    KLIPPER_5AXIS_SERVICE_TEMPLATE,
    KLIPPER_5AXIS_TAG,
    KLIPPER_5AXIS_UDS_NAME,
)
from core.constants import CURRENT_USER, SYSTEMD
from core.logger import Logger
from core.types.component_status import ComponentStatus
from utils.common import get_install_status
from utils.git_utils import git_clone_at_tag
from utils.sys_utils import (
    cmd_sysctl_service,
    create_python_venv,
    install_python_requirements,
)


def install_klipper_5axis() -> bool:
    """Install Klipper 5-axis as a standalone service."""
    Logger.print_status("Installing Klipper 5-axis ...")

    if not KLIPPER_5AXIS_TAG:
        Logger.print_error("No tag configured for klipper_5axis in component_versions.json!")
        return False

    # Clone at pinned tag
    success = git_clone_at_tag(KLIPPER_5AXIS_REPO_URL, KLIPPER_5AXIS_DIR, KLIPPER_5AXIS_TAG)
    if not success:
        Logger.print_error("Failed to clone klipper-5axis repository!")
        return False

    # Install system deps
    _install_system_packages()

    # Create venv and install requirements
    try:
        if create_python_venv(KLIPPER_5AXIS_ENV_DIR, True, False):
            if KLIPPER_5AXIS_REQ_FILE.exists():
                install_python_requirements(KLIPPER_5AXIS_ENV_DIR, KLIPPER_5AXIS_REQ_FILE)
    except CalledProcessError:
        Logger.print_error("Error installing Klipper 5-axis requirements!")
        return False

    # Install systemd service
    _install_service()

    Logger.print_ok("Klipper 5-axis successfully installed!")
    Logger.print_info(f"Installed at tag: {KLIPPER_5AXIS_TAG}")
    return True


def _install_system_packages() -> None:
    """Install system packages needed by klipper."""
    packages = [
        "python3-virtualenv",
        "dfu-util",
        "gcc-arm-none-eabi",
        "binutils-arm-none-eabi",
        "libnewlib-arm-none-eabi",
    ]
    try:
        run(["sudo", "apt-get", "install", "-y", "-qq"] + packages,
            check=True, stdout=DEVNULL, stderr=DEVNULL)
    except CalledProcessError:
        pass


def _install_service() -> None:
    """Install klipper-5axis systemd service."""
    try:
        service_content = KLIPPER_5AXIS_SERVICE_TEMPLATE.read_text()
        service_content = service_content.replace("%USER%", CURRENT_USER)
        service_content = service_content.replace("%KLIPPER_5AXIS_DIR%", KLIPPER_5AXIS_DIR.as_posix())
        service_content = service_content.replace("%ENV%", KLIPPER_5AXIS_ENV_DIR.as_posix())
        service_content = service_content.replace(
            "%ENV_FILE%", str(Path.home() / "printer_data" / "systemd" / KLIPPER_5AXIS_ENV_FILE_NAME)
        )

        service_path = SYSTEMD.joinpath(KLIPPER_5AXIS_SERVICE_NAME)
        run(["sudo", "tee", service_path.as_posix()],
            input=service_content.encode(), stdout=DEVNULL, check=True)

        # Write env file
        env_content = KLIPPER_5AXIS_ENV_FILE_TEMPLATE.read_text()
        env_content = env_content.replace("%KLIPPER_5AXIS_DIR%", KLIPPER_5AXIS_DIR.as_posix())
        env_content = env_content.replace("%CFG%", f"{Path.home()}/printer_data/config/{KLIPPER_5AXIS_CFG_NAME}")
        env_content = env_content.replace("%SERIAL%", f"{Path.home()}/printer_data/comms/{KLIPPER_5AXIS_SERIAL_NAME}")
        env_content = env_content.replace("%LOG%", f"{Path.home()}/printer_data/logs/{KLIPPER_5AXIS_LOG_NAME}")
        env_content = env_content.replace("%UDS%", f"{Path.home()}/printer_data/comms/{KLIPPER_5AXIS_UDS_NAME}")

        env_dir = Path.home() / "printer_data" / "systemd"
        env_dir.mkdir(parents=True, exist_ok=True)
        env_path = env_dir / KLIPPER_5AXIS_ENV_FILE_NAME
        env_path.write_text(env_content)

        run(["sudo", "systemctl", "daemon-reload"], check=True)
        run(["sudo", "systemctl", "enable", KLIPPER_5AXIS_SERVICE_NAME], check=True)
        Logger.print_ok("Klipper 5-axis service installed")
    except (CalledProcessError, OSError) as e:
        Logger.print_error(f"Error installing service: {e}")


def update_klipper_5axis() -> bool:
    """Update Klipper 5-axis."""
    if not KLIPPER_5AXIS_DIR.exists():
        Logger.print_info("Klipper 5-axis is not installed. Skipping ...")
        return False

    Logger.print_status("Updating Klipper 5-axis ...")
    try:
        cmd_sysctl_service(KLIPPER_5AXIS_SERVICE_NAME, "stop")
        success = git_clone_at_tag(KLIPPER_5AXIS_REPO_URL, KLIPPER_5AXIS_DIR, KLIPPER_5AXIS_TAG, force=True)
        if not success:
            return False
        if KLIPPER_5AXIS_REQ_FILE.exists():
            install_python_requirements(KLIPPER_5AXIS_ENV_DIR, KLIPPER_5AXIS_REQ_FILE)
        cmd_sysctl_service(KLIPPER_5AXIS_SERVICE_NAME, "start")
        Logger.print_ok("Klipper 5-axis updated successfully.")
        return True
    except CalledProcessError as e:
        Logger.print_error(f"Error updating: {e}")
        return False


def remove_klipper_5axis() -> None:
    """Remove Klipper 5-axis."""
    if not KLIPPER_5AXIS_DIR.exists():
        Logger.print_info("Klipper 5-axis is not installed. Skipping ...")
        return

    Logger.print_status("Removing Klipper 5-axis ...")
    try:
        cmd_sysctl_service(KLIPPER_5AXIS_SERVICE_NAME, "stop")
    except CalledProcessError:
        pass

    for f in [SYSTEMD.joinpath(KLIPPER_5AXIS_SERVICE_NAME),
               Path.home() / "printer_data" / "systemd" / KLIPPER_5AXIS_ENV_FILE_NAME]:
        if f.exists():
            run(["sudo", "rm", f.as_posix()], check=False)

    run(["sudo", "systemctl", "daemon-reload"], check=False)

    for d in [KLIPPER_5AXIS_DIR, KLIPPER_5AXIS_ENV_DIR]:
        if d.exists():
            shutil.rmtree(d)

    Logger.print_ok("Klipper 5-axis removed.")


def get_klipper_5axis_status() -> ComponentStatus:
    """Get installation status."""
    files = [SYSTEMD.joinpath(KLIPPER_5AXIS_SERVICE_NAME)]
    return get_install_status(KLIPPER_5AXIS_DIR, files=files)

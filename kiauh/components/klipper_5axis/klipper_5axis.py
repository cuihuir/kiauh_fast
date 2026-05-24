"""Klipper 5-axis component - Install, update, remove functions."""
from __future__ import annotations

import shutil
from pathlib import Path
from subprocess import DEVNULL, CalledProcessError, run

from components.klipper_5axis import (
    EXIT_KLIPPER_5AXIS_SETUP,
    KLIPPER_5AXIS_DIR,
    KLIPPER_5AXIS_ENV_DIR,
    KLIPPER_5AXIS_ENV_FILE_NAME,
    KLIPPER_5AXIS_ENV_FILE_TEMPLATE,
    KLIPPER_5AXIS_INSTALL_SCRIPT,
    KLIPPER_5AXIS_LOG_NAME,
    KLIPPER_5AXIS_REPO_URL,
    KLIPPER_5AXIS_REQ_FILE,
    KLIPPER_5AXIS_SERVICE_NAME,
    KLIPPER_5AXIS_SERVICE_TEMPLATE,
    KLIPPER_5AXIS_TAG,
)
from core.constants import CURRENT_USER, SYSTEMD
from core.logger import DialogType, Logger
from core.types.component_status import ComponentStatus
from utils.common import check_install_dependencies, get_install_status
from utils.git_utils import git_clone_at_tag, git_pull_wrapper
from utils.input_utils import get_confirm
from utils.sys_utils import (
    cmd_sysctl_service,
    create_python_venv,
    install_python_requirements,
)


def install_klipper_5axis() -> bool:
    """Install Klipper 5-axis firmware."""
    Logger.print_status("Installing Klipper 5-axis ...")

    if not KLIPPER_5AXIS_TAG:
        Logger.print_error(
            "No tag configured for klipper_5axis in component_versions.json!"
        )
        return False

    # Step 1: Clone at pinned tag
    success = git_clone_at_tag(
        KLIPPER_5AXIS_REPO_URL,
        KLIPPER_5AXIS_DIR,
        KLIPPER_5AXIS_TAG,
    )
    if not success:
        Logger.print_error("Failed to clone klipper-5axis repository!")
        return False

    # Step 2: Install system dependencies
    check_install_dependencies()

    # Step 3: Create Python venv and install requirements
    try:
        if create_python_venv(KLIPPER_5AXIS_ENV_DIR, False, False):
            if KLIPPER_5AXIS_REQ_FILE.exists():
                install_python_requirements(KLIPPER_5AXIS_ENV_DIR, KLIPPER_5AXIS_REQ_FILE)
            else:
                Logger.print_warn("Requirements file not found, skipping pip install")
    except CalledProcessError:
        Logger.print_error("Error installing Klipper 5-axis requirements!")
        return False

    # Step 4: Install systemd service
    _install_service()

    Logger.print_ok("Klipper 5-axis successfully installed!")
    Logger.print_info(f"Installed at tag: {KLIPPER_5AXIS_TAG}")
    return True


def _install_service() -> None:
    """Install the klipper-5axis systemd service file."""
    try:
        if not KLIPPER_5AXIS_SERVICE_TEMPLATE.exists():
            Logger.print_warn("Service template not found, skipping service installation")
            return

        service_content = KLIPPER_5AXIS_SERVICE_TEMPLATE.read_text()
        service_content = service_content.replace("%USER%", CURRENT_USER)
        service_content = service_content.replace(
            "%KLIPPER_5AXIS_DIR%", KLIPPER_5AXIS_DIR.as_posix()
        )
        service_content = service_content.replace(
            "%ENV%", KLIPPER_5AXIS_ENV_DIR.as_posix()
        )
        service_content = service_content.replace(
            "%ENV_FILE%",
            SYSTEMD.joinpath(f"klipper-5axis.env").as_posix(),
        )

        service_path = SYSTEMD.joinpath(KLIPPER_5AXIS_SERVICE_NAME)
        run(["sudo", "tee", service_path.as_posix()],
            input=service_content.encode(), stdout=DEVNULL, check=True)

        # Write env file
        if KLIPPER_5AXIS_ENV_FILE_TEMPLATE.exists():
            env_content = KLIPPER_5AXIS_ENV_FILE_TEMPLATE.read_text()
            env_content = env_content.replace(
                "%KLIPPER_5AXIS_DIR%", KLIPPER_5AXIS_DIR.as_posix()
            )
            env_content = env_content.replace(
                "%CFG%",
                f"{Path.home()}/printer_data/config/printer.cfg",
            )
            env_content = env_content.replace(
                "%SERIAL%",
                f"{Path.home()}/printer_data/comms/klippy.serial",
            )
            env_content = env_content.replace(
                "%LOG%",
                f"{Path.home()}/printer_data/logs/{KLIPPER_5AXIS_LOG_NAME}",
            )
            env_content = env_content.replace(
                "%UDS%",
                f"{Path.home()}/printer_data/comms/klippy.sock",
            )
            env_path = SYSTEMD.joinpath(KLIPPER_5AXIS_ENV_FILE_NAME)
            run(["sudo", "tee", env_path.as_posix()],
                input=env_content.encode(), stdout=DEVNULL, check=True)

        run(["systemctl", "daemon-reload"], check=True)
        run(["systemctl", "enable", KLIPPER_5AXIS_SERVICE_NAME], check=True)
        Logger.print_ok("Klipper 5-axis service installed")
    except (CalledProcessError, OSError) as e:
        Logger.print_error(f"Error installing service: {e}")


def update_klipper_5axis() -> bool:
    """Update Klipper 5-axis to the configured tag version."""
    if not KLIPPER_5AXIS_DIR.exists():
        Logger.print_info("Klipper 5-axis is not installed. Skipping ...")
        return False

    Logger.print_status("Updating Klipper 5-axis ...")

    try:
        cmd_sysctl_service(KLIPPER_5AXIS_SERVICE_NAME, "stop")

        # Re-clone at the pinned tag (handles tag change)
        success = git_clone_at_tag(
            KLIPPER_5AXIS_REPO_URL,
            KLIPPER_5AXIS_DIR,
            KLIPPER_5AXIS_TAG,
            force=True,
        )
        if not success:
            Logger.print_error("Failed to update klipper-5axis!")
            return False

        if KLIPPER_5AXIS_REQ_FILE.exists():
            install_python_requirements(KLIPPER_5AXIS_ENV_DIR, KLIPPER_5AXIS_REQ_FILE)

        cmd_sysctl_service(KLIPPER_5AXIS_SERVICE_NAME, "start")
        Logger.print_ok("Klipper 5-axis updated successfully.")
        return True
    except CalledProcessError as e:
        Logger.print_error(f"Error updating Klipper 5-axis: {e}")
        return False


def remove_klipper_5axis() -> None:
    """Remove Klipper 5-axis installation."""
    if not KLIPPER_5AXIS_DIR.exists():
        Logger.print_info("Klipper 5-axis is not installed. Skipping ...")
        return

    Logger.print_status("Removing Klipper 5-axis ...")

    try:
        cmd_sysctl_service(KLIPPER_5AXIS_SERVICE_NAME, "stop")
    except CalledProcessError:
        pass

    # Remove service files
    service_path = SYSTEMD.joinpath(KLIPPER_5AXIS_SERVICE_NAME)
    env_path = SYSTEMD.joinpath(KLIPPER_5AXIS_ENV_FILE_NAME)
    for f in [service_path, env_path]:
        if f.exists():
            run(["sudo", "rm", f.as_posix()], check=False)
            Logger.print_info(f"Removed {f}")

    try:
        run(["systemctl", "daemon-reload"], check=True)
    except CalledProcessError:
        pass

    # Remove directories
    for d in [KLIPPER_5AXIS_DIR, KLIPPER_5AXIS_ENV_DIR]:
        if d.exists():
            shutil.rmtree(d)
            Logger.print_info(f"Removed {d}")

    Logger.print_ok("Klipper 5-axis removed.")


def get_klipper_5axis_status() -> ComponentStatus:
    """Get installation status of klipper-5axis."""
    files = [SYSTEMD.joinpath(KLIPPER_5AXIS_SERVICE_NAME)]
    return get_install_status(KLIPPER_5AXIS_DIR, files=files)

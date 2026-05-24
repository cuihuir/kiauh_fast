"""Moonraker Tope component - Install, update, remove functions."""
from __future__ import annotations

import shutil
from pathlib import Path
from subprocess import DEVNULL, PIPE, CalledProcessError, run

from components.moonraker_tope import (
    EXIT_MOONRAKER_TOPE_SETUP,
    MOONRAKER_TOPE_DIR,
    MOONRAKER_TOPE_ENV_DIR,
    MOONRAKER_TOPE_ENV_FILE_NAME,
    MOONRAKER_TOPE_ENV_FILE_TEMPLATE,
    MOONRAKER_TOPE_REPO_URL,
    MOONRAKER_TOPE_REQ_FILE,
    MOONRAKER_TOPE_SERVICE_NAME,
    MOONRAKER_TOPE_SERVICE_TEMPLATE,
    MOONRAKER_TOPE_SPEEDUPS_REQ_FILE,
    MOONRAKER_TOPE_DEPS_JSON_FILE,
    MOONRAKER_TOPE_TAG,
    POLKIT_FILE,
    POLKIT_LEGACY_FILE,
    POLKIT_SCRIPT,
    POLKIT_USR_FILE,
)
from core.constants import CURRENT_USER, SYSTEMD
from core.logger import DialogType, Logger
from core.types.component_status import ComponentStatus
from utils.common import check_install_dependencies, get_install_status
from utils.fs_utils import check_file_exist
from utils.git_utils import git_clone_at_tag, git_pull_wrapper
from utils.input_utils import get_confirm
from utils.sys_utils import (
    cmd_sysctl_service,
    create_python_venv,
    install_python_requirements,
)


def install_moonraker_tope() -> bool:
    """Install Moonraker Tope."""
    Logger.print_status("Installing Moonraker Tope ...")

    if not MOONRAKER_TOPE_TAG:
        Logger.print_error(
            "No tag configured for moonraker_tope in component_versions.json!"
        )
        return False

    # Step 1: Clone at pinned tag
    success = git_clone_at_tag(
        MOONRAKER_TOPE_REPO_URL,
        MOONRAKER_TOPE_DIR,
        MOONRAKER_TOPE_TAG,
    )
    if not success:
        Logger.print_error("Failed to clone moonraker-tope repository!")
        return False

    # Step 2: Install system dependencies
    _install_system_packages()

    # Step 3: Create Python venv and install requirements
    try:
        if create_python_venv(MOONRAKER_TOPE_ENV_DIR, True, False):
            if MOONRAKER_TOPE_REQ_FILE.exists():
                install_python_requirements(MOONRAKER_TOPE_ENV_DIR, MOONRAKER_TOPE_REQ_FILE)
            if MOONRAKER_TOPE_SPEEDUPS_REQ_FILE.exists():
                install_python_requirements(MOONRAKER_TOPE_ENV_DIR, MOONRAKER_TOPE_SPEEDUPS_REQ_FILE)
    except CalledProcessError:
        Logger.print_error("Error installing Moonraker Tope requirements!")
        return False

    # Step 4: Install PolicyKit rules
    _install_polkit()

    # Step 5: Install systemd service
    _install_service()

    Logger.print_ok("Moonraker Tope successfully installed!")
    Logger.print_info(f"Installed at tag: {MOONRAKER_TOPE_TAG}")
    return True


def _install_system_packages() -> None:
    """Install system dependencies from system-dependencies.json."""
    deps_json = MOONRAKER_TOPE_DEPS_JSON_FILE
    if not deps_json.exists():
        Logger.print_info("No system-dependencies.json found, skipping system deps")
        return

    try:
        import json
        import platform

        data = json.loads(deps_json.read_text())
        raw_packages = data.get("debian", []) + data.get("arch", [])

        # Filter out conditional entries like "wireless-tools; distro_id != 'ubuntu'"
        # Only keep plain package names
        packages = []
        for pkg in raw_packages:
            if ";" in str(pkg):
                continue
            packages.append(str(pkg).strip())

        if packages:
            Logger.print_status(f"Installing {len(packages)} system packages ...")
            run(
                ["sudo", "apt-get", "install", "-y", "-qq"] + packages,
                check=True,
                stdout=DEVNULL,
            )
    except (CalledProcessError, json.JSONDecodeError) as e:
        Logger.print_warn(f"Some system packages may have failed: {e}")


def _install_polkit() -> None:
    """Install Moonraker policykit rules."""
    Logger.print_status("Installing Moonraker Tope policykit rules ...")

    legacy_exists = check_file_exist(POLKIT_LEGACY_FILE, True)
    polkit_exists = check_file_exist(POLKIT_FILE, True)
    usr_exists = check_file_exist(POLKIT_USR_FILE, True)

    if legacy_exists or (polkit_exists and usr_exists):
        Logger.print_info("Policykit rules already installed.")
        return

    if not POLKIT_SCRIPT.exists():
        Logger.print_warn("Policykit script not found, skipping")
        return

    try:
        command = [POLKIT_SCRIPT.as_posix(), "--disable-systemctl"]
        result = run(command, stderr=PIPE, stdout=DEVNULL, text=True)
        if result.returncode != 0 or result.stderr:
            Logger.print_error(f"{result.stderr}", False)
            Logger.print_error("Installing policykit rules failed!")
            return
        Logger.print_ok("Policykit rules installed!")
    except CalledProcessError as e:
        Logger.print_error(f"Error installing policykit rules: {e}")


def _install_service() -> None:
    """Install the moonraker-tope systemd service file."""
    try:
        if not MOONRAKER_TOPE_SERVICE_TEMPLATE.exists():
            Logger.print_warn("Service template not found, skipping service installation")
            return

        service_content = MOONRAKER_TOPE_SERVICE_TEMPLATE.read_text()
        service_content = service_content.replace("%USER%", CURRENT_USER)
        service_content = service_content.replace(
            "%MOONRAKER_TOPE_DIR%", MOONRAKER_TOPE_DIR.as_posix()
        )
        service_content = service_content.replace(
            "%ENV%", MOONRAKER_TOPE_ENV_DIR.as_posix()
        )
        service_content = service_content.replace(
            "%ENV_FILE%",
            str(Path.home() / "printer_data" / "systemd" / MOONRAKER_TOPE_ENV_FILE_NAME),
        )

        service_path = SYSTEMD.joinpath(MOONRAKER_TOPE_SERVICE_NAME)
        run(["sudo", "tee", service_path.as_posix()],
            input=service_content.encode(), stdout=DEVNULL, check=True)

        # Write env file
        if MOONRAKER_TOPE_ENV_FILE_TEMPLATE.exists():
            env_content = MOONRAKER_TOPE_ENV_FILE_TEMPLATE.read_text()
            env_content = env_content.replace(
                "%MOONRAKER_TOPE_DIR%", MOONRAKER_TOPE_DIR.as_posix()
            )
            env_content = env_content.replace(
                "%PRINTER_DATA%",
                f"{Path.home()}/printer_data",
            )
            env_dir = Path.home() / "printer_data" / "systemd"
            env_dir.mkdir(parents=True, exist_ok=True)
            env_path = env_dir / MOONRAKER_TOPE_ENV_FILE_NAME
            env_path.write_text(env_content)

        run(["sudo", "systemctl", "daemon-reload"], check=True)
        run(["sudo", "systemctl", "enable", MOONRAKER_TOPE_SERVICE_NAME], check=True)
        Logger.print_ok("Moonraker Tope service installed")
    except (CalledProcessError, OSError) as e:
        Logger.print_error(f"Error installing service: {e}")


def update_moonraker_tope() -> bool:
    """Update Moonraker Tope to the configured tag version."""
    if not MOONRAKER_TOPE_DIR.exists():
        Logger.print_info("Moonraker Tope is not installed. Skipping ...")
        return False

    Logger.print_status("Updating Moonraker Tope ...")

    try:
        cmd_sysctl_service(MOONRAKER_TOPE_SERVICE_NAME, "stop")

        success = git_clone_at_tag(
            MOONRAKER_TOPE_REPO_URL,
            MOONRAKER_TOPE_DIR,
            MOONRAKER_TOPE_TAG,
            force=True,
        )
        if not success:
            Logger.print_error("Failed to update moonraker-tope!")
            return False

        if MOONRAKER_TOPE_REQ_FILE.exists():
            install_python_requirements(MOONRAKER_TOPE_ENV_DIR, MOONRAKER_TOPE_REQ_FILE)
        if MOONRAKER_TOPE_SPEEDUPS_REQ_FILE.exists():
            install_python_requirements(MOONRAKER_TOPE_ENV_DIR, MOONRAKER_TOPE_SPEEDUPS_REQ_FILE)

        cmd_sysctl_service(MOONRAKER_TOPE_SERVICE_NAME, "start")
        Logger.print_ok("Moonraker Tope updated successfully.")
        return True
    except CalledProcessError as e:
        Logger.print_error(f"Error updating Moonraker Tope: {e}")
        return False


def remove_moonraker_tope() -> None:
    """Remove Moonraker Tope installation."""
    if not MOONRAKER_TOPE_DIR.exists():
        Logger.print_info("Moonraker Tope is not installed. Skipping ...")
        return

    Logger.print_status("Removing Moonraker Tope ...")

    try:
        cmd_sysctl_service(MOONRAKER_TOPE_SERVICE_NAME, "stop")
    except CalledProcessError:
        pass

    # Remove service files
    for f in [
        SYSTEMD.joinpath(MOONRAKER_TOPE_SERVICE_NAME),
        Path.home() / "printer_data" / "systemd" / MOONRAKER_TOPE_ENV_FILE_NAME,
    ]:
        if f.exists():
            run(["sudo", "rm", f.as_posix()], check=False)
            Logger.print_info(f"Removed {f}")

    try:
        run(["sudo", "systemctl", "daemon-reload"], check=True)
    except CalledProcessError:
        pass

    # Remove directories
    for d in [MOONRAKER_TOPE_DIR, MOONRAKER_TOPE_ENV_DIR]:
        if d.exists():
            shutil.rmtree(d)
            Logger.print_info(f"Removed {d}")

    Logger.print_ok("Moonraker Tope removed.")


def get_moonraker_tope_status() -> ComponentStatus:
    """Get installation status of moonraker-tope."""
    files = [SYSTEMD.joinpath(MOONRAKER_TOPE_SERVICE_NAME)]
    return get_install_status(MOONRAKER_TOPE_DIR, files=files)

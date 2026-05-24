"""Printer GUI (QML) component - Install, update, remove functions."""
from __future__ import annotations

import shutil
from pathlib import Path
from subprocess import DEVNULL, CalledProcessError, run

from components.printer_gui import (
    EXIT_PRINTER_GUI_SETUP,
    PRINTER_GUI_DIR,
    PRINTER_GUI_ENV_DIR,
    PRINTER_GUI_REPO_URL,
    PRINTER_GUI_REQ_FILE,
    PRINTER_GUI_SERVICE_NAME,
    PRINTER_GUI_EGLFS_SERVICE_NAME,
    PRINTER_GUI_TAG,
)
from core.constants import CURRENT_USER, SYSTEMD
from core.logger import DialogType, Logger
from core.types.component_status import ComponentStatus
from utils.common import check_install_dependencies, get_install_status
from utils.git_utils import git_clone_at_tag, git_pull_wrapper
from utils.input_utils import get_confirm
from utils.sys_utils import cmd_sysctl_service


def install_printer_gui() -> bool:
    """Install Printer GUI (QML)."""
    Logger.print_status("Installing Printer GUI (QML) ...")

    if not PRINTER_GUI_TAG:
        Logger.print_error(
            "No tag configured for printer_gui in component_versions.json!"
        )
        return False

    # Step 1: Clone at pinned tag
    success = git_clone_at_tag(
        PRINTER_GUI_REPO_URL,
        PRINTER_GUI_DIR,
        PRINTER_GUI_TAG,
    )
    if not success:
        Logger.print_error("Failed to clone printer-gui repository!")
        return False

    # Step 2: Install system dependencies from deploy/system-packages.txt
    _install_system_packages()

    # Step 3: Create Python venv and install dependencies
    try:
        venv_python = PRINTER_GUI_ENV_DIR / "bin" / "python"
        venv_pip = PRINTER_GUI_ENV_DIR / "bin" / "pip"

        if not PRINTER_GUI_ENV_DIR.exists():
            Logger.print_status("Creating Python virtual environment ...")
            run(
                ["python3", "-m", "venv", PRINTER_GUI_ENV_DIR.as_posix()],
                check=True,
            )

        # Install PySide6
        Logger.print_status("Installing PySide6 ...")
        run(
            [venv_pip.as_posix(), "install", "-q", "PySide6>=6.5.0"],
            check=True,
        )

        # Install requirements if present
        if PRINTER_GUI_REQ_FILE.exists():
            Logger.print_status("Installing requirements ...")
            run(
                [venv_pip.as_posix(), "install", "-q", "-r", PRINTER_GUI_REQ_FILE.as_posix()],
                check=True,
            )
    except CalledProcessError as e:
        Logger.print_error(f"Error installing Printer GUI dependencies: {e}")
        return False

    # Step 4: Install systemd service
    _install_service()

    Logger.print_ok("Printer GUI successfully installed!")
    Logger.print_info(f"Installed at tag: {PRINTER_GUI_TAG}")
    return True


def _install_system_packages() -> None:
    """Install system packages from deploy/system-packages.txt."""
    pkgs_file = PRINTER_GUI_DIR / "deploy" / "system-packages.txt"
    if not pkgs_file.exists():
        Logger.print_info("No system-packages.txt found, skipping system deps")
        return

    try:
        packages = [
            line.strip()
            for line in pkgs_file.read_text().splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        if packages:
            Logger.print_status(f"Installing {len(packages)} system packages ...")
            run(
                ["sudo", "apt-get", "install", "-y", "-qq"] + packages,
                check=True,
                stdout=DEVNULL,
            )
    except CalledProcessError as e:
        Logger.print_warn(f"Some system packages may have failed: {e}")


def _install_service() -> None:
    """Install printer-gui systemd service (defaults to EGLFS mode)."""
    try:
        # Use EGLFS service by default for embedded displays
        template = PRINTER_GUI_DIR / "deploy" / "printer-gui-eglfs.service"
        if not template.exists():
            template = PRINTER_GUI_DIR / "deploy" / "printer-gui.service"
        if not template.exists():
            Logger.print_warn("No service file found in deploy/, skipping service setup")
            return

        service_content = template.read_text()
        service_content = service_content.replace("%USER%", CURRENT_USER)
        service_content = service_content.replace(
            "%HOME_DIR%", str(Path.home())
        )
        service_content = service_content.replace(
            "%PRINTER_GUI_DIR%", PRINTER_GUI_DIR.as_posix()
        )

        # Determine service name from template
        if "eglfs" in template.name:
            service_name = PRINTER_GUI_EGLFS_SERVICE_NAME
        else:
            service_name = PRINTER_GUI_SERVICE_NAME

        service_path = SYSTEMD.joinpath(service_name)
        run(["sudo", "tee", service_path.as_posix()],
            input=service_content.encode(), stdout=DEVNULL, check=True)

        # Copy start scripts to /usr/local/bin
        for script_name in ["printer-gui-start.sh", "printer-gui-eglfs-start.sh"]:
            script_src = PRINTER_GUI_DIR / "deploy" / script_name
            if script_src.exists():
                script_dst = Path("/usr/local/bin") / script_name
                run(["sudo", "cp", script_src.as_posix(), script_dst.as_posix()], check=True)
                run(["sudo", "chmod", "755", script_dst.as_posix()], check=True)

        run(["sudo", "systemctl", "daemon-reload"], check=True)
        run(["sudo", "systemctl", "enable", service_name], check=True)
        Logger.print_ok(f"Printer GUI service ({service_name}) installed")
    except (CalledProcessError, OSError) as e:
        Logger.print_error(f"Error installing service: {e}")


def update_printer_gui() -> bool:
    """Update Printer GUI to the configured tag version."""
    if not PRINTER_GUI_DIR.exists():
        Logger.print_info("Printer GUI is not installed. Skipping ...")
        return False

    Logger.print_status("Updating Printer GUI ...")

    try:
        # Determine which service is active
        service_name = _get_active_service()
        if service_name:
            cmd_sysctl_service(service_name, "stop")

        success = git_clone_at_tag(
            PRINTER_GUI_REPO_URL,
            PRINTER_GUI_DIR,
            PRINTER_GUI_TAG,
            force=True,
        )
        if not success:
            Logger.print_error("Failed to update printer-gui!")
            return False

        # Reinstall deps
        venv_pip = PRINTER_GUI_ENV_DIR / "bin" / "pip"
        if venv_pip.exists() and PRINTER_GUI_REQ_FILE.exists():
            run(
                [venv_pip.as_posix(), "install", "-q", "-r", PRINTER_GUI_REQ_FILE.as_posix()],
                check=True,
            )

        # Reinstall service (in case template changed)
        _install_service()

        if service_name:
            cmd_sysctl_service(service_name, "start")

        Logger.print_ok("Printer GUI updated successfully.")
        return True
    except CalledProcessError as e:
        Logger.print_error(f"Error updating Printer GUI: {e}")
        return False


def remove_printer_gui() -> None:
    """Remove Printer GUI installation."""
    if not PRINTER_GUI_DIR.exists():
        Logger.print_info("Printer GUI is not installed. Skipping ...")
        return

    Logger.print_status("Removing Printer GUI ...")

    service_name = _get_active_service()
    if service_name:
        try:
            cmd_sysctl_service(service_name, "stop")
        except CalledProcessError:
            pass

    # Remove service files
    for svc in [PRINTER_GUI_SERVICE_NAME, PRINTER_GUI_EGLFS_SERVICE_NAME]:
        svc_path = SYSTEMD.joinpath(svc)
        if svc_path.exists():
            run(["sudo", "rm", svc_path.as_posix()], check=False)
            Logger.print_info(f"Removed {svc_path}")

    # Remove start scripts
    for script in ["printer-gui-start.sh", "printer-gui-eglfs-start.sh"]:
        script_path = Path("/usr/local/bin") / script
        if script_path.exists():
            script_path.unlink()

    try:
        run(["sudo", "systemctl", "daemon-reload"], check=True)
    except CalledProcessError:
        pass

    # Remove directories
    for d in [PRINTER_GUI_DIR, PRINTER_GUI_ENV_DIR]:
        if d.exists():
            shutil.rmtree(d)
            Logger.print_info(f"Removed {d}")

    Logger.print_ok("Printer GUI removed.")


def _get_active_service() -> str | None:
    """Determine which printer-gui service is currently enabled."""
    for svc in [PRINTER_GUI_EGLFS_SERVICE_NAME, PRINTER_GUI_SERVICE_NAME]:
        svc_path = SYSTEMD.joinpath(svc)
        if svc_path.exists():
            return svc
    return None


def get_printer_gui_status() -> ComponentStatus:
    """Get installation status of printer-gui."""
    files = [
        SYSTEMD.joinpath(svc)
        for svc in [PRINTER_GUI_SERVICE_NAME, PRINTER_GUI_EGLFS_SERVICE_NAME]
    ]
    return get_install_status(PRINTER_GUI_DIR, files=files)

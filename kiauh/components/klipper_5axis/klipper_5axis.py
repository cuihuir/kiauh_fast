"""Klipper 5-axis component - Overlay installer.

This component installs the 5-axis overlay ON TOP of an existing Klipper
installation. It does NOT create a separate service - the regular klipper
service runs the patched klipper with 5-axis support.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from subprocess import CalledProcessError, run

from components.klipper_5axis import (
    KLIPPER_5AXIS_DIR,
    KLIPPER_5AXIS_REPO_URL,
    KLIPPER_5AXIS_TAG,
)
from core.logger import DialogType, Logger
from core.types.component_status import ComponentStatus
from utils.common import get_install_status
from utils.git_utils import git_clone_at_tag
from utils.input_utils import get_confirm


OVERLAY_INSTALL_SCRIPT = KLIPPER_5AXIS_DIR / "scripts" / "install_klipper_overlay.sh"
KLIPPER_DIR = Path.home() / "klipper"


def install_klipper_5axis() -> bool:
    """Install Klipper 5-axis overlay on top of existing Klipper."""
    Logger.print_status("Installing Klipper 5-axis overlay ...")

    # Check that regular klipper is installed
    if not KLIPPER_DIR.exists():
        Logger.print_error(
            "Klipper is not installed! Install Klipper first before the 5-axis overlay."
        )
        return False

    if not KLIPPER_5AXIS_TAG:
        Logger.print_error(
            "No tag configured for klipper_5axis in component_versions.json!"
        )
        return False

    # Clone the 5-axis repo at the pinned tag
    success = git_clone_at_tag(
        KLIPPER_5AXIS_REPO_URL,
        KLIPPER_5AXIS_DIR,
        KLIPPER_5AXIS_TAG,
    )
    if not success:
        Logger.print_error("Failed to clone klipper-5axis repository!")
        return False

    # Run the overlay install script
    if not OVERLAY_INSTALL_SCRIPT.exists():
        Logger.print_error(f"Overlay install script not found: {OVERLAY_INSTALL_SCRIPT}")
        return False

    Logger.print_status("Running 5-axis overlay installer ...")
    try:
        result = run(
            ["bash", OVERLAY_INSTALL_SCRIPT.as_posix(), "install"],
            capture_output=True,
            text=True,
            check=True,
        )
        Logger.print_info(result.stdout)
        Logger.print_ok("Klipper 5-axis overlay installed!")
        Logger.print_info(f"Overlay version: {KLIPPER_5AXIS_TAG}")
        Logger.print_info("Restart Klipper to load the 5-axis extensions.")
        return True
    except CalledProcessError as e:
        Logger.print_error(f"Overlay install failed: {e.stderr}")
        return False


def update_klipper_5axis() -> bool:
    """Update Klipper 5-axis overlay to the configured tag version."""
    if not KLIPPER_5AXIS_DIR.exists():
        Logger.print_info("Klipper 5-axis overlay is not installed. Skipping ...")
        return False

    Logger.print_status("Updating Klipper 5-axis overlay ...")

    # Uninstall old overlay first
    _uninstall_overlay()

    # Re-clone at the new tag
    success = git_clone_at_tag(
        KLIPPER_5AXIS_REPO_URL,
        KLIPPER_5AXIS_DIR,
        KLIPPER_5AXIS_TAG,
        force=True,
    )
    if not success:
        Logger.print_error("Failed to update klipper-5axis!")
        return False

    # Re-install overlay
    try:
        result = run(
            ["bash", OVERLAY_INSTALL_SCRIPT.as_posix(), "install"],
            capture_output=True,
            text=True,
            check=True,
        )
        Logger.print_ok("Klipper 5-axis overlay updated successfully.")
        return True
    except CalledProcessError as e:
        Logger.print_error(f"Overlay update failed: {e.stderr}")
        return False


def remove_klipper_5axis() -> None:
    """Remove Klipper 5-axis overlay."""
    if not KLIPPER_5AXIS_DIR.exists():
        Logger.print_info("Klipper 5-axis overlay is not installed. Skipping ...")
        return

    Logger.print_status("Removing Klipper 5-axis overlay ...")
    _uninstall_overlay()

    # Remove the cloned repo
    shutil.rmtree(KLIPPER_5AXIS_DIR)
    Logger.print_ok("Klipper 5-axis overlay removed.")


def _uninstall_overlay() -> None:
    """Run the overlay uninstall script."""
    if not OVERLAY_INSTALL_SCRIPT.exists():
        return
    try:
        run(
            ["bash", OVERLAY_INSTALL_SCRIPT.as_posix(), "uninstall"],
            capture_output=True,
            text=True,
            check=True,
        )
    except CalledProcessError as e:
        Logger.print_warn(f"Overlay uninstall warning: {e.stderr}")


def get_klipper_5axis_status() -> ComponentStatus:
    """Get installation status of klipper-5axis overlay."""
    return get_install_status(KLIPPER_5AXIS_DIR)

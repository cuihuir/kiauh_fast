"""Printer GUI (QML) component - Constants and paths."""
from pathlib import Path

from core.constants import SYSTEMD
from utils.version_config import VersionConfigManager

MODULE_PATH = Path(__file__).resolve().parent

# Load version config
_vcm = VersionConfigManager()
_cfg = _vcm.get_config("printer_gui")

# repo - from component_versions.json
PRINTER_GUI_REPO_URL = _cfg.repo_url if _cfg else "git@github.com:cuihuir/printer-gui-qml.git"
PRINTER_GUI_TAG = _cfg.tag if _cfg else ""

# names
PRINTER_GUI_SERVICE_NAME = "printer-gui.service"
PRINTER_GUI_EGLFS_SERVICE_NAME = "printer-gui-eglfs.service"
PRINTER_GUI_UPDATER_SECTION_NAME = "update_manager printer-gui"

# directories
PRINTER_GUI_DIR = Path.home().joinpath(_cfg.install_dir if _cfg else "printer-gui")
PRINTER_GUI_ENV_DIR = Path.home().joinpath(_cfg.env_dir if _cfg else "printer-gui-env")

# files
PRINTER_GUI_REQ_FILE = PRINTER_GUI_DIR.joinpath("requirements.txt")
PRINTER_GUI_INSTALL_SCRIPT = PRINTER_GUI_DIR.joinpath("deploy/install.sh")
PRINTER_GUI_START_SCRIPT = PRINTER_GUI_DIR.joinpath("deploy/printer-gui-start.sh")
PRINTER_GUI_EGLFS_START_SCRIPT = PRINTER_GUI_DIR.joinpath("deploy/printer-gui-eglfs-start.sh")
PRINTER_GUI_SERVICE_FILE = SYSTEMD.joinpath(PRINTER_GUI_SERVICE_NAME)
PRINTER_GUI_EGLFS_SERVICE_FILE = SYSTEMD.joinpath(PRINTER_GUI_EGLFS_SERVICE_NAME)

EXIT_PRINTER_GUI_SETUP = "Exiting Printer GUI setup ..."

"""Moonraker Tope component - Constants and paths."""
from pathlib import Path

from core.constants import SYSTEMD
from utils.version_config import VersionConfigManager

MODULE_PATH = Path(__file__).resolve().parent

# Load version config
_vcm = VersionConfigManager()
_cfg = _vcm.get_config("moonraker_tope")

# repo - from component_versions.json
MOONRAKER_TOPE_REPO_URL = _cfg.repo_url if _cfg else "https://github.com/cuihuir/moonraker.git"
MOONRAKER_TOPE_TAG = _cfg.tag if _cfg else ""

# names
MOONRAKER_TOPE_CFG_NAME = "moonraker.conf"
MOONRAKER_TOPE_LOG_NAME = "moonraker.log"
MOONRAKER_TOPE_SERVICE_NAME = "moonraker-tope.service"
MOONRAKER_TOPE_DEFAULT_PORT = 7125
MOONRAKER_TOPE_ENV_FILE_NAME = "moonraker-tope.env"

# directories
MOONRAKER_TOPE_DIR = Path.home().joinpath(_cfg.install_dir if _cfg else "moonraker-tope")
MOONRAKER_TOPE_ENV_DIR = Path.home().joinpath(_cfg.env_dir if _cfg else "moonraker-tope-env")

# files
MOONRAKER_TOPE_INSTALL_SCRIPT = MOONRAKER_TOPE_DIR.joinpath("scripts/install-moonraker.sh")
MOONRAKER_TOPE_REQ_FILE = MOONRAKER_TOPE_DIR.joinpath("scripts/moonraker-requirements.txt")
MOONRAKER_TOPE_SPEEDUPS_REQ_FILE = MOONRAKER_TOPE_DIR.joinpath("scripts/moonraker-speedups.txt")
MOONRAKER_TOPE_DEPS_JSON_FILE = MOONRAKER_TOPE_DIR.joinpath("scripts/system-dependencies.json")
MOONRAKER_TOPE_SERVICE_TEMPLATE = MODULE_PATH.joinpath(f"assets/{MOONRAKER_TOPE_SERVICE_NAME}")
MOONRAKER_TOPE_ENV_FILE_TEMPLATE = MODULE_PATH.joinpath(f"assets/{MOONRAKER_TOPE_ENV_FILE_NAME}")

# PolicyKit paths (shared with main moonraker if installed)
POLKIT_LEGACY_FILE = Path("/etc/polkit-1/localauthority/50-local.d/10-moonraker.pkla")
POLKIT_FILE = Path("/etc/polkit-1/rules.d/moonraker.rules")
POLKIT_USR_FILE = Path("/usr/share/polkit-1/rules.d/moonraker.rules")
POLKIT_SCRIPT = MOONRAKER_TOPE_DIR.joinpath("scripts/set-policykit-rules.sh")

EXIT_MOONRAKER_TOPE_SETUP = "Exiting Moonraker Tope setup ..."

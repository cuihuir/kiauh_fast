"""Moonraker Fork component - Constants and paths."""
from pathlib import Path

from core.constants import SYSTEMD
from utils.version_config import VersionConfigManager

MODULE_PATH = Path(__file__).resolve().parent

# Load version config
_vcm = VersionConfigManager()
_cfg = _vcm.get_config("moonraker_fork")

# repo - from component_versions.json
MOONRAKER_FORK_REPO_URL = _cfg.repo_url if _cfg else "https://github.com/cuihuir/moonraker.git"
MOONRAKER_FORK_TAG = _cfg.tag if _cfg else ""

# names
MOONRAKER_FORK_CFG_NAME = "moonraker.conf"
MOONRAKER_FORK_LOG_NAME = "moonraker.log"
MOONRAKER_FORK_SERVICE_NAME = "moonraker-fork.service"
MOONRAKER_FORK_DEFAULT_PORT = 7125
MOONRAKER_FORK_ENV_FILE_NAME = "moonraker-fork.env"

# directories
MOONRAKER_FORK_DIR = Path.home().joinpath(_cfg.install_dir if _cfg else "moonraker-fork")
MOONRAKER_FORK_ENV_DIR = Path.home().joinpath(_cfg.env_dir if _cfg else "moonraker-fork-env")

# files
MOONRAKER_FORK_INSTALL_SCRIPT = MOONRAKER_FORK_DIR.joinpath("scripts/install-moonraker.sh")
MOONRAKER_FORK_REQ_FILE = MOONRAKER_FORK_DIR.joinpath("scripts/moonraker-requirements.txt")
MOONRAKER_FORK_SPEEDUPS_REQ_FILE = MOONRAKER_FORK_DIR.joinpath("scripts/moonraker-speedups.txt")
MOONRAKER_FORK_DEPS_JSON_FILE = MOONRAKER_FORK_DIR.joinpath("scripts/system-dependencies.json")
MOONRAKER_FORK_SERVICE_TEMPLATE = MODULE_PATH.joinpath(f"assets/{MOONRAKER_FORK_SERVICE_NAME}")
MOONRAKER_FORK_ENV_FILE_TEMPLATE = MODULE_PATH.joinpath(f"assets/{MOONRAKER_FORK_ENV_FILE_NAME}")

# PolicyKit paths (shared with main moonraker if installed)
POLKIT_LEGACY_FILE = Path("/etc/polkit-1/localauthority/50-local.d/10-moonraker.pkla")
POLKIT_FILE = Path("/etc/polkit-1/rules.d/moonraker.rules")
POLKIT_USR_FILE = Path("/usr/share/polkit-1/rules.d/moonraker.rules")
POLKIT_SCRIPT = MOONRAKER_FORK_DIR.joinpath("scripts/set-policykit-rules.sh")

EXIT_MOONRAKER_FORK_SETUP = "Exiting Moonraker Fork setup ..."

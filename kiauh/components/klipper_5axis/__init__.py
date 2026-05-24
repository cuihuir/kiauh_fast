"""Klipper 5-axis overlay component - Constants and paths."""
from pathlib import Path

from utils.version_config import VersionConfigManager

# Load version config
_vcm = VersionConfigManager()
_cfg = _vcm.get_config("klipper_5axis")

# repo - from component_versions.json
KLIPPER_5AXIS_REPO_URL = _cfg.repo_url if _cfg else "git@github.com:cuihuir/5-axis.git"
KLIPPER_5AXIS_TAG = _cfg.tag if _cfg else ""

# directories
KLIPPER_5AXIS_DIR = Path.home().joinpath(_cfg.install_dir if _cfg else "klipper-5axis")

"""Klipper 5-axis component - Constants and paths."""
from pathlib import Path

from utils.version_config import VersionConfigManager

MODULE_PATH = Path(__file__).resolve().parent

_vcm = VersionConfigManager()
_cfg = _vcm.get_config("klipper_5axis")

KLIPPER_5AXIS_REPO_URL = _cfg.repo_url if _cfg else "git@github.com:cuihuir/5-axis.git"
KLIPPER_5AXIS_TAG = _cfg.tag if _cfg else ""

# names
KLIPPER_5AXIS_LOG_NAME = "klippy.log"
KLIPPER_5AXIS_CFG_NAME = "printer.cfg"
KLIPPER_5AXIS_SERIAL_NAME = "klippy.serial"
KLIPPER_5AXIS_UDS_NAME = "klippy.sock"
KLIPPER_5AXIS_ENV_FILE_NAME = "klipper-5axis.env"
KLIPPER_5AXIS_SERVICE_NAME = "klipper-5axis.service"

# directories
KLIPPER_5AXIS_DIR = Path.home().joinpath(_cfg.install_dir if _cfg else "klipper-5axis")
KLIPPER_5AXIS_ENV_DIR = Path.home().joinpath(_cfg.env_dir if _cfg else "klipper-5axis-env")

# files
KLIPPER_5AXIS_REQ_FILE = KLIPPER_5AXIS_DIR.joinpath("scripts/klippy-requirements.txt")
KLIPPER_5AXIS_SERVICE_TEMPLATE = MODULE_PATH.joinpath("assets/klipper-5axis.service")
KLIPPER_5AXIS_ENV_FILE_TEMPLATE = MODULE_PATH.joinpath("assets/klipper-5axis.env")

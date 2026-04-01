# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import platform
import subprocess
from pathlib import Path

from core.constants import SYSTEMD

# repo
GO2RTC_REPO = "https://github.com/AlexxIT/go2rtc.git"
GO2RTC_RELEASES_URL = "https://github.com/AlexxIT/go2rtc/releases/latest/download"

# names
GO2RTC_SERVICE_NAME = "go2rtc.service"

# directories
GO2RTC_DIR = Path.home().joinpath("go2rtc")
GO2RTC_BIN_DIR = Path("/usr/local/bin")
GO2RTC_CONFIG_DIR = Path.home().joinpath("printer_data/config")

# files
GO2RTC_BIN_FILE = GO2RTC_BIN_DIR.joinpath("go2rtc")
GO2RTC_CONFIG_FILE = GO2RTC_CONFIG_DIR.joinpath("go2rtc.yaml")
GO2RTC_SERVICE_FILE = SYSTEMD.joinpath(GO2RTC_SERVICE_NAME)

# architecture mapping
ARCH_MAP = {
    "x86_64": "linux_amd64",
    "amd64": "linux_amd64",
    "i386": "linux_i386",
    "i686": "linux_i386",
    "aarch64": "linux_arm64",
    "arm64": "linux_arm64",
    "armv7l": "linux_arm",
    "armv6l": "linux_armv6",
    "mips": "linux_mipsel",
    "mipsel": "linux_mipsel",
}


def get_go2rtc_arch() -> str:
    """
    Detect system architecture and return the appropriate go2rtc binary name.
    Returns the binary filename without extension.
    """
    machine = platform.machine().lower()

    # Map platform.machine() to go2rtc binary naming convention
    arch = ARCH_MAP.get(machine)

    if arch is None:
        # Try to get more detailed architecture info
        try:
            uname_output = (
                subprocess.check_output(["uname", "-m"], text=True).strip().lower()
            )
            arch = ARCH_MAP.get(uname_output)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    if arch is None:
        raise ValueError(f"Unsupported architecture: {machine}")

    return f"go2rtc_{arch}"


def get_go2rtc_download_url() -> str:
    """
    Get the download URL for the latest go2rtc binary.
    """
    binary_name = get_go2rtc_arch()
    return f"{GO2RTC_RELEASES_URL}/{binary_name}"

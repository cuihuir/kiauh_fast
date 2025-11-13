# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
import io
import sys

from core.logger import Logger
from core.menus.main_menu import MainMenu
from core.settings.kiauh_settings import KiauhSettings


def ensure_encoding() -> None:
    if sys.stdout.encoding == "UTF-8" or not isinstance(sys.stdout, io.TextIOWrapper):
        return
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    try:
        settings = KiauhSettings()
        ensure_encoding()

        # First-run China network detection - simple prompt
        if (
            settings.kiauh.auto_detect_china_network
            and not settings.kiauh.mirror_wizard_completed
        ):
            from utils.china_mirrors import detect_china_network

            if detect_china_network():
                Logger.print_status("\n" + "═" * 60)
                Logger.print_status("Detected China network environment")
                Logger.print_status("检测到中国大陆网络环境")
                Logger.print_status("═" * 60)
                Logger.print_info(
                    "\nFor faster installation, please use option 2 (Mirror Acceleration)"
                )
                Logger.print_info("为了更快的安装速度，请使用选项 2（镜像加速）\n")
                Logger.print_status("─" * 60 + "\n")

                # Mark as shown (don't show again)
                settings.kiauh.mirror_wizard_completed = True
                settings.save()

        MainMenu().run()
    except KeyboardInterrupt:
        Logger.print_ok("\nHappy printing!\n", prefix=False)


if __name__ == "__main__":
    main()

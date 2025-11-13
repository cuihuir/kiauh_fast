# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
"""镜像加速设置菜单"""
from __future__ import annotations

import textwrap
from typing import Type

from core.menus import FooterType
from core.menus.base_menu import BaseMenu, Option, clear
from core.logger import Logger
from core.types.color import Color
from utils.china_mirrors import (
    setup_china_mirrors,
    check_mirror_status,
    restore_default_mirrors,
    show_apt_mirror_guide,
    show_git_acceleration_guide,
)


class MirrorMenu(BaseMenu):
    """镜像加速设置菜单"""

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        self.previous_menu = previous_menu

    def set_options(self) -> None:
        self.options = {
            "1": Option(method=self.setup_mirrors),
            "2": Option(method=self.show_status),
            "3": Option(method=self.show_apt_guide),
            "4": Option(method=self.show_git_guide),
            "5": Option(method=self.restore_defaults),
        }

    def print_menu(self) -> None:
        header = " [ 镜像加速设置 / Mirror Acceleration ] "
        count = 62 - len(str(Color.CYAN)) - len(str(Color.RST))

        menu = textwrap.dedent(
            f"""
            ╔═══════════════════════════════════════════════════════╗
            ║ {Color.apply(f"{header:^{count}}", Color.CYAN)} ║
            ╠═══════════════════════════════════════════════════════╣
            ║  1) 配置镜像加速                                        ║
            ║     Setup Mirror Acceleration                         ║
            ║                                                       ║
            ║  2) 查看镜像状态                                        ║
            ║     View Mirror Status                                ║
            ║                                                       ║
            ║  3) APT 镜像切换指南                                    ║
            ║     APT Mirror Switch Guide                           ║
            ║                                                       ║
            ║  4) Git 加速方法指南                                    ║
            ║     Git Acceleration Guide                            ║
            ║                                                       ║
            ║  5) 恢复默认源                                          ║
            ║     Restore Default Sources                           ║
            ╠═══════════════════════════════════════════════════════╣
            """
        )[1:]
        print(menu, end="")

    def setup_mirrors(self, **kwargs) -> None:
        """配置镜像加速"""
        clear()
        setup_china_mirrors()
        input("\nPress Enter to continue...")

    def show_status(self, **kwargs) -> None:
        """显示镜像状态"""
        clear()
        Logger.print_status("当前镜像配置状态 / Current Mirror Status\n")

        status = check_mirror_status()

        Logger.print_info("─" * 60)
        Logger.print_info(f"pip 镜像 / pip mirror:")
        Logger.print_info(f"  {status.get('pip', 'Unknown')}")
        Logger.print_info("")
        Logger.print_info(f"uv 镜像 / uv mirror:")
        Logger.print_info(f"  {status.get('uv', 'Unknown')}")
        Logger.print_info("─" * 60)

        input("\nPress Enter to continue...")

    def show_apt_guide(self, **kwargs) -> None:
        """显示 APT 镜像指南"""
        clear()
        show_apt_mirror_guide()
        input("\nPress Enter to continue...")

    def show_git_guide(self, **kwargs) -> None:
        """显示 Git 加速指南"""
        clear()
        show_git_acceleration_guide()
        input("\nPress Enter to continue...")

    def restore_defaults(self, **kwargs) -> None:
        """恢复默认源"""
        clear()
        from utils.input_utils import get_confirm

        if get_confirm(
            "确认恢复默认源？这将移除所有镜像配置。\n"
            "Restore default sources? This will remove all mirror configurations.",
            default_choice=False,
        ):
            restore_default_mirrors()
        else:
            Logger.print_info("操作已取消 / Operation cancelled")

        input("\nPress Enter to continue...")

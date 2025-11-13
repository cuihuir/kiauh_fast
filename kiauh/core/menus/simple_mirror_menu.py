# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
#  ======================================================================= #
"""Simple Mirror Menu - Simplified mirror acceleration for main menu"""
from __future__ import annotations

import textwrap
from typing import Type

from core.menus import FooterType
from core.menus.base_menu import BaseMenu, Option, clear
from core.logger import Logger
from core.types.color import Color


class SimpleMirrorMenu(BaseMenu):
    """简化的镜像加速菜单 - 用于主页"""

    def __init__(self, previous_menu: Type[BaseMenu] | None = None) -> None:
        super().__init__()
        self.title = "Mirror Acceleration / 镜像加速"
        self.title_color = Color.CYAN
        self.footer_type = FooterType.BACK
        self.previous_menu = previous_menu

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from core.menus.main_menu import MainMenu

        self.previous_menu = previous_menu if previous_menu is not None else MainMenu

    def set_options(self) -> None:
        self.options = {
            "1": Option(method=self.quick_setup),
            "2": Option(method=self.view_status),
            "3": Option(method=self.restore_defaults),
        }

    def print_menu(self) -> None:
        menu = textwrap.dedent(
            """
            ╟───────────────────────────────────────────────────────╢
            ║  1) Quick Setup China Mirrors                         ║
            ║     一键配置中国镜像                                    ║
            ║                                                       ║
            ║  2) View Mirror Status                                ║
            ║     查看镜像状态                                        ║
            ║                                                       ║
            ║  3) Restore Default Sources                           ║
            ║     恢复默认源                                          ║
            ╟───────────────────────────────────────────────────────╢
            """
        )[1:]
        print(menu, end="")

    def quick_setup(self, **kwargs) -> None:
        """一键配置中国镜像"""
        clear()

        Logger.print_status("═" * 60)
        Logger.print_status("Quick Setup China Mirrors / 一键配置中国镜像")
        Logger.print_status("═" * 60 + "\n")

        Logger.print_info("This will configure:")
        Logger.print_info("将配置以下镜像：\n")
        Logger.print_info("  ✓ PyPI mirror (清华源) - Python packages")
        Logger.print_info("  ✓ APT mirror (清华源) - System packages")
        Logger.print_info("  ✓ uv mirror (if installed)")
        Logger.print_info("")
        Logger.print_info("Expected speedup / 预期加速效果: 10-50x faster\n")

        from utils.input_utils import get_confirm

        if not get_confirm(
            "Continue with quick setup? / 继续快速配置？", default_choice=True
        ):
            Logger.print_info("Setup cancelled / 配置已取消")
            input("\nPress Enter to continue...")
            return

        # 执行快速配置
        from utils.china_mirrors import quick_setup_china_mirrors

        success = quick_setup_china_mirrors()

        if success:
            Logger.print_ok("\n" + "═" * 60)
            Logger.print_ok("✓ Mirrors configured successfully!")
            Logger.print_ok("✓ 镜像配置成功！")
            Logger.print_ok("═" * 60)
        else:
            Logger.print_error("\n✗ Mirror setup failed")
            Logger.print_error("✗ 镜像配置失败")

        input("\nPress Enter to continue...")

    def view_status(self, **kwargs) -> None:
        """查看镜像状态"""
        clear()

        Logger.print_status("═" * 60)
        Logger.print_status("Mirror Status / 镜像状态")
        Logger.print_status("═" * 60 + "\n")

        from utils.china_mirrors import check_mirror_status

        status = check_mirror_status()

        Logger.print_info("PyPI Mirror / PyPI 镜像:")
        Logger.print_info(f"  {status.get('pip', 'Not configured')}")
        Logger.print_info("")

        Logger.print_info("uv Mirror / uv 镜像:")
        Logger.print_info(f"  {status.get('uv', 'Not configured')}")
        Logger.print_info("")

        Logger.print_info("APT Mirror / APT 镜像:")
        Logger.print_info("  Check /etc/apt/sources.list")
        Logger.print_info("  查看 /etc/apt/sources.list")

        Logger.print_status("\n" + "═" * 60)

        input("\nPress Enter to continue...")

    def restore_defaults(self, **kwargs) -> None:
        """恢复默认源"""
        clear()

        Logger.print_status("═" * 60)
        Logger.print_status("Restore Default Sources / 恢复默认源")
        Logger.print_status("═" * 60 + "\n")

        Logger.print_info("This will remove all mirror configurations.")
        Logger.print_info("这将移除所有镜像配置。\n")

        from utils.input_utils import get_confirm

        if not get_confirm(
            "Confirm restore defaults? / 确认恢复默认？", default_choice=False
        ):
            Logger.print_info("Operation cancelled / 操作已取消")
            input("\nPress Enter to continue...")
            return

        from utils.china_mirrors import restore_default_mirrors

        success = restore_default_mirrors()

        if success:
            Logger.print_ok("\n✓ Defaults restored successfully!")
            Logger.print_ok("✓ 默认配置已恢复！")
        else:
            Logger.print_error("\n✗ Restore failed")
            Logger.print_error("✗ 恢复失败")

        input("\nPress Enter to continue...")

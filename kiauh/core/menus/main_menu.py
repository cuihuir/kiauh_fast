# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
#  ======================================================================= #
from __future__ import annotations

import sys
import textwrap
from typing import Type

from core.logger import Logger
from core.menus import FooterType
from core.menus.base_menu import BaseMenu, Option
from core.types.color import Color
from utils.common import get_kiauh_version


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class MainMenu(BaseMenu):
    """Simplified Main Menu with three core options"""

    def __init__(self) -> None:
        super().__init__()

        self.header: bool = True
        self.title = "KIAUH Fast - Main Menu"
        self.title_color = Color.CYAN
        self.footer_type: FooterType = FooterType.QUIT

        self.version = ""

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        """MainMenu does not have a previous menu"""
        pass

    def set_options(self) -> None:
        self.options = {
            "1": Option(method=self.quick_install_menu),
            "2": Option(method=self.mirror_acceleration_menu),
            "3": Option(method=self.manual_install_menu),
        }

    def _init_status(self) -> None:
        status_vars = ["kl", "mr", "ms", "fl", "ks", "cn"]
        for var in status_vars:
            setattr(
                self,
                f"{var}_status",
                Color.apply("Not installed", Color.RED),
            )

    def _fetch_status(self) -> None:
        self.version = get_kiauh_version()
        self._get_component_status("kl", get_klipper_status)
        self._get_component_status("mr", get_moonraker_status)
        self._get_component_status("ms", get_client_status, MainsailData())
        self._get_component_status("fl", get_client_status, FluiddData())
        self._get_component_status("ks", get_klipperscreen_status)
        self._get_component_status("cn", get_crowsnest_status)
        self.cc_status = get_current_client_config()

    def _get_component_status(self, name: str, status_fn: Callable, *args) -> None:
        status_data: ComponentStatus = status_fn(*args)
        code: int = status_data.status
        status: StatusText = StatusMap[code]
        owner: str = trunc_string(status_data.owner, 23) if status_data.owner else '-'
        repo: str = trunc_string(status_data.repo, 23) if status_data.repo else '-'
        instance_count: int = status_data.instances

        count_txt: str = ""
        if instance_count > 0 and code == 2:
            count_txt = f": {instance_count}"

        setattr(self, f"{name}_status", self._format_by_code(code, status, count_txt))
        setattr(self, f"{name}_owner", Color.apply(owner, Color.CYAN))
        setattr(self, f"{name}_repo", Color.apply(repo, Color.CYAN))

    def _format_by_code(self, code: int, status: str, count: str) -> str:
        color = Color.RED
        if code == 0:
            color = Color.RED
        elif code == 1:
            color = Color.YELLOW
        elif code == 2:
            color = Color.GREEN

        return Color.apply(f"{status}{count}", color)

    def print_menu(self) -> None:
        self.version = get_kiauh_version()
        footer1 = Color.apply(self.version, Color.CYAN)
        link = Color.apply("https://git.io/JnmlX", Color.MAGENTA)
        footer2 = f"Changelog: {link}"

        menu = textwrap.dedent(
            f"""
            ╟───────────────────────────────────────────────────────╢
            ║                                                       ║
            ║  1) Quick Install Klipper Stack                       ║
            ║     一键安装 Klipper 全家桶                            ║
            ║                                                       ║
            ║     → Select components with checkboxes               ║
            ║     → Fully automated installation                    ║
            ║     → No manual intervention (except sudo password)   ║
            ║                                                       ║
            ╟───────────────────────────────────────────────────────╢
            ║                                                       ║
            ║  2) Mirror Acceleration                               ║
            ║     镜像加速                                            ║
            ║                                                       ║
            ║     → Configure China mirrors for faster downloads    ║
            ║     → PyPI, APT, uv mirrors                           ║
            ║     → 10-50x faster installation speed                ║
            ║                                                       ║
            ╟───────────────────────────────────────────────────────╢
            ║                                                       ║
            ║  3) Manual Installation                               ║
            ║     手工安装                                            ║
            ║                                                       ║
            ║     → Original KIAUH menu                             ║
            ║     → Step-by-step installation                       ║
            ║     → Full control over each component                ║
            ║                                                       ║
            ╟───────────────────────────────────────────────────────╢
            ║ {footer1:^25} │ {footer2:^28} ║
            ╟───────────────────────────────────────────────────────╢
            """
        )[1:]
        print(menu, end="")

    def exit(self, **kwargs) -> None:
        Logger.print_ok("###### Happy printing!", False)
        sys.exit(0)

    def quick_install_menu(self, **kwargs) -> None:
        """快速安装菜单"""
        from core.menus.quick_install_menu import QuickInstallMenu

        QuickInstallMenu(previous_menu=self.__class__).run()

    def mirror_acceleration_menu(self, **kwargs) -> None:
        """镜像加速菜单"""
        from core.menus.simple_mirror_menu import SimpleMirrorMenu

        SimpleMirrorMenu(previous_menu=self.__class__).run()

    def manual_install_menu(self, **kwargs) -> None:
        """手工安装菜单"""
        from core.menus.manual_install_menu import ManualInstallMenu

        ManualInstallMenu(previous_menu=self.__class__).run()

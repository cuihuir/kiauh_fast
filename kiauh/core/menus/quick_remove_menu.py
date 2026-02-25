# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
#  ======================================================================= #
"""Quick Remove Menu - One-click Klipper Stack Removal"""
from __future__ import annotations

import textwrap
from typing import Dict, Type

from core.logger import DialogType, Logger
from core.menus import FooterType
from core.menus.base_menu import BaseMenu, Option
from core.types.color import Color
from utils.instance_utils import get_instances


class QuickRemoveMenu(BaseMenu):
    """一键卸载菜单 - 通过复选框选择组件批量卸载"""

    def __init__(self, previous_menu: Type[BaseMenu] | None = None) -> None:
        super().__init__()
        self.title = "Quick Remove / 一键卸载"
        self.title_color = Color.RED
        self.footer_type = FooterType.BACK
        self.previous_menu = previous_menu

        self.selections: Dict[str, bool] = {
            "klipper": False,
            "moonraker": False,
            "mainsail": False,
            "fluidd": False,
            "klipperscreen": False,
            "crowsnest": False,
        }

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from core.menus.main_menu import MainMenu

        self.previous_menu = previous_menu if previous_menu is not None else MainMenu

    def set_options(self) -> None:
        self.options = {
            "1": Option(method=self.toggle_klipper),
            "2": Option(method=self.toggle_moonraker),
            "3": Option(method=self.toggle_mainsail),
            "4": Option(method=self.toggle_fluidd),
            "5": Option(method=self.toggle_klipperscreen),
            "6": Option(method=self.toggle_crowsnest),
            "a": Option(method=self.select_all),
            "c": Option(method=self.clear_all),
            "s": Option(method=self.start_removal),
        }

    def print_menu(self) -> None:
        from components.crowsnest import CROWSNEST_DIR
        from components.klipper.klipper import Klipper
        from components.klipperscreen import KLIPPERSCREEN_DIR
        from components.moonraker.moonraker import Moonraker
        from components.webui_client.fluidd_data import FluiddData
        from components.webui_client.mainsail_data import MainsailData

        checked = f"[{Color.apply('x', Color.RED)}]"
        unchecked = "[ ]"

        o1 = checked if self.selections["klipper"] else unchecked
        o2 = checked if self.selections["moonraker"] else unchecked
        o3 = checked if self.selections["mainsail"] else unchecked
        o4 = checked if self.selections["fluidd"] else unchecked
        o5 = checked if self.selections["klipperscreen"] else unchecked
        o6 = checked if self.selections["crowsnest"] else unchecked

        kl_inst = Color.apply(" ✓已装", Color.CYAN) if get_instances(Klipper) else Color.apply(" ✗未装", Color.RED)
        mr_inst = Color.apply(" ✓已装", Color.CYAN) if get_instances(Moonraker) else Color.apply(" ✗未装", Color.RED)
        ms_inst = Color.apply(" ✓已装", Color.CYAN) if MainsailData().client_dir.exists() else Color.apply(" ✗未装", Color.RED)
        fl_inst = Color.apply(" ✓已装", Color.CYAN) if FluiddData().client_dir.exists() else Color.apply(" ✗未装", Color.RED)
        ks_inst = Color.apply(" ✓已装", Color.CYAN) if KLIPPERSCREEN_DIR.exists() else Color.apply(" ✗未装", Color.RED)
        cn_inst = Color.apply(" ✓已装", Color.CYAN) if CROWSNEST_DIR.exists() else Color.apply(" ✗未装", Color.RED)

        menu = textwrap.dedent(
            f"""
            ╟───────────────────────────────────────────────────────╢
            ║ Select components to remove (toggle with number):     ║
            ║ 选择要卸载的组件（输入数字切换）:                              ║
            ╟───────────────────────────────────────────────────────╢
            ║ 1) {o1} Klipper        {kl_inst:<30}║
            ║ 2) {o2} Moonraker      {mr_inst:<30}║
            ║ 3) {o3} Mainsail       {ms_inst:<30}║
            ║ 4) {o4} Fluidd         {fl_inst:<30}║
            ║ 5) {o5} KlipperScreen  {ks_inst:<30}║
            ║ 6) {o6} Crowsnest      {cn_inst:<30}║
            ╟───────────────────────────────────────────────────────╢
            ║  A) Select All / 全选    C) Clear All / 清除            ║
            ╟───────────────────────────────────────────────────────╢
            ║  S) Start Removal / 开始卸载                            ║
            ╟───────────────────────────────────────────────────────╢
            """
        )[1:]
        print(menu, end="")

    def toggle_klipper(self, **kwargs) -> None:
        self.selections["klipper"] = not self.selections["klipper"]

    def toggle_moonraker(self, **kwargs) -> None:
        self.selections["moonraker"] = not self.selections["moonraker"]

    def toggle_mainsail(self, **kwargs) -> None:
        self.selections["mainsail"] = not self.selections["mainsail"]

    def toggle_fluidd(self, **kwargs) -> None:
        self.selections["fluidd"] = not self.selections["fluidd"]

    def toggle_klipperscreen(self, **kwargs) -> None:
        self.selections["klipperscreen"] = not self.selections["klipperscreen"]

    def toggle_crowsnest(self, **kwargs) -> None:
        self.selections["crowsnest"] = not self.selections["crowsnest"]

    def select_all(self, **kwargs) -> None:
        for key in self.selections:
            self.selections[key] = True

    def clear_all(self, **kwargs) -> None:
        for key in self.selections:
            self.selections[key] = False

    def start_removal(self, **kwargs) -> None:
        if not any(self.selections.values()):
            print(Color.apply("Nothing selected! / 未选择任何组件！", Color.RED))
            return

        selected = [k for k, v in self.selections.items() if v]
        Logger.print_dialog(
            DialogType.ATTENTION,
            [
                "The following components will be removed:",
                "以下组件将被卸载：",
                "",
                *[f"  ● {c.capitalize()}" for c in selected],
                "",
                "⚠ This action cannot be undone! / 此操作不可撤销！",
            ],
        )

        from utils.input_utils import get_confirm
        if not get_confirm(
            "Proceed with removal? / 确认卸载？",
            default_choice=False,
            allow_go_back=True,
        ):
            return

        self._execute_removal()
        self.clear_all()

    def _execute_removal(self) -> None:
        # 卸载顺序与安装相反
        if self.selections["klipperscreen"]:
            self._remove_component("KlipperScreen", self._remove_klipperscreen)

        if self.selections["crowsnest"]:
            self._remove_component("Crowsnest", self._remove_crowsnest)

        if self.selections["fluidd"]:
            self._remove_component("Fluidd", self._remove_fluidd)

        if self.selections["mainsail"]:
            self._remove_component("Mainsail", self._remove_mainsail)

        if self.selections["moonraker"]:
            self._remove_component("Moonraker", self._remove_moonraker)

        if self.selections["klipper"]:
            self._remove_component("Klipper", self._remove_klipper)

        Logger.print_ok("Removal completed! / 卸载完成！", end="\n\n")

    def _remove_component(self, name: str, remove_fn) -> None:
        Logger.print_status(f"Removing {name} ...")
        try:
            remove_fn()
        except Exception as e:
            Logger.print_error(f"Error removing {name}: {e}")

    def _remove_klipper(self) -> None:
        from components.klipper.klipper import Klipper
        from components.klipper.services.klipper_setup_service import (
            KlipperSetupService,
        )

        if not get_instances(Klipper):
            Logger.print_info("Klipper is not installed, skipping... / Klipper 未安装，跳过...")
            return

        KlipperSetupService().remove(
            remove_service=True,
            remove_dir=True,
            remove_env=True,
        )

    def _remove_moonraker(self) -> None:
        from components.moonraker.moonraker import Moonraker
        from components.moonraker.services.moonraker_setup_service import (
            MoonrakerSetupService,
        )

        if not get_instances(Moonraker):
            Logger.print_info("Moonraker is not installed, skipping... / Moonraker 未安装，跳过...")
            return

        MoonrakerSetupService().remove(
            remove_service=True,
            remove_dir=True,
            remove_env=True,
            remove_polkit=True,
        )

    def _remove_mainsail(self) -> None:
        from components.webui_client.client_remove import run_client_removal
        from components.webui_client.mainsail_data import MainsailData

        client = MainsailData()
        if not client.client_dir.exists():
            Logger.print_info("Mainsail is not installed, skipping... / Mainsail 未安装，跳过...")
            return

        run_client_removal(
            client=client,
            remove_client=True,
            remove_client_cfg=True,
            backup_config=False,
        )

    def _remove_fluidd(self) -> None:
        from components.webui_client.client_remove import run_client_removal
        from components.webui_client.fluidd_data import FluiddData

        client = FluiddData()
        if not client.client_dir.exists():
            Logger.print_info("Fluidd is not installed, skipping... / Fluidd 未安装，跳过...")
            return

        run_client_removal(
            client=client,
            remove_client=True,
            remove_client_cfg=True,
            backup_config=False,
        )

    def _remove_klipperscreen(self) -> None:
        from components.klipperscreen import KLIPPERSCREEN_DIR
        from components.klipperscreen.klipperscreen import remove_klipperscreen

        if not KLIPPERSCREEN_DIR.exists():
            Logger.print_info("KlipperScreen is not installed, skipping... / KlipperScreen 未安装，跳过...")
            return

        remove_klipperscreen()

    def _remove_crowsnest(self) -> None:
        from components.crowsnest import CROWSNEST_DIR
        from components.crowsnest.crowsnest import remove_crowsnest

        if not CROWSNEST_DIR.exists():
            Logger.print_info("Crowsnest is not installed, skipping... / Crowsnest 未安装，跳过...")
            return

        remove_crowsnest()

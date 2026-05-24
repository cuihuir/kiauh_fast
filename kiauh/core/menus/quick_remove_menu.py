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
            "klipper_5axis": False,
            "moonraker_tope": False,
            "printer_gui": False,
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
            "7": Option(method=self.toggle_klipper_5axis),
            "8": Option(method=self.toggle_moonraker_tope),
            "9": Option(method=self.toggle_printer_gui),
            "a": Option(method=self.select_all),
            "c": Option(method=self.clear_all),
            "s": Option(method=self.start_removal),
        }

    def print_menu(self) -> None:
        from components.crowsnest.crowsnest import get_crowsnest_status
        from components.klipper.klipper import Klipper
        from components.klipperscreen.klipperscreen import get_klipperscreen_status
        from components.moonraker.moonraker import Moonraker
        from components.webui_client.client_utils import get_client_status
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
        o7 = checked if self.selections["klipper_5axis"] else unchecked
        o8 = checked if self.selections["moonraker_tope"] else unchecked
        o9 = checked if self.selections["printer_gui"] else unchecked

        def status_tag(s: int) -> str:
            if s == 2:
                return Color.apply(" ✓已装", Color.CYAN)
            elif s == 1:
                return Color.apply(" ~不完整", Color.YELLOW)
            return Color.apply(" ✗未装", Color.RED)

        kl_inst = status_tag(2 if get_instances(Klipper) else 0)
        mr_inst = status_tag(2 if get_instances(Moonraker) else 0)
        ms_inst = status_tag(get_client_status(MainsailData()).status)
        fl_inst = status_tag(get_client_status(FluiddData()).status)
        ks_inst = status_tag(get_klipperscreen_status().status)
        cn_inst = status_tag(get_crowsnest_status().status)

        from components.klipper_5axis.klipper_5axis import get_klipper_5axis_status
        from components.moonraker_tope.moonraker_tope import get_moonraker_tope_status
        from components.printer_gui.printer_gui import get_printer_gui_status

        k5axis_inst = status_tag(get_klipper_5axis_status().status)
        mrfork_inst = status_tag(get_moonraker_tope_status().status)
        pgui_inst = status_tag(get_printer_gui_status().status)

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
            ║ 7) {o7} Klipper 5-axis {k5axis_inst:<30}║
            ║ 8) {o8} Moonraker Tope {mrfork_inst:<30}║
            ║ 9) {o9} Printer GUI    {pgui_inst:<30}║
            ╟───────────────────────────────────────────────────────╢
            ║ Tip: Enter multiple numbers (e.g., 125 or 1 2 5)    ║
            ║ 提示: 可输入多个数字 (如 125 或 1 2 5)                 ║
            ║                                                       ║
            ║ A) Select All / 全选    C) Clear All / 清除            ║
            ║ S) Start Removal / 开始卸载                            ║
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

    def toggle_klipper_5axis(self, **kwargs) -> None:
        self.selections["klipper_5axis"] = not self.selections["klipper_5axis"]

    def toggle_moonraker_tope(self, **kwargs) -> None:
        self.selections["moonraker_tope"] = not self.selections["moonraker_tope"]

    def toggle_printer_gui(self, **kwargs) -> None:
        self.selections["printer_gui"] = not self.selections["printer_gui"]

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
        from components.klipper import KLIPPER_DIR, KLIPPER_ENV_DIR
        from components.klipper.klipper import Klipper
        from core.instance_manager.instance_manager import InstanceManager
        from utils.fs_utils import run_remove_routines

        instances = get_instances(Klipper)
        if not instances:
            Logger.print_info("Klipper is not installed, skipping... / Klipper 未安装，跳过...")
            return

        Logger.print_status("Removing Klipper instances ...")
        for instance in instances:
            InstanceManager.remove(instance)

        Logger.print_status("Removing Klipper local repository ...")
        run_remove_routines(KLIPPER_DIR)
        Logger.print_status("Removing Klipper Python environment ...")
        run_remove_routines(KLIPPER_ENV_DIR)
        Logger.print_ok("Klipper removed")

    def _remove_moonraker(self) -> None:
        from components.moonraker import MOONRAKER_DIR, MOONRAKER_ENV_DIR
        from components.moonraker.moonraker import Moonraker
        from components.moonraker.utils.utils import remove_polkit_rules
        from core.instance_manager.instance_manager import InstanceManager
        from utils.fs_utils import run_remove_routines

        instances = get_instances(Moonraker)
        if not instances:
            Logger.print_info("Moonraker is not installed, skipping... / Moonraker 未安装，跳过...")
            return

        Logger.print_status("Removing Moonraker instances ...")
        for instance in instances:
            InstanceManager.remove(instance)

        Logger.print_status("Removing Moonraker policykit rules ...")
        remove_polkit_rules()
        Logger.print_status("Removing Moonraker local repository ...")
        run_remove_routines(MOONRAKER_DIR)
        Logger.print_status("Removing Moonraker Python environment ...")
        run_remove_routines(MOONRAKER_ENV_DIR)
        Logger.print_ok("Moonraker removed")

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
        from pathlib import Path

        from components.crowsnest import CROWSNEST_DIR

        if not CROWSNEST_DIR.exists():
            Logger.print_info("Crowsnest is not installed, skipping... / Crowsnest 未安装，跳过...")
            return

        service_file = Path("/etc/systemd/system/crowsnest.service")
        if service_file.exists():
            # 完整安装过，用 make uninstall 清理
            from components.crowsnest.crowsnest import remove_crowsnest
            remove_crowsnest()
        else:
            # 只 clone 了但未完成安装，直接删目录
            import shutil
            Logger.print_status("Removing crowsnest directory (incomplete install) ...")
            shutil.rmtree(CROWSNEST_DIR)
            Logger.print_ok("Crowsnest directory removed")

    def _remove_klipper_5axis(self) -> None:
        from components.klipper_5axis import KLIPPER_5AXIS_DIR
        from components.klipper_5axis.klipper_5axis import remove_klipper_5axis

        if not KLIPPER_5AXIS_DIR.exists():
            Logger.print_info("Klipper 5-axis is not installed, skipping... / Klipper 5-axis 未安装，跳过...")
            return
        remove_klipper_5axis()

    def _remove_moonraker_tope(self) -> None:
        from components.moonraker_tope import MOONRAKER_TOPE_DIR
        from components.moonraker_tope.moonraker_tope import remove_moonraker_tope

        if not MOONRAKER_TOPE_DIR.exists():
            Logger.print_info("Moonraker Tope is not installed, skipping... / Moonraker Tope 未安装，跳过...")
            return
        remove_moonraker_tope()

    def _remove_printer_gui(self) -> None:
        from components.printer_gui import PRINTER_GUI_DIR
        from components.printer_gui.printer_gui import remove_printer_gui

        if not PRINTER_GUI_DIR.exists():
            Logger.print_info("Printer GUI is not installed, skipping... / Printer GUI 未安装，跳过...")
            return
        remove_printer_gui()

    def run(self) -> None:
        """重写 run 方法以支持批量输入"""
        import sys
        import traceback

        from core.menus.base_menu import clear, print_back_footer, print_header

        try:
            clear()
            print_header()
            self.print_menu()
            print_back_footer()

            # 直接获取用户输入（不验证，因为需要支持批量输入）
            user_input = input(f"###### {self.input_label_txt}: ").lower().strip()

            # 空输入，重新显示菜单
            if not user_input:
                self.run()
                return

            # 单个已知选项处理（优先处理 a, c, s, b）
            if user_input in self.options:
                selected_option: Option = self.options.get(user_input)
                selected_option.method(
                    opt_index=selected_option.opt_index,
                    opt_data=selected_option.opt_data,
                )
                # 递归调用，重新显示菜单
                self.run()
                return

            # 处理批量数字输入（如 "125" 或 "1 2 5"）
            # 移除空格，得到纯数字字符串
            numbers = user_input.replace(" ", "")

            # 检查是否全是有效数字
            valid_numbers = set("123456789")
            if all(c in valid_numbers for c in numbers) and len(numbers) > 0:
                # 批量切换
                toggle_methods = {
                    "1": self.toggle_klipper,
                    "2": self.toggle_moonraker,
                    "3": self.toggle_mainsail,
                    "4": self.toggle_fluidd,
                    "5": self.toggle_klipperscreen,
                    "6": self.toggle_crowsnest,
                    "7": self.toggle_klipper_5axis,
                    "8": self.toggle_moonraker_tope,
                    "9": self.toggle_printer_gui,
                }

                for num in numbers:
                    if num in toggle_methods:
                        toggle_methods[num]()

                # 递归调用，重新显示菜单
                self.run()
                return

            # 无效输入
            Logger.print_error("Invalid option! Please select a valid option.")
            input("Press Enter to continue...")
            self.run()

        except KeyboardInterrupt:
            Logger.print_warn("\n\nOperation cancelled by user (Ctrl-C).")
            Logger.print_info("Returning to previous menu...")
            if self.previous_menu:
                self.previous_menu().run()
            else:
                sys.exit(0)

        except Exception as e:
            Logger.print_error(
                f"An unexpected error occured:\n{e}\n{traceback.format_exc()}"
            )

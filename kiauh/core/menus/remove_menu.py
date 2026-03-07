# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import sys
import textwrap
import traceback
from typing import Dict, Type

from components.crowsnest.crowsnest import get_crowsnest_status, remove_crowsnest
from components.klipper.klipper import Klipper
from components.klipper.menus.klipper_remove_menu import KlipperRemoveMenu
from components.klipperscreen.klipperscreen import (
    get_klipperscreen_status,
    remove_klipperscreen,
)
from components.moonraker.menus.moonraker_remove_menu import (
    MoonrakerRemoveMenu,
)
from components.moonraker.moonraker import Moonraker
from components.webui_client.client_utils import get_client_status
from components.webui_client.fluidd_data import FluiddData
from components.webui_client.mainsail_data import MainsailData
from components.webui_client.menus.client_remove_menu import ClientRemoveMenu
from core.logger import Logger
from core.menus import FooterType, Option
from core.menus.base_menu import BaseMenu, clear
from core.types.color import Color
from utils.instance_utils import get_instances


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class RemoveMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None) -> None:
        super().__init__()
        self.title = "Remove Menu"
        self.title_color = Color.RED
        self.footer_type = FooterType.BACK
        self.previous_menu: Type[BaseMenu] | None = previous_menu

        # 组件选择状态
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
        checked = f"[{Color.apply('✓', Color.GREEN)}]"
        unchecked = "[ ]"

        # 检查安装状态
        klipper_installed = len(get_instances(Klipper)) > 0
        moonraker_installed = len(get_instances(Moonraker)) > 0
        mainsail_status = get_client_status(MainsailData()).status
        fluidd_status = get_client_status(FluiddData()).status
        ks_status = get_klipperscreen_status().status
        cn_status = get_crowsnest_status().status

        def status_tag(s: int) -> str:
            if s == 2:
                return Color.apply(" ✓已装", Color.CYAN)
            elif s == 1:
                return Color.apply(" ~不完整", Color.YELLOW)
            return Color.apply(" ✗未装", Color.DARK_GRAY)

        o1 = checked if self.selections["klipper"] else unchecked
        o2 = checked if self.selections["moonraker"] else unchecked
        o3 = checked if self.selections["mainsail"] else unchecked
        o4 = checked if self.selections["fluidd"] else unchecked
        o5 = checked if self.selections["klipperscreen"] else unchecked
        o6 = checked if self.selections["crowsnest"] else unchecked

        # 安装状态标记
        k_installed = Color.apply(" ✓已装", Color.CYAN) if klipper_installed else Color.apply(" ✗未装", Color.DARK_GRAY)
        m_installed = Color.apply(" ✓已装", Color.CYAN) if moonraker_installed else Color.apply(" ✗未装", Color.DARK_GRAY)
        ms_installed = status_tag(mainsail_status)
        fl_installed = status_tag(fluidd_status)
        ks_installed_txt = status_tag(ks_status)
        cn_installed_txt = status_tag(cn_status)

        menu = textwrap.dedent(
            f"""
            ╟───────────────────────────────────────────────────────╢
            ║ INFO: Configurations and/or any backups will be kept! ║
            ║ 提示: 配置文件和备份将被保留！                          ║
            ╟───────────────────────────────────────────────────────╢
            ║ Select components to remove (toggle with number):    ║
            ║ 选择要卸载的组件（输入数字切换）:                       ║
            ╟───────────────────────────────────────────────────────╢
            ║ 1) {o1} Klipper{k_installed}
            ║ 2) {o2} Moonraker{m_installed}
            ║ 3) {o3} Mainsail{ms_installed}
            ║ 4) {o4} Fluidd{fl_installed}
            ║ 5) {o5} KlipperScreen{ks_installed_txt}
            ║ 6) {o6} Crowsnest{cn_installed_txt}
            ╟───────────────────────────────────────────────────────╢
            ║ Tip: Enter multiple numbers (e.g., 125 or 1 2 5)    ║
            ║ 提示: 可输入多个数字 (如 125 或 1 2 5)                 ║
            ║                                                       ║
            ║ A) Select All / 全选    C) Clear All / 清空          ║
            ║ S) Start Removal / 开始卸载                           ║
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
        """全选所有组件"""
        for key in self.selections:
            self.selections[key] = True

    def clear_all(self, **kwargs) -> None:
        """清空所有选择"""
        for key in self.selections:
            self.selections[key] = False

    def start_removal(self, **kwargs) -> None:
        """开始批量卸载"""
        clear()

        # 验证选择
        if not self._validate_selections():
            input("\nPress Enter to continue...")
            return

        # 显示卸载计划
        self._show_removal_plan()

        # 确认卸载
        from utils.input_utils import get_confirm

        if not get_confirm(
            "\nProceed with removal? / 开始卸载？", default_choice=False
        ):
            Logger.print_info("Removal cancelled / 卸载已取消")
            input("\nPress Enter to continue...")
            return

        # 执行卸载
        self._execute_removal()

        # 完成
        Logger.print_ok("\n" + "═" * 60)
        Logger.print_ok("Removal completed! / 卸载完成！")
        Logger.print_ok("═" * 60 + "\n")

        input("\nPress Enter to continue...")
        if self.previous_menu:
            self.previous_menu().run()

    def _validate_selections(self) -> bool:
        """验证选择的有效性"""
        selected_count = sum(self.selections.values())

        if selected_count == 0:
            Logger.print_error("No components selected! / 未选择任何组件！")
            Logger.print_info(
                "Please select at least one component. / 请至少选择一个组件。"
            )
            return False

        # 检查是否有已安装的组件被选中
        klipper_installed = len(get_instances(Klipper)) > 0
        moonraker_installed = len(get_instances(Moonraker)) > 0
        mainsail_status = get_client_status(MainsailData()).status
        fluidd_status = get_client_status(FluiddData()).status
        ks_status = get_klipperscreen_status().status
        cn_status = get_crowsnest_status().status

        has_installed = False
        if self.selections["klipper"] and klipper_installed:
            has_installed = True
        if self.selections["moonraker"] and moonraker_installed:
            has_installed = True
        if self.selections["mainsail"] and mainsail_status >= 1:
            has_installed = True
        if self.selections["fluidd"] and fluidd_status >= 1:
            has_installed = True
        if self.selections["klipperscreen"] and ks_status >= 1:
            has_installed = True
        if self.selections["crowsnest"] and cn_status >= 1:
            has_installed = True

        if not has_installed:
            Logger.print_warn("None of the selected components are installed! / 所选组件均未安装！")
            Logger.print_info(
                "Please select installed components. / 请选择已安装的组件。"
            )
            return False

        return True

    def _show_removal_plan(self) -> None:
        """显示卸载计划"""
        Logger.print_status("\n" + "═" * 60)
        Logger.print_status("Removal Plan / 卸载计划")
        Logger.print_status("═" * 60 + "\n")

        removal_order = []

        # 确定卸载顺序（与安装顺序相反）
        if self.selections["crowsnest"]:
            removal_order.append("Crowsnest")

        if self.selections["klipperscreen"]:
            removal_order.append("KlipperScreen")

        if self.selections["fluidd"]:
            removal_order.append("Fluidd")

        if self.selections["mainsail"]:
            removal_order.append("Mainsail")

        if self.selections["moonraker"]:
            removal_order.append("Moonraker")

        if self.selections["klipper"]:
            removal_order.append("Klipper")

        for i, component in enumerate(removal_order, 1):
            Logger.print_info(f"  {i}. {component}")

        Logger.print_status("\n" + "─" * 60)
        Logger.print_warn(
            "WARNING: This will remove the selected components!"
        )
        Logger.print_warn("警告: 这将卸载所选组件！")
        Logger.print_info(
            "Configurations and backups will be kept."
        )
        Logger.print_info("配置文件和备份将被保留。")
        Logger.print_status("─" * 60)

    def _execute_removal(self) -> None:
        """执行卸载"""
        Logger.print_status("\n" + "═" * 60)
        Logger.print_status("Starting Removal / 开始卸载")
        Logger.print_status("═" * 60 + "\n")

        try:
            # 按相反顺序卸载（先卸载依赖项）
            if self.selections["crowsnest"]:
                self._remove_component("Crowsnest", self._remove_crowsnest)

            if self.selections["klipperscreen"]:
                self._remove_component("KlipperScreen", self._remove_klipperscreen)

            if self.selections["fluidd"]:
                self._remove_component("Fluidd", self._remove_fluidd)

            if self.selections["mainsail"]:
                self._remove_component("Mainsail", self._remove_mainsail)

            if self.selections["moonraker"]:
                self._remove_component("Moonraker", self._remove_moonraker)

            if self.selections["klipper"]:
                self._remove_component("Klipper", self._remove_klipper)

        except Exception as e:
            Logger.print_error(f"\nRemoval failed: {e}")
            Logger.print_error(f"卸载失败: {e}")
            raise

    def _remove_component(self, name: str, remove_func) -> None:
        """卸载单个组件"""
        Logger.print_status(f"\n{'─' * 60}")
        Logger.print_status(f"Removing {name} / 正在卸载 {name}")
        Logger.print_status("─" * 60)

        try:
            remove_func()
            Logger.print_ok(f"✓ {name} removed successfully / {name} 卸载成功")
        except Exception as e:
            Logger.print_error(f"✗ {name} removal failed: {e}")
            Logger.print_error(f"✗ {name} 卸载失败: {e}")
            raise

    def _remove_klipper(self) -> None:
        """卸载 Klipper"""
        KlipperRemoveMenu(previous_menu=None).remove_klipper()

    def _remove_moonraker(self) -> None:
        """卸载 Moonraker"""
        MoonrakerRemoveMenu(previous_menu=None).remove_moonraker()

    def _remove_mainsail(self) -> None:
        """卸载 Mainsail"""
        ClientRemoveMenu(previous_menu=None, client=MainsailData()).remove_client()

    def _remove_fluidd(self) -> None:
        """卸载 Fluidd"""
        ClientRemoveMenu(previous_menu=None, client=FluiddData()).remove_client()

    def _remove_klipperscreen(self) -> None:
        """卸载 KlipperScreen"""
        remove_klipperscreen()

    def _remove_crowsnest(self) -> None:
        """卸载 Crowsnest"""
        remove_crowsnest()

    def run(self) -> None:
        """重写 run 方法以支持批量输入"""
        try:
            clear()
            from core.menus.base_menu import print_header
            print_header()
            self.print_menu()
            from core.menus.base_menu import print_back_footer
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
            valid_numbers = set("123456")
            if all(c in valid_numbers for c in numbers) and len(numbers) > 0:
                # 批量切换
                toggle_methods = {
                    "1": self.toggle_klipper,
                    "2": self.toggle_moonraker,
                    "3": self.toggle_mainsail,
                    "4": self.toggle_fluidd,
                    "5": self.toggle_klipperscreen,
                    "6": self.toggle_crowsnest,
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

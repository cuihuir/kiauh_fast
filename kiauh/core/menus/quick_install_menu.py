# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
#  ======================================================================= #
"""Quick Install Menu - One-click Klipper Stack Installation"""
from __future__ import annotations

import textwrap
from typing import Type, List, Dict

from core.menus import FooterType
from core.menus.base_menu import BaseMenu, Option, clear
from core.logger import Logger, DialogType
from core.types.color import Color
from utils.input_utils import get_selection_input


class QuickInstallMenu(BaseMenu):
    """一键安装菜单 - 通过复选框选择组件快速安装"""

    def __init__(self, previous_menu: Type[BaseMenu] | None = None) -> None:
        super().__init__()
        self.title = "Quick Install Klipper Stack"
        self.title_color = Color.CYAN
        self.footer_type = FooterType.BACK
        self.previous_menu = previous_menu

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
            "s": Option(method=self.start_installation),
        }

    def print_menu(self) -> None:
        from components.klipper.klipper import Klipper
        from components.moonraker.moonraker import Moonraker

        checked = f"[{Color.apply('✓', Color.GREEN)}]"
        unchecked = "[ ]"

        # 检查安装状态
        klipper_installed = len(get_instances(Klipper)) > 0
        moonraker_installed = len(get_instances(Moonraker)) > 0

        o1 = checked if self.selections["klipper"] else unchecked
        o2 = checked if self.selections["moonraker"] else unchecked
        o3 = checked if self.selections["mainsail"] else unchecked
        o4 = checked if self.selections["fluidd"] else unchecked
        o5 = checked if self.selections["klipperscreen"] else unchecked
        o6 = checked if self.selections["crowsnest"] else unchecked

        # 安装状态标记（简短版本）
        k_installed = Color.apply(" ✓已装", Color.CYAN) if klipper_installed else ""
        m_installed = Color.apply(" ✓已装", Color.CYAN) if moonraker_installed else ""

        menu = textwrap.dedent(
            f"""
            ╟───────────────────────────────────────────────────────╢
            ║ Select components to install (toggle with number):   ║
            ║ 选择要安装的组件（输入数字切换）:                       ║
            ╟───────────────────────────────────────────────────────╢
            ║ 1) {o1} Klipper         (Required / 必需){k_installed}
            ║ 2) {o2} Moonraker       (Required / 必需){m_installed}
            ║ 3) {o3} Mainsail        (Web UI)                      ║
            ║ 4) {o4} Fluidd          (Web UI)                      ║
            ║ 5) {o5} KlipperScreen   (Touch UI, requires reboot)  ║
            ║ 6) {o6} Crowsnest       (Camera streaming)           ║
            ╟───────────────────────────────────────────────────────╢
            ║ S) Start Installation / 开始安装                       ║
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

    def start_installation(self, **kwargs) -> None:
        """开始一键安装"""
        clear()

        # 验证选择
        if not self._validate_selections():
            input("\nPress Enter to continue...")
            return

        # 显示安装计划
        self._show_installation_plan()

        # 确认安装
        from utils.input_utils import get_confirm

        if not get_confirm(
            "\nProceed with installation? / 开始安装？", default_choice=True
        ):
            Logger.print_info("Installation cancelled / 安装已取消")
            input("\nPress Enter to continue...")
            return

        # 执行安装
        self._execute_installation()

        # 完成
        Logger.print_ok("\n" + "═" * 60)
        Logger.print_ok("Installation completed! / 安装完成！")
        Logger.print_ok("═" * 60 + "\n")

        if self.selections["klipperscreen"]:
            Logger.print_dialog(
                DialogType.ATTENTION,
                [
                    "KlipperScreen has been installed.",
                    "KlipperScreen 已安装。",
                    "",
                    "A system reboot is required to start KlipperScreen.",
                    "需要重启系统以启动 KlipperScreen。",
                    "",
                    "Reboot now? / 现在重启？",
                ],
            )
            if get_confirm("Reboot system? / 重启系统？", default_choice=False):
                import subprocess

                subprocess.run(["sudo", "reboot"])

        input("\nPress Enter to continue...")
        self._return_to_previous_menu()

    def _validate_selections(self) -> bool:
        """验证选择的有效性"""
        from components.klipper.klipper import Klipper
        from components.moonraker.moonraker import Moonraker

        selected_count = sum(self.selections.values())

        if selected_count == 0:
            Logger.print_error("No components selected! / 未选择任何组件！")
            Logger.print_info(
                "Please select at least one component. / 请至少选择一个组件。"
            )
            return False

        # 检查 Klipper 是否已安装或已选择
        klipper_instances = get_instances(Klipper)
        klipper_installed = len(klipper_instances) > 0

        if not klipper_installed and not self.selections["klipper"]:
            Logger.print_error("Klipper is required! / Klipper 是必需的！")
            Logger.print_info(
                "Klipper is not installed. Please select Klipper (option 1). / "
                "Klipper 未安装，请选择 Klipper（选项 1）。"
            )
            return False

        # 检查 Moonraker 是否已安装或已选择
        moonraker_instances = get_instances(Moonraker)
        moonraker_installed = len(moonraker_instances) > 0

        if not moonraker_installed and not self.selections["moonraker"]:
            Logger.print_error("Moonraker is required! / Moonraker 是必需的！")
            Logger.print_info(
                "Moonraker is not installed. Please select Moonraker (option 2). / "
                "Moonraker 未安装，请选择 Moonraker（选项 2）。"
            )
            return False

        return True

    def _show_installation_plan(self) -> None:
        """显示安装计划"""
        Logger.print_status("\n" + "═" * 60)
        Logger.print_status("Installation Plan / 安装计划")
        Logger.print_status("═" * 60 + "\n")

        install_order = []
        port_assignments = {}

        # 确定安装顺序
        if self.selections["klipper"]:
            install_order.append("Klipper")

        if self.selections["moonraker"]:
            install_order.append("Moonraker")

        # Web UI - 端口分配 80 -> 81
        current_port = 80
        if self.selections["mainsail"]:
            install_order.append(f"Mainsail (port {current_port})")
            port_assignments["mainsail"] = current_port
            current_port = 81

        if self.selections["fluidd"]:
            install_order.append(f"Fluidd (port {current_port})")
            port_assignments["fluidd"] = current_port
            current_port += 1

        if self.selections["crowsnest"]:
            install_order.append("Crowsnest")

        # KlipperScreen 最后安装（需要重启）
        if self.selections["klipperscreen"]:
            install_order.append("KlipperScreen (requires reboot)")

        for i, component in enumerate(install_order, 1):
            Logger.print_info(f"  {i}. {component}")

        Logger.print_status("\n" + "─" * 60)
        Logger.print_info(
            "Installation will be fully automated except for sudo password prompts."
        )
        Logger.print_info("安装将完全自动化，除了需要输入 sudo 密码。")
        Logger.print_status("─" * 60)

        # 保存端口分配供后续使用
        self._port_assignments = port_assignments

    def _execute_installation(self) -> None:
        """执行安装"""
        from components.klipper.klipper import Klipper
        from components.moonraker.moonraker import Moonraker

        Logger.print_status("\n" + "═" * 60)
        Logger.print_status("Starting Installation / 开始安装")
        Logger.print_status("═" * 60 + "\n")

        try:
            # 1. 安装 Klipper (如果未安装)
            if self.selections["klipper"]:
                if get_instances(Klipper):
                    Logger.print_info("Klipper already installed, skipping... / Klipper 已安装，跳过...")
                else:
                    self._install_component("Klipper", self._install_klipper)

            # 2. 安装 Moonraker (如果未安装)
            if self.selections["moonraker"]:
                if get_instances(Moonraker):
                    Logger.print_info("Moonraker already installed, skipping... / Moonraker 已安装，跳过...")
                else:
                    self._install_component("Moonraker", self._install_moonraker)

            # 3. 安装 Mainsail
            if self.selections["mainsail"]:
                port = self._port_assignments.get("mainsail", 80)
                self._install_component(
                    "Mainsail", lambda: self._install_mainsail(port)
                )

            # 4. 安装 Fluidd
            if self.selections["fluidd"]:
                port = self._port_assignments.get("fluidd", 81)
                self._install_component("Fluidd", lambda: self._install_fluidd(port))

            # 5. 安装 Crowsnest
            if self.selections["crowsnest"]:
                self._install_component("Crowsnest", self._install_crowsnest)

            # 6. 安装 KlipperScreen (最后，需要重启)
            if self.selections["klipperscreen"]:
                self._install_component("KlipperScreen", self._install_klipperscreen)

        except Exception as e:
            Logger.print_error(f"\nInstallation failed: {e}")
            Logger.print_error(f"安装失败: {e}")
            raise

    def _install_component(self, name: str, install_func) -> None:
        """安装单个组件"""
        Logger.print_status(f"\n{'─' * 60}")
        Logger.print_status(f"Installing {name} / 正在安装 {name}")
        Logger.print_status("─" * 60)

        try:
            install_func()
            Logger.print_ok(f"✓ {name} installed successfully / {name} 安装成功")
        except Exception as e:
            Logger.print_error(f"✗ {name} installation failed: {e}")
            Logger.print_error(f"✗ {name} 安装失败: {e}")
            raise

    def _install_klipper(self) -> None:
        """安装 Klipper"""
        from components.klipper.services.klipper_setup_service import (
            KlipperSetupService,
        )

        klsvc = KlipperSetupService()
        klsvc.install()

    def _install_moonraker(self) -> None:
        """安装 Moonraker"""
        from components.moonraker.services.moonraker_setup_service import (
            MoonrakerSetupService,
        )

        mrsvc = MoonrakerSetupService()
        mrsvc.install()

    def _install_mainsail(self, port: int = 80) -> None:
        """安装 Mainsail"""
        from components.webui_client.client_setup import install_client
        from components.webui_client.mainsail_data import MainsailData
        from core.settings.kiauh_settings import KiauhSettings

        # 临时设置端口
        settings = KiauhSettings()
        original_port = settings.mainsail.port
        settings.mainsail.port = port
        settings.save()

        try:
            install_client(MainsailData(), settings=settings)
        finally:
            # 恢复原始端口设置
            settings.mainsail.port = original_port
            settings.save()

    def _install_fluidd(self, port: int = 81) -> None:
        """安装 Fluidd"""
        from components.webui_client.client_setup import install_client
        from components.webui_client.fluidd_data import FluiddData
        from core.settings.kiauh_settings import KiauhSettings

        # 临时设置端口
        settings = KiauhSettings()
        original_port = settings.fluidd.port
        settings.fluidd.port = port
        settings.save()

        try:
            install_client(FluiddData(), settings=settings)
        finally:
            # 恢复原始端口设置
            settings.fluidd.port = original_port
            settings.save()

    def _install_klipperscreen(self) -> None:
        """安装 KlipperScreen"""
        from components.klipperscreen.klipperscreen import install_klipperscreen

        install_klipperscreen()

    def _install_crowsnest(self) -> None:
        """安装 Crowsnest (使用优化版本)"""
        try:
            from components.crowsnest.crowsnest_optimized import (
                install_crowsnest_optimized,
            )

            success = install_crowsnest_optimized()
            if not success:
                raise Exception("Crowsnest installation failed")
        except ImportError:
            # 如果优化版本不存在，使用标准版本
            from components.crowsnest.crowsnest import install_crowsnest

            install_crowsnest()

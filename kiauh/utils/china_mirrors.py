# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
"""
中国大陆镜像源加速工具
提供 PyPI、APT 镜像自动配置和 Git 加速提醒
"""
from __future__ import annotations

import re
from pathlib import Path
from subprocess import run, DEVNULL
from typing import Dict, Optional

from core.logger import Logger, DialogType
from utils.input_utils import get_confirm


def detect_china_network() -> bool:
    """
    检测是否在中国大陆网络环境
    :return: True if in China mainland
    """
    try:
        # 检查 pip 配置是否已使用中国镜像
        pip_config = Path.home().joinpath(".pip/pip.conf")
        if pip_config.exists():
            with open(pip_config) as f:
                if any(m in f.read() for m in ["tuna", "aliyun", "ustc"]):
                    return True

        # 检查 apt sources 是否使用中国镜像
        apt_sources = Path("/etc/apt/sources.list")
        if apt_sources.exists():
            with open(apt_sources) as f:
                if any(m in f.read() for m in ["tuna", "aliyun", "ustc", "huawei"]):
                    return True

    except Exception:
        pass

    return False


def configure_pip_mirror(mirror_url: Optional[str] = None) -> bool:
    """
    配置 pip 镜像源
    :param mirror_url: 镜像URL，默认使用清华源
    :return: True if successful
    """
    if mirror_url is None:
        mirror_url = "https://pypi.tuna.tsinghua.edu.cn/simple"

    try:
        Logger.print_status(f"配置 pip 镜像 / Configuring pip mirror...")

        pip_config_dir = Path.home().joinpath(".pip")
        pip_config_dir.mkdir(parents=True, exist_ok=True)

        pip_config_file = pip_config_dir.joinpath("pip.conf")
        host = mirror_url.split('//')[1].split('/')[0]

        config_content = f"""[global]
index-url = {mirror_url}
trusted-host = {host}

[install]
trusted-host = {host}
"""

        with open(pip_config_file, 'w') as f:
            f.write(config_content)

        Logger.print_ok(f"pip 镜像已配置 / pip mirror configured: {mirror_url}")
        return True

    except Exception as e:
        Logger.print_error(f"配置 pip 镜像失败 / Failed to configure pip: {e}")
        return False


def configure_uv_mirror(mirror_url: Optional[str] = None) -> bool:
    """
    配置 uv 包管理器的镜像源
    :param mirror_url: 镜像URL
    :return: True if successful
    """
    if mirror_url is None:
        mirror_url = "https://pypi.tuna.tsinghua.edu.cn/simple"

    try:
        Logger.print_status("配置 uv 镜像 / Configuring uv mirror...")

        uv_config_dir = Path.home().joinpath(".config/uv")
        uv_config_dir.mkdir(parents=True, exist_ok=True)

        uv_config_file = uv_config_dir.joinpath("uv.toml")
        config_content = f"""# UV Configuration for China Mirrors
[[index]]
url = "{mirror_url}"
default = true
"""

        with open(uv_config_file, 'w') as f:
            f.write(config_content)

        Logger.print_ok(f"uv 镜像已配置 / uv mirror configured")
        return True

    except Exception as e:
        Logger.print_error(f"配置 uv 镜像失败 / Failed to configure uv: {e}")
        return False


def setup_apt_mirror() -> bool:
    """
    APT 镜像源切换（提供两种方式）
    :return: True if switched or skipped
    """
    Logger.print_dialog(
        DialogType.INFO,
        [
            "═══ APT 镜像源切换 / APT Mirror Switch ═══",
            "\n",
            "KIAUH 提供两种切换方式：",
            "KIAUH provides two switching methods:",
            "\n",
            "方式 1: KIAUH 内置自动切换（推荐 / Recommended）",
            "  ● 支持 Debian 10/11/12, Ubuntu 20.04/22.04/24.04",
            "  ● 自动备份原有配置 / Auto backup",
            "  ● 可选多个镜像源 / Multiple mirrors available",
            "  ● 无需 root 登录 / No root login required",
            "\n",
            "方式 2: SuperManito 第三方脚本",
            "  ● 支持更多发行版 / More distros supported",
            "  ● 需要 root 权限 (sudo -i)",
            "  ● 命令: bash <(curl -sSL https://linuxmirrors.cn/main.sh)",
        ],
    )

    choice = input(
        "\n选择切换方式 / Choose method:\n"
        "  1) KIAUH 内置 / Built-in (推荐)\n"
        "  2) 第三方脚本 / External script\n"
        "  0) 跳过 / Skip\n"
        "选择 / Choice [1]: "
    ).strip() or "1"

    if choice == "1":
        # 使用 KIAUH 内置切换
        from utils.apt_mirror_switcher import switch_apt_mirror_auto, show_apt_mirror_menu

        Logger.print_info("\n使用 KIAUH 内置 APT 镜像切换 / Using built-in switcher\n")

        if get_confirm("直接使用清华源？ / Use Tsinghua mirror?", default_choice=True):
            return switch_apt_mirror_auto("tsinghua")
        else:
            show_apt_mirror_menu()
            return True

    elif choice == "2":
        # 提示使用外部脚本
        Logger.print_warn(
            "\n注意：该脚本需要 root 权限\n"
            "Note: This script requires root privileges\n"
        )
        Logger.print_info(
            "请在新终端以 root 身份运行：\n"
            "Run in new terminal as root:\n\n"
            "  sudo -i\n"
            "  bash <(curl -sSL https://linuxmirrors.cn/main.sh)\n"
        )
        input("\n完成后按回车继续... / Press Enter after completion...")
        return True

    else:
        Logger.print_info("跳过 APT 镜像切换 / Skipping APT mirror switch")
        return True


def show_git_acceleration_guide() -> None:
    """显示 Git 加速指南（仅提醒，不强制配置）"""
    Logger.print_dialog(
        DialogType.INFO,
        [
            "═══ Git 加速方法 / Git Acceleration Methods ═══",
            "\n",
            "方法 1: GitHub 文件代理（推荐 / Recommended）",
            "  使用 gh-proxy.com 加速 GitHub 克隆",
            "  Use gh-proxy.com to accelerate GitHub cloning",
            "\n",
            "  手动方式 / Manual method:",
            "  " + "─" * 55,
            "  # 原始 / Original:",
            "  git clone https://github.com/user/repo.git",
            "\n",
            "  # 加速 / Accelerated:",
            "  git clone https://gh-proxy.com/https://github.com/user/repo.git",
            "  " + "─" * 55,
            "\n",
            "  详情 / Details: https://gh-proxy.com/",
            "\n\n",
            "方法 2: 配置 Git HTTP 代理（如有代理服务器）",
            "  If you have a proxy server:",
            "  " + "─" * 55,
            "  git config --global http.proxy http://proxy:port",
            "  git config --global https.proxy https://proxy:port",
            "  " + "─" * 55,
            "\n\n",
            "方法 3: 使用国内 Git 托管平台镜像",
            "  Use domestic Git hosting mirrors",
            "  (某些仓库可能在 Gitee 等平台有镜像)",
            "\n\n",
            "注意 / Note:",
            "  KIAUH 不自动配置 Git 加速",
            "  KIAUH does not auto-configure Git acceleration",
            "  用户可根据需要手动选择方案",
            "  Users can manually choose methods as needed",
        ],
    )


def show_apt_mirror_guide() -> None:
    """显示 APT 镜像切换指南"""
    Logger.print_dialog(
        DialogType.INFO,
        [
            "APT 镜像源切换指南 / APT Mirror Switch Guide",
            "\n",
            "═" * 60,
            "\n\n",
            "方法 1: KIAUH 内置自动切换（推荐 / Recommended）",
            "  通过菜单 \"配置镜像加速\" 选项使用",
            "  Use via menu option \"Setup Mirror Acceleration\"",
            "  " + "─" * 55,
            "  ● 支持 Debian 10/11/12, Ubuntu 20.04/22.04/24.04",
            "  ● 自动备份原有配置 / Auto backup",
            "  ● 无需 root 登录 / No root login required",
            "  " + "─" * 55,
            "\n\n",
            "方法 2: 使用 SuperManito 第三方脚本",
            "  Use SuperManito's Linux Mirror script",
            "  " + "─" * 55,
            "  bash <(curl -sSL https://linuxmirrors.cn/main.sh)",
            "  " + "─" * 55,
            "  ● 需要 root 权限 (sudo -i) / Requires root",
            "  ● 支持更多发行版 / Supports more distros",
            "  ● 项目地址 / Project: https://github.com/SuperManito/LinuxMirrors",
            "\n\n",
            "注意 / Note:",
            "  切换 APT 镜像源可显著提升软件包下载速度",
            "  Switching APT mirrors significantly improves package download speed",
            "  建议在首次安装前配置",
            "  Recommended to configure before first installation",
        ],
    )


def setup_china_mirrors() -> Dict[str, bool]:
    """
    中国大陆镜像加速配置向导（完整流程）
    :return: 配置结果
    """
    results = {
        "pip_configured": False,
        "uv_configured": False,
        "apt_configured": False,
        "git_guided": False,
    }

    Logger.print_status("\n" + "═" * 60)
    Logger.print_status("  中国大陆加速配置向导 / China Acceleration Setup")
    Logger.print_status("═" * 60 + "\n")

    # 1. PyPI 镜像配置
    Logger.print_status("【步骤 1/3】PyPI 镜像配置 / PyPI Mirror Configuration\n")
    Logger.print_info(
        "将配置 pip/uv 使用清华大学镜像源\n"
        "Will configure pip/uv to use Tsinghua University mirror\n"
        "预期加速效果 / Expected speedup: 10-50x\n"
    )

    if get_confirm("配置 PyPI 镜像？ / Configure PyPI mirror?", default_choice=True):
        results["pip_configured"] = configure_pip_mirror()

        # 检查 uv 是否已安装
        try:
            uv_check = run(["which", "uv"], capture_output=True, stderr=DEVNULL)
            if uv_check.returncode == 0:
                Logger.print_info("\n检测到 uv 已安装 / uv detected")
                if get_confirm("同时配置 uv 镜像？ / Configure uv mirror too?", default_choice=True):
                    results["uv_configured"] = configure_uv_mirror()
        except Exception:
            pass

    # 2. APT 镜像切换
    Logger.print_status("\n【步骤 2/3】APT 镜像源切换 / APT Mirror Switch\n")
    Logger.print_info(
        "切换系统软件源以加速软件包下载\n"
        "Switch system repositories for faster package downloads\n"
        "预期加速效果 / Expected speedup: 5-20x\n"
    )

    if get_confirm("切换 APT 镜像源？ / Switch APT mirrors?", default_choice=True):
        results["apt_configured"] = setup_apt_mirror()
    else:
        Logger.print_info("跳过 APT 镜像切换 / Skipping APT mirror switch\n")

    # 3. Git 加速指南
    Logger.print_status("\n【步骤 3/3】Git 加速方法 / Git Acceleration Methods\n")
    Logger.print_info(
        "提供多种 GitHub 加速方案供选择\n"
        "Multiple GitHub acceleration methods available\n"
    )

    if get_confirm("查看 Git 加速指南？ / View Git guide?", default_choice=True):
        show_git_acceleration_guide()
        results["git_guided"] = True

    # 4. 配置摘要
    Logger.print_status("\n" + "═" * 60)
    Logger.print_status("  配置摘要 / Configuration Summary")
    Logger.print_status("═" * 60)

    status_icon = lambda x: "✓" if x else "○"
    Logger.print_info(f"  {status_icon(results['pip_configured'])} pip 镜像 / pip mirror")
    Logger.print_info(f"  {status_icon(results['uv_configured'])} uv 镜像 / uv mirror")
    Logger.print_info(f"  {status_icon(results['apt_configured'])} APT 镜像 / APT mirror")
    Logger.print_info(f"  {status_icon(results['git_guided'])} Git 指南已显示 / Git guide shown")
    Logger.print_status("═" * 60)

    Logger.print_ok("\n✓ 加速配置完成！ / Acceleration setup complete!\n")

    return results


def quick_setup_china_mirrors() -> bool:
    """
    快速配置中国镜像（静默模式，使用默认选项）
    :return: True if successful
    """
    try:
        Logger.print_status("快速配置中国镜像 / Quick setup China mirrors...")

        # 配置 pip 镜像
        configure_pip_mirror()

        # 配置 uv 镜像（如果已安装）
        try:
            uv_check = run(["which", "uv"], capture_output=True, stderr=DEVNULL)
            if uv_check.returncode == 0:
                configure_uv_mirror()
        except Exception:
            pass

        Logger.print_ok("PyPI 镜像配置完成！ / PyPI mirrors configured!")
        Logger.print_info(
            "提示：您还可以切换 APT 镜像源以进一步加速\n"
            "Tip: You can also switch APT mirrors for more acceleration"
        )
        return True

    except Exception as e:
        Logger.print_error(f"镜像配置失败 / Mirror configuration failed: {e}")
        return False


def check_mirror_status() -> Dict[str, str]:
    """
    检查当前镜像配置状态
    :return: 状态字典
    """
    status = {}

    # 检查 pip 镜像
    pip_config = Path.home().joinpath(".pip/pip.conf")
    if pip_config.exists():
        try:
            with open(pip_config) as f:
                content = f.read()
                match = re.search(r'index-url\s*=\s*(.+)', content)
                status["pip"] = match.group(1).strip() if match else "Unknown"
        except Exception:
            status["pip"] = "Error reading config"
    else:
        status["pip"] = "Not configured (using pypi.org)"

    # 检查 uv 镜像
    uv_config = Path.home().joinpath(".config/uv/uv.toml")
    if uv_config.exists():
        try:
            with open(uv_config) as f:
                content = f.read()
                match = re.search(r'url\s*=\s*"(.+)"', content)
                status["uv"] = match.group(1).strip() if match else "Configured"
        except Exception:
            status["uv"] = "Error reading config"
    else:
        status["uv"] = "Not configured"

    # 检查 APT 镜像
    apt_sources = Path("/etc/apt/sources.list")
    if apt_sources.exists():
        try:
            with open(apt_sources) as f:
                content = f.read()
                if "mirrors.tuna.tsinghua.edu.cn" in content:
                    status["apt"] = "Tsinghua University TUNA"
                elif "mirrors.aliyun.com" in content:
                    status["apt"] = "Alibaba Cloud"
                elif "mirrors.ustc.edu.cn" in content:
                    status["apt"] = "USTC"
                elif "mirrors.tencent.com" in content:
                    status["apt"] = "Tencent Cloud"
                else:
                    status["apt"] = "Default (not using China mirror)"
        except Exception:
            status["apt"] = "Error reading sources.list"
    else:
        status["apt"] = "sources.list not found"

    return status


def restore_default_mirrors() -> bool:
    """
    恢复默认镜像配置（移除中国镜像）
    注意：仅移除 PyPI 镜像，APT 镜像需要手动恢复
    :return: True if successful
    """
    try:
        Logger.print_status("恢复默认镜像源 / Restoring default mirrors...")

        # 移除 pip 配置
        pip_config = Path.home().joinpath(".pip/pip.conf")
        if pip_config.exists():
            pip_config.unlink()
            Logger.print_ok("已移除 pip 镜像配置 / Removed pip mirror config")

        # 移除 uv 配置
        uv_config = Path.home().joinpath(".config/uv/uv.toml")
        if uv_config.exists():
            uv_config.unlink()
            Logger.print_ok("已移除 uv 镜像配置 / Removed uv mirror config")

        # APT 镜像恢复提示
        Logger.print_info(
            "\nAPT 镜像源需要手动恢复：\n"
            "To restore APT mirrors manually:\n"
            "  1. 查看备份文件 / Check backups:\n"
            "     ls /etc/apt/sources.list.bak_*\n"
            "  2. 恢复备份 / Restore backup:\n"
            "     sudo cp /etc/apt/sources.list.bak_XXXXXX /etc/apt/sources.list\n"
            "     sudo apt-get update\n"
        )

        # 检查是否有备份
        try:
            from utils.apt_mirror_switcher import list_backups, show_backup_restore_menu

            backups = list_backups()
            if backups:
                Logger.print_info(f"\n找到 {len(backups)} 个 APT 备份文件")
                if get_confirm("现在恢复 APT 备份？ / Restore APT backup now?"):
                    show_backup_restore_menu()
        except Exception:
            pass

        Logger.print_ok("\n默认源恢复完成！ / Default sources restored!")
        return True

    except Exception as e:
        Logger.print_error(f"恢复失败 / Restore failed: {e}")
        return False

# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import os
import re
import select
import shutil
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from subprocess import DEVNULL, PIPE, CalledProcessError, Popen, check_output, run
from typing import List, Literal, Set, Tuple

from core.constants import SYSTEMD
from core.logger import DialogType, Logger
from utils.fs_utils import check_file_exist, remove_with_sudo
from utils.input_utils import get_confirm

SysCtlServiceAction = Literal[
    "start",
    "stop",
    "restart",
    "reload",
    "enable",
    "disable",
    "mask",
    "unmask",
]
SysCtlManageAction = Literal["daemon-reload", "reset-failed"]


class VenvCreationFailedException(Exception):
    pass


def kill(opt_err_msg: str = "") -> None:
    """
    Kills the application |
    :param opt_err_msg: an optional, additional error message
    :return: None
    """

    if opt_err_msg:
        Logger.print_error(opt_err_msg)
    Logger.print_error("A critical error has occured. KIAUH was terminated.")
    sys.exit(1)


def check_python_version(major: int, minor: int) -> bool:
    """
    Checks the python version and returns True if it's at least the given version
    :param major: the major version to check
    :param minor: the minor version to check
    :return: bool
    """
    if not (sys.version_info.major >= major and sys.version_info.minor >= minor):
        Logger.print_error("Versioncheck failed!")
        Logger.print_error(f"Python {major}.{minor} or newer required.")
        return False
    return True


def parse_packages_from_file(source_file: Path) -> List[str]:
    """
    Read the package names from bash scripts, when defined like:
    PKGLIST="package1 package2 package3" |
    :param source_file: path of the sourcefile to read from
    :return: A list of package names
    """

    packages = []
    with open(source_file, "r") as file:
        for line in file:
            line = line.strip()
            if line.startswith("PKGLIST="):
                line = line.replace('"', "")
                line = line.replace("PKGLIST=", "")
                line = line.replace("${PKGLIST}", "")
                packages.extend(line.split())

    return packages


# ============================================================================
# UV (Fast Python Package Manager) Support
# ============================================================================

# 全局状态：记录用户是否已被询问过安装 uv
_UV_INSTALL_ASKED = False
_UV_INSTALL_FAILED = False

def is_uv_installed() -> bool:
    """检查 uv 是否已安装"""
    try:
        result = run(["uv", "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def install_uv() -> bool:
    """
    安装 uv（快速 Python 包管理器）
    :return: True if successful
    """
    Logger.print_status("Installing uv (fast Python package manager)...")
    Logger.print_info("This will speed up Python package installation by 10-100x!")

    # 方法 1: 使用官方安装脚本（推荐）
    try:
        Logger.print_info("Trying official installer (from astral.sh)...")
        Logger.print_info("Downloading and installing uv (showing progress)...")
        print()  # 空行，让输出更清晰

        # 不捕获输出，让用户看到实时进度
        result = run(
            "curl -LsSf https://astral.sh/uv/install.sh | sh",
            shell=True,
            timeout=180,  # 增加到180秒超时（下载可能需要时间）
        )

        print()  # 安装完成后空行

        # 检查是否成功安装（不仅看 returncode，还要检查文件）
        cargo_bin = Path.home() / ".cargo" / "bin" / "uv"
        local_bin = Path.home() / ".local" / "bin" / "uv"

        if cargo_bin.exists() or local_bin.exists():
            uv_path = cargo_bin if cargo_bin.exists() else local_bin
            Logger.print_ok("uv installed successfully via official installer!")
            Logger.print_info(f"uv location: {uv_path}")
            # 添加到当前 shell 的 PATH
            import os
            os.environ["PATH"] = f"{uv_path.parent}:{os.environ.get('PATH', '')}"
            return True

        # 安装器运行了但没找到文件
        Logger.print_warn("Installer completed but uv binary not found")

    except Exception as e:
        Logger.print_warn(f"Official installer error: {e}")

    # 方法 2: 使用 pip 安装（备用方案）
    # 先检查 pip 是否可用
    try:
        pip_check = run(
            ["python3", "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        pip_available = pip_check.returncode == 0
    except:
        pip_available = False

    if not pip_available:
        Logger.print_warn("pip is not available on this system")
        Logger.print_info("To install pip: sudo apt install python3-pip")
    else:
        try:
            Logger.print_info("Trying pip install (alternative method)...")

            # 使用 python3 -m pip (更兼容)
            result = run(
                ["python3", "-m", "pip", "install", "--user", "uv"],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0:
                # 检查 pip 安装位置
                home_bin = Path.home() / ".local" / "bin" / "uv"
                if home_bin.exists():
                    Logger.print_ok("uv installed successfully via pip!")
                    Logger.print_info(f"uv location: {home_bin}")
                    # 添加到 PATH
                    import os
                    os.environ["PATH"] = f"{home_bin.parent}:{os.environ.get('PATH', '')}"
                    return True

                # 检查其他可能的位置
                for loc in ["/usr/local/bin/uv", Path.home() / ".cargo" / "bin" / "uv"]:
                    if Path(loc).exists():
                        Logger.print_ok(f"uv installed successfully! Location: {loc}")
                        return True

            Logger.print_warn(f"pip install failed: {result.stderr[:200] if result.stderr else 'unknown error'}")

        except Exception as e:
            Logger.print_warn(f"pip install error: {e}")

    # 所有方法都失败
    Logger.print_error("Failed to install uv via all methods!")
    Logger.print_dialog(
        DialogType.ERROR,
        [
            "uv installation failed!",
            "",
            "Solutions:",
            "1. Manual installation (recommended):",
            "   curl -LsSf https://astral.sh/uv/install.sh | sh",
            "",
            "2. Or install via pip:",
            "   First install pip: sudo apt install python3-pip",
            "   Then install uv: python3 -m pip install --user uv",
            "",
            "3. If behind firewall, configure proxy or use pip method",
            "",
            "KIAUH will continue with pip (slower but works).",
        ],
    )
    return False


def ensure_uv_installed() -> bool:
    """
    确保 uv 已安装，如果没有则提示安装
    :return: True if uv is available
    """
    global _UV_INSTALL_ASKED, _UV_INSTALL_FAILED

    # 检查 uv 是否已安装
    if is_uv_installed():
        return True

    # 如果之前安装失败过，不再重复尝试
    if _UV_INSTALL_FAILED:
        return False

    # 如果之前已经询问过用户（用户拒绝），不再重复询问
    if _UV_INSTALL_ASKED:
        return False

    # 首次询问用户
    _UV_INSTALL_ASKED = True

    Logger.print_warn("uv is not installed.")
    Logger.print_info("uv is a fast Python package manager (10-100x faster than pip).")

    if get_confirm("Install uv now for faster Python package installation?", default_choice=True):
        success = install_uv()
        if not success:
            _UV_INSTALL_FAILED = True  # 标记安装失败，避免重复尝试
        return success
    else:
        Logger.print_info("Continuing with pip (slower)...")
        return False


def get_uv_binary() -> str:
    """获取 uv 二进制文件路径"""
    # 检查常见位置（包括 pip 安装位置）
    locations = [
        Path.home() / ".local" / "bin" / "uv",  # pip install --user
        Path.home() / ".cargo" / "bin" / "uv",  # official installer
        Path("/usr/local/bin/uv"),
        Path("/usr/bin/uv"),
    ]

    for loc in locations:
        if loc.exists():
            return str(loc)

    # 尝试从 PATH 中找
    try:
        result = run(["which", "uv"], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass

    return "uv"  # 默认假设在 PATH 中


def create_python_venv(
    target: Path,
    force: bool = False,
    allow_access_to_system_site_packages: bool = False,
    use_python_binary: str | None = None
) -> bool:
    """
    Create a python 3 virtualenv at the provided target destination.
    Returns True if the virtualenv was created successfully.
    Returns False if the virtualenv already exists, recreation was declined or creation failed.
    :param target: Path where to create the virtualenv at
    :param force: Force recreation of the virtualenv
    :param allow_access_to_system_site_packages: give the virtual environment access to the system site-packages dir
    :param use_python_binary: allows to override default python binary
    :return: bool
    """
    Logger.print_status("Set up Python virtual environment ...")

    # 尝试使用 uv（如果可用）
    use_uv = ensure_uv_installed()

    # If binary override is not set, we use default defined here
    python_binary = use_python_binary if use_python_binary else "/usr/bin/python3"

    # 根据是否使用 uv 构造命令
    if use_uv:
        uv_bin = get_uv_binary()
        cmd = [uv_bin, "venv", target.as_posix()]
        if use_python_binary:
            cmd.extend(["--python", python_binary])
        if allow_access_to_system_site_packages:
            cmd.append("--system-site-packages")
    else:
        cmd = ["virtualenv", "-p", python_binary, target.as_posix()]
        cmd.append(
            "--system-site-packages"
        ) if allow_access_to_system_site_packages else None

    n = 2
    while(n > 0):
        if not target.exists():
            try:
                run(cmd, check=True)
                if use_uv:
                    Logger.print_ok("Setup of virtualenv successful (using uv - 10-100x faster)!")
                else:
                    Logger.print_ok("Setup of virtualenv successful!")
                return True
            except CalledProcessError as e:
                Logger.print_error(f"Error setting up virtualenv:\n{e}")
                return False
        else:
            if n == 1:
                # This case should never happen,
                # but the function should still behave correctly
                Logger.print_error("Virtualenv still exists after deletion.")
                return False
            if not force and not get_confirm(
                "Virtualenv already exists. Re-create?", default_choice=False
            ):
                Logger.print_info("Skipping re-creation of virtualenv ...")
                return False

            try:
                shutil.rmtree(target)
                n -= 1
            except OSError as e:
                log = f"Error removing existing virtualenv: {e.strerror}"
                Logger.print_error(log, False)
                return False


def update_python_pip(target: Path) -> None:
    """
    Updates pip in the provided target destination |
    :param target: Path of the virtualenv
    :return: None
    """
    # 如果使用 uv，不需要更新 pip（uv 自带最新版本）
    if is_uv_installed():
        Logger.print_info("Using uv - pip update not needed!")
        return

    Logger.print_status("Updating pip ...")
    try:
        pip_location: Path = target.joinpath("bin/pip")
        pip_exists: bool = check_file_exist(pip_location)

        if not pip_exists:
            raise FileNotFoundError("Error updating pip! Not found.")

        command = [pip_location.as_posix(), "install", "-U", "pip"]
        result = run(command, stderr=PIPE, text=True)
        if result.returncode != 0 or result.stderr:
            Logger.print_error(f"{result.stderr}", False)
            Logger.print_error("Updating pip failed!")
            return

        Logger.print_ok("Updating pip successful!")
    except FileNotFoundError as e:
        Logger.print_error(e)
        raise
    except CalledProcessError as e:
        Logger.print_error(f"Error updating pip:\n{e.output.decode()}")
        raise


def install_python_requirements(target: Path, requirements: Path) -> None:
    """
    Installs the python packages based on a provided requirements.txt |
    :param target: Path of the virtualenv
    :param requirements: Path to the requirements.txt file
    :return: None
    """
    try:
        Logger.print_status("Installing Python requirements ...")

        # 检查并分离 requirements.txt 中的标准包和本地路径
        standard_packages = []
        local_paths = []

        if requirements.exists():
            content = requirements.read_text()

            for line in content.splitlines():
                original_line = line
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                # 处理选项行（-e, -r, --index-url, --find-links 等）
                if line.startswith("-"):
                    # 特殊处理 --find-links 选项中的本地路径
                    if line.startswith("--find-links=") or line.startswith("-f="):
                        # 提取路径部分
                        if line.startswith("--find-links="):
                            path_part = line.split("=", 1)[1].strip()
                        else:
                            path_part = line.split("=", 1)[1].strip()

                        # 检查是否是本地路径（不包含 ://）
                        if "://" not in path_part:
                            # 尝试解析为绝对路径
                            potential_paths = [
                                requirements.parent.parent / path_part,
                                requirements.parent / path_part,
                            ]

                            found = False
                            for potential_path in potential_paths:
                                try:
                                    resolved = potential_path.resolve()
                                    if resolved.exists() and resolved.is_dir():
                                        # 替换为绝对路径
                                        if line.startswith("--find-links="):
                                            fixed_line = f"--find-links={resolved}"
                                        else:
                                            fixed_line = f"-f={resolved}"
                                        standard_packages.append(fixed_line)
                                        found = True
                                        break
                                except:
                                    pass

                            if found:
                                continue
                            # 找不到目录，忽略这个选项（避免 uv 报错）

                    # 其他选项行保持原样
                    standard_packages.append(original_line)
                    continue

                # 检测是否是本地路径
                is_local_path = False

                # 明确的相对路径
                if line.startswith("./") or line.startswith("../"):
                    is_local_path = True
                # 包含 / 但不是 URL（如 subdir/package）
                elif "/" in line and "://" not in line:
                    is_local_path = True
                # 包含下划线通常是目录名（如 python_wheels）
                elif "_" in line and "://" not in line:
                    # 确保不是包名带版本（如 some_package==1.0）
                    if not any(op in line for op in ["==", ">=", "<=", "~=", ">", "<", "@"]):
                        is_local_path = True

                if not is_local_path:
                    # 尝试检查目录是否存在
                    if "://" not in line and not any(op in line for op in ["==", ">=", "<=", "~=", ">", "<", "@", "[", ";"]):
                        potential_paths = [
                            requirements.parent.parent / line,
                            requirements.parent / line,
                        ]

                        for potential_path in potential_paths:
                            try:
                                resolved = potential_path.resolve()
                                if resolved.exists() and resolved.is_dir():
                                    is_local_path = True
                                    break
                            except:
                                pass

                if is_local_path:
                    local_paths.append(line)
                else:
                    standard_packages.append(original_line)

        # 如果有本地路径，显示信息
        if local_paths:
            Logger.print_info(f"Detected {len(local_paths)} local path(s): {', '.join(local_paths)}")
            Logger.print_info("Will install standard packages from requirements, then local paths directly")

        # 策略：分两步安装以最大化速度和兼容性
        # 1. 用 uv 安装标准包（从 requirements.txt）
        # 2. 用 uv pip 直接安装本地路径（绕过 requirements.txt 解析）

        use_uv = ensure_uv_installed()

        # 步骤 1: 安装标准包
        if standard_packages:
            if use_uv:
                Logger.print_info("Installing standard packages with uv (10-100x faster)...")
                # 创建临时 requirements 文件
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
                    tmp.write('\n'.join(standard_packages))
                    tmp_req = Path(tmp.name)

                try:
                    uv_bin = get_uv_binary()
                    command = [
                        uv_bin,
                        "pip",
                        "install",
                        "--python",
                        target.joinpath("bin/python").as_posix(),
                        "-r",
                        str(tmp_req),
                    ]
                    result = run(command, stderr=PIPE, text=True)

                    if result.returncode != 0:
                        Logger.print_error(f"{result.stderr}", False)
                        raise VenvCreationFailedException("Installing standard packages failed!")

                    Logger.print_ok("Standard packages installed successfully (via uv)")
                finally:
                    tmp_req.unlink()  # 删除临时文件
            else:
                # 没有 uv，用 pip 安装所有标准包
                Logger.print_info("Installing standard packages with pip...")
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
                    tmp.write('\n'.join(standard_packages))
                    tmp_req = Path(tmp.name)

                try:
                    command = [
                        target.joinpath("bin/pip").as_posix(),
                        "install",
                        "-r",
                        str(tmp_req),
                    ]
                    result = run(command, stderr=PIPE, text=True)

                    if result.returncode != 0:
                        Logger.print_error(f"{result.stderr}", False)
                        raise VenvCreationFailedException("Installing standard packages failed!")

                    Logger.print_ok("Standard packages installed successfully")
                finally:
                    tmp_req.unlink()

        # 步骤 2: 安装本地路径（用 uv pip 直接安装路径）
        if local_paths:
            if use_uv:
                Logger.print_info("Installing local paths with uv pip...")
                uv_bin = get_uv_binary()
                for local_path in local_paths:
                    # 解析完整路径
                    if local_path.startswith("./") or local_path.startswith("../"):
                        full_path = (requirements.parent / local_path).resolve()
                    else:
                        # 尝试父目录的父目录
                        full_path = requirements.parent.parent / local_path
                        if not full_path.exists():
                            full_path = requirements.parent / local_path

                    command = [
                        uv_bin,
                        "pip",
                        "install",
                        "--python",
                        target.joinpath("bin/python").as_posix(),
                        str(full_path),
                    ]
                    result = run(command, stderr=PIPE, text=True)

                    if result.returncode != 0:
                        Logger.print_error(f"{result.stderr}", False)
                        raise VenvCreationFailedException(f"Installing local path {local_path} failed!")

                Logger.print_ok("Local paths installed successfully (via uv)")
            else:
                # 没有 uv，用 pip
                Logger.print_info("Installing local paths with pip...")
                for local_path in local_paths:
                    # 解析完整路径
                    if local_path.startswith("./") or local_path.startswith("../"):
                        full_path = (requirements.parent / local_path).resolve()
                    else:
                        # 尝试父目录的父目录
                        full_path = requirements.parent.parent / local_path
                        if not full_path.exists():
                            full_path = requirements.parent / local_path

                    command = [
                        target.joinpath("bin/pip").as_posix(),
                        "install",
                        str(full_path),
                    ]
                    result = run(command, stderr=PIPE, text=True)

                    if result.returncode != 0:
                        Logger.print_error(f"{result.stderr}", False)
                        raise VenvCreationFailedException(f"Installing local path {local_path} failed!")

                Logger.print_ok("Local paths installed successfully")

        Logger.print_ok("Installing Python requirements successful!")

    except Exception as e:
        log = f"Error installing Python requirements: {e}"
        Logger.print_error(log)
        raise VenvCreationFailedException(log)


def install_python_packages(target: Path, packages: List[str]) -> None:
    """
    Installs the python packages based on a provided packages list |
    :param target: Path of the virtualenv
    :param packages: str list of required packages
    :return: None
    """
    try:
        Logger.print_status("Installing Python requirements ...")

        # 尝试使用 uv（如果可用），如果没有则提示安装
        use_uv = ensure_uv_installed()

        if use_uv:
            uv_bin = get_uv_binary()
            command = [
                uv_bin,
                "pip",
                "install",
                "--python",
                target.joinpath("bin/python").as_posix(),
            ]
            Logger.print_info("Using uv (10-100x faster than pip)...")
        else:
            command = [target.joinpath("bin/pip").as_posix(), "install"]

        for pkg in packages:
            command.append(pkg)

        result = run(command, stderr=PIPE, text=True)

        if result.returncode != 0:
            Logger.print_error(f"{result.stderr}", False)
            raise VenvCreationFailedException("Installing Python requirements failed!")

        Logger.print_ok("Installing Python requirements successful!")

    except Exception as e:
        log = f"Error installing Python requirements: {e}"
        Logger.print_error(log)
        raise VenvCreationFailedException(log)


def update_system_package_lists(silent: bool, rls_info_change=False) -> None:
    """
    Updates the systems package list |
    :param silent: Log info to the console or not
    :param rls_info_change: Flag for "--allow-releaseinfo-change"
    :return: None
    """
    cache_mtime: float = 0
    cache_files: List[Path] = [
        Path("/var/lib/apt/periodic/update-success-stamp"),
        Path("/var/lib/apt/lists"),
    ]
    for cache_file in cache_files:
        if cache_file.exists():
            cache_mtime = max(cache_mtime, os.path.getmtime(cache_file))

    update_age = int(time.time() - cache_mtime)
    update_interval = 6 * 3600  # 48hrs

    if update_age <= update_interval:
        return

    if not silent:
        Logger.print_status("Updating package list...")

    try:
        command = ["sudo", "apt-get", "update"]
        if rls_info_change:
            command.append("--allow-releaseinfo-change")

        result = run(command, stderr=PIPE, text=True)
        if result.returncode != 0 or result.stderr:
            Logger.print_error(f"{result.stderr}", False)
            Logger.print_error("Updating system package list failed!")
            return

        Logger.print_ok("System package list update successful!")
    except CalledProcessError as e:
        Logger.print_error(f"Error updating system package list:\n{e.stderr.decode()}")
        raise


def get_upgradable_packages() -> List[str]:
    """
    Reads all system packages that can be upgraded.
    :return: A list of package names available for upgrade
    """
    try:
        command = ["apt", "list", "--upgradable"]
        output: str = check_output(command, stderr=DEVNULL, text=True, encoding="utf-8")
        pkglist = []
        for line in output.split("\n"):
            if "/" not in line:
                continue
            pkg = line.split("/")[0]
            pkglist.append(pkg)
        return pkglist
    except CalledProcessError as e:
        raise Exception(f"Error reading upgradable packages: {e}")


def check_package_install(packages: Set[str]) -> List[str]:
    """
    Checks the system for installed packages |
    :param packages: List of strings of package names
    :return: A list containing the names of packages that are not installed
    """
    not_installed = []
    for package in packages:
        command = ["dpkg-query", "-f'${Status}'", "--show", package]
        result = run(
            command,
            stdout=PIPE,
            stderr=DEVNULL,
            text=True,
        )
        if "installed" not in result.stdout.strip("'").split():
            not_installed.append(package)

    return not_installed


def install_system_packages(packages: List[str]) -> None:
    """
    Installs a list of system packages |
    :param packages: List of system package names
    :return: None
    """
    try:
        command = ["sudo", "apt-get", "install", "-y"]
        for pkg in packages:
            command.append(pkg)
        run(command, stderr=PIPE, check=True)

        Logger.print_ok("Packages successfully installed.")
    except CalledProcessError as e:
        Logger.print_error(f"Error installing packages:\n{e.stderr.decode()}")
        raise


def upgrade_system_packages(packages: List[str]) -> None:
    """
    Updates a list of system packages |
    :param packages: List of system package names
    :return: None
    """
    try:
        command = ["sudo", "apt-get", "upgrade", "-y"]
        for pkg in packages:
            command.append(pkg)
        run(command, stderr=PIPE, check=True)

        Logger.print_ok("Packages successfully upgraded.")
    except CalledProcessError as e:
        raise Exception(f"Error upgrading packages:\n{e.stderr.decode()}")


# this feels hacky and not quite right, but for now it works
# see: https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
def get_ipv4_addr() -> str:
    """
    Helper function that returns the IPv4 of the current machine
    by opening a socket and sending a package to an arbitrary IP. |
    :return: Local IPv4 of the current machine
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(("192.255.255.255", 1))
        ipv4: str = str(s.getsockname()[0])
        s.close()
        return ipv4
    except Exception:
        s.close()
        return "127.0.0.1"


def download_file(url: str, target: Path, show_progress=True) -> None:
    """
    Helper method for downloading files from a provided URL |
    :param url: the url to the file
    :param target: the target path incl filename
    :param show_progress: show download progress or not
    :return: None
    """
    try:
        if show_progress:
            urllib.request.urlretrieve(url, target, download_progress)
            sys.stdout.write("\n")
        else:
            urllib.request.urlretrieve(url, target)
    except urllib.error.HTTPError as e:
        Logger.print_error(f"Download failed! HTTP error occured: {e}")
        raise
    except urllib.error.URLError as e:
        Logger.print_error(f"Download failed! URL error occured: {e}")
        raise
    except Exception as e:
        Logger.print_error(f"Download failed! An error occured: {e}")
        raise


def download_progress(block_num, block_size, total_size) -> None:
    """
    Reporthook method for urllib.request.urlretrieve() method call in download_file() |
    :param block_num:
    :param block_size:
    :param total_size: total filesize in bytes
    :return: None
    """
    downloaded = block_num * block_size
    percent = 100 if downloaded >= total_size else downloaded / total_size * 100
    mb = 1024 * 1024
    progress = int(percent / 5)
    remaining = "-" * (20 - progress)
    dl = f"\rDownloading: [{'#' * progress}{remaining}]{percent:.2f}% ({downloaded / mb:.2f}/{total_size / mb:.2f}MB)"
    sys.stdout.write(dl)
    sys.stdout.flush()


def set_nginx_permissions() -> None:
    """
    Check if permissions of the users home directory
    grant execution rights to group and other and set them if not set.
    Required permissions for NGINX to be able to serve Mainsail/Fluidd.
    This seems to have become necessary with Ubuntu 21+. |
    :return: None
    """
    cmd = f"ls -ld {Path.home()} | cut -d' ' -f1"
    homedir_perm = run(cmd, shell=True, stdout=PIPE, text=True)
    permissions = homedir_perm.stdout

    if permissions.count("x") < 3:
        Logger.print_status("Granting NGINX the required permissions ...")
        run(["chmod", "og+x", Path.home()])
        Logger.print_ok("Permissions granted.")


def cmd_sysctl_service(name: str, action: SysCtlServiceAction) -> None:
    """
    Helper method to execute several actions for a specific systemd service. |
    :param name: the service name
    :param action: Either "start", "stop", "restart" or "disable"
    :return: None
    """
    try:
        Logger.print_status(f"{action.capitalize()} {name} ...")
        run(["sudo", "systemctl", action, name], stderr=PIPE, check=True)
        Logger.print_ok("OK!")
    except CalledProcessError as e:
        log = f"Failed to {action} {name}: {e.stderr.decode()}"
        Logger.print_error(log)
        raise


def cmd_sysctl_manage(action: SysCtlManageAction) -> None:
    try:
        run(["sudo", "systemctl", action], stderr=PIPE, check=True)
    except CalledProcessError as e:
        log = f"Failed to run {action}: {e.stderr.decode()}"
        Logger.print_error(log)
        raise


def unit_file_exists(
    name: str, suffix: Literal["service", "timer"], exclude: List[str] | None = None
) -> bool:
    """
    Checks if a systemd unit file of the provided suffix exists.
    :param name: the name of the unit file
    :param suffix: suffix of the unit file, either "service" or "timer"
    :param exclude: List of strings of names to exclude
    :return: True if the unit file exists, False otherwise
    """
    exclude = exclude or []
    pattern = re.compile(f"^{name}(-[0-9a-zA-Z]+)?.{suffix}$")
    service_list = [
        Path(SYSTEMD, service)
        for service in SYSTEMD.iterdir()
        if pattern.search(service.name) and not any(s in service.name for s in exclude)
    ]
    return any(service_list)


def log_process(process: Popen) -> None:
    """
    Helper method to print stdout of a process in near realtime to the console.
    :param process: Process to log the output from
    :return: None
    """
    while True:
        if process.stdout is not None:
            reads = [process.stdout.fileno()]
            ret = select.select(reads, [], [])
            for fd in ret[0]:
                if fd == process.stdout.fileno():
                    line = process.stdout.readline()
                    if line:
                        print(line.strip(), flush=True)
                    else:
                        break

        if process.poll() is not None:
            break


def create_service_file(name: str, content: str) -> None:
    """
    Creates a service file at the provided path with the provided content.
    :param name: the name of the service file
    :param content: the content of the service file
    :return: None
    """
    try:
        run(
            ["sudo", "tee", SYSTEMD.joinpath(name)],
            input=content.encode(),
            stdout=DEVNULL,
            check=True,
        )
        Logger.print_ok(f"Service file created: {SYSTEMD.joinpath(name)}")
    except CalledProcessError as e:
        Logger.print_error(f"Error creating service file: {e}")
        raise


def create_env_file(path: Path, content: str) -> None:
    """
    Creates an env file at the provided path with the provided content.
    :param path: the path of the env file
    :param content: the content of the env file
    :return: None
    """
    try:
        with open(path, "w") as env_file:
            env_file.write(content)
        Logger.print_ok(f"Env file created: {path}")
    except OSError as e:
        Logger.print_error(f"Error creating env file: {e}")
        raise


def remove_system_service(service_name: str) -> None:
    """
    Disables and removes a systemd service
    :param service_name: name of the service unit file - must end with '.service'
    :return: None
    """
    try:
        if not service_name.endswith(".service"):
            raise ValueError(f"service_name '{service_name}' must end with '.service'")

        file: Path = SYSTEMD.joinpath(service_name)
        if not file.exists() or not file.is_file():
            Logger.print_info(f"Service '{service_name}' does not exist! Skipped ...")
            return

        Logger.print_status(f"Removing {service_name} ...")
        cmd_sysctl_service(service_name, "stop")
        cmd_sysctl_service(service_name, "disable")
        remove_with_sudo(file)
        cmd_sysctl_manage("daemon-reload")
        cmd_sysctl_manage("reset-failed")
        Logger.print_ok(f"{service_name} successfully removed!")
    except Exception as e:
        Logger.print_error(f"Error removing {service_name}: {e}")
        raise


def get_service_file_path(instance_type: type, suffix: str) -> Path:
    from utils.common import convert_camelcase_to_kebabcase

    if not isinstance(instance_type, type):
        raise ValueError("instance_type must be a class")

    name: str = convert_camelcase_to_kebabcase(instance_type.__name__)
    if suffix != "":
        name += f"-{suffix}"

    file_path: Path = SYSTEMD.joinpath(f"{name}.service")

    return file_path


def get_distro_info() -> Tuple[str, str]:
    distro_info: str = check_output(["cat", "/etc/os-release"]).decode().strip()

    if not distro_info:
        raise ValueError("Error reading distro info!")

    distro_id: str = ""
    distro_id_like: str = ""
    distro_version: str = ""

    for line in distro_info.split("\n"):
        if line.startswith("ID="):
            distro_id = line.split("=")[1].strip('"').strip()
        if line.startswith("ID_LIKE="):
            distro_id_like = line.split("=")[1].strip('"').strip()
        if line.startswith("VERSION_ID="):
            distro_version = line.split("=")[1].strip('"').strip()

    if distro_id == "raspbian":
        distro_id = distro_id_like

    if not distro_id:
        raise ValueError("Error reading distro id!")
    if not distro_version:
        raise ValueError("Error reading distro version!")

    return distro_id.lower(), distro_version


def get_system_timezone() -> str:
    timezone = "UTC"
    try:
        with open("/etc/timezone", "r") as f:
            timezone = f.read().strip()
    except FileNotFoundError:
        # fallback to reading timezone from timedatectl
        try:
            result = run(
                ["timedatectl", "show", "--property=Timezone"],
                capture_output=True,
                text=True,
                check=True,
            )
            timezone = result.stdout.strip().split("=")[1]
        except CalledProcessError:
            # fallback if timedatectl fails, try reading from readlink
            try:
                result = run(
                    ["readlink", "-f", "/etc/localtime"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                timezone = result.stdout.strip().split("zoneinfo/")[1]
            except (CalledProcessError, IndexError):
                Logger.print_warn("Could not determine system timezone, using UTC")
    return timezone

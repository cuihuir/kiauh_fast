from __future__ import annotations

import shutil
from pathlib import Path
from subprocess import CalledProcessError, run

from components.go2rtc import (
    GO2RTC_BIN_FILE,
    GO2RTC_CONFIG_DIR,
    GO2RTC_CONFIG_FILE,
    GO2RTC_DIR,
    GO2RTC_SERVICE_FILE,
    GO2RTC_SERVICE_NAME,
    get_go2rtc_arch,
    get_go2rtc_download_url,
)
from core.logger import Logger
from core.services.backup_service import BackupService
from core.settings.kiauh_settings import KiauhSettings
from core.types.component_status import ComponentStatus
from utils.common import get_install_status
from utils.sys_utils import (
    cmd_sysctl_service,
    create_service_file,
    download_file,
)


def install_go2rtc() -> bool:
    Logger.print_status("Installing go2rtc ...")

    try:
        arch = get_go2rtc_arch()
        Logger.print_status(f"Detected architecture: {arch}")

        download_url = get_go2rtc_download_url()
        Logger.print_status(f"Downloading go2rtc from {download_url} ...")

        GO2RTC_DIR.mkdir(parents=True, exist_ok=True)
        temp_bin = GO2RTC_DIR.joinpath("go2rtc_temp")

        download_file(download_url, temp_bin, show_progress=True)

        Logger.print_status("Installing go2rtc binary ...")
        run(["sudo", "cp", str(temp_bin), str(GO2RTC_BIN_FILE)], check=True)
        run(["sudo", "chmod", "+x", str(GO2RTC_BIN_FILE)], check=True)

        temp_bin.unlink(missing_ok=True)

        create_go2rtc_config()
        create_go2rtc_service()
        setup_nginx_proxy()

        cmd_sysctl_service(GO2RTC_SERVICE_NAME, "enable")
        cmd_sysctl_service(GO2RTC_SERVICE_NAME, "start")

        Logger.print_ok("go2rtc installed successfully!")
        Logger.print_info("Web interface: http://localhost:1984")
        Logger.print_info(f"Config file: {GO2RTC_CONFIG_FILE}")
        return True

    except CalledProcessError as e:
        Logger.print_error(f"Installation failed: {e}")
        return False
    except Exception as e:
        Logger.print_error(f"Installation failed: {e}")
        return False


def create_go2rtc_config() -> None:
    if GO2RTC_CONFIG_FILE.exists():
        Logger.print_info(f"Config file already exists: {GO2RTC_CONFIG_FILE}")
        return

    Logger.print_status("Creating go2rtc config file ...")

    GO2RTC_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    default_config = """# go2rtc configuration
# Documentation: https://github.com/AlexxIT/go2rtc#configuration

# API server (default port 1984)
api:
  listen: ":1984"
  origin: "*"

# RTSP server (default port 8554)
rtsp:
  listen: ":8554"

# WebRTC (default port 8555)
webrtc:
  listen: ":8555"

# Add your camera streams here
# streams:
#   camera1: rtsp://admin:password@192.168.1.100:554/stream1
#   camera2: rtsp://admin:password@192.168.1.101:554/stream2
"""

    with open(GO2RTC_CONFIG_FILE, "w") as f:
        f.write(default_config)

    Logger.print_ok(f"Config file created: {GO2RTC_CONFIG_FILE}")


def create_go2rtc_service() -> None:
    if GO2RTC_SERVICE_FILE.exists():
        Logger.print_info(f"Service file already exists: {GO2RTC_SERVICE_FILE}")
        return

    Logger.print_status("Creating go2rtc systemd service ...")

    service_content = f"""[Unit]
Description=go2rtc - Ultimate camera streaming application
After=network.target

[Service]
Type=simple
User={get_current_user()}
ExecStart={GO2RTC_BIN_FILE} -config {GO2RTC_CONFIG_FILE}
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
"""

    create_service_file(GO2RTC_SERVICE_NAME, service_content)
    run(["sudo", "systemctl", "daemon-reload"], check=True)

    Logger.print_ok("Systemd service created!")


def setup_nginx_proxy() -> None:
    Logger.print_status("Setting up Nginx proxy for go2rtc ...")

    upstream_conf = Path("/etc/nginx/conf.d/upstreams.conf")
    mainsail_conf = Path("/etc/nginx/sites-enabled/mainsail")

    if not upstream_conf.exists() or not mainsail_conf.exists():
        Logger.print_warn("Nginx configuration files not found, skipping proxy setup")
        Logger.print_info("You can manually configure Nginx later (see docs/go2rtc.md)")
        return

    try:
        upstream_content = upstream_conf.read_text()
        if "upstream go2rtc" not in upstream_content:
            upstream_content += """

upstream go2rtc {
    ip_hash;
    server 127.0.0.1:1984;
}
"""
            run(
                ["sudo", "tee", str(upstream_conf)],
                input=upstream_content.encode(),
                check=True,
            )
            Logger.print_ok("Added go2rtc upstream to Nginx")

        mainsail_content = mainsail_conf.read_text()
        if "location /webcam/" not in mainsail_content:
            webcam_block = """
    location /webcam/ {
        postpone_output 0;
        proxy_buffering off;
        proxy_ignore_headers X-Accel-Buffering;
        access_log off;
        error_log off;
        proxy_pass http://go2rtc/api/stream.mjpeg?src=usb_camera&;
    }

    location /webcam/webrtc {
        postpone_output 0;
        proxy_buffering off;
        proxy_ignore_headers X-Accel-Buffering;
        access_log off;
        error_log off;
        proxy_pass http://go2rtc/api/webrtc?src=usb_camera&;
    }

    location /webcam/snapshot {
        access_log off;
        error_log off;
        proxy_pass http://go2rtc/api/frame.jpeg?src=usb_camera&;
    }
"""
            insert_pos = mainsail_content.rfind("}")
            if insert_pos > 0:
                new_content = (
                    mainsail_content[:insert_pos]
                    + webcam_block
                    + mainsail_content[insert_pos:]
                )
                run(
                    ["sudo", "tee", str(mainsail_conf)],
                    input=new_content.encode(),
                    check=True,
                )
                Logger.print_ok("Added go2rtc locations to Nginx")

        run(["sudo", "systemctl", "reload", "nginx"], check=False)
        Logger.print_ok("Nginx proxy configured!")
        Logger.print_info(
            "You can now configure Mailsail with relative URLs (no IP needed)"
        )
        Logger.print_info("See docs/go2rtc.md for Moonraker configuration examples")

    except Exception as e:
        Logger.print_warn(f"Nginx proxy setup failed: {e}")
        Logger.print_info("You can manually configure Nginx later (see docs/go2rtc.md)")


def get_current_user() -> str:
    import os

    return os.getenv("USER") or os.getenv("LOGNAME") or "pi"


def update_go2rtc() -> None:
    Logger.print_status("Updating go2rtc ...")

    try:
        cmd_sysctl_service(GO2RTC_SERVICE_NAME, "stop")

        settings = KiauhSettings()
        if settings.kiauh.backup_before_update:
            svc = BackupService()
            svc.backup_directory(
                source_path=GO2RTC_DIR,
                target_path="go2rtc",
                backup_name="go2rtc",
            )

        arch = get_go2rtc_arch()
        download_url = get_go2rtc_download_url()
        temp_bin = GO2RTC_DIR.joinpath("go2rtc_temp")

        Logger.print_status(f"Downloading latest go2rtc ({arch}) ...")
        download_file(download_url, temp_bin, show_progress=True)

        run(["sudo", "cp", str(temp_bin), str(GO2RTC_BIN_FILE)], check=True)
        run(["sudo", "chmod", "+x", str(GO2RTC_BIN_FILE)], check=True)

        temp_bin.unlink(missing_ok=True)

        cmd_sysctl_service(GO2RTC_SERVICE_NAME, "start")

        Logger.print_ok("go2rtc updated successfully!")

    except CalledProcessError as e:
        Logger.print_error(f"Update failed: {e}")
        return
    except Exception as e:
        Logger.print_error(f"Update failed: {e}")
        return


def get_go2rtc_status() -> ComponentStatus:
    files = [
        GO2RTC_BIN_FILE,
        GO2RTC_CONFIG_FILE,
        GO2RTC_SERVICE_FILE,
    ]
    return get_install_status(GO2RTC_DIR, files=files)


def remove_go2rtc() -> None:
    if not GO2RTC_BIN_FILE.exists():
        Logger.print_info("go2rtc does not seem to be installed! Skipping ...")
        return

    Logger.print_status("Removing go2rtc ...")

    try:
        cmd_sysctl_service(GO2RTC_SERVICE_NAME, "stop")
        cmd_sysctl_service(GO2RTC_SERVICE_NAME, "disable")

        if GO2RTC_SERVICE_FILE.exists():
            run(["sudo", "rm", str(GO2RTC_SERVICE_FILE)], check=True)
            run(["sudo", "systemctl", "daemon-reload"], check=True)

        if GO2RTC_BIN_FILE.exists():
            run(["sudo", "rm", str(GO2RTC_BIN_FILE)], check=True)

        if GO2RTC_DIR.exists():
            shutil.rmtree(GO2RTC_DIR)

        from utils.input_utils import get_confirm

        if GO2RTC_CONFIG_FILE.exists():
            if get_confirm("Remove go2rtc config file?", default_choice=False):
                GO2RTC_CONFIG_FILE.unlink()
                Logger.print_ok("Config file removed!")
            else:
                Logger.print_info("Config file kept.")

        Logger.print_ok("go2rtc removed successfully!")

    except CalledProcessError as e:
        Logger.print_error(f"Removal failed: {e}")
        return
    except Exception as e:
        Logger.print_error(f"Removal failed: {e}")
        return

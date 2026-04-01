<p align="center">
    <img src="docs/assets/logo-large.png" alt="KIAUH Fast Logo" height="181">
    <h1 align="center">KIAUH Fast</h1>
    <h3 align="center">A simplified fork of KIAUH</h3>
</p>

<p align="center">
  <a href="https://github.com/dw-0/kiauh"><img src="https://img.shields.io/badge/Based%20on-KIAUH-blue"></a>
  <a><img src="https://img.shields.io/badge/Python-3.8+-green"></a>
  <a><img src="https://img.shields.io/badge/License-GPL--3.0-orange"></a>
  <a href="README_zh.md"><img src="https://img.shields.io/badge/文档-中文版-red"></a>
</p>

---

A fork of [KIAUH](https://github.com/dw-0/kiauh) with two additions:

1. **Quick Install / Uninstall** — Select components with checkboxes and install or remove them in one go
2. **Mirror Acceleration** — Configure PyPI, APT, and uv mirrors for better download speeds in China

> Note: uv only speeds up the Python dependency installation step. System operations like `apt update` and `apt install` are unaffected and can still take significant time depending on your network.

---

## Quick Start

```bash
git clone https://github.com/cuihuir/kiauh_fast.git
cd kiauh_fast
./kiauh.sh
```

**For users in China**: Go to option 3 (Mirror Acceleration) first to configure mirrors before installing.

---

## Main Menu

```
1) Quick Install  — Checkbox-based component installation
2) Quick Remove   — Checkbox-based component removal
3) Mirror         — Mirror acceleration configuration
4) Manual         — Full original KIAUH menu
```

---

## Components

| Component | Description | Notes |
|-----------|-------------|-------|
| Klipper | 3D printer firmware | Required |
| Moonraker | API server | Required |
| Mainsail | Web UI | Default port 80 |
| Fluidd | Web UI | Default port 81 |
| KlipperScreen | Touchscreen UI | Reboot required after install |
| Crowsnest | Webcam streaming | — |
| go2rtc | Webcam streaming (alternative) | [Usage Guide](docs/go2rtc.md) |

---

## Documentation

- [go2rtc 使用指南](docs/go2rtc.md) — 摄像头流媒体配置和使用说明

---

## Differences from KIAUH

- Added Quick Install and Quick Remove menus
- Added mirror acceleration for China users
- All original KIAUH functionality is preserved under the Manual menu
- Synced upstream bug fixes and new features (TMC Autotune, etc.)

---

## Requirements

- Debian 10/11/12 / Ubuntu 20.04/22.04/24.04 / Raspberry Pi OS
- Python 3.8+
- Raspberry Pi / Orange Pi / other ARM or x86_64 SBCs

---

## Credits

- [dw-0/kiauh](https://github.com/dw-0/kiauh) — Original project
- [Tsinghua TUNA](https://mirrors.tuna.tsinghua.edu.cn/) — Mirror source

---

## License

GNU General Public License v3.0 — same as the original [KIAUH](https://github.com/dw-0/kiauh/blob/master/LICENSE).

<p align="center">
    <img src="docs/assets/logo-large.png" alt="KIAUH Fast Logo" height="181">
    <h1 align="center">KIAUH Fast</h1>
    <h3 align="center">KIAUH 的简化优化版本</h3>
</p>

<p align="center">
  <a href="https://github.com/dw-0/kiauh"><img src="https://img.shields.io/badge/Based%20on-KIAUH-blue"></a>
  <a><img src="https://img.shields.io/badge/Python-3.8+-green"></a>
  <a><img src="https://img.shields.io/badge/License-GPL--3.0-orange"></a>
</p>

---

基于 [KIAUH](https://github.com/dw-0/kiauh) 的 fork，主要做了两件事：

1. **一键安装/卸载** — 复选框选择组件，一次性完成，减少交互步骤
2. **中国镜像加速** — 一键配置 PyPI、APT、uv 镜像源，改善国内网络下的下载速度

> 注意：uv 只加速 Python 依赖安装这一步，apt update/install 等系统操作耗时不受影响，整体安装时间取决于网络状况。

---

## 快速开始

```bash
git clone https://github.com/cuihuir/kiauh_fast.git
cd kiauh_fast
./kiauh.sh
```

**中国用户建议**：先进入选项 3（镜像加速）配置镜像源，再使用选项 1 安装。

---

## 主菜单

```
1) Quick Install  — 一键安装，复选框选择组件
2) Quick Remove   — 一键卸载，复选框选择组件
3) Mirror         — 镜像加速配置
4) Manual         — 原版 KIAUH 完整菜单
```

---

## 可安装组件

| 组件 | 说明 | 备注 |
|------|------|------|
| Klipper | 3D 打印机固件 | 必需 |
| Moonraker | API 服务器 | 必需 |
| Mainsail | Web UI | 默认端口 80 |
| Fluidd | Web UI | 默认端口 81 |
| KlipperScreen | 触摸屏 UI | 安装后需重启 |
| Crowsnest | 摄像头串流 | — |

---

## 与原版 KIAUH 的区别

- 新增一键安装/卸载菜单，减少重复操作
- 新增镜像加速配置（中国用户）
- 原版 KIAUH 所有功能完整保留在「手工安装」菜单中
- 同步上游 bug fix 和新功能（TMC Autotune 等）

---

## 系统要求

- Debian 10/11/12 / Ubuntu 20.04/22.04/24.04 / Raspberry Pi OS
- Python 3.8+
- Raspberry Pi / Orange Pi / 其他 ARM 或 x86_64 单板机

---

## 致谢

- [dw-0/kiauh](https://github.com/dw-0/kiauh) — 原版项目
- [Tsinghua TUNA](https://mirrors.tuna.tsinghua.edu.cn/) — 镜像源

---

## License

GNU General Public License v3.0 — 同原版 [KIAUH](https://github.com/dw-0/kiauh/blob/master/LICENSE)。

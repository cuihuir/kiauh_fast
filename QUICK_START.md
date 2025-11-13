# KIAUH Fast - Quick Start Guide / 快速开始指南

## 🚀 5 分钟快速安装 Klipper 全家桶

### 中国用户推荐流程 / Recommended for China Users

```bash
# 1. 启动 KIAUH
./kiauh.sh

# 2. 配置镜像加速（选项 2）
2  # Mirror Acceleration
1  # Quick Setup China Mirrors
Y  # 确认配置

# 3. 返回主菜单（按 B）
B  # Back to Main Menu

# 4. 一键安装（选项 1）
1  # Quick Install Klipper Stack

# 5. 选择组件（输入数字切换选择）
1  # 选择 Klipper ✓
2  # 选择 Moonraker ✓
3  # 选择 Mainsail ✓
# 4, 5, 6 可选

# 6. 开始安装
S  # Start Installation
Y  # 确认安装

# 7. 等待安装完成（可能需要输入 sudo 密码）
# 预计时间：5-8 分钟（使用镜像）
```

### 国际用户流程 / For International Users

```bash
# 1. 启动 KIAUH
./kiauh.sh

# 2. 一键安装（选项 1）
1  # Quick Install Klipper Stack

# 3. 选择组件
1  # Klipper ✓
2  # Moonraker ✓
3  # Mainsail ✓

# 4. 开始安装
S  # Start Installation
Y  # 确认

# 预计时间：15-20 分钟
```

---

## 📋 三大核心功能 / Three Core Features

### 1️⃣ 一键安装 Klipper 全家桶
**Quick Install Klipper Stack**

- ✅ 通过复选框选择组件
- ✅ 全自动安装
- ✅ 智能端口分配（80 → 81）
- ✅ 自动处理安装顺序

**适合**: 新用户、快速部署

### 2️⃣ 镜像加速
**Mirror Acceleration**

- ✅ 一键配置中国镜像
- ✅ PyPI + APT + uv 镜像
- ✅ 安装速度提升 10-50x

**适合**: 中国大陆用户

### 3️⃣ 手工安装
**Manual Installation**

- ✅ 保留原 KIAUH 所有功能
- ✅ 逐步安装，完全控制
- ✅ 高级配置选项

**适合**: 高级用户、特殊需求

---

## 🎯 组件选择指南 / Component Selection Guide

| 组件 | 必需 | 说明 |
|------|------|------|
| **Klipper** | ✓ 必选 | 3D 打印机固件，核心组件 |
| **Moonraker** | ✓ 必选 | API 服务，核心组件 |
| **Mainsail** | 推荐 | Web 管理界面（推荐） |
| **Fluidd** | 可选 | Web 管理界面（备选） |
| **KlipperScreen** | 可选 | 触摸屏界面（需要重启） |
| **Crowsnest** | 可选 | 摄像头串流（监控打印） |

**建议搭配**:
- **最小安装**: Klipper + Moonraker + Mainsail
- **完整安装**: 全部选择

---

## ⚡ 镜像加速效果 / Mirror Acceleration Performance

### 中国用户（使用镜像）

| 项目 | 不使用镜像 | 使用镜像 | 提升 |
|------|----------|---------|------|
| Python 依赖 | 3-4 分钟 | 20-30 秒 | **85-90% ↓** |
| 系统包安装 | 2-5 分钟 | 30-60 秒 | **70-80% ↓** |
| **总安装时间** | **15-20 分钟** | **5-8 分钟** | **60-70% ↓** |

---

## 🔧 常见问题 / FAQ

### Q1: 我应该选择哪些组件？

**最小配置**: Klipper + Moonraker + Mainsail
- 适合新用户和基础使用

**推荐配置**: Klipper + Moonraker + Mainsail + Crowsnest
- 适合大多数用户

**完整配置**: 全选
- 适合需要触摸屏的用户

### Q2: Mainsail 和 Fluidd 有什么区别？

两者都是 Web 管理界面，功能类似：
- **Mainsail**: 界面更现代，推荐新用户
- **Fluidd**: 界面更传统，性能稍快

建议只选择一个。

### Q3: 为什么 KlipperScreen 需要重启？

KlipperScreen 需要配置显示驱动，必须重启系统才能生效。安装程序会自动在最后安装 KlipperScreen，并提示是否立即重启。

### Q4: 镜像加速会影响国际用户吗？

不会。镜像加速：
- 仅在检测到中国网络时提示
- 不强制配置
- 国际用户不会看到任何镜像相关提示

### Q5: 安装失败怎么办？

1. 查看错误信息
2. 确认网络连接正常
3. 如果在中国，确认已配置镜像加速
4. 使用选项 3（手工安装）逐步排查

### Q6: 我可以修改端口吗？

**一键安装**: 端口自动分配（80 → 81）

**手工安装**: 在 Settings 菜单中可以自定义端口

### Q7: 安装后如何访问？

**Mainsail**: http://打印机IP:80
**Fluidd**: http://打印机IP:81 (如果两者都安装)

### Q8: 如何查看安装状态？

选择选项 3（手工安装），进入后可以看到所有组件的安装状态。

---

## 📞 获取帮助 / Get Help

### 查看完整文档

- `SIMPLIFIED_UX.md` - 完整用户体验文档
- `CHINA_ACCELERATION_GUIDE.md` - 镜像加速详细指南
- `OPTIMIZATION_SUMMARY.md` - 技术优化总结

### 问题报告

提供以下信息有助于快速解决问题：
```bash
# 系统信息
cat /etc/os-release

# KIAUH 版本
# 显示在主菜单底部

# 错误日志
# 截图或复制完整错误信息
```

---

## 🎯 典型使用场景 / Use Cases

### 场景 1: 全新安装

```
目标: 在新树莓派上安装完整的 Klipper 系统

步骤:
1. 配置镜像（如果在中国）
2. 一键安装，选择: Klipper + Moonraker + Mainsail + Crowsnest
3. 等待安装完成（5-8 分钟）
4. 访问 http://打印机IP 开始配置
```

### 场景 2: 只安装 KlipperScreen

```
目标: 在已有系统上添加触摸屏支持

步骤:
1. 选择手工安装（选项 3）
2. 选择 Install → KlipperScreen
3. 安装完成后重启系统
```

### 场景 3: 更新所有组件

```
目标: 更新所有已安装的组件

步骤:
1. 选择手工安装（选项 3）
2. 选择 Update → All
3. 等待更新完成
```

---

## ✅ 检查清单 / Checklist

### 安装前

- [ ] 确认系统是 Debian/Ubuntu/Raspberry Pi OS
- [ ] 网络连接正常
- [ ] 如果在中国，已配置镜像加速
- [ ] 准备好 sudo 密码

### 安装后

- [ ] 所有选择的组件安装成功
- [ ] 可以访问 Web 界面
- [ ] 打印机可以连接
- [ ] （如果安装了 Crowsnest）摄像头可以查看
- [ ] （如果安装了 KlipperScreen）触摸屏显示正常

---

## 🚀 下一步 / Next Steps

安装完成后：

1. **配置打印机**
   - 访问 Mainsail/Fluidd Web 界面
   - 上传打印机配置文件
   - 连接打印机

2. **测试功能**
   - 测试加热
   - 测试移动
   - 测试挤出

3. **开始打印**
   - 上传 G-code 文件
   - 开始首次打印

---

**快速参考**: 2025-11-13
**适用版本**: KIAUH Fast 2.0
**状态**: ✅ 就绪使用

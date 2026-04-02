# go2rtc 使用指南

[go2rtc](https://github.com/AlexxIT/go2rtc) 是一个终极摄像头流媒体应用，支持多种格式和协议，提供零延迟的视频流。

## 目录

- [特性](#特性)
- [安装](#安装)
- [配置摄像头](#配置摄像头)
- [访问摄像头](#访问摄像头)
- [Nginx 代理配置](#nginx-代理配置)
- [常见摄像头配置](#常见摄像头配置)
- [故障排除](#故障排除)

## 特性

- ✅ 零依赖、零延迟
- ✅ 支持多种协议：RTSP、RTMP、HTTP、WebRTC
- ✅ 支持多种品牌：海康威视、大华、TP-Link、小米等
- ✅ 内置 Web 管理界面
- ✅ 支持 USB 摄像头
- ✅ 自动音频转码
- ✅ 支持多摄像头同时监控

## 安装

通过 KIAUH Fast 快速安装：

1. 运行 `./kiauh.sh`
2. 选择 `1) Quick Install`
3. 勾选 `7) go2rtc`
4. 按 `S` 开始安装

安装完成后：
- Web 界面：`http://localhost:1984`
- 配置文件：`~/printer_data/config/go2rtc.yaml`
- 服务状态：`systemctl status go2rtc`

## 配置摄像头

### 配置文件位置

```bash
~/printer_data/config/go2rtc.yaml
```

### 基本格式

```yaml
streams:
  <摄像头名称>: <流地址>
```

### 添加摄像头步骤

1. **编辑配置文件**
   ```bash
   nano ~/printer_data/config/go2rtc.yaml
   ```

2. **添加摄像头流**（参考下方示例）

3. **重启服务**
   ```bash
   sudo systemctl restart go2rtc
   ```

4. **访问 Web 界面**
   ```
   http://<树莓派IP>:1984
   ```

## 访问摄像头

### 方式一：Web 界面（推荐）

访问 `http://localhost:1984`，点击摄像头名称即可观看。

**优点**：零延迟、支持音频、双向语音

### 方式二：RTSP 流

```
rtsp://localhost:8554/<摄像头名称>
```

**用途**：OBS、VLC、Home Assistant、Frigate

### 方式三：HLS 流

```
http://localhost:1984/api/stream.m3u8?src=<摄像头名称>
```

**用途**：iOS 设备、网页嵌入

### 方式四：MJPEG 流

```
http://localhost:1984/api/stream.mjpeg?src=<摄像头名称>
```

**用途**：旧设备、简单网页嵌入

## Mainsail 配置

Mainsail **原生支持 go2rtc**，无需配置 Nginx 代理。但需要注意：**必须使用树莓派的 IP 地址**，不能使用 `localhost`。

### 配置步骤

1. **安装 go2rtc**
   - 运行 `./kiauh.sh` → Quick Install → 勾选 `7) go2rtc`

2. **配置摄像头**
   - 编辑 `~/printer_data/config/go2rtc.yaml`
   - 添加摄像头流（参考上方示例）
   - 重启 go2rtc：`sudo systemctl restart go2rtc`

3. **在 Mainsail 中添加摄像头**

   打开 Mainsail → 右上角齿轮图标 → **Webcams** → **Add Webcam**

### 配置示例

假设你的 `go2rtc.yaml` 配置：

```yaml
streams:
  printer_cam: rtsp://admin:password@192.168.1.100:554/stream1
```

在 Mainsail 中配置：

| 字段 | 值 |
|------|-----|
| **Name** | Printer Camera |
| **URL Stream** | `http://<树莓派IP>:1984/stream.html?src=printer_cam` |
| **URL Snapshot** | `http://<树莓派IP>:1984/api/frame.jpeg?src=printer_cam` |
| **Service** | **WebRTC (go2rtc)** |
| **Enable Audio** | 可选（go2rtc 支持音频） |

> ⚠️ **重要**：将 `<树莓派IP>` 替换为实际 IP 地址，如 `192.168.1.50`
> 
> ❌ 错误：`http://localhost:1984/...`（只能本地访问）
> 
> ✅ 正确：`http://192.168.1.50:1984/...`（可远程访问）

### 方式一：在 Moonraker 中配置（推荐）

通过 Moonraker 配置，前端会自动识别摄像头。

编辑 `~/printer_data/config/moonraker.conf`，添加：

```ini
[webcam printer_cam]
service: webrtc-go2rtc
target_fps: 30
stream_url: http://<树莓派IP>:1984/stream.html?src=printer_cam
snapshot_url: http://<树莓派IP>:1984/api/frame.jpeg?src=printer_cam
flip_horizontal: False
flip_vertical: False
rotation: 0
aspect_ratio: 16:9
```

保存后重启 Moonraker：`sudo systemctl restart moonraker`

### 方式二：在 Mainsail 界面中直接配置

如上所述，在 Mainsail 的 Webcams 设置中手动添加。

### 支持的 Service 类型

Mainsail 支持多种 go2rtc 流类型：

| Service | 说明 | 延迟 |
|---------|------|------|
| **WebRTC (go2rtc)** | 推荐，零延迟，支持音频 | 最低 |
| **HLS Stream** | HTTP Live Streaming | 较高 |
| **MJPEG-Streamer** | 传统 MJPEG 流 | 中等 |

### 为什么推荐 WebRTC (go2rtc)？

- ✅ **零延迟**：实时查看打印状态
- ✅ **低带宽**：比 MJPEG 更省流量
- ✅ **支持音频**：可听到打印声音
- ✅ **自动适配**：根据网络状况自动调整

## Nginx 代理配置（可选）

如果你需要通过统一的 `/webcam/` 路径访问（如某些旧版配置或第三方工具），可以配置 Nginx 代理。

> ⚠️ **注意**：对于 Mainsail + go2rtc 的标准使用场景，通常**不需要**配置 Nginx 代理。

<details>
<summary>点击展开 Nginx 代理配置（可选）</summary>

#### 1. 添加 upstream

编辑 `/etc/nginx/conf.d/upstreams.conf`：

```nginx
upstream go2rtc {
    ip_hash;
    server 127.0.0.1:1984;
}
```

#### 2. 添加 location 代理

编辑 `/etc/nginx/sites-enabled/mainsail`：

```nginx
location /webcam/ {
    postpone_output 0;
    proxy_buffering off;
    proxy_ignore_headers X-Accel-Buffering;
    access_log off;
    error_log off;
    proxy_pass http://go2rtc/api/stream.mjpeg?src=camera1&;
}
```

#### 3. 重启 Nginx

```bash
sudo systemctl restart nginx
```

配置完成后，可通过 `/webcam/?action=stream` 访问 MJPEG 流。

</details>

### 访问方式对比

| 方式 | 地址 | 推荐场景 |
|------|------|----------|
| **Moonraker 配置** | 在 moonraker.conf 中配置 | ✅ **最推荐** |
| **Mainsail 原生** | Mainsail 设置中配置 WebRTC (go2rtc) | ✅ 推荐 |
| go2rtc Web | `http://<IP>:1984` | 管理和调试 |
| RTSP | `rtsp://<IP>:8554/<摄像头名称>` | 第三方软件 |
| Nginx 代理 | `http://<IP>/webcam/?action=stream` | 旧版配置（不推荐） |

### 配置后能否单独访问？

**可以！** go2rtc 的所有功能都保持可用：

- ✅ go2rtc Web 界面：`http://<IP>:1984`
- ✅ WebRTC（通过 Mainsail 或 go2rtc Web）
- ✅ MJPEG：`http://<IP>:1984/api/stream.mjpeg?src=<摄像头名称>`
- ✅ RTSP：`rtsp://<IP>:8554/<摄像头名称>`
- ✅ HLS：`http://<IP>:1984/api/stream.m3u8?src=<摄像头名称>`

## 常见摄像头配置

### 海康威视

```yaml
streams:
  hikvision_main: rtsp://admin:password@192.168.1.100:554/Streaming/Channels/101
  hikvision_sub: rtsp://admin:password@192.168.1.100:554/Streaming/Channels/102
```

### 大华

```yaml
streams:
  dahua_main: rtsp://admin:password@192.168.1.101:554/cam/realmonitor?channel=1&subtype=0
  dahua_sub: rtsp://admin:password@192.168.1.101:554/cam/realmonitor?channel=1&subtype=1
```

### TP-Link Tapo

```yaml
streams:
  tapo_main: rtsp://admin:password@192.168.1.102:554/stream1
  tapo_sub: rtsp://admin:password@192.168.1.102:554/stream2
```

### 小米（需开启 RTSP）

```yaml
streams:
  xiaomi: rtsp://admin:password@192.168.1.103:8554/live/ch00_0
```

### USB 摄像头

```yaml
streams:
  usb_camera: v4l2:///dev/video0
```

### 带音频转码的配置

```yaml
streams:
  camera_with_audio:
    - rtsp://admin:password@192.168.1.100:554/stream1
    - ffmpeg:rtsp://admin:password@192.168.1.100:554/stream1#audio=opus
```

## 完整配置示例

```yaml
# go2rtc 配置文件
api:
  listen: ":1984"

rtsp:
  listen: ":8554"

webrtc:
  listen: ":8555"

streams:
  # 前门摄像头（海康威视）
  front_door: rtsp://admin:password1@192.168.1.100:554/Streaming/Channels/101
  
  # 后院摄像头（大华）
  backyard: rtsp://admin:password2@192.168.1.101:554/cam/realmonitor?channel=1&subtype=0
  
  # 车库摄像头（TP-Link）
  garage: rtsp://admin:password3@192.168.1.102:554/stream1
  
  # 3D 打印机摄像头（USB）
  printer: v4l2:///dev/video0
```

## 故障排除

### 检查服务状态

```bash
systemctl status go2rtc
```

### 查看日志

```bash
journalctl -u go2rtc -f
```

### 测试 RTSP 连接

```bash
ffprobe rtsp://admin:password@192.168.1.100:554/stream1
```

### 检查摄像头是否可达

```bash
ping 192.168.1.100
```

### 常见问题

**Q: 看不到视频流？**

A: 检查以下几点：
1. 摄像头 IP 地址是否正确
2. 用户名密码是否正确
3. 摄像头是否在同一网络
4. RTSP 地址是否正确（可用 VLC 测试）

**Q: 有画面没有声音？**

A: 部分摄像头音频格式不兼容，需要添加音频转码：
```yaml
streams:
  camera:
    - rtsp://admin:password@192.168.1.100:554/stream1
    - ffmpeg:rtsp://admin:password@192.168.1.100:554/stream1#audio=opus
```

**Q: 延迟很高？**

A: 使用 WebRTC 方式观看（Web 界面），这是延迟最低的方式。

**Q: 如何从外部网络访问？**

A: 需要在路由器中转发端口：
- 1984 (TCP) - Web 界面
- 8554 (TCP) - RTSP
- 8555 (TCP/UDP) - WebRTC

⚠️ 注意：开放端口有安全风险，建议使用 VPN 或反向代理。

## 更多信息

- [go2rtc 官方文档](https://github.com/AlexxIT/go2rtc)
- [支持的协议列表](https://github.com/AlexxIT/go2rtc#streaming-input)
- [硬件加速](https://github.com/AlexxIT/go2rtc/wiki/Hardware-acceleration)

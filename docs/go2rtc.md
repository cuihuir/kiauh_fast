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

Mainsail **原生支持 go2rtc**。有两种配置方式：

### 方式一：配置 Nginx 代理（推荐，无需写 IP）

配置 Nginx 后，可以像 crowsnest 一样使用相对路径 `/webcam/?action=stream`。

#### 1. 添加 upstream

编辑 `/etc/nginx/conf.d/upstreams.conf`，添加：

```nginx
upstream go2rtc {
    ip_hash;
    server 127.0.0.1:1984;
}
```

#### 2. 添加 location 代理

编辑 `/etc/nginx/sites-enabled/mainsail`，添加：

```nginx
location /webcam/ {
    postpone_output 0;
    proxy_buffering off;
    proxy_ignore_headers X-Accel-Buffering;
    access_log off;
    error_log off;
    proxy_pass http://go2rtc/api/stream.mjpeg?src=printer_cam&;
}

location /webcam/webrtc {
    postpone_output 0;
    proxy_buffering off;
    proxy_ignore_headers X-Accel-Buffering;
    access_log off;
    error_log off;
    proxy_pass http://go2rtc/api/webrtc?src=printer_cam&;
}

location /webcam/snapshot {
    access_log off;
    error_log off;
    proxy_pass http://go2rtc/api/frame.jpeg?src=printer_cam&;
}
```

> 💡 将 `printer_cam` 替换为你在 `go2rtc.yaml` 中配置的摄像头名称

#### 3. 重启 Nginx

```bash
sudo systemctl restart nginx
```

#### 4. 在 Moonraker 中配置（无需写 IP）

编辑 `~/printer_data/config/moonraker.conf`，添加：

```ini
[webcam printer_cam]
service: webrtc-go2rtc
target_fps: 30
stream_url: /webcam/webrtc
snapshot_url: /webcam/snapshot
flip_horizontal: False
flip_vertical: False
rotation: 0
aspect_ratio: 16:9
```

保存后重启 Moonraker：`sudo systemctl restart moonraker`

#### 5. 在 Mailsail 中验证

打开 Mailsail，摄像头应该自动出现。如果没有：
- Settings → Webcams → 检查是否启用了摄像头
- 刷新页面

### 方式二：直接使用 IP 地址（无需配置 Nginx）

如果你不想配置 Nginx，可以使用树莓派的 IP 地址。

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

> ⚠️ **注意**：
> - 必须使用树莓派的实际 IP 地址，如 `192.168.1.100`
> - 浏览器必须能够访问这个地址（同一局域网或端口已开放）
> - ❌ 不能使用 `localhost`（只能本地访问）

### 配置示例

假设你的 `go2rtc.yaml` 配置：

```yaml
streams:
  printer_cam: rtsp://admin:password@192.168.1.100:554/stream1
```

#### 使用 Nginx 代理（推荐）

```ini
[webcam printer_cam]
service: webrtc-go2rtc
stream_url: /webcam/webrtc
snapshot_url: /webcam/snapshot
```

#### 使用 IP 地址

```ini
[webcam printer_cam]
service: webrtc-go2rtc
stream_url: http://192.168.1.50:1984/stream.html?src=printer_cam
snapshot_url: http://192.168.1.50:1984/api/frame.jpeg?src=printer_cam
```

### 支持的 Service 类型

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

### 多摄像头配置

如果有多个摄像头，需要为每个摄像头配置一个 location：

#### Nginx 配置

```nginx
# 第一个摄像头
location /webcam/ {
    proxy_pass http://go2rtc/api/stream.mjpeg?src=camera1&;
}
location /webcam/webrtc {
    proxy_pass http://go2rtc/api/webrtc?src=camera1&;
}
location /webcam/snapshot {
    proxy_pass http://go2rtc/api/frame.jpeg?src=camera1&;
}

# 第二个摄像头
location /webcam2/ {
    proxy_pass http://go2rtc/api/stream.mjpeg?src=camera2&;
}
location /webcam2/webrtc {
    proxy_pass http://go2rtc/api/webrtc?src=camera2&;
}
location /webcam2/snapshot {
    proxy_pass http://go2rtc/api/frame.jpeg?src=camera2&;
}
```

#### Moonraker 配置

```ini
[webcam camera1]
service: webrtc-go2rtc
stream_url: /webcam/webrtc
snapshot_url: /webcam/snapshot

[webcam camera2]
service: webrtc-go2rtc
stream_url: /webcam2/webrtc
snapshot_url: /webcam2/snapshot
```

### 配置后能否单独访问？

**可以！** go2rtc 的所有功能都保持可用：

- ✅ go2rtc Web 界面：`http://<IP>:1984`
- ✅ WebRTC（通过 Mailsail 或 go2rtc Web）
- ✅ MJPEG：`http://<IP>:1984/api/stream.mjpeg?src=<摄像头名称>`
- ✅ RTSP：`rtsp://<IP>:8554/<摄像头名称>`
- ✅ HLS：`http://<IP>:1984/api/stream.m3u8?src=<摄像头名称>`

Nginx 只是添加了一个代理入口，不影响 go2rtc 原有的任何功能。

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

# ncmdump

NCM to MP3 Conversion Web Service - 网易云音乐 NCM 格式转换为 MP3 的 Web 服务

## 功能

- 在线转换 NCM 文件为 MP3 格式
- Web 界面操作
- 支持批量转换

## 安装

```bash
pip install flask
```

## 运行

```bash
python3 ncmdump_web.py
```

访问 http://localhost:5000

## 服务

可使用 systemd 服务运行：

```bash
sudo cp ncmdump.service /etc/systemd/system/
sudo systemctl enable ncmdump
sudo systemctl start ncmdump
```
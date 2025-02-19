import socket
from src.utils import get_device_id
# 🔹 创建全局 UDP 套接字
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 🔹 OTA 服务地址
OTA_VERSION_URL = 'https://api.tenclass.net/xiaozhi/ota/'

# 🔹 WSS 服务地址
WSS_URL = "wss://api.tenclass.net/xiaozhi/v1/"

# 🔹 设备 MAC 地址
MAC_ADDR = get_device_id()

# 🔹 MQTT 服务器信息
mqtt_info = {}

# 🔹 监听状态
listen_state = None

# 🔹 本地数据
local_sequence = 0

# 🔹 音频传输配置
aes_opus_info = {
    "type": "hello",
    "version": 3,
    "transport": "udp",
    "udp": {
        "server": "",
        "port": 8884,
        "encryption": "",
        "key": "",
        "nonce": ""
    },
    "audio_params": {
        "format": "opus",
        "sample_rate": 16000,
        "channels": 1,
        "frame_duration": 60
    },
    "session_id": None
}

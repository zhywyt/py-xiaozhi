import asyncio
import json
import logging
import time
from typing import Optional, Callable, Dict
import pyaudio
import websockets

from src.audio_player import AudioConfig, AudioPlayer
from src.config import WSS_URL, MAC_ADDR
import src.config
from src.protocols.protocol import ListeningMode
audio = pyaudio.PyAudio()
class WebsocketProtocol():

    def __init__(self):
        self.receive_task = None
        self._running = None
        self.ws = None
        self.session_id: str = ""
        self.audio_params = src.config.aes_opus_info['audio_params']
        self.server_sample_rate: int = 16000
        self.event = asyncio.Event()
        # 回调函数
        self._on_incoming_json: Optional[Callable[[Dict], None]] = None
        self._on_incoming_audio: Optional[Callable[[bytes], None]] = None
        self._on_audio_channel_opened: Optional[Callable[[], None]] = None
        self._on_audio_channel_closed: Optional[Callable[[], None]] = None
        self._on_network_error: Optional[Callable[[str], None]] = None

        self.logger = logging.getLogger("WebsocketProtocol")

        self.audio_config = AudioConfig(
            channels=1,
            sample_rate=16000,
            frame_duration=60
        )
        self.audio_processor = AudioPlayer(self.audio_config,audio)

    async def send_text(self, text: str) -> None:
        """发送文本消息"""
        if self.ws:
            try:
                await self.ws.send(text)
                self.logger.debug(f"Sent text: {text}")
            except Exception as e:
                self.logger.error(f"Failed to send text: {e}")
                if self._on_network_error:
                    self._on_network_error(str(e))

    async def send_start_listening(self, mode: ListeningMode) -> None:
        """发送开始监听消息"""
        message = {
            "session_id": self.session_id,
            "type": "listen",
            "state": "start",
            "mode": mode.value
        }
        await self.send_text(json.dumps(message))

    async def connect(self) -> bool:
        """打开音频通道"""
        try:
            print(WSS_URL)
            """建立WebSocket连接并完成初始化"""
            self.ws = await websockets.connect(WSS_URL, additional_headers={
                "Authorization": f"Bearer test-token",
                "Protocol-Version": "3",
                "Device-Id": "f8:89:d2:84:05:44"
            }, proxy=None)

            # 发送 hello 消息
            hello_message = {
                "type": "hello",
                "transport": "websocket",
                "version": 3,
                "response_mode": "auto",
                "audio_params": self.audio_params
            }
            self.audio_processor.start()
            await self.send_text(json.dumps(hello_message))
            print("[INFO] 发送初始配置")

            time.sleep(0.1)
            await self.ws.send(json.dumps(
                {"session_id": "", "type": "listen", "state": "detect", "mode": "auto", "text": "你是谁？"}))

            # 等待服务器响应
            response = await self.ws.recv()
            print(f"[INFO] 收到服务器回复: {response}")

            # 启动后台接收任务
            self._running = True
            self.receive_task = asyncio.create_task(self._receive_loop())

            return True

        except Exception as e:
            self.logger.error(f"Failed to open channel: {e}")
            if self._on_network_error:
                self._on_network_error(str(e))
            return False

    async def _receive_loop(self):
        """后台持续接收消息的循环"""
        try:
            while True:
                try:
                    message = await self.ws.recv()
                    await self._handle_message(message)
                except websockets.exceptions.ConnectionClosed:
                    print("[INFO] WebSocket连接已关闭")
                    break
                except Exception as e:
                    print(f"[ERROR] 接收消息错误: {e}")
                    continue
        except Exception as e:
            print(f"[ERROR] 接收循环错误: {e}")
        finally:
            print("[INFO] 接收循环结束")

    async def _handle_message(self, message):
        """处理接收到的消息"""
        if isinstance(message, bytes):
            # 检查数据包大小是否合理
            if len(message) < 10:  # 设置一个最小阈值
                print(f"[WARNING] 收到的音频数据包过小: {len(message)} bytes")
                return
            self.audio_processor.process_audio(message)
        else:
            try:
                # 尝试解析JSON消息
                data = json.loads(message)
                if isinstance(data, dict):
                    msg_type = data.get('type', 'unknown')
                    print(f"[INFO] 收到{msg_type}消息: {json.dumps(data, ensure_ascii=False)}")
                    if msg_type == 'tts':
                        msg_state = data.get('state', 'unknown')
                        if msg_state == 'stop':
                            print(f"[INFO] tts结束")
                else:
                    print(f"[INFO] 收到文本: {message}")
            except json.JSONDecodeError:
                print(f"[INFO] 收到文本: {message}")


    async def close(self):
        """关闭连接"""
        if self.ws:
            await self.ws.close()

        # 停止音频处理器
        self.audio_processor.stop()
        self._running = False
# src/audio_player.py

import numpy as np
import opuslib
from dataclasses import dataclass
import struct
import pyaudio
import logging
from typing import Optional, Tuple

from src import config
from src.utils import aes_ctr_encrypt


@dataclass
class AudioConfig:
    """音频配置"""
    channels: int = 1
    sample_rate: int = 24000
    frame_duration: int = 60  # 帧时长(ms)
    aes_key: Optional[str] = None
    aes_nonce: Optional[str] = None

    @property
    def frame_size(self) -> int:
        return int(self.sample_rate * self.frame_duration / 1000)


class AudioSender:
    """音频发送处理器"""

    def __init__(self, config: AudioConfig,audio):
        self.config = config

        # 保存服务器信息
        self.key = config.aes_key
        self.nonce = config.aes_nonce

        # 初始化 Opus 编码器
        self.opus_encoder = opuslib.Encoder(
            fs=16000,
            channels=1,
            application=opuslib.APPLICATION_AUDIO
        )

        # 初始化麦克风
        self.pa = audio
        self.mic = self.pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=960
        )

        self._running = False
        self.sequence = 0

    def capture_and_encode(self) -> bytes:
        """采集并编码音频数据，返回加密后的数据包"""
        try:
            # 读取音频数据
            data = self.mic.read(960, exception_on_overflow=False)

            # Opus编码
            encoded_data = self.opus_encoder.encode(data, 960)
            self.sequence = (self.sequence + 1) & 0xFFFFFFFF

            # 生成新的nonce
            new_nonce = (
                    self.nonce[:4] +  # 固定前缀
                    format(len(encoded_data), '04x') +  # 数据长度
                    self.nonce[8:24] +  # 原始nonce
                    format(self.sequence, '08x')  # 序列号
            )

            # AES加密
            encrypt_encoded_data = aes_ctr_encrypt(
                bytes.fromhex(self.key),
                bytes.fromhex(new_nonce),
                bytes(encoded_data)
            )

            # 拼接nonce和密文
            return bytes.fromhex(new_nonce) + encrypt_encoded_data

        except Exception as e:
            logging.error(f"[ERROR] 音频采集编码错误: {str(e)}")
            raise

    def start(self):
        self._running = True
        logging.info("✅ 音频发送器启动")

    def stop(self):
        self._running = False
        if self.mic:
            try:
                self.mic.stop_stream()
                self.mic.close()
            except:
                pass
        if self.pa:
            try:
                self.pa.terminate()
            except:
                pass
        self.mic = None
        self.pa = None
        self.sequence = 0
        logging.info("🔴 音频发送器停止")

    @property
    def is_running(self):
        return self._running
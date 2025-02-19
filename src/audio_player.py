import numpy as np
import opuslib
from dataclasses import dataclass
import struct
import platform
import pyaudio
from typing import Optional
import logging

@dataclass
class AudioConfig:
    """音频配置"""
    channels: int = 1
    sample_rate: int = 24000
    frame_duration: int = 60  # 帧时长(ms)
    aes_key: Optional[str] = None  # AES密钥
    aes_nonce: Optional[str] = None  # AES nonce

    @property
    def frame_size(self) -> int:
        """计算每帧采样点数"""
        return int(self.sample_rate * self.frame_duration / 1000)


class AudioPlayer:
    def __init__(self, config: AudioConfig, audio):
        self.config = config
        self.frame_size = config.frame_size

        # 初始化 Opus 解码器
        self.opus_decoder = opuslib.Decoder(
            fs=config.sample_rate,
            channels=config.channels
        )

        # 初始化 PyAudio
        self.pa = audio
        self.stream = self.pa.open(
            format=pyaudio.paInt16,
            channels=config.channels,
            rate=config.sample_rate,
            output=True,
            frames_per_buffer=self.frame_size
        )

        self._running = False
        self.debug_counter = 0

        # 保存AES配置
        self.aes_key = bytes.fromhex(config.aes_key) if config.aes_key else None
        self.aes_nonce = bytes.fromhex(config.aes_nonce) if config.aes_nonce else None

        logging.info(f"[INFO] 初始化音频处理器 - "
                     f"采样率: {config.sample_rate}Hz, "
                     f"通道数: {config.channels}, "
                     f"帧大小: {self.frame_size}, "
                     f"加密: {'启用' if self.aes_key else '禁用'}")

    def process_audio(self, audio_data: bytes, encrypted: bool = False):
        """处理接收到的音频数据

        Args:
            audio_data: 音频数据
            encrypted: 是否为加密数据
        """
        try:
            if encrypted and self.aes_key:
                # 解析加密数据
                if len(audio_data) < 16:
                    logging.error(f"[ERROR] 加密数据包太小: {len(audio_data)}")
                    return

                # 分离nonce和加密数据
                received_nonce = audio_data[:16]
                encrypted_audio = audio_data[16:]

                # AES-CTR解密
                from src.utils import aes_ctr_decrypt
                payload = aes_ctr_decrypt(
                    self.aes_key,
                    received_nonce,
                    encrypted_audio
                )
            else:
                # 解析普通二进制协议格式
                if len(audio_data) < 4:
                    logging.error(f"[ERROR] 数据包太小: {len(audio_data)}")
                    return

                # 解析头部 [type(1) + reserved(1) + len(2) + payload]
                type_byte = audio_data[0]
                payload_size = struct.unpack('>H', audio_data[2:4])[0]
                payload = audio_data[4:4 + payload_size]

            try:
                # Opus解码
                pcm_data = self.opus_decoder.decode(
                    payload,
                    frame_size=self.frame_size,
                    decode_fec=False
                )

                # 转换为numpy数组
                pcm_array = np.frombuffer(pcm_data, dtype=np.int16)

                # 调试信息
                if self.debug_counter % 100 == 0:
                    logging.debug(f"[DEBUG] PCM数据: 大小={len(pcm_array)}, "
                                  f"最大值={np.max(np.abs(pcm_array))}, "
                                  f"均值={np.mean(np.abs(pcm_array))}")

                # 播放音频
                if self._running and len(pcm_array) > 0:
                    self.stream.write(pcm_array.tobytes())

            except Exception as e:
                logging.error(f"[ERROR] Opus解码错误: {str(e)}")
                return

            self.debug_counter += 1

        except Exception as e:
            logging.error(f"[ERROR] 音频处理错误: {str(e)}")
            import traceback
            traceback.print_exc()

    def start(self):
        """启动音频处理"""
        self._running = True
        logging.info("[INFO] 音频处理器启动")

    def stop(self):
        """停止音频处理"""
        self._running = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.pa:
            self.pa.terminate()
        logging.info("[INFO] 音频处理器停止")
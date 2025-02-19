from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, Optional, Dict, Any, Union
from dataclasses import dataclass
import json
import logging

class DeviceState(Enum):
    """设备状态枚举"""
    UNKNOWN = "unknown"
    STARTING = "starting"
    IDLE = "idle"
    CONNECTING = "connecting"
    LISTENING = "listening"
    SPEAKING = "speaking"

class ListeningMode(Enum):
    """监听模式枚举
    ALWAYS_ON: 持续监听模式
    AUTO_STOP: 自动停止模式
    MANUAL: 手动控制模式
    """
    ALWAYS_ON = "realtime"
    AUTO_STOP = "auto"
    MANUAL = "manual"


class AbortReason(Enum):
    """中止原因枚举
    NONE: 无特定原因
    WAKE_WORD_DETECTED: 检测到唤醒词
    """
    NONE = "none"
    WAKE_WORD_DETECTED = "wake_word_detected"


@dataclass
class AudioParams:
    """音频参数数据类
    定义了音频流的基本参数
    """
    format: str = "opus"  # 音频编码格式
    sample_rate: int = 16000  # 采样率
    channels: int = 1  # 声道数
    frame_duration: int = 20  # 帧长度(ms)


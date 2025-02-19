import pyaudio
import time
import logging
import src.config
from src.audio_player import AudioConfig, AudioPlayer
from src.audio_sender import AudioSender

# 初始化 PyAudio
audio = pyaudio.PyAudio()


def send_audio():
    """音频发送线程函数"""
    processor = None
    try:
        if src.config.udp_socket is None:
            raise RuntimeError("❌ UDP socket未初始化！")

        audio_config = AudioConfig(
            sample_rate=src.config.aes_opus_info['audio_params']['sample_rate'],
            channels=1,
            frame_duration=src.config.aes_opus_info['audio_params']['frame_duration'],
            aes_key=src.config.aes_opus_info['udp']['key'],
            aes_nonce=src.config.aes_opus_info['udp']['nonce']
        )

        processor = AudioSender(audio_config,audio)
        processor.start()
        logging.info("✅ 音频发送线程启动")

        while src.config.udp_socket and processor.is_running:
            try:
                if src.config.listen_state == "stop":
                    time.sleep(0.1)
                    continue

                # 采集、编码并加密音频数据
                packet_data = processor.capture_and_encode()

                # 发送数据
                if src.config.udp_socket:
                    src.config.udp_socket.sendto(
                        packet_data,
                        (src.config.aes_opus_info['udp']['server'],
                         src.config.aes_opus_info['udp']['port'])
                    )

            except Exception as e:
                logging.error(f"[ERROR] 发送循环错误: {str(e)}")
                time.sleep(0.1)

    except Exception as e:
        logging.error(f"❌ send_audio 错误: {e}")
    finally:
        if processor:
            processor.stop()
        if src.config.udp_socket:
            try:
                src.config.udp_socket.close()
            except:
                pass
            src.config.udp_socket = None
        logging.info("🔴 send_audio 线程退出")


def recv_audio():
    """音频接收和播放线程函数"""
    processor = None
    try:
        # 初始化音频处理器
        audio_config = AudioConfig(
            sample_rate=src.config.aes_opus_info['audio_params']['sample_rate'],
            channels=1,
            frame_duration=src.config.aes_opus_info['audio_params']['frame_duration'],
            aes_key=src.config.aes_opus_info['udp']['key'],
            aes_nonce=src.config.aes_opus_info['udp']['nonce']
        )

        processor = AudioPlayer(audio_config, audio)
        processor.start()
        logging.info("✅ 音频接收线程启动")

        while src.config.udp_socket:
            try:
                data, _ = src.config.udp_socket.recvfrom(4096)
                processor.process_audio(data, encrypted=True)

            except Exception as e:
                logging.error(f"[ERROR] 接收循环错误: {str(e)}")
                time.sleep(0.1)

    except Exception as e:
        logging.error(f"❌ recv_audio 错误: {e}")
    finally:
        if processor:
            processor.stop()
        if src.config.udp_socket:
            try:
                src.config.udp_socket.close()
            except:
                pass
            src.config.udp_socket = None
        logging.info("🔴 recv_audio 线程退出")
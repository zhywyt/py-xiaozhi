import threading
import tkinter as tk
from tkinter import ttk
import src.config
import socket
import time

class GUI:
    def __init__(
        self,
        mqtt_client
    ):
        self.mqtt_client = mqtt_client
        """创建 GUI 界面"""
        root = tk.Tk()
        self.root = root
        self.root.title("小智语音控制")
        self.root.geometry("300x300")  # 增加高度，以便显示更多内容

        # 状态显示
        self.status_frame = ttk.Frame(root)
        self.status_frame.pack(pady=10)

        self.status_label = ttk.Label(self.status_frame, text="状态: 未连接")
        self.status_label.pack(side=tk.LEFT)

        self.emotion_label = tk.Label(root, text="😊", font=("Segoe UI Emoji", 16))
        self.emotion_label.pack(padx=20, pady=20)

        # TTS返回的文本显示
        self.tts_text_label = ttk.Label(root, text="待命", wraplength=250)
        self.tts_text_label.pack(padx=20, pady=10)

        # 音量控制
        self.volume_frame = ttk.Frame(root)
        self.volume_frame.pack(pady=10)

        ttk.Label(self.volume_frame, text="音量:").pack(side=tk.LEFT)
        self.volume_scale = ttk.Scale(
            self.volume_frame,
            from_=0,
            to=100,
            command=lambda v: self.update_volume(int(float(v)))
        )
        self.volume_scale.set(70)
        self.volume_scale.pack(side=tk.LEFT, padx=10)

        # 控制按钮
        self.btn_frame = ttk.Frame(root)
        self.btn_frame.pack(pady=20)

        self.talk_btn = ttk.Button(self.btn_frame, text="按住说话")
        self.talk_btn.bind("<ButtonPress-1>", self.on_button_press)
        self.talk_btn.bind("<ButtonRelease-1>", self.on_button_release)
        self.talk_btn.pack(side=tk.LEFT, padx=10)

        # 状态更新线程
        threading.Thread(target=self.update_status, daemon=True).start()
        threading.Thread(target=self.update_text(), daemon=True).start()
        threading.Thread(target=self.update_emotion(), daemon=True).start()


        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def on_button_press(self, event):
        """按钮按下事件处理
        功能流程：
        1. 检查连接状态，必要时重建连接
        2. 发送hello协议建立会话
        3. 如果正在TTS播放则发送终止指令
        4. 发送listen指令启动语音采集
        """
        # 立即更新按钮状态为"松开以停止"
        self.update_button_status('松开以停止')

        # 检查连接状态和会话
        if not self.mqtt_client.conn_state or not self.mqtt_client.session_id:
            # 清理旧连接
            if src.config.udp_socket:
                src.config.udp_socket.close()
                src.config.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # 发送设备握手协议
            self.mqtt_client.publish(src.config.aes_opus_info)

        # 中断正在播放的语音
        if self.mqtt_client.tts_state in ["start", "entence_start"]:
            self.mqtt_client.publish({
                "type": "abort"
            })

        # 启动语音采集
        session_id = self.mqtt_client.get_session_id()
        if session_id:
            listen_msg = {
                "session_id": session_id,
                "type": "listen",
                "state": "start",
                "mode": "manual"  # 手动模式
            }
            self.mqtt_client.publish(listen_msg)

    def on_button_release(self, event):
        """按钮释放事件处理
        发送停止录音指令
        """
        # 立即更新按钮状态为"按住说话"
        self.update_button_status('按住说话')

        session_id = self.mqtt_client.get_session_id()
        if session_id:
            stop_msg = {
                "session_id": session_id,
                "type": "listen",
                "state": "stop"
            }
            self.mqtt_client.publish(stop_msg)

    def update_status(self):
        """更新状态显示"""
        status = "已连接" if self.mqtt_client.conn_state else "未连接"
        self.status_label.config(text=f"状态: {status} | TTS状态: {self.mqtt_client.tts_state}")
        self.root.after(500, self.update_status)

    def update_button_status(self, touch_state: str):
        self.talk_btn.config(text=touch_state)

    def update_text(self):
        """更新TTS返回的文本内容"""
        # print("self.mqtt_client.tts_text",self.mqtt_client.tts_text)
        self.tts_text_label.config(text=f"{self.mqtt_client.tts_text}")
        self.root.after(500, self.update_text)


    def update_emotion(self):
        self.emotion_label.config(text=f"{self.mqtt_client.emotion}")
        self.root.after(500, self.update_emotion)

    def on_close(self):
        """关闭窗口时退出"""
        self.root.destroy()

    def update_volume(self, volume: int):
        """更新系统音量
        Args:
            volume: 音量值(0-100)
        """
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume_control = cast(interface, POINTER(IAudioEndpointVolume))

            # 将0-100的值转换为-65.25到0的分贝值
            volume_db = -65.25 * (1 - volume/100.0)
            volume_control.SetMasterVolumeLevel(volume_db, None)
        except Exception as e:
            print(f"设置音量失败: {e}")

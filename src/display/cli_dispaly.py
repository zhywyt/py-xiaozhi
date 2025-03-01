import logging
import threading
import time
from src.display.base_display import BaseDisplay

logger = logging.getLogger("CliDisplay")

class CliDisplay(BaseDisplay):
    def __init__(self):
        """初始化CLI显示"""
        self.logger = logging.getLogger("CliDisplay")
        self.running = True
        self.current_volume = 70
        
        # 状态相关
        self.current_status = "未连接"
        self.current_text = "待命"
        self.current_emotion = "😊"
        
        # 回调函数
        self.toggle_chat_callback = None
        self.status_callback = None
        self.text_callback = None
        self.emotion_callback = None
        
        # 按键状态
        self.is_r_pressed = False
        
        # 状态缓存
        self.last_status = None
        self.last_text = None
        self.last_emotion = None
        self.last_volume = None

    def set_callbacks(self,
                     press_callback=None,
                     status_callback=None,
                     text_callback=None,
                     emotion_callback=None):
        """设置回调函数"""
        self.toggle_chat_callback = press_callback
        self.status_callback = status_callback
        self.text_callback = text_callback
        self.emotion_callback = emotion_callback

    def update_button_status(self, text: str):
        """更新按钮状态"""
        print(f"按钮状态: {text}")

    def update_status(self, status: str):
        """更新状态文本"""
        if status != self.current_status:
            self.current_status = status
            self._print_current_status()

    def update_text(self, text: str):
        """更新TTS文本"""
        if text != self.current_text:
            self.current_text = text
            self._print_current_status()

    def update_emotion(self, emotion: str):
        """更新表情"""
        if emotion != self.current_emotion:
            self.current_emotion = emotion
            self._print_current_status()

    def update_volume(self, volume: int):
        """更新系统音量"""
        if volume != self.current_volume:
            self.current_volume = volume
            self._print_current_status()
            # ... cli音量更新待实现 ...

    def start(self):
        """启动CLI显示"""
        self._print_help()
        
        # 启动状态更新线程
        self.start_update_threads()

        # 启动键盘监听线程
        keyboard_thread = threading.Thread(target=self._keyboard_listener)
        keyboard_thread.daemon = True
        keyboard_thread.start()

        # 主循环
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.on_close()

    def on_close(self):
        """关闭CLI显示"""
        self.running = False
        print("\n正在关闭应用...")

    def _print_help(self):
        """打印帮助信息"""
        print("\n=== 小智Ai命令行控制 ===")
        print("可用命令：")
        print("  r     - 开始/停止对话")
        print("  v+    - 增加音量")
        print("  v-    - 减少音量")
        print("  s     - 显示当前状态")
        print("  q     - 退出程序")
        print("  h     - 显示此帮助信息")
        print("=====================\n")

    def _keyboard_listener(self):
        """键盘监听线程"""
        try:
            while self.running:
                cmd = input().lower()
                if cmd == 'q':
                    self.on_close()
                    break
                elif cmd == 'h':
                    self._print_help()
                elif cmd == 'r':
                    if self.toggle_chat_callback:
                        self.toggle_chat_callback()
                elif cmd == 'v+':
                    self.update_volume(min(100, self.current_volume + 10))
                elif cmd == 'v-':
                    self.update_volume(max(0, self.current_volume - 10))
                elif cmd == 's':
                    self._print_current_status()
                else:
                    print("未知命令，输入 'h' 查看帮助")
        except Exception as e:
            logger.error(f"键盘监听错误: {e}")

    def start_update_threads(self):
        """启动更新线程"""
        def update_loop():
            while self.running:
                try:
                    # 更新状态
                    if self.status_callback:
                        status = self.status_callback()
                        if status and status != self.current_status:
                            self.update_status(status)

                    # 更新文本
                    if self.text_callback:
                        text = self.text_callback()
                        if text and text != self.current_text:
                            self.update_text(text)

                    # 更新表情
                    if self.emotion_callback:
                        emotion = self.emotion_callback()
                        if emotion and emotion != self.current_emotion:
                            self.update_emotion(emotion)

                except Exception as e:
                    logger.error(f"状态更新错误: {e}")
                time.sleep(0.1)

        # 启动更新线程
        threading.Thread(target=update_loop, daemon=True).start()

    def _print_current_status(self):
        """打印当前状态"""
        # 检查是否有状态变化
        status_changed = (
            self.current_status != self.last_status or
            self.current_text != self.last_text or
            self.current_emotion != self.last_emotion or
            self.current_volume != self.last_volume
        )
        
        if status_changed:
            print("\n=== 当前状态 ===")
            print(f"状态: {self.current_status}")
            print(f"文本: {self.current_text}")
            print(f"表情: {self.current_emotion}")
            print(f"音量: {self.current_volume}%")
            print("===============\n")
            
            # 更新缓存
            self.last_status = self.current_status
            self.last_text = self.current_text
            self.last_emotion = self.current_emotion
            self.last_volume = self.current_volume
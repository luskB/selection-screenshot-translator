import sys
import time
import threading
import ctypes
import pyperclip
import winreg
from pynput import mouse, keyboard
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QStyle, QMessageBox
from PyQt5.QtCore import QPoint, pyqtSignal as Signal, QObject, QTimer, Qt, QBuffer, QIODevice
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtNetwork import QLocalServer, QLocalSocket

from config_manager import load_config, save_config
from translator_engines import Translator
from ui_components import FloatingIcon, ResultPopup, SettingsWindow

class SignalBridge(QObject):
    request_icon = Signal(int, int)
    request_image_icon = Signal()  # 图片翻译信号
    hide_icon = Signal()  # 隐藏图标信号
    request_direct_translate = Signal(int, int)  # 划词后ALT直接翻译信号

class GlobalListener:
    def __init__(self, bridge, controller):
        self.bridge = bridge
        self.controller = controller
        self.press_pos = None
        self.icon_showing = False
        self.alt_pressed = False       # 实时 ALT 状态
        self.alt_at_press = False      # 鼠标按下瞬间的 ALT 状态
        self.last_drag_pos = None      # 上次普通划词的释放位置
        self.last_drag_time = 0        # 上次普通划词的释放时间

    def on_key_press(self, key):
        if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            self.alt_pressed = True
            # 如果鼠标正在拖拽中途按下ALT，也算ALT+划词
            if self.press_pos is not None:
                self.alt_at_press = True

    def on_key_release(self, key):
        if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            self.alt_pressed = False
            # 检查是否在普通划词后 2 秒内单击了 ALT → 直接翻译
            if self.last_drag_pos and (time.time() - self.last_drag_time) < 2:
                pos = self.last_drag_pos
                self.last_drag_pos = None
                self.last_drag_time = 0
                self.bridge.request_direct_translate.emit(int(pos[0]), int(pos[1]))

    def on_click(self, x, y, button, pressed):
        if button == mouse.Button.left:
            if pressed:
                self.press_pos = (x, y)
                self.alt_at_press = self.alt_pressed  # 记录按下时ALT状态
            else:
                if self.press_pos:
                    dist = ((x - self.press_pos[0])**2 + (y - self.press_pos[1])**2)**0.5
                    if dist > 30 and self.alt_at_press:
                        # ALT+划词 → 显示"译"图标
                        self.last_drag_pos = None
                        self.last_drag_time = 0
                        self.bridge.request_icon.emit(int(x), int(y))
                    elif dist > 30:
                        # 普通划词 → 记录位置和时间，等待2秒内ALT触发
                        self.last_drag_pos = (x, y)
                        self.last_drag_time = time.time()
                    else:
                        # 点击（非划词），清除划词记录
                        self.last_drag_pos = None
                        self.last_drag_time = 0
                        if self.icon_showing:
                            if not self._is_click_on_icon(x, y):
                                self.bridge.hide_icon.emit()
                self.press_pos = None

    def _is_click_on_icon(self, x, y):
        """检查点击位置是否在图标区域内"""
        if not self.controller.icon.isVisible():
            return False
        icon_rect = self.controller.icon.geometry()
        return icon_rect.contains(x, y)

    def start(self):
        self.listener = mouse.Listener(on_click=self.on_click)
        self.listener.daemon = True
        self.listener.start()
        
        self.kb_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release)
        self.kb_listener.daemon = True
        self.kb_listener.start()

class AppController(QObject):
    translation_finished = Signal(str, QPoint)
    retranslation_finished = Signal(str)  # 重翻完成信号

    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.translator = Translator(self.config)
        
        self.icon = FloatingIcon(self.config.get('custom_icon_path', ''))
        self.popup = ResultPopup()
        self.settings = SettingsWindow(self.config)
        
        self.settings.config_saved.connect(self.update_config)
        self.translation_finished.connect(self.show_result)
        
        # 连接重翻信号
        self.popup.retranslate_requested.connect(self.do_retranslation)
        self.retranslation_finished.connect(self.popup.update_result)
        
        self.bridge = SignalBridge()
        self.bridge.request_icon.connect(self.on_request_icon)
        self.bridge.request_image_icon.connect(self.on_image_detected)
        self.bridge.hide_icon.connect(self.hide_icon)  # 连接隐藏图标信号
        self.bridge.request_direct_translate.connect(self.on_request_direct_translate)  # 直接翻译
        
        self.listener = GlobalListener(self.bridge, self)
        self.listener.start()
        
        self.icon.clicked.connect(self.do_translation)
        self.current_text = ""
        self.current_image = None  # 保存当前图片
        self.last_pos = QPoint(0,0)
        self.icon_hide_timer = None  # 图标自动隐藏定时器
        
        # 启动剪贴板监控
        self.clipboard_timer = QTimer()
        self.clipboard_timer.timeout.connect(self.check_clipboard_image)
        self.clipboard_timer.start(500)  # 每500ms检查一次
        self.last_clipboard_seq = 0  # 剪贴板序列号（Windows API）

    def update_config(self, new_config):
        self.config.update(new_config)
        save_config(self.config)
        self.translator = Translator(self.config)
        self.icon.update_icon(self.config.get('custom_icon_path', ''))
        self.handle_auto_start(self.config.get('auto_start', False))

    def handle_auto_start(self, enable):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "OpenCodeTranslate"
        app_path = f'"{sys.argv[0]}"'
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            if enable:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
            else:
                try: winreg.DeleteValue(key, app_name)
                except FileNotFoundError: pass
            winreg.CloseKey(key)
        except Exception as e:
            pass

    def on_request_icon(self, x, y):
        self.last_pos = QPoint(x, y)
        kb = keyboard.Controller()
        kb.press(keyboard.Key.ctrl)
        kb.press('c')
        time.sleep(0.1)
        kb.release('c')
        kb.release(keyboard.Key.ctrl)
        QTimer.singleShot(250, self.get_clipboard_and_show)

    def get_clipboard_and_show(self):
        try:
            text = pyperclip.paste().strip()
            if text:
                self.current_text = text
                self.current_image = None
                self.show_icon_with_timer()
        except: pass

    def on_request_direct_translate(self, x, y):
        """普通划词后2秒内单击ALT → 复制选区并直接翻译，跳过'译'图标"""
        self.last_pos = QPoint(x, y)
        kb = keyboard.Controller()
        kb.press(keyboard.Key.ctrl)
        kb.press('c')
        time.sleep(0.1)
        kb.release('c')
        kb.release(keyboard.Key.ctrl)
        QTimer.singleShot(250, self.get_clipboard_and_translate)

    def get_clipboard_and_translate(self):
        """获取剪贴板文本后直接翻译，不显示'译'图标"""
        try:
            text = pyperclip.paste().strip()
            if text:
                self.current_text = text
                self.current_image = None
                self.do_translation()
        except: pass

    def show_icon_with_timer(self):
        """显示图标并启动5秒自动隐藏定时器"""
        self.icon.show_at(self.last_pos)
        self.listener.icon_showing = True
        
        # 取消之前的定时器
        if self.icon_hide_timer:
            self.icon_hide_timer.stop()
        
        # 启动新的5秒定时器
        self.icon_hide_timer = QTimer()
        self.icon_hide_timer.setSingleShot(True)
        self.icon_hide_timer.timeout.connect(self.hide_icon)
        self.icon_hide_timer.start(5000)
    
    def hide_icon(self):
        """隐藏图标"""
        self.icon.hide()
        self.listener.icon_showing = False
        if self.icon_hide_timer:
            self.icon_hide_timer.stop()
            self.icon_hide_timer = None

    def check_clipboard_image(self):
        """检查剪贴板是否有新图片（使用 Windows API，零开销检测）"""
        try:
            # 1. 先用 GetClipboardSequenceNumber 检查剪贴板是否有变化
            seq = ctypes.windll.user32.GetClipboardSequenceNumber()
            if seq == self.last_clipboard_seq:
                return  # 剪贴板未变化，直接返回，不做任何IO
            self.last_clipboard_seq = seq
            
            # 2. 剪贴板变化了，用 IsClipboardFormatAvailable 检查是否含图片
            CF_BITMAP = 2
            if not ctypes.windll.user32.IsClipboardFormatAvailable(CF_BITMAP):
                return  # 不是图片，直接返回
            
            # 3. 确认是新图片，才读取一次 pixmap
            clipboard = QApplication.clipboard()
            pixmap = clipboard.pixmap()
            if not pixmap.isNull():
                self.current_image = pixmap
                self.current_text = ""
                self.bridge.request_image_icon.emit()
        except:
            pass
    
    def on_image_detected(self):
        """检测到剪贴板有新图片时，在屏幕左侧中间显示图标"""
        screen = QApplication.primaryScreen().geometry()
        # 左侧中间位置（距离左边50像素，垂直居中）
        x = 50
        y = screen.height() // 2 - 25  # 减去图标高度的一半
        self.last_pos = QPoint(x, y)
        self.show_icon_with_timer()

    def do_translation(self):
        self.hide_icon()  # 使用统一的隐藏方法
        self.popup.display("正在请求接口...", self.last_pos)
        
        # 判断是文本翻译还是图片翻译
        if self.current_image and not self.current_image.isNull():
            # 图片翻译
            engine = self.config.get("image_engine", "tencent")
            t = threading.Thread(target=self._async_run_image, args=(self.current_image, self.last_pos, engine))
            t.daemon = True
            t.start()
        else:
            # 文本翻译
            engine = self.config.get("engine", "google")
            t = threading.Thread(target=self._async_run, args=(self.current_text, self.last_pos, engine))
            t.daemon = True
            t.start()

    def _async_run_image(self, pixmap, pos, engine):
        """异步执行图片翻译"""
        target_lang = self.popup.get_target_lang()
        
        # 将 QPixmap 转换为字节流
        buffer = QBuffer()
        buffer.open(QIODevice.WriteOnly)
        pixmap.save(buffer, "PNG")
        image_bytes = buffer.data().data()
        buffer.close()
        
        result = self.translator.translate_image(image_bytes, target_lang, engine=engine)
        self.translation_finished.emit(result, pos)

    def _async_run(self, text, pos, engine):
        target_lang = self.popup.get_target_lang()
        result = self.translator.translate(text, target_lang, engine=engine)
        self.translation_finished.emit(result, pos)

    def show_result(self, text, pos):
        # 判断是文本翻译还是图片翻译
        if self.current_image and not self.current_image.isNull():
            engine = self.config.get("image_engine", "tencent")
            self.popup.display_with_source(text, pos, "[图片翻译]", engine=engine, is_image=True)
        else:
            engine = self.config.get("engine", "google")
            self.popup.display_with_source(text, pos, self.current_text, engine=engine, is_image=False)

    def do_retranslation(self, engine, target_lang):
        """弹窗中切换引擎/语言时触发的重翻"""
        # 使用 popup.is_image 标记来判断当前是文本翻译还是图片翻译
        if self.popup.is_image and self.current_image and not self.current_image.isNull():
            # 图片重翻
            t = threading.Thread(target=self._async_retranslate_image, args=(self.current_image, engine, target_lang))
            t.daemon = True
            t.start()
        else:
            # 文本重翻
            source = self.popup.source_text
            if not source or source == "[图片翻译]":
                return
            t = threading.Thread(target=self._async_retranslate, args=(source, engine, target_lang))
            t.daemon = True
            t.start()

    def _async_retranslate(self, text, engine, target_lang):
        result = self.translator.translate(text, target_lang, engine=engine)
        self.retranslation_finished.emit(result)
    
    def _async_retranslate_image(self, pixmap, engine, target_lang):
        """异步执行图片重翻"""
        # 将 QPixmap 转换为字节流
        buffer = QBuffer()
        buffer.open(QIODevice.WriteOnly)
        pixmap.save(buffer, "PNG")
        image_bytes = buffer.data().data()
        buffer.close()
        
        result = self.translator.translate_image(image_bytes, target_lang, engine=engine)
        self.retranslation_finished.emit(result)

if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # 单实例检测
    server_name = "OpenCodeTranslate_SingleInstance"
    socket = QLocalSocket()
    socket.connectToServer(server_name)
    
    if socket.waitForConnected(500):
        # 已有实例在运行
        QMessageBox.warning(None, "提示", "划词翻译程序已经在运行中！")
        sys.exit(0)
    
    # 创建本地服务器，防止多实例
    local_server = QLocalServer()
    local_server.removeServer(server_name)
    local_server.listen(server_name)
    
    controller = AppController()
    
    # 获取资源文件路径（支持 PyInstaller 打包）
    import os
    def resource_path(relative_path):
        try:
            # PyInstaller 创建临时文件夹，路径存储在 _MEIPASS 中
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        return os.path.join(base_path, relative_path)
    
    # 使用程序图标
    icon_path = resource_path("icon.ico")
    if os.path.exists(icon_path):
        tray_icon = QIcon(icon_path)
        app.setWindowIcon(tray_icon)
    else:
        # 如果找不到 icon.ico，尝试使用 exe 自身的图标
        exe_path = sys.argv[0]
        if exe_path.endswith('.exe'):
            tray_icon = QIcon(exe_path)
            app.setWindowIcon(tray_icon)
        else:
            tray_icon = QIcon()
    
    tray = QSystemTrayIcon(tray_icon)
    menu = QMenu()
    menu.addAction("设置 (Settings)", controller.settings.show)
    menu.addSeparator()
    menu.addAction("退出 (Exit)", app.quit)
    tray.setContextMenu(menu)
    tray.show()
    
    sys.exit(app.exec_())

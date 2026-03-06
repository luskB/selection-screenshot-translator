from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel,
                             QTextEdit, QLineEdit, QComboBox, QFormLayout,
                             QTabWidget, QApplication, QHBoxLayout, QCheckBox,
                             QFileDialog, QGraphicsDropShadowEffect, QGroupBox,
                             QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, QPoint, pyqtSignal as Signal, QTimer, QEvent
from PyQt5.QtGui import QIcon, QCursor, QPixmap, QColor, QFont

# ── 引擎名称映射 ──
ENGINE_NAMES = {
    "google":    "Google",
    "deepl":     "DeepL",
    "microsoft": "Microsoft",
    "tencent":   "腾讯翻译",
    "volcano":   "火山翻译",
    "ai":        "AI 大模型",
}
ENGINE_KEYS = list(ENGINE_NAMES.keys())

# ── DPI 自适应缩放 ──
_dpi_scale_cache = None

def _get_dpi_scale():
    """获取屏幕 DPI 缩放比例（基准 96 DPI）"""
    global _dpi_scale_cache
    if _dpi_scale_cache is not None:
        return _dpi_scale_cache
    try:
        screen = QApplication.primaryScreen()
        if screen:
            logical_dpi = screen.logicalDotsPerInch()
            _dpi_scale_cache = max(1.0, logical_dpi / 96.0)
            return _dpi_scale_cache
    except:
        pass
    _dpi_scale_cache = 1.0
    return 1.0

def sp(base_px):
    """根据屏幕 DPI 缩放像素值，确保不同分辨率下字体大小一致"""
    return max(1, round(base_px * _get_dpi_scale()))

# ── 通用样式片段 ──
def _combo_style_header():
    return """
        QComboBox {
            border: none;
            background: rgba(255,255,255,0.2);
            color: white;
            padding: 4px 10px;
            border-radius: 8px;
            font-size: %dpx;
        }
        QComboBox:hover { background: rgba(255,255,255,0.3); }
        QComboBox::drop-down { border: none; }
        QComboBox QAbstractItemView {
            background: white; color: #333;
            selection-background-color: #667eea;
            selection-color: white;
        }
    """ % sp(12)

def _btn_style(dark, accent=False):
    if accent:
        bg = "#5a5a7a" if dark else "#667eea"
        bgh = "#6a6a8a" if dark else "#5568d3"
        fg = "#e0e0e0" if dark else "white"
    else:
        bg = "#3d3d3d" if dark else "#e8eaf0"
        bgh = "#4d4d4d" if dark else "#d0d3dc"
        fg = "#e0e0e0" if dark else "#333"
    return f"""
        QPushButton {{
            background: {bg}; color: {fg};
            border: none; border-radius: 8px;
            padding: 5px 14px; font-size: {sp(13)}px;
        }}
        QPushButton:hover {{ background: {bgh}; }}
    """

# ================================================================
#  悬浮"译"图标
# ================================================================
class FloatingIcon(QWidget):
    clicked = Signal()

    def __init__(self, icon_path=""):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(45, 45)
        self.button = QPushButton(self)
        self.button.setFixedSize(40, 40)
        self.update_icon(icon_path)
        self.button.clicked.connect(self.clicked.emit)

    def update_icon(self, icon_path):
        if icon_path and hasattr(self, 'button'):
            self.button.setText("")
            self.button.setIcon(QIcon(icon_path))
            self.button.setIconSize(self.button.size())
            self.button.setStyleSheet("QPushButton{border:none;background:transparent;}")
        else:
            self.button.setText("译")
            self.button.setStyleSheet("""
                QPushButton{background-color:#0078D4;color:white;border-radius:20px;
                    font-weight:bold;font-size:%dpx;border:2px solid #fff;}
                QPushButton:hover{background-color:#2b88d8;}""" % sp(16))

    def show_at(self, pos):
        self.move(pos + QPoint(15, 15))
        self.show()

# ================================================================
#  翻译结果弹窗
# ================================================================
class ResultPopup(QWidget):
    # 引擎/语言切换时发出信号，由 main.py 的 controller 处理
    retranslate_requested = Signal(str, str)  # (engine, target_lang)
    show_history_requested = Signal()         # 请求显示历史记录

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(420, 340)
        self.resize(500, 420)

        self.dark_mode = False
        self.target_lang = "zh-CN"
        self.current_engine = "google"
        self.source_text = ""   # 保存原文，用于切换引擎/语言时重翻
        self.is_image = False   # 标记是否为图片翻译
        self.pinned = False     # 钉住状态：True时点击外部不隐藏

        self.dragging = False
        self.resizing = False
        self.drag_position = QPoint()
        self.resize_edge = None
        self.start_geometry = None
        self._block_engine_signal = False

        self.main_container = QWidget(self)
        self.main_container.setObjectName("mc")
        self._build()

    # ── 构建界面 ──
    def _build(self):
        dk = self.dark_mode
        if self.main_container.layout():
            QWidget().setLayout(self.main_container.layout())

        self.main_container.setStyleSheet(
            f"#mc{{background:{'#1e1e1e' if dk else '#ffffff'};border-radius:16px;}}")

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 120 if dk else 80))
        shadow.setOffset(0, 4)
        self.main_container.setGraphicsEffect(shadow)

        root = QVBoxLayout(self.main_container)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── 标题栏 ──
        self.title_bar = QWidget()
        grad = "stop:0 #2d3561,stop:1 #3d2d52" if dk else "stop:0 #667eea,stop:1 #764ba2"
        self.title_bar.setStyleSheet(f"""QWidget{{
            background:qlineargradient(x1:0,y1:0,x2:1,y2:0,{grad});
            border-top-left-radius:16px;border-top-right-radius:16px;}}""")
        self.title_bar.setFixedHeight(50)

        hdr = QHBoxLayout(self.title_bar)
        hdr.setContentsMargins(18, 0, 8, 0)

        title = QLabel("✦ 智能翻译")
        title.setStyleSheet(f"font-weight:600;color:#fff;font-size:{sp(15)}px;border:none;background:transparent;")

        # 引擎切换下拉框
        self.engine_combo = QComboBox()
        self.engine_combo.addItems([ENGINE_NAMES[k] for k in ENGINE_KEYS])
        idx = ENGINE_KEYS.index(self.current_engine) if self.current_engine in ENGINE_KEYS else 0
        self.engine_combo.setCurrentIndex(idx)
        self.engine_combo.setStyleSheet(_combo_style_header())
        self.engine_combo.setFixedWidth(100)
        self.engine_combo.currentIndexChanged.connect(self._on_engine_changed)

        # 语言切换下拉框
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["中文", "English"])
        self.lang_combo.setCurrentIndex(0 if self.target_lang == "zh-CN" else 1)
        self.lang_combo.setStyleSheet(_combo_style_header())
        self.lang_combo.currentIndexChanged.connect(self._on_lang_changed)

        theme_btn = QPushButton("🌙" if not dk else "☀️")
        theme_btn.setFixedSize(32, 32)
        theme_btn.setStyleSheet(f"QPushButton{{border:none;font-size:{sp(18)}px;color:rgba(255,255,255,.9);"
            "background:transparent;border-radius:16px;}"
            "QPushButton:hover{background:rgba(255,255,255,.2);}")
        theme_btn.clicked.connect(self.toggle_theme)

        # 钉住按钮
        self.pin_btn = QPushButton("📌" if self.pinned else "📍")
        self.pin_btn.setFixedSize(32, 32)
        self.pin_btn.setToolTip("钉住窗口" if not self.pinned else "取消钉住")
        self.pin_btn.setStyleSheet(f"QPushButton{{border:none;font-size:{sp(16)}px;color:rgba(255,255,255,.9);"
            "background:transparent;border-radius:16px;}"
            "QPushButton:hover{background:rgba(255,255,255,.2);}")
        self.pin_btn.clicked.connect(self.toggle_pin)

        close_btn = QPushButton("×")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet(f"QPushButton{{border:none;font-size:{sp(24)}px;color:rgba(255,255,255,.8);"
            "background:transparent;border-radius:16px;}"
            "QPushButton:hover{color:#fff;background:rgba(255,255,255,.2);}")
        close_btn.clicked.connect(self.hide)

        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(self.engine_combo)
        hdr.addWidget(self.lang_combo)
        hdr.addWidget(self.pin_btn)
        hdr.addWidget(theme_btn)
        hdr.addWidget(close_btn)
        root.addWidget(self.title_bar)

        # ── 内容区域 ──
        body = QWidget()
        body.setStyleSheet("background:transparent;border:none;")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(15, 12, 15, 12)

        self.content = QTextEdit()
        self.content.setReadOnly(True)
        bg2 = "#2d2d2d" if dk else "#f8f9fa"
        fg2 = "#e0e0e0" if dk else "#2c3e50"
        sb_h  = "#606060" if dk else "#c0c0c0"
        sb_hh = "#707070" if dk else "#a0a0a0"
        self.content.setStyleSheet(f"""
            QTextEdit{{border:none;background:{bg2};font-size:{sp(14)}px;
                padding:15px;padding-right:5px;color:{fg2};border-radius:12px;}}
            QScrollBar:vertical{{border:none;background:transparent;width:8px;margin:2px 2px 2px 0;}}
            QScrollBar::handle:vertical{{background:{sb_h};border-radius:4px;min-height:20px;}}
            QScrollBar::handle:vertical:hover{{background:{sb_hh};}}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}""")
        bl.addWidget(self.content)

        # ── 底部按钮栏 ──
        bar = QWidget()
        bar.setStyleSheet("background:transparent;border:none;")
        barL = QHBoxLayout(bar)
        barL.setContentsMargins(0, 6, 0, 0)

        retranslate_btn = QPushButton("🔄 重翻")
        retranslate_btn.setFixedHeight(32)
        retranslate_btn.setStyleSheet(_btn_style(dk))
        retranslate_btn.setToolTip("使用当前引擎和语言重新翻译")
        retranslate_btn.clicked.connect(self._on_retranslate_clicked)

        history_btn = QPushButton("📜 历史")
        history_btn.setFixedHeight(32)
        history_btn.setStyleSheet(_btn_style(dk))
        history_btn.setToolTip("查看翻译历史记录")
        history_btn.clicked.connect(self.show_history_requested.emit)

        copy_btn = QPushButton("📋 复制")
        copy_btn.setFixedHeight(32)
        copy_btn.setStyleSheet(_btn_style(dk, accent=True))
        copy_btn.clicked.connect(self.copy_to_clipboard)

        barL.addWidget(retranslate_btn)
        barL.addWidget(history_btn)
        barL.addStretch()
        barL.addWidget(copy_btn)
        bl.addWidget(bar)

        root.addWidget(body)
        self.main_container.setGeometry(0, 0, self.width(), self.height())

    # ── 回调 ──
    def _on_engine_changed(self, idx):
        if self._block_engine_signal:
            return
        self.current_engine = ENGINE_KEYS[idx]
        if self.source_text:
            self.content.setText("正在重新翻译...")
            self.retranslate_requested.emit(self.current_engine, self.target_lang)

    def _on_lang_changed(self, idx):
        self.target_lang = "zh-CN" if idx == 0 else "en"
        if self.source_text:
            self.content.setText("正在重新翻译...")
            self.retranslate_requested.emit(self.current_engine, self.target_lang)

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        txt = self.content.toPlainText()
        self._build()
        self.content.setText(txt)

    def toggle_pin(self):
        self.pinned = not self.pinned
        self.pin_btn.setText("📌" if self.pinned else "📍")
        self.pin_btn.setToolTip("取消钉住" if self.pinned else "钉住窗口")

    def _on_retranslate_clicked(self):
        """点击重翻按钮时，用当前引擎和语言重新翻译"""
        if self.source_text:
            self.content.setText("正在重新翻译...")
            self.retranslate_requested.emit(self.current_engine, self.target_lang)

    def copy_to_clipboard(self):
        QApplication.clipboard().setText(self.content.toPlainText())

    def get_target_lang(self):
        return self.target_lang

    def get_current_engine(self):
        return self.current_engine

    # ── 显示翻译结果 ──
    def display(self, text, pos):
        self.content.setText(text)
        self.move(pos + QPoint(20, 20))
        self.show()
        self.activateWindow()

    def display_with_source(self, text, pos, source_text, engine=None, is_image=False):
        """首次翻译时调用，保存原文"""
        self.source_text = source_text if source_text else "[图片翻译]"
        self.is_image = is_image
        if engine:
            self._block_engine_signal = True
            idx = ENGINE_KEYS.index(engine) if engine in ENGINE_KEYS else 0
            self.engine_combo.setCurrentIndex(idx)
            self.current_engine = engine
            self._block_engine_signal = False
        self.content.setText(text)
        self.move(pos + QPoint(20, 20))
        self.show()
        self.activateWindow()

    def update_result(self, text):
        """重翻完成后更新内容"""
        self.content.setText(text)

    # ── 窗口拖动 / 缩放 ──
    def resizeEvent(self, event):
        self.main_container.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            edge = self._edge(event.pos())
            if edge:
                self.resizing = True
                self.resize_edge = edge
                self.drag_position = event.globalPos()
                self.start_geometry = self.geometry()
            elif self.title_bar.geometry().contains(event.pos()):
                self.dragging = True
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.resizing and self.resize_edge and self.start_geometry:
            d = event.globalPos() - self.drag_position
            x, y = self.start_geometry.x(), self.start_geometry.y()
            w, h = self.start_geometry.width(), self.start_geometry.height()
            if 'left'   in self.resize_edge: x += d.x(); w -= d.x()
            if 'right'  in self.resize_edge: w += d.x()
            if 'top'    in self.resize_edge: y += d.y(); h -= d.y()
            if 'bottom' in self.resize_edge: h += d.y()
            if w >= self.minimumWidth() and h >= self.minimumHeight():
                self.setGeometry(x, y, w, h)
        elif self.dragging:
            self.move(event.globalPos() - self.drag_position)
        else:
            e = self._edge(event.pos())
            if e:
                cur = {frozenset({'top'}): Qt.SizeVerCursor,
                       frozenset({'bottom'}): Qt.SizeVerCursor,
                       frozenset({'left'}): Qt.SizeHorCursor,
                       frozenset({'right'}): Qt.SizeHorCursor,
                       frozenset({'top','left'}): Qt.SizeFDiagCursor,
                       frozenset({'bottom','right'}): Qt.SizeFDiagCursor,
                       frozenset({'top','right'}): Qt.SizeBDiagCursor,
                       frozenset({'bottom','left'}): Qt.SizeBDiagCursor}
                parts = frozenset(e.split('-'))
                self.setCursor(cur.get(parts, Qt.ArrowCursor))
            else:
                self.setCursor(Qt.ArrowCursor)
        event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = self.resizing = False
        self.resize_edge = self.start_geometry = None
        event.accept()

    def _edge(self, pos):
        m, r = 8, self.rect()
        l = pos.x() <= m; ri = pos.x() >= r.width() - m
        t = pos.y() <= m; b  = pos.y() >= r.height() - m
        if t and l: return 'top-left'
        if t and ri: return 'top-right'
        if b and l: return 'bottom-left'
        if b and ri: return 'bottom-right'
        if t: return 'top'
        if b: return 'bottom'
        if l: return 'left'
        if ri: return 'right'
        return None

    def changeEvent(self, event):
        if event.type() == QEvent.ActivationChange and not self.isActiveWindow():
            if not self.pinned:
                self.hide()

# ================================================================
#  设置窗口（美化版 + 多引擎 tab）
# ================================================================

def _settings_style():
    fs = sp(13)
    return f"""
    QWidget {{ font-size: {fs}px; }}
    QTabWidget::pane {{ border: 1px solid #ddd; border-radius: 8px; background: #fff; }}
    QTabBar::tab {{ padding: 8px 18px; margin-right: 2px; border-top-left-radius: 6px;
        border-top-right-radius: 6px; background: #eee; }}
    QTabBar::tab:selected {{ background: #fff; border-bottom: 2px solid #667eea; font-weight: bold; }}
    QLineEdit, QComboBox {{ padding: 6px 10px; border: 1px solid #ccc; border-radius: 6px; }}
    QLineEdit:focus, QComboBox:focus {{ border-color: #667eea; }}
    QTextEdit {{ border: 1px solid #ccc; border-radius: 6px; }}
    QTextEdit:focus {{ border-color: #667eea; }}
    QGroupBox {{ font-weight: bold; border: 1px solid #ddd; border-radius: 8px;
        margin-top: 12px; padding-top: 18px; }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 14px; padding: 0 6px; }}
    QCheckBox {{ spacing: 8px; }}
"""

def _save_btn_style():
    return """QPushButton{height:42px;background:#667eea;color:white;font-size:%dpx;
        font-weight:bold;border:none;border-radius:8px;}
        QPushButton:hover{background:#5568d3;}""" % sp(15)

def _proxy_combo():
    c = QComboBox()
    c.addItems(["auto", "manual", "direct"])
    return c

class SettingsWindow(QWidget):
    config_saved = Signal(dict)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowTitle("划词翻译设置")
        self.resize(600, 620)
        self.setStyleSheet(_settings_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        tabs = QTabWidget()

        tabs.addTab(self._tab_general(config), "⚙ 通用")
        tabs.addTab(self._tab_google(config),  "Google")
        tabs.addTab(self._tab_deepl(config),   "DeepL")
        tabs.addTab(self._tab_microsoft(config), "Microsoft")
        tabs.addTab(self._tab_tencent(config), "腾讯")
        tabs.addTab(self._tab_volcano(config), "火山")
        tabs.addTab(self._tab_ai(config),      "AI 大模型")

        layout.addWidget(tabs)

        save_btn = QPushButton("保存配置")
        save_btn.setStyleSheet(_save_btn_style())
        save_btn.clicked.connect(self.save)
        layout.addWidget(save_btn)

    # ── 通用 ──
    def _tab_general(self, c):
        w = QWidget()
        f = QFormLayout(w); f.setSpacing(12)

        self.auto_start = QCheckBox("随开机自动启动")
        self.auto_start.setChecked(c.get('auto_start', False))

        self.engine_combo = QComboBox()
        self.engine_combo.addItems(ENGINE_KEYS)
        self.engine_combo.setCurrentText(c.get('engine', 'google'))

        # 图片翻译引擎选择
        self.image_engine_combo = QComboBox()
        self.image_engine_combo.addItems(["tencent", "volcano", "ai"])
        self.image_engine_combo.setCurrentText(c.get('image_engine', 'tencent'))

        self.proxy_url = QLineEdit(c.get('proxy_url', 'http://127.0.0.1:7897'))
        self.proxy_url.setPlaceholderText("http://127.0.0.1:7897")

        # 历史记录数量设置
        self.history_max_combo = QComboBox()
        self.history_max_combo.addItems(["5", "10", "20", "30", "50"])
        current_max = str(c.get('history_max_count', 10))
        idx = self.history_max_combo.findText(current_max)
        self.history_max_combo.setCurrentIndex(idx if idx >= 0 else 1)

        icon_row = QHBoxLayout()
        self.icon_path_display = QLineEdit(c.get('custom_icon_path', ''))
        self.icon_path_display.setPlaceholderText("使用默认图标")
        btn_browse = QPushButton("浏览...")
        btn_browse.clicked.connect(self.browse_icon)
        icon_row.addWidget(self.icon_path_display)
        icon_row.addWidget(btn_browse)

        f.addRow(self.auto_start)
        f.addRow("默认翻译引擎:", self.engine_combo)
        f.addRow("图片翻译引擎:", self.image_engine_combo)
        f.addRow("代理服务器地址:", self.proxy_url)
        f.addRow("历史记录保留数量:", self.history_max_combo)
        f.addRow("自定义悬浮图标:", icon_row)
        tip = QLabel("<font color='gray'>提示：代理地址用于 manual 模式，确保端口与 Clash 等代理工具一致。<br>"
                     "各引擎的代理模式请在各自的 Tab 中设置。<br>"
                     "图片翻译仅支持腾讯/火山/AI 引擎。</font>")
        tip.setWordWrap(True)
        f.addRow(tip)
        return w

    def _tab_google(self, c):
        w = QWidget(); f = QFormLayout(w); f.setSpacing(12)
        self.g_proxy_mode = _proxy_combo()
        self.g_proxy_mode.setCurrentText(c.get('google_proxy_mode', 'auto'))
        f.addRow("代理模式:", self.g_proxy_mode)
        f.addRow(QLabel("<font color='gray'>Google 翻译免费，无需 API Key。<br>"
                        "需要代理才能访问的用户请选择 auto 或 manual。</font>"))
        return w

    def _tab_deepl(self, c):
        w = QWidget(); f = QFormLayout(w); f.setSpacing(12)
        self.deepl_key = QLineEdit(c.get('deepl_api_key', ''))
        self.deepl_key.setPlaceholderText("输入 DeepL API Key")
        self.deepl_proxy = _proxy_combo()
        self.deepl_proxy.setCurrentText(c.get('deepl_proxy_mode', 'auto'))
        f.addRow("API Key:", self.deepl_key)
        f.addRow("代理模式:", self.deepl_proxy)
        f.addRow(QLabel("<font color='gray'>获取地址：https://www.deepl.com/pro-api<br>"
                        "注册后在 Account 页面获取 Authentication Key。免费版每月 50 万字符。</font>"))
        return w

    def _tab_microsoft(self, c):
        w = QWidget(); f = QFormLayout(w); f.setSpacing(12)
        self.ms_key = QLineEdit(c.get('microsoft_api_key', ''))
        self.ms_key.setPlaceholderText("输入 Microsoft Translator API Key")
        self.ms_region = QLineEdit(c.get('microsoft_region', 'eastasia'))
        self.ms_region.setPlaceholderText("如 eastasia, westus2 等")
        self.ms_proxy = _proxy_combo()
        self.ms_proxy.setCurrentText(c.get('microsoft_proxy_mode', 'direct'))
        f.addRow("API Key:", self.ms_key)
        f.addRow("Region:", self.ms_region)
        f.addRow("代理模式:", self.ms_proxy)
        f.addRow(QLabel("<font color='gray'>Azure 门户创建 Translator 资源：<br>"
                        "portal.azure.com -> 创建资源 -> Translator<br>"
                        "免费层 F0 每月 200 万字符。</font>"))
        return w

    def _tab_tencent(self, c):
        w = QWidget(); f = QFormLayout(w); f.setSpacing(12)
        self.tx_id = QLineEdit(c.get('tencent_secret_id', ''))
        self.tx_id.setPlaceholderText("输入 SecretId")
        self.tx_key = QLineEdit(c.get('tencent_secret_key', ''))
        self.tx_key.setPlaceholderText("输入 SecretKey")
        self.tx_region = QLineEdit(c.get('tencent_region', 'ap-beijing'))
        self.tx_region.setPlaceholderText("如 ap-beijing, ap-guangzhou 等")
        self.tx_proxy = _proxy_combo()
        self.tx_proxy.setCurrentText(c.get('tencent_proxy_mode', 'direct'))
        f.addRow("SecretId:", self.tx_id)
        f.addRow("SecretKey:", self.tx_key)
        f.addRow("Region:", self.tx_region)
        f.addRow("代理模式:", self.tx_proxy)
        f.addRow(QLabel("<font color='gray'>腾讯云控制台获取密钥：<br>"
                        "console.cloud.tencent.com -> 访问管理 -> API密钥管理<br>"
                        "需开通机器翻译(TMT)，每月免费 500 万字符。</font>"))
        return w

    def _tab_volcano(self, c):
        w = QWidget(); f = QFormLayout(w); f.setSpacing(12)
        self.vol_ak = QLineEdit(c.get('volcano_access_key', ''))
        self.vol_ak.setPlaceholderText("输入 AccessKey")
        self.vol_sk = QLineEdit(c.get('volcano_secret_key', ''))
        self.vol_sk.setPlaceholderText("输入 SecretKey")
        self.vol_region = QLineEdit(c.get('volcano_region', 'cn-north-1'))
        self.vol_region.setPlaceholderText("如 cn-north-1, cn-beijing 等")
        self.vol_proxy = _proxy_combo()
        self.vol_proxy.setCurrentText(c.get('volcano_proxy_mode', 'direct'))
        f.addRow("AccessKey:", self.vol_ak)
        f.addRow("SecretKey:", self.vol_sk)
        f.addRow("Region:", self.vol_region)
        f.addRow("代理模式:", self.vol_proxy)
        f.addRow(QLabel("<font color='gray'>火山引擎控制台获取密钥：<br>"
                        "console.volcengine.com -> 密钥管理<br>"
                        "需开通机器翻译服务，每月免费 200 万字符。</font>"))
        return w

    def _tab_ai(self, c):
        w = QWidget(); f = QFormLayout(w); f.setSpacing(12)
        self.ai_key = QLineEdit(c.get('ai_api_key', ''))
        self.ai_key.setPlaceholderText("输入 API Key")
        self.ai_endpoint = QLineEdit(c.get('ai_endpoint', ''))
        self.ai_endpoint.setPlaceholderText("https://api.openai.com/v1")
        self.ai_model = QLineEdit(c.get('ai_model', ''))
        self.ai_model.setPlaceholderText("gpt-3.5-turbo")
        self.ai_prompt = QTextEdit()
        self.ai_prompt.setText(c.get('ai_prompt', ''))
        self.ai_prompt.setMaximumHeight(100)
        self.ai_proxy = _proxy_combo()
        self.ai_proxy.setCurrentText(c.get('ai_proxy_mode', 'direct'))
        f.addRow("API Key:", self.ai_key)
        f.addRow("Endpoint:", self.ai_endpoint)
        f.addRow("Model:", self.ai_model)
        f.addRow("Prompt:", self.ai_prompt)
        f.addRow("代理模式:", self.ai_proxy)
        f.addRow(QLabel("<font color='gray'>支持 OpenAI 及所有兼容 API（DeepSeek、Kimi 等）。<br>"
                        "只需修改 Endpoint 和 Model 即可。</font>"))
        return w

    def browse_icon(self):
        f, _ = QFileDialog.getOpenFileName(self, "选择图标", "", "Images (*.png *.jpg *.jpeg *.ico *.svg)")
        if f: self.icon_path_display.setText(f)

    def save(self):
        new_config = {
            "engine":             self.engine_combo.currentText(),
            "image_engine":       self.image_engine_combo.currentText(),
            "auto_start":         self.auto_start.isChecked(),
            "proxy_url":          self.proxy_url.text(),
            "custom_icon_path":   self.icon_path_display.text(),
            "google_proxy_mode":  self.g_proxy_mode.currentText(),
            "deepl_api_key":      self.deepl_key.text(),
            "deepl_proxy_mode":   self.deepl_proxy.currentText(),
            "microsoft_api_key":  self.ms_key.text(),
            "microsoft_region":   self.ms_region.text(),
            "microsoft_proxy_mode": self.ms_proxy.currentText(),
            "tencent_secret_id":  self.tx_id.text(),
            "tencent_secret_key": self.tx_key.text(),
            "tencent_region":     self.tx_region.text(),
            "tencent_proxy_mode": self.tx_proxy.currentText(),
            "volcano_access_key": self.vol_ak.text(),
            "volcano_secret_key": self.vol_sk.text(),
            "volcano_region":     self.vol_region.text(),
            "volcano_proxy_mode": self.vol_proxy.currentText(),
            "ai_api_key":         self.ai_key.text(),
            "ai_endpoint":        self.ai_endpoint.text(),
            "ai_model":           self.ai_model.text(),
            "ai_prompt":          self.ai_prompt.toPlainText(),
            "ai_proxy_mode":      self.ai_proxy.currentText(),
            "history_max_count":  int(self.history_max_combo.currentText()),
        }
        self.config_saved.emit(new_config)
        self.hide()

# ================================================================
#  翻译历史记录窗口
# ================================================================

def _history_style():
    fs = sp(13)
    return f"""
    QWidget {{ font-size: {fs}px; }}
    QScrollArea {{ border: none; background: #f8f9fa; }}
    QPushButton#clear_btn {{
        background: #e74c3c; color: white; border: none;
        border-radius: 6px; padding: 6px 16px; font-size: {fs}px;
    }}
    QPushButton#clear_btn:hover {{ background: #c0392b; }}
"""

class HistoryWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("翻译历史记录")
        self.resize(620, 500)
        self.setStyleSheet(_history_style())

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(12, 12, 12, 12)
        self.root_layout.setSpacing(8)

        # 顶部操作栏
        top_bar = QHBoxLayout()
        self.title_label = QLabel("翻译历史记录")
        self.title_label.setStyleSheet(f"font-size:{sp(16)}px; font-weight:bold; color:#333;")
        self.count_label = QLabel("")
        self.count_label.setStyleSheet(f"color: gray; font-size: {sp(12)}px;")
        clear_btn = QPushButton("清空历史")
        clear_btn.setObjectName("clear_btn")
        clear_btn.clicked.connect(self._clear_history)
        top_bar.addWidget(self.title_label)
        top_bar.addWidget(self.count_label)
        top_bar.addStretch()
        top_bar.addWidget(clear_btn)
        self.root_layout.addLayout(top_bar)

        # 滚动区域
        from PyQt5.QtWidgets import QScrollArea
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(8)
        self.scroll_layout.addStretch()
        self.scroll.setWidget(self.scroll_content)
        self.root_layout.addWidget(self.scroll)

    def load_and_display(self, history):
        """加载并显示历史记录列表"""
        # 清空旧的卡片
        while self.scroll_layout.count() > 0:
            item = self.scroll_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        self.count_label.setText(f"共 {len(history)} 条")

        if not history:
            empty = QLabel("暂无翻译历史记录")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(f"color: #999; font-size: {sp(14)}px; padding: 40px;")
            self.scroll_layout.addWidget(empty)
            self.scroll_layout.addStretch()
            return

        for record in history:
            card = self._make_card(record)
            self.scroll_layout.addWidget(card)

        self.scroll_layout.addStretch()

    def _make_card(self, record):
        """为单条历史记录创建卡片 widget"""
        card = QWidget()
        card.setStyleSheet("""
            QWidget#card {
                background: white; border: 1px solid #e0e0e0;
                border-radius: 10px;
            }
            QWidget#card:hover { border-color: #667eea; }
        """)
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        # 时间 + 引擎 + 语言
        engine_name = ENGINE_NAMES.get(record.get("engine", ""), record.get("engine", ""))
        lang = "中文" if record.get("target_lang") == "zh-CN" else "English"
        meta = QLabel(f"{record.get('time', '')}    {engine_name}  →  {lang}")
        meta.setStyleSheet(f"color: #888; font-size: {sp(11)}px;")
        layout.addWidget(meta)

        # 原文
        source = record.get("source", "")
        if source and source != "[图片翻译]":
            src_label = QLabel(f"原文: {source[:120]}{'...' if len(source) > 120 else ''}")
            src_label.setWordWrap(True)
            src_label.setStyleSheet(f"color: #555; font-size: {sp(12)}px;")
            layout.addWidget(src_label)
        elif source == "[图片翻译]":
            src_label = QLabel("原文: [图片翻译]")
            src_label.setStyleSheet(f"color: #888; font-size: {sp(12)}px; font-style: italic;")
            layout.addWidget(src_label)

        # 译文
        result = record.get("result", "")
        res_label = QLabel(f"译文: {result[:200]}{'...' if len(result) > 200 else ''}")
        res_label.setWordWrap(True)
        res_label.setStyleSheet(f"color: #2c3e50; font-size: {sp(13)}px;")
        layout.addWidget(res_label)

        # 复制按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        copy_btn = QPushButton("复制译文")
        copy_btn.setFixedHeight(26)
        copy_btn.setStyleSheet("""
            QPushButton {
                background: #667eea; color: white; border: none;
                border-radius: 5px; padding: 2px 12px; font-size: %dpx;
            }
            QPushButton:hover { background: #5568d3; }
        """ % sp(12))
        copy_btn.clicked.connect(lambda checked, txt=result: QApplication.clipboard().setText(txt))
        btn_row.addWidget(copy_btn)
        layout.addLayout(btn_row)

        return card

    def _clear_history(self):
        """清空所有历史记录"""
        from config_manager import save_history
        save_history([])
        self.load_and_display([])

#!/usr/bin/env python3
"""NEXUS — PS5 Utility Suite (PyQt6)."""

import os
import sys
import json
import re
import sqlite3
import string
import struct
import subprocess
import tempfile
import shutil
import socket
import time
import uuid
import datetime
from ftplib import FTP, error_perm

try:
    from PyQt6.QtCore import (
        Qt, QThread, pyqtSignal, pyqtSlot, QObject, QTimer, QSize, QUrl, QDateTime, QPoint,
        QPropertyAnimation, QEasingCurve, QRect, QParallelAnimationGroup
    )
    from PyQt6.QtGui import (
        QIcon, QFont, QColor, QPainter, QPainterPath, QPen, QBrush, QPixmap, QLinearGradient
    )
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
        QPushButton, QLineEdit, QComboBox, QStackedWidget, QTextEdit, 
        QTreeWidget, QTreeWidgetItem, QHeaderView, QDialog, QSlider, QFrame, 
        QSizePolicy, QFileDialog, QSplitter, QProgressBar, QMessageBox
    )
except ImportError:
    print("PyQt6 is required. Install with: pip install PyQt6")
    sys.exit(1)

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False

try:
    import winsound
    HAS_SOUND = True
except ImportError:
    HAS_SOUND = False


#  CONSTANTS & CONFIG
APP_NAME     = "NEXUS"
APP_TITLE    = "NEXUS — PS5 Utility Suite"
APP_SUBTITLE = "PS5 Utility Suite"

DEFAULT_TITLE_IDS        = ["PPSA01650", "PPSA01651", "PPSA01652"]
DEFAULT_VERSION          = "99.999.999"
DEFAULT_VERSION_FILE_URI = "https://127.0.0.1"

REMOTE_AUTOLOAD_BASE = "/data/ps5_autoloader"

REMOTE_YT_APPINFO_DB = "/system_data/priv/mms/appinfo.db"
REMOTE_YT_APP_DB     = "/system_data/priv/mms/app.db"

REMOTE_ICON_PATH_TEMPLATE  = "/user/appmeta/{title_id}/icon0.png"
REMOTE_PARAM_SYS_TEMPLATE  = "/system_data/priv/appmeta/{title_id}/param.json"
REMOTE_PARAM_USER_TEMPLATE = "/user/appmeta/{title_id}/param.json"

REMOTE_SANDBOX_TEMPLATE = (
    "/mnt/sandbox/{title_id}_{sandbox_idx}/download0/cache/splash_screen/"
    "aHR0cHM6Ly93d3cueW91dHViZS5jb20vdHY=/"
)
SANDBOX_IDX_CHOICES = ["000", "001", "002"]

BROWSER_BOOKMARKS = [
    ("Garlic Saves", 8082, 105),
    ("CheatRunner", 9999, 100),
    ("BFPilot", 5905, 80),
    ("PS5 Upload :9113", 9113, 125),
    ("PS5 Upload :9114", 9114, 125),
]

PAYLOAD_EXTS     = (".bin", ".elf")
DEFAULT_DELAY_MS = 2000
APP_CONFIG_DIR   = os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "NexusPS5Utility")
SETTINGS_FILE    = os.path.join(APP_CONFIG_DIR, "settings.json")
TCP_HISTORY_FILE = os.path.join(APP_CONFIG_DIR, "tcp_history.json")


#  THEME (QSS) — Dark + Light
class Theme:
    """Active palette tokens. Call Theme.apply_dark() / apply_light() then rebuild QSS."""
    ACCENT_RED  = "#FF0033"
    ACCENT_ROSE = "#CC0028"
    GREEN       = "#12C55E"
    RED_GLOW    = "#FF0033"
    ORANGE      = "#FF5C42"
    WHITE       = "#F5F5F5"
    BLACK       = "#111111"

    # defaults = dark
    BG_DARK     = "#111111"
    BG_MID      = "#1A1A1A"
    BG_SURFACE  = "#1E1E1E"
    BG_CARD     = "#242424"
    BG_INPUT    = "#2A2A2A"
    ACCENT_WARM = "#F5F5F5"
    TEXT        = "#F5F5F5"
    TEXT_DIM    = "#AAAAAA"
    TEXT_MUTED  = "#665665"
    SEPARATOR   = "#333333"
    HEADER_TEXT = "#F5F5F5"
    HEADER_BG   = "#242424"
    INSET_BG    = "#111111"
    ICON_CARD_BG = "#242424"
    mode        = "dark"

    @classmethod
    def apply_dark(cls):
        cls.mode = "dark"
        cls.BG_DARK     = "#111111"
        cls.BG_MID      = "#1A1A1A"
        cls.BG_SURFACE  = "#1E1E1E"
        cls.BG_CARD     = "#242424"
        cls.BG_INPUT    = "#2A2A2A"
        cls.ACCENT_WARM = "#F5F5F5"
        cls.TEXT        = "#F5F5F5"
        cls.TEXT_DIM    = "#AAAAAA"
        cls.TEXT_MUTED  = "#665665"
        cls.SEPARATOR   = "#333333"
        cls.HEADER_TEXT = "#F5F5F5"
        cls.HEADER_BG   = "#242424"
        cls.INSET_BG    = "#0A0A0A"
        cls.ICON_CARD_BG = "#1A1A1A"

    @classmethod
    def apply_light(cls):
        cls.mode = "light"
        cls.BG_DARK     = "#E8EAED"
        cls.BG_MID      = "#F1F3F4"
        cls.BG_SURFACE  = "#FFFFFF"
        cls.BG_CARD     = "#E8EAED"
        cls.BG_INPUT    = "#FFFFFF"
        cls.ACCENT_WARM = "#111111"
        cls.TEXT        = "#111111"
        cls.TEXT_DIM    = "#5F6368"
        cls.TEXT_MUTED  = "#80868B"
        cls.SEPARATOR   = "#DADCE0"
        cls.HEADER_TEXT = "#FFFFFF"
        cls.HEADER_BG   = "#3C4043"
        cls.INSET_BG    = "#202124"
        cls.ICON_CARD_BG = "#BDC1C6"

    @classmethod
    def build_qss(cls):
        return f"""
QWidget {{
    background-color: {cls.BG_DARK};
    color: {cls.TEXT};
    font-family: "Segoe UI", sans-serif;
    font-size: 10pt;
}}
QFrame#Sidebar {{
    background-color: {cls.BG_MID};
    border-right: 1px solid {cls.SEPARATOR};
}}
QFrame#Card {{
    background-color: {cls.BG_SURFACE};
    border-radius: 8px;
    border: 1px solid {cls.SEPARATOR};
}}
QLabel {{
    background-color: transparent;
}}
QLabel#Brand {{
    color: {cls.ACCENT_RED};
    font-size: 22pt;
    font-weight: bold;
}}
QLabel#Heading {{
    color: {cls.ACCENT_WARM};
    font-size: 16pt;
    font-weight: bold;
}}
QLineEdit, QComboBox {{
    background-color: {cls.BG_INPUT};
    border: 1px solid {cls.SEPARATOR};
    border-radius: 6px;
    padding: 4px 8px;
    color: {cls.TEXT};
}}
QLineEdit:focus, QComboBox:focus {{
    border: 1px solid {cls.ACCENT_RED};
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border: none;
    border-left: 1px solid {cls.SEPARATOR};
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
    background: {cls.BG_CARD};
}}
QComboBox::down-arrow {{
    image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMiIgaGVpZ2h0PSIxMiIgdmlld0JveD0iMCAwIDEyIDEyIj48cG9seWdvbiBwb2ludHM9IjIsNCA2LDkgMTAsNCIgZmlsbD0iIzY2NjY2NiIvPjwvc3ZnPg==);
    width: 12px;
    height: 12px;
}}
QComboBox QAbstractItemView {{
    background-color: {cls.BG_SURFACE};
    color: {cls.TEXT};
    selection-background-color: {cls.ACCENT_RED};
    border: 1px solid {cls.SEPARATOR};
}}
QPushButton {{
    background-color: {cls.BG_CARD};
    border: 1px solid {cls.SEPARATOR};
    border-radius: 6px;
    padding: 5px 12px;
    color: {cls.TEXT};
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {cls.BG_INPUT};
    border-color: {cls.TEXT_DIM};
}}
QPushButton:pressed {{
    background-color: {cls.SEPARATOR};
}}
QPushButton#Primary {{
    background-color: {cls.ACCENT_RED};
    border: none;
    font-weight: bold;
    color: #FFFFFF;
}}
QPushButton#Primary:hover {{
    background-color: {cls.ACCENT_ROSE};
}}
QPushButton#Danger {{
    background-color: {cls.BG_CARD};
    border: 1px solid {cls.ACCENT_RED};
    color: {cls.ACCENT_RED};
    font-weight: bold;
}}
QPushButton#Danger:hover {{
    background-color: {cls.ACCENT_RED};
    color: #FFFFFF;
}}
QPushButton#SidebarBtn {{
    background-color: transparent;
    border: none;
    text-align: left;
    padding-left: 14px;
    font-size: 11pt;
    font-weight: bold;
    color: {cls.TEXT_DIM};
    border-radius: 6px;
}}
QPushButton#SidebarBtn:hover {{
    background-color: {cls.BG_CARD};
    color: {cls.TEXT};
}}
QPushButton#SidebarBtn:checked {{
    background-color: {cls.ACCENT_RED};
    color: #FFFFFF;
}}
QTreeWidget {{
    background-color: {cls.BG_SURFACE};
    border: 1px solid {cls.SEPARATOR};
    border-radius: 6px;
    outline: none;
}}
QTreeWidget::item {{
    height: 28px;
    border-bottom: 1px solid {cls.BG_DARK};
}}
QTreeWidget::item:hover {{
    background-color: {cls.BG_CARD};
}}
QTreeWidget::item:selected {{
    background-color: {cls.ACCENT_RED};
    color: #FFFFFF;
}}
QHeaderView::section {{
    background-color: {cls.HEADER_BG};
    color: {cls.HEADER_TEXT};
    font-weight: bold;
    border: none;
    border-bottom: 2px solid {cls.SEPARATOR};
    padding: 4px 8px;
}}
QTextEdit#LogBox {{
    background-color: {cls.INSET_BG};
    color: {cls.GREEN};
    font-family: "Consolas", monospace;
    font-size: 9.5pt;
    border: 1px solid {cls.SEPARATOR};
    border-radius: 6px;
}}
QLabel#IconPreview {{
    background-color: #111111;
    color: #AAAAAA;
    border: 1px solid {cls.SEPARATOR};
    border-radius: 8px;
}}
QFrame#YtIconCard {{
    background-color: {cls.ICON_CARD_BG};
    border-radius: 8px;
    border: 1px solid {cls.SEPARATOR};
}}
QScrollBar:vertical {{
    background: {cls.BG_SURFACE};
    width: 10px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: {cls.BG_CARD};
    border-radius: 5px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {cls.ACCENT_RED};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QSlider {{
    border: none;
    background: transparent;
}}
QSlider::groove:horizontal {{
    background: {cls.BG_CARD};
    height: 8px;
    border-radius: 4px;
    border: none;
    outline: none;
}}
QSlider::sub-page:horizontal {{
    background: {cls.ACCENT_RED};
    border-radius: 4px;
    border: none;
}}
QSlider::add-page:horizontal {{
    background: {cls.BG_CARD};
    border-radius: 4px;
    border: none;
}}
QSlider::handle:horizontal {{
    background: {cls.ACCENT_RED};
    border: none;
    width: 16px;
    height: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}}
QSlider::handle:horizontal:hover {{
    background: {cls.ACCENT_ROSE};
}}
"""

GLOBAL_QSS = Theme.build_qss()


#  UTILITIES & PERSISTENCE
def load_settings():
    defaults = {
        "last_ip": "",
        "last_port": "2121",
        "ip_history": [],
        "port_history": ["2121", "9021"],
        "pc_folder": os.path.expanduser("~"),
        "is_muted": False,
        "theme": "dark",
    }
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
        if isinstance(saved, dict):
            defaults.update(saved)
    except Exception:
        pass
    return defaults

def save_settings(settings):
    try:
        os.makedirs(APP_CONFIG_DIR, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass

def load_tcp_history():
    try:
        if os.path.exists(TCP_HISTORY_FILE):
            with open(TCP_HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []

def save_tcp_history(history):
    try:
        os.makedirs(APP_CONFIG_DIR, exist_ok=True)
        with open(TCP_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception:
        pass

def fmt_bytes(n):
    n = int(n or 0)
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n} {unit}"
        n //= 1024
    return f"{n} TB"

def fmt_speed(bps):
    if bps < 1024: return f"{bps:.0f} B/s"
    elif bps < 1024*1024: return f"{bps/1024:.1f} KB/s"
    else: return f"{bps/(1024*1024):.2f} MB/s"

def fmt_eta(seconds):
    if seconds < 0 or seconds > 359999: return "--:--"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0: return f"{h}h {m:02d}m"
    return f"{m:02d}:{s:02d}"

def ts_fmt(value):
    if not value: return ""
    try: return datetime.datetime.fromtimestamp(float(value)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception: return ""

def is_payload_name(name):
    return name.lower().endswith(PAYLOAD_EXTS)

def ensure_uid(item):
    if "uid" not in item or not item["uid"]:
        item["uid"] = uuid.uuid4().hex[:10]
    return item

def get_drives():
    drives = []
    if sys.platform == "win32":
        try:
            for d in os.listdrives():
                if os.path.isdir(d):
                    drives.append(d)
            return drives
        except AttributeError:
            pass
        for letter in string.ascii_uppercase:
            path = f"{letter}:\\"
            if os.path.isdir(path):
                drives.append(path)
    else:
        drives.append("/")
    return drives or [os.path.expanduser("~")]

def parse_autoload_text(text):
    blocks = []
    current = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line: continue
        if line.startswith("!"):
            if current is None: continue
            try: current["delay_ms"] = int(line[1:].strip())
            except ValueError: current["delay_ms"] = None
            continue
        current = ensure_uid({"name": line, "delay_ms": None, "enabled": True})
        blocks.append(current)
    return blocks

def build_autoload_text(blocks):
    lines = []
    enabled_blocks = [b for b in blocks if b.get("enabled", True) and b.get("name")]
    for i, block in enumerate(enabled_blocks):
        lines.append(block["name"].strip())
        delay_ms = block.get("delay_ms", None)
        if delay_ms is not None and i < len(enabled_blocks) - 1:
            lines.append(f"!{int(delay_ms)}")
    return "\n".join(lines) + ("\n" if lines else "")

def merge_autoload_payloads(autoload_blocks, available_names):
    available = sorted({os.path.basename(n) for n in available_names if is_payload_name(n)}, key=str.lower)
    known = set()
    merged = []
    for block in autoload_blocks:
        name = os.path.basename(block.get("name", ""))
        if not name or name in known: continue
        known.add(name)
        merged.append(ensure_uid({"name": name, "delay_ms": block.get("delay_ms"), "enabled": name in available}))
    for name in available:
        if name not in known:
            merged.append(ensure_uid({"name": name, "delay_ms": None, "enabled": False}))
    return merged

def collect_folder_entries(folder_path):
    entries = []
    for root, _, files in os.walk(folder_path):
        for name in sorted(files):
            full = os.path.join(root, name)
            rel = os.path.relpath(full, folder_path)
            try: size = os.path.getsize(full)
            except Exception: size = 0
            entries.append({"name": rel, "path": full, "size": size})
    return entries


#  CUSTOM UI WIDGETS
class CustomMessageBox(QDialog):
    """Unique custom-styled modal message box avoiding basic OS dialogs."""
    def __init__(self, title, message, parent=None, buttons=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Theme.BG_SURFACE};
                border: 2px solid {Theme.ACCENT_RED};
                border-radius: 8px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"color: {Theme.ACCENT_RED}; font-weight: bold; font-size: 13pt;")
        layout.addWidget(lbl_title)
        
        lbl_msg = QLabel(message)
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet(f"color: {Theme.TEXT}; font-size: 10.5pt; margin-top: 10px; margin-bottom: 15px;")
        layout.addWidget(lbl_msg)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.clicked_button = None
        
        buttons = buttons or [("OK", True, "Primary")]
        for text, result_val, btn_style in buttons:
            btn = QPushButton(text)
            if btn_style == "Primary":
                btn.setObjectName("Primary")
            elif btn_style == "Danger":
                btn.setObjectName("Danger")
            btn.clicked.connect(lambda _, r=result_val: self._on_click(r))
            btn_layout.addWidget(btn)
            
        layout.addLayout(btn_layout)
        self.setMinimumWidth(380)

    def _on_click(self, val):
        self.clicked_button = val
        self.accept()

    @staticmethod
    def show_info(parent, title, message):
        dlg = CustomMessageBox(title, message, parent, [("OK", True, "Primary")])
        dlg.exec()
        return True

    @staticmethod
    def ask_yes_no(parent, title, message):
        dlg = CustomMessageBox(title, message, parent, [("Yes", True, "Primary"), ("No", False, "Normal")])
        dlg.exec()
        return dlg.clicked_button is True

    @staticmethod
    def ask_conflict(parent, filename):
        dlg = CustomMessageBox(
            "File Exists",
            f"'{filename}' already exists. What would you like to do?",
            parent,
            [("Overwrite", "overwrite", "Primary"), ("Rename (_copy)", "rename", "Normal"), ("Skip", "skip", "Normal")]
        )
        dlg.exec()
        return dlg.clicked_button or "skip"


class GlowIndicator(QWidget):
    """Pulsing hardware-accelerated connection glow widget."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(22, 22)
        self.connected = False
        self.phase = 0.0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(60)

    def set_connected(self, state):
        self.connected = state
        self.update()

    def animate(self):
        self.phase += 0.15
        if self.phase > 6.28:
            self.phase = 0.0
        self.update()

    def paintEvent(self, event):
        import math
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        cx, cy = self.width() / 2, self.height() / 2
        r = 6.0
        
        alpha = 0.35 + 0.2 * math.sin(self.phase)
        base_color = QColor(Theme.GREEN if self.connected else Theme.RED_GLOW)
        
        for i in range(3, 0, -1):
            gr = r + i * 2.0
            c = QColor(base_color)
            c.setAlphaF(max(0, min(1, alpha * (1 - i/4))))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(c))
            painter.drawEllipse(QPoint(int(cx), int(cy)), int(gr), int(gr))
            
        painter.setBrush(QBrush(base_color))
        painter.drawEllipse(QPoint(int(cx), int(cy)), int(r), int(r))
        
        hl_color = QColor(255, 255, 255, 120)
        painter.setBrush(QBrush(hl_color))
        painter.drawEllipse(QPoint(int(cx - 2), int(cy - 2)), 2, 2)


class FancyProgressBar(QWidget):
    """Smooth GPU gradient progress bar with automatic zero reset upon task completion."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(24)
        self.value = 0.0
        self.display_value = 0.0
        self.speed_text = ""
        self.eta_text = ""
        self.label_text = ""
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(30)
        
        self.reset_timer = QTimer(self)
        self.reset_timer.setSingleShot(True)
        self.reset_timer.timeout.connect(self._do_reset)

    def set_progress(self, val, speed=0, eta=-1, label=""):
        val = max(0.0, min(100.0, float(val)))
        self.value = val
        if self.value <= 0:
            self.display_value = 0.0
            
        self.speed_text = fmt_speed(speed) if speed > 0 else ""
        self.eta_text = fmt_eta(eta) if eta >= 0 else ""
        self.label_text = label
        
        if self.value >= 100.0:
            if not self.reset_timer.isActive():
                self.reset_timer.start(1500)  # Reset to 0 after 1.5 seconds
        else:
            self.reset_timer.stop()

    def _do_reset(self):
        self.value = 0.0
        self.display_value = 0.0
        self.speed_text = ""
        self.eta_text = ""
        self.label_text = ""
        self.update()

    def tick(self):
        diff = self.value - self.display_value
        if abs(diff) > 0.1:
            self.display_value += diff * 0.2
        else:
            self.display_value = self.value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        r = h / 2
        
        # Pill Background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(Theme.BG_MID)))
        painter.drawRoundedRect(0, 0, w, h, r, r)
        
        if self.display_value <= 0:
            return
            
        fill_w = (self.display_value / 100.0) * w
        fill_w = max(fill_w, r*2 if self.display_value > 0 else 0)
        
        gradient = QLinearGradient(0, 0, fill_w, 0)
        if self.value >= 100.0:
            gradient.setColorAt(0, QColor(Theme.GREEN))
            gradient.setColorAt(1, QColor("#10B981"))
        else:
            gradient.setColorAt(0, QColor(Theme.ACCENT_RED))
            gradient.setColorAt(1, QColor(Theme.ORANGE))
            
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(0, 0, int(fill_w), h, r, r)
        
        text = f"{self.display_value:.0f}%"
        extra = []
        if self.speed_text: extra.append(self.speed_text)
        if self.eta_text: extra.append(f"ETA {self.eta_text}")
        if self.label_text: extra.append(self.label_text)
        if extra: text += "   " + "  ".join(extra)
        
        painter.setPen(QColor(Theme.TEXT))
        font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)


#  BACKGROUND WORKER THREAD ARCHITECTURE
class WorkerSignals(QObject):
    log = pyqtSignal(str)
    progress = pyqtSignal(float, float, float, str) # val, speed, eta, label
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str, object) # success, message, data

class BaseTaskWorker(QThread):
    def __init__(self, target_func, *args, **kwargs):
        super().__init__()
        self.signals = WorkerSignals()
        self.target_func = target_func
        self.args = args
        self.kwargs = kwargs
        self.is_cancelled = False

    def cancel(self):
        self.is_cancelled = True

    def run(self):
        try:
            res = self.target_func(self.signals, self, *self.args, **self.kwargs)
            self.signals.finished.emit(True, "OK", res)
        except Exception as e:
            self.signals.log.emit(f"[ERROR] {e}")
            self.signals.finished.emit(False, str(e), None)


#  MAIN APPLICATION CLASS
class NexusApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1180, 740)
        self.setMinimumSize(850, 580)
        
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nexus_icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.settings = load_settings()
        self.is_muted = self.settings.get("is_muted", False)
        if self.settings.get("theme") == "light":
            Theme.apply_light()
        else:
            Theme.apply_dark()
        self.setStyleSheet(Theme.build_qss())
        self.ftp = None
        self.ftp5 = None
        self.tcp_history = load_tcp_history()
        
        self.current_ip = self.settings.get("last_ip", "")
        self.current_port = self.settings.get("last_port", "2121")
        self.current_title_id = DEFAULT_TITLE_IDS[0]
        
        self.autoload_blocks = []
        self.autoload_local_dir = None
        self.autoload_backup_path = None
        
        self.y2jb_items = []
        self._y2jb_has_remote = False
        
        self.ftp5_local_folder = self.settings.get("pc_folder", os.path.expanduser("~"))
        self.ftp5_remote_path = "/"
        self.ftp5_cancel_flag = False
        
        self.selected_icon_path = None
        self.active_workers = []
        
        self._build_ui()
        self._load_tcp_history_tree()
        self._ftp5_refresh_local_tree()

    def _sound_path(self):
        """Resolve UI click sample: next to script, or bundled sounds/ folder."""
        candidates = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds", "ui_click.wav"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui_click.wav"),
            os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "NexusPS5Utility", "ui_click.wav"),
        ]
        for p in candidates:
            if os.path.isfile(p):
                return p
        return None

    def play_sound(self):
        if self.is_muted:
            return
        path = self._sound_path()
        if path and HAS_SOUND:
            try:
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                return
            except Exception:
                pass
        if HAS_SOUND:
            try:
                winsound.Beep(880, 35)
            except Exception:
                pass

    #  UI INITIALIZATION & LAYOUT
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(220)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(12, 16, 12, 12)
        
        lbl_brand = QLabel(APP_NAME)
        lbl_brand.setObjectName("Brand")
        side_layout.addWidget(lbl_brand)
        side_layout.addSpacing(2)
        side_layout.addStretch()
        
        # Connection Box
        conn_box = QVBoxLayout()
        conn_box.setSpacing(2)
        
        lbl_ip = QLabel("Console IP")
        lbl_ip.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 9pt;")
        self.ip_entry = QLineEdit(self.current_ip)
        self.ip_entry.setPlaceholderText("192.168.1.1")
        self.ip_entry.textChanged.connect(self._autosave_conn)
        
        lbl_port = QLabel("Port")
        lbl_port.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 9pt;")
        self.port_entry = QLineEdit(self.current_port)
        self.port_entry.textChanged.connect(self._autosave_conn)
        
        lbl_title = QLabel("Title ID")
        lbl_title.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 9pt;")
        self.title_combo = QComboBox()
        self.title_combo.addItems(DEFAULT_TITLE_IDS)
        
        conn_box.addWidget(lbl_ip)
        conn_box.addWidget(self.ip_entry)
        conn_box.addWidget(lbl_port)
        conn_box.addWidget(self.port_entry)
        conn_box.addWidget(lbl_title)
        conn_box.addWidget(self.title_combo)
        conn_box.addStretch()
        side_layout.addLayout(conn_box)
        side_layout.addSpacing(3)

        
        # Connect / Disconnect Buttons
        btn_row = QHBoxLayout()
        self.btn_connect = QPushButton("Connect")
        self.btn_connect.setObjectName("Primary")
        self.btn_connect.clicked.connect(self._on_connect)
        self.btn_disconnect = QPushButton("Disconnect")
        self.btn_disconnect.clicked.connect(self._on_disconnect)
        btn_row.addWidget(self.btn_connect)
        btn_row.addWidget(self.btn_disconnect)
        side_layout.addLayout(btn_row)
        
        status_row = QHBoxLayout()
        self.glow = GlowIndicator()
        self.conn_label = QLabel("Disconnected")
        self.conn_label.setStyleSheet(f"color: {Theme.RED_GLOW}; font-weight: bold;")
        
        self.btn_mute = QLabel("🔇" if self.is_muted else "🔊")
        self.btn_mute.setFixedSize(28, 28)
        self.btn_mute.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_mute.setToolTip("Toggle Sound Effects")
        self.btn_mute.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mute.setStyleSheet(f"""
            QLabel {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.SEPARATOR};
                border-radius: 6px;
                font-size: 14pt;
                padding: 0px;
            }}
            QLabel:hover {{
                background-color: {Theme.BG_INPUT};
                border-color: {Theme.TEXT_DIM};
            }}
        """)
        self.btn_mute.mousePressEvent = lambda e: self._toggle_mute()
        
        self.btn_theme = QLabel("☀️" if Theme.mode == "dark" else "🌙")
        self.btn_theme.setFixedSize(28, 28)
        self.btn_theme.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_theme.setToolTip("Toggle Light / Dark Theme")
        self.btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme.setStyleSheet(self.btn_mute.styleSheet())
        self.btn_theme.mousePressEvent = lambda e: self._toggle_theme()
        
        status_row.addWidget(self.glow)
        status_row.addWidget(self.conn_label)
        status_row.addSpacing(6)
        status_row.addWidget(self.btn_mute)
        status_row.addWidget(self.btn_theme)
        status_row.addStretch()
        side_layout.addLayout(status_row)
        side_layout.addSpacing(14)
        
        # Sidebar Tabs
        self.stack = QStackedWidget()
        self.tab_buttons = []
        
        tab_defs = [
            ("YouTube Patcher", "🎬", self._build_tab_yt),
            ("Autoload Editor", "📋", self._build_tab_autoload),
            ("Update Y2JB",     "📡", self._build_tab_y2jb),
            ("TCP Sender",      "🔌", self._build_tab_tcp),
            ("FTP Manager",     "📁", self._build_tab_ftp),
            ("FFPFSC Creator",  "💿", self._build_tab_ffpfsc),
            ("Console Browser", "🌐", self._build_tab_browser)
        ]
        
        for i, (name, icon, builder) in enumerate(tab_defs):
            btn = QPushButton(f"  {icon}   {name}")
            btn.setObjectName("SidebarBtn")
            btn.setCheckable(True)
            btn.setFixedHeight(38)
            btn.clicked.connect(lambda checked, idx=i: self._switch_tab(idx))
            side_layout.addWidget(btn)
            self.tab_buttons.append(btn)
            
            page = QWidget()
            builder(page)
            self.stack.addWidget(page)
            
        side_layout.addStretch()
        
        # Footer Credits
        lbl_quote = QLabel('"In my heart, I am Palestinian"\n- A Wise Man')
        lbl_quote.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 8.5pt; font-style: italic;")
        lbl_dev = QLabel("Issu. 2026")
        lbl_dev.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 8pt; font-weight: bold;")
        side_layout.addWidget(lbl_quote)
        side_layout.addWidget(lbl_dev)
        
        main_layout.addWidget(sidebar)
        
        content_wrap = QWidget()
        cw_layout = QVBoxLayout(content_wrap)
        cw_layout.setContentsMargins(12, 12, 12, 12)
        cw_layout.setSpacing(10)
        
        cw_layout.addWidget(self.stack, 1)
        
        # Log Box
        log_frame = QFrame()
        log_frame.setObjectName("Card")
        log_frame.setFixedHeight(200)
        log_layout = QVBoxLayout(log_frame)
        log_layout.setContentsMargins(5, 5, 5, 5)
        
        lbl_log = QLabel("⚡ Log")
        lbl_log.setStyleSheet(f"color: {Theme.ACCENT_RED}; font-weight: bold; font-size: 10.5pt;")
        log_layout.addWidget(lbl_log)
        
        self.log_box = QTextEdit()
        self.log_box.setObjectName("LogBox")
        self.log_box.setReadOnly(True)
        log_layout.addWidget(self.log_box)
        
        cw_layout.addWidget(log_frame)
        main_layout.addWidget(content_wrap, 1)
        
        self._switch_tab(0)

    def _toggle_mute(self):
        self.is_muted = not self.is_muted
        self.btn_mute.setText("🔇" if self.is_muted else "🔊")
        self.settings["is_muted"] = self.is_muted
        save_settings(self.settings)

    def _toggle_theme(self):
        self.play_sound()
        if Theme.mode == "dark":
            Theme.apply_light()
            self.btn_theme.setText("🌙")
        else:
            Theme.apply_dark()
            self.btn_theme.setText("☀️")
        self.setStyleSheet(Theme.build_qss())
        chrome = f"""
            QLabel {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.SEPARATOR};
                border-radius: 6px;
                font-size: 14pt;
                padding: 0px;
            }}
            QLabel:hover {{
                background-color: {Theme.BG_INPUT};
                border-color: {Theme.TEXT_DIM};
            }}
        """
        self.btn_mute.setStyleSheet(chrome)
        self.btn_theme.setStyleSheet(chrome)
        self.settings["theme"] = Theme.mode
        save_settings(self.settings)

    def changeEvent(self, event):
        """Subtle scale animation on maximize / restore (mac-style polish)."""
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMaximized() or (self.windowState() == Qt.WindowState.WindowNoState):
                try:
                    anim = QPropertyAnimation(self, b"windowOpacity")
                    anim.setDuration(180)
                    anim.setStartValue(0.82)
                    anim.setEndValue(1.0)
                    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                    anim.start()
                    self._win_anim = anim
                except Exception:
                    pass
        super().changeEvent(event)

    def _switch_tab(self, idx):
        self.play_sound()
        for i, btn in enumerate(self.tab_buttons):
            btn.setChecked(i == idx)
        self.stack.setCurrentIndex(idx)
        
        if idx == 3: # TCP tab defaults port to 9021
            self.port_entry.setText("9021")
        else:
            self.port_entry.setText(self.settings.get("last_port", "2121"))

    def log(self, msg):
        self.log_box.append(msg)

    def _autosave_conn(self):
        self.current_ip = self.ip_entry.text().strip()
        self.current_port = self.port_entry.text().strip()
        self.settings["last_ip"] = self.current_ip
        self.settings["last_port"] = self.current_port
        save_settings(self.settings)

    def get_title_id(self):
        return self.title_combo.currentText().strip().split()[0]

    #  CONNECTION LOGIC
    def _on_connect(self):
        self.play_sound()
        ip = self.ip_entry.text().strip()
        try: port = int(self.port_entry.text().strip())
        except ValueError:
            CustomMessageBox.show_info(self, "Error", "Port must be a valid integer.")
            return
            
        if not ip:
            CustomMessageBox.show_info(self, "Error", "Enter console IP first.")
            return
            
        self.btn_connect.setEnabled(False)
        self.log(f"Connecting to {ip}:{port} ...")
        
        def _connect_task(signals, worker):
            if self.ftp:
                try: self.ftp.quit()
                except: pass
            ftp = FTP()
            ftp.connect(ip, port, timeout=10)
            ftp.login()
            self.ftp = ftp
            return "Connected"

        worker = BaseTaskWorker(_connect_task)
        worker.signals.log.connect(self.log)
        worker.signals.finished.connect(self._on_connect_finished)
        worker.start()
        self.active_workers.append(worker)

    def _on_connect_finished(self, success, msg, res):
        self.btn_connect.setEnabled(True)
        if success:
            self.glow.set_connected(True)
            self.conn_label.setText("Connected") # ONLY CONNECTED (NO IP SHOWING)
            self.conn_label.setStyleSheet(f"color: {Theme.GREEN}; font-weight: bold;")
            self.log("FTP connected.")
        else:
            self.glow.set_connected(False)
            self.conn_label.setText("Disconnected")
            self.conn_label.setStyleSheet(f"color: {Theme.RED_GLOW}; font-weight: bold;")
            CustomMessageBox.show_info(self, "Connection Error", msg)

    def _on_disconnect(self):
        self.play_sound()
        if self.ftp:
            try: self.ftp.quit()
            except: pass
            self.ftp = None
        self.glow.set_connected(False)
        self.conn_label.setText("Disconnected")
        self.conn_label.setStyleSheet(f"color: {Theme.RED_GLOW}; font-weight: bold;")
        self.log("FTP disconnected.")

    #  TAB 1 — YOUTUBE PATCHER (CENTERED ICON VIEWER + COMPACT SIDE BUTTONS)
    def _build_tab_yt(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_heading = QLabel("🎬 YouTube Patcher")
        lbl_heading.setObjectName("Heading")
        layout.addWidget(lbl_heading)
        
        card = QFrame()
        card.setObjectName("YtIconCard")
        self.yt_icon_card = card
        cl = QHBoxLayout(card)
        cl.setContentsMargins(24, 20, 24, 20)
        cl.addStretch(1)
        
        self.icon_lbl = QLabel("No Icon")
        self.icon_lbl.setObjectName("IconPreview")
        self.icon_lbl.setFixedSize(170, 165)
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(self.icon_lbl)
        cl.addSpacing(16)
        
        # 3 Small Adjacent Buttons on the Right
        btn_vbox = QVBoxLayout()
        btn_vbox.setSpacing(8)
        btn_vbox.addStretch()
        
        btn_retrieve = QPushButton("Retrieve Icon")
        btn_retrieve.setFixedSize(130, 32)
        btn_retrieve.clicked.connect(self._yt_retrieve_icon)
        
        btn_load = QPushButton("Load from PC")
        btn_load.setFixedSize(130, 32)
        btn_load.clicked.connect(self._yt_load_icon)
        
        self.btn_up_icon = QPushButton("Upload Icon")
        self.btn_up_icon.setObjectName("Primary")
        self.btn_up_icon.setFixedSize(130, 32)
        self.btn_up_icon.setEnabled(False)
        self.btn_up_icon.clicked.connect(self._yt_upload_icon)
        
        btn_vbox.addWidget(btn_retrieve)
        btn_vbox.addWidget(btn_load)
        btn_vbox.addWidget(self.btn_up_icon)
        btn_vbox.addStretch()
        
        cl.addLayout(btn_vbox)
        cl.addStretch(1)
        layout.addWidget(card)
        
        lbl_desc = QLabel("Patch app.db, appinfo.db, and param.json for the selected Title ID.")
        lbl_desc.setStyleSheet(f"color: {Theme.TEXT_DIM}; margin-top: 10px;")
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_desc)
        
        patch_wrap = QHBoxLayout()
        patch_wrap.addStretch()
        self.btn_patch = QPushButton("⚡ Patch YouTube Now")
        self.btn_patch.setObjectName("Primary")
        self.btn_patch.setFixedSize(240, 38)
        self.btn_patch.clicked.connect(self._yt_do_patch)
        patch_wrap.addWidget(self.btn_patch)
        patch_wrap.addStretch()
        layout.addLayout(patch_wrap)
        
        self.yt_prog = FancyProgressBar()
        layout.addWidget(self.yt_prog)
        layout.addStretch()

    def _yt_retrieve_icon(self):
        self.play_sound()
        title_id = self.get_title_id()
        ip, port = self.current_ip, self.current_port
        if not ip:
            CustomMessageBox.show_info(self, "Error", "Enter console IP first.")
            return
            
        self.yt_prog.set_progress(0)
        self.log(f"[ICON] Retrieving icon for {title_id} ...")
        
        def _task(signals, worker):
            ftp = FTP()
            ftp.connect(ip, int(port), timeout=10)
            ftp.login()
            remote = REMOTE_ICON_PATH_TEMPLATE.format(title_id=title_id)
            fd, tmp = tempfile.mkstemp(suffix=".png")
            os.close(fd)
            with open(tmp, "wb") as f:
                ftp.retrbinary(f"RETR {remote}", f.write)
            ftp.quit()
            return tmp

        worker = BaseTaskWorker(_task)
        worker.signals.log.connect(self.log)
        worker.signals.finished.connect(self._yt_on_icon_retrieved)
        worker.start()
        self.active_workers.append(worker)

    def _yt_on_icon_retrieved(self, success, msg, tmp_file):
        if success and tmp_file and os.path.exists(tmp_file):
            pixmap = QPixmap(tmp_file)
            if not pixmap.isNull():
                self.icon_lbl.setPixmap(pixmap.scaled(160, 160, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.yt_prog.set_progress(100)
            self.log("[ICON] Icon retrieved successfully.")
            try: os.remove(tmp_file)
            except: pass
        else:
            self.yt_prog.set_progress(0)
            CustomMessageBox.show_info(self, "Retrieve Failed", msg)

    def _yt_load_icon(self):
        self.play_sound()
        fp, _ = QFileDialog.getOpenFileName(self, "Select PNG Icon", "", "PNG Image (*.png)")
        if fp:
            self.selected_icon_path = fp
            pixmap = QPixmap(fp)
            if not pixmap.isNull():
                self.icon_lbl.setPixmap(pixmap.scaled(160, 160, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                self.btn_up_icon.setEnabled(True)
                self.log(f"[ICON] Loaded local PNG: {os.path.basename(fp)}")

    def _yt_upload_icon(self):
        self.play_sound()
        if not self.selected_icon_path or not os.path.exists(self.selected_icon_path):
            return
        title_id = self.get_title_id()
        ip, port = self.current_ip, self.current_port
        self.yt_prog.set_progress(0)
        self.log(f"[ICON] Uploading icon to {title_id} ...")
        
        def _task(signals, worker):
            ftp = FTP()
            ftp.connect(ip, int(port), timeout=10)
            ftp.login()
            remote = REMOTE_ICON_PATH_TEMPLATE.format(title_id=title_id)
            with open(self.selected_icon_path, "rb") as f:
                ftp.storbinary(f"STOR {remote}", f)
            ftp.quit()
            return True

        worker = BaseTaskWorker(_task)
        worker.signals.log.connect(self.log)
        worker.signals.finished.connect(lambda s, m, r: self.yt_prog.set_progress(100 if s else 0))
        worker.start()
        self.active_workers.append(worker)

    def _yt_do_patch(self):
        self.play_sound()
        title_id = self.get_title_id()
        ip, port = self.current_ip, self.current_port
        if not CustomMessageBox.ask_yes_no(self, "Confirm Patch", f"Patch YouTube appinfo.db, app.db, and param.json for {title_id}?"):
            return
            
        self.btn_patch.setEnabled(False)
        self.yt_prog.set_progress(0)
        
        def _task(signals, worker):
            signals.log.emit(f"[PATCH] Connecting to {ip}:{port} ...")
            ftp = FTP()
            ftp.connect(ip, int(port), timeout=10)
            ftp.login()
            
            workdir = os.path.join(tempfile.gettempdir(), f"yt_patch_{title_id}")
            os.makedirs(workdir, exist_ok=True)
            local_appinfo = os.path.join(workdir, "appinfo.db")
            local_appdb   = os.path.join(workdir, "app.db")
            local_param   = os.path.join(workdir, "param.json")
            
            # Download
            with open(local_appinfo, "wb") as f: ftp.retrbinary(f"RETR {REMOTE_YT_APPINFO_DB}", f.write)
            signals.progress.emit(25, 0, -1, "appinfo.db")
            
            with open(local_appdb, "wb") as f: ftp.retrbinary(f"RETR {REMOTE_YT_APP_DB}", f.write)
            signals.progress.emit(50, 0, -1, "app.db")
            
            param_remote = REMOTE_PARAM_SYS_TEMPLATE.format(title_id=title_id)
            try:
                with open(local_param, "wb") as f: ftp.retrbinary(f"RETR {param_remote}", f.write)
            except:
                param_remote = REMOTE_PARAM_USER_TEMPLATE.format(title_id=title_id)
                with open(local_param, "wb") as f: ftp.retrbinary(f"RETR {param_remote}", f.write)
            signals.progress.emit(65, 0, -1, "param.json")
            
            # Patch Databases
            conn = sqlite3.connect(local_appinfo)
            cur = conn.cursor()
            cur.execute("UPDATE tbl_appinfo SET val = ? WHERE titleId = ? AND key = 'CONTENT_VERSION'", (DEFAULT_VERSION, title_id))
            cur.execute("UPDATE tbl_appinfo SET val = ? WHERE titleId = ? AND key = 'VERSION_FILE_URI'", (DEFAULT_VERSION_FILE_URI, title_id))
            conn.commit()
            conn.close()
            
            conn = sqlite3.connect(local_appdb)
            cur = conn.cursor()
            cur.execute("UPDATE tbl_contentinfo SET AppInfoJson = json_set(AppInfoJson, '$.CONTENT_VERSION', ?, '$.VERSION_FILE_URI', ?) WHERE titleId = ?", (DEFAULT_VERSION, DEFAULT_VERSION_FILE_URI, title_id))
            conn.commit()
            conn.close()
            
            # Patch Param.json
            with open(local_param, "r", encoding="utf-8") as f: data = json.load(f)
            for k in data:
                if k in ("targetContentVersion", "contentVersion"): data[k] = DEFAULT_VERSION
                elif k == "versionFileUri": data[k] = DEFAULT_VERSION_FILE_URI
            with open(local_param, "w", encoding="utf-8") as f: json.dump(data, f, indent=2)
            
            # Upload Back
            with open(local_appinfo, "rb") as f: ftp.storbinary(f"STOR {REMOTE_YT_APPINFO_DB}", f)
            with open(local_appdb, "rb") as f: ftp.storbinary(f"STOR {REMOTE_YT_APP_DB}", f)
            with open(local_param, "rb") as f: ftp.storbinary(f"STOR {param_remote}", f)
            
            ftp.quit()
            return True

        worker = BaseTaskWorker(_task)
        worker.signals.log.connect(self.log)
        worker.signals.progress.connect(lambda v, s, e, l: self.yt_prog.set_progress(v, s, e, l))
        worker.signals.finished.connect(self._yt_on_patch_finished)
        worker.start()
        self.active_workers.append(worker)

    def _yt_on_patch_finished(self, success, msg, res):
        self.btn_patch.setEnabled(True)
        if success:
            self.yt_prog.set_progress(100)
            self.log("[PATCH] YouTube patch complete!")
            CustomMessageBox.show_info(self, "Success", "YouTube patch complete.")
        else:
            self.yt_prog.set_progress(0)
            CustomMessageBox.show_info(self, "Patch Failed", msg)

    #  TAB 2 — AUTOLOAD EDITOR
    def _build_tab_autoload(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)
        
        lbl = QLabel("📋 Autoload Editor")
        lbl.setObjectName("Heading")
        layout.addWidget(lbl)
        
        # Toolbar Row 1: Target directory dropdown + Search Filter
        tb1 = QHBoxLayout()
        tb1.addWidget(QLabel("Target Directory:"))
        
        self.auto_dir_combo = QComboBox()
        self.auto_dir_combo.setEditable(False)
        self.auto_dir_combo.addItem(REMOTE_AUTOLOAD_BASE)
        for tid in DEFAULT_TITLE_IDS:
            self.auto_dir_combo.addItem(f"{REMOTE_AUTOLOAD_BASE}_{tid}")
        self.auto_dir_combo.setCurrentIndex(0)
        tb1.addWidget(self.auto_dir_combo, 1)
        
        tb1.addWidget(QLabel("Filter:"))
        self.auto_filter_input = QLineEdit()
        self.auto_filter_input.setFixedWidth(130)
        self.auto_filter_input.textChanged.connect(self._refresh_autoload_tree)
        tb1.addWidget(self.auto_filter_input)
        
        layout.addLayout(tb1)
        
        # Toolbar Row 2: Action Buttons
        tb2 = QHBoxLayout()
        
        btn_fetch = QPushButton("Fetch Console")
        btn_fetch.clicked.connect(self._autoload_fetch)
        btn_local = QPushButton("Load Local Folder")
        btn_local.clicked.connect(self._autoload_load_dir)
        btn_upload_single = QPushButton("Upload Single File")
        btn_upload_single.setObjectName("Primary")
        btn_upload_single.clicked.connect(self._autoload_upload_single)
        
        btn_sel_all = QPushButton("Select All")
        btn_sel_all.clicked.connect(lambda: self._autoload_set_all(True))
        btn_desel_all = QPushButton("Deselect All")
        btn_desel_all.clicked.connect(lambda: self._autoload_set_all(False))
        
        tb2.addWidget(btn_fetch)
        tb2.addWidget(btn_local)
        tb2.addWidget(btn_upload_single)
        tb2.addWidget(btn_sel_all)
        tb2.addWidget(btn_desel_all)
        tb2.addStretch()
        
        btn_save = QPushButton("Save & Upload")
        btn_save.setObjectName("Primary")
        btn_save.clicked.connect(self._autoload_save)
        btn_undo = QPushButton("Undo / Backup")
        btn_undo.clicked.connect(self._autoload_restore_backup)
        
        tb2.addWidget(btn_undo)
        tb2.addWidget(btn_save)
        layout.addLayout(tb2)
        
        # Toolbar Row 3: Move / Delay
        tb3 = QHBoxLayout()
        btn_up = QPushButton("▲ Up")
        btn_up.setFixedWidth(65)
        btn_up.clicked.connect(self._autoload_move_up)
        btn_down = QPushButton("▼ Down")
        btn_down.setFixedWidth(70)
        btn_down.clicked.connect(self._autoload_move_down)
        
        tb3.addWidget(btn_up)
        tb3.addWidget(btn_down)
        tb3.addWidget(QLabel("Delay (ms):"))
        self.auto_delay_input = QLineEdit(str(DEFAULT_DELAY_MS))
        self.auto_delay_input.setFixedWidth(70)
        tb3.addWidget(self.auto_delay_input)
        
        btn_apply_delay = QPushButton("Apply")
        btn_apply_delay.setFixedWidth(60)
        btn_apply_delay.clicked.connect(self._autoload_apply_delay)
        btn_rem_delay = QPushButton("Remove")
        btn_rem_delay.setFixedWidth(70)
        btn_rem_delay.clicked.connect(self._autoload_remove_delay)
        tb3.addWidget(btn_apply_delay)
        tb3.addWidget(btn_rem_delay)
        tb3.addStretch()
        layout.addLayout(tb3)
        
        self.auto_tree = QTreeWidget()
        self.auto_tree.setHeaderLabels(["State", "Payload File", "Delay ms"])
        hdr = self.auto_tree.header()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        hdr.setStretchLastSection(False)
        hdr.resizeSection(0, 70)
        hdr.resizeSection(2, 100)
        self.auto_tree.itemClicked.connect(self._autoload_on_item_click)
        layout.addWidget(self.auto_tree, 1)
        
        self.auto_prog = FancyProgressBar()
        layout.addWidget(self.auto_prog)

    def _get_target_autoload_dir(self):
        return self.auto_dir_combo.currentText().strip() or REMOTE_AUTOLOAD_BASE

    def _refresh_autoload_tree(self):
        self.auto_tree.clear()
        query = self.auto_filter_input.text().strip().lower()
        for b in self.autoload_blocks:
            if query and query not in b.get("name", "").lower():
                continue
            chk = "✦" if b.get("enabled", True) else "◇"
            delay = "" if b.get("delay_ms") is None else str(b["delay_ms"])
            item = QTreeWidgetItem([chk, b["name"], delay])
            item.setData(0, Qt.ItemDataRole.UserRole, b["uid"])
            self.auto_tree.addTopLevelItem(item)

    def _autoload_on_item_click(self, item, col):
        if col == 0:
            uid = item.data(0, Qt.ItemDataRole.UserRole)
            for b in self.autoload_blocks:
                if b["uid"] == uid:
                    b["enabled"] = not b.get("enabled", True)
                    break
            self._refresh_autoload_tree()

    def _autoload_set_all(self, state):
        for b in self.autoload_blocks: b["enabled"] = state
        self._refresh_autoload_tree()

    def _autoload_move_up(self):
        sel = self.auto_tree.selectedItems()
        if not sel: return
        uid = sel[0].data(0, Qt.ItemDataRole.UserRole)
        idx = next((i for i, b in enumerate(self.autoload_blocks) if b["uid"] == uid), None)
        if idx is not None and idx > 0:
            self.autoload_blocks[idx], self.autoload_blocks[idx-1] = self.autoload_blocks[idx-1], self.autoload_blocks[idx]
            self._refresh_autoload_tree()

    def _autoload_move_down(self):
        sel = self.auto_tree.selectedItems()
        if not sel: return
        uid = sel[0].data(0, Qt.ItemDataRole.UserRole)
        idx = next((i for i, b in enumerate(self.autoload_blocks) if b["uid"] == uid), None)
        if idx is not None and idx < len(self.autoload_blocks) - 1:
            self.autoload_blocks[idx], self.autoload_blocks[idx+1] = self.autoload_blocks[idx+1], self.autoload_blocks[idx]
            self._refresh_autoload_tree()

    def _autoload_apply_delay(self):
        sel = self.auto_tree.selectedItems()
        if not sel: return
        uid = sel[0].data(0, Qt.ItemDataRole.UserRole)
        try: delay = int(self.auto_delay_input.text().strip())
        except ValueError: return
        for b in self.autoload_blocks:
            if b["uid"] == uid: b["delay_ms"] = delay; break
        self._refresh_autoload_tree()

    def _autoload_remove_delay(self):
        sel = self.auto_tree.selectedItems()
        if not sel: return
        uid = sel[0].data(0, Qt.ItemDataRole.UserRole)
        for b in self.autoload_blocks:
            if b["uid"] == uid: b["delay_ms"] = None; break
        self._refresh_autoload_tree()

    def _autoload_fetch(self):
        self.play_sound()
        ip, port = self.current_ip, self.current_port
        target_dir = self._get_target_autoload_dir()
        target_file = f"{target_dir}/autoload.txt"
        
        self.auto_prog.set_progress(0)
        self.log(f"[AUTOLOAD] Fetching from {target_file} ...")
        
        def _task(signals, worker):
            ftp = FTP()
            ftp.connect(ip, int(port), timeout=10)
            ftp.login()
            
            try:
                ftp.cwd(target_dir)
            except Exception:
                return ("DIR_NOT_FOUND", target_dir)
                
            workdir = os.path.join(tempfile.gettempdir(), "autoload_editor")
            os.makedirs(workdir, exist_ok=True)
            local_path = os.path.join(workdir, "autoload.txt")
            
            try:
                with open(local_path, "wb") as f: ftp.retrbinary(f"RETR {target_file}", f.write)
                with open(local_path, "r", encoding="utf-8", errors="ignore") as f: text = f.read()
            except Exception:
                text = ""
                
            available = [os.path.basename(n) for n in ftp.nlst() if is_payload_name(n)]
            ftp.quit()
            return ("SUCCESS", text, available, local_path)

        worker = BaseTaskWorker(_task)
        worker.signals.log.connect(self.log)
        worker.signals.finished.connect(self._autoload_on_fetch_finished)
        worker.start()
        self.active_workers.append(worker)

    def _autoload_on_fetch_finished(self, success, msg, res):
        if not success:
            self.auto_prog.set_progress(0)
            CustomMessageBox.show_info(self, "Fetch Failed", msg)
            return
            
        code = res[0]
        if code == "DIR_NOT_FOUND":
            target_dir = res[1]
            if CustomMessageBox.ask_yes_no(self, "Directory Missing", f"The directory '{target_dir}' does not exist on console.\nWould you like to create it now?"):
                self._autoload_create_dir(target_dir)
            self.auto_prog.set_progress(0)
            return
            
        _, text, available, local_path = res
        self.autoload_blocks = merge_autoload_payloads(parse_autoload_text(text), available)
        self.autoload_local_dir = None
        self.autoload_backup_path = local_path + ".bak"
        if os.path.exists(local_path): shutil.copy(local_path, self.autoload_backup_path)
        
        self._refresh_autoload_tree()
        self.auto_prog.set_progress(100)
        self.log(f"[AUTOLOAD] Loaded {len(self.autoload_blocks)} payloads.")

    def _autoload_create_dir(self, target_dir):
        ip, port = self.current_ip, self.current_port
        def _task(signals, worker):
            ftp = FTP()
            ftp.connect(ip, int(port), timeout=10)
            ftp.login()
            ftp.mkd(target_dir)
            ftp.quit()
            return True
            
        worker = BaseTaskWorker(_task)
        worker.signals.log.connect(self.log)
        worker.signals.finished.connect(lambda s, m, r: CustomMessageBox.show_info(self, "Directory Created", f"Created {target_dir}") if s else CustomMessageBox.show_info(self, "Error", m))
        worker.start()

    def _autoload_load_dir(self):
        self.play_sound()
        folder = QFileDialog.getExistingDirectory(self, "Select Payload Folder")
        if not folder: return
        self.autoload_local_dir = folder
        existing = []
        local_al = os.path.join(folder, "autoload.txt")
        if os.path.exists(local_al):
            with open(local_al, "r", encoding="utf-8", errors="ignore") as f:
                existing = parse_autoload_text(f.read())
        payloads = [n for n in os.listdir(folder) if is_payload_name(n)]
        self.autoload_blocks = merge_autoload_payloads(existing, payloads)
        self.autoload_backup_path = os.path.join(folder, "autoload.txt.bak")
        self._refresh_autoload_tree()
        self.log(f"[AUTOLOAD] Local folder scanned: {folder}")

    def _autoload_upload_single(self):
        self.play_sound()
        fp, _ = QFileDialog.getOpenFileName(self, "Select Payload to Upload", "", "Payloads (*.bin *.elf)")
        if not fp: return
        target_dir = self._get_target_autoload_dir()
        ip, port = self.current_ip, self.current_port
        
        self.auto_prog.set_progress(0)
        self.log(f"[AUTOLOAD] Uploading single file: {os.path.basename(fp)} ...")
        
        def _task(signals, worker):
            ftp = FTP()
            ftp.connect(ip, int(port), timeout=10)
            ftp.login()
            try: ftp.cwd(target_dir)
            except: ftp.mkd(target_dir)
            
            rpath = f"{target_dir}/{os.path.basename(fp)}"
            with open(fp, "rb") as f: ftp.storbinary(f"STOR {rpath}", f)
            ftp.quit()
            return True
            
        worker = BaseTaskWorker(_task)
        worker.signals.log.connect(self.log)
        worker.signals.finished.connect(lambda s, m, r: self.auto_prog.set_progress(100 if s else 0))
        worker.start()
        self.active_workers.append(worker)

    def _autoload_save(self):
        self.play_sound()
        ip, port = self.current_ip, self.current_port
        target_dir = self._get_target_autoload_dir()
        target_file = f"{target_dir}/autoload.txt"
        payload_text = build_autoload_text(self.autoload_blocks)
        
        self.auto_prog.set_progress(0)
        
        def _task(signals, worker):
            ftp = FTP()
            ftp.connect(ip, int(port), timeout=10)
            ftp.login()
            try: ftp.cwd(target_dir)
            except: ftp.mkd(target_dir)
            
            tmp = os.path.join(tempfile.gettempdir(), "autoload_out.txt")
            with open(tmp, "w", encoding="utf-8") as f: f.write(payload_text)
            
            with open(tmp, "rb") as f: ftp.storbinary(f"STOR {target_file}", f)
            ftp.quit()
            return True

        worker = BaseTaskWorker(_task)
        worker.signals.log.connect(self.log)
        worker.signals.finished.connect(lambda s, m, r: CustomMessageBox.show_info(self, "Success", "autoload.txt updated.") if s else CustomMessageBox.show_info(self, "Error", m))
        worker.start()
        self.active_workers.append(worker)

    def _autoload_restore_backup(self):
        self.play_sound()
        if not self.autoload_backup_path or not os.path.exists(self.autoload_backup_path):
            CustomMessageBox.show_info(self, "Error", "No backup file found to restore.")
            return
        with open(self.autoload_backup_path, "r", encoding="utf-8", errors="ignore") as f: text = f.read()
        self.autoload_blocks = parse_autoload_text(text)
        self._refresh_autoload_tree()
        self.log("[AUTOLOAD] Restored from backup.")

    #  TAB 3 — UPDATE Y2JB
    def _build_tab_y2jb(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)
        
        lbl = QLabel("📡 Update Y2JB")
        lbl.setObjectName("Heading")
        layout.addWidget(lbl)
        
        tb1 = QHBoxLayout()
        tb1.addWidget(QLabel("Filter:"))
        self.y2jb_filter_input = QLineEdit()
        self.y2jb_filter_input.setFixedWidth(130)
        self.y2jb_filter_input.textChanged.connect(self._refresh_y2jb_tree)
        tb1.addWidget(self.y2jb_filter_input)
        
        btn_sel = QPushButton("Select Files")
        btn_sel.clicked.connect(self._y2jb_select_files)
        btn_load_rem = QPushButton("Load Remote")
        btn_load_rem.clicked.connect(self._y2jb_load_remote)
        
        tb1.addWidget(btn_sel)
        tb1.addWidget(btn_load_rem)
        
        tb1.addWidget(QLabel("Sandbox:"))
        self.y2jb_sb_combo = QComboBox()
        self.y2jb_sb_combo.addItems(SANDBOX_IDX_CHOICES)
        tb1.addWidget(self.y2jb_sb_combo)
        
        btn_all = QPushButton("Select All")
        btn_all.clicked.connect(lambda: self._y2jb_set_all(True))
        btn_none = QPushButton("Deselect All")
        btn_none.clicked.connect(lambda: self._y2jb_set_all(False))
        tb1.addWidget(btn_all)
        tb1.addWidget(btn_none)
        
        btn_up = QPushButton("Upload Selected")
        btn_up.setObjectName("Primary")
        btn_up.clicked.connect(self._y2jb_upload)
        tb1.addWidget(btn_up)
        layout.addLayout(tb1)
        
        # Remote Ops Toolbar (Disabled until Remote Loaded)
        tb2 = QHBoxLayout()
        tb2.addWidget(QLabel("Remote Ops:"))
        
        self.y2jb_btn_rename = QPushButton("Rename")
        self.y2jb_btn_rename.setEnabled(False)
        self.y2jb_btn_rename.clicked.connect(self._y2jb_rename)
        
        self.y2jb_btn_perm = QPushButton("Permissions (777)")
        self.y2jb_btn_perm.setEnabled(False)
        self.y2jb_btn_perm.clicked.connect(self._y2jb_permissions)
        
        self.y2jb_btn_del = QPushButton("Delete Remote")
        self.y2jb_btn_del.setObjectName("Danger")
        self.y2jb_btn_del.setEnabled(False)
        self.y2jb_btn_del.clicked.connect(self._y2jb_delete)
        
        tb2.addWidget(self.y2jb_btn_rename)
        tb2.addWidget(self.y2jb_btn_perm)
        tb2.addWidget(self.y2jb_btn_del)
        tb2.addStretch()
        layout.addLayout(tb2)
        
        self.y2jb_tree = QTreeWidget()
        self.y2jb_tree.setHeaderLabels(["State", "File", "Size"])
        hdr = self.y2jb_tree.header()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        hdr.setStretchLastSection(False)
        hdr.resizeSection(0, 70)
        hdr.resizeSection(2, 100)
        self.y2jb_tree.itemClicked.connect(self._y2jb_on_item_click)
        layout.addWidget(self.y2jb_tree, 1)
        
        self.y2jb_prog = FancyProgressBar()
        layout.addWidget(self.y2jb_prog)

    def _set_y2jb_remote_enabled(self, state):
        self._y2jb_has_remote = state
        self.y2jb_btn_rename.setEnabled(state)
        self.y2jb_btn_perm.setEnabled(state)
        self.y2jb_btn_del.setEnabled(state)

    def _refresh_y2jb_tree(self):
        self.y2jb_tree.clear()
        query = self.y2jb_filter_input.text().strip().lower()
        for item in self.y2jb_items:
            if query and query not in item.get("name", "").lower(): continue
            chk = "✦" if item.get("enabled", True) else "◇"
            t_item = QTreeWidgetItem([chk, item["name"], fmt_bytes(item.get("size", 0))])
            t_item.setData(0, Qt.ItemDataRole.UserRole, item["uid"])
            self.y2jb_tree.addTopLevelItem(t_item)

    def _y2jb_on_item_click(self, item, col):
        if col == 0:
            uid = item.data(0, Qt.ItemDataRole.UserRole)
            for it in self.y2jb_items:
                if it["uid"] == uid:
                    it["enabled"] = not it.get("enabled", True)
                    break
            self._refresh_y2jb_tree()

    def _y2jb_set_all(self, state):
        for it in self.y2jb_items: it["enabled"] = state
        self._refresh_y2jb_tree()

    def _y2jb_select_files(self):
        self.play_sound()
        fps, _ = QFileDialog.getOpenFileNames(self, "Select Files to Upload")
        if not fps: return
        self.y2jb_items = [ensure_uid({"name": os.path.basename(f), "path": f, "size": os.path.getsize(f), "enabled": True, "remote": False}) for f in fps]
        self._set_y2jb_remote_enabled(False)
        self._refresh_y2jb_tree()

    def _y2jb_load_remote(self):
        self.play_sound()
        if not CustomMessageBox.ask_yes_no(self, "Open YouTube", "Please open YouTube on your PS5 first.\nProceed to load remote sandbox files?"):
            return
        title_id = self.get_title_id()
        sb_idx = self.y2jb_sb_combo.currentText()
        remote_dir = REMOTE_SANDBOX_TEMPLATE.format(title_id=title_id, sandbox_idx=sb_idx)
        ip, port = self.current_ip, self.current_port
        
        self.y2jb_prog.set_progress(0)
        self.log(f"[Y2JB] Loading remote files from sandbox {sb_idx} ...")
        
        def _task(signals, worker):
            ftp = FTP()
            ftp.connect(ip, int(port), timeout=10)
            ftp.login()
            ftp.cwd(remote_dir)
            names = ftp.nlst()
            items = []
            for n in names:
                if n in (".", ".."): continue
                try: sz = ftp.size(n) or 0
                except: sz = 0
                items.append(ensure_uid({"name": n, "path": n, "size": sz, "enabled": True, "remote": True}))
            ftp.quit()
            return items

        worker = BaseTaskWorker(_task)
        worker.signals.log.connect(self.log)
        worker.signals.finished.connect(self._y2jb_on_remote_loaded)
        worker.start()
        self.active_workers.append(worker)

    def _y2jb_on_remote_loaded(self, success, msg, res):
        if success:
            self.y2jb_items = res
            self._set_y2jb_remote_enabled(True)
            self._refresh_y2jb_tree()
            self.y2jb_prog.set_progress(100)
            self.log(f"[Y2JB] Loaded {len(res)} remote file(s).")
        else:
            self.y2jb_prog.set_progress(0)
            CustomMessageBox.show_info(self, "Load Error", msg)

    def _y2jb_upload(self):
        self.play_sound()
        selected = [it for it in self.y2jb_items if it.get("enabled") and not it.get("remote") and os.path.exists(it.get("path", ""))]
        if not selected:
            CustomMessageBox.show_info(self, "No Files", "No local files selected to upload.")
            return
            
        title_id = self.get_title_id()
        sb_idx = self.y2jb_sb_combo.currentText()
        remote_dir = REMOTE_SANDBOX_TEMPLATE.format(title_id=title_id, sandbox_idx=sb_idx)
        ip, port = self.current_ip, self.current_port
        
        self.y2jb_prog.set_progress(0)
        
        def _task(signals, worker):
            ftp = FTP()
            ftp.connect(ip, int(port), timeout=10)
            ftp.login()
            try: ftp.cwd(remote_dir)
            except: pass
            total = len(selected)
            for i, item in enumerate(selected, 1):
                rpath = f"{remote_dir}{os.path.basename(item['path'])}"
                signals.log.emit(f"[Y2JB] Uploading {os.path.basename(item['path'])} ...")
                with open(item['path'], "rb") as f: ftp.storbinary(f"STOR {rpath}", f)
                signals.progress.emit(i/total*100, 0, -1, os.path.basename(item['path']))
            ftp.quit()
            return True

        worker = BaseTaskWorker(_task)
        worker.signals.log.connect(self.log)
        worker.signals.progress.connect(lambda v, s, e, l: self.y2jb_prog.set_progress(v, s, e, l))
        worker.signals.finished.connect(lambda s, m, r: CustomMessageBox.show_info(self, "Success", "Y2JB upload complete.") if s else CustomMessageBox.show_info(self, "Error", m))
        worker.start()
        self.active_workers.append(worker)

    def _y2jb_delete(self):
        sel = self.y2jb_tree.selectedItems()
        if not sel: return
        uids = {item.data(0, Qt.ItemDataRole.UserRole) for item in sel}
        targets = [it for it in self.y2jb_items if it["uid"] in uids and it.get("remote")]
        if not targets: return
        
        if not CustomMessageBox.ask_yes_no(self, "Delete Remote Files", f"Delete {len(targets)} remote file(s) from console sandbox?"):
            return
            
        title_id = self.get_title_id()
        sb_idx = self.y2jb_sb_combo.currentText()
        remote_dir = REMOTE_SANDBOX_TEMPLATE.format(title_id=title_id, sandbox_idx=sb_idx)
        ip, port = self.current_ip, self.current_port
        
        def _task(signals, worker):
            ftp = FTP()
            ftp.connect(ip, int(port), timeout=10)
            ftp.login()
            for it in targets:
                try: ftp.delete(f"{remote_dir}{os.path.basename(it['path'])}")
                except Exception as e: signals.log.emit(f"[ERROR] {e}")
            ftp.quit()
            return True

        worker = BaseTaskWorker(_task)
        worker.signals.log.connect(self.log)
        worker.signals.finished.connect(lambda s, m, r: self._y2jb_load_remote())
        worker.start()

    def _y2jb_rename(self):
        sel = self.y2jb_tree.selectedItems()
        if not sel or len(sel) > 1: return
        uid = sel[0].data(0, Qt.ItemDataRole.UserRole)
        target = next((it for it in self.y2jb_items if it["uid"] == uid and it.get("remote")), None)
        if not target: return
        
        old_name = target["name"]
        new_name, ok = QFileDialog.getSaveFileName(self, "Rename Remote File", old_name)
        if not ok or not new_name: return
        new_name = os.path.basename(new_name).strip()
        
        title_id = self.get_title_id()
        sb_idx = self.y2jb_sb_combo.currentText()
        remote_dir = REMOTE_SANDBOX_TEMPLATE.format(title_id=title_id, sandbox_idx=sb_idx)
        ip, port = self.current_ip, self.current_port
        
        def _task(signals, worker):
            ftp = FTP()
            ftp.connect(ip, int(port), timeout=10)
            ftp.login()
            ftp.rename(f"{remote_dir}{old_name}", f"{remote_dir}{new_name}")
            ftp.quit()
            return True

        worker = BaseTaskWorker(_task)
        worker.signals.log.connect(self.log)
        worker.signals.finished.connect(lambda s, m, r: self._y2jb_load_remote())
        worker.start()

    def _y2jb_permissions(self):
        targets = [it for it in self.y2jb_items if it.get("enabled") and it.get("remote")]
        if not targets: return
        
        title_id = self.get_title_id()
        sb_idx = self.y2jb_sb_combo.currentText()
        remote_dir = REMOTE_SANDBOX_TEMPLATE.format(title_id=title_id, sandbox_idx=sb_idx)
        ip, port = self.current_ip, self.current_port
        
        def _task(signals, worker):
            ftp = FTP()
            ftp.connect(ip, int(port), timeout=10)
            ftp.login()
            for it in targets:
                rpath = f"{remote_dir}{os.path.basename(it['path'])}"
                try: ftp.sendcmd(f"SITE CHMOD 777 {rpath}")
                except Exception as e: signals.log.emit(f"[ERROR] chmod failed for {it['name']}: {e}")
            ftp.quit()
            return True

        worker = BaseTaskWorker(_task)
        worker.signals.log.connect(self.log)
        worker.signals.finished.connect(lambda s, m, r: CustomMessageBox.show_info(self, "Success", "Permissions (777) applied.") if s else None)
        worker.start()

    #  TAB 4 — TCP SENDER
    def _build_tab_tcp(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)
        
        lbl = QLabel("🔌 TCP Payload Sender")
        lbl.setObjectName("Heading")
        layout.addWidget(lbl)
        
        tb = QHBoxLayout()
        self.tcp_path_input = QLineEdit()
        self.tcp_path_input.setPlaceholderText("Select file or folder to send...")
        tb.addWidget(self.tcp_path_input, 1)
        
        btn_file = QPushButton("📁 File")
        btn_file.setFixedWidth(75)
        btn_file.clicked.connect(self._tcp_pick_file)
        btn_folder = QPushButton("📂 Folder")
        btn_folder.setFixedWidth(80)
        btn_folder.clicked.connect(self._tcp_pick_folder)
        btn_send = QPushButton("⚡ Send")
        btn_send.setObjectName("Primary")
        btn_send.setFixedWidth(80)
        btn_send.clicked.connect(self._tcp_send_current)
        
        tb.addWidget(btn_file)
        tb.addWidget(btn_folder)
        tb.addWidget(btn_send)
        layout.addLayout(tb)
        
        # History filter
        tb2 = QHBoxLayout()
        tb2.addWidget(QLabel("History Filter:"))
        self.tcp_filter_input = QLineEdit()
        self.tcp_filter_input.setFixedWidth(130)
        self.tcp_filter_input.textChanged.connect(self._load_tcp_history_tree)
        tb2.addWidget(self.tcp_filter_input)
        tb2.addStretch()
        
        btn_send_sel = QPushButton("Send Selected")
        btn_send_sel.setObjectName("Primary")
        btn_send_sel.clicked.connect(self._tcp_send_selected)
        btn_rem = QPushButton("Remove")
        btn_rem.setFixedWidth(70)
        btn_rem.clicked.connect(self._tcp_remove_history)
        btn_clear = QPushButton("Clear All")
        btn_clear.setFixedWidth(75)
        btn_clear.clicked.connect(self._tcp_clear_history)
        
        tb2.addWidget(btn_send_sel)
        tb2.addWidget(btn_rem)
        tb2.addWidget(btn_clear)
        layout.addLayout(tb2)
        
        self.tcp_tree = QTreeWidget()
        self.tcp_tree.setHeaderLabels(["Name", "Type", "Size", "Last Sent"])
        hdr = self.tcp_tree.header()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        hdr.setStretchLastSection(False)
        hdr.resizeSection(1, 80)
        hdr.resizeSection(2, 90)
        hdr.resizeSection(3, 150)
        self.tcp_tree.itemDoubleClicked.connect(lambda item, col: self._tcp_send_selected())
        layout.addWidget(self.tcp_tree, 1)
        
        self.tcp_prog = FancyProgressBar()
        layout.addWidget(self.tcp_prog)

    def _load_tcp_history_tree(self):
        self.tcp_tree.clear()
        query = self.tcp_filter_input.text().strip().lower()
        for item in sorted(self.tcp_history, key=lambda x: float(x.get("last_used", 0) or 0), reverse=True):
            if query and query not in str(item.get("name", "")).lower(): continue
            kind = item.get("kind", "file")
            prefix = "📂 " if kind == "folder" else "📄 "
            
            t_item = QTreeWidgetItem([prefix + item.get("name", ""), kind, fmt_bytes(item.get("size", 0)), ts_fmt(item.get("last_used"))])
            t_item.setData(0, Qt.ItemDataRole.UserRole, item["uid"])
            
            if kind == "folder":
                for child in item.get("children", []) or []:
                    c_item = QTreeWidgetItem(["  📄 " + child.get("name", ""), "file", fmt_bytes(child.get("size", 0)), ts_fmt(child.get("last_used"))])
                    c_item.setData(0, Qt.ItemDataRole.UserRole, child["uid"])
                    t_item.addChild(c_item)
                    
            self.tcp_tree.addTopLevelItem(t_item)

    def _tcp_pick_file(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Select Payload", "", "Payloads (*.bin *.elf *.sprx)")
        if fp:
            self.tcp_path_input.setText(fp)

    def _tcp_pick_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Payload Folder")
        if folder:
            self.tcp_path_input.setText(folder)

    def _tcp_send_current(self):
        path = self.tcp_path_input.text().strip()
        if not path or not os.path.exists(path):
            CustomMessageBox.show_info(self, "Error", "Select an existing file or folder first.")
            return
        if os.path.isfile(path):
            files = [path]
        else:
            files = [e["path"] for e in collect_folder_entries(path)]
        self._tcp_send_files_task(files)

    def _tcp_send_selected(self):
        sel = self.tcp_tree.selectedItems()
        if not sel: return
        files = []
        for item in sel:
            uid = item.data(0, Qt.ItemDataRole.UserRole)
            hist_item = next((h for h in self.tcp_history if h["uid"] == uid), None)
            if hist_item:
                if hist_item.get("kind") == "folder":
                    for c in hist_item.get("children", []):
                        if os.path.exists(c.get("path", "")): files.append(c["path"])
                else:
                    if os.path.exists(hist_item.get("path", "")): files.append(hist_item["path"])
        if files:
            self._tcp_send_files_task(files)

    def _tcp_send_files_task(self, files):
        ip, port = self.current_ip, self.current_port
        if not ip:
            CustomMessageBox.show_info(self, "Error", "Enter console IP first.")
            return
            
        self.tcp_prog.set_progress(0)
        total_size = sum(os.path.getsize(f) for f in files if os.path.exists(f))
        
        def _task(signals, worker):
            sent_bytes = 0
            start_time = time.time()
            with socket.create_connection((ip, int(port)), timeout=10) as sock:
                for fpath in files:
                    signals.log.emit(f"[TCP] Sending {os.path.basename(fpath)} ...")
                    with open(fpath, "rb") as fh:
                        while True:
                            chunk = fh.read(1024*1024)
                            if not chunk: break
                            sock.sendall(chunk)
                            sent_bytes += len(chunk)
                            el = time.time() - start_time
                            spd = sent_bytes / max(0.001, el)
                            eta = (total_size - sent_bytes) / max(1, spd)
                            signals.progress.emit(sent_bytes/max(1, total_size)*100, spd, eta, os.path.basename(fpath))
            return True

        worker = BaseTaskWorker(_task)
        worker.signals.log.connect(self.log)
        worker.signals.progress.connect(lambda v, s, e, l: self.tcp_prog.set_progress(v, s, e, l))
        worker.signals.finished.connect(lambda s, m, r: CustomMessageBox.show_info(self, "Success", f"Sent {len(files)} file(s).") if s else CustomMessageBox.show_info(self, "TCP Error", m))
        worker.start()
        self.active_workers.append(worker)

    def _tcp_remove_history(self):
        sel = self.tcp_tree.selectedItems()
        if not sel: return
        uids = {item.data(0, Qt.ItemDataRole.UserRole) for item in sel}
        self.tcp_history = [h for h in self.tcp_history if h["uid"] not in uids]
        save_tcp_history(self.tcp_history)
        self._load_tcp_history_tree()

    def _tcp_clear_history(self):
        if CustomMessageBox.ask_yes_no(self, "Clear History", "Clear all TCP history items?"):
            self.tcp_history = []
            save_tcp_history(self.tcp_history)
            self._load_tcp_history_tree()

    #  TAB 5 — FTP MANAGER
    def _build_tab_ftp(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)
        
        lbl = QLabel("📁 FTP Manager")
        lbl.setObjectName("Heading")
        layout.addWidget(lbl)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        pc_panel = QWidget()
        pcl = QVBoxLayout(pc_panel)
        pcl.setContentsMargins(0, 0, 4, 0)
        
        pc_top = QHBoxLayout()
        pc_top.addWidget(QLabel("Drive:"))
        self.ftp5_drive_combo = QComboBox()
        self.ftp5_drive_combo.setFixedWidth(70)
        self.ftp5_drive_combo.addItems(get_drives())
        self.ftp5_drive_combo.currentTextChanged.connect(self._ftp5_on_drive_changed)
        pc_top.addWidget(self.ftp5_drive_combo)
        
        self.ftp5_pc_path_input = QLineEdit(self.ftp5_local_folder)
        self.ftp5_pc_path_input.returnPressed.connect(lambda: self._ftp5_navigate_local(self.ftp5_pc_path_input.text()))
        pc_top.addWidget(self.ftp5_pc_path_input, 1)
        
        btn_pc_up = QPushButton("⬆")
        btn_pc_up.setFixedWidth(32)
        btn_pc_up.clicked.connect(self._ftp5_local_up)
        pc_top.addWidget(btn_pc_up)
        pcl.addLayout(pc_top)
        
        # SEARCH FILTER FOR LOCAL FILES
        pc_search = QHBoxLayout()
        pc_search.addWidget(QLabel("Search:"))
        self.ftp5_local_search = QLineEdit()
        self.ftp5_local_search.setPlaceholderText("Filter PC files...")
        self.ftp5_local_search.textChanged.connect(self._ftp5_filter_local_tree)
        pc_search.addWidget(self.ftp5_local_search)
        pcl.addLayout(pc_search)
        
        self.ftp5_local_tree = QTreeWidget()
        self.ftp5_local_tree.setHeaderLabels(["Name", "Last Modified", "Last Accessed", "Type", "Size"])
        self.ftp5_local_tree.setSortingEnabled(True)
        hdr = self.ftp5_local_tree.header()
        for col in range(5):
            hdr.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
        hdr.setStretchLastSection(False)
        hdr.resizeSection(0, 220)
        hdr.resizeSection(1, 130)
        hdr.resizeSection(2, 130)
        hdr.resizeSection(3, 60)
        hdr.resizeSection(4, 70)
        self.ftp5_local_tree.itemDoubleClicked.connect(self._ftp5_local_open)
        pcl.addWidget(self.ftp5_local_tree, 1)
        
        splitter.addWidget(pc_panel)
        
        rem_panel = QWidget()
        rml = QVBoxLayout(rem_panel)
        rml.setContentsMargins(4, 0, 0, 0)
        
        rem_top = QHBoxLayout()
        rem_top.addWidget(QLabel("Remote:"))
        self.ftp5_rem_path_input = QLineEdit("/")
        self.ftp5_rem_path_input.returnPressed.connect(self._ftp5_load_remote)
        rem_top.addWidget(self.ftp5_rem_path_input, 1)
        
        btn_rem_go = QPushButton("Go")
        btn_rem_go.setFixedWidth(45)
        btn_rem_go.clicked.connect(self._ftp5_load_remote)
        btn_rem_up = QPushButton("⬆")
        btn_rem_up.setFixedWidth(32)
        btn_rem_up.clicked.connect(self._ftp5_remote_up)
        btn_mkdir = QPushButton("New Folder")
        btn_mkdir.clicked.connect(self._ftp5_mkdir)
        
        rem_top.addWidget(btn_rem_go)
        rem_top.addWidget(btn_rem_up)
        rem_top.addWidget(btn_mkdir)
        rml.addLayout(rem_top)
        
        self.ftp5_remote_tree = QTreeWidget()
        self.ftp5_remote_tree.setHeaderLabels(["Name", "Type", "Size"])
        hdr = self.ftp5_remote_tree.header()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        hdr.setStretchLastSection(False)
        hdr.resizeSection(0, 280)
        hdr.resizeSection(1, 70)
        hdr.resizeSection(2, 90)
        self.ftp5_remote_tree.itemDoubleClicked.connect(self._ftp5_remote_open)
        rml.addWidget(self.ftp5_remote_tree, 1)
        
        splitter.addWidget(rem_panel)
        layout.addWidget(splitter, 1)
        
        # Action Bar with Cancel Button
        ab = QHBoxLayout()
        btn_upload = QPushButton("Upload →")
        btn_upload.setObjectName("Primary")
        btn_upload.clicked.connect(self._ftp5_upload)
        btn_download = QPushButton("← Download")
        btn_download.clicked.connect(self._ftp5_download)
        btn_delete = QPushButton("Delete")
        btn_delete.setObjectName("Danger")
        btn_delete.clicked.connect(self._ftp5_delete)
        
        self.ftp5_btn_cancel = QPushButton("⛔ Cancel")
        self.ftp5_btn_cancel.setEnabled(False)
        self.ftp5_btn_cancel.clicked.connect(self._ftp5_cancel_transfer)
        
        ab.addWidget(btn_upload)
        ab.addWidget(btn_download)
        ab.addWidget(btn_delete)
        ab.addWidget(self.ftp5_btn_cancel)
        ab.addStretch()
        layout.addLayout(ab)
        
        self.ftp5_prog = FancyProgressBar()
        layout.addWidget(self.ftp5_prog)

    def _ftp5_on_drive_changed(self, drive):
        self._ftp5_navigate_local(drive)

    def _ftp5_local_up(self):
        parent = os.path.dirname(self.ftp5_local_folder.rstrip("\\/"))
        if parent and os.path.exists(parent):
            self._ftp5_navigate_local(parent)

    def _ftp5_navigate_local(self, path):
        if os.path.exists(path) and os.path.isdir(path):
            self.ftp5_local_folder = path
            self.ftp5_pc_path_input.setText(path)
            self._ftp5_refresh_local_tree()

    def _ftp5_refresh_local_tree(self):
        self.ftp5_local_tree.clear()
        folder = self.ftp5_local_folder
        if not os.path.exists(folder): return
        
        try: names = sorted(os.listdir(folder), key=lambda x: (not os.path.isdir(os.path.join(folder, x)), x.lower()))
        except: names = []
        
        for n in names:
            full = os.path.join(folder, n)
            try:
                is_dir = os.path.isdir(full)
                st = os.stat(full)
                mtime = ts_fmt(st.st_mtime)
                atime = ts_fmt(st.st_atime)
                size = fmt_bytes(st.st_size) if not is_dir else ""
                kind = "folder" if is_dir else "file"
                prefix = "📁 " if is_dir else "📄 "
                
                t_item = QTreeWidgetItem([prefix + n, mtime, atime, kind, size])
                t_item.setData(0, Qt.ItemDataRole.UserRole, full)
                self.ftp5_local_tree.addTopLevelItem(t_item)
            except: continue

    def _ftp5_filter_local_tree(self, text):
        query = text.strip().lower()
        for i in range(self.ftp5_local_tree.topLevelItemCount()):
            item = self.ftp5_local_tree.topLevelItem(i)
            name = item.text(0).lower()
            item.setHidden(bool(query and query not in name))

    def _ftp5_local_open(self, item, col):
        full = item.data(0, Qt.ItemDataRole.UserRole)
        if full and os.path.isdir(full):
            self._ftp5_navigate_local(full)

    def _ftp5_remote_up(self):
        curr = self.ftp5_rem_path_input.text().strip() or "/"
        if curr == "/": return
        parent = os.path.dirname(curr.rstrip("/")) or "/"
        self.ftp5_rem_path_input.setText(parent)
        self._ftp5_load_remote()

    def _ftp5_load_remote(self):
        ip, port = self.current_ip, self.current_port
        target_dir = self.ftp5_rem_path_input.text().strip() or "/"
        if not ip: return
        
        def _task(signals, worker):
            ftp = FTP()
            ftp.connect(ip, int(port), timeout=10)
            ftp.login()
            ftp.cwd(target_dir)
            names = ftp.nlst()
            entries = []
            for n in sorted(names):
                if n in (".", ".."): continue
                try:
                    cwd = ftp.pwd()
                    ftp.cwd(n)
                    ftp.cwd(cwd)
                    is_dir = True
                except:
                    is_dir = False
                sz = ""
                if not is_dir:
                    try: sz = fmt_bytes(ftp.size(n) or 0)
                    except: pass
                entries.append((n, is_dir, sz))
            ftp.quit()
            return entries

        worker = BaseTaskWorker(_task)
        worker.signals.log.connect(self.log)
        worker.signals.finished.connect(self._ftp5_on_remote_loaded)
        worker.start()
        self.active_workers.append(worker)

    def _ftp5_on_remote_loaded(self, success, msg, entries):
        self.ftp5_remote_tree.clear()
        if success and entries:
            for name, is_dir, sz in entries:
                prefix = "📁 " if is_dir else "📄 "
                kind = "folder" if is_dir else "file"
                t_item = QTreeWidgetItem([prefix + name, kind, sz])
                t_item.setData(0, Qt.ItemDataRole.UserRole, name)
                self.ftp5_remote_tree.addTopLevelItem(t_item)

    def _ftp5_remote_open(self, item, col):
        name = item.data(0, Qt.ItemDataRole.UserRole)
        kind = item.text(1)
        if kind == "folder":
            curr = self.ftp5_rem_path_input.text().strip().rstrip("/")
            new_path = f"{curr}/{name}"
            self.ftp5_rem_path_input.setText(new_path)
            self._ftp5_load_remote()

    def _ftp5_cancel_transfer(self):
        self.ftp5_cancel_flag = True
        self.log("[FTP] Cancelling ongoing transfer...")

    def _ftp5_upload(self):
        self.play_sound()
        sel = self.ftp5_local_tree.selectedItems()
        if not sel: return
        paths = [item.data(0, Qt.ItemDataRole.UserRole) for item in sel]
        ip, port = self.current_ip, self.current_port
        target_dir = self.ftp5_rem_path_input.text().strip() or "/"
        
        self.ftp5_cancel_flag = False
        self.ftp5_btn_cancel.setEnabled(True)
        self.ftp5_prog.set_progress(0)
        
        def _task(signals, worker):
            ftp = FTP()
            ftp.connect(ip, int(port), timeout=10)
            ftp.login()
            ftp.cwd(target_dir)
            total = len(paths)
            for i, p in enumerate(paths, 1):
                if self.ftp5_cancel_flag: break
                fn = os.path.basename(p)
                rpath = f"{target_dir.rstrip('/')}/{fn}"
                
                try:
                    ftp.size(rpath)
                    choice = CustomMessageBox.ask_conflict(self, fn)
                    if choice == "skip": continue
                    elif choice == "rename": rpath = f"{target_dir.rstrip('/')}/{os.path.splitext(fn)[0]}_copy{os.path.splitext(fn)[1]}"
                except: pass
                
                with open(p, "rb") as f: ftp.storbinary(f"STOR {rpath}", f)
                signals.progress.emit(i/total*100, 0, -1, fn)
            ftp.quit()
            return True

        worker = BaseTaskWorker(_task)
        worker.signals.log.connect(self.log)
        worker.signals.progress.connect(lambda v, s, e, l: self.ftp5_prog.set_progress(v, s, e, l))
        worker.signals.finished.connect(lambda s, m, r: (self.ftp5_btn_cancel.setEnabled(False), self._ftp5_load_remote()))
        worker.start()
        self.active_workers.append(worker)

    def _ftp5_download(self):
        self.play_sound()
        sel = self.ftp5_remote_tree.selectedItems()
        if not sel: return
        names = [item.data(0, Qt.ItemDataRole.UserRole) for item in sel]
        dest = QFileDialog.getExistingDirectory(self, "Download To Folder")
        if not dest: return
        
        ip, port = self.current_ip, self.current_port
        target_dir = self.ftp5_rem_path_input.text().strip() or "/"
        
        self.ftp5_cancel_flag = False
        self.ftp5_btn_cancel.setEnabled(True)
        self.ftp5_prog.set_progress(0)
        
        def _task(signals, worker):
            ftp = FTP()
            ftp.connect(ip, int(port), timeout=10)
            ftp.login()
            ftp.cwd(target_dir)
            total = len(names)
            for i, fn in enumerate(names, 1):
                if self.ftp5_cancel_flag: break
                lpath = os.path.join(dest, fn)
                if os.path.exists(lpath):
                    choice = CustomMessageBox.ask_conflict(self, fn)
                    if choice == "skip": continue
                    elif choice == "rename": lpath = os.path.join(dest, f"{os.path.splitext(fn)[0]}_copy{os.path.splitext(fn)[1]}")
                    
                with open(lpath, "wb") as f: ftp.retrbinary(f"RETR {fn}", f.write)
                signals.progress.emit(i/total*100, 0, -1, fn)
            ftp.quit()
            return True

        worker = BaseTaskWorker(_task)
        worker.signals.log.connect(self.log)
        worker.signals.progress.connect(lambda v, s, e, l: self.ftp5_prog.set_progress(v, s, e, l))
        worker.signals.finished.connect(lambda s, m, r: (self.ftp5_btn_cancel.setEnabled(False), self._ftp5_refresh_local_tree()))
        worker.start()
        self.active_workers.append(worker)

    def _ftp5_delete(self):
        self.play_sound()
        sel = self.ftp5_remote_tree.selectedItems()
        if not sel: return
        names = [item.data(0, Qt.ItemDataRole.UserRole) for item in sel]
        if not CustomMessageBox.ask_yes_no(self, "Delete Remote Files", f"Delete {len(names)} remote item(s)?"):
            return
            
        ip, port = self.current_ip, self.current_port
        target_dir = self.ftp5_rem_path_input.text().strip() or "/"
        
        def _task(signals, worker):
            ftp = FTP()
            ftp.connect(ip, int(port), timeout=10)
            ftp.login()
            ftp.cwd(target_dir)
            for fn in names:
                try: ftp.delete(fn)
                except: pass
            ftp.quit()
            return True

        worker = BaseTaskWorker(_task)
        worker.signals.log.connect(self.log)
        worker.signals.finished.connect(lambda s, m, r: self._ftp5_load_remote())
        worker.start()

    def _ftp5_mkdir(self):
        self.play_sound()
        ip, port = self.current_ip, self.current_port
        target_dir = self.ftp5_rem_path_input.text().strip() or "/"
        folder_name, ok = QFileDialog.getSaveFileName(self, "New Folder Name", "NewFolder")
        if not ok or not folder_name: return
        folder_name = os.path.basename(folder_name)
        
        def _task(signals, worker):
            ftp = FTP()
            ftp.connect(ip, int(port), timeout=10)
            ftp.login()
            ftp.cwd(target_dir)
            ftp.mkd(folder_name)
            ftp.quit()
            return True

        worker = BaseTaskWorker(_task)
        worker.signals.log.connect(self.log)
        worker.signals.finished.connect(lambda s, m, r: self._ftp5_load_remote())
        worker.start()

    #  TAB 6 — FFPFSC CREATOR (COMPACT SLIDERS & MODERN LAYOUT)
    def _build_tab_ffpfsc(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)
        
        lbl = QLabel("💿 FFPFSC Creator")
        lbl.setObjectName("Heading")
        layout.addWidget(lbl)
        
        # Source
        f1 = QHBoxLayout()
        f1.addWidget(QLabel("Source File/Folder:"))
        self.ffpfsc_src_input = QLineEdit()
        f1.addWidget(self.ffpfsc_src_input, 1)
        btn_src = QPushButton("Browse")
        btn_src.setFixedWidth(80)
        btn_src.clicked.connect(self._ffpfsc_browse_src)
        f1.addWidget(btn_src)
        layout.addLayout(f1)
        
        # Dst
        f2 = QHBoxLayout()
        f2.addWidget(QLabel("Output File:"))
        self.ffpfsc_dst_input = QLineEdit()
        f2.addWidget(self.ffpfsc_dst_input, 1)
        btn_dst = QPushButton("Save As")
        btn_dst.setFixedWidth(80)
        btn_dst.clicked.connect(self._ffpfsc_browse_dst)
        f2.addWidget(btn_dst)
        layout.addLayout(f2)
        
        card = QFrame()
        card.setObjectName("Card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 16, 16, 16)
        cl.setSpacing(12)
        
        # Comp level
        hl1 = QHBoxLayout()
        lbl_c = QLabel("Compression Level:")
        lbl_c.setFixedWidth(140)
        hl1.addWidget(lbl_c)
        self.ffpfsc_comp_slider = QSlider(Qt.Orientation.Horizontal)
        self.ffpfsc_comp_slider.setRange(0, 9)
        self.ffpfsc_comp_slider.setValue(9)
        self.lbl_comp_val = QLabel("9")
        self.lbl_comp_val.setFixedWidth(25)
        self.lbl_comp_val.setStyleSheet(f"color: {Theme.ACCENT_RED}; font-weight: bold;")
        self.ffpfsc_comp_slider.valueChanged.connect(lambda v: self.lbl_comp_val.setText(str(v)))
        hl1.addWidget(self.ffpfsc_comp_slider)
        hl1.addWidget(self.lbl_comp_val)
        cl.addLayout(hl1)
        
        # Threshold gain
        hl2 = QHBoxLayout()
        lbl_t = QLabel("Threshold Gain:")
        lbl_t.setFixedWidth(140)
        hl2.addWidget(lbl_t)
        self.ffpfsc_thresh_slider = QSlider(Qt.Orientation.Horizontal)
        self.ffpfsc_thresh_slider.setRange(0, 100)
        self.ffpfsc_thresh_slider.setValue(0)
        self.lbl_thresh_val = QLabel("0")
        self.lbl_thresh_val.setFixedWidth(25)
        self.lbl_thresh_val.setStyleSheet(f"color: {Theme.ACCENT_RED}; font-weight: bold;")
        self.ffpfsc_thresh_slider.valueChanged.connect(lambda v: self.lbl_thresh_val.setText(str(v)))
        hl2.addWidget(self.ffpfsc_thresh_slider)
        hl2.addWidget(self.lbl_thresh_val)
        cl.addLayout(hl2)
        
        # Block size
        hl3 = QHBoxLayout()
        lbl_b = QLabel("Block Size:")
        lbl_b.setFixedWidth(140)
        hl3.addWidget(lbl_b)
        self.ffpfsc_block_combo = QComboBox()
        self.ffpfsc_block_combo.setFixedWidth(100)
        self.ffpfsc_block_combo.addItems(["65536", "32768", "16384"])
        hl3.addWidget(self.ffpfsc_block_combo)
        hl3.addStretch()
        cl.addLayout(hl3)
        
        layout.addWidget(card)
        
        start_wrap = QHBoxLayout()
        start_wrap.addStretch()
        btn_start = QPushButton("▶ Compress Direct to FFPFSC")
        btn_start.setObjectName("Primary")
        btn_start.setFixedSize(260, 38)
        btn_start.clicked.connect(self._ffpfsc_start)
        start_wrap.addWidget(btn_start)
        start_wrap.addStretch()
        layout.addLayout(start_wrap)
        
        self.ffpfsc_prog = FancyProgressBar()
        layout.addWidget(self.ffpfsc_prog)
        layout.addStretch()

    def _ffpfsc_browse_src(self):
        self.play_sound()
        fp, _ = QFileDialog.getOpenFileName(self, "Select Source File", "", "exFAT / FFPKG (*.exfat *.ffpkg *.dat);;All Files (*.*)")
        if fp:
            self.ffpfsc_src_input.setText(fp)
            base, _ = os.path.splitext(fp)
            self.ffpfsc_dst_input.setText(base + ".ffpfsc")

    def _ffpfsc_browse_dst(self):
        self.play_sound()
        fp, _ = QFileDialog.getSaveFileName(self, "Save Output", "", "FFPFSC (*.ffpfsc)")
        if fp: self.ffpfsc_dst_input.setText(fp)

    def _ffpfsc_start(self):
        self.play_sound()
        src = self.ffpfsc_src_input.text().strip()
        dst = self.ffpfsc_dst_input.text().strip()
        if not src or not dst or not os.path.exists(src):
            CustomMessageBox.show_info(self, "Error", "Select valid source and output file paths.")
            return
            
        if os.path.exists(dst):
            # Same 3-way conflict dialog used elsewhere: Overwrite / Rename / Skip
            choice = CustomMessageBox.ask_conflict(self, os.path.basename(dst))
            if choice == "skip":
                return
            elif choice == "rename":
                base, ext = os.path.splitext(dst)
                dst = f"{base}_copy{ext}"
                self.ffpfsc_dst_input.setText(dst)
            else:  # overwrite
                try:
                    os.remove(dst)
                except Exception as e:
                    CustomMessageBox.show_info(self, "Error", f"Could not remove existing file:\n{e}")
                    return
                
        self.ffpfsc_prog.set_progress(0)
        mode = "folder" if os.path.isdir(src) else "file"
        cmd = [
            sys.executable, "-m", "mkpfs", "pack", mode, src, dst,
            "--compress",
            "--compression-level", str(self.ffpfsc_comp_slider.value()),
            "--threshold-gain", str(self.ffpfsc_thresh_slider.value()),
            "--block-size", self.ffpfsc_block_combo.currentText(),
            "--inode-bits", "32"
        ]
        
        def _task(signals, worker):
            # Parse mkpfs stdout exactly like the original exfat_gym.py
            signals.log.emit(f"[FFPFSC] Running mkpfs command ...")
            signals.progress.emit(0, 0, -1, "starting")
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                clean = line.strip()
                if clean:
                    signals.log.emit(f"[FFPFSC] {clean}")
                # Dynamic matching regex tracking fractional block progress outputs
                match_blocks = re.search(r'(\d+)\s*/\s*(\d+)', clean)
                match_pct = re.search(r'(\d+)\s*%', clean)
                if match_blocks:
                    curr, total = int(match_blocks.group(1)), int(match_blocks.group(2))
                    if total > 0:
                        pct = (curr / total) * 100.0
                        signals.progress.emit(pct, 0, -1, f"{curr}/{total}")
                elif match_pct:
                    pct = float(match_pct.group(1))
                    signals.progress.emit(pct, 0, -1, f"{int(pct)}%")
            proc.wait()
            ok = proc.returncode == 0
            signals.progress.emit(100.0 if ok else 0.0, 0, -1, "done" if ok else "failed")
            return ok

        worker = BaseTaskWorker(_task)
        worker.signals.log.connect(self.log)
        worker.signals.progress.connect(lambda v, s, e, l: self.ffpfsc_prog.set_progress(v, s, e, l))
        worker.signals.finished.connect(
            lambda s, m, r: CustomMessageBox.show_info(self, "Done", f"FFPFSC created successfully:\n{dst}")
            if s else CustomMessageBox.show_info(self, "Error", "FFPFSC creation failed.")
        )
        worker.start()
        self.active_workers.append(worker)

    #  TAB 7 — CONSOLE BROWSER / WEB APPS
    def _build_tab_browser(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)
        
        lbl = QLabel("🌐 Console Browser")
        lbl.setObjectName("Heading")
        layout.addWidget(lbl)
        
        tb = QHBoxLayout()
        btn_back = QPushButton("◀")
        btn_back.setFixedWidth(32)
        btn_fwd = QPushButton("▶")
        btn_fwd.setFixedWidth(32)
        btn_ref = QPushButton("⟳")
        btn_ref.setFixedWidth(32)
        
        self.browser_url_input = QLineEdit()
        self.browser_url_input.setPlaceholderText("http://console-ip:port")
        self.browser_url_input.returnPressed.connect(self._browser_navigate)
        
        btn_go = QPushButton("Go")
        btn_go.setObjectName("Primary")
        btn_go.setFixedWidth(45)
        btn_go.clicked.connect(self._browser_navigate)
        btn_auto = QPushButton("Auto-fill")
        btn_auto.setFixedWidth(75)
        btn_auto.clicked.connect(self._browser_autofill)
        
        tb.addWidget(btn_back)
        tb.addWidget(btn_fwd)
        tb.addWidget(btn_ref)
        tb.addWidget(self.browser_url_input, 1)
        tb.addWidget(btn_go)
        tb.addWidget(btn_auto)
        layout.addLayout(tb)
        
        # Bookmarks Bar
        bm_bar = QHBoxLayout()
        bm_bar.addWidget(QLabel("Bookmarks:"))
        for label, port, width in BROWSER_BOOKMARKS:
            btn_bm = QPushButton(label)
            btn_bm.setFixedWidth(width)
            btn_bm.clicked.connect(lambda _, p=port: self._browser_bookmark(p))
            bm_bar.addWidget(btn_bm)
        bm_bar.addStretch()
        layout.addLayout(bm_bar)
        
        if HAS_WEBENGINE:
            self.web = QWebEngineView()
            btn_back.clicked.connect(self.web.back)
            btn_fwd.clicked.connect(self.web.forward)
            btn_ref.clicked.connect(self.web.reload)
            
            html_landing = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                body {{
                    background: linear-gradient(135deg, #111111 0%, #1a050a 50%, #1a1a1a 100%);
                    color: {Theme.TEXT};
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    height: 100vh;
                    margin: 0;
                }}
                h1 {{
                    color: {Theme.ACCENT_RED};
                    font-size: 32px;
                    margin-bottom: 5px;
                    text-shadow: 0 0 10px rgba(255,0,51,0.5);
                }}
                p {{
                    color: {Theme.TEXT_DIM};
                    font-size: 14px;
                    margin-bottom: 30px;
                }}
                .bookmark-grid {{
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 15px;
                    max-width: 600px;
                }}
                .card {{
                    background: #242424;
                    border: 1px solid #333333;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    cursor: pointer;
                    transition: all 0.2s ease-in-out;
                    text-decoration: none;
                    color: #f5f5f5;
                    font-weight: bold;
                }}
                .card:hover {{
                    background: {Theme.ACCENT_RED};
                    border-color: {Theme.ACCENT_ROSE};
                    transform: translateY(-3px);
                    box-shadow: 0 5px 15px rgba(255,0,51,0.4);
                }}
            </style>
            </head>
            <body>
                <h1>NEXUS Web Portal</h1>
                <p>Select a bookmarked service or enter a custom URL above.</p>
                <div class="bookmark-grid">
            """
            for name, port, _ in BROWSER_BOOKMARKS:
                html_landing += f'<div class="card" onclick="alert(\'Use the top bookmarks bar or enter IP: {port}\')">{name}<br><small style="font-weight:normal; opacity:0.8;">Port {port}</small></div>'
            html_landing += "</div></body></html>"
            
            self.web.setHtml(html_landing)
            layout.addWidget(self.web, 1)
        else:
            lbl_no_web = QLabel("PyQt6-WebEngine is missing.\nInstall with: pip install PyQt6-WebEngine")
            lbl_no_web.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_no_web.setStyleSheet(f"color: {Theme.ACCENT_RED}; font-size: 12pt; font-weight: bold;")
            layout.addWidget(lbl_no_web, 1)

    def _browser_autofill(self):
        self.play_sound()
        ip, port = self.current_ip, self.current_port
        if ip: self.browser_url_input.setText(f"http://{ip}:{port}")

    def _browser_bookmark(self, port):
        self.play_sound()
        ip = self.current_ip
        if not ip:
            CustomMessageBox.show_info(self, "Error", "Enter console IP first.")
            return
        url = f"http://{ip}:{port}"
        self.browser_url_input.setText(url)
        self._browser_navigate()

    def _browser_navigate(self):
        url = self.browser_url_input.text().strip()
        if not url: return
        if not url.startswith(("http://", "https://")):
            url = f"http://{url}"
            self.browser_url_input.setText(url)
        if HAS_WEBENGINE and hasattr(self, 'web'):
            self.web.load(QUrl(url))




def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    
    window = NexusApp()
    window.show()
    
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

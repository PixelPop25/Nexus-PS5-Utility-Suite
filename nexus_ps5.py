
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
import hashlib
import queue as pyqueue
import threading
from ftplib import FTP, error_perm

try:
    from PyQt6.QtCore import (
        Qt, QThread, pyqtSignal, QObject, QTimer, QUrl, QPoint,
        QPropertyAnimation, QEasingCurve, QMimeData, QStandardPaths
    )
    from PyQt6.QtGui import (
        QIcon, QFont, QColor, QPainter, QBrush, QPixmap, QLinearGradient,
        QShortcut, QKeySequence
    )
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
        QPushButton, QLineEdit, QComboBox, QStackedWidget, QTextEdit, 
        QTreeWidget, QTreeWidgetItem, QHeaderView, QDialog, QSlider, QFrame, 
        QSizePolicy, QFileDialog, QSplitter, QMessageBox, QScrollArea,
        QMenu, QInputDialog, QAbstractItemView, QSpinBox, QCheckBox, QTabWidget, QTreeView
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
    ("PS5 Upload", 9113, 125),
    ("Direct PKG Installerv2", 12800, 135),
]

PAYLOAD_EXTS     = (".bin", ".elf")
DEFAULT_DELAY_MS = 2000
APP_CONFIG_DIR   = os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "NexusPS5Utility")
SETTINGS_FILE    = os.path.join(APP_CONFIG_DIR, "settings.json")
TCP_HISTORY_FILE = os.path.join(APP_CONFIG_DIR, "tcp_history.json")
FTP5_HISTORY_FILE = os.path.join(APP_CONFIG_DIR, "ftp5_history.json")


class Theme:
    """Active palette tokens. Call Theme.apply_dark() / apply_light() then rebuild QSS."""
    ACCENT_RED  = "#FF0033"
    ACCENT_ROSE = "#CC0028"
    GREEN       = "#12C55E"
    RED_GLOW    = "#FF0033"
    ORANGE      = "#FF5C42"
    WHITE       = "#F5F5F5"
    BLACK       = "#111111"

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
QMainWindow {{
    border: 1px solid #1A1A1A;
}}
QWidget {{
    background-color: {cls.BG_DARK};
    color: {cls.TEXT};
    font-family: "Segoe UI", sans-serif;
    font-size: 9pt;
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
    font-size: 20pt;
    font-weight: bold;
}}
QLabel#Heading {{
    color: {cls.ACCENT_WARM};
    font-size: 14pt;
    font-weight: bold;
}}
QLineEdit, QComboBox {{
    background-color: {cls.BG_INPUT};
    border: 1px solid {cls.SEPARATOR};
    border-radius: 5px;
    padding: 3px 7px;
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
    border-radius: 8px;
    padding: 4px 10px;
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
    padding-left: 12px;
    font-size: 10pt;
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
    height: 25px;
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
    font-size: 8.5pt;
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
QScrollBar:horizontal {{
    background: {cls.BG_SURFACE};
    height: 10px;
    margin: 0px;
}}
QScrollBar::handle:horizontal {{
    background: {cls.BG_CARD};
    border-radius: 5px;
    min-width: 20px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {cls.ACCENT_RED};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
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


def load_settings():
    defaults = {
        "last_ip": "",
        "last_port": "2121",
        "last_tcp_port": "9021",
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
                return data[-20:]
    except Exception:
        pass
    return []

def save_tcp_history(history):
    try:
        os.makedirs(APP_CONFIG_DIR, exist_ok=True)
        with open(TCP_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history[-20:], f, indent=2)
    except Exception:
        pass

def load_ftp5_history():
    try:
        if os.path.exists(FTP5_HISTORY_FILE):
            with open(FTP5_HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data[-20:]
    except Exception:
        pass
    return []

def save_ftp5_history(history):
    try:
        os.makedirs(APP_CONFIG_DIR, exist_ok=True)
        with open(FTP5_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history[-20:], f, indent=2)
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
            return drives or [os.path.expanduser("~")]
        except AttributeError:
            pass
        for letter in string.ascii_uppercase:
            p = f"{letter}:\\"
            if os.path.isdir(p):
                drives.append(p)
    elif sys.platform == "darwin":
        drives.append("/")
        vol = "/Volumes"
        if os.path.isdir(vol):
            try:
                for name in sorted(os.listdir(vol)):
                    full = os.path.join(vol, name)
                    if os.path.isdir(full) and full not in drives:
                        drives.append(full)
            except Exception:
                pass
    else:
        drives.append("/")
        for root in ("/mnt", "/media"):
            if not os.path.isdir(root):
                continue
            try:
                for name in sorted(os.listdir(root)):
                    full = os.path.join(root, name)
                    if os.path.isdir(full) and full not in drives:
                        drives.append(full)
            except Exception:
                pass
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
        self.setFixedSize(18, 18)
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
        r = 5.0
        
        alpha = 0.35 + 0.2 * math.sin(self.phase)
        base_color = QColor(Theme.GREEN if self.connected else Theme.RED_GLOW)
        
        for i in range(3, 0, -1):
            gr = r + i * 1.6
            c = QColor(base_color)
            c.setAlphaF(max(0, min(1, alpha * (1 - i/4))))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(c))
            painter.drawEllipse(QPoint(int(cx), int(cy)), int(gr), int(gr))
            
        painter.setBrush(QBrush(base_color))
        painter.drawEllipse(QPoint(int(cx), int(cy)), int(r), int(r))
        
        hl_color = QColor(255, 255, 255, 120)
        painter.setBrush(QBrush(hl_color))
        painter.drawEllipse(QPoint(int(cx - 1.5), int(cy - 1.5)), 1, 1)


class FancyProgressBar(QWidget):
    """Smooth GPU gradient progress bar with automatic zero reset upon task completion."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(22)
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


_UNIX_LIST_RE = re.compile(
    r"^([bcdlps-])([r-][w-][xsS-]){3}\s+\d+\s+\S+\s+\S+\s+(\d+)\s+"
    r"(\w{3}\s+\d{1,2}\s+(?:\d{1,2}:\d{2}|\d{4}))\s+(.+)$"
)

def parse_ftp_mlsd_line(name, facts):
    """facts is a dict from ftp.mlsd()."""
    typ = (facts.get("type") or "file").lower()
    is_dir = typ in ("dir", "cdir", "pdir")
    try:
        size = int(facts.get("size") or 0)
    except Exception:
        size = 0
    perm = facts.get("unix.mode") or facts.get("perm") or ""
    mtime = ""
    if facts.get("modify"):
        # YYYYMMDDHHMMSS
        try:
            mtime = datetime.datetime.strptime(facts["modify"][:14], "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            mtime = facts.get("modify", "")
    return {"name": name, "is_dir": is_dir, "size": size, "perm": perm, "mtime": mtime}

def parse_ftp_list_line(line):
    line = line.rstrip("\r\n")
    if not line or line.startswith("total "):
        return None
    m = _UNIX_LIST_RE.match(line)
    if not m:
        # bare name fallback
        name = line.strip().split()[-1] if line.strip() else ""
        if name in (".", "..") or not name:
            return None
        return {"name": name, "is_dir": False, "size": 0, "perm": "", "mtime": ""}
    kind, size_s, date_s, name = m.group(1), m.group(3), m.group(4), m.group(5)
    if name in (".", ".."):
        return None
    is_dir = kind == "d" or name.endswith("/")
    name = name.rstrip("/")
    try:
        size = int(size_s)
    except Exception:
        size = 0
    # permission string like -rwxr-xr-x
    perm_match = re.match(r"^([bcdlps-](?:[r-][w-][xsS-]){3})", line)
    perm = perm_match.group(1) if perm_match else ""
    return {"name": name, "is_dir": is_dir, "size": size, "perm": perm, "mtime": date_s.strip()}

def ftp_list_detailed(ftp, path="."):
    """Prefer MLSD; fall back to LIST -l; last resort nlst + size."""
    entries = []
    try:
        for name, facts in ftp.mlsd(path):
            if name in (".", ".."):
                continue
            entries.append(parse_ftp_mlsd_line(name, facts))
        return entries
    except Exception:
        pass
    lines = []
    try:
        ftp.retrlines(f"LIST {path}", lines.append)
        for line in lines:
            parsed = parse_ftp_list_line(line)
            if parsed:
                entries.append(parsed)
        if entries:
            return entries
    except Exception:
        pass
    # nlst fallback
    try:
        cwd = ftp.pwd()
        if path and path not in (".", cwd):
            ftp.cwd(path)
        for n in ftp.nlst():
            if n in (".", ".."):
                continue
            is_dir = False
            try:
                here = ftp.pwd()
                ftp.cwd(n)
                ftp.cwd(here)
                is_dir = True
            except Exception:
                is_dir = False
            sz = 0
            if not is_dir:
                try:
                    sz = ftp.size(n) or 0
                except Exception:
                    pass
            entries.append({"name": n, "is_dir": is_dir, "size": sz, "perm": "", "mtime": ""})
        if path and path not in (".", cwd):
            try:
                ftp.cwd(cwd)
            except Exception:
                pass
    except Exception:
        pass
    return entries

def collect_local_transfer_jobs(paths, remote_base="/"):
    """Expand local files/folders into flat job list for upload."""
    jobs = []
    remote_base = remote_base.rstrip("/") or ""
    for p in paths:
        if not p or not os.path.exists(p):
            continue
        if os.path.isfile(p):
            jobs.append({
                "local": p,
                "remote": f"{remote_base}/{os.path.basename(p)}" if remote_base else f"/{os.path.basename(p)}",
                "size": os.path.getsize(p),
                "is_dir": False,
            })
        elif os.path.isdir(p):
            root_name = os.path.basename(p.rstrip("\\/"))
            for root, dirs, files in os.walk(p):
                rel_dir = os.path.relpath(root, p)
                if rel_dir == ".":
                    remote_dir = f"{remote_base}/{root_name}" if remote_base else f"/{root_name}"
                else:
                    remote_dir = f"{remote_base}/{root_name}/{rel_dir.replace(os.sep, '/')}" if remote_base else f"/{root_name}/{rel_dir.replace(os.sep, '/')}"
                # ensure directory itself is created (empty marker job)
                jobs.append({
                    "local": root,
                    "remote": remote_dir.replace("\\", "/"),
                    "size": 0,
                    "is_dir": True,
                })
                for fn in files:
                    full = os.path.join(root, fn)
                    try:
                        sz = os.path.getsize(full)
                    except Exception:
                        sz = 0
                    jobs.append({
                        "local": full,
                        "remote": f"{remote_dir}/{fn}".replace("\\", "/"),
                        "size": sz,
                        "is_dir": False,
                    })
    return jobs


class DragDropTreeWidget(QTreeWidget):
    """Tree that supports internal selection drag and external path drops."""
    pathsDropped = pyqtSignal(list)          # local filesystem paths dropped onto this tree
    remoteNamesDropped = pyqtSignal(list)    # remote names dragged from remote tree

    def __init__(self, role="local", parent=None):
        super().__init__(parent)
        self.role = role  # "local" or "remote"
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

    def mimeTypes(self):
        return ["text/uri-list", "application/x-nexus-ftp-local", "application/x-nexus-ftp-remote"]

    def mimeData(self, items):
        md = QMimeData()
        if self.role == "local":
            paths = []
            for it in items:
                p = it.data(0, Qt.ItemDataRole.UserRole)
                if p:
                    paths.append(str(p))
            md.setData("application/x-nexus-ftp-local", "\n".join(paths).encode("utf-8"))
            urls = [QUrl.fromLocalFile(p) for p in paths if os.path.exists(p)]
            if urls:
                md.setUrls(urls)
        else:
            names = []
            for it in items:
                n = it.data(0, Qt.ItemDataRole.UserRole)
                if n:
                    names.append(str(n))
            md.setData("application/x-nexus-ftp-remote", "\n".join(names).encode("utf-8"))
        return md

    def dragEnterEvent(self, event):
        md = event.mimeData()
        if md.hasUrls() or md.hasFormat("application/x-nexus-ftp-local") or md.hasFormat("application/x-nexus-ftp-remote"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        self.dragEnterEvent(event)

    def dropEvent(self, event):
        md = event.mimeData()
        if self.role == "remote":
            # accept local paths → upload
            paths = []
            if md.hasFormat("application/x-nexus-ftp-local"):
                raw = bytes(md.data("application/x-nexus-ftp-local")).decode("utf-8", errors="ignore")
                paths = [p for p in raw.splitlines() if p]
            elif md.hasUrls():
                paths = [u.toLocalFile() for u in md.urls() if u.isLocalFile()]
            if paths:
                self.pathsDropped.emit(paths)
                event.acceptProposedAction()
                return
        if self.role == "local":
            # accept remote names → download
            if md.hasFormat("application/x-nexus-ftp-remote"):
                raw = bytes(md.data("application/x-nexus-ftp-remote")).decode("utf-8", errors="ignore")
                names = [n for n in raw.splitlines() if n]
                if names:
                    self.remoteNamesDropped.emit(names)
                    event.acceptProposedAction()
                    return
        event.ignore()


class FolderPickerPopup(QDialog):
    folderSelected = pyqtSignal(str)

    def __init__(self, start_path, parent=None):
        super().__init__(parent, Qt.WindowType.Popup)
        self.setObjectName("Card")
        self.setFixedSize(340, 400)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(1, 1, 1, 1)
        lay.setSpacing(0)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setIndentation(16)
        self.tree.setExpandsOnDoubleClick(False)
        self.tree.itemClicked.connect(self._on_clicked)
        self.tree.itemDoubleClicked.connect(self._on_double_clicked)
        self.tree.itemExpanded.connect(self._on_expanded)
        lay.addWidget(self.tree)

        self._populate()
        if start_path and os.path.isdir(start_path):
            self._select_path(start_path)

    @staticmethod
    def _shortcut_dirs():
        """Cross-platform quick-access folders (Desktop, Downloads, …)."""
        mapping = [
            ("Home", QStandardPaths.StandardLocation.HomeLocation),
            ("Desktop", QStandardPaths.StandardLocation.DesktopLocation),
            ("Documents", QStandardPaths.StandardLocation.DocumentsLocation),
            ("Downloads", QStandardPaths.StandardLocation.DownloadLocation),
            ("Pictures", QStandardPaths.StandardLocation.PicturesLocation),
            ("Music", QStandardPaths.StandardLocation.MusicLocation),
            ("Videos", QStandardPaths.StandardLocation.MoviesLocation),
        ]
        seen = set()
        out = []
        for label, loc in mapping:
            paths = QStandardPaths.standardLocations(loc)
            if not paths:
                continue
            p = paths[0]
            if not p or p in seen or not os.path.isdir(p):
                continue
            seen.add(p)
            out.append((label, p))
        return out

    def _populate(self):
        self.tree.clear()

        hdr = QTreeWidgetItem(["Quick access"])
        hdr.setFlags(hdr.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        self.tree.addTopLevelItem(hdr)
        for label, path in self._shortcut_dirs():
            item = QTreeWidgetItem([f"📁 {label}"])
            item.setData(0, Qt.ItemDataRole.UserRole, path)
            item.setToolTip(0, path)
            if self._has_subdirs(path):
                item.addChild(QTreeWidgetItem([""]))
                item.setExpanded(False)
            hdr.addChild(item)
        hdr.setExpanded(True)

        roots_hdr = QTreeWidgetItem(["This PC" if sys.platform == "win32" else "Volumes"])
        roots_hdr.setFlags(roots_hdr.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        self.tree.addTopLevelItem(roots_hdr)
        for drive in get_drives():
            label = drive.rstrip("\\/") or drive
            if sys.platform == "win32":
                display = f"💿 {label}"
            elif sys.platform == "darwin":
                display = f"💿 {os.path.basename(label) or label}"
            else:
                display = f"🖴 {label}"
            item = QTreeWidgetItem([display])
            item.setData(0, Qt.ItemDataRole.UserRole, drive)
            item.setToolTip(0, drive)
            if self._has_subdirs(drive):
                item.addChild(QTreeWidgetItem([""]))
            roots_hdr.addChild(item)
        roots_hdr.setExpanded(True)

    @staticmethod
    def _has_subdirs(path):
        try:
            with os.scandir(path) as it:
                for e in it:
                    if e.is_dir(follow_symlinks=False):
                        return True
        except Exception:
            pass
        return False

    def _load_children(self, item):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if not path or not os.path.isdir(path):
            return
        item.takeChildren()
        try:
            names = sorted(
                (e.name for e in os.scandir(path) if e.is_dir(follow_symlinks=False)),
                key=str.lower,
            )
        except Exception:
            names = []
        for name in names:
            full = os.path.join(path, name)
            child = QTreeWidgetItem([f"📁 {name}"])
            child.setData(0, Qt.ItemDataRole.UserRole, full)
            child.setToolTip(0, full)
            if self._has_subdirs(full):
                child.addChild(QTreeWidgetItem([""]))
            item.addChild(child)

    def _on_expanded(self, item):
        if item.childCount() == 1 and not item.child(0).data(0, Qt.ItemDataRole.UserRole):
            self._load_children(item)

    def _on_clicked(self, item, _col):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        # Section headers (Quick access / This PC) and folders: toggle expand on single click
        if item.childCount() > 0:
            if path and item.childCount() == 1 and not item.child(0).data(0, Qt.ItemDataRole.UserRole):
                self._load_children(item)
            item.setExpanded(not item.isExpanded())
        if path:
            self.tree.setCurrentItem(item)

    def _on_double_clicked(self, item, _col):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path and os.path.isdir(path):
            self.folderSelected.emit(path)
            self.close()

    def _select_path(self, path):
        target = os.path.normpath(path)
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            for j in range(top.childCount()):
                child = top.child(j)
                p = child.data(0, Qt.ItemDataRole.UserRole)
                if p and os.path.normpath(p) == target:
                    self.tree.setCurrentItem(child)
                    self.tree.scrollToItem(child)
                    return

    def show_below(self, widget):
        pt = widget.mapToGlobal(QPoint(0, widget.height()))
        self.move(pt)
        self.show()


class WorkerSignals(QObject):
    log = pyqtSignal(str)
    progress = pyqtSignal(float, float, float, str) # val, speed, eta, label
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str, object) # success, message, data
    conflict = pyqtSignal(str)  # filename — main thread answers via worker._conflict_result
    item_update = pyqtSignal(str, str)  # job_key, status ("Queued"/"Active"/"Done"/"Failed"/"Skipped")

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


class NexusApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(990, 630)
        self.setMinimumSize(720, 480)
        
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
        self.ftp5_conn = None  # persistent FTP session for tab 5 keep-alive
        self.ftp5_conflict_policy = "ask"  # ask | overwrite | rename | skip

        # Tab-5 feature state
        self.ftp5_history = load_ftp5_history()
        self.ftp5_parallel_count = int(self.settings.get("ftp5_parallel_count", 4))
        self.ftp5_verify_checksum = False
        self.ftp5_paused = False
        self.ftp5_queue_items = []
        self._ftp5_active_workers = []
        self._ftp5_queue_item_map = {}
        
        self.selected_icon_path = None
        self.active_workers = []
        
        self.ftp5_keepalive_timer = QTimer(self)
        self.ftp5_keepalive_timer.setInterval(25000)
        self.ftp5_keepalive_timer.timeout.connect(self._ftp5_keepalive_ping)
        
        self._build_ui()
        self._load_tcp_history_tree()
        self._ftp5_refresh_local_tree()

    def _sound_path(self):
        candidates = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds", "ui_click.wav"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui_click.wav"),
            os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "NexusPS5Utility", "ui_click.wav"),
            os.path.join(os.path.expanduser("~"), ".config", "NexusPS5Utility", "ui_click.wav"),
        ]
        for p in candidates:
            if os.path.isfile(p):
                return p
        return None

    def play_sound(self):
        if self.is_muted:
            return
        path = self._sound_path()
        if path:
            if HAS_SOUND:
                try:
                    winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                    return
                except Exception:
                    pass
            # Linux / macOS: fire-and-forget system players
            for cmd in (
                ["afplay", path],
                ["paplay", path],
                ["aplay", "-q", path],
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
            ):
                try:
                    subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    return
                except Exception:
                    continue
        if HAS_SOUND:
            try:
                winsound.Beep(880, 35)
            except Exception:
                pass

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setMinimumWidth(150)
        sidebar.setMaximumWidth(300)
        sidebar.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        side_inner = QWidget()
        side_layout = QVBoxLayout(side_inner)
        side_layout.setContentsMargins(10, 10, 10, 10)
        side_layout.setSpacing(4)

        lbl_brand = QLabel(APP_NAME)
        lbl_brand.setObjectName("Brand")
        brand_row = QHBoxLayout()
        brand_row.setSpacing(4)
        brand_row.addWidget(lbl_brand, 1)
        self.btn_hide_sidebar = QPushButton("✕")
        self.btn_hide_sidebar.setFixedSize(20, 20)
        self.btn_hide_sidebar.setToolTip("Hide sidebar")
        self.btn_hide_sidebar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_hide_sidebar.setStyleSheet(
            f"QPushButton {{ background: {Theme.BG_CARD}; color: {Theme.TEXT_DIM};"
            f" border: 1px solid {Theme.SEPARATOR}; border-radius: 4px; font-size: 9pt; padding: 0; }}"
            f"QPushButton:hover {{ background: {Theme.ACCENT_RED}; border-color: {Theme.ACCENT_RED}; color: #fff; }}"
        )
        self.btn_hide_sidebar.clicked.connect(self._hide_sidebar)
        brand_row.addWidget(self.btn_hide_sidebar, 0, Qt.AlignmentFlag.AlignTop)
        side_layout.addLayout(brand_row)
        lbl_sub = QLabel(APP_SUBTITLE)
        lbl_sub.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 8pt;")
        side_layout.addWidget(lbl_sub)
        side_layout.addSpacing(2)

        conn_box = QVBoxLayout()
        conn_box.setSpacing(2)

        lbl_ip = QLabel("Console IP")
        lbl_ip.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 8pt;")
        self.ip_entry = QLineEdit(self.current_ip)
        self.ip_entry.setPlaceholderText("192.168.1.X")
        self.ip_entry.setMinimumHeight(24)
        self.ip_entry.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.ip_entry.textChanged.connect(self._autosave_conn)

        lbl_port = QLabel("Port")
        lbl_port.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 8pt;")
        self.port_entry = QLineEdit(self.current_port)
        self.port_entry.setMinimumHeight(24)
        self.port_entry.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.port_entry.textChanged.connect(self._autosave_conn)

        lbl_title = QLabel("Title ID")
        lbl_title.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 8pt;")
        self.title_combo = QComboBox()
        self.title_combo.addItems(DEFAULT_TITLE_IDS)
        self.title_combo.setMinimumHeight(24)

        conn_box.addWidget(lbl_ip)
        conn_box.addWidget(self.ip_entry)
        conn_box.addWidget(lbl_port)
        conn_box.addWidget(self.port_entry)
        conn_box.addWidget(lbl_title)
        conn_box.addWidget(self.title_combo)
        side_layout.addLayout(conn_box)
        side_layout.addSpacing(2)

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
        status_row.setSpacing(4)
        self.glow = GlowIndicator()
        self.conn_label = QLabel("Disconnected")
        self.conn_label.setStyleSheet(f"color: {Theme.RED_GLOW}; font-weight: bold; font-size: 9pt;")
        status_row.addWidget(self.glow)
        status_row.addWidget(self.conn_label)
        status_row.addStretch()

        chrome = f"""
            QLabel {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.SEPARATOR};
                border-radius: 5px;
                font-size: 11pt;
                padding: 0px;
            }}
            QLabel:hover {{
                background-color: {Theme.BG_INPUT};
                border-color: {Theme.TEXT_DIM};
            }}
        """
        self.btn_mute = QLabel("🔇" if self.is_muted else "🔊")
        self.btn_mute.setFixedSize(24, 24)
        self.btn_mute.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_mute.setToolTip("Toggle Sound Effects")
        self.btn_mute.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mute.setStyleSheet(chrome)
        self.btn_mute.mousePressEvent = lambda e: self._toggle_mute()

        self.btn_theme = QLabel("☀" if Theme.mode == "dark" else "☾")
        self.btn_theme.setFixedSize(24, 24)
        self.btn_theme.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_theme.setToolTip("Toggle Light / Dark Theme")
        self.btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme.setStyleSheet(chrome)
        self.btn_theme.mousePressEvent = lambda e: self._toggle_theme()

        status_row.addWidget(self.btn_mute)
        status_row.addWidget(self.btn_theme)
        side_layout.addLayout(status_row)
        side_layout.addSpacing(6)

        self.stack = QStackedWidget()
        self.tab_buttons = []

        tab_defs = [
            ("YouTube Patcher", "🎬", self._build_tab_yt),
            ("Autoload Editor", "📋", self._build_tab_autoload),
            ("Update Y2JB",     "📡", self._build_tab_y2jb),
            ("TCP Sender",      "🔌", self._build_tab_tcp),
            ("FTP Manager",     "📁", self._build_tab_ftp),
            ("FFPFSC Creator",  "💿", self._build_tab_ffpfsc),
            ("Web Apps", "🌐", self._build_tab_browser)
        ]

        for i, (name, icon, builder) in enumerate(tab_defs):
            btn = QPushButton(f"  {icon}   {name}")
            btn.setObjectName("SidebarBtn")
            btn.setCheckable(True)
            btn.setFixedHeight(30)
            btn.clicked.connect(lambda checked, idx=i: self._switch_tab(idx))
            side_layout.addWidget(btn)
            self.tab_buttons.append(btn)

            page = QWidget()
            builder(page)
            self.stack.addWidget(page)

        side_layout.addStretch()

        lbl_quote = QLabel('"In my heart, I am Palestinian"\n- A Wise Man')
        lbl_quote.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 8pt; font-style: italic;")
        lbl_dev = QLabel("Issu. 2026")
        lbl_dev.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 8pt; font-weight: bold;")
        side_layout.addWidget(lbl_quote)
        side_layout.addWidget(lbl_dev)

        side_scroll = QScrollArea()
        side_scroll.setWidgetResizable(True)
        side_scroll.setFrameShape(QFrame.Shape.NoFrame)
        side_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        side_scroll.setWidget(side_inner)
        side_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        side_outer = QVBoxLayout(sidebar)
        side_outer.setContentsMargins(0, 0, 0, 0)
        side_outer.setSpacing(0)
        side_outer.addWidget(side_scroll)
        sidebar.setMinimumWidth(150)
        sidebar.setMaximumWidth(300)

        content_wrap = QWidget()
        cw_layout = QVBoxLayout(content_wrap)
        cw_layout.setContentsMargins(0, 8, 8, 8)
        cw_layout.setSpacing(6)

        # edge of the main panel, vertically centered; only while sidebar hidden.
        self.sidebar_show_btn = QPushButton("◂", content_wrap)
        self.sidebar_show_btn.setFixedSize(22, 64)
        self.sidebar_show_btn.setToolTip("Show sidebar")
        self.sidebar_show_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sidebar_show_btn.setStyleSheet(
            f"QPushButton {{ background: {Theme.BG_MID}; color: {Theme.TEXT};"
            f" border: 1px solid {Theme.SEPARATOR}; border-left: 3px solid {Theme.ACCENT_RED};"
            " border-top-right-radius: 10px; border-bottom-right-radius: 10px;"
            " font-size: 14pt; font-weight: bold; padding: 0; }"
            f"QPushButton:hover {{ background: {Theme.ACCENT_RED}; border-color: {Theme.ACCENT_RED}; color: #fff; }}"
        )
        self.sidebar_show_btn.clicked.connect(self._show_sidebar)
        self.sidebar_show_btn.hide()
        self._content_wrap = content_wrap
        self._cw_layout = cw_layout
        self._content_wrap.installEventFilter(self)
        cw_layout.setContentsMargins(0, 8, 8, 8)

        cw_layout.addWidget(self.stack, 1)

        log_frame = QFrame()
        log_frame.setObjectName("Card")
        log_frame.setFixedHeight(180)
        log_layout = QVBoxLayout(log_frame)
        log_layout.setContentsMargins(8, 6, 8, 6)

        lbl_log = QLabel("⚡ Log")
        lbl_log.setStyleSheet(f"color: {Theme.ACCENT_RED}; font-weight: bold; font-size: 10.5pt;")
        log_layout.addWidget(lbl_log)

        self.log_box = QTextEdit()
        self.log_box.setObjectName("LogBox")
        self.log_box.setReadOnly(True)
        log_layout.addWidget(self.log_box)

        cw_layout.addWidget(log_frame)
        self.log_frame = log_frame

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setHandleWidth(6)
        self.main_splitter.setChildrenCollapsible(False)
        self._apply_splitter_style()
        self.main_splitter.addWidget(sidebar)
        self._sidebar_widget = sidebar
        self.main_splitter.addWidget(content_wrap)
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setSizes([200, 900])
        main_layout.addWidget(self.main_splitter)

        self._switch_tab(0)

        # F11 toggles fullscreen while on the Console Browser tab (tab 7 / index 6)
        self._fullscreen_shortcut = QShortcut(QKeySequence("F11"), self)
        self._fullscreen_shortcut.activated.connect(self._toggle_browser_fullscreen)
        self._apply_window_chrome()

    def _toggle_mute(self):
        self.is_muted = not self.is_muted
        self.btn_mute.setText("🔇" if self.is_muted else "🔊")
        self.settings["is_muted"] = self.is_muted
        save_settings(self.settings)

    def _toggle_theme(self):
        self.play_sound()
        if Theme.mode == "dark":
            Theme.apply_light()
            self.btn_theme.setText("☾")
        else:
            Theme.apply_dark()
            self.btn_theme.setText("☀")
        self.setStyleSheet(Theme.build_qss())
        chrome = f"""
            QLabel {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.SEPARATOR};
                border-radius: 5px;
                font-size: 11pt;
                padding: 0px;
            }}
            QLabel:hover {{
                background-color: {Theme.BG_INPUT};
                border-color: {Theme.TEXT_DIM};
            }}
        """
        self.btn_mute.setStyleSheet(chrome)
        self.btn_theme.setStyleSheet(chrome)
        if hasattr(self, "btn_hide_sidebar"):
            self.btn_hide_sidebar.setStyleSheet(
                f"QPushButton {{ background: {Theme.BG_CARD}; color: {Theme.TEXT_DIM};"
                f" border: 1px solid {Theme.SEPARATOR}; border-radius: 4px; font-size: 9pt; padding: 0; }}"
                f"QPushButton:hover {{ background: {Theme.ACCENT_RED}; border-color: {Theme.ACCENT_RED}; color: #fff; }}"
            )
        self._apply_splitter_style()
        self.settings["theme"] = Theme.mode
        save_settings(self.settings)
        self._apply_window_chrome()

    def _apply_splitter_style(self):
        """Transparent separator; red only while actively being dragged."""
        if not hasattr(self, "main_splitter"):
            return
        self.main_splitter.setStyleSheet(f"""
            QSplitter::handle:horizontal {{
                background: transparent;
                width: 6px;
                margin: 0px;
                border: none;
            }}
            QSplitter::handle:horizontal:pressed {{
                background: {Theme.ACCENT_RED};
            }}
        """)

    def _apply_window_chrome(self):
        """No red window border. Title-bar / caption follows light or dark theme on Windows."""
        self.setStyleSheet(Theme.build_qss())
        if sys.platform == "win32":
            try:
                import ctypes
                hwnd = int(self.winId())
                DWMWA_BORDER_COLOR = 34
                DWMWA_CAPTION_COLOR = 35
                # COLORREF is 0x00BBGGRR
                if Theme.mode == "light":
                    # light caption (~#F1F3F4), neutral border
                    caption = 0x00F4F3F1
                    border = 0x00DADCE0
                else:
                    # dark caption (~#1A1A1A), dark border
                    caption = 0x001A1A1A
                    border = 0x00111111
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, DWMWA_BORDER_COLOR, ctypes.byref(ctypes.c_int(border)), ctypes.sizeof(ctypes.c_int)
                )
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, DWMWA_CAPTION_COLOR, ctypes.byref(ctypes.c_int(caption)), ctypes.sizeof(ctypes.c_int)
                )
            except Exception:
                pass

    def changeEvent(self, event):
        """Subtle opacity animation on maximize / restore (mac-style polish)."""
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

    def _hide_sidebar(self):
        self.play_sound()
        self._sidebar_widget.hide()
        if hasattr(self, "_cw_layout"):
            self._cw_layout.setContentsMargins(28, 8, 8, 8)
        self.sidebar_show_btn.setStyleSheet(
            f"QPushButton {{ background: {Theme.BG_MID}; color: {Theme.TEXT};"
            f" border: 1px solid {Theme.SEPARATOR}; border-left: 3px solid {Theme.ACCENT_RED};"
            " border-top-right-radius: 10px; border-bottom-right-radius: 10px;"
            " font-size: 14pt; font-weight: bold; padding: 0; }"
            f"QPushButton:hover {{ background: {Theme.ACCENT_RED}; border-color: {Theme.ACCENT_RED}; color: #fff; }}"
        )
        self.sidebar_show_btn.show()
        self._reposition_sidebar_show_btn()
        self.sidebar_show_btn.raise_()

    def _show_sidebar(self):
        self.play_sound()
        self._sidebar_widget.show()
        self.sidebar_show_btn.hide()
        if hasattr(self, "_cw_layout"):
            self._cw_layout.setContentsMargins(0, 8, 8, 8)

    def _reposition_sidebar_show_btn(self):
        if not hasattr(self, "sidebar_show_btn") or not hasattr(self, "_content_wrap"):
            return
        if self.sidebar_show_btn.isHidden():
            return
        h = self._content_wrap.height()
        btn = self.sidebar_show_btn
        btn.move(0, max(8, (h - btn.height()) // 2))
        btn.raise_()

    def eventFilter(self, obj, event):
        if obj is getattr(self, "_content_wrap", None) and event.type() == event.Type.Resize:
            self._reposition_sidebar_show_btn()
        return super().eventFilter(obj, event)

    def _toggle_browser_fullscreen(self):
        idx = self.stack.currentIndex() if hasattr(self, "stack") else -1
        if idx != 6:  # Console Browser is the 7th tab
            return
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _switch_tab(self, idx):
        self.play_sound()
        prev_idx = self.stack.currentIndex() if hasattr(self, "stack") else -1
        for i, btn in enumerate(self.tab_buttons):
            btn.setChecked(i == idx)
        self.stack.setCurrentIndex(idx)

        # vertical space for the Queue/History panel instead.
        if hasattr(self, "log_frame"):
            self.log_frame.setVisible(idx != 4)

        if idx == 3:
            if prev_idx != 3:
                ftp_port = self.port_entry.text().strip() or self.settings.get("last_port", "2121")
                if ftp_port != "9021":
                    self.settings["last_port"] = ftp_port
                    save_settings(self.settings)
            tcp_port = self.settings.get("last_tcp_port", "9021")
            self.port_entry.blockSignals(True)
            self.port_entry.setText(tcp_port)
            self.port_entry.blockSignals(False)
            self.current_port = tcp_port
        else:
            if prev_idx == 3:
                tcp_port = self.port_entry.text().strip() or "9021"
                self.settings["last_tcp_port"] = tcp_port
                save_settings(self.settings)
            ftp_port = self.settings.get("last_port", "2121")
            self.port_entry.blockSignals(True)
            self.port_entry.setText(ftp_port)
            self.port_entry.blockSignals(False)
            self.current_port = ftp_port

        if idx == 6 and HAS_WEBENGINE and hasattr(self, "web"):
            try:
                self._browser_show_landing()
            except Exception:
                pass

    def log(self, msg):
        self.log_box.append(msg)

    def _autosave_conn(self):
        self.current_ip = self.ip_entry.text().strip()
        self.current_port = self.port_entry.text().strip()
        self.settings["last_ip"] = self.current_ip
        # Only persist last_port when we are NOT on the TCP tab (index 3)
        if hasattr(self, "stack") and self.stack.currentIndex() == 3:
            self.settings["last_tcp_port"] = self.current_port or "9021"
        else:
            self.settings["last_port"] = self.current_port or "2121"
        save_settings(self.settings)

    def get_title_id(self):
        return self.title_combo.currentText().strip().split()[0]

    def _prune_workers(self):
        self.active_workers = [w for w in self.active_workers if w.isRunning()]
        if hasattr(self, "_ftp5_active_workers"):
            self._ftp5_active_workers = [w for w in self._ftp5_active_workers if w.isRunning()]

    def _is_connected(self):
        if self.ftp is not None:
            return True
        if getattr(self, "ftp5_conn", None) is not None:
            return True
        return False

    def _require_ip(self, need_connected=True):
        """Return (ip, port) or None. By default requires an active Connect session."""
        ip = (self.ip_entry.text().strip() if hasattr(self, "ip_entry") else "") or self.current_ip
        if not ip:
            CustomMessageBox.show_info(self, "Error", "Enter console IP first.")
            return None
        port = (self.port_entry.text().strip() if hasattr(self, "port_entry") else "") or self.current_port or "2121"
        self.current_ip = ip
        self.current_port = port
        if need_connected and not self._is_connected():
            CustomMessageBox.show_info(self, "Not Connected", "Connect to the console first.")
            return None
        return ip, port

    def _track_worker(self, worker):
        self.active_workers.append(worker)
        worker.signals.finished.connect(lambda *a: self._prune_workers())

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
        self._track_worker(worker)

    def _on_connect_finished(self, success, msg, res):
        self.btn_connect.setEnabled(True)
        if success:
            self.glow.set_connected(True)
            self.conn_label.setText("Connected")
            self.conn_label.setStyleSheet(f"color: {Theme.GREEN}; font-weight: bold;")
            self.log("FTP connected.")
            try:
                ip = self.ip_entry.text().strip() or self.current_ip
                port = self.port_entry.text().strip() or self.current_port or "2121"
                self._ftp5_open_session(ip, port)
                if hasattr(self, "ftp5_rem_path_input"):
                    if not self.ftp5_rem_path_input.text().strip():
                        self.ftp5_rem_path_input.setText("/")
                    self._ftp5_load_remote()
            except Exception as e:
                self.log(f"[FTP] Tab session setup: {e}")
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
        if getattr(self, "ftp5_conn", None) is not None:
            try:
                self.ftp5_conn.quit()
            except Exception:
                try:
                    self.ftp5_conn.close()
                except Exception:
                    pass
            self.ftp5_conn = None
        if hasattr(self, "ftp5_keepalive_timer"):
            self.ftp5_keepalive_timer.stop()
        if hasattr(self, "ftp5_remote_tree"):
            self.ftp5_remote_tree.clear()
        self.glow.set_connected(False)
        self.conn_label.setText("Disconnected")
        self.conn_label.setStyleSheet(f"color: {Theme.RED_GLOW}; font-weight: bold;")
        self.log("FTP disconnected.")

    def _build_tab_yt(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        lbl_heading = QLabel("🎬 YouTube Patcher")
        lbl_heading.setObjectName("Heading")
        layout.addWidget(lbl_heading)

        card = QFrame()
        card.setObjectName("YtIconCard")
        self.yt_icon_card = card
        cl = QHBoxLayout(card)
        cl.setContentsMargins(16, 12, 16, 12)
        cl.setSpacing(12)

        _btn_col_w = 120
        # invisible balance so icon stays centered; buttons stay on the right
        cl.addSpacing(_btn_col_w)

        cl.addStretch(1)
        self.icon_lbl = QLabel("No Icon")
        self.icon_lbl.setObjectName("IconPreview")
        self.icon_lbl.setFixedSize(135, 135)
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(self.icon_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        cl.addStretch(1)

        btn_vbox = QVBoxLayout()
        btn_vbox.setSpacing(6)
        btn_vbox.setContentsMargins(0, 0, 0, 0)
        btn_vbox.addStretch()

        btn_retrieve = QPushButton("Retrieve Icon")
        btn_retrieve.setFixedSize(_btn_col_w, 28)
        btn_retrieve.clicked.connect(self._yt_retrieve_icon)

        btn_load = QPushButton("Load from PC")
        btn_load.setFixedSize(_btn_col_w, 28)
        btn_load.clicked.connect(self._yt_load_icon)

        self.btn_up_icon = QPushButton("Upload Icon")
        self.btn_up_icon.setObjectName("Primary")
        self.btn_up_icon.setFixedSize(_btn_col_w, 28)
        self.btn_up_icon.setEnabled(False)
        self.btn_up_icon.clicked.connect(self._yt_upload_icon)

        btn_vbox.addWidget(btn_retrieve)
        btn_vbox.addWidget(btn_load)
        btn_vbox.addWidget(self.btn_up_icon)
        btn_vbox.addStretch()
        cl.addLayout(btn_vbox)
        layout.addWidget(card)

        lbl_desc = QLabel("Patch app.db, appinfo.db, and param.json for the selected Title ID.")
        lbl_desc.setStyleSheet(f"color: {Theme.TEXT_DIM}; margin-top: 2px;")
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_desc)

        self.btn_patch = QPushButton("⚡ Patch YouTube Now")
        self.btn_patch.setObjectName("Primary")
        self.btn_patch.setMinimumHeight(34)
        self.btn_patch.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_patch.clicked.connect(self._yt_do_patch)
        layout.addWidget(self.btn_patch)

        self.yt_prog = FancyProgressBar()
        layout.addWidget(self.yt_prog)
        layout.addStretch(1)

    def _yt_retrieve_icon(self):
        self.play_sound()
        conn = self._require_ip(need_connected=True)
        if not conn:
            return
        ip, port = conn
        title_id = self.get_title_id()
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
        self._track_worker(worker)

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
        conn = self._require_ip(need_connected=True)
        if not conn:
            return
        ip, port = conn
        title_id = self.get_title_id()
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
        self._track_worker(worker)

    def _yt_do_patch(self):
        self.play_sound()
        conn = self._require_ip()
        if not conn:
            return
        ip, port = conn
        title_id = self.get_title_id()
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
            local_appdb = os.path.join(workdir, "app.db")
            local_param = os.path.join(workdir, "param.json")

            signals.log.emit(f"[PATCH] Downloading appinfo.db ...")
            with open(local_appinfo, "wb") as f:
                ftp.retrbinary(f"RETR {REMOTE_YT_APPINFO_DB}", f.write)
            signals.progress.emit(20, 0, -1, "appinfo.db")

            signals.log.emit(f"[PATCH] Downloading app.db ...")
            with open(local_appdb, "wb") as f:
                ftp.retrbinary(f"RETR {REMOTE_YT_APP_DB}", f.write)
            signals.progress.emit(40, 0, -1, "app.db")

            param_remote = REMOTE_PARAM_SYS_TEMPLATE.format(title_id=title_id)
            try:
                signals.log.emit(f"[PATCH] Downloading param.json (system) ...")
                with open(local_param, "wb") as f:
                    ftp.retrbinary(f"RETR {param_remote}", f.write)
            except Exception:
                param_remote = REMOTE_PARAM_USER_TEMPLATE.format(title_id=title_id)
                signals.log.emit(f"[PATCH] Downloading param.json (user) ...")
                with open(local_param, "wb") as f:
                    ftp.retrbinary(f"RETR {param_remote}", f.write)
            signals.progress.emit(55, 0, -1, "param.json")

            signals.log.emit(f"[PATCH] Updating appinfo.db for {title_id} ...")
            conn = sqlite3.connect(local_appinfo)
            cur = conn.cursor()
            cur.execute(
                "SELECT key, val FROM tbl_appinfo WHERE titleId = ? AND key IN ('CONTENT_VERSION', 'VERSION_FILE_URI')",
                (title_id,),
            )
            before = dict(cur.fetchall())
            signals.log.emit(f"[PATCH] appinfo.db keys found: {list(before.keys()) or '(none)'}")
            for k, v in before.items():
                signals.log.emit(f"[PATCH]   before {k}: {v}")

            cur.execute(
                "UPDATE tbl_appinfo SET val = ? WHERE titleId = ? AND key = 'CONTENT_VERSION'",
                (DEFAULT_VERSION, title_id),
            )
            cur.execute(
                "UPDATE tbl_appinfo SET val = ? WHERE titleId = ? AND key = 'VERSION_FILE_URI'",
                (DEFAULT_VERSION_FILE_URI, title_id),
            )
            conn.commit()

            cur.execute(
                "SELECT key, val FROM tbl_appinfo WHERE titleId = ? AND key IN ('CONTENT_VERSION', 'VERSION_FILE_URI')",
                (title_id,),
            )
            after = dict(cur.fetchall())
            for k, v in after.items():
                signals.log.emit(f"[PATCH]   after  {k}: {v}")
            conn.close()
            signals.progress.emit(70, 0, -1, "appinfo.db")

            signals.log.emit(f"[PATCH] Updating app.db AppInfoJson ...")
            conn = sqlite3.connect(local_appdb)
            cur = conn.cursor()
            cur.execute(
                "UPDATE tbl_contentinfo SET AppInfoJson = json_set(AppInfoJson, '$.CONTENT_VERSION', ?, '$.VERSION_FILE_URI', ?) WHERE titleId = ?",
                (DEFAULT_VERSION, DEFAULT_VERSION_FILE_URI, title_id),
            )
            conn.commit()
            cur.execute("SELECT AppInfoJson FROM tbl_contentinfo WHERE titleId = ?", (title_id,))
            row = cur.fetchone()
            if row and row[0]:
                try:
                    j = json.loads(row[0])
                    signals.log.emit(f"[PATCH]   app.db CONTENT_VERSION: {j.get('CONTENT_VERSION')}")
                    signals.log.emit(f"[PATCH]   app.db VERSION_FILE_URI: {j.get('VERSION_FILE_URI')}")
                except json.JSONDecodeError:
                    signals.log.emit("[PATCH]   app.db AppInfoJson: (could not parse)")
            conn.close()
            signals.progress.emit(82, 0, -1, "app.db")

            signals.log.emit(f"[PATCH] Updating param.json ...")
            with open(local_param, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k in list(data.keys()):
                if k in ("targetContentVersion", "contentVersion"):
                    data[k] = DEFAULT_VERSION
                    signals.log.emit(f"[PATCH]   param.json {k} -> {DEFAULT_VERSION}")
                elif k == "versionFileUri":
                    data[k] = DEFAULT_VERSION_FILE_URI
                    signals.log.emit(f"[PATCH]   param.json {k} -> {DEFAULT_VERSION_FILE_URI}")
            with open(local_param, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            signals.progress.emit(90, 0, -1, "param.json")

            signals.log.emit("[PATCH] Uploading modified files ...")
            with open(local_appinfo, "rb") as f:
                ftp.storbinary(f"STOR {REMOTE_YT_APPINFO_DB}", f)
            with open(local_appdb, "rb") as f:
                ftp.storbinary(f"STOR {REMOTE_YT_APP_DB}", f)
            with open(local_param, "rb") as f:
                ftp.storbinary(f"STOR {param_remote}", f)

            ftp.quit()
            signals.log.emit("[PATCH] All modifications completed successfully.")
            return True

        worker = BaseTaskWorker(_task)
        worker.signals.log.connect(self.log)
        worker.signals.progress.connect(lambda v, s, e, l: self.yt_prog.set_progress(v, s, e, l))
        worker.signals.finished.connect(self._yt_on_patch_finished)
        worker.start()
        self._track_worker(worker)

    def _yt_on_patch_finished(self, success, msg, res):
        self.btn_patch.setEnabled(True)
        if success:
            self.yt_prog.set_progress(100)
            self.log("[PATCH] YouTube patch complete!")
            CustomMessageBox.show_info(self, "Success", "YouTube patch complete.")
        else:
            self.yt_prog.set_progress(0)
            CustomMessageBox.show_info(self, "Patch Failed", msg)

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
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        hdr.setStretchLastSection(True)
        hdr.resizeSection(0, 70)
        hdr.resizeSection(2, 100)
        self.auto_tree.itemClicked.connect(self._autoload_on_item_click)
        self.auto_tree.itemDoubleClicked.connect(self._autoload_on_item_double_click)
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

    def _autoload_on_item_double_click(self, item, col):
        """Double-click anywhere on a row toggles enabled/disabled."""
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
        conn = self._require_ip(need_connected=True)
        if not conn:
            return
        ip, port = conn
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
        self._track_worker(worker)

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
        conn = self._require_ip(need_connected=True)
        if not conn:
            return
        ip, port = conn
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
        conn = self._require_ip(need_connected=True)
        if not conn:
            return
        ip, port = conn
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
        self._track_worker(worker)

    def _autoload_save(self):
        self.play_sound()
        conn = self._require_ip(need_connected=True)
        if not conn:
            return
        ip, port = conn
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
        self._track_worker(worker)

    def _autoload_restore_backup(self):
        self.play_sound()
        if not self.autoload_backup_path or not os.path.exists(self.autoload_backup_path):
            CustomMessageBox.show_info(self, "Error", "No backup file found to restore.")
            return
        with open(self.autoload_backup_path, "r", encoding="utf-8", errors="ignore") as f: text = f.read()
        self.autoload_blocks = parse_autoload_text(text)
        self._refresh_autoload_tree()
        self.log("[AUTOLOAD] Restored from backup.")

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
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        hdr.setStretchLastSection(True)
        hdr.resizeSection(0, 70)
        hdr.resizeSection(2, 100)
        self.y2jb_tree.itemClicked.connect(self._y2jb_on_item_click)
        self.y2jb_tree.itemDoubleClicked.connect(self._y2jb_on_item_double_click)
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

    def _y2jb_on_item_double_click(self, item, col):
        """Double-click anywhere on a row toggles enabled/disabled."""
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
        conn = self._require_ip(need_connected=True)
        if not conn:
            return
        ip, port = conn
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
        self._track_worker(worker)

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
        conn = self._require_ip(need_connected=True)
        if not conn:
            return
        ip, port = conn
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
        self._track_worker(worker)

    def _y2jb_delete(self):
        conn = self._require_ip(need_connected=True)
        if not conn:
            return
        ip, port = conn
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
        conn = self._require_ip(need_connected=True)
        if not conn:
            return
        ip, port = conn
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
        conn = self._require_ip(need_connected=True)
        if not conn:
            return
        ip, port = conn
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
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        hdr.setStretchLastSection(True)
        hdr.resizeSection(0, 220)
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
        conn = self._require_ip(need_connected=False)
        if not conn:
            return
        ip, port = conn
            
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
        worker.signals.finished.connect(
            lambda s, m, r: CustomMessageBox.show_info(self, "Success", f"Sent {len(files)} file(s).")
            if s else CustomMessageBox.show_info(self, "TCP Error", m)
        )
        worker.start()
        self._track_worker(worker)

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

    def _build_tab_ftp(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)

        lbl = QLabel("📁 FTP Manager")
        lbl.setObjectName("Heading")
        layout.addWidget(lbl)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        pc_panel = QWidget()
        pcl = QVBoxLayout(pc_panel)
        pcl.setContentsMargins(0, 0, 2, 0)
        pcl.setSpacing(4)

        pc_title = QLabel("💻 PC Files")
        pc_title.setStyleSheet(f"color: {Theme.ACCENT_RED}; font-weight: bold; font-size: 11pt;")
        pcl.addWidget(pc_title)

        pc_top = QHBoxLayout()
        pc_top.setSpacing(6)
        pc_top.addWidget(QLabel("Folder:"))

        self.ftp5_pc_path_btn = QPushButton(self.ftp5_local_folder)
        self.ftp5_pc_path_btn.setToolTip("Click to browse the full PC folder structure")
        self.ftp5_pc_path_btn.setStyleSheet("text-align:left; padding-left:8px;")
        self.ftp5_pc_path_btn.clicked.connect(self._ftp5_open_folder_picker)
        pc_top.addWidget(self.ftp5_pc_path_btn, 1)

        btn_pc_up = QPushButton("↑")
        btn_pc_up.setFixedWidth(32)
        btn_pc_up.setToolTip("Parent folder")
        btn_pc_up.setStyleSheet("background:#2D6CDF; border-color:#2D6CDF; color:#fff;")
        btn_pc_up.clicked.connect(self._ftp5_local_up)
        pc_top.addWidget(btn_pc_up)
        pcl.addLayout(pc_top)

        pc_search = QHBoxLayout()
        pc_search.setSpacing(6)
        pc_search.addWidget(QLabel("Local filter:"))
        self.ftp5_local_search = QLineEdit()
        self.ftp5_local_search.setPlaceholderText("Filter PC files...")
        self.ftp5_local_search.textChanged.connect(self._ftp5_filter_local_tree)
        pc_search.addWidget(self.ftp5_local_search)
        lbl_sort_hint = QLabel("Click headers to sort")
        lbl_sort_hint.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 9pt;")
        pc_search.addWidget(lbl_sort_hint)
        pc_search.addStretch()
        pcl.addLayout(pc_search)

        self.ftp5_local_tree = DragDropTreeWidget(role="local")
        self.ftp5_local_tree.setHeaderLabels(["Name", "Size", "Type", "Date Modified"])
        self.ftp5_local_tree.setSortingEnabled(True)
        self.ftp5_local_tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.ftp5_local_tree.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.ftp5_local_tree.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.ftp5_local_tree.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.ftp5_local_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ftp5_local_tree.customContextMenuRequested.connect(self._ftp5_local_context_menu)
        self.ftp5_local_tree.pathsDropped.connect(lambda paths: None)
        self.ftp5_local_tree.remoteNamesDropped.connect(self._ftp5_drop_download)
        hdr = self.ftp5_local_tree.header()
        for col in range(4):
            hdr.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
        hdr.setStretchLastSection(True)
        hdr.resizeSection(0, 220)
        hdr.resizeSection(1, 70)
        hdr.resizeSection(2, 60)
        hdr.resizeSection(3, 140)
        self.ftp5_local_tree.itemDoubleClicked.connect(self._ftp5_local_open)
        pcl.addWidget(self.ftp5_local_tree, 1)

        splitter.addWidget(pc_panel)

        rem_panel = QWidget()
        rml = QVBoxLayout(rem_panel)
        rml.setContentsMargins(2, 0, 0, 0)
        rml.setSpacing(4)

        rem_title = QLabel("🎮 Console Files")
        rem_title.setStyleSheet(f"color: {Theme.ACCENT_RED}; font-weight: bold; font-size: 11pt;")
        rml.addWidget(rem_title)

        rem_top = QHBoxLayout()
        rem_top.setSpacing(6)
        rem_top.addWidget(QLabel("Remote:"))
        self.ftp5_rem_path_input = QLineEdit("/")
        self.ftp5_rem_path_input.setPlaceholderText("Remote path")
        self.ftp5_rem_path_input.returnPressed.connect(self._ftp5_load_remote)
        rem_top.addWidget(self.ftp5_rem_path_input, 1)

        btn_rem_go = QPushButton("Go")
        btn_rem_go.setFixedWidth(40)
        btn_rem_go.setToolTip("Navigate to the typed remote path")
        btn_rem_go.clicked.connect(self._ftp5_load_remote)
        rem_top.addWidget(btn_rem_go)

        btn_rem_up = QPushButton("↑")
        btn_rem_up.setFixedWidth(32)
        btn_rem_up.setToolTip("Parent folder")
        btn_rem_up.setStyleSheet("background:#2D6CDF; border-color:#2D6CDF; color:#fff;")
        btn_rem_up.clicked.connect(self._ftp5_remote_up)
        rem_top.addWidget(btn_rem_up)

        btn_mkdir = QPushButton("New Folder")
        btn_mkdir.setFixedWidth(90)
        btn_mkdir.clicked.connect(self._ftp5_mkdir)
        rem_top.addWidget(btn_mkdir)

        btn_rem_refresh = QPushButton("Refresh")
        btn_rem_refresh.setFixedWidth(70)
        btn_rem_refresh.setToolTip("Reload current remote directory (uses sidebar connection)")
        btn_rem_refresh.clicked.connect(self._ftp5_load_remote)
        rem_top.addWidget(btn_rem_refresh)
        rml.addLayout(rem_top)

        rem_search = QHBoxLayout()
        rem_search.setSpacing(6)
        rem_search.addWidget(QLabel("Search:"))
        self.ftp5_remote_search = QLineEdit()
        self.ftp5_remote_search.setPlaceholderText("Filter remote files...")
        self.ftp5_remote_search.textChanged.connect(self._ftp5_filter_remote_tree)
        rem_search.addWidget(self.ftp5_remote_search)
        rml.addLayout(rem_search)

        self.ftp5_remote_tree = DragDropTreeWidget(role="remote")
        self.ftp5_remote_tree.setHeaderLabels(["Name", "Size", "Type"])
        self.ftp5_remote_tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.ftp5_remote_tree.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.ftp5_remote_tree.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.ftp5_remote_tree.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.ftp5_remote_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ftp5_remote_tree.customContextMenuRequested.connect(self._ftp5_remote_context_menu)
        self.ftp5_remote_tree.pathsDropped.connect(self._ftp5_drop_upload)
        self.ftp5_remote_tree.remoteNamesDropped.connect(lambda n: None)
        hdr = self.ftp5_remote_tree.header()
        for col in range(3):
            hdr.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
        hdr.setStretchLastSection(True)
        hdr.resizeSection(0, 300)
        hdr.resizeSection(1, 90)
        hdr.resizeSection(2, 70)
        self.ftp5_remote_tree.itemDoubleClicked.connect(self._ftp5_remote_open)
        rml.addWidget(self.ftp5_remote_tree, 1)

        splitter.addWidget(rem_panel)
        splitter.setHandleWidth(5)
        splitter.setChildrenCollapsible(False)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([1, 1])  # equal share; Qt stretches to fill
        splitter.setStyleSheet(f"""
            QSplitter::handle:horizontal {{
                background: transparent;
                width: 5px;
                margin: 0px;
                border: none;
            }}
            QSplitter::handle:horizontal:hover {{
                background: {Theme.SEPARATOR};
            }}
            QSplitter::handle:horizontal:pressed {{
                background: {Theme.ACCENT_RED};
            }}
        """)

        bottom_widget = QWidget()
        blayout = QVBoxLayout(bottom_widget)
        blayout.setContentsMargins(0, 0, 0, 0)

        ab = QHBoxLayout()
        ab.setSpacing(8)
        ab.addWidget(QLabel("Conflict:"))
        self.ftp5_conflict_combo = QComboBox()
        self.ftp5_conflict_combo.addItems(["Ask each", "Overwrite all", "Rename all", "Skip existing"])
        self.ftp5_conflict_combo.setCurrentIndex(0)
        self.ftp5_conflict_combo.setMinimumWidth(120)
        self.ftp5_conflict_combo.setToolTip("How to handle files that already exist at the destination")
        ab.addWidget(self.ftp5_conflict_combo)

        ab.addWidget(QLabel("Parallel:"))
        self.ftp5_parallel_spin = QSpinBox()
        self.ftp5_parallel_spin.setRange(1, 8)
        self.ftp5_parallel_spin.setValue(self.ftp5_parallel_count)
        self.ftp5_parallel_spin.setFixedWidth(52)
        self.ftp5_parallel_spin.setToolTip("Concurrent FTP connections for multi-file transfers")
        self.ftp5_parallel_spin.valueChanged.connect(self._ftp5_on_parallel_changed)
        ab.addWidget(self.ftp5_parallel_spin)

        ab.addStretch()

        btn_upload = QPushButton("Upload →")
        btn_upload.setObjectName("Primary")
        btn_upload.clicked.connect(self._ftp5_upload)
        btn_download = QPushButton("← Download")
        btn_download.clicked.connect(self._ftp5_download)
        btn_delete = QPushButton("Delete")
        btn_delete.clicked.connect(self._ftp5_delete)
        self.ftp5_btn_cancel = QPushButton("⛔ Cancel")
        self.ftp5_btn_cancel.setEnabled(False)
        self.ftp5_btn_cancel.clicked.connect(self._ftp5_cancel_transfer)
        self.ftp5_btn_pause = QPushButton("⏸ Pause")
        self.ftp5_btn_pause.setEnabled(False)
        self.ftp5_btn_pause.clicked.connect(self._ftp5_toggle_pause)

        ab.addWidget(btn_upload)
        ab.addWidget(btn_download)
        ab.addWidget(btn_delete)
        ab.addWidget(self.ftp5_btn_pause)
        ab.addWidget(self.ftp5_btn_cancel)
        blayout.addLayout(ab)

        self.ftp5_prog = FancyProgressBar()
        blayout.addWidget(self.ftp5_prog)

        self.ftp5_status = QLabel("FTP5 idle.")
        self.ftp5_status.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 9pt;")
        blayout.addWidget(self.ftp5_status)

        self.ftp5_subtabs = QTabWidget()
        self.ftp5_subtabs.setMinimumHeight(90)
        self.ftp5_subtabs.setMaximumHeight(180)

        queue_page = QWidget()
        ql = QVBoxLayout(queue_page)
        ql.setContentsMargins(4, 4, 4, 4)
        self.ftp5_queue_tree = QTreeWidget()
        self.ftp5_queue_tree.setHeaderLabels(["File", "Direction", "Status", "Progress"])
        self.ftp5_queue_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ftp5_queue_tree.customContextMenuRequested.connect(self._ftp5_queue_context_menu)
        qhdr = self.ftp5_queue_tree.header()
        for col in range(4):
            qhdr.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
        qhdr.setStretchLastSection(True)
        qhdr.resizeSection(0, 260)
        qhdr.resizeSection(1, 80)
        qhdr.resizeSection(2, 90)
        ql.addWidget(self.ftp5_queue_tree)
        self.ftp5_subtabs.addTab(queue_page, "Queue")

        hist_page = QWidget()
        hl = QVBoxLayout(hist_page)
        hl.setContentsMargins(4, 4, 4, 4)
        hist_top = QHBoxLayout()
        hist_top.addWidget(QLabel("Transfer History"))
        hist_top.addStretch()
        btn_retry = QPushButton("Retry Selected")
        btn_retry.setObjectName("Primary")
        btn_retry.setToolTip("Retries only the Failed rows currently selected below")
        btn_retry.clicked.connect(self._ftp5_retry_failed)
        hist_top.addWidget(btn_retry)
        btn_rem_hist = QPushButton("Remove")
        btn_rem_hist.setToolTip("Remove selected history rows")
        btn_rem_hist.clicked.connect(self._ftp5_remove_history_rows)
        hist_top.addWidget(btn_rem_hist)
        btn_clear_hist = QPushButton("Clear")
        btn_clear_hist.clicked.connect(self._ftp5_clear_history)
        hist_top.addWidget(btn_clear_hist)
        hl.addLayout(hist_top)
        self.ftp5_history_tree = QTreeWidget()
        self.ftp5_history_tree.setHeaderLabels(["Time", "Direction", "File", "Status", "Size"])
        self.ftp5_history_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        hhdr = self.ftp5_history_tree.header()
        for col in range(5):
            hhdr.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
        hhdr.setStretchLastSection(True)
        hhdr.resizeSection(0, 130)
        hhdr.resizeSection(1, 70)
        hhdr.resizeSection(2, 220)
        hhdr.resizeSection(3, 80)
        hl.addWidget(self.ftp5_history_tree)
        self.ftp5_subtabs.addTab(hist_page, "History")

        blayout.addWidget(self.ftp5_subtabs)

        # Vertical "slider" splitter between the trees and everything below —
        # transparent, themed, only shows red while actively being dragged.
        v_splitter = QSplitter(Qt.Orientation.Vertical)
        v_splitter.setHandleWidth(5)
        v_splitter.setChildrenCollapsible(False)
        v_splitter.setStyleSheet(f"""
            QSplitter::handle:vertical {{
                background: transparent;
                height: 5px;
                margin: 0px;
                border: none;
            }}
            QSplitter::handle:vertical:hover {{
                background: {Theme.SEPARATOR};
            }}
            QSplitter::handle:vertical:pressed {{
                background: {Theme.ACCENT_RED};
            }}
        """)
        v_splitter.addWidget(splitter)
        v_splitter.addWidget(bottom_widget)
        v_splitter.setStretchFactor(0, 1)
        v_splitter.setStretchFactor(1, 0)
        v_splitter.setSizes([520, 160])
        layout.addWidget(v_splitter, 1)

        self._ftp5_reload_history_tree()

    def _ftp5_conflict_mode(self):
        idx = self.ftp5_conflict_combo.currentIndex() if hasattr(self, "ftp5_conflict_combo") else 0
        return ["ask", "overwrite", "rename", "skip"][idx]

    def _ftp5_open_folder_picker(self):
        popup = FolderPickerPopup(self.ftp5_local_folder, self)
        popup.folderSelected.connect(self._ftp5_navigate_local)
        popup.show_below(self.ftp5_pc_path_btn)





    def _ftp5_local_up(self):
        parent = os.path.dirname(self.ftp5_local_folder.rstrip("\\/"))
        if parent and os.path.exists(parent):
            self._ftp5_navigate_local(parent)

    def _ftp5_navigate_local(self, path):
        if os.path.exists(path) and os.path.isdir(path):
            self.ftp5_local_folder = path
            self.ftp5_pc_path_btn.setText(path)
            self.settings["pc_folder"] = path
            save_settings(self.settings)
            self._ftp5_refresh_local_tree()

    def _ftp5_refresh_local_tree(self):
        self.ftp5_local_tree.clear()
        folder = self.ftp5_local_folder
        if not os.path.exists(folder):
            return
        try:
            names = sorted(
                os.listdir(folder),
                key=lambda x: (not os.path.isdir(os.path.join(folder, x)), x.lower()),
            )
        except Exception:
            names = []
        for n in names:
            full = os.path.join(folder, n)
            try:
                is_dir = os.path.isdir(full)
                st = os.stat(full)
                mtime = ts_fmt(st.st_mtime)
                size = fmt_bytes(st.st_size) if not is_dir else ""
                kind = "folder" if is_dir else "file"
                prefix = "📁 " if is_dir else "📄 "
                t_item = QTreeWidgetItem([prefix + n, size, kind, mtime])
                t_item.setData(0, Qt.ItemDataRole.UserRole, full)
                self.ftp5_local_tree.addTopLevelItem(t_item)
            except Exception:
                continue

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
        if curr == "/":
            return
        parent = os.path.dirname(curr.rstrip("/")) or "/"
        self.ftp5_rem_path_input.setText(parent)
        self._ftp5_load_remote()

    def _ftp5_open_session(self, ip, port):
        """Open or reuse a persistent FTP session for tab 5."""
        try:
            if self.ftp5_conn is not None:
                try:
                    self.ftp5_conn.voidcmd("NOOP")
                    return self.ftp5_conn
                except Exception:
                    try:
                        self.ftp5_conn.close()
                    except Exception:
                        pass
                    self.ftp5_conn = None
            ftp = FTP()
            ftp.connect(ip, int(port), timeout=15)
            ftp.login()
            self.ftp5_conn = ftp
            if not self.ftp5_keepalive_timer.isActive():
                self.ftp5_keepalive_timer.start()
            return ftp
        except Exception:
            self.ftp5_conn = None
            raise


    def _ftp5_keepalive_ping(self):
        if self.ftp5_conn is None:
            self.ftp5_keepalive_timer.stop()
            return
        try:
            self.ftp5_conn.voidcmd("NOOP")
        except Exception as e:
            self.log(f"[FTP] Keep-alive failed: {e}")
            try:
                self.ftp5_conn.close()
            except Exception:
                pass
            self.ftp5_conn = None
            self.ftp5_keepalive_timer.stop()


    def _ftp5_load_remote(self):
        conn = self._require_ip()
        if not conn:
            return
        ip, port = conn
        target_dir = self.ftp5_rem_path_input.text().strip() or "/"
        self.log(f"[FTP] Listing {target_dir} on {ip}:{port} ...")

        # Always maintain keep-alive session
        try:
            self._ftp5_open_session(ip, port)
        except Exception as e:
            self.log(f"[FTP] Session: {e}")

        def _task(signals, worker):
            # Dedicated connection for listing (FTP is not multi-thread safe on one socket)
            ftp = FTP()
            ftp.connect(ip, int(port), timeout=15)
            ftp.login()
            try:
                ftp.cwd(target_dir)
            except Exception as e:
                try:
                    ftp.quit()
                except Exception:
                    pass
                raise RuntimeError(f"Cannot cwd to {target_dir}: {e}")
            entries = ftp_list_detailed(ftp, ".")
            try:
                ftp.quit()
            except Exception:
                pass
            return entries

        worker = BaseTaskWorker(_task)
        worker.signals.log.connect(self.log)
        worker.signals.finished.connect(self._ftp5_on_remote_loaded)
        worker.start()
        self._track_worker(worker)

    def _ftp5_on_remote_loaded(self, success, msg, entries):
        self.ftp5_remote_tree.clear()
        if success:
            entries = entries or []
            for e in entries:
                name = e.get("name", "")
                is_dir = e.get("is_dir", False)
                prefix = "📁 " if is_dir else "📄 "
                kind = "folder" if is_dir else "file"
                sz = fmt_bytes(e.get("size", 0)) if not is_dir else ""
                t_item = QTreeWidgetItem([prefix + name, sz, kind])
                t_item.setData(0, Qt.ItemDataRole.UserRole, name)
                t_item.setData(1, Qt.ItemDataRole.UserRole, is_dir)
                self.ftp5_remote_tree.addTopLevelItem(t_item)
            self.log(f"[FTP] Listed {len(entries)} item(s).")
            if hasattr(self, "ftp5_remote_search"):
                self._ftp5_filter_remote_tree(self.ftp5_remote_search.text())
        else:
            CustomMessageBox.show_info(self, "FTP Error", msg or "Failed to list remote directory.")

    def _ftp5_filter_remote_tree(self, text):
        query = (text or "").strip().lower()
        for i in range(self.ftp5_remote_tree.topLevelItemCount()):
            item = self.ftp5_remote_tree.topLevelItem(i)
            name = item.text(0).lower()
            item.setHidden(bool(query and query not in name))

    def _ftp5_remote_open(self, item, col):
        name = item.data(0, Qt.ItemDataRole.UserRole)
        is_dir = item.data(1, Qt.ItemDataRole.UserRole)
        if is_dir is None:
            is_dir = item.text(1) == "folder"
        if is_dir:
            curr = self.ftp5_rem_path_input.text().strip().rstrip("/")
            new_path = f"{curr}/{name}" if curr != "/" else f"/{name}"
            self.ftp5_rem_path_input.setText(new_path)
            self._ftp5_load_remote()

    def _ftp5_remote_context_menu(self, pos):
        item = self.ftp5_remote_tree.itemAt(pos)
        if item is None:
            return
        if item not in self.ftp5_remote_tree.selectedItems():
            self.ftp5_remote_tree.clearSelection()
            item.setSelected(True)

        menu = QMenu(self)
        act_download = menu.addAction("Download")
        act_rename = menu.addAction("Rename")
        act_delete = menu.addAction("Delete")
        menu.addSeparator()
        act_chmod = menu.addAction("Permissions (chmod)…")
        act_mkdir = menu.addAction("New Folder")
        menu.addSeparator()
        act_refresh = menu.addAction("Refresh")
        act_copy_path = menu.addAction("Copy Path")

        chosen = menu.exec(self.ftp5_remote_tree.viewport().mapToGlobal(pos))
        if chosen is None:
            return
        if chosen == act_download:
            self._ftp5_download()
        elif chosen == act_rename:
            self._ftp5_remote_rename()
        elif chosen == act_delete:
            self._ftp5_delete()
        elif chosen == act_chmod:
            self._ftp5_remote_chmod()
        elif chosen == act_mkdir:
            self._ftp5_mkdir()
        elif chosen == act_refresh:
            self._ftp5_load_remote()
        elif chosen == act_copy_path:
            names = [it.data(0, Qt.ItemDataRole.UserRole) for it in self.ftp5_remote_tree.selectedItems()]
            base = self.ftp5_rem_path_input.text().strip().rstrip("/") or ""
            paths = [f"{base}/{n}" if base else f"/{n}" for n in names]
            QApplication.clipboard().setText("\n".join(paths))
            self.log(f"[FTP] Copied {len(paths)} path(s) to clipboard.")

    def _ftp5_local_context_menu(self, pos):
        item = self.ftp5_local_tree.itemAt(pos)
        if item is None:
            return
        if item not in self.ftp5_local_tree.selectedItems():
            self.ftp5_local_tree.clearSelection()
            item.setSelected(True)

        menu = QMenu(self)
        act_upload = menu.addAction("Upload →")
        act_open = menu.addAction("Open / Enter")
        menu.addSeparator()
        act_copy_path = menu.addAction("Copy Path")
        act_refresh = menu.addAction("Refresh")

        chosen = menu.exec(self.ftp5_local_tree.viewport().mapToGlobal(pos))
        if chosen is None:
            return
        if chosen == act_upload:
            self._ftp5_upload()
        elif chosen == act_open:
            self._ftp5_local_open(item, 0)
        elif chosen == act_copy_path:
            paths = [it.data(0, Qt.ItemDataRole.UserRole) for it in self.ftp5_local_tree.selectedItems()]
            QApplication.clipboard().setText("\n".join(str(p) for p in paths if p))
            self.log(f"[FTP] Copied {len(paths)} local path(s) to clipboard.")
        elif chosen == act_refresh:
            self._ftp5_refresh_local_tree()

    def _ftp5_remote_rename(self):
        conn = self._require_ip(need_connected=True)
        if not conn:
            return
        ip, port = conn
        sel = self.ftp5_remote_tree.selectedItems()
        if not sel or len(sel) > 1:
            CustomMessageBox.show_info(self, "Rename", "Select exactly one remote item to rename.")
            return
        old_name = sel[0].data(0, Qt.ItemDataRole.UserRole)
        new_name, ok = QInputDialog.getText(self, "Rename Remote", "New name:", text=old_name)
        if not ok or not new_name.strip() or new_name.strip() == old_name:
            return
        new_name = new_name.strip()
        ip, port = self.current_ip, self.current_port
        target_dir = self.ftp5_rem_path_input.text().strip() or "/"

        def _task(signals, worker):
            ftp = FTP()
            ftp.connect(ip, int(port), timeout=10)
            ftp.login()
            ftp.cwd(target_dir)
            ftp.rename(old_name, new_name)
            ftp.quit()
            return True

        worker = BaseTaskWorker(_task)
        worker.signals.log.connect(self.log)
        worker.signals.finished.connect(
            lambda s, m, r: (self.log(f"[FTP] Renamed {old_name} → {new_name}"), self._ftp5_load_remote())
            if s else CustomMessageBox.show_info(self, "Rename Failed", m)
        )
        worker.start()
        self._track_worker(worker)

    def _ftp5_remote_chmod(self):
        conn = self._require_ip(need_connected=True)
        if not conn:
            return
        ip, port = conn
        sel = self.ftp5_remote_tree.selectedItems()
        if not sel:
            return
        mode, ok = QInputDialog.getText(self, "Permissions", "chmod mode (e.g. 777 or 755):", text="777")
        if not ok or not mode.strip():
            return
        mode = mode.strip()
        names = [it.data(0, Qt.ItemDataRole.UserRole) for it in sel]
        ip, port = self.current_ip, self.current_port
        target_dir = self.ftp5_rem_path_input.text().strip() or "/"

        def _task(signals, worker):
            ftp = FTP()
            ftp.connect(ip, int(port), timeout=10)
            ftp.login()
            ftp.cwd(target_dir)
            for fn in names:
                rpath = f"{target_dir.rstrip('/')}/{fn}" if target_dir != "/" else f"/{fn}"
                try:
                    ftp.sendcmd(f"SITE CHMOD {mode} {rpath}")
                    signals.log.emit(f"[FTP] chmod {mode} {fn}")
                except Exception as e:
                    signals.log.emit(f"[ERROR] chmod {fn}: {e}")
            ftp.quit()
            return True

        worker = BaseTaskWorker(_task)
        worker.signals.log.connect(self.log)
        worker.signals.finished.connect(
            lambda s, m, r: CustomMessageBox.show_info(self, "Permissions", f"chmod {mode} applied.") if s else None
        )
        worker.start()
        self._track_worker(worker)

    def _ftp5_cancel_transfer(self):
        self.ftp5_cancel_flag = True
        self.log("[FTP] Cancelling ongoing transfer...")



    def _ftp5_drop_upload(self, paths):
        """Drag from local tree (or desktop) onto remote tree."""
        if not paths:
            return
        self._ftp5_run_upload(paths)

    def _ftp5_drop_download(self, names):
        """Drag from remote tree onto local tree."""
        if not names:
            return
        dest = self.ftp5_local_folder
        if not dest or not os.path.isdir(dest):
            dest = QFileDialog.getExistingDirectory(self, "Download To Folder")
            if not dest:
                return
        self._ftp5_run_download(names, dest)

    def _ftp5_upload(self):
        self.play_sound()
        if not self._require_ip():
            return
        sel = self.ftp5_local_tree.selectedItems()
        if not sel:
            return
        paths = [item.data(0, Qt.ItemDataRole.UserRole) for item in sel]
        self._ftp5_run_upload(paths)

    def _ftp5_job_key(self, direction, remote_path):
        return f"{direction}:{remote_path}"

    def _ftp5_populate_queue(self, direction, file_jobs):
        """Seed the Queue tab with one row per file job; returns {job_key: item}."""
        self.ftp5_queue_tree.clear()
        item_map = {}
        for job in file_jobs:
            fn = os.path.basename(job["local"] if direction == "upload" else job["local"])
            item = QTreeWidgetItem([fn, "Upload" if direction == "upload" else "Download", "Queued", ""])
            self.ftp5_queue_tree.addTopLevelItem(item)
            item_map[self._ftp5_job_key(direction, job["remote"])] = item
        return item_map

    def _ftp5_on_queue_item_update(self, job_key, status):
        item = self._ftp5_queue_item_map.get(job_key)
        if item:
            item.setText(2, status)

    def _ftp5_toggle_pause(self):
        self.ftp5_paused = not self.ftp5_paused
        self.ftp5_btn_pause.setText("▶ Resume" if self.ftp5_paused else "⏸ Pause")
        self.log("[FTP] Transfer paused." if self.ftp5_paused else "[FTP] Transfer resumed.")

    def _ftp5_queue_context_menu(self, pos):
        menu = QMenu(self)
        if self.ftp5_paused:
            act = menu.addAction("▶ Resume transfers")
        else:
            act = menu.addAction("⏸ Pause transfers")
        act_cancel = menu.addAction("⛔ Cancel transfers")
        chosen = menu.exec(self.ftp5_queue_tree.viewport().mapToGlobal(pos))
        if chosen is act:
            self._ftp5_toggle_pause()
        elif chosen is act_cancel:
            self._ftp5_cancel_transfer()

    def _ftp5_on_parallel_changed(self, val):
        self.ftp5_parallel_count = int(val)
        self.settings["ftp5_parallel_count"] = self.ftp5_parallel_count
        save_settings(self.settings)


    def _ftp5_file_md5(self, path):
        try:
            h = hashlib.md5()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    h.update(chunk)
            return h.hexdigest()
        except Exception:
            return None

    def _ftp5_launch_parallel(self, direction, file_jobs, fixed_policy, ip, port, dir_jobs=None):
        if not file_jobs and not dir_jobs:
            return
        dir_jobs = dir_jobs or []

        if direction == "upload" and dir_jobs:
            try:
                try:
                    ftp = self._ftp5_open_session(ip, port)
                    own = False
                except Exception:
                    ftp = FTP()
                    ftp.connect(ip, int(port), timeout=15)
                    ftp.login()
                    own = True
                for dj in dir_jobs:
                    parts = [p for p in dj["remote"].strip("/").split("/") if p]
                    cur = ""
                    for part in parts:
                        cur = f"{cur}/{part}"
                        try:
                            ftp.mkd(cur)
                        except Exception:
                            pass
                if own:
                    try:
                        ftp.quit()
                    except Exception:
                        pass
            except Exception as e:
                self.log(f"[ERROR] mkdir pass failed: {e}")
        elif direction == "download" and dir_jobs:
            for dj in dir_jobs:
                os.makedirs(dj["local"], exist_ok=True)

        total_bytes = sum(j["size"] for j in file_jobs) or 1
        self.ftp5_cancel_flag = False
        self.ftp5_paused = False
        self.ftp5_btn_pause.setText("⏸ Pause")
        self.ftp5_btn_pause.setEnabled(True)
        self.ftp5_btn_cancel.setEnabled(True)
        self.ftp5_prog.set_progress(0)

        self._ftp5_queue_item_map = self._ftp5_populate_queue(direction, file_jobs)

        n_workers = max(1, min(self.ftp5_parallel_count, len(file_jobs))) if file_jobs else 0
        self.log(f"[FTP] {direction.capitalize()} queue: {len(file_jobs)} file(s), "
                 f"{fmt_bytes(total_bytes)}, {n_workers} connection(s)")

        chunks = [file_jobs[i::n_workers] for i in range(n_workers)] if n_workers else []

        shared = {
            "lock": threading.Lock(),
            "sent": 0,
            "start": time.time(),
            "total": total_bytes,
            "completed": 0,
            "worker_count": len(chunks),
            "history": [],
            "any_fail": False,
        }

        if not chunks:
            self._ftp5_finish_parallel_transfer(shared, direction)
            return

        for chunk in chunks:
            worker = BaseTaskWorker(self._ftp5_chunk_task, direction, chunk, fixed_policy, ip, port, shared)
            worker.signals.log.connect(self.log)
            worker.signals.item_update.connect(self._ftp5_on_queue_item_update)
            worker.signals.progress.connect(lambda v, s, e, l: self.ftp5_prog.set_progress(v, s, e, l))
            worker.signals.finished.connect(
                lambda ok, msg, res, shared=shared, direction=direction:
                    self._ftp5_on_chunk_finished(ok, msg, res, shared, direction)
            )
            worker.start()
            self._ftp5_active_workers.append(worker)
            self._track_worker(worker)

    def _ftp5_chunk_task(self, signals, worker, direction, chunk, fixed_policy, ip, port, shared):
        ftp = FTP()
        ftp.connect(ip, int(port), timeout=15)
        ftp.login()
        for job in chunk:
            if self.ftp5_cancel_flag:
                break
            while self.ftp5_paused and not self.ftp5_cancel_flag:
                time.sleep(0.2)
            rpath = job["remote"]
            lpath = job["local"]
            fn = os.path.basename(lpath)
            key = self._ftp5_job_key(direction, rpath)
            signals.item_update.emit(key, "Active")

            # conflict check
            exists = os.path.exists(lpath) if direction == "download" else False
            if direction == "upload":
                try:
                    ftp.size(rpath)
                    exists = True
                except Exception:
                    exists = False
            if exists:
                decision = fixed_policy or "skip"
                if decision == "skip":
                    signals.log.emit(f"[FTP] Skip existing {fn}")
                    signals.item_update.emit(key, "Skipped")
                    with shared["lock"]:
                        shared["sent"] += job["size"]
                        shared["history"].append(self._ftp5_history_row(direction, fn, "Skipped", job["size"]))
                    continue
                elif decision == "rename":
                    if direction == "upload":
                        stem, ext = os.path.splitext(rpath)
                        rpath = f"{stem}_copy{ext}"
                    else:
                        stem, ext = os.path.splitext(lpath)
                        lpath = f"{stem}_copy{ext}"

            def _cb(nbytes):
                if self.ftp5_cancel_flag:
                    raise IOError("cancelled")
                with shared["lock"]:
                    shared["sent"] += nbytes
                    sent = shared["sent"]
                el = time.time() - shared["start"]
                spd = sent / max(0.001, el)
                eta = (shared["total"] - sent) / max(1, spd)
                pct = min(100.0, sent / shared["total"] * 100.0)
                signals.progress.emit(pct, spd, eta, fn)

            status = "Done"
            try:
                if direction == "upload":
                    signals.log.emit(f"[FTP] Uploading {fn} → {rpath}")
                    with open(lpath, "rb") as f:
                        ftp.storbinary(f"STOR {rpath}", f, blocksize=1024 * 512,
                                        callback=lambda data: _cb(len(data)))
                else:
                    signals.log.emit(f"[FTP] Downloading {fn}")
                    os.makedirs(os.path.dirname(lpath) or ".", exist_ok=True)
                    with open(lpath, "wb") as f:
                        def writer(data, _f=f):
                            _f.write(data)
                            _cb(len(data))
                        try:
                            ftp.retrbinary(f"RETR {rpath}", writer, blocksize=1024 * 512)
                        except Exception:
                            ftp.cwd(os.path.dirname(rpath) or "/")
                            ftp.retrbinary(f"RETR {os.path.basename(rpath)}", writer, blocksize=1024 * 512)

                checksum = None
                if self.ftp5_verify_checksum:
                    hash_target = lpath if direction == "upload" else lpath
                    checksum = self._ftp5_file_md5(hash_target)
                    if checksum:
                        signals.log.emit(f"[FTP] MD5 {fn}: {checksum}")
            except Exception as e:
                if "cancelled" in str(e).lower():
                    signals.log.emit("[FTP] Transfer cancelled.")
                    signals.item_update.emit(key, "Cancelled")
                    break
                signals.log.emit(f"[ERROR] {fn}: {e}")
                status = "Failed"
                with shared["lock"]:
                    shared["any_fail"] = True
                checksum = None

            signals.item_update.emit(key, status)
            with shared["lock"]:
                shared["history"].append(
                    self._ftp5_history_row(direction, fn, status, job["size"], checksum=checksum,
                                            local=lpath, remote=rpath))
        try:
            ftp.quit()
        except Exception:
            pass
        return True

    def _ftp5_history_row(self, direction, name, status, size, checksum=None, local=None, remote=None):
        return {
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "direction": direction,
            "name": name,
            "status": status,
            "size": size,
            "checksum": checksum,
            "local": local,
            "remote": remote,
        }

    def _ftp5_on_chunk_finished(self, ok, msg, res, shared, direction):
        with shared["lock"]:
            shared["completed"] += 1
            done = shared["completed"] >= shared["worker_count"]
        if not ok:
            self.log(f"[ERROR] Transfer connection failed: {msg}")
        if done:
            self._ftp5_finish_parallel_transfer(shared, direction)

    def _ftp5_finish_parallel_transfer(self, shared, direction):
        self.ftp5_btn_cancel.setEnabled(False)
        self.ftp5_btn_pause.setEnabled(False)
        self.ftp5_paused = False
        self.ftp5_cancel_flag = False
        self._ftp5_active_workers = []
        if shared["history"]:
            self.ftp5_history.extend(shared["history"])
            self.ftp5_history = self.ftp5_history[-20:]
            save_ftp5_history(self.ftp5_history)
            self._ftp5_reload_history_tree()
        self.ftp5_prog.set_progress(100 if not shared.get("any_fail") else 0)
        if direction == "upload":
            self._ftp5_load_remote()
        else:
            self._ftp5_refresh_local_tree()
        if shared.get("any_fail"):
            self.log("[FTP] Transfer finished with errors — see History tab / Retry Failed.")

    def _ftp5_run_upload(self, paths):
        ip = self.ip_entry.text().strip() or self.current_ip
        port = self.port_entry.text().strip() or self.current_port or "2121"
        if not ip:
            CustomMessageBox.show_info(self, "Error", "Enter console IP first.")
            return
        target_dir = self.ftp5_rem_path_input.text().strip() or "/"
        jobs = collect_local_transfer_jobs(paths, target_dir)
        if not jobs:
            return

        policy = self._ftp5_conflict_mode()
        fixed_policy = policy if policy != "ask" else None
        if policy == "ask":
            choice = CustomMessageBox(
                "Conflict Policy",
                "If a file already exists on the console, what should happen?\n"
                "(Applies to this whole upload batch.)",
                self,
                [
                    ("Overwrite", "overwrite", "Primary"),
                    ("Rename (_copy)", "rename", "Normal"),
                    ("Skip", "skip", "Normal"),
                ],
            )
            choice.exec()
            fixed_policy = choice.clicked_button or "skip"

        file_jobs = [j for j in jobs if not j["is_dir"]]
        dir_jobs = [j for j in jobs if j["is_dir"]]
        self._ftp5_launch_parallel("upload", file_jobs, fixed_policy, ip, port, dir_jobs)


    def _ftp5_download(self):
        self.play_sound()
        if not self._require_ip():
            return
        sel = self.ftp5_remote_tree.selectedItems()
        if not sel:
            return
        names = [item.data(0, Qt.ItemDataRole.UserRole) for item in sel]
        is_dirs = [bool(item.data(1, Qt.ItemDataRole.UserRole)) for item in sel]
        dest = QFileDialog.getExistingDirectory(self, "Download To Folder")
        if not dest:
            return
        self._ftp5_run_download(names, dest, is_dirs)

    def _ftp5_run_download(self, names, dest, is_dirs=None):
        ip = self.ip_entry.text().strip() or self.current_ip
        port = self.port_entry.text().strip() or self.current_port or "2121"
        if not ip:
            CustomMessageBox.show_info(self, "Error", "Enter console IP first.")
            return
        target_dir = self.ftp5_rem_path_input.text().strip() or "/"
        if is_dirs is None:
            is_dirs = [False] * len(names)

        policy = self._ftp5_conflict_mode()
        fixed_policy = policy if policy != "ask" else None
        if policy == "ask":
            choice = CustomMessageBox(
                "Conflict Policy",
                "If a file already exists on your PC, what should happen?\n"
                "(Applies to this whole download batch.)",
                self,
                [
                    ("Overwrite", "overwrite", "Primary"),
                    ("Rename (_copy)", "rename", "Normal"),
                    ("Skip", "skip", "Normal"),
                ],
            )
            choice.exec()
            fixed_policy = choice.clicked_button or "skip"

        self.log(f"[FTP] Preparing download of {len(names)} item(s) → {dest} ...")

        def _walk_remote(ftp, remote_path, local_base, jobs):
            try:
                ftp.cwd(remote_path)
            except Exception:
                return
            entries = ftp_list_detailed(ftp, ".")
            for e in entries:
                name = e["name"]
                r = f"{remote_path.rstrip('/')}/{name}"
                l = os.path.join(local_base, name)
                if e["is_dir"]:
                    jobs.append({"remote": r, "local": l, "size": 0, "is_dir": True})
                    _walk_remote(ftp, r, l, jobs)
                    try:
                        ftp.cwd(remote_path)
                    except Exception:
                        pass
                else:
                    jobs.append({"remote": r, "local": l, "size": e.get("size", 0), "is_dir": False})

        def _expand_task(signals, worker):
            ftp = FTP()
            ftp.connect(ip, int(port), timeout=15)
            ftp.login()
            try:
                ftp.cwd(target_dir)
            except Exception:
                pass
            jobs = []
            for name, is_dir in zip(names, is_dirs):
                rpath = f"{target_dir.rstrip('/')}/{name}" if target_dir != "/" else f"/{name}"
                lpath = os.path.join(dest, name)
                if is_dir:
                    jobs.append({"remote": rpath, "local": lpath, "size": 0, "is_dir": True})
                    _walk_remote(ftp, rpath, lpath, jobs)
                    try:
                        ftp.cwd(target_dir)
                    except Exception:
                        pass
                else:
                    sz = 0
                    try:
                        sz = ftp.size(name) or 0
                    except Exception:
                        try:
                            sz = ftp.size(rpath) or 0
                        except Exception:
                            pass
                    jobs.append({"remote": rpath, "local": lpath, "size": sz, "is_dir": False})
            try:
                ftp.quit()
            except Exception:
                pass
            return jobs

        def _on_expanded(ok, msg, jobs):
            if not ok or not jobs:
                if not ok:
                    CustomMessageBox.show_info(self, "FTP Error", msg or "Could not list remote items.")
                return
            file_jobs = [j for j in jobs if not j["is_dir"]]
            dir_jobs = [j for j in jobs if j["is_dir"]]
            self.log(f"[FTP] Expanded to {len(file_jobs)} file(s).")
            self._ftp5_launch_parallel("download", file_jobs, fixed_policy, ip, port, dir_jobs)

        worker = BaseTaskWorker(_expand_task)
        worker.signals.log.connect(self.log)
        worker.signals.finished.connect(_on_expanded)
        worker.start()
        self._track_worker(worker)

    def _ftp5_delete(self):
        self.play_sound()
        if not self._require_ip():
            return
        sel = self.ftp5_remote_tree.selectedItems()
        if not sel:
            return
        names = [item.data(0, Qt.ItemDataRole.UserRole) for item in sel]
        is_dirs = [bool(item.data(1, Qt.ItemDataRole.UserRole)) for item in sel]
        if not CustomMessageBox.ask_yes_no(self, "Delete Remote Files", f"Delete {len(names)} remote item(s)?"):
            return

        ip, port = self.current_ip, self.current_port
        target_dir = self.ftp5_rem_path_input.text().strip() or "/"

        def _rm_tree(ftp, path):
            try:
                ftp.cwd(path)
            except Exception:
                try:
                    ftp.delete(path)
                except Exception:
                    pass
                return
            entries = ftp_list_detailed(ftp, ".")
            for e in entries:
                child = f"{path.rstrip('/')}/{e['name']}"
                if e["is_dir"]:
                    _rm_tree(ftp, child)
                else:
                    try:
                        ftp.delete(child)
                    except Exception:
                        try:
                            ftp.delete(e["name"])
                        except Exception as ex:
                            signals_ref[0].log.emit(f"[ERROR] delete {e['name']}: {ex}")
            try:
                ftp.cwd("..")
                ftp.rmd(path if path.startswith("/") else os.path.basename(path))
            except Exception:
                try:
                    ftp.rmd(os.path.basename(path))
                except Exception:
                    pass

        signals_ref = [None]

        def _task(signals, worker):
            signals_ref[0] = signals
            ftp = FTP()
            ftp.connect(ip, int(port), timeout=10)
            ftp.login()
            ftp.cwd(target_dir)
            for name, is_dir in zip(names, is_dirs):
                rpath = f"{target_dir.rstrip('/')}/{name}" if target_dir != "/" else f"/{name}"
                if is_dir:
                    _rm_tree(ftp, rpath)
                else:
                    try:
                        ftp.delete(name)
                    except Exception:
                        try:
                            ftp.delete(rpath)
                        except Exception as e:
                            signals.log.emit(f"[ERROR] {e}")
            ftp.quit()
            return True

        worker = BaseTaskWorker(_task)
        worker.signals.log.connect(self.log)
        worker.signals.finished.connect(lambda s, m, r: self._ftp5_load_remote())
        worker.start()
        self._track_worker(worker)

    def _ftp5_mkdir(self):
        self.play_sound()
        conn = self._require_ip()
        if not conn:
            return
        ip, port = conn
        target_dir = self.ftp5_rem_path_input.text().strip() or "/"
        folder_name, ok = QInputDialog.getText(self, "New Folder", "Folder name:", text="NewFolder")
        if not ok or not folder_name.strip():
            return
        folder_name = folder_name.strip()

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
        self._track_worker(worker)

    def _ftp5_reload_history_tree(self):
        self.ftp5_history_tree.clear()
        for row in reversed(self.ftp5_history[-20:]):
            item = QTreeWidgetItem([
                row.get("time", ""),
                "Up" if row.get("direction") == "upload" else "Down",
                row.get("name", ""),
                row.get("status", ""),
                fmt_bytes(row.get("size", 0)),
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, row)
            if row.get("status") == "Failed":
                item.setForeground(3, QColor(Theme.ACCENT_RED))
            self.ftp5_history_tree.addTopLevelItem(item)

    def _ftp5_remove_history_rows(self):
        sel = self.ftp5_history_tree.selectedItems()
        if not sel:
            return
        keys = set()
        for it in sel:
            row = it.data(0, Qt.ItemDataRole.UserRole) or {}
            keys.add((row.get("time"), row.get("name"), row.get("direction"), row.get("status")))
        self.ftp5_history = [
            r for r in self.ftp5_history
            if (r.get("time"), r.get("name"), r.get("direction"), r.get("status")) not in keys
        ][-20:]
        save_ftp5_history(self.ftp5_history)
        self._ftp5_reload_history_tree()

    def _ftp5_clear_history(self):
        self.ftp5_history = []
        save_ftp5_history(self.ftp5_history)
        self._ftp5_reload_history_tree()

    def _ftp5_retry_failed(self):
        """Retry only the Failed rows currently SELECTED in the History tree."""
        ip = self.ip_entry.text().strip() or self.current_ip
        port = self.port_entry.text().strip() or self.current_port or "2121"
        if not ip:
            CustomMessageBox.show_info(self, "Error", "Enter console IP first.")
            return
        sel = self.ftp5_history_tree.selectedItems()
        if not sel:
            CustomMessageBox.show_info(self, "Retry Selected", "Select one or more Failed rows in History first.")
            return
        rows = [it.data(0, Qt.ItemDataRole.UserRole) for it in sel]
        failed = [r for r in rows if r and r.get("status") == "Failed" and r.get("local") and r.get("remote")]
        if not failed:
            CustomMessageBox.show_info(self, "Retry Selected", "None of the selected rows are retryable (Failed with known paths).")
            return
        up_jobs = [{"remote": r["remote"], "local": r["local"], "size": 0, "is_dir": False}
                   for r in failed if r["direction"] == "upload"]
        down_jobs = [{"remote": r["remote"], "local": r["local"], "size": 0, "is_dir": False}
                     for r in failed if r["direction"] == "download"]
        if up_jobs:
            self._ftp5_launch_parallel("upload", up_jobs, "overwrite", ip, port)
        if down_jobs:
            self._ftp5_launch_parallel("download", down_jobs, "overwrite", ip, port)


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
        
        btn_start = QPushButton("Compress")
        btn_start.setObjectName("Primary")
        btn_start.setMinimumHeight(34)
        btn_start.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn_start.clicked.connect(self._ffpfsc_start)
        layout.addWidget(btn_start)
        
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
        try:
            import mkpfs  # noqa: F401
        except ImportError:
            CustomMessageBox.show_info(
                self,
                "mkpfs Missing",
                "The mkpfs package is required to create FFPFSC files.\n\n"
                "Install it with:\n  pip install mkpfs\n\n"
                "Or place the mkpfs module next to this app.",
            )
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
                # Label must NOT include a trailing "%" — FancyProgressBar already paints "N%"
                match_blocks = re.search(r'(\d+)\s*/\s*(\d+)', clean)
                match_pct = re.search(r'(\d+(?:\.\d+)?)\s*%', clean)
                if match_blocks:
                    curr, total = int(match_blocks.group(1)), int(match_blocks.group(2))
                    if total > 0:
                        pct = (curr / total) * 100.0
                        signals.progress.emit(pct, 0, -1, f"{curr}/{total} blocks")
                elif match_pct:
                    pct = float(match_pct.group(1))
                    signals.progress.emit(pct, 0, -1, "compressing")
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
        self._track_worker(worker)

    def _build_tab_browser(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)
        
        lbl = QLabel("🌐 Web Apps")
        lbl.setObjectName("Heading")
        layout.addWidget(lbl)
        
        tb = QHBoxLayout()
        btn_back = QPushButton("◀")
        btn_back.setFixedWidth(32)
        btn_fwd = QPushButton("▶")
        btn_fwd.setFixedWidth(32)
        btn_ref = QPushButton("⟳")
        btn_ref.setFixedWidth(32)
        btn_home = QPushButton("⌂")
        btn_home.setFixedWidth(32)
        btn_home.setToolTip("Home — NEXUS Web Portal")
        btn_home.clicked.connect(self._browser_home)
        
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
        tb.addWidget(btn_home)
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
            btn_ref.clicked.connect(self._browser_reload_or_landing)
            # Intercept nexus://port/<n> links from landing cards
            self.web.urlChanged.connect(self._browser_on_url_changed)
            self._browser_show_landing()
            layout.addWidget(self.web, 1)
        else:
            lbl_no_web = QLabel("PyQt6-WebEngine is missing.\nInstall with: pip install PyQt6-WebEngine")
            lbl_no_web.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_no_web.setStyleSheet(f"color: {Theme.ACCENT_RED}; font-size: 12pt; font-weight: bold;")
            layout.addWidget(lbl_no_web, 1)

    def _browser_build_landing_html(self):
        # nexus://port/<n> interception (falls back to http://ip:port when known).
        ip = (self.ip_entry.text().strip() if hasattr(self, "ip_entry") else "") or self.current_ip or ""
        buttons_html = ""
        for name, port, _ in BROWSER_BOOKMARKS:
            href = f"http://{ip}:{port}" if ip else f"nexus://port/{port}"
            buttons_html += (
                f'<a class="bm-btn" href="{href}" '
                f'onclick="window.location.href=\'{href}\';return false;">{name}</a>'
            )
        html = (
            "<!DOCTYPE html><html><head><meta charset='utf-8'><style>"
            "*{margin:0;padding:0;box-sizing:border-box}"
            "body{font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh;"
            "background:linear-gradient(135deg,#111111 0%,#1A1A1A 40%,#2A0A12 70%,#FF0033 140%);"
            "color:#F5F5F5;display:flex;flex-direction:column;align-items:center;"
            "justify-content:center;padding:40px 20px}"
            ".card{background:rgba(30,30,30,0.88);border:1px solid #333;border-radius:16px;"
            "padding:40px 48px;max-width:560px;width:100%;text-align:center;"
            "box-shadow:0 12px 40px rgba(255,0,51,0.18)}"
            "h1{font-size:28px;font-weight:700;color:#FF0033;margin-bottom:8px}"
            ".sub{font-size:14px;color:#B0B0B0;margin-bottom:28px;line-height:1.5}"
            ".bm-grid{display:flex;flex-wrap:wrap;gap:12px;justify-content:center}"
            ".bm-btn{display:inline-block;background:#242424;color:#F5F5F5;text-decoration:none;"
            "padding:12px 20px;border-radius:8px;font-size:13px;font-weight:600;border:1px solid #333}"
            ".bm-btn:hover{background:#FF0033;border-color:#FF0033}"
            ".footer{margin-top:24px;font-size:11px;color:#665665}"
            "</style></head><body><div class='card'><h1>NEXUS</h1>"
            "<p class='sub'>Welcome!<br>"
            "Pick a quick link below or type a URL in the address bar.</p>"
            f"<div class='bm-grid'>{buttons_html}</div>"
            "<p class='footer'>PS5 Utility Suite · Issu. 2026</p>"
            "</div></body></html>"
        )
        return html

    def _browser_home(self):
        self.play_sound()
        self.browser_url_input.setText("")
        self._browser_show_landing()

    def _browser_show_landing(self):
        if HAS_WEBENGINE and hasattr(self, "web"):
            self.web.setHtml(self._browser_build_landing_html())

    def _browser_reload_or_landing(self):
        if not HAS_WEBENGINE or not hasattr(self, "web"):
            return
        url = self.web.url().toString() if self.web.url() else ""
        if not url or url in ("about:blank", "") or url.startswith("data:"):
            self._browser_show_landing()
        else:
            self.web.reload()

    def _browser_on_url_changed(self, qurl):
        """Handle nexus://port/<n> from landing cards when IP is unknown."""
        s = qurl.toString()
        if not s.startswith("nexus://port/"):
            return
        try:
            port = int(s.rsplit("/", 1)[-1])
        except ValueError:
            return
        ip = self.ip_entry.text().strip() or self.current_ip
        if not ip:
            CustomMessageBox.show_info(
                self, "Console IP Required",
                "Enter your console IP in the sidebar first, then click a bookmark card again."
            )
            self._browser_show_landing()
            return
        url = f"http://{ip}:{port}"
        self.browser_url_input.setText(url)
        self.web.load(QUrl(url))

    def _browser_autofill(self):
        self.play_sound()
        ip = self.ip_entry.text().strip() or self.current_ip
        port = self.browser_url_input.text().strip() or "9999"
        if ip:
            self.browser_url_input.setText(f"http://{ip}:{port}")
            self._browser_show_landing()  # refresh cards with live IP links

    def _browser_bookmark(self, port):
        self.play_sound()
        ip = self.ip_entry.text().strip() or self.current_ip
        if not ip:
            CustomMessageBox.show_info(self, "Error", "Enter console IP first.")
            return
        url = f"http://{ip}:{port}"
        self.browser_url_input.setText(url)
        self._browser_navigate()

    def _browser_navigate(self):
        url = self.browser_url_input.text().strip()
        if not url:
            return
        if not url.startswith(("http://", "https://")):
            url = f"http://{url}"
            self.browser_url_input.setText(url)
        if HAS_WEBENGINE and hasattr(self, "web"):
            self.web.load(QUrl(url))


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = NexusApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

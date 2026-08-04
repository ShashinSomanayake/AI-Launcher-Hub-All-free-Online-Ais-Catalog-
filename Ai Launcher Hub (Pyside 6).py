"""
AI Launcher Hub — A fast, searchable launcher for AI websites and developer tools.
Optimised for daily use by software engineers on Windows.
PySide6 port — all features preserved from the original Tkinter version.
"""

import json
import os
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog, QLabel, QPushButton,
    QLineEdit, QListWidget, QComboBox, QCheckBox, QFrame,
    QHBoxLayout, QVBoxLayout, QGridLayout, QSplitter, QScrollArea,
    QMenu, QFileDialog, QMessageBox, QSizePolicy, QGroupBox, QFormLayout,
)
from PySide6.QtCore import (
    Qt, Signal, QObject, QEvent, QTimer, QPoint,
)
from PySide6.QtGui import (
    QPixmap, QImage, QKeySequence, QShortcut, QFont, QAction,
)

# Optional favicon support
try:
    from PIL import Image
    from urllib.request import urlopen, Request
    from io import BytesIO
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
APP_NAME = "AI Launcher Hub"
DATA_DIR = Path(os.environ.get("APPDATA", ".")) / APP_NAME
DATA_FILE = DATA_DIR / "launcher_data.json"
DEFAULT_FAVICON_SIZE = (32, 32)
MAX_RECENT = 20
DEFAULT_BROWSER = "chrome"

DEFAULT_TOOLS = [
    {"id": "chatgpt",     "name": "ChatGPT",         "url": "https://chat.openai.com",                  "category": "Chatbots",          "icon": "", "notes": "", "pinned": False},
    {"id": "gemini",      "name": "Gemini",           "url": "https://gemini.google.com",                "category": "Chatbots",          "icon": "", "notes": "", "pinned": False},
    {"id": "claude",      "name": "Claude",           "url": "https://claude.ai",                        "category": "Chatbots",          "icon": "", "notes": "", "pinned": False},
    {"id": "perplexity",  "name": "Perplexity AI",    "url": "https://www.perplexity.ai",                "category": "Research",          "icon": "", "notes": "", "pinned": False},
    {"id": "midjourney",  "name": "Midjourney",       "url": "https://www.midjourney.com",               "category": "Image Generation",  "icon": "", "notes": "", "pinned": False},
    {"id": "dalle",       "name": "DALL·E",           "url": "https://labs.openai.com",                  "category": "Image Generation",  "icon": "", "notes": "", "pinned": False},
    {"id": "copilot",     "name": "GitHub Copilot",   "url": "https://github.com/features/copilot",      "category": "Coding",            "icon": "", "notes": "", "pinned": False},
    {"id": "codewhisper", "name": "CodeWhisperer",    "url": "https://aws.amazon.com/codewhisperer/",    "category": "Coding",            "icon": "", "notes": "", "pinned": False},
    {"id": "bard",        "name": "Bard",             "url": "https://bard.google.com",                  "category": "Chatbots",          "icon": "", "notes": "", "pinned": False},
    {"id": "hugchat",     "name": "HuggingChat",      "url": "https://huggingface.co/chat",              "category": "Chatbots",          "icon": "", "notes": "", "pinned": False},
    {"id": "phind",       "name": "Phind",            "url": "https://www.phind.com",                    "category": "Research",          "icon": "", "notes": "", "pinned": False},
    {"id": "jasper",      "name": "Jasper",           "url": "https://www.jasper.ai",                    "category": "Writing",           "icon": "", "notes": "", "pinned": False},
    {"id": "writesonic",  "name": "Writesonic",       "url": "https://writesonic.com",                   "category": "Writing",           "icon": "", "notes": "", "pinned": False},
    {"id": "runway",      "name": "RunwayML",         "url": "https://runwayml.com",                     "category": "Media",             "icon": "", "notes": "", "pinned": False},
    {"id": "kaiber",      "name": "Kaiber",           "url": "https://kaiber.ai",                        "category": "Media",             "icon": "", "notes": "", "pinned": False},
]

PRIVATE_FLAGS: Dict[str, List[str]] = {
    "chrome":  ["--incognito"],
    "edge":    ["--inprivate"],
    "firefox": ["--private-window"],
    "brave":   ["--incognito"],
    "opera":   ["--private"],
    "vivaldi": ["--incognito"],
}

# ----------------------------------------------------------------------
# Browser Detection (Windows)
# ----------------------------------------------------------------------
def detect_browsers() -> List[Dict[str, Any]]:
    """Detect installed browsers via registry and known paths."""
    browsers: List[Dict[str, Any]] = []
    known = [
        ("chrome",  "chrome.exe",   "Google Chrome",  "Google\\Chrome\\Application"),
        ("edge",    "msedge.exe",   "Microsoft Edge", "Microsoft\\Edge\\Application"),
        ("firefox", "firefox.exe",  "Mozilla Firefox","Mozilla Firefox"),
        ("brave",   "brave.exe",    "Brave",          "BraveSoftware\\Brave-Browser\\Application"),
        ("opera",   "launcher.exe", "Opera Stable",   "Opera\\launcher.exe"),
        ("vivaldi", "vivaldi.exe",  "Vivaldi",        "Vivaldi\\Application"),
    ]

    # Registry approach
    try:
        import winreg
        uninstall_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, uninstall_key) as key:
            for i in range(winreg.QueryInfoKey(key)[0]):
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    with winreg.OpenKey(key, subkey_name) as subkey:
                        try:
                            display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                            install_loc  = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                        except Exception:
                            continue
                        for bname, bexe, substr, path_parts in known:
                            if substr.lower() in display_name.lower():
                                exe_path = Path(install_loc) / bexe
                                if exe_path.exists():
                                    browsers.append({
                                        "name":         bname,
                                        "display_name": display_name,
                                        "path":         str(exe_path),
                                        "private_flag": PRIVATE_FLAGS.get(bname, []),
                                        "profiles":     _detect_profiles(bname),
                                    })
                except Exception:
                    pass
    except ImportError:
        pass

    # Fallback: common Program Files paths
    program_files = [
        os.environ.get("ProgramFiles",      "C:\\Program Files"),
        os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
    ]
    for bname, bexe, substr, path_parts in known:
        if not any(b["name"] == bname for b in browsers):
            for pf in program_files:
                exe_path = Path(pf) / path_parts / bexe
                if exe_path.exists():
                    browsers.append({
                        "name":         bname,
                        "display_name": bname.title(),
                        "path":         str(exe_path),
                        "private_flag": PRIVATE_FLAGS.get(bname, []),
                        "profiles":     _detect_profiles(bname),
                    })
                    break

    # Always ensure at least the system default
    try:
        default = webbrowser.get().name
        if not any(b["name"] == default.lower() for b in browsers):
            browsers.append({
                "name":         default.lower(),
                "display_name": default,
                "path":         "",
                "private_flag": [],
                "profiles":     [],
            })
    except Exception:
        pass

    return browsers


def _detect_profiles(browser_name: str) -> List[str]:
    """Return profile directory names for Chromium-based browsers."""
    if browser_name not in ("chrome", "edge", "brave", "vivaldi"):
        return []
    base_map = {
        "chrome":  os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data"),
        "edge":    os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data"),
        "brave":   os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data"),
        "vivaldi": os.path.expandvars(r"%LOCALAPPDATA%\Vivaldi\User Data"),
    }
    user_data = base_map.get(browser_name, "")
    if not user_data or not os.path.isdir(user_data):
        return []
    profiles = []
    for entry in os.listdir(user_data):
        if entry.startswith("Profile ") or entry == "Default":
            profiles.append(entry)
    return sorted(profiles)


# ----------------------------------------------------------------------
# Async Favicon/Icon Cache
# ----------------------------------------------------------------------
class IconCache:
    """Thread-safe async favicon loader; marshals results to main thread via QTimer."""

    def __init__(self):
        self._cache: Dict[str, Optional[QPixmap]] = {}
        self._pending: set = set()
        self._lock = threading.Lock()

    def get_icon(self, url: str) -> Optional[QPixmap]:
        with self._lock:
            return self._cache.get(url)

    def load_icon_async(self, url: str, callback, size: tuple = DEFAULT_FAVICON_SIZE):
        with self._lock:
            if url in self._cache or url in self._pending:
                return
            self._pending.add(url)

        def _fetch():
            qimg: Optional[QImage] = None
            if HAS_PIL:
                try:
                    domain = url.split("/")[2]
                    favicon_url = (
                        f"https://www.google.com/s2/favicons?domain={domain}&sz={size[0]}"
                    )
                    req = Request(favicon_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urlopen(req, timeout=5) as u:
                        raw = u.read()
                    img = Image.open(BytesIO(raw)).resize(size, Image.LANCZOS).convert("RGBA")
                    data = img.tobytes("raw", "RGBA")
                    qimg = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
                    # Keep a copy of the bytes so QImage data isn't GC'd before conversion
                    qimg._data = data  # type: ignore[attr-defined]
                except Exception:
                    qimg = None

            # Marshal back to main thread — QPixmap must be created on the GUI thread
            def _deliver():
                pixmap = QPixmap.fromImage(qimg) if qimg and not qimg.isNull() else None
                with self._lock:
                    self._cache[url] = pixmap
                    self._pending.discard(url)
                callback(url, pixmap)

            QTimer.singleShot(0, _deliver)

        threading.Thread(target=_fetch, daemon=True).start()


# ----------------------------------------------------------------------
# Tool Card Widget
# ----------------------------------------------------------------------
class ToolCard(QFrame):
    """Self-contained card for a single tool: icon, name, category, open & fav buttons."""

    def __init__(
        self,
        tool: dict,
        is_favorite: bool,
        launch_cb,
        fav_cb,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.tool = tool
        self.tool_id = tool["id"]
        self._launch_cb = launch_cb
        self._fav_cb = fav_cb
        self.parent_hub: Optional["AILauncherHub"] = None  # set after construction

        self.setObjectName("ToolCard")
        self.setFixedWidth(185)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

        self._build(is_favorite)

        # Forward right-clicks from all children up to this card via event filter
        for child in self.findChildren(QWidget):
            child.installEventFilter(self)

    def _build(self, is_favorite: bool) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 10, 8, 8)
        layout.setSpacing(5)

        # --- Icon / letter placeholder ---
        self.icon_label = QLabel()
        self.icon_label.setObjectName("IconLabel")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFixedSize(48, 48)
        letter = self.tool["name"][0].upper() if self.tool["name"] else "?"
        self.icon_label.setText(letter)
        self.icon_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        layout.addWidget(self.icon_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        # --- Tool name ---
        name_lbl = QLabel(self.tool["name"])
        name_lbl.setObjectName("CardName")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        name_lbl.setWordWrap(True)
        layout.addWidget(name_lbl)

        # --- Category ---
        cat_lbl = QLabel(self.tool["category"])
        cat_lbl.setObjectName("CardCategory")
        cat_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cat_lbl.setFont(QFont("Segoe UI", 8))
        layout.addWidget(cat_lbl)

        # --- Notes tooltip ---
        if self.tool.get("notes"):
            self.setToolTip(self.tool["notes"])

        # --- Buttons ---
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)

        open_btn = QPushButton("Open")
        open_btn.setObjectName("CardButton")
        open_btn.clicked.connect(lambda: self._launch_cb(self.tool))
        btn_row.addWidget(open_btn)

        self.fav_btn = QPushButton("★" if is_favorite else "☆")
        self.fav_btn.setObjectName("CardButton")
        self.fav_btn.setFixedWidth(32)
        self.fav_btn.clicked.connect(lambda: self._fav_cb(self.tool))
        btn_row.addWidget(self.fav_btn)

        layout.addLayout(btn_row)

    # ------------------------------------------------------------------ #
    # Public helpers                                                       #
    # ------------------------------------------------------------------ #
    def set_icon(self, pixmap: QPixmap) -> None:
        if pixmap and not pixmap.isNull():
            self.icon_label.setPixmap(
                pixmap.scaled(
                    48, 48,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            self.icon_label.setText("")

    def update_favorite(self, is_fav: bool) -> None:
        self.fav_btn.setText("★" if is_fav else "☆")

    # ------------------------------------------------------------------ #
    # Context menu (card + all children)                                  #
    # ------------------------------------------------------------------ #
    def contextMenuEvent(self, event) -> None:
        if self.parent_hub:
            self.parent_hub.show_context_menu(self.tool, event.globalPos())
        event.accept()

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.Type.ContextMenu:
            if self.parent_hub:
                self.parent_hub.show_context_menu(self.tool, event.globalPos())
            return True
        return super().eventFilter(obj, event)


# ----------------------------------------------------------------------
# Tool Editor Dialog
# ----------------------------------------------------------------------
class ToolEditor(QDialog):
    def __init__(
        self,
        parent: QWidget,
        tool: dict,
        all_tools: list,
        callback,
        is_new: bool = False,
    ):
        super().__init__(parent)
        self.setWindowTitle("Add New Tool" if is_new else "Edit Tool")
        self.setModal(True)
        self.setMinimumWidth(420)
        self.tool = tool.copy()
        self.all_tools = all_tools
        self.callback = callback
        self.is_new = is_new
        self._build()

    def _build(self) -> None:
        layout = QFormLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        self.name_edit = QLineEdit(self.tool.get("name", ""))
        self.name_edit.setMinimumWidth(300)
        layout.addRow("Name:", self.name_edit)

        self.url_edit = QLineEdit(self.tool.get("url", ""))
        layout.addRow("URL:", self.url_edit)

        cats = sorted({t["category"] for t in self.all_tools})
        self.cat_combo = QComboBox()
        self.cat_combo.setEditable(True)
        self.cat_combo.addItems(cats)
        self.cat_combo.setCurrentText(self.tool.get("category", "Custom"))
        layout.addRow("Category:", self.cat_combo)

        self.notes_edit = QLineEdit(self.tool.get("notes", ""))
        layout.addRow("Notes:", self.notes_edit)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)

        wrapper = QWidget()
        wrapper.setLayout(btn_row)
        layout.addRow(wrapper)

    def _save(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Tool name required.")
            return
        self.tool["name"]     = name
        self.tool["url"]      = self.url_edit.text().strip()
        self.tool["category"] = self.cat_combo.currentText().strip() or "Custom"
        self.tool["notes"]    = self.notes_edit.text()
        self.callback(self.tool, self.is_new)
        self.accept()


# ----------------------------------------------------------------------
# Settings Dialog
# ----------------------------------------------------------------------
class SettingsDialog(QDialog):
    def __init__(self, parent: QWidget, data: dict, callback):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(360)
        self.data     = data
        self.callback = callback
        self.settings = data["settings"].copy()
        self._build()

    def _build(self) -> None:
        layout = QFormLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Default browser
        browsers = [b["name"] for b in self.data.get("browsers", [])]
        if not browsers:
            browsers = ["chrome", "edge", "firefox"]
        self.browser_combo = QComboBox()
        self.browser_combo.addItems(browsers)
        current_browser = self.settings.get("default_browser", DEFAULT_BROWSER)
        if current_browser in browsers:
            self.browser_combo.setCurrentText(current_browser)
        layout.addRow("Default Browser:", self.browser_combo)

        # Private mode default
        self.private_cb = QCheckBox("Default Private Mode")
        self.private_cb.setChecked(self.settings.get("default_private", False))
        layout.addRow(self.private_cb)

        # Theme
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        self.theme_combo.setCurrentText(self.settings.get("theme", "dark"))
        layout.addRow("Theme:", self.theme_combo)

        # Always on top
        self.top_cb = QCheckBox("Always on Top")
        self.top_cb.setChecked(self.settings.get("always_on_top", False))
        layout.addRow(self.top_cb)

        # Start minimized
        self.minimize_cb = QCheckBox("Start Minimized to Taskbar")
        self.minimize_cb.setChecked(self.settings.get("start_minimized", False))
        layout.addRow(self.minimize_cb)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)

        wrapper = QWidget()
        wrapper.setLayout(btn_row)
        layout.addRow(wrapper)

    def _save(self) -> None:
        self.settings["default_browser"] = self.browser_combo.currentText()
        self.settings["default_private"] = self.private_cb.isChecked()
        self.settings["theme"]            = self.theme_combo.currentText()
        self.settings["always_on_top"]    = self.top_cb.isChecked()
        self.settings["start_minimized"]  = self.minimize_cb.isChecked()
        self.data["settings"].update(self.settings)
        self.callback()
        self.accept()


# ----------------------------------------------------------------------
# Dark / Light Stylesheets
# ----------------------------------------------------------------------
DARK_QSS = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI";
}
QFrame#ToolCard {
    background-color: #2e2e3e;
    border: 1px solid #45475a;
    border-radius: 6px;
}
QFrame#ToolCard:hover { border: 1px solid #89b4fa; }
QLabel#IconLabel {
    background-color: #45475a;
    border-radius: 4px;
    color: #cdd6f4;
}
QLabel#CardName    { color: #cdd6f4; }
QLabel#CardCategory{ color: #a6adc8; }
QPushButton {
    background-color: #45475a;
    color: #cdd6f4;
    border: 1px solid #585b70;
    border-radius: 4px;
    padding: 4px 12px;
    font-family: "Segoe UI";
}
QPushButton:hover   { background-color: #585b70; }
QPushButton:pressed { background-color: #313244; }
QPushButton#CardButton { padding: 3px 8px; font-size: 11px; }
QLineEdit {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}
QLineEdit:focus { border: 1px solid #89b4fa; }
QComboBox {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 4px 8px;
}
QComboBox::drop-down  { border: none; }
QComboBox QAbstractItemView {
    background-color: #313244;
    color: #cdd6f4;
    selection-background-color: #585b70;
    border: 1px solid #45475a;
}
QListWidget {
    background-color: #313244;
    color: #cdd6f4;
    border: none;
    font-size: 10px;
}
QListWidget::item:selected { background-color: #585b70; color: #cdd6f4; }
QListWidget::item:hover    { background-color: #45475a; }
QScrollBar:vertical {
    background: #313244; width: 10px; border-radius: 5px;
}
QScrollBar::handle:vertical { background: #585b70; border-radius: 5px; min-height: 20px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #313244; height: 10px; border-radius: 5px;
}
QScrollBar::handle:horizontal { background: #585b70; border-radius: 5px; min-width: 20px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QGroupBox {
    border: 1px solid #45475a;
    border-radius: 4px;
    margin-top: 8px;
    color: #cdd6f4;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px; padding: 0 3px;
}
QCheckBox { color: #cdd6f4; }
QSplitter::handle { background-color: #45475a; }
QMenu {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
}
QMenu::item:selected { background-color: #585b70; }
QMenu::separator { height: 1px; background: #45475a; margin: 3px 0; }
QDialog { background-color: #1e1e2e; }
QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
QToolTip {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    padding: 4px;
}
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    color: #45475a;
}
"""

LIGHT_QSS = """
QMainWindow, QWidget {
    background-color: #f5f5f5;
    color: #11111b;
    font-family: "Segoe UI";
}
QFrame#ToolCard {
    background-color: #ffffff;
    border: 1px solid #d0d0d0;
    border-radius: 6px;
}
QFrame#ToolCard:hover { border: 1px solid #4a9eff; }
QLabel#IconLabel {
    background-color: #e0e0e0;
    border-radius: 4px;
    color: #11111b;
}
QLabel#CardName    { color: #11111b; }
QLabel#CardCategory{ color: #555555; }
QPushButton {
    background-color: #e0e0e0;
    color: #11111b;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    padding: 4px 12px;
    font-family: "Segoe UI";
}
QPushButton:hover   { background-color: #d0d0d0; }
QPushButton:pressed { background-color: #b8b8b8; }
QPushButton#CardButton { padding: 3px 8px; font-size: 11px; }
QLineEdit {
    background-color: #ffffff;
    color: #11111b;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}
QLineEdit:focus { border: 1px solid #4a9eff; }
QComboBox {
    background-color: #ffffff;
    color: #11111b;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    padding: 4px 8px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #11111b;
    selection-background-color: #d0d0d0;
    border: 1px solid #c0c0c0;
}
QListWidget {
    background-color: #ffffff;
    color: #11111b;
    border: 1px solid #c0c0c0;
    font-size: 10px;
}
QListWidget::item:selected { background-color: #d0d0d0; color: #11111b; }
QListWidget::item:hover    { background-color: #ebebeb; }
QScrollBar:vertical {
    background: #e8e8e8; width: 10px; border-radius: 5px;
}
QScrollBar::handle:vertical { background: #b0b0b0; border-radius: 5px; min-height: 20px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #e8e8e8; height: 10px; border-radius: 5px;
}
QScrollBar::handle:horizontal { background: #b0b0b0; border-radius: 5px; min-width: 20px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QGroupBox {
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    margin-top: 8px;
    color: #11111b;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px; padding: 0 3px;
}
QCheckBox { color: #11111b; }
QSplitter::handle { background-color: #c0c0c0; }
QMenu {
    background-color: #ffffff;
    color: #11111b;
    border: 1px solid #c0c0c0;
}
QMenu::item:selected { background-color: #d0d0d0; }
QMenu::separator { height: 1px; background: #c0c0c0; margin: 3px 0; }
QDialog { background-color: #f5f5f5; }
QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
QToolTip {
    background-color: #ffffe0;
    color: #11111b;
    border: 1px solid #c0c0c0;
    padding: 4px;
}
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    color: #c0c0c0;
}
"""


# ----------------------------------------------------------------------
# Main Application Window
# ----------------------------------------------------------------------
class AILauncherHub(QMainWindow):

    CARD_COLS = 4  # cards per row in grid

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1200, 750)
        self.setMinimumSize(900, 550)

        self.browsers: List[Dict[str, Any]] = detect_browsers()
        self.icon_cache = IconCache()
        self._right_click_tool: Optional[dict] = None
        self._card_widgets: List[ToolCard] = []

        self.data: Dict[str, Any] = {
            "tools":    [],
            "favorites":[],
            "recent":  [],
            "settings": {
                "default_browser":  self._get_default_browser_name(),
                "default_private":  False,
                "theme":            "dark",
                "always_on_top":    False,
                "start_minimized":  False,
                "last_profile":     "",
            },
        }
        # browsers stored temporarily for Settings dialog; excluded from JSON
        self.data["browsers"] = self.browsers

        DATA_DIR.mkdir(parents=True, exist_ok=True)

        self._load_data()
        self._build_ui()
        self._apply_settings()
        self._refresh_lists()

        # Ctrl+Shift+L — toggle window visibility
        shortcut = QShortcut(QKeySequence("Ctrl+Shift+L"), self)
        shortcut.activated.connect(self._toggle_visibility)

        if self.data["settings"].get("start_minimized", False):
            self.showMinimized()

    # ------------------------------------------------------------------ #
    # Data Persistence                                                     #
    # ------------------------------------------------------------------ #
    def _load_data(self) -> None:
        if DATA_FILE.exists():
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                self.data["settings"].update(loaded.get("settings", {}))
                self.data["favorites"] = loaded.get("favorites", [])
                self.data["recent"]    = loaded.get("recent", [])[:MAX_RECENT]

                saved_tools    = loaded.get("tools", [])
                default_ids    = {t["id"] for t in DEFAULT_TOOLS}
                user_tools     = [t for t in saved_tools if t["id"] not in default_ids]
                saved_default_map = {t["id"]: t for t in saved_tools if t["id"] in default_ids}

                merged = []
                for d in DEFAULT_TOOLS:
                    merged.append(saved_default_map.get(d["id"], d))
                merged.extend(user_tools)
                self.data["tools"] = merged
            except Exception:
                self.data["tools"] = list(DEFAULT_TOOLS)
        else:
            self.data["tools"] = list(DEFAULT_TOOLS)

    def _save_data(self) -> None:
        try:
            payload = {k: v for k, v in self.data.items() if k != "browsers"}
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception as e:
            print(f"Save error: {e}")

    def _get_default_browser_name(self) -> str:
        return self.browsers[0]["name"] if self.browsers else DEFAULT_BROWSER

    # ------------------------------------------------------------------ #
    # Settings Application                                                 #
    # ------------------------------------------------------------------ #
    def _apply_settings(self) -> None:
        s = self.data["settings"]

        # Always-on-top — must hide/show to apply on Windows
        flag = Qt.WindowType.WindowStaysOnTopHint
        if s.get("always_on_top", False):
            self.setWindowFlag(flag, True)
        else:
            self.setWindowFlag(flag, False)
        self.show()

        theme = s.get("theme", "dark")
        QApplication.instance().setStyleSheet(DARK_QSS if theme == "dark" else LIGHT_QSS)

    # ------------------------------------------------------------------ #
    # UI Construction                                                      #
    # ------------------------------------------------------------------ #
    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Toolbar ──────────────────────────────────────────────────── #
        toolbar = QWidget()
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(8, 6, 8, 6)
        tb_layout.setSpacing(6)

        search_icon = QLabel("🔍")
        search_icon.setFont(QFont("Segoe UI", 14))
        tb_layout.addWidget(search_icon)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search tools…")
        self.search_edit.setFont(QFont("Segoe UI", 12))
        self.search_edit.setMinimumWidth(180)
        self.search_edit.textChanged.connect(self._on_search)
        tb_layout.addWidget(self.search_edit, stretch=1)

        tb_layout.addWidget(QLabel("Browser:"))
        self.browser_combo = QComboBox()
        self.browser_combo.addItems([b["name"] for b in self.browsers])
        self.browser_combo.setCurrentText(
            self.data["settings"].get("default_browser", self._get_default_browser_name())
        )
        self.browser_combo.setMinimumWidth(100)
        self.browser_combo.currentTextChanged.connect(self._on_browser_changed)
        tb_layout.addWidget(self.browser_combo)

        tb_layout.addWidget(QLabel("Profile:"))
        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(120)
        tb_layout.addWidget(self.profile_combo)

        self.private_cb = QCheckBox("Private")
        self.private_cb.setChecked(self.data["settings"].get("default_private", False))
        tb_layout.addWidget(self.private_cb)

        # must be called after profile_combo and private_cb exist
        self._update_profile_list()

        tb_layout.addStretch()

        new_btn = QPushButton("➕ New Tool")
        new_btn.clicked.connect(self._add_new_tool)
        tb_layout.addWidget(new_btn)

        settings_btn = QPushButton("⚙ Settings")
        settings_btn.clicked.connect(self._open_settings)
        tb_layout.addWidget(settings_btn)

        import_btn = QPushButton("📥 Import")
        import_btn.clicked.connect(self._import_data)
        tb_layout.addWidget(import_btn)

        export_btn = QPushButton("📤 Export")
        export_btn.clicked.connect(self._export_data)
        tb_layout.addWidget(export_btn)

        root_layout.addWidget(toolbar)

        sep1 = QFrame(); sep1.setFrameShape(QFrame.Shape.HLine)
        root_layout.addWidget(sep1)

        # ── Favorites Bar ─────────────────────────────────────────────── #
        self.fav_bar_widget = QWidget()
        self.fav_bar_layout = QHBoxLayout(self.fav_bar_widget)
        self.fav_bar_layout.setContentsMargins(8, 4, 8, 4)
        self.fav_bar_layout.setSpacing(4)
        root_layout.addWidget(self.fav_bar_widget)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine)
        root_layout.addWidget(sep2)

        # ── Recently Opened ───────────────────────────────────────────── #
        self.recent_group = QGroupBox("Recently Opened")
        recent_outer = QHBoxLayout(self.recent_group)
        recent_outer.setContentsMargins(4, 4, 4, 4)

        recent_scroll = QScrollArea()
        recent_scroll.setWidgetResizable(True)
        recent_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        recent_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        recent_scroll.setFixedHeight(46)

        self.recent_inner = QWidget()
        self.recent_layout = QHBoxLayout(self.recent_inner)
        self.recent_layout.setContentsMargins(2, 2, 2, 2)
        self.recent_layout.setSpacing(4)
        self.recent_layout.addStretch()

        recent_scroll.setWidget(self.recent_inner)
        recent_outer.addWidget(recent_scroll)
        root_layout.addWidget(self.recent_group)

        # ── Main Splitter: Sidebar | Tools Grid ──────────────────────── #
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Sidebar – category list
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(4, 4, 4, 4)
        sidebar_layout.setSpacing(2)

        cat_hdr = QLabel("Categories")
        cat_hdr.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        sidebar_layout.addWidget(cat_hdr)

        self.category_list = QListWidget()
        self.category_list.setMinimumWidth(130)
        self.category_list.currentItemChanged.connect(self._on_category_select)
        sidebar_layout.addWidget(self.category_list)

        sidebar.setMinimumWidth(130)
        sidebar.setMaximumWidth(220)
        self.splitter.addWidget(sidebar)

        # Tools area – scrollable grid
        tools_outer = QWidget()
        tools_outer_layout = QVBoxLayout(tools_outer)
        tools_outer_layout.setContentsMargins(0, 0, 0, 0)

        self.tools_scroll = QScrollArea()
        self.tools_scroll.setWidgetResizable(True)

        self.tools_container = QWidget()
        self.tools_grid = QGridLayout(self.tools_container)
        self.tools_grid.setContentsMargins(10, 10, 10, 10)
        self.tools_grid.setSpacing(10)
        self.tools_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.tools_scroll.setWidget(self.tools_container)
        tools_outer_layout.addWidget(self.tools_scroll)
        self.splitter.addWidget(tools_outer)

        self.splitter.setSizes([160, 1040])
        root_layout.addWidget(self.splitter, stretch=1)

        # ── Context Menu ─────────────────────────────────────────────── #
        self.context_menu = QMenu(self)
        self._build_context_menu()

    def _build_context_menu(self) -> None:
        a = self.context_menu.addAction("Open (Normal)")
        a.triggered.connect(lambda: self._launch_tool(self._right_click_tool, private=False))

        a = self.context_menu.addAction("Open Private/Incognito")
        a.triggered.connect(lambda: self._launch_tool(self._right_click_tool, private=True))

        self.context_menu.addSeparator()

        a = self.context_menu.addAction("Copy URL")
        a.triggered.connect(self._copy_url)

        a = self.context_menu.addAction("Toggle Favorite")
        a.triggered.connect(lambda: self._toggle_favorite(self._right_click_tool))

        a = self.context_menu.addAction("Pin/Unpin")
        a.triggered.connect(lambda: self._toggle_pin(self._right_click_tool))

        self.context_menu.addSeparator()

        a = self.context_menu.addAction("Move Up")
        a.triggered.connect(lambda: self._move_tool(-1))

        a = self.context_menu.addAction("Move Down")
        a.triggered.connect(lambda: self._move_tool(1))

        self.context_menu.addSeparator()

        a = self.context_menu.addAction("Edit Tool")
        a.triggered.connect(lambda: self._edit_tool(self._right_click_tool))

        a = self.context_menu.addAction("Delete Tool")
        a.triggered.connect(lambda: self._delete_tool(self._right_click_tool))

    def show_context_menu(self, tool: dict, global_pos: QPoint) -> None:
        """Called by ToolCard (and favorites bar buttons) to pop the context menu."""
        self._right_click_tool = tool
        self.context_menu.exec(global_pos)

    # ------------------------------------------------------------------ #
    # Profile / Browser helpers                                            #
    # ------------------------------------------------------------------ #
    def _update_profile_list(self) -> None:
        browser_name = self.browser_combo.currentText()
        browser = next((b for b in self.browsers if b["name"] == browser_name), None)
        self.profile_combo.clear()
        if browser and browser.get("profiles"):
            profiles = browser["profiles"]
            self.profile_combo.addItems(profiles)
            last = self.data["settings"].get("last_profile", "")
            if last in profiles:
                self.profile_combo.setCurrentText(last)
        has_private = bool(browser and browser.get("private_flag"))
        self.private_cb.setEnabled(has_private)
        if not has_private:
            self.private_cb.setChecked(False)

    def _on_browser_changed(self, _text: str = "") -> None:
        self._update_profile_list()

    # ------------------------------------------------------------------ #
    # Refresh / Population                                                 #
    # ------------------------------------------------------------------ #
    def _refresh_lists(self) -> None:
        self._refresh_categories()
        self._refresh_tools_list()
        self._refresh_favorites_bar()
        self._refresh_recent()
        self._apply_settings()

    def _refresh_categories(self) -> None:
        cats = sorted({tool["category"] for tool in self.data["tools"]})
        self.category_list.blockSignals(True)
        self.category_list.clear()
        self.category_list.addItem("All")
        for cat in cats:
            self.category_list.addItem(cat)
        self.category_list.setCurrentRow(0)
        self.category_list.blockSignals(False)

    def _get_selected_category(self) -> str:
        item = self.category_list.currentItem()
        return item.text() if item else "All"

    def _on_category_select(self, current, previous=None) -> None:
        self._refresh_tools_list()

    def _on_search(self, _text: str = "") -> None:
        self._refresh_tools_list()

    def _refresh_tools_list(self) -> None:
        # Clear grid
        while self.tools_grid.count():
            item = self.tools_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._card_widgets.clear()

        search = self.search_edit.text().lower()
        cat    = self._get_selected_category()
        tools  = self.data["tools"]

        # Pinned tools first, then rest
        pinned_first = sorted(tools, key=lambda t: not t.get("pinned", False))

        shown = []
        for tool in pinned_first:
            if search and (
                search not in tool["name"].lower()
                and search not in tool.get("notes", "").lower()
                and search not in tool.get("url",   "").lower()
            ):
                continue
            if cat != "All" and tool["category"] != cat:
                continue
            shown.append(tool)

        for i, tool in enumerate(shown):
            is_fav = tool["id"] in self.data["favorites"]
            card = ToolCard(tool, is_fav, self._launch_tool, self._toggle_favorite)
            card.parent_hub = self
            self.tools_grid.addWidget(card, i // self.CARD_COLS, i % self.CARD_COLS)
            self._card_widgets.append(card)

            # Async favicon
            if tool.get("url"):
                cached = self.icon_cache.get_icon(tool["url"])
                if cached:
                    card.set_icon(cached)
                else:
                    self.icon_cache.load_icon_async(
                        tool["url"],
                        lambda url, pix, c=card: self._on_icon_ready(url, pix, c),
                    )

    def _on_icon_ready(self, url: str, pixmap: Optional[QPixmap], card: ToolCard) -> None:
        # Already on main thread (QTimer.singleShot delivered us here)
        if pixmap and not pixmap.isNull() and not card.isHidden():
            card.set_icon(pixmap)

    # ── Favorites Bar ─────────────────────────────────────────────────── #
    def _refresh_favorites_bar(self) -> None:
        while self.fav_bar_layout.count():
            item = self.fav_bar_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        fav_tools = [t for t in self.data["tools"] if t["id"] in self.data["favorites"]]

        if not fav_tools:
            lbl = QLabel("⭐ Favorites: none yet")
            lbl.setFont(QFont("Segoe UI", 9))
            self.fav_bar_layout.addWidget(lbl)
        else:
            for tool in fav_tools:
                btn = QPushButton(f"★ {tool['name']}")
                btn.setFont(QFont("Segoe UI", 9))
                btn.clicked.connect(lambda _checked, t=tool: self._launch_tool(t))
                # Right-click on fav bar button
                btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                btn.customContextMenuRequested.connect(
                    lambda pos, t=tool, b=btn: self.show_context_menu(t, b.mapToGlobal(pos))
                )
                self.fav_bar_layout.addWidget(btn)

        self.fav_bar_layout.addStretch()

    # ── Recently Opened ────────────────────────────────────────────────── #
    def _refresh_recent(self) -> None:
        while self.recent_layout.count():
            item = self.recent_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        recent = self.data["recent"][:10]
        if not recent:
            lbl = QLabel("No recent items")
            lbl.setFont(QFont("Segoe UI", 9))
            self.recent_layout.addWidget(lbl)
        else:
            for r in recent:
                ts = r.get("timestamp", "")
                try:
                    time_str = datetime.fromisoformat(ts).strftime("%H:%M")
                except Exception:
                    time_str = ""
                btn = QPushButton(f"🕒 {r['name']} ({time_str})")
                btn.setFont(QFont("Segoe UI", 9))
                btn.setToolTip(f"Opened: {ts}\nURL: {r.get('url', '')}")
                btn.clicked.connect(lambda _checked, item=r: self._launch_recent(item))
                self.recent_layout.addWidget(btn)

        self.recent_layout.addStretch()

    def _launch_recent(self, recent_item: dict) -> None:
        tool = next((t for t in self.data["tools"] if t["id"] == recent_item["id"]), None)
        if tool:
            self._launch_tool(tool)
        else:
            webbrowser.open(recent_item["url"])

    # ------------------------------------------------------------------ #
    # Tool Actions                                                         #
    # ------------------------------------------------------------------ #
    def _launch_tool(self, tool: Optional[dict], private: Optional[bool] = None) -> None:
        if not tool:
            return
        browser_name = self.browser_combo.currentText()
        if private is None:
            private = self.private_cb.isChecked()
        browser = next((b for b in self.browsers if b["name"] == browser_name), None)
        url = tool.get("url", "")

        if not url:
            QMessageBox.critical(self, "Error", "No URL defined for this tool.")
            return

        # Warn if private requested but unsupported
        if private and browser and not browser.get("private_flag"):
            QMessageBox.warning(
                self,
                "Private Mode Unsupported",
                f"{browser.get('display_name', browser_name)} does not support private/incognito mode. "
                "Opening normally.",
            )
            private = False

        try:
            if browser and browser.get("path"):
                args = [browser["path"]]
                profile = self.profile_combo.currentText().strip()
                if profile and browser["name"] in ("chrome", "edge", "brave", "vivaldi"):
                    args.append(f"--profile-directory={profile}")
                if private and browser.get("private_flag"):
                    args.extend(browser["private_flag"])
                args.append(url)
                subprocess.Popen(args, shell=False)
            else:
                if private and browser and browser.get("private_flag"):
                    subprocess.Popen([browser["path"]] + browser["private_flag"] + [url])
                else:
                    webbrowser.open(url)
        except Exception as e:
            QMessageBox.critical(self, "Launch Error", f"Could not open {url}\nError: {e}")
            return

        self._add_recent(tool)
        self._save_data()

    def _add_recent(self, tool: dict) -> None:
        recent = [r for r in self.data["recent"] if r["id"] != tool["id"]]
        recent.insert(0, {
            "id":        tool["id"],
            "name":      tool["name"],
            "url":       tool["url"],
            "timestamp": datetime.now().isoformat(),
        })
        self.data["recent"] = recent[:MAX_RECENT]
        self._refresh_recent()

    def _toggle_favorite(self, tool: Optional[dict]) -> None:
        if not tool:
            return
        if tool["id"] in self.data["favorites"]:
            self.data["favorites"].remove(tool["id"])
        else:
            self.data["favorites"].append(tool["id"])
        self._refresh_lists()
        self._save_data()

    def _toggle_pin(self, tool: Optional[dict]) -> None:
        if not tool:
            return
        tool["pinned"] = not tool.get("pinned", False)
        self._refresh_lists()
        self._save_data()

    def _copy_url(self) -> None:
        if self._right_click_tool:
            QApplication.clipboard().setText(self._right_click_tool["url"])
            QMessageBox.information(self, "Copied", f"URL copied: {self._right_click_tool['url']}")

    def _move_tool(self, direction: int) -> None:
        if not self._right_click_tool:
            return
        tools = self.data["tools"]
        idx = next((i for i, t in enumerate(tools) if t["id"] == self._right_click_tool["id"]), None)
        if idx is None:
            return
        new_idx = idx + direction
        if 0 <= new_idx < len(tools):
            tools.insert(new_idx, tools.pop(idx))
            self._refresh_tools_list()
            self._save_data()

    # ------------------------------------------------------------------ #
    # Tool Management                                                      #
    # ------------------------------------------------------------------ #
    def _add_new_tool(self) -> None:
        new_tool = {
            "id":       f"custom_{int(time.time())}",
            "name":     "",
            "url":      "",
            "category": "Custom",
            "icon":     "",
            "notes":    "",
            "pinned":   False,
        }
        dlg = ToolEditor(self, new_tool, self.data["tools"], self._on_tool_edited, is_new=True)
        dlg.exec()

    def _edit_tool(self, tool: Optional[dict] = None) -> None:
        if tool is None:
            tool = self._right_click_tool
        if not tool:
            return
        dlg = ToolEditor(self, tool, self.data["tools"], self._on_tool_edited)
        dlg.exec()

    def _on_tool_edited(self, updated_tool: dict, is_new: bool = False) -> None:
        if is_new:
            self.data["tools"].append(updated_tool)
        else:
            idx = next(
                (i for i, t in enumerate(self.data["tools"]) if t["id"] == updated_tool["id"]),
                None,
            )
            if idx is not None:
                self.data["tools"][idx] = updated_tool
        self._refresh_lists()
        self._save_data()

    def _delete_tool(self, tool: Optional[dict]) -> None:
        if not tool:
            return
        reply = QMessageBox.question(
            self, "Delete", f"Remove '{tool['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.data["tools"]   = [t for t in self.data["tools"]   if t["id"] != tool["id"]]
            self.data["recent"]  = [r for r in self.data["recent"]   if r["id"] != tool["id"]]
            if tool["id"] in self.data["favorites"]:
                self.data["favorites"].remove(tool["id"])
            self._refresh_lists()
            self._save_data()

    # ------------------------------------------------------------------ #
    # Import / Export                                                      #
    # ------------------------------------------------------------------ #
    def _import_data(self) -> None:
        filepath, _ = QFileDialog.getOpenFileName(self, "Import", "", "JSON Files (*.json)")
        if filepath:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    imported = json.load(f)
                self.data["tools"]     = imported.get("tools",     self.data["tools"])
                self.data["favorites"] = imported.get("favorites", self.data["favorites"])
                self.data["recent"]    = imported.get("recent",    self.data["recent"])
                self.data["settings"].update(imported.get("settings", {}))
                self._refresh_lists()
                self._save_data()
                QMessageBox.information(self, "Import", "Data imported successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Import Error", str(e))

    def _export_data(self) -> None:
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export", "launcher_data.json", "JSON Files (*.json)"
        )
        if filepath:
            try:
                payload = {k: v for k, v in self.data.items() if k != "browsers"}
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2)
                QMessageBox.information(self, "Export", "Data exported successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    # ------------------------------------------------------------------ #
    # Settings Dialog                                                      #
    # ------------------------------------------------------------------ #
    def _open_settings(self) -> None:
        self.data["browsers"] = self.browsers
        dlg = SettingsDialog(self, self.data, self._on_settings_changed)
        dlg.exec()

    def _on_settings_changed(self) -> None:
        self._apply_settings()
        self._refresh_lists()
        self._save_data()

    # ------------------------------------------------------------------ #
    # Visibility Toggle (Ctrl+Shift+L)                                    #
    # ------------------------------------------------------------------ #
    def _toggle_visibility(self) -> None:
        if self.isVisible() and not self.isMinimized():
            self.hide()
        else:
            self.showNormal()
            self.activateWindow()
            self.raise_()

    # ------------------------------------------------------------------ #
    # Window Close                                                         #
    # ------------------------------------------------------------------ #
    def closeEvent(self, event) -> None:
        self._save_data()
        event.accept()


# ----------------------------------------------------------------------
# Entry Point
# ----------------------------------------------------------------------
def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")  # consistent cross-platform base
    window = AILauncherHub()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

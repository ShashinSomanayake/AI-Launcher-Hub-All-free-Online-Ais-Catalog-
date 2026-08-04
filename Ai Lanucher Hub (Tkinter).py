"""
AI Launcher Hub — A fast, searchable launcher for AI websites and developer tools.
Optimised for daily use by software engineers on Windows.
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
from tkinter import (Tk, Toplevel, Frame, Label, Button, Entry, Listbox,
                     Menu, messagebox, filedialog, StringVar, IntVar, BooleanVar,
                     ttk, Event)
from tkinter.font import Font
from typing import List, Dict, Optional, Any

# Optional favicon support
try:
    from PIL import Image, ImageTk
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
DEFAULT_BROWSER = "chrome"  # default if detected, else first found

# Built-in AI tools
DEFAULT_TOOLS = [
    {"id": "chatgpt", "name": "ChatGPT", "url": "https://chat.openai.com", "category": "Chatbots", "icon": "", "notes": "", "pinned": False},
    {"id": "gemini", "name": "Gemini", "url": "https://gemini.google.com", "category": "Chatbots", "icon": "", "notes": "", "pinned": False},
    {"id": "claude", "name": "Claude", "url": "https://claude.ai", "category": "Chatbots", "icon": "", "notes": "", "pinned": False},
    {"id": "perplexity", "name": "Perplexity AI", "url": "https://www.perplexity.ai", "category": "Research", "icon": "", "notes": "", "pinned": False},
    {"id": "midjourney", "name": "Midjourney", "url": "https://www.midjourney.com", "category": "Image Generation", "icon": "", "notes": "", "pinned": False},
    {"id": "dalle", "name": "DALL·E", "url": "https://labs.openai.com", "category": "Image Generation", "icon": "", "notes": "", "pinned": False},
    {"id": "copilot", "name": "GitHub Copilot", "url": "https://github.com/features/copilot", "category": "Coding", "icon": "", "notes": "", "pinned": False},
    {"id": "codewhisper", "name": "CodeWhisperer", "url": "https://aws.amazon.com/codewhisperer/", "category": "Coding", "icon": "", "notes": "", "pinned": False},
    {"id": "bard", "name": "Bard", "url": "https://bard.google.com", "category": "Chatbots", "icon": "", "notes": "", "pinned": False},
    {"id": "hugchat", "name": "HuggingChat", "url": "https://huggingface.co/chat", "category": "Chatbots", "icon": "", "notes": "", "pinned": False},
    {"id": "phind", "name": "Phind", "url": "https://www.phind.com", "category": "Research", "icon": "", "notes": "", "pinned": False},
    {"id": "jasper", "name": "Jasper", "url": "https://www.jasper.ai", "category": "Writing", "icon": "", "notes": "", "pinned": False},
    {"id": "writesonic", "name": "Writesonic", "url": "https://writesonic.com", "category": "Writing", "icon": "", "notes": "", "pinned": False},
    {"id": "runway", "name": "RunwayML", "url": "https://runwayml.com", "category": "Media", "icon": "", "notes": "", "pinned": False},
    {"id": "kaiber", "name": "Kaiber", "url": "https://kaiber.ai", "category": "Media", "icon": "", "notes": "", "pinned": False},
]

PRIVATE_FLAGS = {
    "chrome": ["--incognito"],
    "edge": ["--inprivate"],
    "firefox": ["--private-window"],
    "brave": ["--incognito"],
    "opera": ["--private"],
    "vivaldi": ["--incognito"],
}

# ----------------------------------------------------------------------
# Browser Detection (Windows)
# ----------------------------------------------------------------------
def detect_browsers() -> List[Dict[str, Any]]:
    """Detect installed browsers using registry and known paths."""
    browsers = []
    known = [
        ("chrome", "chrome.exe", "Google Chrome", "Google\\Chrome\\Application"),
        ("edge", "msedge.exe", "Microsoft Edge", "Microsoft\\Edge\\Application"),
        ("firefox", "firefox.exe", "Mozilla Firefox", "Mozilla Firefox"),
        ("brave", "brave.exe", "Brave", "BraveSoftware\\Brave-Browser\\Application"),
        ("opera", "launcher.exe", "Opera Stable", "Opera\\launcher.exe"),
        ("vivaldi", "vivaldi.exe", "Vivaldi", "Vivaldi\\Application"),
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
                            install_loc = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                        except:
                            continue
                        for bname, bexe, substr, path_parts in known:
                            if substr.lower() in display_name.lower():
                                exe_path = Path(install_loc) / bexe if bexe == "launcher.exe" else Path(install_loc) / bexe
                                if exe_path.exists():
                                    browsers.append({
                                        "name": bname,
                                        "display_name": display_name,
                                        "path": str(exe_path),
                                        "private_flag": PRIVATE_FLAGS.get(bname, []),
                                        "profiles": _detect_profiles(bname),
                                    })
                except:
                    pass
    except ImportError:
        pass

    # Fallback: check common Program Files paths
    program_files = [os.environ.get("ProgramFiles", "C:\\Program Files"),
                     os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")]
    for bname, bexe, substr, path_parts in known:
        if not any(b["name"] == bname for b in browsers):
            for pf in program_files:
                exe_path = Path(pf) / path_parts / bexe
                if exe_path.exists():
                    browsers.append({
                        "name": bname,
                        "display_name": bname.title(),
                        "path": str(exe_path),
                        "private_flag": PRIVATE_FLAGS.get(bname, []),
                        "profiles": _detect_profiles(bname),
                    })
                    break

    # Ensure we have at least the default web browser
    try:
        default = webbrowser.get().name
        if not any(b["name"] == default.lower() for b in browsers):
            browsers.append({
                "name": default.lower(),
                "display_name": default,
                "path": "",
                "private_flag": [],
                "profiles": [],
            })
    except:
        pass

    return browsers

def _detect_profiles(browser_name: str) -> List[str]:
    """Return list of profile directory names for Chromium-based browsers."""
    if browser_name not in ("chrome", "edge", "brave", "vivaldi"):
        return []
    base_map = {
        "chrome": os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data"),
        "edge": os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data"),
        "brave": os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data"),
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
# Utility class for async favicon loading
# ----------------------------------------------------------------------
class IconCache:
    def __init__(self):
        self._cache = {}  # url -> PhotoImage or None
        self._lock = threading.Lock()

    def get_icon(self, url: str, size: tuple = DEFAULT_FAVICON_SIZE) -> Optional[Any]:
        with self._lock:
            return self._cache.get(url)

    def load_icon_async(self, url: str, callback, size: tuple = DEFAULT_FAVICON_SIZE):
        def _fetch():
            if HAS_PIL:
                try:
                    favicon_url = f"https://www.google.com/s2/favicons?domain={url.split('/')[2]}&sz={size[0]}"
                    req = Request(favicon_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urlopen(req, timeout=5) as u:
                        raw = u.read()
                    img = Image.open(BytesIO(raw)).resize(size, Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    with self._lock:
                        self._cache[url] = photo
                    callback(photo)
                except Exception:
                    callback(None)
            else:
                callback(None)
        threading.Thread(target=_fetch, daemon=True).start()

# ----------------------------------------------------------------------
# Simple ToolTip for notes
# ----------------------------------------------------------------------
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, "bbox") else (0,0,0,0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tip_window = tw = Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = Label(tw, text=self.text, justify="left",
                      background="#ffffe0", relief="solid", borderwidth=1,
                      font=("Segoe UI", 9), wraplength=250)
        label.pack()

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

# ----------------------------------------------------------------------
# Main Application Class
# ----------------------------------------------------------------------
class AILauncherHub:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1200x750")
        self.root.minsize(900, 550)
        self.browsers = detect_browsers()
        self.icon_cache = IconCache()
        self.data = {
            "tools": [],
            "favorites": [],
            "recent": [],
            "settings": {
                "default_browser": self._get_default_browser_name(),
                "default_private": False,
                "theme": "dark",
                "always_on_top": False,
                "start_minimized": False,
                "last_profile": "",
            }
        }
        self.data_dir = DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.save_file = DATA_FILE

        self._load_data()
        self._apply_settings()
        self._build_ui()
        self._refresh_lists()

        # Global hotkey: Ctrl+Shift+L toggles window visibility
        self.root.bind_all("<Control-Shift-L>", self._toggle_visibility)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Start minimized if setting says so
        if self.data["settings"].get("start_minimized", False):
            self.root.iconify()

    # ------- Data Persistence -------
    def _load_data(self):
        if self.save_file.exists():
            try:
                with open(self.save_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                self.data["settings"].update(loaded.get("settings", {}))
                self.data["favorites"] = loaded.get("favorites", [])
                self.data["recent"] = loaded.get("recent", [])[:MAX_RECENT]
                saved_tools = loaded.get("tools", [])
                default_ids = {t["id"] for t in DEFAULT_TOOLS}
                user_tools = [t for t in saved_tools if t["id"] not in default_ids]
                saved_default_map = {t["id"]: t for t in saved_tools if t["id"] in default_ids}
                merged = []
                for d in DEFAULT_TOOLS:
                    if d["id"] in saved_default_map:
                        merged.append(saved_default_map[d["id"]])
                    else:
                        merged.append(d)
                merged.extend(user_tools)
                self.data["tools"] = merged
            except Exception:
                self.data["tools"] = list(DEFAULT_TOOLS)
        else:
            self.data["tools"] = list(DEFAULT_TOOLS)

    def _save_data(self):
        try:
            with open(self.save_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Save error: {e}")

    def _get_default_browser_name(self) -> str:
        if self.browsers:
            return self.browsers[0]["name"]
        return DEFAULT_BROWSER

    # ------- Settings Application -------
    def _apply_settings(self):
        s = self.data["settings"]
        if s.get("always_on_top", False):
            self.root.attributes("-topmost", True)
        else:
            self.root.attributes("-topmost", False)
        theme = s.get("theme", "dark")
        if theme == "dark":
            self._apply_dark_theme()
        else:
            self._apply_light_theme()

    def _apply_dark_theme(self):
        self.root.configure(bg="#1e1e2e")
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", background="#1e1e2e", foreground="#cdd6f4",
                        fieldbackground="#313244", borderwidth=1)
        style.configure("TFrame", background="#1e1e2e")
        style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4")
        style.configure("TButton", background="#45475a", foreground="#cdd6f4",
                        borderwidth=1, focusthickness=0)
        style.map("TButton", background=[("active", "#585b70")])
        style.configure("TEntry", fieldbackground="#313244", foreground="#cdd6f4",
                        insertcolor="#cdd6f4")
        style.configure("Vertical.TScrollbar", background="#45475a",
                        troughcolor="#313244", arrowcolor="#cdd6f4")
        style.configure("TCheckbutton", background="#1e1e2e", foreground="#cdd6f4")
        style.configure("TLabelframe", background="#1e1e2e", foreground="#cdd6f4")
        style.configure("Card.TFrame", background="#2e2e3e", relief="ridge", borderwidth=1)

    def _apply_light_theme(self):
        self.root.configure(bg="#f5f5f5")
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", background="#f5f5f5", foreground="#11111b",
                        fieldbackground="#ffffff", borderwidth=1)
        style.configure("TFrame", background="#f5f5f5")
        style.configure("TLabel", background="#f5f5f5", foreground="#11111b")
        style.configure("TButton", background="#e0e0e0", foreground="#11111b",
                        borderwidth=1, focusthickness=0)
        style.map("TButton", background=[("active", "#d0d0d0")])
        style.configure("TEntry", fieldbackground="#ffffff", foreground="#11111b",
                        insertcolor="#11111b")
        style.configure("Vertical.TScrollbar", background="#cccccc",
                        troughcolor="#f5f5f5", arrowcolor="#11111b")
        style.configure("TCheckbutton", background="#f5f5f5", foreground="#11111b")
        style.configure("TLabelframe", background="#f5f5f5", foreground="#11111b")
        style.configure("Card.TFrame", background="#ffffff", relief="ridge", borderwidth=1)

    # ------- UI Construction -------
    def _build_ui(self):
        # --- Top Toolbar ---
        self.toolbar = ttk.Frame(self.root, padding=5)
        self.toolbar.pack(fill="x")

        # Left side: search
        ttk.Label(self.toolbar, text="🔍", font=("Segoe UI", 14)).pack(side="left", padx=(5, 2))
        self.search_var = StringVar()
        self.search_var.trace_add("write", lambda *_: self._on_search())
        self.search_entry = ttk.Entry(self.toolbar, textvariable=self.search_var,
                                      font=("Segoe UI", 12), width=30)
        self.search_entry.pack(side="left", padx=5, pady=5, fill="x", expand=True)

        # Browser selector
        ttk.Label(self.toolbar, text="Browser:", font=("Segoe UI", 10)).pack(side="left", padx=(10,2))
        self.browser_var = StringVar(value=self.data["settings"].get("default_browser", self._get_default_browser_name()))
        self.browser_menu = ttk.Combobox(self.toolbar, textvariable=self.browser_var,
                                         values=[b["name"] for b in self.browsers],
                                         state="readonly", width=12)
        self.browser_menu.pack(side="left", padx=2)
        self.browser_menu.bind("<<ComboboxSelected>>", self._on_browser_changed)

        # Profile selector
        ttk.Label(self.toolbar, text="Profile:", font=("Segoe UI", 10)).pack(side="left", padx=(5,2))
        self.profile_var = StringVar()
        self.profile_menu = ttk.Combobox(self.toolbar, textvariable=self.profile_var,
                                         values=[], state="readonly", width=14)
        self.profile_menu.pack(side="left", padx=2)

        # Private checkbox – must be created before _update_profile_list
        self.private_var = BooleanVar(value=self.data["settings"].get("default_private", False))
        self.private_cb = ttk.Checkbutton(self.toolbar, text="Private", variable=self.private_var)
        self.private_cb.pack(side="left", padx=10)

        # Now update profile list and private checkbox state
        self._update_profile_list()

        # Right side: action buttons
        ttk.Button(self.toolbar, text="📥 Import", command=self._import_data).pack(side="right", padx=2)
        ttk.Button(self.toolbar, text="📤 Export", command=self._export_data).pack(side="right", padx=2)
        ttk.Button(self.toolbar, text="⚙ Settings", command=self._open_settings).pack(side="right", padx=5)
        ttk.Button(self.toolbar, text="➕ New Tool", command=self._add_new_tool).pack(side="right", padx=5)

        # --- Favorites Bar ---
        self.fav_bar_frame = ttk.Frame(self.root, padding=5)
        self.fav_bar_frame.pack(fill="x")

        # --- Recently Opened ---
        self.recent_frame = ttk.LabelFrame(self.root, text="Recently Opened", padding=5)
        self.recent_frame.pack(fill="x", padx=5, pady=(0,5))
        self.recent_inner = ttk.Frame(self.recent_frame)
        self.recent_inner.pack(fill="x")

        # --- Main Content Area ---
        self.main_pw = ttk.PanedWindow(self.root, orient="horizontal")
        self.main_pw.pack(fill="both", expand=True, padx=5, pady=5)

        # Sidebar categories
        self.sidebar = ttk.Frame(self.main_pw, width=150)
        self.category_listbox = Listbox(self.sidebar, bg="#313244", fg="#cdd6f4",
                                        selectbackground="#585b70",
                                        font=("Segoe UI", 10), activestyle="none",
                                        borderwidth=0, highlightthickness=0)
        self.category_listbox.pack(fill="both", expand=True)
        self.category_listbox.bind("<<ListboxSelect>>", self._on_category_select)
        self.main_pw.add(self.sidebar, weight=0)

        # Tools canvas
        self.tools_frame = ttk.Frame(self.main_pw)
        self.tools_canvas = ttk.Frame(self.tools_frame)
        self.tools_canvas.pack(fill="both", expand=True)
        self.main_pw.add(self.tools_frame, weight=1)

        # Context menu
        self.context_menu = Menu(self.root, tearoff=0)
        self._build_context_menu()
        self.root.bind_all("<Button-3>", self._on_right_click)

    def _update_profile_list(self):
        browser_name = self.browser_var.get()
        browser = next((b for b in self.browsers if b["name"] == browser_name), None)
        if browser and browser.get("profiles"):
            profiles = browser["profiles"]
            self.profile_menu["values"] = profiles
            if self.data["settings"].get("last_profile") in profiles:
                self.profile_var.set(self.data["settings"]["last_profile"])
            else:
                self.profile_var.set("")
        else:
            self.profile_menu["values"] = []
            self.profile_var.set("")
        # Update private checkbox availability
        has_private = bool(browser and browser.get("private_flag"))
        if has_private:
            self.private_cb.configure(state="normal")
        else:
            self.private_cb.configure(state="disabled")
            self.private_var.set(False)

    def _on_browser_changed(self, event=None):
        self._update_profile_list()
        # Optionally store last profile? Not implemented

    # ------- Populate UI elements -------
    def _refresh_lists(self):
        self._refresh_categories()
        self._refresh_tools_list()
        self._refresh_favorites_bar()
        self._refresh_recent()
        self._apply_settings()

    def _refresh_categories(self):
        cats = sorted(list({tool["category"] for tool in self.data["tools"]}))
        self.category_listbox.delete(0, "end")
        self.category_listbox.insert("end", "All")
        for cat in cats:
            self.category_listbox.insert("end", cat)
        self.category_listbox.selection_clear(0, "end")
        self.category_listbox.selection_set(0)

    def _refresh_tools_list(self, filter_text=None, category=None):
        for widget in self.tools_canvas.winfo_children():
            widget.destroy()
        search = filter_text if filter_text is not None else self.search_var.get().lower()
        cat = category if category is not None else self._get_selected_category()
        tools = self.data["tools"]
        pinned_first = sorted(tools, key=lambda t: not t.get("pinned", False))
        shown = []
        for tool in pinned_first:
            if search and search not in tool["name"].lower() and search not in tool.get("notes","").lower() and search not in tool.get("url","").lower():
                continue
            if cat != "All" and tool["category"] != cat:
                continue
            shown.append(tool)

        row_frame = None
        for i, tool in enumerate(shown):
            if i % 3 == 0:
                row_frame = ttk.Frame(self.tools_canvas)
                row_frame.pack(fill="x", pady=2)
            card = self._create_tool_card(row_frame, tool)
            card.pack(side="left", padx=5, pady=5, expand=True, fill="both")

    def _create_tool_card(self, parent, tool: dict):
        card = ttk.Frame(parent, style="Card.TFrame")
        card.tool_id = tool["id"]
        card.tool_url = tool["url"]

        # Icon
        icon_label = ttk.Label(card, text="", background="#45475a", width=6)
        icon_label.pack(padx=5, pady=5)
        if tool["url"]:
            cached = self.icon_cache.get_icon(tool["url"])
            if cached:
                icon_label.configure(image=cached, text="")
                icon_label.image = cached
            else:
                self.icon_cache.load_icon_async(tool["url"],
                    lambda img, l=icon_label, t=tool: self._set_icon(l, img, t))
                letter = tool["name"][0].upper() if tool["name"] else "?"
                icon_label.configure(text=letter, font=("Segoe UI", 16, "bold"),
                                     foreground="#cdd6f4")
        # Name
        name_label = ttk.Label(card, text=tool["name"], font=("Segoe UI", 10, "bold"),
                               anchor="center")
        name_label.pack(fill="x", padx=5)
        # Category
        ttk.Label(card, text=tool["category"], font=("Segoe UI", 8),
                  foreground="#a6adc8").pack(padx=5)
        # Notes tooltip
        if tool.get("notes"):
            ToolTip(icon_label, tool["notes"])  # attached to icon for visibility
        # Buttons
        btn_frame = ttk.Frame(card)
        btn_frame.pack(pady=5)
        open_btn = ttk.Button(btn_frame, text="Open",
                              command=lambda t=tool: self._launch_tool(t))
        open_btn.pack(side="left", padx=2)
        fav_btn = ttk.Button(btn_frame,
                             text="★" if tool["id"] in self.data["favorites"] else "☆",
                             command=lambda t=tool: self._toggle_favorite(t))
        fav_btn.pack(side="left", padx=2)
        return card

    def _set_icon(self, label, photo, tool):
        if photo:
            label.configure(image=photo, text="")
            label.image = photo
        else:
            letter = tool["name"][0].upper() if tool["name"] else "?"
            label.configure(text=letter, font=("Segoe UI", 16, "bold"),
                            foreground="#cdd6f4")

    def _refresh_favorites_bar(self):
        for widget in self.fav_bar_frame.winfo_children():
            widget.destroy()
        fav_ids = self.data["favorites"]
        fav_tools = [t for t in self.data["tools"] if t["id"] in fav_ids]
        if not fav_tools:
            ttk.Label(self.fav_bar_frame, text="⭐ Favorites: none yet",
                      font=("Segoe UI", 9)).pack(side="left")
            return
        for tool in fav_tools:
            btn = ttk.Button(self.fav_bar_frame, text=f"★ {tool['name']}",
                             command=lambda t=tool: self._launch_tool(t))
            btn.pack(side="left", padx=2, pady=2)

    def _refresh_recent(self):
        for widget in self.recent_inner.winfo_children():
            widget.destroy()
        recent = self.data["recent"][:10]
        if not recent:
            ttk.Label(self.recent_inner, text="No recent items",
                      font=("Segoe UI", 9)).pack(side="left")
            return
        for r in recent:
            ts = r.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(ts)
                time_str = dt.strftime("%H:%M")
            except:
                time_str = ""
            btn_text = f"🕒 {r['name']} ({time_str})"
            btn = ttk.Button(self.recent_inner, text=btn_text,
                             command=lambda url=r["url"]: self._launch_recent(r))
            btn.pack(side="left", padx=2, pady=2)
            ToolTip(btn, f"Opened: {ts}\nURL: {r['url']}")

    def _launch_recent(self, recent_item):
        tool = next((t for t in self.data["tools"] if t["id"] == recent_item["id"]), None)
        if tool:
            self._launch_tool(tool)
        else:
            webbrowser.open(recent_item["url"])

    def _get_selected_category(self):
        sel = self.category_listbox.curselection()
        if sel:
            idx = sel[0]
            cat = self.category_listbox.get(idx)
            return cat
        return "All"

    def _on_category_select(self, event):
        self._refresh_tools_list()

    def _on_search(self):
        self._refresh_tools_list()

    # ------- Context Menu & Reordering -------
    def _build_context_menu(self):
        self.context_menu.add_command(label="Open (Normal)", command=lambda: self._launch_tool(self._right_click_tool, private=False))
        self.context_menu.add_command(label="Open Private/Incognito", command=lambda: self._launch_tool(self._right_click_tool, private=True))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Copy URL", command=self._copy_url)
        self.context_menu.add_command(label="Toggle Favorite", command=lambda: self._toggle_favorite(self._right_click_tool))
        self.context_menu.add_command(label="Pin/Unpin", command=lambda: self._toggle_pin(self._right_click_tool))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Move Up", command=lambda: self._move_tool(-1))
        self.context_menu.add_command(label="Move Down", command=lambda: self._move_tool(1))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Edit Tool", command=lambda: self._edit_tool(self._right_click_tool))
        self.context_menu.add_command(label="Delete Tool", command=lambda: self._delete_tool(self._right_click_tool))

    def _on_right_click(self, event):
        widget = event.widget
        while widget:
            if hasattr(widget, "tool_id"):
                self._right_click_tool = next((t for t in self.data["tools"] if t["id"] == widget.tool_id), None)
                if self._right_click_tool:
                    self.context_menu.tk_popup(event.x_root, event.y_root)
                break
            widget = widget.master

    def _move_tool(self, direction):
        if not self._right_click_tool:
            return
        tools = self.data["tools"]
        idx = next(i for i, t in enumerate(tools) if t["id"] == self._right_click_tool["id"])
        new_idx = idx + direction
        if 0 <= new_idx < len(tools):
            tools.insert(new_idx, tools.pop(idx))
            self._refresh_tools_list()
            self._save_data()

    # ------- Tool Actions -------
    def _launch_tool(self, tool: dict, private: bool = None):
        if not tool:
            return
        browser_name = self.browser_var.get()
        if private is None:
            private = self.private_var.get()
        browser = next((b for b in self.browsers if b["name"] == browser_name), None)
        url = tool["url"]
        if not url:
            messagebox.showerror("Error", "No URL defined for this tool.")
            return

        # Warn if private requested but unsupported
        if private and browser and not browser.get("private_flag"):
            messagebox.showwarning("Private Mode Unsupported",
                                   f"{browser['display_name']} does not support private/incognito mode. Opening normally.")
            private = False

        try:
            args = []
            if browser and browser["path"]:
                args.append(browser["path"])
                # Profile flag
                profile = self.profile_var.get().strip()
                if profile and browser["name"] in ("chrome", "edge", "brave", "vivaldi"):
                    args.append(f"--profile-directory={profile}")
                if private and browser["private_flag"]:
                    args.extend(browser["private_flag"])
                args.append(url)
                subprocess.Popen(args, shell=False)
            else:
                if private and browser and browser["private_flag"]:
                    subprocess.Popen([browser["path"]] + browser["private_flag"] + [url])
                else:
                    webbrowser.open(url)
        except Exception as e:
            messagebox.showerror("Launch Error", f"Could not open {url}\nError: {e}")
            return

        self._add_recent(tool)
        self._save_data()

    def _add_recent(self, tool):
        recent = self.data["recent"]
        recent = [r for r in recent if r["id"] != tool["id"]]
        recent.insert(0, {
            "id": tool["id"],
            "name": tool["name"],
            "url": tool["url"],
            "timestamp": datetime.now().isoformat(),
        })
        self.data["recent"] = recent[:MAX_RECENT]
        self._refresh_recent()

    def _toggle_favorite(self, tool):
        if tool["id"] in self.data["favorites"]:
            self.data["favorites"].remove(tool["id"])
        else:
            self.data["favorites"].append(tool["id"])
        self._refresh_lists()
        self._save_data()

    def _toggle_pin(self, tool):
        tool["pinned"] = not tool.get("pinned", False)
        self._refresh_lists()
        self._save_data()

    def _copy_url(self):
        if self._right_click_tool:
            self.root.clipboard_clear()
            self.root.clipboard_append(self._right_click_tool["url"])
            messagebox.showinfo("Copied", f"URL copied: {self._right_click_tool['url']}")

    # ------- Tool Management -------
    def _add_new_tool(self):
        new_id = f"custom_{int(time.time())}"
        new_tool = {
            "id": new_id,
            "name": "",
            "url": "",
            "category": "Custom",
            "icon": "",
            "notes": "",
            "pinned": False,
        }
        dialog = ToolEditor(self.root, new_tool, self.data["tools"], self._on_tool_edited, is_new=True)

    def _edit_tool(self, tool=None):
        if tool is None:
            tool = self._right_click_tool
        if not tool:
            return
        dialog = ToolEditor(self.root, tool, self.data["tools"], self._on_tool_edited)

    def _on_tool_edited(self, updated_tool, is_new=False):
        if is_new:
            self.data["tools"].append(updated_tool)
        else:
            idx = next(i for i, t in enumerate(self.data["tools"]) if t["id"] == updated_tool["id"])
            self.data["tools"][idx] = updated_tool
        self._refresh_lists()
        self._save_data()

    def _delete_tool(self, tool):
        if not tool:
            return
        if messagebox.askyesno("Delete", f"Remove '{tool['name']}'?"):
            self.data["tools"] = [t for t in self.data["tools"] if t["id"] != tool["id"]]
            if tool["id"] in self.data["favorites"]:
                self.data["favorites"].remove(tool["id"])
            self.data["recent"] = [r for r in self.data["recent"] if r["id"] != tool["id"]]
            self._refresh_lists()
            self._save_data()

    # ------- Import / Export (main toolbar) -------
    def _import_data(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if filepath:
            try:
                with open(filepath, "r") as f:
                    imported = json.load(f)
                # Merge carefully
                self.data["tools"] = imported.get("tools", self.data["tools"])
                self.data["favorites"] = imported.get("favorites", self.data["favorites"])
                self.data["recent"] = imported.get("recent", self.data["recent"])
                self.data["settings"].update(imported.get("settings", {}))
                self._refresh_lists()
                self._save_data()
                messagebox.showinfo("Import", "Data imported successfully.")
            except Exception as e:
                messagebox.showerror("Import Error", str(e))

    def _export_data(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".json",
                                                filetypes=[("JSON", "*.json")])
        if filepath:
            try:
                with open(filepath, "w") as f:
                    json.dump(self.data, f, indent=2)
                messagebox.showinfo("Export", "Data exported successfully.")
            except Exception as e:
                messagebox.showerror("Export Error", str(e))

    # ------- Settings Dialog -------
    def _open_settings(self):
        SettingsDialog(self.root, self.data, self._on_settings_changed)

    def _on_settings_changed(self):
        self._apply_settings()
        self._refresh_lists()
        self._save_data()

    # ------- Visibility Toggle (Ctrl+Shift+L) -------
    def _toggle_visibility(self, event=None):
        if self.root.state() == "withdrawn":
            self.root.deiconify()
        elif self.root.state() == "iconic":
            self.root.deiconify()
        else:
            self.root.withdraw()

    # ------- Window Close -------
    def _on_closing(self):
        self._save_data()
        self.root.destroy()

# ----------------------------------------------------------------------
# Tool Editor Dialog (supports new tools and custom categories)
# ----------------------------------------------------------------------
class ToolEditor(Toplevel):
    def __init__(self, parent, tool: dict, all_tools: list, callback, is_new=False):
        super().__init__(parent)
        self.title("Add New Tool" if is_new else "Edit Tool")
        self.tool = tool.copy()
        self.all_tools = all_tools
        self.callback = callback
        self.is_new = is_new

        frame = ttk.Frame(self, padding=10)
        frame.pack()

        ttk.Label(frame, text="Name:").grid(row=0, column=0, sticky="e", pady=2)
        self.name_var = StringVar(value=tool["name"])
        ttk.Entry(frame, textvariable=self.name_var, width=40).grid(row=0, column=1, pady=2)

        ttk.Label(frame, text="URL:").grid(row=1, column=0, sticky="e", pady=2)
        self.url_var = StringVar(value=tool.get("url", ""))
        ttk.Entry(frame, textvariable=self.url_var, width=40).grid(row=1, column=1, pady=2)

        ttk.Label(frame, text="Category:").grid(row=2, column=0, sticky="e", pady=2)
        cats = sorted(list({t["category"] for t in all_tools}))
        self.cat_var = StringVar(value=tool.get("category", "Custom"))
        self.cat_combo = ttk.Combobox(frame, textvariable=self.cat_var, values=cats, width=25)
        self.cat_combo.grid(row=2, column=1, pady=2)
        self.cat_combo.set(self.cat_var.get())

        ttk.Label(frame, text="Notes:").grid(row=3, column=0, sticky="ne", pady=2)
        self.notes_text = ttk.Entry(frame, width=40)
        self.notes_text.insert(0, tool.get("notes", ""))
        self.notes_text.grid(row=3, column=1, pady=2)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Save", command=self._save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="left", padx=5)

    def _save(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Validation", "Tool name required.")
            return
        url = self.url_var.get().strip()
        category = self.cat_var.get().strip()
        if not category:
            category = "Custom"
        self.tool["name"] = name
        self.tool["url"] = url
        self.tool["category"] = category
        self.tool["notes"] = self.notes_text.get()
        self.callback(self.tool, self.is_new)
        self.destroy()

# ----------------------------------------------------------------------
# Settings Dialog
# ----------------------------------------------------------------------
class SettingsDialog(Toplevel):
    def __init__(self, parent, data: dict, callback):
        super().__init__(parent)
        self.title("Settings")
        self.data = data
        self.callback = callback
        self.settings = data["settings"].copy()

        frame = ttk.Frame(self, padding=10)
        frame.pack()

        # Default browser
        ttk.Label(frame, text="Default Browser:").grid(row=0, column=0, sticky="e", pady=5)
        self.browser_var = StringVar(value=self.settings.get("default_browser", DEFAULT_BROWSER))
        browsers = [b["name"] for b in data.get("browsers", [])]
        if not browsers:
            browsers = ["chrome", "edge", "firefox"]
        ttk.Combobox(frame, textvariable=self.browser_var, values=browsers,
                     state="readonly", width=20).grid(row=0, column=1)

        # Private mode default
        self.private_var = BooleanVar(value=self.settings.get("default_private", False))
        ttk.Checkbutton(frame, text="Default Private Mode",
                        variable=self.private_var).grid(row=1, column=0, columnspan=2, sticky="w")

        # Theme
        ttk.Label(frame, text="Theme:").grid(row=2, column=0, sticky="e", pady=5)
        self.theme_var = StringVar(value=self.settings.get("theme", "dark"))
        ttk.Combobox(frame, textvariable=self.theme_var, values=["dark", "light"],
                     state="readonly", width=10).grid(row=2, column=1)

        # Always on top
        self.top_var = BooleanVar(value=self.settings.get("always_on_top", False))
        ttk.Checkbutton(frame, text="Always on Top",
                        variable=self.top_var).grid(row=3, column=0, columnspan=2, sticky="w")

        # Start minimized
        self.minimize_var = BooleanVar(value=self.settings.get("start_minimized", False))
        ttk.Checkbutton(frame, text="Start Minimized to Taskbar",
                        variable=self.minimize_var).grid(row=4, column=0, columnspan=2, sticky="w")

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Save", command=self._save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="left", padx=5)

    def _save(self):
        self.settings["default_browser"] = self.browser_var.get()
        self.settings["default_private"] = self.private_var.get()
        self.settings["theme"] = self.theme_var.get()
        self.settings["always_on_top"] = self.top_var.get()
        self.settings["start_minimized"] = self.minimize_var.get()
        self.data["settings"].update(self.settings)
        self.callback()
        self.destroy()

# ----------------------------------------------------------------------
# Main Entry
# ----------------------------------------------------------------------
def main():
    root = Tk()
    app = AILauncherHub(root)
    root.mainloop()

if __name__ == "__main__":
    main()
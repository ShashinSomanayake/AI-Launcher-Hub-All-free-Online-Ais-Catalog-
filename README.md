# 🚀 AI Launcher Hub

**A fast, searchable launcher for AI websites, developer tools, and cloud services – optimised for daily use by software engineers on Windows.**  
*Two implementations: Tkinter (lightweight) and PySide6 (modern Qt).*

---

## 📖 Table of Contents

1. [Overview](#-overview)  
2. [Key Features](#-key-features)  
3. [System Requirements](#-system-requirements)  
4. [Installation](#-installation)  
   - [Tkinter Version](#tkinter-version)  
   - [PySide6 Version](#pyside6-version)  
   - [Optional Dependencies](#optional-dependencies)  
5. [First Run & Data Storage](#-first-run--data-storage)  
6. [Usage Guide](#-usage-guide)  
   - [Main Interface](#main-interface)  
   - [Launching Tools](#launching-tools)  
   - [Search & Filtering](#search--filtering)  
   - [Favorites Bar](#favorites-bar)  
   - [Recently Opened](#recently-opened)  
   - [Categories Sidebar](#categories-sidebar)  
   - [Browser & Profile Selection](#browser--profile-selection)  
   - [Private/Incognito Mode](#privateincognito-mode)  
   - [Context Menu (Right‑Click)](#context-menu-rightclick)  
   - [Global Hotkey](#global-hotkey)  
7. [Settings Dialog](#-settings-dialog)  
8. [Customisation & Data Management](#-customisation--data-management)  
   - [Adding / Editing / Deleting Tools](#adding--editing--deleting-tools)  
   - [Manual JSON Editing](#manual-json-editing)  
   - [Import & Export](#import--export)  
9. [Browser Detection & Profiles](#-browser-detection--profiles)  
10. [Favicon Support](#-favicon-support)  
11. [Theme Switching](#-theme-switching)  
12. [Keyboard Shortcuts](#-keyboard-shortcuts)  
13. [Troubleshooting](#-troubleshooting)  
14. [Development & Contributing](#-development--contributing)  
15. [License](#-license)  
16. [Acknowledgements](#-acknowledgements)

---

## 🧠 Overview

AI Launcher Hub is a desktop application that centralises all your AI‑related web tools into one convenient place. Instead of bookmarking dozens of URLs or typing them manually, you get a fast, searchable grid with one‑click launches, favourites, recent items, and full control over which browser and profile to use.

The project started as a productivity booster for developers who frequently switch between ChatGPT, Claude, Copilot, and other AI assistants. It has evolved into a fully‑fledged launcher that can manage any web‑based tool – internal dashboards, cloud consoles, documentation, etc.

Two versions are provided:

- **Tkinter** – uses Python’s built‑in GUI toolkit (no extra dependencies) and is very lightweight.  
- **PySide6** – uses the Qt framework for a more polished, modern look and better cross‑platform consistency.  

Both versions share the same feature set and data format, so you can switch between them without losing your configuration.

---

## ✨ Key Features

### Core Launcher
- **Pre‑loaded with 15+ popular AI tools** – ChatGPT, Claude, Gemini, Perplexity, Midjourney, DALL·E, GitHub Copilot, CodeWhisperer, Bard, HuggingChat, Phind, Jasper, Writesonic, RunwayML, Kaiber.  
- **Live search** – start typing and the grid instantly filters by name, category, URL, or notes.  
- **Category sidebar** – browse by categories (Chatbots, Coding, Image Generation, Research, Writing, Media, Custom).  
- **Favorites bar** – pin your most‑used tools for instant access.  
- **Recently opened** – the last 20 launched tools are shown as clickable buttons with timestamps.  

### Browser & Launch Options
- **Automatic browser detection** – finds installed browsers (Chrome, Edge, Firefox, Brave, Opera, Vivaldi) via registry and common paths.  
- **Profile support** – for Chromium‑based browsers, select any existing profile (e.g., “Default”, “Profile 1”) to launch with that profile’s cookies and extensions.  
- **Private/Incognito mode** – launch any tool in private mode with a single toggle (supported by most modern browsers).  
- **One‑click launch** – from the main grid, favorites bar, or recent items.  
- **Right‑click context menu** – open normal/private, copy URL, toggle favorite, pin/unpin, move up/down, edit, delete.  

### Tool Management
- **Add new tools** – custom name, URL, category, and notes.  
- **Edit existing tools** – update any field.  
- **Delete tools** – with confirmation; also removes from favorites and recent.  
- **Reorder tools** – move up/down to customise the grid order.  
- **Pin/Unpin** – pinned tools always appear first in the grid.  

### Personalisation
- **Dark / Light theme** – switch between two colour schemes.  
- **Always on Top** – keep the window above other applications.  
- **Start Minimized** – launch the app minimised to the taskbar (great for startup).  
- **Global hotkey** – `Ctrl+Shift+L` toggles the window visibility from anywhere.  

### Data & Portability
- **Import / Export** – backup your entire configuration (tools, favorites, recent, settings) as a JSON file.  
- **Manual JSON editing** – advanced users can directly edit the data file for batch changes.  
- **Automatic save** – all changes are persisted immediately to `%APPDATA%\AI Launcher Hub\launcher_data.json`.  

### Extras
- **Favicon fetching** – automatically downloads and displays website icons (requires Pillow).  
- **Tooltips** – hover over a tool to see its notes (or over recent items to see the full URL and timestamp).  
- **Responsive grid** – tools are arranged in a clean, scrollable grid that adapts to window size.  

---

## 🖥️ System Requirements

- **Operating System**: Windows 10 or 11 (tested).  
  *Linux/macOS may work with minor adjustments, but browser detection relies on Windows registry.*  
- **Python**: 3.8 or higher.  
- **RAM**: Minimal (<100 MB).  
- **Disk space**: ~10 MB for the code + dependencies.  

### Required Python Packages
- **Tkinter version**: Only the Python standard library (tkinter, webbrowser, subprocess, etc.).  
- **PySide6 version**: Requires `PySide6`.  

### Optional Packages
- **Pillow** – enables favicon downloading. Highly recommended for a better visual experience.

---

## 📦 Installation

### 1. Clone or Download the Repository
```bash
git clone https://github.com/yourusername/AI-Launcher-Hub.git
cd AI-Launcher-Hub
```

Alternatively, download the ZIP from GitHub and extract it.

### 2. Set Up a Virtual Environment (Recommended)
```bash
python -m venv venv
venv\Scripts\activate   # On Windows
```

### 3. Install Dependencies

#### Tkinter Version
```bash
# No mandatory dependencies.
# For favicon support:
pip install pillow
```

#### PySide6 Version
```bash
pip install PySide6
# Optional for favicons:
pip install pillow
```

### 4. Run the Application

**Tkinter version** (file: `Ai lanucher hub (1).py`):
```bash
python "Ai lanucher hub (1).py"
```

**PySide6 version** (file: `ai_launcher_hub.py`):
```bash
python ai_launcher_hub.py
```

> **Note**: The first time you run the app, it will create the data directory and a default configuration with the built‑in tools.

---

## 🗂️ First Run & Data Storage

On startup, the application:

- Creates the folder `%APPDATA%\AI Launcher Hub\` (where `%APPDATA%` is typically `C:\Users\<YourUser>\AppData\Roaming`).
- Generates `launcher_data.json` with the default tool list if the file doesn’t exist.
- Detects installed browsers and stores that information (not saved to JSON, only used at runtime).

All your data – tools, favorites, recent items, settings – is stored in this single JSON file. You can back it up, share it, or edit it manually.

---

## 🎮 Usage Guide

### Main Interface

When you launch the app, you’ll see:

- **Top toolbar** – search box, browser selector, profile selector, private toggle, and action buttons (Import, Export, Settings, New Tool).
- **Favorites bar** – immediately below the toolbar, shows your starred tools.
- **Recently opened** – a horizontal bar with the last few launched tools.
- **Category sidebar** – on the left, lists all categories; clicking one filters the grid.
- **Tools grid** – the main area displaying tool cards (each with name, category, icon, Open button, and star/favorite button).

### Launching Tools

- **Click the “Open” button** on any tool card.
- **Double‑click** on a tool card? (Not implemented by default, but you can modify the code.)
- **Click a favorite button** in the favorites bar.
- **Click a recent item button** in the recently opened bar.
- **Right‑click** a tool card and select **Open (Normal)** or **Open Private/Incognito**.

When launched, the tool opens in the selected browser and profile, with private mode if enabled. The tool is then added to the recent list.

### Search & Filtering

- Type any keyword into the **search box**.
- The grid will instantly filter tools whose name, notes, or URL contain the keyword (case‑insensitive).
- Combine search with a category selection for even finer filtering.

### Favorites Bar

- Mark a tool as a favorite by clicking the star (☆) on its card; it becomes a ★ and appears in the favorites bar.
- Click the favorite button in the bar to launch that tool directly.
- Right‑click a favorite button to access the same context menu (copy URL, edit, etc.).
- Remove from favorites by clicking the star again (or via context menu).

### Recently Opened

- The bar shows the last 10 launched tools (the full history keeps up to 20, but only 10 are displayed for brevity).
- Each button shows the tool name and the time it was opened (HH:MM).
- Hover over a recent button to see the full timestamp and URL.
- Click any recent item to re‑launch it. If the tool still exists in the list, it will use the same configuration; otherwise, it falls back to opening the URL directly with the system default browser.

### Categories Sidebar

- The left panel lists all categories that appear in your tools.
- Click a category to show only tools belonging to that group.
- Select “All” to show everything.
- The list is automatically updated when you add/rename categories.

### Browser & Profile Selection

- Use the **Browser** dropdown to choose which browser to use for launching.
- The dropdown is populated with detected browsers.
- **Profile** dropdown appears only for Chromium‑based browsers (Chrome, Edge, Brave, Vivaldi). It lists all available profiles found in the user data directory (e.g., “Default”, “Profile 1”, etc.).
- The profile selection is remembered per browser instance (the last used profile is saved in settings under `last_profile`).

### Private/Incognito Mode

- Tick the **Private** checkbox to launch all tools in private/incognito mode (if the selected browser supports it).
- This is a global toggle – you can still override it per launch via the context menu.
- If the browser does not support private mode, the checkbox is disabled and a warning is shown when you attempt to launch with it enabled.

### Context Menu (Right‑Click)

Right‑click on any tool card (or its favorite button) to open a context menu with the following options:

- **Open (Normal)** – launch in the current browser with normal mode (overrides the private toggle).
- **Open Private/Incognito** – launch in private mode (overrides the private toggle).
- **Copy URL** – copies the tool’s URL to the clipboard.
- **Toggle Favorite** – adds/removes the tool from favorites.
- **Pin/Unpin** – pins the tool so it appears at the top of the grid regardless of sorting.
- **Move Up / Move Down** – reorders the tool in the main list (useful for custom ordering).
- **Edit Tool** – opens the tool editor dialog.
- **Delete Tool** – removes the tool (with confirmation).

### Global Hotkey

Press **Ctrl+Shift+L** at any time (even when the app is in the background or minimised) to:

- If the window is hidden or minimised, bring it to the front and restore it.
- If the window is visible and active, hide it (minimise to taskbar).

This makes the launcher instantly accessible without reaching for the mouse.

---

## ⚙️ Settings Dialog

Click the **⚙ Settings** button on the toolbar to open the settings window. Here you can configure:

| Setting | Description |
|---------|-------------|
| **Default Browser** | Choose which browser is selected by default on startup. |
| **Default Private Mode** | If checked, the “Private” toggle will be on by default. |
| **Theme** | Switch between `dark` and `light`. |
| **Always on Top** | When enabled, the window stays above all other windows. |
| **Start Minimized to Taskbar** | If checked, the application starts minimised (useful for autorun). |

All settings are saved automatically when you click **Save**.

---

## 🛠️ Customisation & Data Management

### Adding / Editing / Deleting Tools

- **Add**: Click the **➕ New Tool** button on the toolbar. Fill in the name, URL, category (you can type a new one), and optional notes. Click Save.
- **Edit**: Right‑click a tool and select **Edit Tool**. Modify any field and save.
- **Delete**: Right‑click and select **Delete Tool**. Confirm the deletion.

### Manual JSON Editing

For bulk changes, you can directly edit `%APPDATA%\AI Launcher Hub\launcher_data.json`. The file structure is:

```json
{
  "tools": [
    {
      "id": "unique_id",
      "name": "Tool Name",
      "url": "https://example.com",
      "category": "Category",
      "icon": "",
      "notes": "Optional note",
      "pinned": false
    }
  ],
  "favorites": ["id1", "id2"],
  "recent": [
    {
      "id": "id1",
      "name": "Tool Name",
      "url": "https://example.com",
      "timestamp": "2026-08-04T12:34:56"
    }
  ],
  "settings": {
    "default_browser": "chrome",
    "default_private": false,
    "theme": "dark",
    "always_on_top": false,
    "start_minimized": false,
    "last_profile": "Default"
  }
}
```

- **id**: Must be unique. For custom tools, use a prefix like `custom_` followed by a timestamp.
- **pinned**: If `true`, the tool appears first in the grid.
- **favorites**: Array of tool IDs that are starred.
- **recent**: Keeps up to 20 items; only the first 10 are shown in the UI.

After editing, save the file and restart the application, or use the **Import** feature to reload.

### Import & Export

- **Export**: Click the **📤 Export** button, choose a location and filename (default `launcher_data.json`). The entire configuration is saved.
- **Import**: Click **📥 Import**, select a previously exported JSON file. The app will merge the imported data with the current configuration (tools, favorites, recent, settings).  
  *Note: Import does not overwrite existing tools with the same ID; it replaces them.*

---

## 🌐 Browser Detection & Profiles

The application uses two methods to detect browsers:

1. **Windows Registry** – scans `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall` for known display names.
2. **Fallback paths** – checks `Program Files` and `Program Files (x86)` for common executable names.

Browsers detected: Chrome, Edge, Firefox, Brave, Opera, Vivaldi.

For Chromium‑based browsers, it also scans the user data directory (`%LOCALAPPDATA%\...\User Data`) for subfolders named “Default” or “Profile *”. These are presented in the Profile dropdown.

If you have a browser installed in a non‑standard location, you can add it manually by editing the `detect_browsers()` function or by adding a custom entry in the JSON (not currently supported, but you can contribute).

---

## 🖼️ Favicon Support

The application attempts to fetch favicons from Google’s favicon service (`https://www.google.com/s2/favicons`).  
This requires the **Pillow** library to be installed.

- **With Pillow**: Icons are downloaded asynchronously and displayed on each tool card.
- **Without Pillow**: A placeholder with the first letter of the tool name is shown.

To install Pillow:
```bash
pip install pillow
```

---

## 🎨 Theme Switching

Two themes are available: **Dark** (default) and **Light**.  
Switch via the Settings dialog. The theme is applied immediately and saved.

- **Dark**: Dark backgrounds (#1e1e2e), light text, subtle borders – easy on the eyes in low‑light environments.
- **Light**: Light backgrounds (#f5f5f5), dark text – better for bright rooms.

Each version (Tkinter and PySide6) implements themes using its own styling mechanisms; the visual result is similar.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+L` | Toggle window visibility (show/hide). |
| `Tab` / `Shift+Tab` | Move focus through UI elements (standard). |
| `Enter` | When focus is on the search box, it does nothing special, but you can press Enter to move to the grid. (Not a dedicated shortcut.) |

*More shortcuts can be added by modifying the source code.*

---

## 🐛 Troubleshooting

### Application fails to start
- Ensure you have Python 3.8+ installed.
- For the PySide6 version, verify that PySide6 is correctly installed (`pip show PySide6`).
- Check for any error messages in the console; they often indicate missing dependencies.

### Tools not launching
- Verify that the URL is valid and includes `http://` or `https://`.
- Ensure the selected browser executable exists at the detected path. If not, the app falls back to `webbrowser.open()`.
- If private mode is not supported, the app shows a warning and opens normally.

### Favicons not showing
- Install Pillow: `pip install pillow`.
- The favicon service might be rate‑limited; wait a moment or try again later.

### Profiles not appearing
- The browser must be installed in the standard location. If you moved the user data directory, the detection might fail.
- You can manually add profiles by editing the JSON (not directly, but you can modify the `_detect_profiles()` function).

### Data lost after update
- The data file is stored in `%APPDATA%\AI Launcher Hub\`. It is not overwritten by updates, so your data is safe.

### Global hotkey not working
- Some applications may intercept `Ctrl+Shift+L`. Try a different key combination by modifying the source (look for `bind_all("<Control-Shift-L>")` in the Tkinter version or `QShortcut` in the PySide6 version).

---

## 👨‍💻 Development & Contributing

We welcome contributions! Here’s how you can help:

### Setting Up for Development
1. Fork the repository and clone it.
2. Create a virtual environment and install dependencies.
3. Make your changes.
4. Test thoroughly (both Tkinter and PySide6 versions, if possible).
5. Submit a pull request with a clear description of the changes.

### Code Style
- Use 4 spaces for indentation.
- Add docstrings for functions and classes.
- Keep the code compatible with Python 3.8+.

### Ideas for Future Enhancements
- Custom icons (local image files).
- Multi‑workspace support (different sets of tools for different projects).
- Integration with browser extensions (e.g., open directly in a new tab).
- Linux/macOS support (adjust browser detection).
- Export/import as CSV or HTML.
- More keyboard shortcuts (e.g., `Ctrl+Number` to launch favorites).
- Tool grouping and drag‑and‑drop reordering.

If you have any questions, feel free to open an issue.

---

## 📄 License

This project is licensed under the **MIT License**. You are free to use, modify, distribute, and sublicense the code as long as you include the original copyright notice. See the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- **Google Favicon Service** for providing icons.
- All the AI platforms that make our work more efficient.
- The Python community for creating robust libraries.
- The Qt Company for PySide6.

---

## 📬 Contact & Support

For bugs, feature requests, or general questions, please [open an issue](https://github.com/yourusername/AI-Launcher-Hub/issues) on GitHub.  
You can also reach out to the maintainer directly (provide contact if desired).

---

**Happy launching! 🚀**

"""
BrowserPilot GUI — wxPython control panel for browser automation.
"""
import wx
import json
import threading
from pathlib import Path
from browserpilot.core import BrowserPilot
from common.settings import is_dark_mode, check_for_updates, set_macos_app_name, CURRENT_VERSION


# ── Dark Theme Colours ────────────────────────────────────────────────

DARK_BG = wx.Colour(22, 27, 34)
DARK_FG = wx.Colour(201, 209, 217)
DARK_PANEL = wx.Colour(13, 17, 23)
DARK_INPUT = wx.Colour(33, 38, 45)
DARK_ACCENT = wx.Colour(88, 166, 255)


def apply_dark_theme(widget):
    """Recursively apply dark theme to a widget tree."""
    if isinstance(widget, (wx.TextCtrl, wx.ComboBox)):
        widget.SetBackgroundColour(DARK_INPUT)
        widget.SetForegroundColour(DARK_FG)
    elif isinstance(widget, wx.StaticText):
        widget.SetForegroundColour(DARK_FG)
    elif isinstance(widget, wx.Panel):
        widget.SetBackgroundColour(DARK_PANEL)
    elif isinstance(widget, wx.Frame):
        widget.SetBackgroundColour(DARK_BG)

    if hasattr(widget, 'GetChildren'):
        for child in widget.GetChildren():
            apply_dark_theme(child)


class BrowserPilotFrame(wx.Frame):
    def __init__(self):
        super().__init__(
            None, title="BrowserPilot Control Center", size=(800, 700)
        )
        self.bp = BrowserPilot(headless=False)
        self.dark = is_dark_mode()

        self.init_menubar()
        self.init_icon()
        self.init_ui()

        if self.dark:
            apply_dark_theme(self)
            self.Refresh()

        # Check for updates
        self._check_updates()

    def _check_updates(self):
        def _task():
            has_update, latest = check_for_updates()
            if has_update:
                wx.CallAfter(
                    self.StatusBar.SetStatusText,
                    f"Update available: v{latest} (current: v{CURRENT_VERSION})"
                )
        threading.Thread(target=_task, daemon=True).start()

    # ── Resource path resolution ──────────────────────────────────────

    def get_resource_path(self, relative_path):
        import sys

        dev_path = Path(__file__).parent.parent.parent / relative_path
        if dev_path.exists():
            return dev_path

        base_path = Path(sys.executable).parent
        standalone_path = base_path / relative_path
        if standalone_path.exists():
            return standalone_path

        if sys.platform == "darwin" and ".app/Contents/MacOS" in str(base_path):
            resource_path = (
                base_path.parent.parent / "Resources" / relative_path
            )
            if resource_path.exists():
                return resource_path

        return standalone_path

    # ── Initialisation ────────────────────────────────────────────────

    def init_icon(self):
        wx.InitAllImageHandlers()
        icon_path = self.get_resource_path("assets/icon.png")
        if icon_path.exists():
            try:
                image = wx.Image(str(icon_path), wx.BITMAP_TYPE_PNG)
                bitmap = wx.Bitmap(image)
                icon = wx.Icon()
                icon.CopyFromBitmap(bitmap)
                self.SetIcon(icon)
            except Exception as e:
                print(f"Error loading icon: {e}")

    def init_menubar(self):
        menubar = wx.MenuBar()

        file_menu = wx.Menu()
        exit_item = file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl+Q")
        menubar.Append(file_menu, "&File")

        edit_menu = wx.Menu()
        prefs_item = edit_menu.Append(wx.ID_PREFERENCES, "&Preferences")
        menubar.Append(edit_menu, "&Edit")

        tools_menu = wx.Menu()
        nav_item = tools_menu.Append(wx.ID_ANY, "&Navigate\tCtrl+L")
        snap_item = tools_menu.Append(wx.ID_ANY, "&Screenshot\tCtrl+Shift+S")
        js_item = tools_menu.Append(wx.ID_ANY, "Execute &JS\tCtrl+J")
        tools_menu.AppendSeparator()
        ai_click_item = tools_menu.Append(wx.ID_ANY, "AI Cli&ck\tCtrl+Shift+C")
        ai_query_item = tools_menu.Append(wx.ID_ANY, "AI &Query\tCtrl+Shift+Q")
        ai_clear_item = tools_menu.Append(wx.ID_ANY, "Clear AI &History")
        tools_menu.AppendSeparator()
        reset_item = tools_menu.Append(wx.ID_ANY, "&Reset Profile")
        menubar.Append(tools_menu, "&Tools")

        help_menu = wx.Menu()
        guide_item = help_menu.Append(wx.ID_ANY, "User &Guide\tF1")
        about_item = help_menu.Append(wx.ID_ABOUT, "&About")
        menubar.Append(help_menu, "&Help")

        self.SetMenuBar(menubar)

        self.Bind(wx.EVT_MENU, lambda e: self.Close(), exit_item)
        self.Bind(wx.EVT_MENU, self.on_navigate, nav_item)
        self.Bind(wx.EVT_MENU, self.on_screenshot, snap_item)
        self.Bind(wx.EVT_MENU, self.on_js, js_item)
        self.Bind(wx.EVT_MENU, self.on_ai_click, ai_click_item)
        self.Bind(wx.EVT_MENU, self.on_ai_query, ai_query_item)
        self.Bind(wx.EVT_MENU, self.on_ai_clear, ai_clear_item)
        self.Bind(wx.EVT_MENU, self.on_reset, reset_item)
        self.Bind(wx.EVT_MENU, self.on_guide, guide_item)
        self.Bind(wx.EVT_MENU, self.on_about, about_item)

    def init_ui(self):
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # ── Navigation ────────────────────────────────────────────────
        nav_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.url_text = wx.TextCtrl(panel, value="https://google.com")
        nav_sizer.Add(self.url_text, 4, wx.ALL | wx.CENTER, 5)

        nav_btn = wx.Button(panel, label="Navigate")
        nav_btn.Bind(wx.EVT_BUTTON, self.on_navigate)
        nav_sizer.Add(nav_btn, 1, wx.ALL | wx.CENTER, 5)
        sizer.Add(nav_sizer, 0, wx.EXPAND)

        # ── Actions ───────────────────────────────────────────────────
        action_sizer = wx.GridSizer(2, 2, 10, 10)

        snap_btn = wx.Button(panel, label="Take Screenshot")
        snap_btn.Bind(wx.EVT_BUTTON, self.on_screenshot)
        action_sizer.Add(snap_btn, 1, wx.EXPAND)

        js_btn = wx.Button(panel, label="Execute JS")
        js_btn.Bind(wx.EVT_BUTTON, self.on_js)
        action_sizer.Add(js_btn, 1, wx.EXPAND)

        reset_btn = wx.Button(panel, label="Reset Profile")
        reset_btn.Bind(wx.EVT_BUTTON, self.on_reset)
        action_sizer.Add(reset_btn, 1, wx.EXPAND)

        ai_clear_btn = wx.Button(panel, label="Clear AI History")
        ai_clear_btn.Bind(wx.EVT_BUTTON, self.on_ai_clear)
        action_sizer.Add(ai_clear_btn, 1, wx.EXPAND)

        sizer.Add(action_sizer, 0, wx.EXPAND | wx.ALL, 20)

        # ── AI Section ────────────────────────────────────────────────
        sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND | wx.ALL, 5)
        ai_label = wx.StaticText(panel, label="AI Pilot")
        ai_label.SetFont(
            wx.Font(
                11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
            )
        )
        sizer.Add(ai_label, 0, wx.LEFT | wx.TOP, 10)

        ai_sizer = wx.BoxSizer(wx.HORIZONTAL)
        aiclick_btn = wx.Button(panel, label="AI Click")
        aiclick_btn.Bind(wx.EVT_BUTTON, self.on_ai_click)
        ai_sizer.Add(aiclick_btn, 1, wx.ALL, 5)

        aiquery_btn = wx.Button(panel, label="AI Query")
        aiquery_btn.Bind(wx.EVT_BUTTON, self.on_ai_query)
        ai_sizer.Add(aiquery_btn, 1, wx.ALL, 5)
        sizer.Add(ai_sizer, 0, wx.EXPAND)

        # ── Log ───────────────────────────────────────────────────────
        self.log_text = wx.TextCtrl(
            panel, style=wx.TE_MULTILINE | wx.TE_READONLY
        )
        sizer.Add(self.log_text, 2, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(sizer)
        self.CreateStatusBar()
        self.Show()

    # ── Helpers ────────────────────────────────────────────────────────

    def log(self, msg):
        self.log_text.AppendText(msg + "\n")

    def _run_async(self, label, func):
        """Run a BrowserPilot function in a thread to avoid blocking the UI."""
        self.log(f"{label}...")
        self.StatusBar.SetStatusText(f"{label}...")

        def _task():
            try:
                result = func()
                if result is not None:
                    wx.CallAfter(self.log, f"Result: {result}")
                wx.CallAfter(self.log, f"{label} — done.")
                wx.CallAfter(self.StatusBar.SetStatusText, "Ready")
            except Exception as e:
                wx.CallAfter(self.log, f"Error: {e}")
                wx.CallAfter(self.StatusBar.SetStatusText, f"Error: {e}")

        threading.Thread(target=_task, daemon=True).start()

    # ── Event handlers ────────────────────────────────────────────────

    def on_navigate(self, event):
        url = self.url_text.GetValue()
        self._run_async(f"Navigating to {url}", lambda: self.bp.open(url))

    def on_screenshot(self, event):
        path = "gui_screenshot.png"
        self._run_async(
            f"Screenshot → {path}", lambda: self.bp.screenshot(path)
        )

    def on_js(self, event):
        dlg = wx.TextEntryDialog(self, "Enter JS to execute:", "Execute JS")
        if dlg.ShowModal() == wx.ID_OK:
            script = dlg.GetValue()
            self._run_async(f"JS: {script}", lambda: self.bp.js(script))
        dlg.Destroy()

    def on_ai_click(self, event):
        dlg = wx.TextEntryDialog(
            self, "Describe what to click:", "AI Click"
        )
        if dlg.ShowModal() == wx.ID_OK:
            desc = dlg.GetValue()
            self._run_async(f"AI clicking: {desc}",
                            lambda: self.bp.ai_click(desc))
        dlg.Destroy()

    def on_ai_query(self, event):
        dlg = wx.TextEntryDialog(
            self, "Ask a question about the page:", "AI Query"
        )
        if dlg.ShowModal() == wx.ID_OK:
            q = dlg.GetValue()
            self._run_async(f"AI query: {q}", lambda: self.bp.ai_query(q))
        dlg.Destroy()

    def on_ai_clear(self, event):
        self.bp.ai_clear()
        self.log("AI conversation history cleared.")

    def on_reset(self, event):
        self.bp.reset()
        self.log("Browser profile cleared.")

    def on_about(self, event):
        about_text = (
            f"BrowserPilot v{CURRENT_VERSION}\n"
            "AI-powered browser automation engine.\n\n"
            "By Mohammed Maniruzzaman, PhD\n"
            "License: MIT\n\n"
            "Third-Party Components:\n"
            "- Playwright (Apache 2.0)\n"
            "- ollama (MIT)\n"
            "- httpx (BSD 3-Clause)\n"
            "- wxPython (LGPL)"
        )
        wx.MessageBox(
            about_text, "About BrowserPilot", wx.OK | wx.ICON_INFORMATION
        )

    def on_guide(self, event):
        import subprocess
        import sys
        import os

        guide_path = self.get_resource_path("USER_GUIDE.md")
        if guide_path.exists():
            if sys.platform == "darwin":
                subprocess.run(["open", str(guide_path)])
            elif sys.platform == "win32":
                os.startfile(str(guide_path))
            else:
                subprocess.run(["xdg-open", str(guide_path)])
        else:
            wx.MessageBox(
                f"User Guide not found at {guide_path}",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )


def main():
    set_macos_app_name("BrowserPilot")
    app = wx.App()
    wx.InitAllImageHandlers()
    app.SetAppName("BrowserPilot")
    app.SetAppDisplayName("BrowserPilot")
    BrowserPilotFrame()
    app.MainLoop()


if __name__ == "__main__":
    main()

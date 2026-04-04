import wx
import wx.html2
import markdown2
import threading
from pathlib import Path
from showmaster.core import Showmaster
from common.settings import is_dark_mode, check_for_updates, CURRENT_VERSION


# ── Dark / Light Theme CSS ──────────────────────────────────────────────

LIGHT_CSS = """
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    padding: 40px; line-height: 1.6; color: #24292e;
    max-width: 800px; margin: 0 auto; background: #fff;
}
pre { background: #f6f8fa; padding: 16px; border-radius: 6px; overflow-x: auto;
      font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace; }
code { background: rgba(27,31,35,0.05); padding: 0.2em 0.4em; border-radius: 3px; font-size: 85%; }
img { max-width: 100%; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.12); margin: 20px 0; }
h1 { border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }
h2 { border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }
blockquote { padding: 0 1em; color: #6a737d; border-left: 0.25em solid #dfe2e1; margin: 0; }
hr { height: 0.25em; padding: 0; margin: 24px 0; background-color: #e1e4e8; border: 0; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #dfe2e5; padding: 8px; text-align: left; }
th { background: #f6f8fa; }
"""

DARK_CSS = """
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    padding: 40px; line-height: 1.6; color: #c9d1d9;
    max-width: 800px; margin: 0 auto; background: #0d1117;
}
pre { background: #161b22; padding: 16px; border-radius: 6px; overflow-x: auto; color: #c9d1d9;
      font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace; }
code { background: rgba(240,246,252,0.1); padding: 0.2em 0.4em; border-radius: 3px; font-size: 85%; color: #c9d1d9; }
img { max-width: 100%; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.4); margin: 20px 0; }
h1 { border-bottom: 1px solid #21262d; padding-bottom: 0.3em; color: #f0f6fc; }
h2 { border-bottom: 1px solid #21262d; padding-bottom: 0.3em; color: #f0f6fc; }
h3 { color: #f0f6fc; }
a { color: #58a6ff; }
blockquote { padding: 0 1em; color: #8b949e; border-left: 0.25em solid #30363d; margin: 0; }
hr { height: 0.25em; padding: 0; margin: 24px 0; background-color: #21262d; border: 0; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #30363d; padding: 8px; text-align: left; color: #c9d1d9; }
th { background: #161b22; }
"""

# ── Dark Mode wxPython Colours ──────────────────────────────────────────

DARK_BG = wx.Colour(22, 27, 34)       # #161B22
DARK_FG = wx.Colour(201, 209, 217)    # #C9D1D9
DARK_PANEL = wx.Colour(13, 17, 23)    # #0D1117
DARK_INPUT = wx.Colour(33, 38, 45)    # #21262D
DARK_ACCENT = wx.Colour(88, 166, 255) # #58A6FF


def apply_dark_theme(widget, depth=0):
    """Recursively apply dark theme to a widget and its children."""
    if isinstance(widget, (wx.TextCtrl, wx.ComboBox)):
        widget.SetBackgroundColour(DARK_INPUT)
        widget.SetForegroundColour(DARK_FG)
    elif isinstance(widget, wx.Button):
        # Don't override accent buttons
        pass
    elif isinstance(widget, wx.StaticText):
        widget.SetForegroundColour(DARK_FG)
    elif isinstance(widget, wx.Panel):
        widget.SetBackgroundColour(DARK_PANEL)
    elif isinstance(widget, wx.Frame):
        widget.SetBackgroundColour(DARK_BG)

    if hasattr(widget, 'GetChildren'):
        for child in widget.GetChildren():
            apply_dark_theme(child, depth + 1)


class ShowmasterFrame(wx.Frame):
    def __init__(self, filename="demo.md"):
        super().__init__(None, title=f"Showmaster - {filename}", size=(1000, 800))
        self.filename = Path(filename)
        self.sm = Showmaster(self.filename)
        self.dark = is_dark_mode()

        self.init_menubar()
        self.init_icon()
        self.init_ui()
        self.update_preview()

        if self.dark:
            apply_dark_theme(self)
            self.Refresh()

        # Check for updates in background
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
            resource_path = base_path.parent.parent / "Resources" / relative_path
            if resource_path.exists():
                return resource_path

        return standalone_path

    def init_icon(self):
        wx.InitAllImageHandlers()
        icon_path = Path(__file__).parent / "assets" / "icon.png"
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

        # File Menu
        file_menu = wx.Menu()
        new_item = file_menu.Append(wx.ID_NEW, "&New\tCtrl+N")
        open_item = file_menu.Append(wx.ID_OPEN, "&Open\tCtrl+O")
        save_item = file_menu.Append(wx.ID_SAVE, "&Save\tCtrl+S")
        file_menu.AppendSeparator()
        finalize_item = file_menu.Append(wx.ID_ANY, "&Finalize Report\tCtrl+Shift+F")
        export_pdf_item = file_menu.Append(wx.ID_ANY, "Export as &PDF\tCtrl+Shift+P")
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl+Q")
        menubar.Append(file_menu, "&File")

        # Edit Menu
        edit_menu = wx.Menu()
        undo_item = edit_menu.Append(wx.ID_UNDO, "&Undo (Pop Last)\tCtrl+Z")
        edit_menu.AppendSeparator()
        prefs_item = edit_menu.Append(wx.ID_PREFERENCES, "&Preferences")
        menubar.Append(edit_menu, "&Edit")

        # Tools Menu
        tools_menu = wx.Menu()
        record_item = tools_menu.Append(wx.ID_ANY, "Start &Video Recording\tCtrl+R")
        stop_record_item = tools_menu.Append(wx.ID_ANY, "Stop Video Recording\tCtrl+Shift+R")
        tools_menu.AppendSeparator()
        browser_item = tools_menu.Append(wx.ID_ANY, "Open Browser Session")
        tools_menu.AppendSeparator()
        template_menu = wx.Menu()
        from showmaster.templates import list_templates
        self._template_items = {}
        for key, name, desc in list_templates():
            item = template_menu.Append(wx.ID_ANY, f"{name}\t{desc}")
            self._template_items[item.GetId()] = key
            self.Bind(wx.EVT_MENU, self.on_template, item)
        tools_menu.AppendSubMenu(template_menu, "New from &Template")
        menubar.Append(tools_menu, "&Tools")

        # Help Menu
        help_menu = wx.Menu()
        guide_item = help_menu.Append(wx.ID_ANY, "User &Guide\tF1")
        about_item = help_menu.Append(wx.ID_ABOUT, "&About")
        menubar.Append(help_menu, "&Help")

        self.SetMenuBar(menubar)

        # Bindings
        self.Bind(wx.EVT_MENU, self.on_pop, undo_item)
        self.Bind(wx.EVT_MENU, self.on_finalize, finalize_item)
        self.Bind(wx.EVT_MENU, self.on_export_pdf, export_pdf_item)
        self.Bind(wx.EVT_MENU, lambda e: self.Close(), exit_item)
        self.Bind(wx.EVT_MENU, self.on_start_record, record_item)
        self.Bind(wx.EVT_MENU, self.on_stop_record, stop_record_item)
        self.Bind(wx.EVT_MENU, self.on_open_browser, browser_item)
        self.Bind(wx.EVT_MENU, self.on_guide, guide_item)
        self.Bind(wx.EVT_MENU, self.on_about, about_item)

    def init_ui(self):
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Left side: Controls
        left_panel = wx.Panel(panel)
        left_sizer = wx.BoxSizer(wx.VERTICAL)

        # Title
        title_label = wx.StaticText(left_panel, label="Showmaster Controls")
        title_label.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        left_sizer.Add(title_label, 0, wx.ALL | wx.EXPAND, 10)

        # Note
        self.note_text = wx.TextCtrl(left_panel, style=wx.TE_MULTILINE, size=(-1, 100))
        left_sizer.Add(wx.StaticText(left_panel, label="Add Note:"), 0, wx.LEFT | wx.TOP, 10)
        left_sizer.Add(self.note_text, 0, wx.ALL | wx.EXPAND, 10)

        note_btn = wx.Button(left_panel, label="Add Note")
        note_btn.Bind(wx.EVT_BUTTON, self.on_add_note)
        left_sizer.Add(note_btn, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        # Exec
        self.exec_text = wx.TextCtrl(left_panel)
        left_sizer.Add(wx.StaticText(left_panel, label="Execute Command:"), 0, wx.LEFT | wx.TOP, 10)
        left_sizer.Add(self.exec_text, 0, wx.ALL | wx.EXPAND, 10)

        exec_btn = wx.Button(left_panel, label="Run Exec")
        exec_btn.Bind(wx.EVT_BUTTON, self.on_run_exec)
        left_sizer.Add(exec_btn, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        # Image
        img_btn = wx.Button(left_panel, label="Run Image Command")
        img_btn.Bind(wx.EVT_BUTTON, self.on_run_image)
        left_sizer.Add(img_btn, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        # Action Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        pop_btn = wx.Button(left_panel, label="Undo Last")
        pop_btn.Bind(wx.EVT_BUTTON, self.on_pop)
        btn_sizer.Add(pop_btn, 1, wx.RIGHT, 5)

        finalize_btn = wx.Button(left_panel, label="Finalize")
        finalize_btn.SetBackgroundColour(wx.Colour(0, 120, 215))
        finalize_btn.SetForegroundColour(wx.WHITE)
        finalize_btn.Bind(wx.EVT_BUTTON, self.on_finalize)
        btn_sizer.Add(finalize_btn, 1, wx.LEFT, 5)

        left_sizer.Add(btn_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # Web Capture Section
        left_sizer.Add(wx.StaticLine(left_panel), 0, wx.EXPAND | wx.ALL, 5)
        web_label = wx.StaticText(left_panel, label="Web Capture")
        web_label.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        left_sizer.Add(web_label, 0, wx.LEFT | wx.TOP, 10)

        self.url_text = wx.TextCtrl(left_panel, value="https://google.com")
        left_sizer.Add(self.url_text, 0, wx.ALL | wx.EXPAND, 10)

        web_btn = wx.Button(left_panel, label="Capture Page")
        web_btn.Bind(wx.EVT_BUTTON, self.on_browser_snap)
        left_sizer.Add(web_btn, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        # Video Section
        left_sizer.Add(wx.StaticLine(left_panel), 0, wx.EXPAND | wx.ALL, 5)
        vid_label = wx.StaticText(left_panel, label="Video Recording")
        vid_label.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        left_sizer.Add(vid_label, 0, wx.LEFT | wx.TOP, 10)

        vid_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.start_vid_btn = wx.Button(left_panel, label="Start")
        self.start_vid_btn.Bind(wx.EVT_BUTTON, self.on_start_record)
        vid_btn_sizer.Add(self.start_vid_btn, 1, wx.RIGHT, 5)

        self.stop_vid_btn = wx.Button(left_panel, label="Stop")
        self.stop_vid_btn.Bind(wx.EVT_BUTTON, self.on_stop_record)
        self.stop_vid_btn.Disable()
        vid_btn_sizer.Add(self.stop_vid_btn, 1, wx.LEFT, 5)

        left_sizer.Add(vid_btn_sizer, 0, wx.ALL | wx.EXPAND, 10)

        left_panel.SetSizer(left_sizer)
        main_sizer.Add(left_panel, 1, wx.EXPAND)

        # Right side: Preview
        self.browser = wx.html2.WebView.New(panel)
        main_sizer.Add(self.browser, 2, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(main_sizer)
        self.CreateStatusBar()
        self.Show()

    def update_preview(self):
        if self.filename.exists():
            content = self.filename.read_text()
            html = markdown2.markdown(content)
            css = DARK_CSS if self.dark else LIGHT_CSS
            styled_html = f"""<html><head><style>{css}</style></head><body>{html}</body></html>"""
            self.browser.SetPage(styled_html, "")

    # ── Event handlers ────────────────────────────────────────────────

    def on_add_note(self, event):
        text = self.note_text.GetValue()
        if text:
            self.sm.note(text)
            self.note_text.Clear()
            self.update_preview()

    def on_run_exec(self, event):
        cmd = self.exec_text.GetValue()
        if cmd:
            self.sm.exec(cmd)
            self.exec_text.Clear()
            self.update_preview()

    def on_run_image(self, event):
        cmd = self.exec_text.GetValue()
        if cmd:
            self.sm.image(cmd)
            self.exec_text.Clear()
            self.update_preview()

    def on_pop(self, event):
        self.sm.pop()
        self.update_preview()

    def on_finalize(self, event):
        res = self.sm.finalize()
        wx.MessageBox(res, "Finalize", wx.OK | wx.ICON_INFORMATION)
        self.update_preview()

    def on_export_pdf(self, event):
        msg = self.sm.export_pdf()
        wx.MessageBox(msg, "Export PDF", wx.OK | wx.ICON_INFORMATION)

    def on_template(self, event):
        key = self._template_items.get(event.GetId())
        if key:
            dlg = wx.TextEntryDialog(self, "Enter report title:", f"New {key} Report")
            if dlg.ShowModal() == wx.ID_OK:
                title = dlg.GetValue()
                from showmaster.templates import apply_template
                apply_template(key, self.filename, title=title)
                self.sm = Showmaster(self.filename)  # Reinit
                self.update_preview()
                self.StatusBar.SetStatusText(f"Template '{key}' applied.")
            dlg.Destroy()

    def on_browser_snap(self, event):
        url = self.url_text.GetValue()
        if url:
            self.StatusBar.SetStatusText(f"Capturing {url}...")

            def _task():
                try:
                    res = self.sm.browser_snap(url)
                    wx.CallAfter(self.update_preview)
                    wx.CallAfter(self.StatusBar.SetStatusText, res)
                except Exception as e:
                    wx.CallAfter(self.StatusBar.SetStatusText, f"Error: {e}")
            threading.Thread(target=_task, daemon=True).start()

    def on_start_record(self, event):
        res = self.sm.start_record()
        self.StatusBar.SetStatusText(res)
        self.start_vid_btn.Disable()
        self.stop_vid_btn.Enable()

    def on_stop_record(self, event):
        res = self.sm.stop_record()
        self.StatusBar.SetStatusText(res)
        self.start_vid_btn.Enable()
        self.stop_vid_btn.Disable()
        self.update_preview()

    def on_about(self, event):
        about_text = (
            f"Showmaster v{CURRENT_VERSION}\n"
            "A comprehensive documentation and demo tool.\n\n"
            "By Mohammed Maniruzzaman, PhD\n"
            "License: MIT\n\n"
            "Third-Party Components:\n"
            "- wxPython (LGPL)\n"
            "- Playwright (Apache 2.0)\n"
            "- markdown2 (MIT)\n"
            "- httpx (BSD 3-Clause)\n"
            "- mss (MIT)\n"
            "- opencv-python (Apache 2.0)\n"
            "- numpy (BSD 3-Clause)"
        )
        wx.MessageBox(about_text, "About Showmaster", wx.OK | wx.ICON_INFORMATION)

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
            wx.MessageBox(f"User Guide not found at {guide_path}", "Error", wx.OK | wx.ICON_ERROR)

    def on_open_browser(self, event):
        import subprocess
        import sys
        subprocess.Popen([sys.executable, "-m", "browserpilot.gui"])


def main():
    app = wx.App()
    wx.InitAllImageHandlers()
    app.SetAppName("Showmaster")
    app.SetAppDisplayName("Showmaster")
    ShowmasterFrame("demo.md")
    app.MainLoop()


if __name__ == '__main__':
    main()

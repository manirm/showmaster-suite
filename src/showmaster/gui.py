import wx
import wx.html2
import wx.stc
import markdown2
import threading
import time
from pathlib import Path
from showmaster.core import Showmaster
from common.settings import (
    check_for_updates, load_settings, save_settings,
    set_macos_app_name,
    CURRENT_VERSION,
)
from common.gui_utils import (
    is_dark_mode, apply_dark_theme, get_resource_path, BusyContext
)
from common.logger import get_logger

logger = get_logger("gui")


# ── Theme CSS ─────────────────────────────────────────────────────────

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
    padding: 40px; line-height: 1.6; color: #adbac7;
    max-width: 800px; margin: 0 auto; background: #22272e;
}
pre { background: #2d333b; padding: 16px; border-radius: 6px; overflow-x: auto; color: #adbac7;
      font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace; }
code { background: rgba(99,110,123,0.2); padding: 0.2em 0.4em; border-radius: 3px; font-size: 85%; color: #adbac7; }
img { max-width: 100%; border-radius: 6px; box-shadow: 0 4px 12px rgba(0,0,0,0.5); margin: 24px 0; }
h1 { border-bottom: 1px solid #444c56; padding-bottom: 0.3em; color: #cdd9e5; }
h2 { border-bottom: 1px solid #444c56; padding-bottom: 0.3em; color: #cdd9e5; }
h3 { color: #cdd9e5; }
a { color: #539bf5; }
blockquote { padding: 0 1em; color: #768390; border-left: 0.25em solid #444c56; margin: 0; }
hr { height: 0.25em; padding: 0; margin: 24px 0; background-color: #444c56; border: 0; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #444c56; padding: 8px; text-align: left; color: #adbac7; }
th { background: #2d333b; }
"""

# ── Dark Mode wxPython Colours ────────────────────────────────────────

DARK_BG = wx.Colour(22, 27, 34)
DARK_FG = wx.Colour(201, 209, 217)
DARK_PANEL = wx.Colour(13, 17, 23)
DARK_INPUT = wx.Colour(33, 38, 45)


def load_custom_css():
    """Load user's custom CSS theme if it exists."""
    custom_path = Path.home() / ".showmaster" / "themes" / "custom.css"
    if custom_path.exists():
        return custom_path.read_text()
    return None


class ShowmasterFrame(wx.Frame):
    def __init__(self, filename="demo.md"):
        super().__init__(None, title=f"Showmaster — {filename}", size=(1200, 850))
        self.filename = Path(filename)
        self.sm = Showmaster(self.filename)
        self.dark = is_dark_mode()
        self._last_mtime = 0  # For auto-refresh
        self._autosave_dirty = False

        self.init_menubar()
        self.init_icon()
        self.init_ui()
        self.update_preview()

        if self.dark:
            apply_dark_theme(self, DARK_BG, DARK_FG, DARK_PANEL, DARK_INPUT)
            # Style the Scintilla editor for dark mode
            self._apply_dark_to_editor()
            self.Refresh()

        # Background tasks
        self._check_updates()
        self._start_auto_refresh()
        self._start_autosave()

    # ── Background Tasks ──────────────────────────────────────────────

    def _check_updates(self):
        def _task():
            has_update, latest = check_for_updates()
            if has_update:
                wx.CallAfter(
                    self.StatusBar.SetStatusText,
                    f"Update available: v{latest} (current: v{CURRENT_VERSION})"
                )
        threading.Thread(target=_task, daemon=True).start()

    def _start_auto_refresh(self):
        """Poll the file for changes every 2 seconds and auto-refresh preview."""
        self._refresh_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_auto_refresh, self._refresh_timer)
        self._refresh_timer.Start(2000)

    def _on_auto_refresh(self, event):
        if self.filename.exists():
            mtime = self.filename.stat().st_mtime
            if mtime != self._last_mtime:
                self._last_mtime = mtime
                self.update_preview()
                # Also sync the editor if it wasn't the source of the change
                if not self._autosave_dirty:
                    self.editor.SetText(self.sm.get_text())

    def _start_autosave(self):
        """Auto-save every 30 seconds if there are unsaved changes."""
        self._autosave_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_autosave, self._autosave_timer)
        self._autosave_timer.Start(30000)

    def _on_autosave(self, event):
        if self._autosave_dirty:
            self._save_editor_to_file()
            self.StatusBar.SetStatusText("Auto-saved")

    def _save_editor_to_file(self):
        content = self.editor.GetText()
        with self.sm._lock:
            self.filename.write_text(content)
        self._autosave_dirty = False
        self._last_mtime = self.filename.stat().st_mtime

    # ── Resource Path ─────────────────────────────────────────────────

    def get_resource_path(self, relative_path):
        return get_resource_path(__file__, relative_path)

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
            except Exception:
                pass

    # ── Menu ──────────────────────────────────────────────────────────

    def init_menubar(self):
        menubar = wx.MenuBar()

        # File
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

        # Edit
        edit_menu = wx.Menu()
        undo_item = edit_menu.Append(wx.ID_UNDO, "&Undo (Pop Last)\tCtrl+Z")
        edit_menu.AppendSeparator()
        prefs_item = edit_menu.Append(wx.ID_PREFERENCES, "&Preferences")
        menubar.Append(edit_menu, "&Edit")

        # View
        view_menu = wx.Menu()
        self.editor_toggle = view_menu.AppendCheckItem(wx.ID_ANY, "Show &Editor\tCtrl+E")
        self.editor_toggle.Check(True)
        menubar.Append(view_menu, "&View")

        # Tools
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

        # Help
        help_menu = wx.Menu()
        guide_item = help_menu.Append(wx.ID_ANY, "User &Guide\tF1")
        about_item = help_menu.Append(wx.ID_ABOUT, "&About")
        menubar.Append(help_menu, "&Help")

        self.SetMenuBar(menubar)

        # Bindings
        self.Bind(wx.EVT_MENU, self.on_new, new_item)
        self.Bind(wx.EVT_MENU, self.on_open, open_item)
        self.Bind(wx.EVT_MENU, self.on_save, save_item)
        self.Bind(wx.EVT_MENU, self.on_pop, undo_item)
        self.Bind(wx.EVT_MENU, self.on_finalize, finalize_item)
        self.Bind(wx.EVT_MENU, self.on_export_pdf, export_pdf_item)
        self.Bind(wx.EVT_MENU, lambda e: self.Close(), exit_item)
        self.Bind(wx.EVT_MENU, self.on_toggle_editor, self.editor_toggle)
        self.Bind(wx.EVT_MENU, self.on_start_record, record_item)
        self.Bind(wx.EVT_MENU, self.on_stop_record, stop_record_item)
        self.Bind(wx.EVT_MENU, self.on_open_browser, browser_item)
        self.Bind(wx.EVT_MENU, self.on_guide, guide_item)
        self.Bind(wx.EVT_MENU, self.on_about, about_item)

    # ── UI ────────────────────────────────────────────────────────────

    def init_ui(self):
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # ── Left: Controls ────────────────────────────────────────────
        left_panel = wx.Panel(panel)
        left_panel.SetMinSize((280, -1))
        left_sizer = wx.BoxSizer(wx.VERTICAL)

        # Title
        title_label = wx.StaticText(left_panel, label="Showmaster")
        title_label.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        left_sizer.Add(title_label, 0, wx.ALL | wx.EXPAND, 10)

        # Note
        self.note_text = wx.TextCtrl(left_panel, style=wx.TE_MULTILINE, size=(-1, 80))
        left_sizer.Add(wx.StaticText(left_panel, label="Add Note:"), 0, wx.LEFT | wx.TOP, 10)
        left_sizer.Add(self.note_text, 0, wx.ALL | wx.EXPAND, 5)
        note_btn = wx.Button(left_panel, label="Add Note")
        note_btn.Bind(wx.EVT_BUTTON, self.on_add_note)
        left_sizer.Add(note_btn, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)

        # Exec
        self.exec_text = wx.TextCtrl(left_panel)
        left_sizer.Add(wx.StaticText(left_panel, label="Execute:"), 0, wx.LEFT | wx.TOP, 10)
        left_sizer.Add(self.exec_text, 0, wx.ALL | wx.EXPAND, 5)

        exec_sizer = wx.BoxSizer(wx.HORIZONTAL)
        exec_btn = wx.Button(left_panel, label="Run")
        exec_btn.Bind(wx.EVT_BUTTON, self.on_run_exec)
        exec_sizer.Add(exec_btn, 1, wx.RIGHT, 3)
        img_btn = wx.Button(left_panel, label="Image")
        img_btn.Bind(wx.EVT_BUTTON, self.on_run_image)
        exec_sizer.Add(img_btn, 1, wx.LEFT, 3)
        left_sizer.Add(exec_sizer, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)

        # Action buttons
        left_sizer.Add(wx.StaticLine(left_panel), 0, wx.EXPAND | wx.ALL, 5)
        
        self.unsafe_cb = wx.CheckBox(left_panel, label="Allow Shell Pipes (Unsafe)")
        self.unsafe_cb.SetToolTip("Enable this to use pipes (|), redirection (>), or shell built-ins.")
        self.unsafe_cb.Bind(wx.EVT_CHECKBOX, self.on_toggle_unsafe)
        left_sizer.Add(self.unsafe_cb, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        pop_btn = wx.Button(left_panel, label="Undo Last")
        pop_btn.Bind(wx.EVT_BUTTON, self.on_pop)
        btn_sizer.Add(pop_btn, 1, wx.RIGHT, 3)
        finalize_btn = wx.Button(left_panel, label="Finalize")
        finalize_btn.SetBackgroundColour(wx.Colour(0, 120, 215))
        finalize_btn.SetForegroundColour(wx.WHITE)
        finalize_btn.Bind(wx.EVT_BUTTON, self.on_finalize)
        btn_sizer.Add(finalize_btn, 1, wx.LEFT, 3)
        left_sizer.Add(btn_sizer, 0, wx.ALL | wx.EXPAND, 5)

        # Web Capture
        left_sizer.Add(wx.StaticLine(left_panel), 0, wx.EXPAND | wx.ALL, 3)
        web_label = wx.StaticText(left_panel, label="Web Capture")
        web_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        left_sizer.Add(web_label, 0, wx.LEFT | wx.TOP, 10)
        self.url_text = wx.TextCtrl(left_panel, value="https://google.com")
        left_sizer.Add(self.url_text, 0, wx.ALL | wx.EXPAND, 5)
        web_btn = wx.Button(left_panel, label="Capture Page")
        web_btn.Bind(wx.EVT_BUTTON, self.on_browser_snap)
        left_sizer.Add(web_btn, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)

        # Video
        left_sizer.Add(wx.StaticLine(left_panel), 0, wx.EXPAND | wx.ALL, 3)
        vid_label = wx.StaticText(left_panel, label="Video")
        vid_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        left_sizer.Add(vid_label, 0, wx.LEFT | wx.TOP, 10)
        vid_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.start_vid_btn = wx.Button(left_panel, label="Start")
        self.start_vid_btn.Bind(wx.EVT_BUTTON, self.on_start_record)
        vid_sizer.Add(self.start_vid_btn, 1, wx.RIGHT, 3)
        self.stop_vid_btn = wx.Button(left_panel, label="Stop")
        self.stop_vid_btn.Bind(wx.EVT_BUTTON, self.on_stop_record)
        self.stop_vid_btn.Disable()
        vid_sizer.Add(self.stop_vid_btn, 1, wx.LEFT, 3)
        left_sizer.Add(vid_sizer, 0, wx.ALL | wx.EXPAND, 5)

        left_panel.SetSizer(left_sizer)
        main_sizer.Add(left_panel, 0, wx.EXPAND)

        # ── Center: Split pane (Editor + Preview) ─────────────────────
        center_panel = wx.Panel(panel)
        center_sizer = wx.BoxSizer(wx.VERTICAL)

        # Formatting Toolbar
        fmt_toolbar = wx.BoxSizer(wx.HORIZONTAL)
        
        def _fmt_btn(label, hint, func, size=(30, 30), bold=False):
            btn = wx.Button(center_panel, label=label, size=size)
            if bold:
                btn.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            btn.SetToolTip(hint)
            btn.Bind(wx.EVT_BUTTON, func)
            return btn

        fmt_toolbar.Add(_fmt_btn("B", "Bold", lambda e: self._wrap_selection("**", "**"), bold=True), 0, wx.RIGHT, 2)
        fmt_toolbar.Add(_fmt_btn("I", "Italic", lambda e: self._wrap_selection("*", "*")), 0, wx.RIGHT, 2)
        fmt_toolbar.Add(_fmt_btn("H", "Header", lambda e: self._wrap_selection("### ", "")), 0, wx.RIGHT, 2)
        fmt_toolbar.Add(_fmt_btn("Code", "Code Block", lambda e: self._wrap_selection("```\n", "\n```"), size=(50, 30)), 0, wx.RIGHT, 2)
        fmt_toolbar.Add(_fmt_btn("Link", "Insert Link", lambda e: self._wrap_selection("[", "](url)"), size=(50, 30)), 0, wx.RIGHT, 2)
        
        center_sizer.Add(fmt_toolbar, 0, wx.EXPAND | wx.BOTTOM, 5)

        self.splitter = wx.SplitterWindow(center_panel, style=wx.SP_LIVE_UPDATE)

        # Editor (Scintilla)
        self.editor = wx.stc.StyledTextCtrl(self.splitter)
        self.editor.SetLexer(wx.stc.STC_LEX_MARKDOWN)
        self.editor.SetMarginType(0, wx.stc.STC_MARGIN_NUMBER)
        self.editor.SetMarginWidth(0, 40)
        self.editor.SetTabWidth(4)
        self.editor.SetUseTabs(False)
        self.editor.SetWrapMode(wx.stc.STC_WRAP_WORD)
        font = wx.Font(12, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="Menlo")
        self.editor.StyleSetFont(wx.stc.STC_STYLE_DEFAULT, font)
        self.editor.StyleClearAll()
        if self.filename.exists():
            self.editor.SetText(self.filename.read_text())
        self.editor.Bind(wx.stc.EVT_STC_MODIFIED, self.on_editor_modified)

        # Enable drag & drop for images
        self.editor.SetDropTarget(ImageDropTarget(self))

        # Preview
        self.browser = wx.html2.WebView.New(self.splitter)

        self.splitter.SplitVertically(self.editor, self.browser, 400)
        self.splitter.SetMinimumPaneSize(200)

        center_sizer.Add(self.splitter, 1, wx.EXPAND)
        center_panel.SetSizer(center_sizer)

        main_sizer.Add(center_panel, 1, wx.EXPAND | wx.ALL, 3)

        panel.SetSizer(main_sizer)
        self.CreateStatusBar(2)
        self.SetStatusWidths([-1, 150])
        self.SetStatusText("Safe Mode 🛡️", 1)
        self.Show()

    def _apply_dark_to_editor(self):
        """Style the Scintilla editor for dark mode."""
        self.editor.StyleSetBackground(wx.stc.STC_STYLE_DEFAULT, wx.Colour(13, 17, 23))
        self.editor.StyleSetForeground(wx.stc.STC_STYLE_DEFAULT, wx.Colour(201, 209, 217))
        self.editor.StyleClearAll()
        self.editor.SetCaretForeground(wx.Colour(201, 209, 217))
        # Markdown heading styles
        for style_num in range(wx.stc.STC_MARKDOWN_HEADER1, wx.stc.STC_MARKDOWN_HEADER6 + 1):
            self.editor.StyleSetForeground(style_num, wx.Colour(88, 166, 255))
            self.editor.StyleSetBold(style_num, True)
        # Code
        self.editor.StyleSetForeground(wx.stc.STC_MARKDOWN_CODE, wx.Colour(230, 237, 243))
        self.editor.StyleSetBackground(wx.stc.STC_MARKDOWN_CODE, wx.Colour(33, 38, 45))
        self.editor.StyleSetForeground(wx.stc.STC_MARKDOWN_CODE2, wx.Colour(230, 237, 243))
        self.editor.StyleSetBackground(wx.stc.STC_MARKDOWN_CODE2, wx.Colour(33, 38, 45))
        # Line numbers
        self.editor.StyleSetBackground(wx.stc.STC_STYLE_LINENUMBER, wx.Colour(22, 27, 34))
        self.editor.StyleSetForeground(wx.stc.STC_STYLE_LINENUMBER, wx.Colour(110, 118, 129))

    # ── Preview ───────────────────────────────────────────────────────

    def update_preview(self):
        if self.filename.exists():
            content = self.sm.get_text()
            html = markdown2.markdown(content, extras=["tables", "fenced-code-blocks"])
            # Inline images as base64 data URIs (macOS WebView blocks file://)
            html = self._inline_images(html)
            custom_css = load_custom_css()
            css = custom_css or (DARK_CSS if self.dark else LIGHT_CSS)
            styled_html = f"<html><head><style>{css}</style></head><body>{html}</body></html>"
            self.browser.SetPage(styled_html, "")

    def _inline_images(self, html):
        """Replace relative <img src="..."> with base64 data URIs."""
        import re
        import base64
        import mimetypes

        base_dir = self.filename.absolute().parent

        def _replace_img(match):
            prefix = match.group(1)
            src = match.group(2)
            suffix = match.group(3)

            # Skip if already a URL or data URI
            if src.startswith(("http://", "https://", "data:")):
                return match.group(0)

            img_path = base_dir / src
            if img_path.exists():
                try:
                    mime, _ = mimetypes.guess_type(str(img_path))
                    if not mime:
                        mime = "image/png"
                    b64 = base64.b64encode(img_path.read_bytes()).decode()
                    return f'{prefix}data:{mime};base64,{b64}{suffix}'
                except Exception:
                    pass
            return match.group(0)

        return re.sub(r'(<img\s[^>]*src=["\'])([^"\']+)(["\'])', _replace_img, html)

    # ── Event Handlers ────────────────────────────────────────────────

    def on_editor_modified(self, event):
        mod_type = event.GetModificationType()
        if mod_type & (wx.stc.STC_MOD_INSERTTEXT | wx.stc.STC_MOD_DELETETEXT):
            self._autosave_dirty = True

    def on_new(self, event):
        dlg = wx.TextEntryDialog(self, "Enter report title:", "New Report")
        if dlg.ShowModal() == wx.ID_OK:
            self.sm.init(dlg.GetValue())
            self.editor.SetText(self.sm.get_text())
            self.update_preview()
        dlg.Destroy()

    def on_open(self, event):
        dlg = wx.FileDialog(self, "Open Markdown", wildcard="Markdown (*.md)|*.md",
                            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = Path(dlg.GetPath())
            self.sm = Showmaster(self.filename)
            self.editor.SetText(self.sm.get_text())
            self.update_preview()
            self.SetTitle(f"Showmaster — {self.filename.name}")
        dlg.Destroy()

    def on_save(self, event):
        self._save_editor_to_file()
        self.update_preview()
        self.StatusBar.SetStatusText(f"Saved {self.filename}")

    def on_add_note(self, event):
        text = self.note_text.GetValue()
        if text:
            self.sm.note(text)
            self.note_text.Clear()
            self.editor.SetText(self.sm.get_text())
            self.update_preview()

    def on_run_exec(self, event):
        cmd = self.exec_text.GetValue()
        if cmd:
            use_raw = self.unsafe_cb.GetValue()
            self.StatusBar.SetStatusText(f"Running {'(raw) ' if use_raw else ''}{cmd}...")
            def _task():
                with BusyContext(self, [self.exec_text]):
                    if use_raw:
                        self.sm.raw_exec(cmd)
                    else:
                        self.sm.exec(cmd)
                    wx.CallAfter(self.editor.SetText, self.filename.read_text())
                    wx.CallAfter(self.update_preview)
                    wx.CallAfter(self.StatusBar.SetStatusText, "Ready")
            threading.Thread(target=_task, daemon=True).start()
            self.exec_text.Clear()

    def on_run_image(self, event):
        cmd = self.exec_text.GetValue()
        if cmd:
            self.sm.image(cmd)
            self.exec_text.Clear()
            self.editor.SetText(self.filename.read_text())
            self.update_preview()

    def on_pop(self, event):
        self.sm.pop()
        self.editor.SetText(self.filename.read_text())
        self.update_preview()

    def on_finalize(self, event):
        self._save_editor_to_file()
        logger.info("Finalizing report...")
        res = self.sm.finalize()
        self.editor.SetText(self.sm.get_text())
        self.update_preview()
        wx.MessageBox(res, "Finalize", wx.OK | wx.ICON_INFORMATION)
        logger.info("Report finalized successfully.")

    def on_export_pdf(self, event):
        self._save_editor_to_file()
        msg = self.sm.export_pdf()
        wx.MessageBox(msg, "Export PDF", wx.OK | wx.ICON_INFORMATION)

    def on_template(self, event):
        key = self._template_items.get(event.GetId())
        if key:
            dlg = wx.TextEntryDialog(self, "Enter report title:", f"New {key} Report")
            if dlg.ShowModal() == wx.ID_OK:
                from showmaster.templates import apply_template
                apply_template(key, self.filename, title=dlg.GetValue())
                self.sm = Showmaster(self.filename)
                self.editor.SetText(self.sm.get_text())
                self.update_preview()
                self.StatusBar.SetStatusText(f"Template '{key}' applied.")
            dlg.Destroy()

    def on_toggle_editor(self, event):
        if self.editor_toggle.IsChecked():
            self.splitter.SplitVertically(self.editor, self.browser, 400)
        else:
            self.splitter.Unsplit(self.editor)

    def on_browser_snap(self, event):
        url = self.url_text.GetValue()
        if url:
            self.StatusBar.SetStatusText(f"Capturing {url}...")
            def _task():
                # Use BusyContext in the UI thread
                with BusyContext(self, [self.url_text]):
                    try:
                        logger.info(f"Starting browser capture for: {url}")
                        res = self.sm.browser_snap(url)
                        wx.CallAfter(self.editor.SetText, self.sm.get_text())
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
        self.editor.SetText(self.sm.get_text())
        self.update_preview()

    def on_toggle_unsafe(self, event):
        enabled = self.unsafe_cb.GetValue()
        self.sm.unsafe_mode = enabled
        if enabled:
            self.SetStatusText("⚠️ UNSAFE MODE", 1)
        else:
            self.SetStatusText("Safe Mode 🛡️", 1)

    def on_about(self, event):
        about_text = (
            f"Showmaster v{CURRENT_VERSION}\n"
            "Documentation & demo tool with live editor.\n\n"
            "By Mohammed Maniruzzaman, PhD\n"
            "License: MIT"
        )
        wx.MessageBox(about_text, "About Showmaster", wx.OK | wx.ICON_INFORMATION)

    def on_guide(self, event):
        import subprocess, sys, os
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

    def _wrap_selection(self, prefix, suffix):
        """Wrap selected text in the editor with the given prefix and suffix."""
        start, end = self.editor.GetSelection()
        if start == end:
            # No selection, just insert at cursor
            pos = self.editor.GetCurrentPos()
            self.editor.InsertText(pos, prefix + suffix)
            self.editor.SetSelection(pos + len(prefix), pos + len(prefix))
        else:
            text = self.editor.GetSelectedText()
            self.editor.ReplaceSelection(prefix + text + suffix)
        self.editor.SetFocus()

    def on_open_browser(self, event):
        import subprocess, sys
        subprocess.Popen([sys.executable, "-m", "browserpilot.gui"])

    def embed_image(self, path):
        """Embed an image file into the report (called by drag & drop)."""
        import shutil
        src = Path(path)
        if src.exists() and src.suffix.lower() in ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'):
            dest = self.filename.parent / src.name
            if src.absolute() != dest.absolute():
                shutil.copy(src, dest)
            with self.sm._lock:
                with self.filename.open("a") as f:
                    f.write(f"\n![{src.name}]({src.name})\n\n")
            self.editor.SetText(self.sm.get_text())
            self.update_preview()
            self.StatusBar.SetStatusText(f"Embedded image: {src.name}")


class ImageDropTarget(wx.FileDropTarget):
    """Drag & drop handler for image files."""

    def __init__(self, frame):
        super().__init__()
        self.frame = frame

    def OnDropFiles(self, x, y, filenames):
        for f in filenames:
            self.frame.embed_image(f)
        return True


def main():
    set_macos_app_name("Showmaster")
    app = wx.App()
    wx.InitAllImageHandlers()
    app.SetAppName("Showmaster")
    app.SetAppDisplayName("Showmaster")
    ShowmasterFrame("demo.md")
    app.MainLoop()


if __name__ == '__main__':
    main()

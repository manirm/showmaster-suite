import wx
import json
from pathlib import Path
import os
import signal
from browserpilot.core import BrowserPilot

SESSION_FILE = Path(".browserpilot_session.json")

class BrowserPilotFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="BrowserPilot Control Center", size=(800, 700))
        self.bp = BrowserPilot()
        
        self.init_menubar()
        self.init_icon()
        self.init_ui()
        self.check_session()

    def get_resource_path(self, relative_path):
        import sys
        
        # Check standard dev path first
        dev_path = Path(__file__).parent.parent.parent / relative_path
        if dev_path.exists():
            return dev_path
            
        # In Nuitka standalone, files are typically in the same dir as the executable
        base_path = Path(sys.executable).parent
        standalone_path = base_path / relative_path
        if standalone_path.exists():
            return standalone_path
            
        if sys.platform == "darwin" and ".app/Contents/MacOS" in str(base_path):
            # Fallback for macOS app bundle if Nuitka put them in Resources
            resource_path = base_path.parent.parent / "Resources" / relative_path
            if resource_path.exists():
                return resource_path
                
        return standalone_path

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
        exit_item = file_menu.Append(wx.ID_EXIT, "E&xit")
        menubar.Append(file_menu, "&File")
        
        edit_menu = wx.Menu()
        prefs_item = edit_menu.Append(wx.ID_PREFERENCES, "&Preferences")
        menubar.Append(edit_menu, "&Edit")
        
        help_menu = wx.Menu()
        guide_item = help_menu.Append(wx.ID_ANY, "User &Guide")
        about_item = help_menu.Append(wx.ID_ABOUT, "&About")
        menubar.Append(help_menu, "&Help")
        
        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, lambda e: self.Close(), exit_item)
        self.Bind(wx.EVT_MENU, self.on_guide, guide_item)
        self.Bind(wx.EVT_MENU, self.on_about, about_item)
        
    def init_ui(self):
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Session Status
        self.status_label = wx.StaticText(panel, label="Session: Not started")
        sizer.Add(self.status_label, 0, wx.ALL | wx.EXPAND, 10)
        
        # Start/Stop Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.start_btn = wx.Button(panel, label="Start Session")
        self.start_btn.Bind(wx.EVT_BUTTON, self.on_start)
        btn_sizer.Add(self.start_btn, 1, wx.ALL, 5)
        
        self.stop_btn = wx.Button(panel, label="Stop Session")
        self.stop_btn.Bind(wx.EVT_BUTTON, self.on_stop)
        self.stop_btn.Disable()
        btn_sizer.Add(self.stop_btn, 1, wx.ALL, 5)
        
        sizer.Add(btn_sizer, 0, wx.EXPAND)
        
        # Navigation
        nav_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.url_text = wx.TextCtrl(panel, value="https://google.com")
        nav_sizer.Add(self.url_text, 4, wx.ALL | wx.CENTER, 5)
        
        nav_btn = wx.Button(panel, label="Go")
        nav_btn.Bind(wx.EVT_BUTTON, self.on_navigate)
        nav_sizer.Add(nav_btn, 1, wx.ALL | wx.CENTER, 5)
        
        sizer.Add(nav_sizer, 0, wx.EXPAND)
        
        # Actions
        action_sizer = wx.GridSizer(2, 2, 10, 10)
        
        snap_btn = wx.Button(panel, label="Take Screenshot")
        snap_btn.Bind(wx.EVT_BUTTON, self.on_screenshot)
        action_sizer.Add(snap_btn, 1, wx.EXPAND)
        
        js_btn = wx.Button(panel, label="Execute JS")
        js_btn.Bind(wx.EVT_BUTTON, self.on_js)
        action_sizer.Add(js_btn, 1, wx.EXPAND)
        
        sizer.Add(action_sizer, 0, wx.EXPAND | wx.ALL, 20)
        
        # AI Section
        sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND | wx.ALL, 5)
        ai_label = wx.StaticText(panel, label="AI Pilot")
        ai_label.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(ai_label, 0, wx.LEFT | wx.TOP, 10)
        
        ai_sizer = wx.BoxSizer(wx.HORIZONTAL)
        aiclick_btn = wx.Button(panel, label="AI Click")
        aiclick_btn.Bind(wx.EVT_BUTTON, self.on_ai_click)
        ai_sizer.Add(aiclick_btn, 1, wx.ALL, 5)
        
        aiquery_btn = wx.Button(panel, label="AI Query")
        aiquery_btn.Bind(wx.EVT_BUTTON, self.on_ai_query)
        ai_sizer.Add(aiquery_btn, 1, wx.ALL, 5)
        
        sizer.Add(ai_sizer, 0, wx.EXPAND)
        
        # Log
        self.log_text = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        sizer.Add(self.log_text, 2, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        self.Show()

    def check_session(self):
        if SESSION_FILE.exists():
            self.status_label.SetLabel("Session: Running")
            self.start_btn.Disable()
            self.stop_btn.Enable()
        else:
            self.status_label.SetLabel("Session: Not started")
            self.start_btn.Enable()
            self.stop_btn.Disable()

    def on_start(self, event):
        # We can just call the CLI's logic here or run the CLI command
        self.log("Starting session...")
        import subprocess
        import sys
        subprocess.run([sys.executable, "-m", "browserpilot.cli", "start"])
        self.check_session()
        self.log("Session started.")

    def on_stop(self, event):
        self.log("Stopping session...")
        import subprocess
        import sys
        subprocess.run([sys.executable, "-m", "browserpilot.cli", "stop"])
        self.check_session()
        self.log("Session stopped.")

    def on_navigate(self, event):
        url = self.url_text.GetValue()
        self.log(f"Navigating to {url}...")
        import threading
        def _task():
            try:
                self.bp.open(url)
                wx.CallAfter(self.log, "Success.")
            except Exception as e:
                wx.CallAfter(self.log, f"Error: {e}")
        threading.Thread(target=_task, daemon=True).start()

    def on_screenshot(self, event):
        path = "gui_screenshot.png"
        self.log(f"Taking screenshot to {path}...")
        import threading
        def _task():
            try:
                self.bp.screenshot(path)
                wx.CallAfter(self.log, "Saved.")
            except Exception as e:
                wx.CallAfter(self.log, f"Error: {e}")
        threading.Thread(target=_task, daemon=True).start()

    def on_js(self, event):
        dlg = wx.TextEntryDialog(self, "Enter JS to execute:", "Execute JS")
        if dlg.ShowModal() == wx.ID_OK:
            script = dlg.GetValue()
            self.log(f"Executing JS: {script}")
            import threading
            def _task():
                try:
                    result = self.bp.js(script)
                    wx.CallAfter(self.log, f"Result: {result}")
                except Exception as e:
                    wx.CallAfter(self.log, f"Error: {e}")
            threading.Thread(target=_task, daemon=True).start()
        dlg.Destroy()

    def on_ai_click(self, event):
        dlg = wx.TextEntryDialog(self, "Describe what to click:", "AI Click")
        if dlg.ShowModal() == wx.ID_OK:
            desc = dlg.GetValue()
            self.log(f"AI clicking: {desc}")
            import threading
            def _task():
                try:
                    res = self.bp.ai_click(desc)
                    wx.CallAfter(self.log, f"Clicked element with selector: {res}")
                except Exception as e:
                    wx.CallAfter(self.log, f"Error: {e}")
            threading.Thread(target=_task, daemon=True).start()
        dlg.Destroy()

    def on_ai_query(self, event):
        dlg = wx.TextEntryDialog(self, "Ask a question about the page:", "AI Query")
        if dlg.ShowModal() == wx.ID_OK:
            q = dlg.GetValue()
            self.log(f"AI Query: {q}")
            import threading
            def _task():
                try:
                    res = self.bp.ai_query(q)
                    wx.CallAfter(self.log, f"AI Answer: {res}")
                except Exception as e:
                    wx.CallAfter(self.log, f"Error: {e}")
            threading.Thread(target=_task, daemon=True).start()
        dlg.Destroy()

    def on_about(self, event):
        about_text = (
            "BrowserPilot v0.2.0\n"
            "AI-powered browser automation engine.\n\n"
            "By Mohammed Maniruzzaman, PhD\n"
            "License: MIT\n\n"
            "Third-Party Components:\n"
            "- Playwright (Apache 2.0)\n"
            "- ollama (MIT)\n"
            "- httpx (BSD 3-Clause)\n"
            "- wxPython (LGPL)"
        )
        wx.MessageBox(about_text, "About BrowserPilot", wx.OK | wx.ICON_INFORMATION)

    def on_guide(self, event):
        import subprocess
        import sys
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

    def log(self, msg):
        self.log_text.AppendText(msg + "\n")

def main():
    app = wx.App()
    wx.InitAllImageHandlers()
    app.SetAppName("BrowserPilot")
    app.SetAppDisplayName("BrowserPilot")
    BrowserPilotFrame()
    app.MainLoop()

if __name__ == '__main__':
    main()

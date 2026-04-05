import wx
import sys
from pathlib import Path
from common.settings import load_settings

def is_dark_mode():
    """Detect whether the OS is currently in dark mode."""
    settings = load_settings()
    mode = settings.get("dark_mode", "auto")
    if mode == "dark":
        return True
    if mode == "light":
        return False
    # Auto-detect
    if sys.platform == "darwin":
        try:
            import subprocess
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True, text=True,
            )
            return "dark" in result.stdout.lower()
        except Exception:
            return False
    elif sys.platform == "win32":
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return value == 0
        except Exception:
            return False
    return False

def apply_dark_theme(widget, dark_bg, dark_fg, dark_panel, dark_input):
    """Recursively apply dark theme to a widget and its children."""
    if isinstance(widget, (wx.TextCtrl, wx.ComboBox, wx.stc.StyledTextCtrl)):
        widget.SetBackgroundColour(dark_input)
        widget.SetForegroundColour(dark_fg)
    elif isinstance(widget, wx.StaticText):
        widget.SetForegroundColour(dark_fg)
    elif isinstance(widget, wx.Panel):
        widget.SetBackgroundColour(dark_panel)
    elif isinstance(widget, wx.Frame):
        widget.SetBackgroundColour(dark_bg)
    
    if hasattr(widget, 'GetChildren'):
        for child in widget.GetChildren():
            apply_dark_theme(child, dark_bg, dark_fg, dark_panel, dark_input)

def get_resource_path(base_file, relative_path):
    """Resolve resource path for both development and standalone modes."""
    dev_path = Path(base_file).parent.parent.parent / relative_path
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

class BusyContext:
    """Context manager to show a busy cursor and disable widgets during a task."""
    def __init__(self, window, disable_widgets=None):
        self.window = window
        self.disable_widgets = disable_widgets or []
        self.busy = None

    def __enter__(self):
        self.busy = wx.BusyCursor()
        for w in self.disable_widgets:
            if hasattr(w, 'Disable'):
                w.Disable()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.busy:
            del self.busy
        for w in self.disable_widgets:
            if hasattr(w, 'Enable'):
                w.Enable()

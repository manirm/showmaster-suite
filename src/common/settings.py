import json
from pathlib import Path

SETTINGS_FILE = Path.home() / ".showmaster_settings.json"

DEFAULT_SETTINGS = {
    "ollama_url": "http://localhost:11434",
    "ollama_model": "llama3",
    "browser_headless": False,
    "video_format": "mov",
    "dark_mode": "auto",  # "auto", "dark", "light"
    "check_updates": True,
}


def load_settings():
    if SETTINGS_FILE.exists():
        try:
            return {**DEFAULT_SETTINGS, **json.loads(SETTINGS_FILE.read_text())}
        except Exception:
            return dict(DEFAULT_SETTINGS)
    return dict(DEFAULT_SETTINGS)


def save_settings(settings):
    SETTINGS_FILE.write_text(json.dumps(settings, indent=4))


def is_dark_mode():
    """Detect whether the OS is currently in dark mode."""
    settings = load_settings()
    mode = settings.get("dark_mode", "auto")
    if mode == "dark":
        return True
    if mode == "light":
        return False
    # Auto-detect
    import sys
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


# ── Auto-Update Check ─────────────────────────────────────────────────

GITHUB_REPO = "manirm/showmaster-suite"
CURRENT_VERSION = "0.5.0"


def check_for_updates():
    """Check GitHub for a newer release. Returns (bool, str) => (has_update, latest_tag)."""
    settings = load_settings()
    if not settings.get("check_updates", True):
        return False, CURRENT_VERSION
    try:
        import httpx
        resp = httpx.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
            timeout=5,
            follow_redirects=True,
        )
        if resp.status_code == 200:
            data = resp.json()
            latest = data.get("tag_name", "").lstrip("v")
            if latest and latest != CURRENT_VERSION:
                return True, latest
    except Exception:
        pass
    return False, CURRENT_VERSION

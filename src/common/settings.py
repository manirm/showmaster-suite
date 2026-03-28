import json
from pathlib import Path

SETTINGS_FILE = Path.home() / ".showmaster_settings.json"

DEFAULT_SETTINGS = {
    "ollama_url": "http://localhost:11434",
    "ollama_model": "llama3",
    "browser_headless": False,
    "video_format": "mov"
}

def load_settings():
    if SETTINGS_FILE.exists():
        try:
            return {**DEFAULT_SETTINGS, **json.loads(SETTINGS_FILE.read_text())}
        except:
            return DEFAULT_SETTINGS
    return DEFAULT_SETTINGS

def save_settings(settings):
    SETTINGS_FILE.write_text(json.dumps(settings, indent=4))


import os
import json
import time
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

try:
    with sync_playwright() as p:
        server = p.chromium.launch_server(headless=True)
        Path(".browserpilot_session.json").write_text(json.dumps({"ws_endpoint": server.ws_endpoint, "pid": os.getpid()}))
        while True:
            time.sleep(10)
except Exception as e:
    with open(".bp_error.log", "w") as f:
        f.write(str(e))

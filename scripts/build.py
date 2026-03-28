import subprocess
import sys
import os
from pathlib import Path

def build_app(module_name, app_name, icon_path):
    print(f"Building {app_name}...")
    
    cmd = [
        sys.executable, "-m", "nuitka",
        "--onefile",
        "--enable-plugin=wx-python",
        f"--output-filename={app_name}",
        f"--include-data-dir=src/{module_name.split('.')[0]}/assets={module_name.replace('.', '/')}/assets",
        f"src/{module_name.replace('.', '/')}/gui.py"
    ]
    
    if sys.platform == "darwin":
        cmd.extend([
            "--macos-create-app-bundle",
            f"--macos-app-icon={icon_path}",
            f"--macos-app-name={app_name}",
            "--macos-signed-app-binaries",
        ])
    elif sys.platform == "win32":
        cmd.extend([
            f"--windows-icon-from-ico={icon_path}",
            "--windows-uac-admin",
            "--windows-console-mode=disable"
        ])
    
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    # Create build directory
    os.makedirs("build", exist_ok=True)
    
    # Build Showmaster
    build_app(
        "showmaster", 
        "Showmaster", 
        "src/showmaster/assets/icon.png"
    )
    
    # Build BrowserPilot
    build_app(
        "browserpilot", 
        "BrowserPilot", 
        "src/browserpilot/assets/icon.png"
    )

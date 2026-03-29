import subprocess
import sys
import os
from pathlib import Path

def build_app(module_name, app_name, icon_path):
    print(f"Building {app_name}...")
    
    # Create a temporary main file with the exact App name so Nuitka names the .dmg and .dist correctly
    temp_main = f"{app_name}.py"
    with open(temp_main, "w") as out_f:
        with open(f"src/{module_name.replace('.', '/')}/gui.py", "r") as in_f:
            out_f.write(in_f.read())
            
    try:
        cmd = [
            sys.executable, "-m", "nuitka",
            "--enable-plugin=playwright",
            f"--output-filename={app_name}_bin",
            "--output-dir=dist",
            # Include assets
            f"--include-data-dir=src/{module_name.split('.')[0]}/assets={module_name.replace('.', '/')}/assets",
            # Include root documentation
            "--include-data-files=LICENSE=LICENSE",
            "--include-data-files=USER_GUIDE.md=USER_GUIDE.md",
            temp_main
        ]
        
        if sys.platform == "darwin":
            cmd.extend([
                "--standalone",
                "--macos-create-app-bundle",
                f"--macos-app-icon={icon_path}",
                f"--macos-app-name={app_name}",
            ])
        else:
            cmd.append("--onefile")
            
        if sys.platform == "win32":
            cmd.extend([
                f"--windows-icon-from-ico={icon_path}",
                "--windows-console-mode=disable"
            ])
        
        subprocess.run(cmd, check=True)
        
        # Build DMG manually on macOS to avoid Nuitka packaging the .dist folder
        if sys.platform == "darwin":
            print(f"Creating macOS disk image for {app_name}...")
            dmg_path = f"dist/{app_name}.dmg"
            if os.path.exists(dmg_path):
                os.remove(dmg_path)
            
            # Use native hdiutil to ensure headless and reliable DMG generation
            subprocess.run([
                "hdiutil", "create",
                "-volname", app_name,
                "-srcfolder", f"dist/{app_name}.app",
                "-ov", "-format", "UDZO",
                dmg_path
            ], check=True)
            
    finally:
        # Cleanup the temporary entry script
        if os.path.exists(temp_main):
            os.remove(temp_main)

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

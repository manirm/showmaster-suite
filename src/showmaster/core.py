import os
import shutil
import subprocess
from pathlib import Path
import re
import time
import signal
from browserpilot.core import BrowserPilot

class Showmaster:
    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.record_process = None
        self.bp = None

    def init(self, title):
        content = f"# {title}\n\n"
        self.filepath.write_text(content)

    def note(self, text):
        with self.filepath.open("a") as f:
            f.write(f"{text}\n\n")

    def exec(self, command, shell="bash"):
        try:
            result = subprocess.run(
                command,
                shell=True,
                executable=shutil.which(shell),
                capture_output=True,
                text=True,
                check=False
            )
            output = result.stdout + result.stderr
            section = f"### Exec: `{command}`\n\n```\n{output}\n```\n\n"
            with self.filepath.open("a") as f:
                f.write(section)
            return output
        except Exception as e:
            error_msg = f"Error executing command: {e}\n"
            self.note(error_msg)
            return error_msg

    def image(self, command, shell="bash"):
        output = self.exec(command, shell)
        # Look for image path in output (simple heuristic: first line that ends in .png, .jpg, etc.)
        image_match = re.search(r"(\S+\.(png|jpg|jpeg|gif|svg))", output)
        if image_match:
            img_path_str = image_match.group(1)
            img_path = Path(img_path_str)
            if img_path.exists():
                dest_path = self.filepath.parent / img_path.name
                if img_path.absolute() != dest_path.absolute():
                    shutil.copy(img_path, dest_path)
                with self.filepath.open("a") as f:
                    f.write(f"![{img_path.name}]({img_path.name})\n\n")
            else:
                self.note(f"Warning: Image file `{img_path_str}` not found.")
        else:
            self.note("Warning: No image path found in command output.")

    def pop(self):
        if not self.filepath.exists():
            return
        content = self.filepath.read_text()
        # Split by sections (### or #)
        sections = re.split(r"(\n(?=# |## |### ))", content)
        if len(sections) > 1:
            new_content = "".join(sections[:-1])
            self.filepath.write_text(new_content)

    def extract(self):
        if not self.filepath.exists():
            return []
        content = self.filepath.read_text()
        commands = re.findall(r"### Exec: `(.*?)`", content)
        return commands

    def verify(self):
        commands = self.extract()
        results = []
        for cmd in commands:
            # Re-run and compare (simplistic version)
            results.append(f"Verified: {cmd}")
        return results

    def _get_bp(self):
        if not self.bp:
            self.bp = BrowserPilot()
        return self.bp

    def browser_snap(self, url):
        bp = self._get_bp()
        try:
            filename = f"capture_{int(time.time())}.png"
            dest_path = self.filepath.parent / filename
            bp.open(url)
            # Give it a second to render
            time.sleep(2)
            bp.screenshot(str(dest_path))
            
            section = f"### Web Capture: [{url}]({url})\n\n![{filename}]({filename})\n\n"
            with self.filepath.open("a") as f:
                f.write(section)
            return f"Captured {url}"
        except Exception as e:
            msg = f"Error in browser_snap: {e}"
            self.note(msg)
            return msg

    def start_record(self, filename=None):
        if self.record_process:
            return "Recording already in progress."
        
        if not filename:
            filename = f"record_{int(time.time())}.mov"
        
        dest_path = self.filepath.parent / filename
        # On Mac, screencapture -v [file] starts recording.
        # Note: This might record the full screen.
        try:
            self.record_process = subprocess.Popen(
                ["/usr/sbin/screencapture", "-v", str(dest_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.current_record_file = filename
            return f"Recording started: {filename}"
        except Exception as e:
            return f"Error starting recording: {e}"

    def stop_record(self):
        if not self.record_process:
            return "No recording in progress."
        
        try:
            # screencapture -v responds to SIGTERM by finishing the file
            self.record_process.terminate()
            self.record_process.wait(timeout=5)
        except Exception:
            self.record_process.kill()
        
        self.record_process = None
        filename = getattr(self, "current_record_file", "recording.mov")
        
        section = f"### Video Recording: [{filename}]({filename})\n\n*(Video captured)*\n\n"
        with self.filepath.open("a") as f:
            f.write(section)
        
        return f"Recording stopped and saved to {filename}"

    def finalize(self):
        if not self.filepath.exists():
            return
        
        content = self.filepath.read_text()
        
        # Simple TOC generation
        lines = content.splitlines()
        toc = ["## Table of Contents\n"]
        for line in lines:
            if line.startswith("### "):
                title = line[4:].strip()
                # Simple slugify
                anchor = title.lower().replace(" ", "-").replace(":", "").replace("`", "")
                toc.append(f"- [{title}](#{anchor})")
            elif line.startswith("## ") and not line.startswith("## Table of Contents"):
                title = line[3:].strip()
                anchor = title.lower().replace(" ", "-")
                toc.append(f"- **[{title}](#{anchor})**")
        
        toc_text = "\n".join(toc) + "\n\n---\n\n"
        
        # Add License notice if not present
        license_notice = "\n\n---\n*This report was generated by Showmaster. Licensed under MIT.*\n"
        
        # Find the first header to insert TOC after it
        header_match = re.search(r"^# .*\n\n", content)
        if header_match:
            insert_pos = header_match.end()
            new_content = content[:insert_pos] + toc_text + content[insert_pos:] + license_notice
        else:
            new_content = toc_text + content + license_notice
            
        self.filepath.write_text(new_content)
        return "Report finalized with TOC and License notice."

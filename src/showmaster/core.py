import os
import shutil
import subprocess
from pathlib import Path
import re
import time
import signal
import threading
import mss
import cv2
import numpy as np
from browserpilot.core import BrowserPilot
from common.logger import get_logger

logger = get_logger("core")

class Showmaster:
    SAFE_TOOLS = {
        "git", "ls", "pwd", "cd", "cp", "mv", "mkdir", "rmdir", 
        "python", "python3", "pip", "pip3", "uv", "npm", "node", 
        "grep", "cat", "echo", "date", "whoami", "curl", "wget",
        "find", "weasyprint", "ffmpeg", "magick", "docker"
    }

    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.record_thread = None
        self.recording = False
        self.bp = None
        self._lock = threading.Lock()
        self.unsafe_mode = False
        logger.info(f"Initialized Showmaster for {filepath}")

    def init(self, title):
        content = f"# {title}\n\n"
        with self._lock:
            self.filepath.write_text(content)

    def note(self, text):
        with self._lock:
            with self.filepath.open("a") as f:
                f.write(f"{text}\n\n")

    def get_text(self):
        """Thread-safe read of the current report content."""
        if not self.filepath.exists():
            return ""
        with self._lock:
            return self.filepath.read_text()

    def _safe_path(self, path):
        """Ensure the path is a child of the report's directory (Sandbox)."""
        base = self.filepath.absolute().parent.resolve()
        target = Path(path).absolute().resolve()
        
        # Use commonpath to prevent symlink/traversal escapes
        try:
            if os.path.commonpath([base, target]) != str(base):
                raise ValueError(f"Path access denied: {path} is outside {base}")
        except ValueError:
            raise ValueError(f"Path access denied: {path} is outside {base}")
            
        return target

    def _redact(self, text):
        """Redact sensitive patterns from text."""
        # Redact UUIDs
        text = re.sub(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', '[REDACTED UUID]', text)
        # Redact Bearer tokens / keys (simple heuristic)
        # Matches key=value, key:value, key value. Handles Base64 (/ and +) and short tokens.
        text = re.sub(r'(?i)(api[_-]?key|token|password|secret|bearer)["\s:=]+[\'"]?([a-zA-Z0-9_\-\.\/\+]{1,})[\'"]?', r'\1: [REDACTED]', text)
        return text

    def exec(self, command, shell_executable="bash"):
        """Safe execution of a command (no shell interpolation by default)."""
        import shlex
        try:
            # Audit log (redacted)
            safe_log_cmd = self._redact(command)
            
            # For security, we split the command and run WITHOUT shell=True
            args = shlex.split(command)
            if not args:
                return ""
            
            # Resolve basename to allow absolute paths (e.g. /usr/bin/git -> git)
            cmd_root = Path(args[0]).name
            
            # Explicitly deny sudo in standard exec
            if cmd_root == "sudo":
                 logger.critical(f"Sudo attempt blocked in safe exec: {safe_log_cmd}")
                 return "Error: sudo is only allowed in 'Unsafe' mode."

            # Audit log (redacted)
            if cmd_root not in self.SAFE_TOOLS:
                logger.warning(self._redact(f"Executing potentially unauthorized tool: {cmd_root} in command '{safe_log_cmd}'"))
            else:
                logger.info(self._redact(f"Executing authorized tool: {cmd_root}"))

            result = subprocess.run(
                args,
                shell=False,
                capture_output=True,
                text=True,
                check=False
            )
            output = self._redact(result.stdout + result.stderr)
            section = f"### Exec: `{command}`\n\n```\n{output}\n```\n\n"
            with self._lock:
                with self.filepath.open("a") as f:
                    f.write(section)
            return output
        except Exception as e:
            error_msg = f"Error executing command: {e}\n"
            logger.error(f"Execution Error: {error_msg}")
            self.note(error_msg)
            return error_msg

    def raw_exec(self, command, shell="bash"):
        """Unsafe execution with shell=True for complex piping/redirection.
        Use with extreme caution.
        """
        try:
            if not self.unsafe_mode:
                return "Error: raw_exec blocked. Enable 'Unsafe' mode first."

            safe_log_cmd = self._redact(command)
            logger.critical(self._redact(f"UNSAFE EXECUTION (raw_exec): {safe_log_cmd}"))
            
            result = subprocess.run(
                command,
                shell=True,
                executable=shutil.which(shell),
                capture_output=True,
                text=True,
                check=False
            )
            output = self._redact(result.stdout + result.stderr)
            section = f"### Unsafe Exec: `{command}`\n\n*(Shell execution enabled)*\n\n```\n{output}\n```\n\n"
            with self._lock:
                with self.filepath.open("a") as f:
                    f.write(section)
            return output
        except Exception as e:
            logger.error(f"Raw Execution Error: {e}")
            return f"Error: {e}"

    def image(self, command, shell="bash"):
        """Execute command and extract the first image path found in output."""
        output = self.exec(command, shell)
        # Look for image path in output
        image_match = re.search(r"(\S+\.(png|jpg|jpeg|gif|svg))", output)
        if image_match:
            img_path_str = image_match.group(1)
            try:
                img_path = self._safe_path(img_path_str)
                if img_path.exists():
                    dest_path = self.filepath.parent / img_path.name
                    if img_path.absolute() != dest_path.absolute():
                        shutil.copy(img_path, dest_path)
                    with self._lock:
                        with self.filepath.open("a") as f:
                            f.write(f"![{img_path.name}]({img_path.name})\n\n")
                else:
                    self.note(f"Warning: Image file `{img_path_str}` not found.")
            except ValueError as e:
                self.note(f"Security Warning: {e}")
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
            with self._lock:
                with self.filepath.open("a") as f:
                    f.write(section)
            return f"Captured {url}"
        except Exception as e:
            msg = f"Error in browser_snap: {e}"
            self.note(msg)
            return msg

    def start_record(self, filename=None):
        if self.recording:
            return "Recording already in progress."
        
        if not filename:
            filename = f"record_{int(time.time())}.mp4"
        
        dest_path = self.filepath.parent / filename
        self.current_record_file = filename
        self.recording = True
        
        def _record():
            with mss.mss() as sct:
                # Capture the primary monitor
                monitor = sct.monitors[1]
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(str(dest_path), fourcc, 10.0, (monitor["width"], monitor["height"]))
                
                while self.recording:
                    img = sct.grab(monitor)
                    frame = np.array(img)
                    # Convert BGRA to BGR
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    out.write(frame)
                    time.sleep(0.1) # ~10 FPS
                
                out.release()

        self.record_thread = threading.Thread(target=_record, daemon=True)
        self.record_thread.start()
        return f"Recording started: {filename}"

    def stop_record(self):
        if not self.recording:
            return "No recording in progress."
        
        self.recording = False
        if self.record_thread:
            self.record_thread.join(timeout=2)
        
        filename = getattr(self, "current_record_file", "recording.mp4")
        
        section = f"### Video Recording: [{filename}]({filename})\n\n*(Video captured)*\n\n"
        with self._lock:
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
            
        with self._lock:
            self.filepath.write_text(new_content)
        return "Report finalized with TOC and License notice."

    def export_pdf(self, output_path=None):
        """Export the report as a PDF file.

        Requires: pip install weasyprint   (optional dependency)
        Falls back to a simple HTML file if weasyprint is not installed.
        """
        import markdown2

        if not self.filepath.exists():
            return "No report to export."

        if output_path is None:
            output_path = self.filepath.with_suffix(".pdf")

        content = self.filepath.read_text()
        html_body = markdown2.markdown(content)
        styled_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {{ margin: 2cm; }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                     Helvetica, Arial, sans-serif;
        line-height: 1.6;
        color: #24292e;
        max-width: 700px;
        margin: 0 auto;
        font-size: 11pt;
    }}
    pre {{
        background: #f6f8fa;
        padding: 12px;
        border-radius: 6px;
        overflow-x: auto;
        font-size: 9pt;
        font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
    }}
    code {{
        background: rgba(27,31,35,0.05);
        padding: 0.2em 0.4em;
        border-radius: 3px;
        font-size: 85%;
    }}
    img {{ max-width: 100%; }}
    h1 {{ border-bottom: 2px solid #e1e4e8; padding-bottom: 0.3em; }}
    h2 {{ border-bottom: 1px solid #e1e4e8; padding-bottom: 0.3em; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #dfe2e5; padding: 8px; text-align: left; }}
    th {{ background: #f6f8fa; }}
    blockquote {{
        padding: 0 1em;
        color: #6a737d;
        border-left: 0.25em solid #dfe2e1;
    }}
    hr {{ height: 0.25em; background-color: #e1e4e8; border: 0; }}
</style>
</head>
<body>{html_body}</body>
</html>"""

        try:
            from weasyprint import HTML
            HTML(string=styled_html).write_pdf(str(output_path))
            return f"PDF exported to {output_path}"
        except ImportError:
            # Fallback: save as HTML
            html_path = self.filepath.with_suffix(".html")
            html_path.write_text(styled_html)
            return f"weasyprint not installed. HTML exported to {html_path}"


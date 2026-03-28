import click
import os
import sys
import subprocess
import json
import time
import signal
from pathlib import Path
from browserpilot.core import BrowserPilot

@click.group(name="browserpilot")
@click.pass_context
def main_cli(ctx):
    ctx.obj = BrowserPilot()

@main_cli.command()
@click.option('--headful', is_flag=True, help='Run in headful mode (visual).')
@click.pass_obj
def start(bp, headful):
    """Start a persistent browser session."""
    # Launch Chromium with remote debugging port
    # We use a simple subprocess to keep it alive
    headless_arg = "--headless" if not headful else ""
    port = 9222
    
    # Try using playwright's bundled chromium
    # Find the path to playwright chromium
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            executable_path = p.chromium.executable_path
    except:
        executable_path = "chromium"

    cmd = [executable_path, f"--remote-debugging-port={port}", "--remote-allow-origins=*"]
    if not headful:
        cmd.append("--headless=new")
    
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    
    # Save session info
    session_file = Path(".browserpilot_session.json")
    session_file.write_text(json.dumps({"cdp_url": f"http://localhost:{port}", "port": port}))
    
    click.echo(f"Browser session started on port {port}")
    click.echo("Allowing a few seconds for initialization...")
    time.sleep(3)

@main_cli.command()
@click.argument('url')
@click.pass_obj
def navigate(bp, url):
    """Open a URL."""
    bp.open(url)

@main_cli.command()
@click.argument('selector')
@click.pass_obj
def click_el(bp, selector):
    """Click an element."""
    bp.click(selector)

@main_cli.command()
@click.argument('script')
@click.pass_obj
def execute_js(bp, script):
    """Execute JS."""
    bp.js(script)

@main_cli.command()
@click.argument('path')
@click.pass_obj
def snap(bp, path):
    """Take screenshot."""
    bp.screenshot(path)

@main_cli.command()
@click.argument('description')
@click.pass_obj
def ai_click(bp, description):
    """AI-powered click using natural language."""
    bp.ai_click(description)

@main_cli.command()
@click.argument('question')
@click.pass_obj
def ai_query(bp, question):
    """AI-powered question about the current page."""
    answer = bp.ai_query(question)
    click.echo(f"\nAI Answer:\n{answer}")

@main_cli.command()
@click.pass_obj
def stop(bp):
    """Stop session."""
    # Find process on port 9222 and kill it (simplistic)
    # Or just remove the session file
    session_file = Path(".browserpilot_session.json")
    if session_file.exists():
        session_file.unlink()
    click.echo("Browser session script stopped (please close browser manually if still open).")

if __name__ == '__main__':
    main_cli()

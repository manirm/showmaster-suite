# Showmaster Suite — User Guide

> **Version 0.4.0** | By Mohammed Maniruzzaman, PhD | MIT License

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Showmaster Tutorials](#showmaster-tutorials)
4. [BrowserPilot Tutorials](#browserpilot-tutorials)
5. [Report Templates](#report-templates)
6. [Action Recording & Playback](#action-recording--playback)
7. [AI Conversation Memory](#ai-conversation-memory)
8. [Dark Mode](#dark-mode)
9. [PDF Export](#pdf-export)
10. [GUI Reference](#gui-reference)
11. [CLI Reference](#cli-reference)
12. [Keyboard Shortcuts](#keyboard-shortcuts)
13. [Desktop Launchers](#desktop-launchers)
14. [Configuration](#configuration)
15. [Code Signing & Distribution](#code-signing--distribution)
16. [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# Install from source
git clone https://github.com/manirm/showmaster-suite.git
cd showmaster-suite
uv sync
uv run playwright install chromium

# Create your first report
uv run showmaster init "My First Demo"
uv run showmaster note "This is a demo report."
uv run showmaster exec "echo Hello, world!"
uv run showmaster finalize

# Launch the GUI
uv run showmaster-gui
```

---

## Installation

### Prerequisites

- **Python 3.12+**
- **uv** (recommended) or pip
- **Playwright** browsers (for BrowserPilot)
- **Ollama** (optional, for AI features)

### From Source (Development)

```bash
git clone https://github.com/manirm/showmaster-suite.git
cd showmaster-suite
uv sync                          # Install all dependencies
uv sync --extra dev              # Include test dependencies
uv sync --extra pdf              # Include PDF export (weasyprint)
uv run playwright install chromium
```

### From PyPI (when published)

```bash
pip install showmaster-suite
playwright install chromium
```

---

## Showmaster Tutorials

### Tutorial 1: Create a Simple Documentation Report

```bash
# Initialize a new report
showmaster init "System Health Check"

# Add descriptive notes
showmaster note "Checking system status on $(date)"

# Run commands and capture their output
showmaster exec "uname -a"
showmaster exec "df -h"
showmaster exec "uptime"

# Finalize with table of contents
showmaster finalize
```

Result: `demo.md` now contains a professional report with all outputs, a TOC, and a license footer.

### Tutorial 2: Work with a Custom File

```bash
showmaster -f deployment_notes.md init "Deployment Log — Production"
showmaster -f deployment_notes.md exec "docker ps"
showmaster -f deployment_notes.md note "All services running."
showmaster -f deployment_notes.md finalize
```

### Tutorial 3: Capture Command Output Images

```bash
# Run a command that produces an image file
showmaster exec "python plot_chart.py"  # prints path like "chart.png"

# Or use the image command to auto-embed it
showmaster image "python plot_chart.py"
```

### Tutorial 4: Record Screen Video

```bash
# Record for 15 seconds
showmaster record --duration 15
```

Or in the GUI: click **Start** in the Video Recording section, perform your demo, then click **Stop**.

### Tutorial 5: Undo and Edit

```bash
# Remove the last section added
showmaster pop

# You can pop multiple times
showmaster pop
showmaster pop
```

### Tutorial 6: Web Page Capture

```bash
# Capture a screenshot of a website
showmaster -f report.md browser-snap https://github.com
```

### Tutorial 7: Extract Commands from a Report

```bash
# List all commands that were run in a report
showmaster extract
```

This is useful for reproducing a workflow documented in a report.

---

## BrowserPilot Tutorials

### Tutorial 8: Navigate and Screenshot

```bash
# Navigate to a page
browserpilot navigate https://github.com

# Take a screenshot
browserpilot snap github_home.png

# View in headful mode (see the browser)
browserpilot --headful navigate https://github.com
```

### Tutorial 9: Execute JavaScript

```bash
# Get the page title
browserpilot execute-js "document.title"

# Count all links
browserpilot execute-js "document.querySelectorAll('a').length"

# Extract all heading text
browserpilot execute-js "Array.from(document.querySelectorAll('h1,h2,h3')).map(e => e.textContent)"
```

### Tutorial 10: Click Elements

```bash
# Click by CSS selector
browserpilot click-el "a.nav-link"

# Click the first button
browserpilot click-el "button"
```

### Tutorial 11: AI-Powered Interaction

Requires [Ollama](https://ollama.com/) running locally.

```bash
# Start Ollama
ollama serve

# Navigate to a page
browserpilot navigate https://news.ycombinator.com

# AI Click — describe what you want to click
browserpilot ai-click "the login link"

# AI Query — ask questions about page content
browserpilot ai-query "What are the top 3 stories?"

# Follow-up query (uses conversation memory!)
browserpilot ai-query "Summarize the first one in detail"

# Clear conversation history
browserpilot ai-clear
```

### Tutorial 12: Reset Browser State

```bash
# Clear all cookies, history, and cached data
browserpilot reset
```

---

## Report Templates

Showmaster includes 4 built-in report templates:

| Template | Description |
|----------|-------------|
| `bug_report` | Structured bug report with reproduction steps |
| `feature_demo` | Feature showcase with before/after sections |
| `api_walkthrough` | API documentation with endpoint examples |
| `project_setup` | Project installation and configuration guide |

### Using Templates (CLI)

```bash
# List all templates
showmaster list-templates

# Create a bug report
showmaster init-template bug_report "Login Page Crash" --author "Dr. Manir"

# Create an API walkthrough
showmaster init-template api_walkthrough "Payment API v2" -f api_docs.md --author "Team"
```

### Using Templates (GUI)

1. Open Showmaster GUI
2. Go to **Tools → New from Template**
3. Select a template (e.g., Bug Report)
4. Enter the title
5. The report is created with all sections pre-populated

---

## Action Recording & Playback

BrowserPilot can record sequences of browser actions as JSON scripts and replay them later. This is useful for regression testing, demos, and automated workflows.

### Create a Script Interactively

```bash
browserpilot create-script my_test.json
```

Then type actions one per line:
```
navigate https://example.com
wait 2
screenshot before.png
click a
wait 1
screenshot after.png
```

Press `Ctrl+D` (or `Ctrl+Z` on Windows) to finish.

### Create a Script Programmatically

```python
from browserpilot.recorder import create_script

create_script([
    {"type": "navigate", "url": "https://example.com"},
    {"type": "wait", "seconds": 2},
    {"type": "screenshot", "path": "home.png"},
    {"type": "click", "selector": "a"},
    {"type": "wait", "seconds": 1},
    {"type": "screenshot", "path": "linked_page.png"},
], "my_workflow.json")
```

### Replay a Script

```bash
# Normal speed
browserpilot replay my_test.json

# 2x speed
browserpilot replay my_test.json --speed 2.0

# In headful mode (watch it happen)
browserpilot --headful replay my_test.json
```

### Supported Action Types

| Action | Fields | Example |
|--------|--------|---------|
| `navigate` | `url` | `{"type": "navigate", "url": "https://example.com"}` |
| `click` | `selector` | `{"type": "click", "selector": "#submit"}` |
| `type` | `selector`, `text` | `{"type": "type", "selector": "#email", "text": "me@example.com"}` |
| `screenshot` | `path` | `{"type": "screenshot", "path": "result.png"}` |
| `js` | `script` | `{"type": "js", "script": "document.title"}` |
| `wait` | `seconds` | `{"type": "wait", "seconds": 3}` |
| `ai_click` | `description` | `{"type": "ai_click", "description": "the login button"}` |
| `ai_query` | `question` | `{"type": "ai_query", "question": "What is the page about?"}` |

---

## AI Conversation Memory

BrowserPilot maintains a conversation history for AI queries. This enables multi-turn conversations where follow-up questions reference previous answers.

```bash
browserpilot navigate https://en.wikipedia.org/wiki/Python_(programming_language)

# First question
browserpilot ai-query "When was Python created?"

# Follow-up (AI remembers the previous answer)
browserpilot ai-query "Who created it?"

# Clear memory to start fresh
browserpilot ai-clear
```

Memory is stored at `~/.browserpilot_profile/.conversation.json` and keeps the last 20 turns.

---

## Dark Mode

Both GUIs automatically detect your OS theme and switch between light and dark mode.

### Automatic Detection
- **macOS**: Reads `AppleInterfaceStyle` from system defaults
- **Windows**: Reads `AppsUseLightTheme` from the registry
- **Linux**: Defaults to light mode

### Manual Override

Edit `~/.showmaster_settings.json`:

```json
{
    "dark_mode": "dark"
}
```

Options: `"auto"` (default), `"dark"`, `"light"`

The Showmaster markdown preview also renders in dark mode with GitHub-style dark CSS.

---

## PDF Export

Export your finalized reports as PDFs or HTML.

### CLI

```bash
# Export to PDF (requires weasyprint)
showmaster export-pdf

# Export to a specific path
showmaster export-pdf -o report.pdf
```

### GUI

Go to **File → Export as PDF** (or press `Ctrl+Shift+P`).

### Installing weasyprint (optional)

```bash
uv sync --extra pdf
```

If weasyprint is not installed, the export falls back to a styled HTML file.

---

## GUI Reference

### Showmaster GUI

Launch: `showmaster-gui` or double-click `launchers/Showmaster.command`

| Area | Description |
|------|-------------|
| **Add Note** | Free-text notes appended to the report |
| **Execute Command** | Run shell commands, output captured |
| **Run Image Command** | Run commands that produce images |
| **Undo Last / Finalize** | Remove last section / add TOC |
| **Web Capture** | Screenshot any URL via BrowserPilot |
| **Video Recording** | Start/stop screen recording |
| **Preview Pane** | Live HTML preview of the report |

### BrowserPilot GUI

Launch: `browserpilot-gui` or double-click `launchers/BrowserPilot.command`

| Area | Description |
|------|-------------|
| **Navigation Bar** | URL input + Navigate button |
| **Take Screenshot** | Capture current page |
| **Execute JS** | Run JavaScript on the page |
| **Reset Profile** | Clear all browser state |
| **Clear AI History** | Reset conversation memory |
| **AI Click** | Describe an element to click |
| **AI Query** | Ask questions about page content |
| **Log Panel** | Shows all actions and results |

---

## CLI Reference

### Showmaster

```
showmaster [OPTIONS] COMMAND [ARGS]

Options:
  -f, --file PATH    Target markdown file (default: demo.md)

Commands:
  init TITLE           Initialize a new report
  note TEXT            Add a note
  exec COMMAND         Execute a command and capture output
  image COMMAND        Execute and embed output image
  pop                  Remove the last section
  extract              List all commands in the report
  finalize             Add TOC and license footer
  export-pdf           Export as PDF/HTML
  record               Record screen video
  browser-snap URL     Capture a web page screenshot
  list-templates       List available report templates
  init-template TPL TITLE  Create report from template
```

### BrowserPilot

```
browserpilot [OPTIONS] COMMAND [ARGS]

Options:
  --headful    Show the browser window

Commands:
  navigate URL         Open a URL
  click-el SELECTOR    Click an element
  execute-js SCRIPT    Execute JavaScript
  snap PATH            Take a screenshot
  ai-click DESC        AI-powered click
  ai-query QUESTION    Ask AI about the page
  ai-clear             Clear conversation history
  reset                Clear browser profile
  replay FILE          Replay an action script
  create-script FILE   Create an action script interactively
```

---

## Keyboard Shortcuts

### Showmaster GUI

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New report |
| `Ctrl+O` | Open report |
| `Ctrl+S` | Save |
| `Ctrl+Z` | Undo (pop last section) |
| `Ctrl+Shift+F` | Finalize report |
| `Ctrl+Shift+P` | Export as PDF |
| `Ctrl+R` | Start video recording |
| `Ctrl+Shift+R` | Stop video recording |
| `Ctrl+Q` | Quit |
| `F1` | Open User Guide |

### BrowserPilot GUI

| Shortcut | Action |
|----------|--------|
| `Ctrl+L` | Focus URL / Navigate |
| `Ctrl+Shift+S` | Take screenshot |
| `Ctrl+J` | Execute JavaScript |
| `Ctrl+Shift+C` | AI Click |
| `Ctrl+Shift+Q` | AI Query |
| `Ctrl+Q` | Quit |
| `F1` | Open User Guide |

---

## Desktop Launchers

### macOS
Double-click these files in Finder (no terminal needed):
- `launchers/Showmaster.command`
- `launchers/BrowserPilot.command`

### Windows
Double-click these batch files:
- `launchers/Showmaster.bat`
- `launchers/BrowserPilot.bat`

### Linux
```bash
./launchers/Showmaster.command
```

---

## Configuration

Settings are stored at `~/.showmaster_settings.json`:

```json
{
    "ollama_url": "http://localhost:11434",
    "ollama_model": "llama3",
    "browser_headless": false,
    "video_format": "mov",
    "dark_mode": "auto",
    "check_updates": true
}
```

| Setting | Default | Description |
|---------|---------|-------------|
| `ollama_url` | `http://localhost:11434` | Ollama API endpoint |
| `ollama_model` | `llama3` | AI model for queries |
| `browser_headless` | `false` | Default browser mode |
| `video_format` | `mov` | Screen recording format |
| `dark_mode` | `auto` | Theme: `auto`, `dark`, `light` |
| `check_updates` | `true` | Check GitHub for updates on launch |

---

## Code Signing & Distribution

### For End Users

Download signed binaries from [GitHub Releases](https://github.com/manirm/showmaster-suite/releases).

### For Developers: Setting Up Code Signing

#### macOS (Apple Developer Program — $99/year)

1. Enroll at [developer.apple.com/programs](https://developer.apple.com/programs/)
2. Create a **Developer ID Application** certificate in Xcode
3. Export as `.p12` and encode: `base64 -i cert.p12 | pbcopy`
4. Add these GitHub Secrets:
   - `APPLE_CERTIFICATE_BASE64` — The base64 `.p12`
   - `APPLE_CERTIFICATE_PASSWORD` — The `.p12` password
   - `APPLE_TEAM_ID` — Your team ID
   - `APPLE_ID` — Your Apple ID email
   - `APPLE_APP_SPECIFIC_PASSWORD` — Generate at [appleid.apple.com](https://appleid.apple.com)

#### Windows (Code Signing Certificate)

Options:
- **Free for open-source**: [SignPath Foundation](https://signpath.org/)
- **Paid**: DigiCert ($289/yr), Sectigo ($200/yr), SSL.com ($200/yr)

1. Obtain an OV code signing certificate (.pfx)
2. Encode: `base64 cert.pfx > cert_b64.txt`
3. Add GitHub Secrets:
   - `WINDOWS_CERTIFICATE_BASE64`
   - `WINDOWS_CERTIFICATE_PASSWORD`

#### Linux (GPG — Free)

1. Create GPG key: `gpg --full-generate-key`
2. Export: `gpg --armor --export-secret-keys YOUR_EMAIL | base64`
3. Add GitHub Secret: `GPG_PRIVATE_KEY`

The CI pipeline auto-detects available secrets and only signs when certificates are present.

---

## Troubleshooting

### "Browser not found"
```bash
uv run playwright install chromium
```

### "Ollama connection refused"
```bash
ollama serve    # Start the Ollama server
ollama pull llama3  # Download the model
```

### "weasyprint not installed"
```bash
uv sync --extra pdf
```
On macOS you may also need: `brew install pango`

### GUI won't start
```bash
# Check wxPython installation
uv run python -c "import wx; print(wx.version())"
```

### "Unidentified developer" (macOS)
If downloading an unsigned binary: right-click → Open → Open.
To permanently fix: set up code signing (see above).

### Reset everything
```bash
browserpilot reset                    # Clear browser state
rm ~/.showmaster_settings.json        # Reset settings
rm ~/.browserpilot_profile/.conversation.json  # Clear AI memory
```

---

*This guide covers Showmaster Suite v0.4.0. For updates, visit [github.com/manirm/showmaster-suite](https://github.com/manirm/showmaster-suite).*

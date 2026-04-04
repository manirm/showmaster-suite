<div align="center">

# Showmaster Suite

**Professional documentation tool + AI-powered browser automation**

[![Build](https://github.com/manirm/showmaster-suite/actions/workflows/release.yml/badge.svg)](https://github.com/manirm/showmaster-suite/actions/workflows/release.yml)
[![Tests](https://github.com/manirm/showmaster-suite/actions/workflows/test.yml/badge.svg)](https://github.com/manirm/showmaster-suite/actions/workflows/test.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-0.4.0-orange.svg)](https://github.com/manirm/showmaster-suite/releases)

*Create rich documentation, automate the browser, and capture everything — all from one toolkit.*

</div>

---

## ✨ Features

### 🖊️ Showmaster — Documentation & Demo Tool

- **Split-pane editor** — Markdown editor with syntax highlighting + live HTML preview
- **Command capture** — Run commands and auto-embed their output into reports
- **Screen recording** — Record screen video directly into your documentation
- **Web capture** — Screenshot any URL and embed it inline
- **PDF export** — Export polished reports as PDF or styled HTML
- **4 built-in templates** — Bug report, feature demo, API walkthrough, project setup
- **Dark mode** — Auto-detects OS theme (macOS, Windows)
- **Drag & drop** — Drop images directly into the editor to embed
- **Auto-save** — Never lose work with 30-second auto-save

### 🤖 BrowserPilot — AI Browser Automation

- **Persistent sessions** — Browser state (cookies, tabs, history) persists between commands
- **AI-powered interaction** — Click elements by natural language description
- **Conversational AI** — Ask questions about page content with multi-turn memory
- **Action recording** — Record browser actions as JSON scripts, replay at any speed
- **Form automation** — Fill fields, select dropdowns, type with keystroke simulation
- **PDF capture** — Save any webpage as PDF with native Playwright rendering
- **Wait strategies** — Wait for selectors, network idle, URL patterns
- **Cookie management** — Export and import cookies for session sharing

---

## 🚀 Quick Start

```bash
# Clone and install
git clone https://github.com/manirm/showmaster-suite.git
cd showmaster-suite
uv sync
uv run playwright install chromium

# Create a report
uv run showmaster init "My Demo"
uv run showmaster exec "echo Hello!"
uv run showmaster finalize

# Launch the GUI
uv run showmaster-gui
```

---

## 📦 Installation

### From Source (Development)

```bash
git clone https://github.com/manirm/showmaster-suite.git
cd showmaster-suite
uv sync                     # Core dependencies
uv sync --extra dev         # + pytest for testing
uv sync --extra pdf         # + weasyprint for PDF export
uv run playwright install chromium
```

### Desktop Launchers (No Terminal)

Double-click these files to launch the GUI:

| Platform | Showmaster | BrowserPilot |
|----------|-----------|--------------|
| macOS | `launchers/Showmaster.command` | `launchers/BrowserPilot.command` |
| Windows | `launchers/Showmaster.bat` | `launchers/BrowserPilot.bat` |

---

## 🎯 CLI Usage

### Showmaster

```bash
showmaster init "Project Report"           # Start a new report
showmaster note "Setup complete"           # Add a note
showmaster exec "pytest -v"                # Run & capture command output
showmaster image "python chart.py"         # Run & embed output image
showmaster browser-snap https://github.com # Screenshot a webpage
showmaster finalize                        # Add TOC & footer
showmaster export-pdf                      # Export as PDF
showmaster list-templates                  # Show available templates
showmaster init-template bug_report "Bug"  # Use a template
```

### BrowserPilot

```bash
browserpilot navigate https://example.com     # Open URL
browserpilot snap screenshot.png              # Screenshot
browserpilot save-pdf page.pdf                # Save as PDF
browserpilot fill "#email" "me@test.com"      # Fill form field
browserpilot type-text "#search" "hello"      # Type with keystrokes
browserpilot click-el "button.submit"         # Click element
browserpilot wait-for "#loaded"               # Wait for element
browserpilot wait-idle                        # Wait for network idle
browserpilot execute-js "document.title"      # Run JavaScript
browserpilot ai-click "the login button"      # AI-powered click
browserpilot ai-query "What is this page?"    # Ask AI about the page
browserpilot export-cookies cookies.json      # Export cookies
browserpilot import-cookies cookies.json      # Import cookies
browserpilot replay test.json --speed 2       # Replay action script
browserpilot create-script workflow.json      # Create script interactively
```

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Showmaster | BrowserPilot |
|----------|-----------|--------------|
| `Ctrl+S` | Save | — |
| `Ctrl+E` | Toggle editor | — |
| `Ctrl+Shift+F` | Finalize | — |
| `Ctrl+Shift+P` | Export PDF | — |
| `Ctrl+L` | — | Navigate |
| `Ctrl+J` | — | Execute JS |
| `Ctrl+Shift+S` | — | Screenshot |
| `Ctrl+R` | Start recording | — |
| `F1` | User Guide | User Guide |
| `Ctrl+Q` | Quit | Quit |

---

## 🎨 Themes

Dark mode auto-detects your OS theme. Override in `~/.showmaster_settings.json`:

```json
{ "dark_mode": "dark" }
```

Custom CSS: create `~/.showmaster/themes/custom.css` for custom preview styling.

---

## 🧪 Testing

```bash
uv sync --extra dev
uv run pytest tests/ -v         # 44 tests (unit + browser integration)
```

---

## 🏗️ Project Structure

```
showmaster-suite/
├── src/
│   ├── showmaster/          # Documentation tool
│   │   ├── core.py          # Report engine
│   │   ├── gui.py           # Split-pane GUI
│   │   ├── cli.py           # CLI interface
│   │   └── templates.py     # Report templates
│   ├── browserpilot/        # Browser automation
│   │   ├── core.py          # Playwright engine
│   │   ├── gui.py           # Control center GUI
│   │   ├── cli.py           # CLI interface
│   │   ├── recorder.py      # Action recording/playback
│   │   └── memory.py        # AI conversation memory
│   └── common/
│       └── settings.py      # Shared settings & dark mode
├── tests/                   # pytest test suite
├── launchers/               # Desktop launchers
├── .github/workflows/       # CI/CD pipelines
├── USER_GUIDE.md            # Comprehensive user guide
└── pyproject.toml           # Package config
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

**Author:** Mohammed Maniruzzaman, PhD

---

<div align="center">

*Built with [Playwright](https://playwright.dev/) · [wxPython](https://wxpython.org/) · [Ollama](https://ollama.com/)*

</div>

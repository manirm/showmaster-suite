# Showmaster & BrowserPilot — User Guide

Welcome to the documentation and browser automation suite. This guide walks you through every feature of **Showmaster** (documentation builder) and **BrowserPilot** (browser automation), step by step.

---

## Table of Contents

- [Installation](#-installation)
- [Part 1 — Showmaster](#-part-1--showmaster)
  - [Tutorial 1: Your First Report (CLI)](#tutorial-1-your-first-report-cli)
  - [Tutorial 2: Using the GUI](#tutorial-2-using-the-gui)
  - [Tutorial 3: Capturing Images](#tutorial-3-capturing-images)
  - [Tutorial 4: Screen Recording](#tutorial-4-screen-recording)
  - [Tutorial 5: Web Screenshots](#tutorial-5-web-screenshots)
  - [Tutorial 6: Finalizing a Report](#tutorial-6-finalizing-a-report)
  - [CLI Reference](#showmaster-cli-reference)
- [Part 2 — BrowserPilot](#-part-2--browserpilot)
  - [Tutorial 7: Navigate & Screenshot (CLI)](#tutorial-7-navigate--screenshot-cli)
  - [Tutorial 8: AI-Powered Interactions](#tutorial-8-ai-powered-interactions)
  - [Tutorial 9: JavaScript Execution](#tutorial-9-javascript-execution)
  - [Tutorial 10: Using the GUI](#tutorial-10-using-the-gui)
  - [CLI Reference](#browserpilot-cli-reference)
- [Integration: Using Both Together](#-integration-using-both-together)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## 🚀 Installation

### Prerequisites

| Requirement | Purpose | Install |
|---|---|---|
| **Python 3.12+** | Runtime | [python.org](https://www.python.org/) |
| **uv** | Dependency management | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **Ollama** | Local AI for BrowserPilot | [ollama.com](https://ollama.com/) |
| **FFmpeg** | Video processing | `brew install ffmpeg` (macOS) |

### Step-by-Step Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-username/showmaster-suite.git
cd showmaster-suite

# 2. Install Python dependencies
uv sync

# 3. Install the Playwright browser
uv run playwright install chromium

# 4. (Optional) Pull an AI model for BrowserPilot
ollama pull llama3
```

### Verify Installation

```bash
# Check that both CLIs are available
uv run showmaster --help
uv run browserpilot --help
```

You should see a list of commands for each tool. If so, you're ready!

---

## 🎬 Part 1 — Showmaster

Showmaster records your workflow into a professional Markdown report. Think of it as a "live notebook" for demos, tutorials, and documentation.

---

### Tutorial 1: Your First Report (CLI)

**Goal**: Create a simple Markdown report with notes and command output.

**Step 1 — Initialize a new report file:**

```bash
uv run showmaster -f my_report.md init "My First Demo"
```

This creates `my_report.md` with a title header.

**Step 2 — Add a descriptive note:**

```bash
uv run showmaster -f my_report.md note "This report documents the setup of our project."
```

**Step 3 — Execute a command and log its output:**

```bash
uv run showmaster -f my_report.md exec "ls -la"
```

This runs `ls -la`, captures the output, and appends it to the report as a fenced code block.

**Step 4 — Add another command:**

```bash
uv run showmaster -f my_report.md exec "python --version"
```

**Step 5 — Review the report:**

Open `my_report.md` in any Markdown viewer. You'll see the title, your note, and each command with its output formatted neatly.

> **Tip**: The `-f` flag specifies the target file. It defaults to `demo.md` if omitted.

---

### Tutorial 2: Using the GUI

**Goal**: Use the graphical interface for a more interactive experience.

**Step 1 — Launch the GUI:**

```bash
uv run showmaster-gui
```

A window opens with controls on the left and a live Markdown preview on the right.

**Step 2 — Add a note:**

1. Type your text in the **"Add Note"** text area.
2. Click **"Add Note"**.
3. Watch the preview update instantly on the right.

**Step 3 — Execute a command:**

1. Type a shell command (e.g., `echo Hello World`) in the **"Execute Command"** field.
2. Click **"Run Exec"**.
3. The command output appears in the preview.

**Step 4 — Undo a mistake:**

Click **"Undo Last"** to remove the most recently added section.

**Step 5 — Finalize:**

Click **"Finalize"** to generate a Table of Contents and add a license footer.

---

### Tutorial 3: Capturing Images

**Goal**: Run a command that produces an image and auto-embed it in the report.

```bash
# Suppose you have a Python script that generates a chart:
uv run showmaster -f my_report.md image "python plot_chart.py"
```

**How it works:**

1. Showmaster runs the command.
2. It scans the output for image file paths (`.png`, `.jpg`, `.gif`, `.svg`).
3. If found, it copies the image next to the report and embeds it with Markdown syntax: `![filename](filename)`.

> **Note**: The command's stdout must print the path to the generated image. For example: `print("output_chart.png")`.

---

### Tutorial 4: Screen Recording

**Goal**: Record your screen and embed the video in the report.

**Using the CLI:**

```bash
# Record for 10 seconds (default)
uv run showmaster -f my_report.md record --duration 15
```

**Using the GUI:**

1. Go to **Tools → Start Video Recording** (or click the **"Start"** button in the Video Recording section).
2. Perform your demo on screen.
3. Click **"Stop"** when finished.

The recording is saved as an `.mp4` file and linked in the report.

> **macOS Note**: You may need to grant "Screen Recording" permissions to your terminal in **System Settings → Privacy & Security → Screen Recording**.

---

### Tutorial 5: Web Screenshots

**Goal**: Capture a screenshot of a live website and embed it in the report.

```bash
uv run showmaster -f my_report.md browser-snap "https://github.com"
```

**How it works:**

1. Showmaster uses BrowserPilot to open the URL.
2. Waits 2 seconds for the page to render.
3. Takes a screenshot and saves it next to the report.
4. Embeds the screenshot in Markdown.

**In the GUI:**

1. Enter a URL in the **"Web Capture"** section.
2. Click **"Capture Page"**.
3. The preview updates with the embedded screenshot.

---

### Tutorial 6: Finalizing a Report

**Goal**: Add a professional Table of Contents and footer.

```bash
uv run showmaster -f my_report.md finalize
```

**What Finalize does:**

1. Scans all `##` and `###` headings in your report.
2. Generates a clickable Table of Contents after the title.
3. Appends a license footer: *"This report was generated by Showmaster. Licensed under MIT."*

> **Tip**: Always finalize as the last step — it inserts the TOC at the top.

---

### Showmaster CLI Reference

| Command | Description | Example |
|---|---|---|
| `init TITLE` | Create a new report | `showmaster -f report.md init "Demo"` |
| `note TEXT` | Add a text note | `showmaster -f report.md note "Step 1"` |
| `exec COMMAND` | Run command, log output | `showmaster -f report.md exec "ls"` |
| `image COMMAND` | Run command, embed output image | `showmaster -f report.md image "python plot.py"` |
| `pop` | Remove the last section | `showmaster -f report.md pop` |
| `extract` | List all logged commands | `showmaster -f report.md extract` |
| `browser-snap URL` | Screenshot a web page | `showmaster -f report.md browser-snap "https://..."` |
| `record --duration N` | Record screen for N seconds | `showmaster -f report.md record --duration 10` |
| `finalize` | Add TOC and footer | `showmaster -f report.md finalize` |

---

## 🤖 Part 2 — BrowserPilot

BrowserPilot automates a real Chromium browser from the command line or GUI. Browser state (cookies, history) persists between commands.

---

### Tutorial 7: Navigate & Screenshot (CLI)

**Goal**: Open a website and capture a screenshot.

**Step 1 — Navigate to a URL:**

```bash
uv run browserpilot navigate "https://example.com"
```

The browser opens (headless by default), loads the page, and exits.

**Step 2 — Take a screenshot:**

```bash
uv run browserpilot snap screenshot.png
```

BrowserPilot remembers the last URL you visited and restores it automatically.

**Step 3 — Visit another page:**

```bash
uv run browserpilot navigate "https://github.com/trending"
uv run browserpilot snap github_trending.png
```

**Headful mode** (to see the browser window):

```bash
uv run browserpilot --headful navigate "https://example.com"
```

---

### Tutorial 8: AI-Powered Interactions

**Goal**: Use natural language to interact with web pages.

> **Prerequisite**: Ollama must be running with a model pulled (e.g., `ollama pull llama3`).

**Step 1 — Navigate to a page:**

```bash
uv run browserpilot navigate "https://github.com"
```

**Step 2 — AI Click — click an element by describing it:**

```bash
uv run browserpilot ai-click "Sign in button"
```

BrowserPilot extracts all interactive elements from the page, sends them to the local AI, and clicks the best match.

**Step 3 — AI Query — ask a question about the page:**

```bash
uv run browserpilot navigate "https://news.ycombinator.com"
uv run browserpilot ai-query "What is the top story right now?"
```

The AI reads the page text and responds in plain English.

---

### Tutorial 9: JavaScript Execution

**Goal**: Run custom JavaScript on the current page.

**Step 1 — Navigate to a page:**

```bash
uv run browserpilot navigate "https://example.com"
```

**Step 2 — Execute JavaScript:**

```bash
uv run browserpilot execute-js "document.title"
```

This prints the page title. You can run any JavaScript expression.

**More examples:**

```bash
# Get all link URLs on the page
uv run browserpilot execute-js "Array.from(document.querySelectorAll('a')).map(a => a.href)"

# Scroll to the bottom
uv run browserpilot execute-js "window.scrollTo(0, document.body.scrollHeight)"

# Click an element by selector
uv run browserpilot click-el "#my-button"
```

---

### Tutorial 10: Using the GUI

**Goal**: Control the browser through the graphical interface.

**Step 1 — Launch the GUI:**

```bash
uv run browserpilot-gui
```

**Step 2 — Navigate:**

1. Enter a URL in the address bar.
2. Click **"Navigate"**.
3. The log panel shows the result.

**Step 3 — Take a screenshot:**

Click **"Take Screenshot"** — the image is saved as `gui_screenshot.png`.

**Step 4 — Execute JavaScript:**

Click **"Execute JS"**, enter your expression in the dialog, and see the result in the log.

**Step 5 — AI interactions:**

1. Click **"AI Click"** and describe what to click (e.g., "the search box").
2. Click **"AI Query"** and ask a question about the page.

**Step 6 — Reset browser profile:**

Click **"Reset Profile"** to clear all saved cookies, history, and cached data.

---

### Resetting Browser State

To clear all saved browser state (cookies, history, cached data):

```bash
uv run browserpilot reset
```

This deletes the `~/.browserpilot_profile` directory and gives you a fresh start.

---

### BrowserPilot CLI Reference

| Command | Description | Example |
|---|---|---|
| `navigate URL` | Open a URL | `browserpilot navigate "https://..."` |
| `snap PATH` | Screenshot current page | `browserpilot snap output.png` |
| `click-el SELECTOR` | Click by CSS selector | `browserpilot click-el "#login-btn"` |
| `execute-js SCRIPT` | Run JavaScript | `browserpilot execute-js "document.title"` |
| `ai-click DESC` | AI-powered click | `browserpilot ai-click "Sign in"` |
| `ai-query QUESTION` | AI-powered page query | `browserpilot ai-query "What is..."` |
| `reset` | Clear browser profile | `browserpilot reset` |
| `--headful` | Show browser window | `browserpilot --headful navigate "..."` |

---

## 🔗 Integration: Using Both Together

The most powerful workflow combines Showmaster and BrowserPilot.

### Example: Documenting a Web App

```bash
# 1. Start your report
uv run showmaster -f web_review.md init "Web App Review"

# 2. Add a description
uv run showmaster -f web_review.md note "Reviewing the homepage design."

# 3. Capture a web screenshot directly into the report
uv run showmaster -f web_review.md browser-snap "https://myapp.example.com"

# 4. Add additional commentary
uv run showmaster -f web_review.md note "The homepage loads quickly and has a clean layout."

# 5. Capture another page
uv run showmaster -f web_review.md browser-snap "https://myapp.example.com/dashboard"

# 6. Log some API responses
uv run showmaster -f web_review.md exec "curl -s https://myapp.example.com/api/health"

# 7. Finalize with TOC
uv run showmaster -f web_review.md finalize
```

### Using the GUI

1. Open **Showmaster GUI** (`uv run showmaster-gui`).
2. In the **Web Capture** section, enter URLs and click **"Capture Page"**.
3. Showmaster automatically opens BrowserPilot, takes the screenshot, and embeds it in your live preview.
4. To open a full BrowserPilot GUI, go to **Tools → Open Browser Session**.

---

## ⚙ Configuration

Settings are stored in `~/.showmaster_settings.json`:

```json
{
    "ollama_url": "http://localhost:11434",
    "ollama_model": "llama3",
    "browser_headless": false,
    "video_format": "mov"
}
```

| Setting | Description | Default |
|---|---|---|
| `ollama_url` | Ollama server address | `http://localhost:11434` |
| `ollama_model` | AI model for BrowserPilot | `llama3` |
| `browser_headless` | Run browser without a window | `false` |
| `video_format` | Screen recording format | `mov` |

To change a setting, edit the file directly or use the **Preferences** menu in either GUI.

---

## 🛠 Troubleshooting

### Ollama / AI Features Not Working

- **Ensure Ollama is running**: `ollama serve`
- **Verify the model is installed**: `ollama list` — you should see `llama3` or your configured model.
- **Check connectivity**: `curl http://localhost:11434/api/tags`

### Screen Recording Permissions (macOS)

On macOS, screen recording requires explicit permission:

1. Go to **System Settings → Privacy & Security → Screen Recording**.
2. Enable your terminal application (e.g., Terminal, iTerm2, VS Code).
3. Restart the terminal after granting permission.

### Browser Screenshots Are Blank

If `browserpilot snap` returns a blank image:

- Make sure you ran `browserpilot navigate URL` first.
- The state file tracks the last-visited URL. Run `browserpilot reset` and try again.
- Ensure Playwright browsers are installed: `uv run playwright install chromium`.

### Import Errors

If you see `ModuleNotFoundError`:

```bash
# Re-sync dependencies
uv sync

# Verify the package is installed
uv run python -c "import showmaster; import browserpilot; print('OK')"
```

### Playwright Browser Missing

```bash
# Install/reinstall browsers
uv run playwright install chromium
```

---

## 📜 License

Showmaster and BrowserPilot are licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

Built by Mohammed Maniruzzaman, PhD.

# Showmaster & BrowserPilot: The Ultimate Documentation Suite

An integrated suite of tools for software demonstration, browser automation, and high-quality reporting, built for developers and AI agents.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)

---

## 🌟 Overview

This project consists of two core applications designed to work together:

1.  **Showmaster**: A documentation director that records your workflow into professional Markdown reports. It supports shell command logging, image capture, **video recording**, and **web snapshots**.
2.  **BrowserPilot**: A persistent, **AI-powered browser automation** tool. It uses Playwright to control a real browser and **Local Ollama** to provide natural language interaction (e.g., "Click the login button").

---

## 🎨 Showmaster (Recording & Documentation)

Showmaster lets you build a "live" documentation of your work.

### Features
-   **Notes & Executive Summaries**: Record descriptions of your process.
-   **Terminal Integration**: Log shell commands and their exact outputs.
-   **Automatic Image Embedding**: Run a command (e.g., a script that generates a plot) and Showmaster embeds it instantly.
-   **Video Capturing (macOS Native)**: Record your screen for complex demos.
-   **Professional Finalization**: Automatic Table of Contents and polished formatting.

### Quick Start
```bash
# GUI
uv run showmaster-gui

# CLI
showmaster init demo.md "My Project Demo"
showmaster note demo.md "Adding a new feature"
showmaster exec demo.md "ls -R"
```

---

## 🤖 BrowserPilot (Automation & AI)

BrowserPilot is a persistent browser session that you control via CLI, GUI, or AI.

### Features
-   **Persistent CDP Session**: Start a browser once and interact with it across many turns.
-   **AI Interaction**: Use **Local Ollama** to find elements or query the page text in plain English.
-   **Playwright Backend**: Reliable and fast interaction with any modern web page.

### Quick Start
```bash
# Start the session
browserpilot start --headful

# AI-powered interaction
browserpilot navigate "https://github.com/trending"
browserpilot ai-click "See the top repositories"
browserpilot ai-query "What is the most popular repository today?"

# Stop the session
browserpilot stop
```

---

## 🚀 Installation & System Requirements

### Prerequisites
-   **Python 3.12+**
-   **uv** (recommended): `curl -LsSf https://astral.sh/uv/install.sh | sh`
-   **Local Ollama**: Install from [ollama.ai](https://ollama.ai) and run `ollama pull llama3`.
-   **FFmpeg**: For video processing features.

### Installation
```bash
# Sync dependencies
uv sync

# Install Playwright browsers
uv run playwright install chromium
```

---

## 📖 Comprehensive Documentation
For a full breakdown of features and advanced usage, please refer to the [**User Guide**](USER_GUIDE.md).

---

## ⚖️ License
This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

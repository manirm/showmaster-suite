# Showmaster & BrowserPilot User Guide

Welcome to the ultimate documentation and browser automation suite. This guide will help you get started with **Showmaster** (for creating documentation) and **BrowserPilot** (for automating your web browser).

---

## 🚀 Getting Started

### Prerequisites
1.  **Python**: 3.12 or higher.
2.  **uv**: Recommended for dependency management.
3.  **Playwright Browsers**:
    ```bash
    playwright install chromium
    ```
4.  **Local AI (Ollama)**: Required for AI features.
    - Install [Ollama](https://ollama.com/).
    - Run `ollama pull llama3` to get the default model.

### Installation
Clone the repository and install dependencies:
```bash
uv sync
```

---

## 🎬 Showmaster: Documentation Made Easy

Showmaster allows you to record your workflow into a beautiful Markdown report.

### Running the GUI
```bash
showmaster-gui
```

### Key Features
-   **Notes**: Add text descriptions to your report.
-   **Run Exec**: Execute shell commands and log their output.
-   **Image Command**: Run a command that produces an image; Showmaster will automatically embed it.
-   **Web Capture**: Enter a URL and Showmaster will use BrowserPilot to take a screenshot.
-   **Video Recording**: Capture your screen (macOS native) and link it in the report.
-   **Undo Last**: Quickly remove the last section added to the report.
-   **Finalize**: Generates a Table of Contents and adds a professional footer.

---

## 🤖 BrowserPilot: AI-Powered Automation

BrowserPilot provides a persistent browser session that you can control via CLI or GUI.

### Running the GUI
```bash
browserpilot-gui
```

### Key Features
-   **Persistent Sessions**: Start a browser once and interact with it across multiple commands.
-   **AI Click**: Instead of finding complex CSS selectors, just say "Click the Login button".
-   **AI Query**: Ask questions about the current page (e.g., "What is the price of the first item?").
-   **JavaScript Execution**: Run custom JS snippets directly in the page.

### CLI Usage
-   `browserpilot start --headful`: Start the browser.
-   `browserpilot navigate "https://github.com"`: Go to a URL.
-   `browserpilot ai-click "Sign in"`: Use AI to click.
-   `browserpilot ai-query "What are the trending topics?"`: Ask AI about the page.
-   `browserpilot stop`: Close the session.

---

## 🔗 Integration

You can use Showmaster and BrowserPilot together:
1.  Open **Showmaster GUI**.
2.  In the "Web Capture" section, enter a URL.
3.  Showmaster will communicate with the active **BrowserPilot** session to capture the exact state of your web app.

---

## 🛠 Troubleshooting

-   **Ollama Connection Error**: Ensure Ollama is running (`ollama serve`) and that the `llama3` model is pulled.
-   **Screen Recording Permissions**: On macOS, you may need to grant "Screen Recording" permissions to your terminal or Python executable in System Settings.
-   **Port Conflict**: BrowserPilot uses port `9222` for debugging. Ensure no other Chrome instances are using this port.

---

## 📜 License
Showmaster and BrowserPilot are licensed under the MIT License.

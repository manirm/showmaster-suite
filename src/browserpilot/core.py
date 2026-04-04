"""
BrowserPilot core engine.

Uses Playwright's persistent context (user-data-dir) to maintain browser state
between commands. Each command launches Playwright, performs its action, and exits.
The browser state (cookies, history, tabs) persists via the user data directory.
A small state file tracks the last-visited URL so it can be restored.
"""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
import ollama
from common.settings import load_settings

# Directory where browser profile/state is stored between commands
USER_DATA_DIR = Path.home() / ".browserpilot_profile"
# Tiny state file to remember the last URL across invocations
STATE_FILE = USER_DATA_DIR / ".bp_state.json"


class BrowserPilot:
    def __init__(self, headless=True):
        self.headless = headless

    def _save_state(self, url):
        USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps({"last_url": url}))

    def _load_state(self):
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def _run_with_page(self, callback, timeout=30000, restore_url=True):
        """
        Launch a persistent browser context, execute the callback with a Page,
        then close. State is preserved in USER_DATA_DIR between invocations.
        If restore_url is True, navigates to the last-visited URL first.
        """
        USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(USER_DATA_DIR),
                headless=self.headless,
                timeout=timeout,
            )
            try:
                # Reuse existing page or create one
                page = context.pages[0] if context.pages else context.new_page()

                # Restore last URL if needed
                if restore_url:
                    state = self._load_state()
                    last_url = state.get("last_url")
                    if last_url and page.url in ("about:blank", ""):
                        page.goto(last_url, timeout=timeout)

                result = callback(page)
            finally:
                context.close()

            return result

    def open(self, url):
        def _task(page):
            page.goto(url, timeout=30000)
            self._save_state(url)
            print(f"Opened {url}")

        return self._run_with_page(_task, restore_url=False)

    def click(self, selector):
        def _task(page):
            page.click(selector, timeout=10000)
            print(f"Clicked {selector}")

        return self._run_with_page(_task)

    def js(self, script):
        def _task(page):
            result = page.evaluate(script)
            print(result)
            return result

        return self._run_with_page(_task)

    def screenshot(self, path):
        def _task(page):
            page.screenshot(path=path)
            print(f"Screenshot saved to {path}")

        return self._run_with_page(_task)

    def get_page_text(self):
        """Get the text content of the current page."""
        def _task(page):
            return page.evaluate("document.body.innerText")
        return self._run_with_page(_task)

    # ── PDF Capture ───────────────────────────────────────────────────

    def save_pdf(self, path):
        """Save the current page as a PDF file (headless Chromium only)."""
        def _task(page):
            page.pdf(path=path)
            print(f"PDF saved to {path}")
            return path
        # PDF generation requires headless mode
        old_headless = self.headless
        self.headless = True
        try:
            return self._run_with_page(_task)
        finally:
            self.headless = old_headless

    # ── Form Filling ──────────────────────────────────────────────────

    def fill(self, selector, text):
        """Fill a form field with text."""
        def _task(page):
            page.fill(selector, text, timeout=10000)
            print(f"Filled {selector} with '{text}'")
        return self._run_with_page(_task)

    def select(self, selector, value):
        """Select a dropdown option by value."""
        def _task(page):
            page.select_option(selector, value, timeout=10000)
            print(f"Selected '{value}' in {selector}")
        return self._run_with_page(_task)

    def type_text(self, selector, text, delay=50):
        """Type text character by character (for inputs that need keystrokes)."""
        def _task(page):
            page.type(selector, text, delay=delay, timeout=10000)
            print(f"Typed '{text}' into {selector}")
        return self._run_with_page(_task)

    # ── Wait Strategies ───────────────────────────────────────────────

    def wait_for(self, selector, timeout=30000):
        """Wait for a CSS selector to appear on the page."""
        def _task(page):
            page.wait_for_selector(selector, timeout=timeout)
            print(f"Element found: {selector}")
        return self._run_with_page(_task)

    def wait_for_url(self, url_pattern, timeout=30000):
        """Wait for the URL to match a pattern (string or regex)."""
        def _task(page):
            page.wait_for_url(url_pattern, timeout=timeout)
            print(f"URL matched: {url_pattern}")
        return self._run_with_page(_task)

    def wait_idle(self, timeout=30000):
        """Wait for the network to be idle (no requests for 500ms)."""
        def _task(page):
            page.wait_for_load_state("networkidle", timeout=timeout)
            print("Network idle")
        return self._run_with_page(_task)

    # ── Cookie / Session Management ───────────────────────────────────

    def export_cookies(self, path):
        """Export browser cookies to a JSON file."""
        USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(USER_DATA_DIR),
                headless=True,
            )
            try:
                cookies = context.cookies()
                Path(path).write_text(json.dumps(cookies, indent=2))
                print(f"Exported {len(cookies)} cookies to {path}")
                return cookies
            finally:
                context.close()

    def import_cookies(self, path):
        """Import cookies from a JSON file into the browser."""
        cookie_data = json.loads(Path(path).read_text())
        USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(USER_DATA_DIR),
                headless=True,
            )
            try:
                context.add_cookies(cookie_data)
                print(f"Imported {len(cookie_data)} cookies from {path}")
            finally:
                context.close()

    # ── AI Features ───────────────────────────────────────────────────

    def ai_click(self, description):
        def _task(page):
            # Extract interactive elements for context
            elements_data = page.evaluate("""
                () => {
                    const elements = Array.from(
                        document.querySelectorAll('button, a, input, [role="button"]')
                    );
                    return elements.map(el => ({
                        tag: el.tagName,
                        text: el.innerText || el.value || el.placeholder,
                        id: el.id,
                        class: el.className,
                        selector: el.id
                            ? `#${el.id}`
                            : el.tagName.toLowerCase() +
                              (el.className
                                  ? `.${el.className.split(' ').join('.')}`
                                  : '')
                    })).filter(e => e.text && e.text.trim().length > 0);
                }
            """)

            prompt = (
                f"Given these interactive elements on a web page:\n"
                f"{json.dumps(elements_data[:50])}\n\n"
                f"Which one best matches the description: '{description}'? "
                f"Return ONLY the CSS selector of that element."
            )

            settings = load_settings()
            model = settings.get("ollama_model", "llama3")

            response = ollama.chat(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a browser automation assistant. "
                                   "Return only a valid CSS selector.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )

            selector = (
                response["message"]["content"]
                .strip()
                .split("\n")[0]
                .replace("`", "")
            )
            print(f"AI suggests selector: {selector}")
            page.click(selector)
            return selector

        return self._run_with_page(_task)

    def ai_query(self, prompt):
        from browserpilot.memory import get_context_messages, add_turn

        def _task(page):
            text_content = page.evaluate("document.body.innerText")

            full_prompt = (
                f"Context from the current web page:\n"
                f"{text_content[:4000]}\n\n"
                f"User Question: {prompt}"
            )

            settings = load_settings()
            model = settings.get("ollama_model", "llama3")

            # Build messages with conversation history
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful browser assistant. "
                               "Answer questions about the current web page.",
                }
            ]
            messages.extend(get_context_messages())
            messages.append({"role": "user", "content": full_prompt})

            response = ollama.chat(model=model, messages=messages)

            answer = response["message"]["content"]
            # Save this turn to conversation memory
            add_turn(full_prompt, answer)
            print(f"AI Answer: {answer}")
            return answer

        return self._run_with_page(_task)

    def ai_clear(self):
        """Clear AI conversation history."""
        from browserpilot.memory import clear_conversation
        result = clear_conversation()
        print(result)
        return result

    def reset(self):
        """Clear the persistent browser profile."""
        import shutil
        if USER_DATA_DIR.exists():
            shutil.rmtree(USER_DATA_DIR)
            print("Browser profile reset.")
        else:
            print("No profile to reset.")


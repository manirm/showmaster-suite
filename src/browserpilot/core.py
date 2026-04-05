"""
BrowserPilot core engine.

Uses Playwright's persistent context (user-data-dir) to maintain browser state
between commands. Each command launches Playwright, performs its action, and exits.
The browser state (cookies, history, tabs) persists via the user data directory.
A small state file tracks the last-visited URL so it can be restored.
"""
from __future__ import annotations

import json
import logging
import os
import re
import shutil
from pathlib import Path
from typing import Any, Callable, Optional, Union

from playwright.sync_api import Page, sync_playwright
import ollama
from common.settings import load_settings

logger = logging.getLogger(__name__)

# Directory where browser profile/state is stored between commands
USER_DATA_DIR = Path.home() / ".browserpilot_profile"
# Tiny state file to remember the last URL across invocations
STATE_FILE = USER_DATA_DIR / ".bp_state.json"


class BrowserPilot:
    """Persistent browser automation engine backed by Playwright and Ollama."""

    DEFAULT_TIMEOUT: int = 30_000
    """Default timeout in milliseconds for navigation and element waits."""

    INTERACTION_TIMEOUT: int = 10_000
    """Shorter timeout for quick interactions (click, fill, type)."""

    MAX_AI_ELEMENTS: int = 30
    """Maximum number of DOM elements sent to the AI for selector matching."""

    MAX_CONTEXT_CHARS: int = 4000
    """Maximum characters of page text sent as AI context."""

    def __init__(self, headless: bool = True) -> None:
        self.headless = headless

    # ── State Persistence ─────────────────────────────────────────────

    def _save_state(self, url: str) -> None:
        USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps({"last_url": url}))

    def _load_state(self) -> dict[str, Any]:
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    # ── Safety Helpers ────────────────────────────────────────────────

    @staticmethod
    def _safe_path(path: str, must_exist: bool = False) -> Path:
        """Resolve and validate a file path against directory traversal."""
        resolved = Path(path).resolve()
        if must_exist and not resolved.exists():
            raise FileNotFoundError(f"File not found: {resolved}")
        home = Path.home().resolve()
        if not str(resolved).startswith(str(home)):
            raise ValueError(
                f"Path must be within home directory: {resolved}"
            )
        return resolved

    @staticmethod
    def _validate_selector(page: Page, selector: str) -> str:
        """Sanitize and verify an AI-generated CSS selector before use."""
        # Strip markdown / code-fence artifacts
        selector = selector.strip().strip("`").strip('"').strip("'")
        # Remove any leading/trailing whitespace or newlines
        selector = selector.split("\n")[0].strip()

        # Reject obviously dangerous patterns
        dangerous = ["javascript:", "data:", "<script", "onclick", "onerror"]
        lower = selector.lower()
        if any(d in lower for d in dangerous):
            raise ValueError(f"Rejected dangerous selector: {selector}")

        # Reject empty or overly broad selectors
        if not selector or selector in ("*", "body", "html", "head"):
            raise ValueError(f"Rejected overly broad selector: {selector}")

        # Verify the element actually exists on the page
        element = page.query_selector(selector)
        if element is None:
            raise ValueError(f"Selector not found on page: {selector}")

        return selector

    @staticmethod
    def _extract_structured_text(page: Page, max_chars: int = 4000) -> str:
        """Extract page text with structure, truncating at sentence boundaries."""
        raw_text: str = page.evaluate("document.body.innerText") or ""
        if len(raw_text) <= max_chars:
            return raw_text

        # Truncate at the last sentence boundary before the limit
        truncated = raw_text[:max_chars]
        # Find the last sentence-ending punctuation
        last_period = max(
            truncated.rfind(". "),
            truncated.rfind(".\n"),
            truncated.rfind("! "),
            truncated.rfind("? "),
        )
        if last_period > max_chars * 0.5:
            truncated = truncated[: last_period + 1]

        return truncated + "\n\n[… content truncated]"

    # ── Core Runner ───────────────────────────────────────────────────

    def _run_with_page(
        self,
        callback: Callable[[Page], Any],
        timeout: int | None = None,
        restore_url: bool = True,
        headless_override: bool | None = None,
    ) -> Any:
        """
        Launch a persistent browser context, execute the callback with a Page,
        then close. State is preserved in USER_DATA_DIR between invocations.

        Args:
            callback: Function receiving a Playwright Page and returning a result.
            timeout: Navigation/launch timeout in ms. Defaults to DEFAULT_TIMEOUT.
            restore_url: If True, navigates to the last-visited URL first.
            headless_override: If set, overrides self.headless for this call only.
        """
        if timeout is None:
            timeout = self.DEFAULT_TIMEOUT

        headless = headless_override if headless_override is not None else self.headless
        USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(USER_DATA_DIR),
                headless=headless,
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
                        try:
                            page.goto(last_url, timeout=timeout)
                        except Exception as exc:
                            logger.warning("Failed to restore URL %s: %s", last_url, exc)

                result = callback(page)
            finally:
                context.close()

            return result

    # ── Navigation ────────────────────────────────────────────────────

    def open(self, url: str) -> None:
        """Open a URL in the browser."""
        def _task(page: Page) -> None:
            page.goto(url, timeout=self.DEFAULT_TIMEOUT)
            self._save_state(url)
            logger.info("Opened %s", url)

        return self._run_with_page(_task, restore_url=False)

    def click(self, selector: str) -> None:
        """Click an element by CSS selector."""
        def _task(page: Page) -> None:
            page.click(selector, timeout=self.INTERACTION_TIMEOUT)
            logger.info("Clicked %s", selector)

        return self._run_with_page(_task)

    def js(self, script: str) -> Any:
        """Execute JavaScript on the current page and return the result."""
        def _task(page: Page) -> Any:
            result = page.evaluate(script)
            logger.info("JS result: %s", result)
            return result

        return self._run_with_page(_task)

    def screenshot(self, path: str) -> None:
        """Take a screenshot and save to the given path."""
        safe = self._safe_path(path)

        def _task(page: Page) -> None:
            page.screenshot(path=str(safe))
            logger.info("Screenshot saved to %s", safe)

        return self._run_with_page(_task)

    def get_page_text(self) -> str:
        """Get the text content of the current page."""
        def _task(page: Page) -> str:
            return page.evaluate("document.body.innerText")
        return self._run_with_page(_task)

    # ── PDF Capture ───────────────────────────────────────────────────

    def save_pdf(self, path: str) -> str:
        """Save the current page as a PDF file (headless Chromium only)."""
        safe = self._safe_path(path)

        def _task(page: Page) -> str:
            page.pdf(path=str(safe))
            logger.info("PDF saved to %s", safe)
            return str(safe)

        # PDF generation requires headless mode — use override instead of
        # mutating self.headless (fixes unsafe state toggle bug).
        return self._run_with_page(_task, headless_override=True)

    # ── Form Filling ──────────────────────────────────────────────────

    def fill(self, selector: str, text: str) -> None:
        """Fill a form field with text."""
        def _task(page: Page) -> None:
            page.fill(selector, text, timeout=self.INTERACTION_TIMEOUT)
            logger.info("Filled %s", selector)
        return self._run_with_page(_task)

    def select(self, selector: str, value: str) -> None:
        """Select a dropdown option by value."""
        def _task(page: Page) -> None:
            page.select_option(selector, value, timeout=self.INTERACTION_TIMEOUT)
            logger.info("Selected '%s' in %s", value, selector)
        return self._run_with_page(_task)

    def type_text(self, selector: str, text: str, delay: int = 50) -> None:
        """Type text character by character (for inputs that need keystrokes)."""
        def _task(page: Page) -> None:
            page.type(selector, text, delay=delay, timeout=self.INTERACTION_TIMEOUT)
            logger.info("Typed into %s", selector)
        return self._run_with_page(_task)

    # ── Wait Strategies ───────────────────────────────────────────────

    def wait_for(self, selector: str, timeout: int | None = None) -> None:
        """Wait for a CSS selector to appear on the page."""
        wait_ms = timeout or self.DEFAULT_TIMEOUT

        def _task(page: Page) -> None:
            page.wait_for_selector(selector, timeout=wait_ms)
            logger.info("Element found: %s", selector)
        return self._run_with_page(_task)

    def wait_for_url(self, url_pattern: str, timeout: int | None = None) -> None:
        """Wait for the URL to match a pattern (string or regex)."""
        wait_ms = timeout or self.DEFAULT_TIMEOUT

        def _task(page: Page) -> None:
            page.wait_for_url(url_pattern, timeout=wait_ms)
            logger.info("URL matched: %s", url_pattern)
        return self._run_with_page(_task)

    def wait_idle(self, timeout: int | None = None) -> None:
        """Wait for the network to be idle (no requests for 500ms)."""
        wait_ms = timeout or self.DEFAULT_TIMEOUT

        def _task(page: Page) -> None:
            page.wait_for_load_state("networkidle", timeout=wait_ms)
            logger.info("Network idle")
        return self._run_with_page(_task)

    # ── Cookie / Session Management ───────────────────────────────────

    def export_cookies(self, path: str) -> list[dict]:
        """Export browser cookies to a JSON file."""
        safe = self._safe_path(path)

        def _task(page: Page) -> list[dict]:
            cookies = page.context.cookies()
            safe.write_text(json.dumps(cookies, indent=2))
            logger.info("Exported %d cookies to %s", len(cookies), safe)
            return cookies

        # Reuse _run_with_page instead of duplicating Playwright setup
        return self._run_with_page(_task, headless_override=True)

    def import_cookies(self, path: str) -> None:
        """Import cookies from a JSON file into the browser."""
        safe = self._safe_path(path, must_exist=True)
        cookie_data = json.loads(safe.read_text())

        def _task(page: Page) -> None:
            page.context.add_cookies(cookie_data)
            logger.info("Imported %d cookies from %s", len(cookie_data), safe)

        # Reuse _run_with_page instead of duplicating Playwright setup
        return self._run_with_page(_task, headless_override=True)

    # ── AI Features ───────────────────────────────────────────────────

    def ai_click(self, description: str) -> str:
        """AI-powered click — describe what to click in plain English."""
        def _task(page: Page) -> str:
            # Extract interactive elements with robust, ranked selectors.
            # Scoped to visible elements only, capped at MAX_AI_ELEMENTS.
            elements_data = page.evaluate("""
                (maxElements) => {
                    const elements = Array.from(
                        document.querySelectorAll(
                            'button, a, input, select, textarea, '
                            + '[role="button"], [role="link"], [role="tab"]'
                        )
                    );
                    return elements
                        .filter(el => {
                            // Only include visible elements
                            const rect = el.getBoundingClientRect();
                            const style = window.getComputedStyle(el);
                            return (
                                rect.width > 0 &&
                                rect.height > 0 &&
                                style.display !== 'none' &&
                                style.visibility !== 'hidden'
                            );
                        })
                        .slice(0, maxElements)
                        .map((el, idx) => {
                            const text = (
                                el.innerText || el.value ||
                                el.placeholder || el.getAttribute('aria-label') || ''
                            ).trim().substring(0, 80);

                            // Build selector candidates ranked by reliability
                            let selector;
                            if (el.id) {
                                selector = `#${CSS.escape(el.id)}`;
                            } else if (el.getAttribute('data-testid')) {
                                selector = `[data-testid="${el.getAttribute('data-testid')}"]`;
                            } else if (el.getAttribute('aria-label')) {
                                selector = `[aria-label="${el.getAttribute('aria-label')}"]`;
                            } else if (el.name) {
                                selector = `${el.tagName.toLowerCase()}[name="${el.name}"]`;
                            } else {
                                // Fallback: use tag + nth-of-type for uniqueness
                                const parent = el.parentElement;
                                const siblings = parent
                                    ? Array.from(parent.children).filter(
                                          c => c.tagName === el.tagName
                                      )
                                    : [];
                                const nth = siblings.indexOf(el) + 1;
                                selector =
                                    el.tagName.toLowerCase() +
                                    `:nth-of-type(${nth})`;
                            }

                            return {
                                tag: el.tagName,
                                text: text,
                                selector: selector,
                            };
                        })
                        .filter(e => e.text.length > 0);
                }
            """, self.MAX_AI_ELEMENTS)

            prompt = (
                f"Given these interactive elements on a web page:\n"
                f"{json.dumps(elements_data, indent=2)}\n\n"
                f"Which one best matches the description: '{description}'? "
                f"Return ONLY the CSS selector of that element, nothing else."
            )

            settings = load_settings()
            model = settings.get("ollama_model", "llama3")

            response = ollama.chat(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a browser automation assistant. "
                                   "Return only a valid CSS selector, with no "
                                   "explanation or formatting.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )

            raw_selector = response["message"]["content"]
            selector = self._validate_selector(page, raw_selector)
            logger.info("AI suggests selector: %s", selector)
            page.click(selector, timeout=self.INTERACTION_TIMEOUT)
            return selector

        return self._run_with_page(_task)

    def ai_query(self, prompt: str) -> str:
        """Ask AI a question about the current page content."""
        from browserpilot.memory import get_context_messages, add_turn

        def _task(page: Page) -> str:
            text_content = self._extract_structured_text(
                page, max_chars=self.MAX_CONTEXT_CHARS
            )

            full_prompt = (
                f"Context from the current web page:\n"
                f"{text_content}\n\n"
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
            logger.info("AI query answered (%d chars)", len(answer))
            return answer

        return self._run_with_page(_task)

    def ai_clear(self) -> str:
        """Clear AI conversation history."""
        from browserpilot.memory import clear_conversation
        result = clear_conversation()
        logger.info(result)
        return result

    # ── Profile Management ────────────────────────────────────────────

    def reset(self) -> None:
        """Clear the persistent browser profile."""
        if USER_DATA_DIR.exists():
            shutil.rmtree(USER_DATA_DIR)
            logger.info("Browser profile reset.")
        else:
            logger.info("No profile to reset.")

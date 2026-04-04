"""Integration tests for BrowserPilot core functionality.

These tests launch a real headless browser via Playwright.
They require Playwright browsers to be installed:
    uv run playwright install chromium
"""
import pytest
from pathlib import Path
import json


class TestBrowserPilotNavigation:
    def test_open_url(self, bp):
        """Navigate to a URL without error."""
        bp.open("https://example.com")

    def test_state_saved_after_open(self, bp):
        """The last URL should be saved to the state file."""
        bp.open("https://example.com")
        state_file = Path.home() / ".browserpilot_profile" / ".bp_state.json"
        assert state_file.exists()
        data = json.loads(state_file.read_text())
        assert data["last_url"] == "https://example.com"


class TestBrowserPilotScreenshot:
    def test_screenshot_saves_file(self, bp, tmp_path):
        """Take a screenshot and verify the file exists."""
        bp.open("https://example.com")
        screenshot_path = tmp_path / "test_screenshot.png"
        bp.screenshot(str(screenshot_path))
        assert screenshot_path.exists()
        assert screenshot_path.stat().st_size > 0

    def test_screenshot_restores_url(self, bp, tmp_path):
        """Screenshot on a previously navigated page should show content."""
        bp.open("https://example.com")
        screenshot_path = tmp_path / "restored.png"
        bp.screenshot(str(screenshot_path))
        assert screenshot_path.exists()
        assert screenshot_path.stat().st_size > 1000  # Not a blank page


class TestBrowserPilotJS:
    def test_evaluate_expression(self, bp):
        """Execute JavaScript and get a result."""
        bp.open("https://example.com")
        result = bp.js("document.title")
        assert "Example" in str(result)

    def test_evaluate_array(self, bp):
        """Execute JavaScript that returns an array."""
        bp.open("https://example.com")
        result = bp.js("Array.from(document.querySelectorAll('h1')).map(e => e.textContent)")
        assert isinstance(result, list)
        assert len(result) > 0


class TestBrowserPilotClick:
    def test_click_element(self, bp):
        """Click a link on the page by CSS selector."""
        bp.open("https://example.com")
        # example.com has a "More information..." link
        bp.click("a")  # Click the first link


class TestBrowserPilotReset:
    def test_reset_clears_profile(self, bp):
        """Reset should remove the profile directory."""
        bp.open("https://example.com")
        profile_dir = Path.home() / ".browserpilot_profile"
        assert profile_dir.exists()
        bp.reset()
        assert not profile_dir.exists()

    def test_reset_no_profile(self, bp):
        """Reset when no profile exists should not error."""
        profile_dir = Path.home() / ".browserpilot_profile"
        if profile_dir.exists():
            import shutil
            shutil.rmtree(profile_dir)
        bp.reset()  # Should not raise


class TestBrowserPilotGetPageText:
    def test_get_text(self, bp):
        """Get page text content."""
        bp.open("https://example.com")
        text = bp.get_page_text()
        assert "Example Domain" in text

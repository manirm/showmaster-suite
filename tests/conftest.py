"""Shared test fixtures for the Showmaster & BrowserPilot test suite."""
import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def tmp_report(tmp_path):
    """Provide a temporary markdown file path for Showmaster tests."""
    return tmp_path / "test_report.md"


@pytest.fixture
def sm(tmp_report):
    """Provide a pre-initialized Showmaster instance."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from showmaster.core import Showmaster
    instance = Showmaster(tmp_report)
    instance.init("Test Report")
    return instance


@pytest.fixture
def bp():
    """Provide a BrowserPilot instance (headless)."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from browserpilot.core import BrowserPilot
    return BrowserPilot(headless=True)

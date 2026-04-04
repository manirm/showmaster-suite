"""CLI invocation tests using Click's CliRunner."""
import pytest
import sys
from pathlib import Path
from click.testing import CliRunner

# Ensure src is on path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from showmaster.cli import cli as showmaster_cli
from browserpilot.cli import main_cli as browserpilot_cli


class TestShowmasterCLI:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_help(self, runner):
        result = runner.invoke(showmaster_cli, ["--help"])
        assert result.exit_code == 0
        assert "Commands" in result.output

    def test_init(self, runner, tmp_path):
        report = tmp_path / "cli_test.md"
        result = runner.invoke(showmaster_cli, ["-f", str(report), "init", "CLI Test"])
        assert result.exit_code == 0
        assert "Initialized" in result.output
        assert report.exists()

    def test_note(self, runner, tmp_path):
        report = tmp_path / "cli_test.md"
        runner.invoke(showmaster_cli, ["-f", str(report), "init", "Test"])
        result = runner.invoke(showmaster_cli, ["-f", str(report), "note", "My note"])
        assert result.exit_code == 0
        assert "Added note" in result.output

    def test_exec(self, runner, tmp_path):
        report = tmp_path / "cli_test.md"
        runner.invoke(showmaster_cli, ["-f", str(report), "init", "Test"])
        result = runner.invoke(showmaster_cli, ["-f", str(report), "exec", "echo hello"])
        assert result.exit_code == 0
        assert "Executed" in result.output

    def test_extract(self, runner, tmp_path):
        report = tmp_path / "cli_test.md"
        runner.invoke(showmaster_cli, ["-f", str(report), "init", "Test"])
        runner.invoke(showmaster_cli, ["-f", str(report), "exec", "echo cmd1"])
        result = runner.invoke(showmaster_cli, ["-f", str(report), "extract"])
        assert result.exit_code == 0
        assert "echo cmd1" in result.output

    def test_pop(self, runner, tmp_path):
        report = tmp_path / "cli_test.md"
        runner.invoke(showmaster_cli, ["-f", str(report), "init", "Test"])
        runner.invoke(showmaster_cli, ["-f", str(report), "exec", "echo to_remove"])
        result = runner.invoke(showmaster_cli, ["-f", str(report), "pop"])
        assert result.exit_code == 0
        assert "Popped" in result.output

    def test_finalize(self, runner, tmp_path):
        report = tmp_path / "cli_test.md"
        runner.invoke(showmaster_cli, ["-f", str(report), "init", "Test"])
        result = runner.invoke(showmaster_cli, ["-f", str(report), "finalize"])
        assert result.exit_code == 0
        assert "finalized" in result.output.lower()


class TestBrowserPilotCLI:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_help(self, runner):
        result = runner.invoke(browserpilot_cli, ["--help"])
        assert result.exit_code == 0
        assert "Commands" in result.output
        assert "navigate" in result.output

    def test_reset(self, runner):
        result = runner.invoke(browserpilot_cli, ["reset"])
        assert result.exit_code == 0

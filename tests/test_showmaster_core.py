"""Unit tests for Showmaster core functionality."""
import pytest
from pathlib import Path


class TestInit:
    def test_creates_file(self, sm, tmp_report):
        assert tmp_report.exists()

    def test_file_has_title(self, sm, tmp_report):
        content = tmp_report.read_text()
        assert content.startswith("# Test Report\n")

    def test_overwrites_existing(self, sm, tmp_report):
        sm.init("New Title")
        content = tmp_report.read_text()
        assert "# New Title" in content
        assert "Test Report" not in content


class TestNote:
    def test_appends_text(self, sm, tmp_report):
        sm.note("Hello World")
        content = tmp_report.read_text()
        assert "Hello World" in content

    def test_multiple_notes(self, sm, tmp_report):
        sm.note("First note")
        sm.note("Second note")
        content = tmp_report.read_text()
        assert "First note" in content
        assert "Second note" in content

    def test_preserves_title(self, sm, tmp_report):
        sm.note("Some note")
        content = tmp_report.read_text()
        assert content.startswith("# Test Report\n")


class TestExec:
    def test_captures_stdout(self, sm, tmp_report):
        output = sm.exec("echo hello")
        assert "hello" in output

    def test_appends_to_report(self, sm, tmp_report):
        sm.exec("echo test123")
        content = tmp_report.read_text()
        assert "### Exec: `echo test123`" in content
        assert "test123" in content

    def test_captures_stderr(self, sm, tmp_report):
        output = sm.exec("echo err >&2")
        assert "err" in output

    def test_failed_command(self, sm, tmp_report):
        output = sm.exec("false")
        # Should not raise, just capture the empty output
        assert isinstance(output, str)

    def test_custom_shell(self, sm, tmp_report):
        output = sm.exec("echo $SHELL", shell="sh")
        assert isinstance(output, str)


class TestPop:
    def test_removes_last_section(self, sm, tmp_report):
        sm.exec("echo first")
        sm.exec("echo second")
        sm.pop()
        content = tmp_report.read_text()
        assert "first" in content
        assert "second" not in content

    def test_pop_empty_file(self, sm, tmp_report):
        # Should not raise on a file with just the title
        sm.pop()

    def test_pop_nonexistent_file(self, tmp_path):
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        from showmaster.core import Showmaster
        sm = Showmaster(tmp_path / "nonexistent.md")
        sm.pop()  # Should not raise


class TestExtract:
    def test_extracts_commands(self, sm):
        sm.exec("echo cmd1")
        sm.exec("echo cmd2")
        commands = sm.extract()
        assert commands == ["echo cmd1", "echo cmd2"]

    def test_empty_report(self, sm):
        commands = sm.extract()
        assert commands == []

    def test_ignores_notes(self, sm):
        sm.note("Just a note")
        sm.exec("echo real_cmd")
        commands = sm.extract()
        assert commands == ["echo real_cmd"]


class TestImage:
    def test_image_not_found_adds_warning(self, sm, tmp_report):
        # Command that outputs no image path
        sm.image("echo no_image_here")
        content = tmp_report.read_text()
        assert "Warning" in content

    def test_image_found_embeds(self, sm, tmp_report, tmp_path):
        # Create a dummy image and have the command print its path
        img = tmp_path / "test_chart.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n")  # Minimal PNG header
        sm.image(f"echo {img}")
        content = tmp_report.read_text()
        assert "test_chart.png" in content


class TestFinalize:
    def test_adds_toc(self, sm, tmp_report):
        sm.exec("echo step1")
        sm.exec("echo step2")
        result = sm.finalize()
        content = tmp_report.read_text()
        assert "## Table of Contents" in content
        assert "Report finalized" in result

    def test_adds_license_notice(self, sm, tmp_report):
        sm.finalize()
        content = tmp_report.read_text()
        assert "Licensed under MIT" in content

    def test_toc_has_links(self, sm, tmp_report):
        sm.exec("echo step1")
        sm.finalize()
        content = tmp_report.read_text()
        assert "](#" in content  # Anchor link


class TestRecord:
    def test_start_stop(self, sm, tmp_report):
        import time
        result_start = sm.start_record()
        assert "started" in result_start.lower() or "Recording" in result_start
        time.sleep(0.5)
        result_stop = sm.stop_record()
        assert "stopped" in result_stop.lower() or "saved" in result_stop.lower()

    def test_double_start(self, sm):
        sm.start_record()
        result = sm.start_record()
        assert "already" in result.lower()
        sm.stop_record()

    def test_stop_without_start(self, sm):
        result = sm.stop_record()
        assert "no recording" in result.lower()

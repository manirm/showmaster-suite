#!/bin/bash
# BrowserPilot GUI Launcher
# Double-click this file to open BrowserPilot without using a terminal.
cd "$(dirname "$0")/.."
exec .venv/bin/python -m browserpilot.gui

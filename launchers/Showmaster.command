#!/bin/bash
# Showmaster GUI Launcher
# Double-click this file to open Showmaster without using a terminal.
cd "$(dirname "$0")/.."
exec .venv/bin/python -m showmaster.gui

@echo off
REM BrowserPilot GUI Launcher
REM Double-click this file to open BrowserPilot without using a terminal.
cd /d "%~dp0\.."
.venv\Scripts\python.exe -m browserpilot.gui

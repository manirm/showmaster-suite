@echo off
REM Showmaster GUI Launcher
REM Double-click this file to open Showmaster without using a terminal.
cd /d "%~dp0\.."
.venv\Scripts\python.exe -m showmaster.gui

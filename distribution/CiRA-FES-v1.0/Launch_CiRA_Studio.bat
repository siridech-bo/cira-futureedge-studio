@echo off
REM CiRA Studio Launcher
cd /d "%~dp0\cira_studio_source"
if not exist "main.py" (
    echo ERROR: CiRA Studio source files not found!
    pause
    exit /b 1
)
call run_cira_studio.bat

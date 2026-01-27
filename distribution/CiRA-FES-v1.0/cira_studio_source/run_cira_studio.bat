@echo off
REM CiRA Studio - Launcher Script
REM This script runs CiRA Studio from Python source

REM Change to the script directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo.
    echo Please run install.bat first to set up the environment.
    echo.
    pause
    exit /b 1
)

REM Check if dependencies are installed (quick check for one key package)
python -c "import customtkinter" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Dependencies are not installed!
    echo.
    echo Please run install.bat first to install dependencies.
    echo.
    pause
    exit /b 1
)

REM Run CiRA Studio
echo Starting CiRA Studio...
python main.py

REM If python exits with error, pause to show error message
if errorlevel 1 (
    echo.
    echo CiRA Studio exited with an error.
    pause
)

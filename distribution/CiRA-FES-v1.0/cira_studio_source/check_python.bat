@echo off
REM Check if Python is installed

echo Checking Python installation...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Python is NOT installed or not in PATH
    echo.
    echo CiRA Studio requires Python 3.10 or higher.
    echo.
    echo Please download and install Python from:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANT: Check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo [OK] Python is installed:
python --version
echo.

python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Python version is too old!
    echo Python 3.8 or higher is required.
    echo.
    pause
    exit /b 1
)

echo [OK] Python version is compatible
echo.
echo Next step: Run install.bat to install CiRA Studio dependencies
echo.
pause

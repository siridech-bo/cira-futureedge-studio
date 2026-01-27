@echo off
REM CiRA Studio - Installation Script
REM This script installs all required Python dependencies

echo ========================================
echo CiRA FutureEdge Studio - Installation
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.10 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

REM Check Python version (must be 3.8+)
python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.8 or higher is required!
    echo.
    pause
    exit /b 1
)

echo Installing dependencies from requirements.txt...
echo This may take 5-10 minutes...
echo.

REM Install llama-cpp-python separately with pre-built wheels (avoids compilation)
echo Step 1/2: Installing llama-cpp-python (pre-built binary)...
pip install llama-cpp-python>=0.3.0 --prefer-binary --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu

echo.
echo Step 2/2: Installing remaining dependencies...
REM Install dependencies
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR: Installation failed!
    echo.
    echo Please check your internet connection and try again.
    echo If the problem persists, install dependencies manually:
    echo    pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Installation completed successfully!
echo ========================================
echo.
echo You can now run CiRA Studio by double-clicking:
echo    run_cira_studio.bat
echo.
pause

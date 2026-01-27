@echo off
REM CiRA Pipeline Builder - Installer Build Script
REM Self-contained distribution version

echo ============================================================
echo CiRA Pipeline Builder - Installer Build
echo ============================================================
echo.

REM Check if Inno Setup is installed
set INNO_COMPILER="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %INNO_COMPILER% (
    echo ERROR: Inno Setup not found at %INNO_COMPILER%
    echo.
    echo Please install Inno Setup 6 from:
    echo https://jrsoftware.org/isdl.php
    echo.
    pause
    exit /b 1
)

REM Check if executable exists
if not exist "pipeline_builder.exe" (
    echo ERROR: pipeline_builder.exe not found in this folder!
    echo.
    echo This distribution folder should contain:
    echo   - pipeline_builder.exe
    echo   - All required DLL files
    echo   - templates\ folder
    echo   - fonts\ folder
    echo.
    pause
    exit /b 1
)

REM Verify required DLLs
echo Checking required DLLs...
set MISSING=0
if not exist "libgcc_s_seh-1.dll" (
    echo   MISSING: libgcc_s_seh-1.dll
    set MISSING=1
)
if not exist "libstdc++-6.dll" (
    echo   MISSING: libstdc++-6.dll
    set MISSING=1
)
if not exist "libssh.dll" (
    echo   MISSING: libssh.dll
    set MISSING=1
)
if not exist "libwinpthread-1.dll" (
    echo   MISSING: libwinpthread-1.dll
    set MISSING=1
)

if %MISSING%==1 (
    echo.
    echo ERROR: Required DLL files are missing!
    echo Please run the prepare_distribution script first.
    pause
    exit /b 1
)

echo   All required DLLs present
echo.

REM Create output directory
if not exist "installer_output" mkdir "installer_output"

REM Compile the installer
echo Compiling Inno Setup script...
echo.
%INNO_COMPILER% "pipeline_builder_installer.iss"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo SUCCESS! Installer created successfully
    echo ============================================================
    echo.
    echo Location: installer_output\CiRA_Pipeline_Builder_Setup_v1.0.0.exe
    echo.
    echo Distribution Details:
    dir /b installer_output\*.exe
    echo.
    echo File size:
    for %%F in (installer_output\*.exe) do echo   %%~zF bytes (%%~nF%%~xF)
    echo.
    echo You can now distribute this installer to customers.
    echo No Python, MinGW, or other dependencies needed!
    echo.
) else (
    echo.
    echo ============================================================
    echo ERROR: Installer compilation failed!
    echo ============================================================
    echo.
    pause
    exit /b 1
)

pause

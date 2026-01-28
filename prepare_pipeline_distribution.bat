@echo off
REM Prepare Pipeline Builder Distribution Folder
REM Run this script after rebuilding pipeline_builder.exe to update the distribution

echo ============================================================
echo Pipeline Builder - Distribution Preparation
echo ============================================================
echo.

set SOURCE_DIR=pipeline_builder\build\bin
set DIST_DIR=pipeline_builder_distribution
set MINGW_BIN=C:\msys64\mingw64\bin

REM Check if source executable exists
if not exist "%SOURCE_DIR%\pipeline_builder.exe" (
    echo ERROR: pipeline_builder.exe not found!
    echo Please build the project first:
    echo   cd pipeline_builder\build
    echo   cmake --build . --config Release
    echo.
    pause
    exit /b 1
)

REM Create distribution directory
if not exist "%DIST_DIR%" mkdir "%DIST_DIR%"
echo Created/verified distribution directory
echo.

REM Copy executable
echo Copying executable...
copy /Y "%SOURCE_DIR%\pipeline_builder.exe" "%DIST_DIR%\" >nul
echo   [OK] pipeline_builder.exe

REM Copy templates
if exist "%SOURCE_DIR%\templates" (
    echo Copying templates...
    xcopy /Y /E /I "%SOURCE_DIR%\templates" "%DIST_DIR%\templates" >nul
    echo   [OK] templates\
) else if exist "pipeline_builder\templates" (
    echo Copying templates...
    xcopy /Y /E /I "pipeline_builder\templates" "%DIST_DIR%\templates" >nul
    echo   [OK] templates\
)

REM Copy fonts
echo Copying fonts...
if not exist "%DIST_DIR%\fonts" mkdir "%DIST_DIR%\fonts"
if exist "pipeline_builder\fonts\Roboto-Medium.ttf" (
    copy /Y "pipeline_builder\fonts\Roboto-Medium.ttf" "%DIST_DIR%\fonts\" >nul
    echo   [OK] Roboto-Medium.ttf
) else if exist "pipeline_builder\third_party\imgui\misc\fonts\Roboto-Medium.ttf" (
    copy /Y "pipeline_builder\third_party\imgui\misc\fonts\Roboto-Medium.ttf" "%DIST_DIR%\fonts\" >nul
    echo   [OK] Roboto-Medium.ttf (from ImGui)
) else (
    echo   [WARNING] Roboto-Medium.ttf not found
)

REM Copy MinGW DLLs
echo Copying MinGW runtime DLLs...
if not exist "%MINGW_BIN%" (
    echo WARNING: MinGW not found at %MINGW_BIN%
    echo Please update the MINGW_BIN path in this script
    pause
    exit /b 1
)

copy /Y "%MINGW_BIN%\libgcc_s_seh-1.dll" "%DIST_DIR%\" >nul
echo   [OK] libgcc_s_seh-1.dll

copy /Y "%MINGW_BIN%\libstdc++-6.dll" "%DIST_DIR%\" >nul
echo   [OK] libstdc++-6.dll

copy /Y "%MINGW_BIN%\libssh.dll" "%DIST_DIR%\" >nul
echo   [OK] libssh.dll

copy /Y "%MINGW_BIN%\libwinpthread-1.dll" "%DIST_DIR%\" >nul
echo   [OK] libwinpthread-1.dll

REM Copy optional DLLs (don't fail if missing)
copy /Y "%MINGW_BIN%\libcrypto-3-x64.dll" "%DIST_DIR%\" >nul 2>&1
if %ERRORLEVEL%==0 echo   [OK] libcrypto-3-x64.dll (optional)

copy /Y "%MINGW_BIN%\libssl-3-x64.dll" "%DIST_DIR%\" >nul 2>&1
if %ERRORLEVEL%==0 echo   [OK] libssl-3-x64.dll (optional)

copy /Y "%MINGW_BIN%\zlib1.dll" "%DIST_DIR%\" >nul 2>&1
if %ERRORLEVEL%==0 echo   [OK] zlib1.dll (optional)

echo.

REM Copy cira-block-runtime (CRITICAL for Setup Device and Deploy)
echo Copying cira-block-runtime...
if not exist "cira-block-runtime" (
    echo   [ERROR] cira-block-runtime directory not found!
    echo   This is CRITICAL - Pipeline Builder cannot function without it.
    echo   The Setup Device and Deploy functions will fail.
    pause
    exit /b 1
)

REM Copy source directories
echo   Copying source files...
xcopy /Y /E /I "cira-block-runtime\src" "%DIST_DIR%\cira-block-runtime\src" >nul
xcopy /Y /E /I "cira-block-runtime\include" "%DIST_DIR%\cira-block-runtime\include" >nul
xcopy /Y /E /I "cira-block-runtime\blocks" "%DIST_DIR%\cira-block-runtime\blocks" >nul
xcopy /Y /E /I "cira-block-runtime\web" "%DIST_DIR%\cira-block-runtime\web" >nul
xcopy /Y /E /I "cira-block-runtime\platforms" "%DIST_DIR%\cira-block-runtime\platforms" >nul
xcopy /Y /E /I "cira-block-runtime\tests" "%DIST_DIR%\cira-block-runtime\tests" >nul
xcopy /Y /E /I "cira-block-runtime\templates" "%DIST_DIR%\cira-block-runtime\templates" >nul
echo   [OK] Source directories copied

REM Copy CMakeLists and documentation
echo   Copying build configuration...
copy /Y "cira-block-runtime\CMakeLists.txt" "%DIST_DIR%\cira-block-runtime\" >nul
copy /Y "cira-block-runtime\*.md" "%DIST_DIR%\cira-block-runtime\" >nul 2>&1
echo   [OK] CMakeLists.txt and docs

REM Copy pre-built binaries (optional reference)
echo   Copying pre-built binaries...
if exist "cira-block-runtime\build\cira-block-runtime.exe" (
    if not exist "%DIST_DIR%\cira-block-runtime\build" mkdir "%DIST_DIR%\cira-block-runtime\build"
    copy /Y "cira-block-runtime\build\cira-block-runtime.exe" "%DIST_DIR%\cira-block-runtime\build\" >nul
    echo   [OK] cira-block-runtime.exe
)

if exist "cira-block-runtime\build\blocks" (
    if not exist "%DIST_DIR%\cira-block-runtime\build\blocks" mkdir "%DIST_DIR%\cira-block-runtime\build\blocks"
    xcopy /Y "cira-block-runtime\build\blocks\*.dll" "%DIST_DIR%\cira-block-runtime\build\blocks\" >nul 2>&1
    if %ERRORLEVEL%==0 echo   [OK] Block DLLs
)

echo   [OK] cira-block-runtime complete
echo.

echo ============================================================
echo Distribution preparation complete!
echo ============================================================
echo.
echo Location: %DIST_DIR%\
echo.
echo Contents:
dir /b "%DIST_DIR%"
echo.
echo Next steps:
echo 1. Open %DIST_DIR%\pipeline_builder_installer.iss with Inno Setup
echo 2. Click Build -^> Compile (or press F9)
echo 3. Installer will be in %DIST_DIR%\installer_output\
echo.
pause

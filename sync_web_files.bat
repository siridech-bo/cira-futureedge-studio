@echo off
echo ========================================
echo   Syncing Web Files to Jetson Nano
echo ========================================
echo.
echo This script transfers ONLY web files (HTML/CSS/JS) to the Jetson
echo without recompiling the runtime. Use this after editing dashboard files.
echo.
echo Target: 192.168.1.200 (Jetson Nano)
echo Local:  D:\CiRA FES\cira-block-runtime\web
echo Remote: /home/user/cira_projects/cira-runtime/
echo.

REM Transfer web files to both /src/web and /bin/web
echo Step 1: Uploading web directory to src/...
scp -r "D:\CiRA FES\cira-block-runtime\web" user@192.168.1.200:/home/user/cira_projects/cira-runtime/src/
if errorlevel 1 (
    echo ERROR: Failed to upload to src/
    pause
    exit /b 1
)

echo.
echo Step 2: Copying to bin/web (runtime location)...
ssh user@192.168.1.200 "cp -r /home/user/cira_projects/cira-runtime/src/web /home/user/cira_projects/cira-runtime/bin/"
if errorlevel 1 (
    echo ERROR: Failed to copy to bin/web
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Web Files Synced Successfully!
echo ========================================
echo.
echo The changes will take effect on next browser refresh.
echo No need to restart the runtime.
echo.
echo TIP: Use Ctrl+Shift+R in browser to force reload.
echo.
pause

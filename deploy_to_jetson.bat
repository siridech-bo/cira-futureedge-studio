@echo off
echo ===================================
echo Deploying Updated Runtime to Jetson
echo ===================================
echo.
echo Step 1: Stopping runtime on Jetson...
echo Please manually run: ssh user@192.168.1.200 (password: aaaa)
echo Then run: pkill cira-block-runtime
echo.
pause

echo.
echo Step 2: Copying runtime executable...
scp "d:\CiRA FES\cira-block-runtime\build\cira-block-runtime.exe" user@192.168.1.200:/home/user/cira_projects/cira-runtime/bin/cira-block-runtime
echo.

echo Step 3: Copying synthetic signal block...
scp "d:\CiRA FES\cira-block-runtime\build\blocks\sensors\synthetic_signal\synthetic-signal-generator.dll" user@192.168.1.200:/home/user/cira_projects/cira-runtime/blocks/
echo.

echo Step 4: Copying TimesNet block...
scp "d:\CiRA FES\cira-block-runtime\build\blocks\ai\timesnet_onnx\timesnet-v1.2.0.dll" user@192.168.1.200:/home/user/cira_projects/cira-runtime/blocks/
echo.

echo ===================================
echo Deployment Complete!
echo The runtime should auto-restart via deployment system
echo ===================================
pause

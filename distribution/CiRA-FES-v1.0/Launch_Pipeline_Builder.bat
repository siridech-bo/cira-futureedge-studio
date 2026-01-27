@echo off
REM CiRA FES - Pipeline Builder Launcher
REM This ensures the working directory is correct for finding cira-block-runtime

cd /d "%~dp0"
start "" "bin\pipeline_builder.exe"

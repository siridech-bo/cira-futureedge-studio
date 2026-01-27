================================================================================
CiRA Pipeline Builder - Standalone Distribution
================================================================================

VERSION: 1.0.0
BUILD DATE: 2026-01-27

================================================================================
WHAT IS THIS?
================================================================================

CiRA Pipeline Builder is a visual pipeline editor for deploying AI models to
embedded hardware (Jetson Nano and Arduino devices).

This distribution folder contains:
- pipeline_builder.exe - Main application (42 MB)
- MinGW Runtime DLLs - Required libraries (~10 MB)
- templates/ - Code generation templates
- fonts/ - UI fonts

Total size: ~52 MB (uncompressed)

================================================================================
BUILDING THE INSTALLER
================================================================================

This folder is ready to build a Windows installer (.exe).

REQUIREMENTS:
1. Inno Setup 6 (download from https://jrsoftware.org/isdl.php)

STEPS:
1. Install Inno Setup 6
2. Double-click: build_installer.bat
3. Output will be in: installer_output\

OR:

1. Right-click "pipeline_builder_installer.iss"
2. Select "Compile"

================================================================================
INSTALLER OUTPUT
================================================================================

File: CiRA_Pipeline_Builder_Setup_v1.0.0.exe
Size: ~15-20 MB (compressed with LZMA2)

The installer includes:
- All executable files and DLLs
- Templates and fonts
- Start Menu shortcuts
- Optional desktop shortcut
- Uninstaller

================================================================================
DISTRIBUTION
================================================================================

The generated installer is COMPLETELY STANDALONE.

End users need:
- Windows 10/11 (64-bit)
- OpenGL 3.3+ graphics card (any modern GPU)
- 4 GB RAM minimum

End users DO NOT need:
- Python
- Visual Studio
- MinGW/GCC
- Any build tools
- Manual DLL installation

Simply send them the installer .exe file!

================================================================================
SYSTEM REQUIREMENTS (for building installer)
================================================================================

- Windows 10/11
- Inno Setup 6
- 100 MB free disk space

================================================================================
PORTABILITY
================================================================================

This entire folder is self-contained and can be:
- Copied to another Windows machine
- Zipped and shared
- Used to build the installer without needing the development environment

You do NOT need:
- The original pipeline_builder source code
- MinGW installation
- CMake or build tools

Everything needed to create the installer is in this folder!

================================================================================
INTEGRATION WITH CIRA STUDIO
================================================================================

After installation, CiRA Studio can launch Pipeline Builder:

Python example:
    import subprocess
    import os

    pb_path = os.path.join(
        os.environ['PROGRAMFILES'],
        'CiRA Pipeline Builder',
        'pipeline_builder.exe'
    )

    subprocess.Popen([pb_path])

================================================================================
TROUBLESHOOTING
================================================================================

Q: Inno Setup compile fails
A: Make sure all files are in this folder:
   - pipeline_builder.exe
   - libgcc_s_seh-1.dll
   - libstdc++-6.dll
   - libssh.dll
   - libwinpthread-1.dll

Q: Installer too large
A: Normal size is 15-20 MB due to:
   - 42 MB executable (compressed to ~12 MB)
   - DLLs and templates (compressed to ~3-5 MB)
   - LZMA2 compression is already at maximum

Q: Need to update version
A: Edit pipeline_builder_installer.iss:
   Line 5: #define MyAppVersion "1.0.0"

================================================================================
SUPPORT
================================================================================

For questions or issues:
- Check INSTALLER_BUILD_GUIDE.md in the pipeline_builder folder
- Contact CiRA FutureEdge Studio support

================================================================================

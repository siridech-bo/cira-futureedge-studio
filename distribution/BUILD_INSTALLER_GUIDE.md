# CiRA FutureEdge Studio v1.0 - Installer Build Guide

## ✅ Prerequisites Completed

1. ✅ Pipeline Builder templates folder copied
2. ✅ CiRA Studio Python source files copied
3. ✅ All batch scripts created
4. ✅ Documentation prepared
5. ✅ Example datasets included
6. ✅ Inno Setup script created

## 📦 Build the Installer

### Step 1: Download Inno Setup

1. Go to https://jrsoftware.org/isinfo.php
2. Download **Inno Setup 6.x** (latest stable version)
3. Install Inno Setup (use default settings)

### Step 2: Open the Installer Script

1. Navigate to `D:\CiRA FES\distribution\`
2. Right-click `CiRA_FES_Installer.iss`
3. Select **"Compile"** (or open with Inno Setup Compiler)

### Step 3: Build Process

The build will:
- Compile the installer script
- Package all files from `CiRA-FES-v1.0\` folder
- Create `CiRA-FES-v1.0-Setup.exe` in the `distribution\` folder
- Should take 1-2 minutes

### Step 4: Test the Installer

1. Copy `CiRA-FES-v1.0-Setup.exe` to a clean Windows machine (or VM)
2. Run the installer
3. Follow the installation wizard
4. After installation:
   - Verify Start Menu shortcuts appear
   - Check `C:\Program Files\CiRA FES\` has all files
   - Run `check_python.bat` to verify Python
   - Run `install.bat` to install dependencies
   - Test launching Pipeline Builder from Start Menu
   - Test launching CiRA Studio from Start Menu

## 🎯 What the Installer Does

### Installation Process:
1. Checks for 64-bit Windows 10+
2. Prompts for installation directory (default: `C:\Program Files\CiRA FES`)
3. Copies all files:
   - Pipeline Builder (bin/)
   - CiRA Studio Python source (cira_studio_source/)
   - Runtime source code (cira-block-runtime/)
   - Example datasets (examples/)
   - Documentation (docs/)
   - Launcher scripts
4. Creates Start Menu folder "CiRA FutureEdge Studio" with:
   - Pipeline Builder shortcut
   - CiRA Studio shortcut
   - Documentation shortcuts
   - Check Python shortcut
   - Uninstall shortcut
5. Optionally creates desktop shortcuts
6. Offers to run Python check after installation
7. Registers uninstaller in Windows Settings

### Post-Installation User Steps:
1. Run "Check Python Installation" from Start Menu
2. If Python not installed, download from https://www.python.org/downloads/
3. Run "CiRA Studio - Install Dependencies" from Start Menu
4. Launch applications from Start Menu

## 📝 Installer File Structure

```
D:\CiRA FES\distribution\
├── CiRA_FES_Installer.iss           ← Inno Setup script
├── CiRA-FES-v1.0-Setup.exe          ← Generated installer (after build)
└── CiRA-FES-v1.0\                   ← Source files for installer
    ├── bin\
    │   ├── pipeline_builder.exe
    │   └── templates\
    │       ├── arduino\
    │       └── jetson\
    ├── cira-block-runtime\
    ├── cira_studio_source\
    │   ├── main.py
    │   ├── ui\, core\, etc.
    │   ├── install.bat
    │   └── run_cira_studio.bat
    ├── examples\
    ├── docs\
    ├── Launch_Pipeline_Builder.bat
    ├── Launch_CiRA_Studio.bat
    └── README.md
```

## 🚀 Distribution

Once the installer is built and tested:

1. **Upload to distribution platform**:
   - Google Drive / Dropbox / OneDrive
   - Company website download page
   - GitHub Releases (if public)

2. **Provide to customers**:
   - Single file: `CiRA-FES-v1.0-Setup.exe`
   - Size: ~100-150 MB
   - Requirements: Windows 10+ (64-bit), Python 3.8+ (can be installed separately)

3. **Customer installation**:
   - Download `CiRA-FES-v1.0-Setup.exe`
   - Run installer (requires admin rights)
   - Follow installation wizard
   - Install Python if needed
   - Run dependency installer
   - Launch from Start Menu

## 📄 Customer Quick Start

Send customers this simple guide:

```
CiRA FutureEdge Studio v1.0 - Installation Guide

1. Download CiRA-FES-v1.0-Setup.exe
2. Run the installer (right-click → Run as Administrator)
3. Click through the installation wizard
4. After installation, from Start Menu:
   - Run "Check Python Installation"
   - If needed, install Python 3.10+ from python.org
   - Run "CiRA Studio - Install Dependencies"
   - Launch "Pipeline Builder" or "CiRA Studio"

Need help? See docs/QuickStart_Guide.md
```

## ⚠️ Troubleshooting Build Issues

### Issue: "Cannot find source files"
**Solution**: Make sure you're running the Inno Setup compiler from the `distribution\` folder, or adjust paths in the .iss file to absolute paths.

### Issue: "Templates folder not found"
**Solution**: Run this command again:
```bash
cp -r "D:\CiRA FES\pipeline_builder\build\bin\templates"/* "D:\CiRA FES\distribution\CiRA-FES-v1.0\bin\templates/"
```

### Issue: "Installer build fails with permission error"
**Solution**: Run Inno Setup Compiler as Administrator

### Issue: Installer is too large (>500 MB)
**Solution**: Normal size is ~100-150 MB. If larger, check for extra files in CiRA-FES-v1.0\ folder (logs/, output/, models/, __pycache__)

## ✨ Next Steps

After successful installer build:

1. **Test on clean machine**: Most important step!
2. **Create release notes**: Document v1.0 features
3. **Prepare support materials**: Training videos, FAQ
4. **Customer onboarding**: Send installer + quick start guide

---

**Last Updated**: 2026-01-27
**Installer Version**: 1.0.0
**Build Tool**: Inno Setup 6.x

# Pipeline Builder - Installer Quick Start Guide

## What Was Created

### 1. Distribution Folder: `pipeline_builder_distribution\`
**Self-contained, portable folder** with everything needed to build the installer:
- `pipeline_builder.exe` (43 MB)
- All MinGW DLLs (10 MB total)
- `templates\` - Code generation templates
- `fonts\` - UI fonts
- `pipeline_builder_installer.iss` - Inno Setup script
- `build_installer.bat` - One-click build script
- `README.txt` - Distribution documentation

**Total:** ~52 MB uncompressed

### 2. Preparation Script: `prepare_pipeline_distribution.bat`
Run this script whenever you rebuild `pipeline_builder.exe` to update the distribution folder.

---

## How to Build the Installer

### Prerequisites
1. **Install Inno Setup 6**: https://jrsoftware.org/isdl.php

### Build Steps

#### Option 1: Using Batch Script (Easiest)
```bash
cd pipeline_builder_distribution
build_installer.bat
```

#### Option 2: Using Inno Setup GUI
1. Open `pipeline_builder_distribution\pipeline_builder_installer.iss` with Inno Setup
2. Click **Build → Compile** (or press F9)

### Output
```
pipeline_builder_distribution\installer_output\CiRA_Pipeline_Builder_Setup_v1.0.0.exe
```
- Size: ~15-20 MB (compressed)
- Ready to distribute!

---

## Distribution

### What Customers Get
One simple installer file: `CiRA_Pipeline_Builder_Setup_v1.0.0.exe`

### What It Installs
- Pipeline Builder application
- All required DLLs
- Templates and fonts
- Start Menu shortcuts
- Desktop shortcut (optional)
- Uninstaller

### Customer Requirements
✅ Windows 10/11 (64-bit)
✅ OpenGL 3.3+ graphics card
✅ 4 GB RAM

❌ NO Python needed
❌ NO Visual Studio needed
❌ NO MinGW needed
❌ NO manual DLL installation

---

## Updating the Distribution

When you rebuild `pipeline_builder.exe`:

1. Run from project root:
   ```bash
   prepare_pipeline_distribution.bat
   ```

2. This will:
   - Copy latest `pipeline_builder.exe`
   - Update all DLLs
   - Refresh templates and fonts

3. Then rebuild installer:
   ```bash
   cd pipeline_builder_distribution
   build_installer.bat
   ```

---

## Folder Structure

```
CiRA FES/
├── pipeline_builder/                      # Source code & build
│   ├── src/, include/                     # C++ source
│   ├── build/bin/pipeline_builder.exe     # Compiled executable
│   └── templates/, fonts/                 # Resources
│
├── pipeline_builder_distribution/         # INSTALLER PACKAGE
│   ├── pipeline_builder.exe               # Copied from build
│   ├── *.dll                              # Copied from MinGW
│   ├── templates/, fonts/                 # Copied from source
│   ├── pipeline_builder_installer.iss     # Inno Setup script
│   ├── build_installer.bat                # Build script
│   ├── README.txt                         # Documentation
│   └── installer_output/                  # Generated installer
│       └── CiRA_Pipeline_Builder_Setup_v1.0.0.exe
│
└── prepare_pipeline_distribution.bat      # Update distribution
```

---

## Key Benefits

### 1. Self-Contained
The `pipeline_builder_distribution\` folder contains everything needed. You can:
- Zip it and send to another machine
- Build the installer without the source code
- Build without MinGW installed

### 2. Safe for Development
- Original source code untouched
- Build directory untouched
- No mixing development and distribution files

### 3. Easy Updates
One command to refresh the distribution:
```bash
prepare_pipeline_distribution.bat
```

### 4. Customer-Friendly
One installer file, no dependencies, no hassle.

---

## Troubleshooting

### "pipeline_builder.exe not found"
**Solution:** Build the project first:
```bash
cd pipeline_builder/build
cmake --build . --config Release
```

### "Inno Setup not found"
**Solution:** Install from https://jrsoftware.org/isdl.php
Default path: `C:\Program Files (x86)\Inno Setup 6\`

### "Missing DLL files"
**Solution:** Run `prepare_pipeline_distribution.bat` to copy all DLLs

### Update MinGW path
If MinGW is not at `C:\msys64\mingw64\bin`, edit:
- `prepare_pipeline_distribution.bat` (line 9)

---

## Version Control

### What to Commit
✅ `pipeline_builder_installer.iss`
✅ `build_installer.bat`
✅ `prepare_pipeline_distribution.bat`
✅ `README.txt`

### What to Ignore
❌ `pipeline_builder_distribution/*.exe`
❌ `pipeline_builder_distribution/*.dll`
❌ `pipeline_builder_distribution/installer_output/`

The preparation script regenerates these files.

---

## Next Steps

1. **Test the installer**:
   - Build the installer
   - Run it on a clean Windows VM
   - Verify Pipeline Builder launches

2. **Customize** (optional):
   - Add app icon: Edit `pipeline_builder_installer.iss` line 18
   - Change version: Edit line 5
   - Add license: Create `LICENSE.txt` and reference in script

3. **Distribute**:
   - Upload to GitHub Releases
   - Share via Google Drive
   - Host on your website
   - Email to customers

---

## Support

- Full guide: `pipeline_builder/INSTALLER_BUILD_GUIDE.md`
- Distribution readme: `pipeline_builder_distribution/README.txt`
- Inno Setup docs: https://jrsoftware.org/ishelp/

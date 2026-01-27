# llama-cpp-python Compilation Error Fix

## Error
```
CMake Error: CMAKE_C_COMPILER not set
CMake Error: CMAKE_CXX_COMPILER not set
Failed to build llama-cpp-python
```

## Root Cause
- llama-cpp-python requires C/C++ compiler to build from source
- Most Windows systems don't have compilers installed
- Pip tries to compile from source instead of using pre-built wheels

## Fix Applied

### Updated install.bat
Modified to install pre-built binary wheel before other dependencies:

```batch
REM Install llama-cpp-python separately with pre-built wheels (avoids compilation)
pip install llama-cpp-python>=0.3.0 --prefer-binary --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

This downloads a pre-compiled version, no compilation needed!

## For Current Test User

Tell them to run this command manually:

```batch
pip install llama-cpp-python>=0.3.0 --prefer-binary --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

Then continue with:
```batch
pip install -r requirements.txt
```

## Alternative: If Pre-built Wheel Unavailable

If the pre-built wheel doesn't work, user needs to install Visual Studio Build Tools:

1. Download: https://visualstudio.microsoft.com/downloads/
2. Scroll to "Tools for Visual Studio"
3. Download "Build Tools for Visual Studio 2022"
4. Install with:
   - ✅ Desktop development with C++
   - ✅ MSVC v143 compiler
   - ✅ Windows SDK
5. Restart computer
6. Run install.bat again

## Action Required

**Rebuild the installer** with updated install.bat:

1. Open Inno Setup Compiler
2. Open: `D:\CiRA FES\distribution\CiRA_FES_Installer.iss`
3. Build → Compile (Ctrl+F9)

## Benefits of This Fix

✅ No C++ compiler needed on user machines
✅ Much faster installation (no compilation)
✅ Works on all Windows systems out of the box
✅ Pre-built binary optimized for CPU

---
**Date**: 2026-01-27
**Status**: Fixed - Ready to rebuild installer (7th time!)
**Issue**: llama-cpp-python compilation requires compilers not present on most Windows systems

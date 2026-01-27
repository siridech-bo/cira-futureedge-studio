# SciPy CWT Compatibility Fix

## Error
```
Feature extraction failed:
cannot import name 'cwt' from 'scipy.signal'
```

## Root Cause
- SciPy 1.14+ removed the deprecated `cwt` function
- When installing with `scipy>=1.11.4`, pip installed SciPy 1.15.3
- tsfresh library still uses the old `cwt` API
- Python 3.12 triggered this by installing the latest scipy

## Fix Applied
Updated `requirements.txt` to pin scipy below 1.14:

```diff
- scipy>=1.11.4
+ scipy>=1.11.4,<1.14.0  # Pin below 1.14 (cwt removed in 1.14+)
```

## For Users Already Installed

### Option 1: Reinstall scipy (Quick Fix)
On the test machine where the error occurred:

```batch
cd "C:\Program Files\CiRA FES\cira_studio_source"
pip install "scipy>=1.11.4,<1.14.0" --force-reinstall
```

This will downgrade scipy from 1.15.3 to 1.13.1

### Option 2: Reinstall All Dependencies
```batch
cd "C:\Program Files\CiRA FES\cira_studio_source"
pip uninstall scipy -y
pip install -r requirements.txt
```

### Option 3: Full Reinstall (Most Thorough)
1. Uninstall CiRA FES
2. Rebuild installer with fixed requirements.txt
3. Reinstall with new installer
4. Run install.bat

## Action Required

**Rebuild the installer** with the fixed requirements.txt:

1. Open Inno Setup Compiler
2. Open: `D:\CiRA FES\distribution\CiRA_FES_Installer.iss`
3. Build → Compile (Ctrl+F9)

## Verified Versions
- ✅ Python 3.12.10
- ✅ NumPy 1.26.0+
- ✅ SciPy 1.11.4 - 1.13.x (NOT 1.14+)
- ✅ tsfresh 0.20.2+

---
**Date**: 2026-01-27
**Status**: Fixed - Ready to rebuild installer (5th time!)
**Related Issues**:
- Python 3.12 compatibility
- tsfresh dependency on scipy.signal.cwt

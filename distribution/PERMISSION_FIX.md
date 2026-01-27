# Permission Error Fix - Program Files Log Directory

## Issue
CiRA Studio crashed when launched from `C:\Program Files\` with error:
```
PermissionError: [Errno 13] Permission denied: 'C:\\Program Files\\CiRA FES\\cira_studio_source\\logs\\...'
```

## Root Cause
- Applications in `C:\Program Files\` cannot write files without admin privileges
- CiRA Studio was trying to write logs to `PROJECT_ROOT/logs/` which is inside Program Files
- Users don't have write permissions in Program Files without elevation

## Fix Applied
Changed log directory location in `main.py`:

**Before:**
```python
log_dir = PROJECT_ROOT / "logs"  # Inside C:\Program Files\CiRA FES\
```

**After:**
```python
# Use user's AppData folder for logs (writable without admin)
if os.name == 'nt':  # Windows
    log_dir = Path(os.environ.get('LOCALAPPDATA', os.environ.get('APPDATA', PROJECT_ROOT))) / "CiRA FES" / "logs"
else:  # Linux/Mac
    log_dir = Path.home() / ".cira_fes" / "logs"
```

## New Log Location
Logs will now be written to:
- **Windows**: `C:\Users\<username>\AppData\Local\CiRA FES\logs\`
- **Linux/Mac**: `~/.cira_fes/logs/`

This location is always writable without admin privileges.

## Other Writable Directories
The application also writes to these user-writable locations:
- **Output files**: User's Documents or selected directory
- **Models**: Saved in project directories or user-selected locations
- **Config**: Should also be in AppData (check if needed)

## Action Required
**Rebuild the installer** with the fixed main.py:

1. Open Inno Setup Compiler
2. Open: `D:\CiRA FES\distribution\CiRA_FES_Installer.iss`
3. Build → Compile (Ctrl+F9)

## Testing
After rebuilding and installing:
1. Launch CiRA Studio from Start Menu (no admin rights needed)
2. Should start without permission errors
3. Check logs at: `C:\Users\<username>\AppData\Local\CiRA FES\logs\`

---
**Date**: 2026-01-27
**Status**: Fixed - Ready to rebuild installer
**Related**: Windows UAC, Standard User Permissions

# Complete Permission Fixes for Program Files Installation

## Problem Summary
CiRA Studio installed in `C:\Program Files\` cannot write to its own directory without admin rights. Multiple permission errors occurred:

1. **Log files** - Cannot write to `C:\Program Files\CiRA FES\cira_studio_source\logs\`
2. **Output files** - Cannot write to `C:\Program Files\CiRA FES\cira_studio_source\output\`
3. **Model files** - Cannot write to `C:\Program Files\CiRA FES\cira_studio_source\models\`

## Root Cause
Windows User Account Control (UAC) prevents standard users from writing to `C:\Program Files\` for security reasons.

## Complete Fix Applied

### 1. Fixed `main.py` - Log Directory
Changed log location from `PROJECT_ROOT/logs/` to user's AppData:

```python
def setup_logging():
    """Configure logging system."""
    # Use user's AppData folder for logs (writable without admin)
    if os.name == 'nt':  # Windows
        log_dir = Path(os.environ.get('LOCALAPPDATA', os.environ.get('APPDATA', PROJECT_ROOT))) / "CiRA FES" / "logs"
    else:  # Linux/Mac
        log_dir = Path.home() / ".cira_fes" / "logs"

    log_dir.mkdir(parents=True, exist_ok=True)
    # ... rest of logging setup
```

**New Location**: `C:\Users\<username>\AppData\Local\CiRA FES\logs\`

### 2. Fixed `core/config.py` - Models & Output Directories
Changed default paths for writable directories:

```python
def _get_user_data_dir() -> Path:
    """Get user-writable data directory."""
    if os.name == 'nt':  # Windows
        base = Path(os.environ.get('LOCALAPPDATA', os.environ.get('APPDATA', Path.home())))
        return base / "CiRA FES"
    else:  # Linux/Mac
        return Path.home() / ".cira_fes"

@dataclass
class Config:
    # ... other fields ...

    # Paths - Use user-writable directories
    project_root: Path = Path(__file__).parent.parent
    models_dir: Path = _get_user_data_dir() / "models"
    output_dir: Path = _get_user_data_dir() / "output"
    sdk_dir: Path = project_root / "sdk"  # Read-only, can stay in Program Files
    toolchain_dir: Path = project_root / "toolchain"  # Read-only, can stay in Program Files
```

**New Locations**:
- Models: `C:\Users\<username>\AppData\Local\CiRA FES\models\`
- Output: `C:\Users\<username>\AppData\Local\CiRA FES\output\`

## Final Directory Structure

### Program Files (Read-Only)
```
C:\Program Files\CiRA FES\
├── bin\
│   ├── pipeline_builder.exe
│   └── templates\
├── cira_studio_source\
│   ├── main.py
│   ├── ui\, core\, etc.
│   └── requirements.txt
├── cira-block-runtime\
├── sdk\
├── toolchain\
├── examples\
└── docs\
```

### User AppData (Writable)
```
C:\Users\<username>\AppData\Local\CiRA FES\
├── logs\
│   └── cira_studio_*.log
├── models\
│   └── (trained models)
├── output\
│   └── (project output files)
└── (user projects)
```

## Benefits
✅ No admin rights required to run CiRA Studio
✅ Each user has their own data directory
✅ Multiple users can use the same installation
✅ Follows Windows best practices
✅ Uninstaller won't delete user data

## Action Required
**Rebuild the installer** with both fixes:

1. Open Inno Setup Compiler
2. Open: `D:\CiRA FES\distribution\CiRA_FES_Installer.iss`
3. Build → Compile (Ctrl+F9)

## Testing Checklist
After rebuilding and reinstalling:
- [ ] CiRA Studio launches without admin rights
- [ ] Logs appear in `%LOCALAPPDATA%\CiRA FES\logs\`
- [ ] Can create new project (writes to AppData)
- [ ] Can train models (saves to AppData)
- [ ] Can export output files (writes to AppData)
- [ ] No permission errors in UI

---
**Date**: 2026-01-27
**Files Modified**:
- `main.py` (logging)
- `core/config.py` (models & output paths)
**Status**: Fixed - Ready to rebuild installer

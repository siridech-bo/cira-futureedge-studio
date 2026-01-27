# CRITICAL: Pipeline Builder Missing Files

## Problem Found

Pipeline Builder needs the `templates` folder to work correctly!

## Fix Required

Copy from: `D:\CiRA FES\pipeline_builder\build\bin\templates\`
To: `D:\CiRA FES\distribution\CiRA-FES-v1.0\bin\templates\`

### Using Windows Explorer:

1. Navigate to: `D:\CiRA FES\pipeline_builder\build\bin\`
2. **Copy** the `templates` folder (entire folder with arduino/ and jetson/ subfolders)
3. Navigate to: `D:\CiRA FES\distribution\CiRA-FES-v1.0\bin\`
4. **Paste** the templates folder here

### Final structure should be:
```
CiRA-FES-v1.0\
├── bin\
│   ├── pipeline_builder.exe
│   └── templates\          <-- THIS WAS MISSING!
│       ├── arduino\
│       └── jetson\
├── cira-block-runtime\
├── cira_studio_source\
└── ...
```

## Why This Happened

Pipeline Builder looks for code generation templates relative to its executable location. The `templates` folder contains:
- **arduino/**: Arduino code generation templates
- **jetson/**: Jetson deployment script templates

Without this folder, Pipeline Builder may have font rendering issues or fail to deploy properly.

## After Fixing

1. Delete the old broken ZIP
2. Recreate the ZIP with the templates folder included
3. Test again with `Launch_Pipeline_Builder.bat`

---

**Status**: MUST FIX before distribution
**Priority**: CRITICAL

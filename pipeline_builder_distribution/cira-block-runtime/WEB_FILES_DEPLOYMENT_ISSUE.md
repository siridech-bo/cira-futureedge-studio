# Web Files Deployment Issue - Root Cause Analysis

## Problem Summary
When editing web files (HTML/CSS/JS) locally on Windows, running "Setup Device" does NOT deploy the updated files to the Jetson. This causes browser cache issues and wastes debugging time.

## Root Cause

The deployment process in `pipeline_builder/src/deployment/block_runtime_deployer.cpp` works as follows:

### Deployment Timeline:
1. **Line 260**: `TransferRuntimeSource()` uploads all source files including `/web` directory
   - Local: `D:\CiRA FES\cira-block-runtime\web`
   - Remote: `/home/user/cira_projects/cira-runtime/src/web`

2. **Lines 69-73**: Runtime compilation happens on Jetson

3. **Line 407**: After compilation, web files are copied on Jetson:
   ```cpp
   cmd = "cp -r " + remote_src_path + "/web " + bin_dir + "/";
   ```
   - Copies from: `/home/user/cira_projects/cira-runtime/src/web`
   - To: `/home/user/cira_projects/cira-runtime/bin/web`

### The Critical Issue:
**If you edit web files on Windows AFTER "Setup Device" has run**, those changes are NOT transferred because:
- The deployment already transferred the old files in step 1
- The Jetson's `/src/web` directory now contains outdated files
- Future compilations just copy the outdated `/src/web` to `/bin/web`
- The updated Windows files are never uploaded

## Symptoms
- Browser shows old version of JavaScript files (check version in `<script src="js/widgets.js?v=20251231t">`)
- Code changes in web files don't appear after "Setup Device"
- Hard refresh (Ctrl+Shift+R) doesn't help because server is serving old files
- Manual `scp` is required to transfer updated files

## Solutions

### Quick Fix (Manual)
Transfer updated files manually using SCP:
```bash
scp "D:\CiRA FES\cira-block-runtime\web\js\widgets.js" user@192.168.1.200:/home/user/cira_projects/cira-runtime/bin/web/js/widgets.js
```

### Better Fix (Use sync_web_files.bat)
Run the batch script that transfers ALL web files:
```bash
sync_web_files.bat
```

This script:
1. Uploads local web files to `/src/web` on Jetson
2. Copies from `/src/web` to `/bin/web` on Jetson
3. Does NOT recompile (much faster than "Setup Device")

### Best Practice Going Forward
1. **BEFORE editing web files**: Ensure "Setup Device" is complete
2. **AFTER editing web files**: Run `sync_web_files.bat`
3. **In browser**: Hard refresh with Ctrl+Shift+R
4. **Verify**: Check console logs for new version string

## Long-term Solutions

### Option 1: Timestamp-based Sync
Modify `TransferDirectory()` in deployer to check file timestamps and only transfer changed files.

### Option 2: Separate Web Sync Command
Add a "Sync Web Files Only" button to the deployment dialog that calls a new `SyncWebFiles()` function without triggering full recompilation.

### Option 3: Post-Edit Hook
Add a file watcher that automatically runs `sync_web_files.bat` when web files are edited.

## Files Affected
- `pipeline_builder/src/deployment/block_runtime_deployer.cpp` (lines 222-286, 407)
- `cira-block-runtime/web/index.html` (cache-busting version strings)
- All JavaScript files in `cira-block-runtime/web/js/`

## Resolution Date
January 5, 2026

## Created By
Claude (debugging session with user)

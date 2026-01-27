# CiRA FES v1.0 - Known Issues & Solutions

## Issue 1: Pipeline Builder - Font Not Rendering Correctly

### Symptoms:
- Text appears as squares/boxes or is unreadable
- UI looks garbled
- Menus show wrong characters

### Root Cause:
Pipeline Builder is running from the wrong working directory and cannot find font files or the cira-block-runtime directory.

### Solution:
**ALWAYS use the launcher script!**

✅ **Correct**: Double-click `Launch_Pipeline_Builder.bat` (from the root CiRA-FES-v1.0 folder)
❌ **Wrong**: Navigate to `bin\` and run `pipeline_builder.exe` directly

The launcher ensures the working directory is set correctly.

### If Issue Persists:
1. Check if you extracted the entire ZIP correctly
2. Ensure `cira-block-runtime\` folder exists in the same directory as `Launch_Pipeline_Builder.bat`
3. Try running as Administrator

---

## Issue 2: CiRA Studio - Crashes or "Module Not Found"

### Symptoms:
- Python crashes when running CiRA Studio
- "ModuleNotFoundError: No module named 'xxx'"
- Window closes immediately

### Root Cause:
Dependencies not installed or Python version incompatible.

### Solution:

#### Step 1: Verify Python Installation
Open Command Prompt and run:
```batch
python --version
```

**Required**: Python 3.8 or higher (Python 3.10 recommended)

If Python is not found or version is too old:
1. Install Python 3.10 from https://www.python.org/downloads/
2. During installation, check "Add Python to PATH"
3. Restart computer

#### Step 2: Install Dependencies
Navigate to `cira_studio_source\` and run:
```batch
install.bat
```

Wait for installation to complete (5-10 minutes).

#### Step 3: Verify Installation
After install.bat completes, test if key packages are installed:
```batch
python -c "import customtkinter, torch, sklearn, pandas"
```

If this shows an error, reinstall:
```batch
pip install --force-reinstall -r requirements.txt
```

### Common Specific Errors:

#### "No module named 'customtkinter'"
```batch
pip install customtkinter
```

#### "No module named 'torch'"
```batch
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

#### "No module named 'sklearn'"
```batch
pip install scikit-learn
```

#### "DLL load failed" or "ImportError"
**Solution**: Install Visual C++ Redistributable:
- Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
- Install and restart computer

---

## Issue 3: "Python is not in PATH"

### Symptoms:
- `python` command not recognized
- install.bat says "Python is not installed"

### Solution:
1. Find where Python is installed:
   - Default location: `C:\Users\<YourName>\AppData\Local\Programs\Python\Python310\`
   - Or search for `python.exe` in File Explorer

2. Add to PATH manually:
   - Open "Environment Variables" (search in Start menu)
   - Under "User variables", select "Path"
   - Click "Edit"
   - Click "New"
   - Add: `C:\Users\<YourName>\AppData\Local\Programs\Python\Python310\`
   - Add: `C:\Users\<YourName>\AppData\Local\Programs\Python\Python310\Scripts\`
   - Click OK on all dialogs
   - Restart Command Prompt

3. Or reinstall Python with "Add Python to PATH" checked

---

## Issue 4: Pipeline Builder - "Cannot find cira-block-runtime"

### Symptoms:
- Error when trying to deploy
- "Setup Device" fails
- Cannot compile runtime

### Root Cause:
Wrong working directory (same as Issue 1)

### Solution:
Use `Launch_Pipeline_Builder.bat` instead of running the exe directly.

### Verify Fix:
After launching correctly, go to Deploy → Setup Device and the dialog should open without errors.

---

## Issue 5: Very Slow Installation (install.bat)

### Symptoms:
- install.bat takes >30 minutes
- Download speeds are very slow
- Timeouts during installation

### Solution:

**Option 1**: Use a faster pip mirror (China/Asia users)
Edit `requirements.txt` temporarily or use:
```batch
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

**Option 2**: Install in batches
```batch
pip install customtkinter pillow pandas numpy scipy
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install scikit-learn matplotlib seaborn
pip install -r requirements.txt
```

**Option 3**: Download wheel files manually
For slow/unstable connections, download .whl files from:
- https://pypi.org/project/torch/#files (torch)
- https://pypi.org/project/scikit-learn/#files
etc., then install with:
```batch
pip install path\to\downloaded.whl
```

---

## Issue 6: CiRA Studio - Black Screen or Won't Start

### Symptoms:
- Window appears but is completely black
- Window flashes and closes immediately
- No error message visible

### Solution:

**Run from Command Prompt to see errors**:
```batch
cd cira_studio_source
python main.py
```

This will show the actual error message.

Common causes:
1. **Missing dependencies**: Run `install.bat` again
2. **Graphics driver issue**: Update GPU drivers
3. **Display scaling**: Try disabling Windows display scaling
4. **Corrupted installation**: Delete `cira_studio_source` and extract again

---

## Issue 7: Pipeline Builder Works But Deploy Fails

### Symptoms:
- Pipeline Builder starts fine
- Can open pipelines
- But "Setup Device" or "Deploy" fails

### Solutions:

#### Check Jetson Connection
```batch
ping 192.168.1.200
```
(Replace with your Jetson's IP)

If ping fails:
- Check network cable/WiFi
- Verify Jetson is powered on
- Check IP address is correct

#### Check SSH Access
```batch
ssh user@192.168.1.200
```
(Replace 'user' with your Jetson username)

If SSH fails:
- Enable SSH on Jetson: `sudo systemctl start ssh`
- Check firewall: `sudo ufw allow 22`
- Verify credentials are correct

#### Check Jetson Has Space
```batch
ssh user@192.168.1.200 "df -h"
```

Ensure at least 1GB free space.

---

## Still Having Issues?

1. **Check logs**:
   - CiRA Studio: `cira_studio_source\logs\` folder
   - Pipeline Builder: Look for error dialogs

2. **Provide this info for support**:
   - Windows version
   - Python version (`python --version`)
   - Exact error message
   - Steps to reproduce

3. **Contact support**:
   - Email: support@cira-fes.com
   - Include log files and screenshots

---

**CiRA FES v1.0** - Troubleshooting Guide

# Llama-cpp-python Version Fix

## Error
```
llama_model_load: error loading model: done_getting_tensors: wrong number of tensors; expected 255, got 254
llama_load_model_from_file: failed to load model
```

## Root Cause
- **Requirements.txt had**: `llama-cpp-python==0.2.56` (old version)
- **Model format**: Llama 3.2 uses newer GGUF format
- **Old version incompatible**: llama-cpp-python 0.2.x cannot load newer GGUF files
- **Dev machine had**: llama-cpp-python 0.3.2 (works fine)

## Fix Applied
Updated `requirements.txt`:

```diff
- llama-cpp-python==0.2.56
+ llama-cpp-python>=0.3.0  # 0.3+ required for newer GGUF models
```

## For Test User - Quick Fix

On the test machine where the error occurred:

```batch
pip install llama-cpp-python>=0.3.0 --upgrade
```

Then restart CiRA Studio and try loading the model again.

## For New Installations

After rebuilding the installer with the updated requirements.txt, this will be fixed automatically.

## Version Compatibility

| llama-cpp-python | GGUF Support | Llama 3.2 |
|------------------|--------------|-----------|
| 0.2.x | Old format | ❌ No |
| 0.3.x | New format | ✅ Yes |

## Action Required

**Rebuild the installer** with updated requirements.txt:

1. Open Inno Setup Compiler
2. Open: `D:\CiRA FES\distribution\CiRA_FES_Installer.iss`
3. Build → Compile (Ctrl+F9)

---
**Date**: 2026-01-27
**Status**: Fixed - Ready to rebuild installer (6th time!)
**Issue**: llama-cpp-python version too old for Llama 3.2 GGUF format

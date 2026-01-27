# LLM Model Installation Guide

The LLM (Large Language Model) feature in CiRA Studio is **optional** and requires downloading a separate model file.

## Why Separate Download?

- **Large file size**: The model is 2-4 GB
- **Optional feature**: Not required for basic functionality
- **User choice**: Different model sizes available based on your needs

---

## Recommended Model

**Llama 3.2 3B Instruct (Q4_K_M quantization)**
- Size: ~2 GB
- Good balance of performance and quality
- Works well on CPU (no GPU required)

---

## Installation Steps

### Step 1: Download the Model

**Option A: Download from Hugging Face (Recommended)**

1. Visit: https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF
2. Click on **Files and versions** tab
3. Download: `Llama-3.2-3B-Instruct-Q4_K_M.gguf` (~2 GB)

**Option B: Alternative Models**

Other compatible models from Hugging Face:
- **Smaller/Faster**: Llama-3.2-1B-Instruct-Q4_K_M.gguf (~1 GB)
- **Larger/Better**: Llama-3.2-3B-Instruct-Q8_0.gguf (~3.5 GB)

Search on Hugging Face for: `GGUF quantized instruct models`

### Step 2: Place the Model File

**Windows Installation:**

1. Open File Explorer
2. Navigate to: `C:\Users\<YourUsername>\AppData\Local\CiRA FES\models\`
   - Quick way: Press `Win+R`, type `%LOCALAPPDATA%\CiRA FES\models`, press Enter
3. If the `models` folder doesn't exist, create it
4. Copy the downloaded `.gguf` file into this folder

**Expected location:**
```
C:\Users\<YourUsername>\AppData\Local\CiRA FES\models\Llama-3.2-3B-Instruct-Q4_K_M.gguf
```

### Step 3: Verify Installation

1. Open CiRA Studio
2. The LLM features should now be available
3. If using a different model name, update settings in CiRA Studio

---

## Using a Different Model

If you downloaded a different model file:

1. Place the `.gguf` file in: `%LOCALAPPDATA%\CiRA FES\models\`
2. Note the exact filename
3. In CiRA Studio, update the model name in settings to match your file

---

## Troubleshooting

### "Model file not found" error

**Check:**
1. File is in correct location: `%LOCALAPPDATA%\CiRA FES\models\`
2. Filename matches exactly: `Llama-3.2-3B-Instruct-Q4_K_M.gguf`
3. File downloaded completely (~2 GB)

### LLM is very slow

**Try:**
- Use a smaller quantized model (Q4_K_M is good balance)
- Close other applications to free up RAM
- Check your CPU has at least 4 cores

### Download failed or incomplete

**Solutions:**
- Use a download manager for large files
- Check available disk space (need ~4 GB free)
- Try alternative download mirrors on Hugging Face

---

## Model Comparison

| Model | Size | Speed | Quality | RAM Required |
|-------|------|-------|---------|--------------|
| Llama-3.2-1B-Q4_K_M | ~1 GB | Fast | Good | 4 GB |
| Llama-3.2-3B-Q4_K_M | ~2 GB | Medium | Better | 8 GB |
| Llama-3.2-3B-Q8_0 | ~3.5 GB | Slower | Best | 8 GB |

**Recommended for most users:** Llama-3.2-3B-Q4_K_M

---

## What Does the LLM Do?

The LLM in CiRA Studio helps with:
- **Feature selection**: Suggest relevant features for your data
- **Model recommendations**: Propose suitable ML algorithms
- **Code generation**: Generate deployment code snippets
- **Documentation**: Create descriptions for your models

**Note:** The LLM is an assistant tool. You can use all core features of CiRA Studio without it.

---

## Alternative: Disable LLM Features

If you don't want to use LLM features:
- Simply don't download the model file
- CiRA Studio will work normally
- LLM-dependent features will show a message that the model is not installed

---

**Model Storage Location**: `C:\Users\<YourUsername>\AppData\Local\CiRA FES\models\`

**Download Link**: https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF

**Support**: See main documentation or contact support if you need help

# Download Llama-3.2-3B Model

To enable LLM-powered feature selection, you need to download the Llama-3.2-3B model.

## Option 1: Manual Download (Recommended)

1. **Visit HuggingFace:**
   https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF

2. **Download the Q4_K_M quantized model** (~2.5 GB):
   https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf

3. **Save to models folder:**
   ```
   D:\CiRA FES\models\Llama-3.2-3B-Instruct-Q4_K_M.gguf
   ```

## Option 2: Use wget or curl

### Using PowerShell:
```powershell
cd "D:\CiRA FES\models"
Invoke-WebRequest -Uri "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf" -OutFile "Llama-3.2-3B-Instruct-Q4_K_M.gguf"
```

### Using wget (if installed):
```bash
cd "D:\CiRA FES\models"
wget https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf
```

## Option 3: Use huggingface-cli

```bash
pip install huggingface-hub
huggingface-cli download bartowski/Llama-3.2-3B-Instruct-GGUF Llama-3.2-3B-Instruct-Q4_K_M.gguf --local-dir "D:\CiRA FES\models" --local-dir-use-symlinks False
```

## Verify Installation

After downloading, verify the file:

```bash
cd "D:\CiRA FES"
python -c "from pathlib import Path; p = Path('models/Llama-3.2-3B-Instruct-Q4_K_M.gguf'); print(f'Model found: {p.exists()}, Size: {p.stat().st_size / 1024 / 1024:.1f} MB' if p.exists() else 'Model not found')"
```

Expected output: `Model found: True, Size: ~2500 MB`

## Model Details

- **Model:** Llama-3.2-3B-Instruct
- **Quantization:** Q4_K_M (4-bit quantization, medium quality)
- **Size:** ~2.5 GB
- **Context Length:** 2048 tokens
- **License:** Llama 3.2 Community License

## Using in Application

Once downloaded:

1. Open CiRA FutureEdge Studio
2. Go to **LLM Selection** stage
3. Click **Browse...** and select the model file
4. Click **Load Model**
5. Wait for loading (10-30 seconds)
6. Status should show: "✓ Model loaded successfully"

Now the LLM-powered feature selection will be available!

# Installation Guide

## Quick Start

### 1. Prerequisites

- **Python 3.8+** (Python 3.10 recommended)
- **Windows 10/11** (64-bit)
- **16 GB RAM** recommended (8 GB minimum)
- **10 GB free disk space**

### 2. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

**Note:** Some packages may require compilation. If you encounter errors:
- Install [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- Or use pre-built wheels from [Unofficial Windows Binaries](https://www.lfd.uci.edu/~gohlke/pythonlibs/)

### 3. Download LLM Model (Optional for Phase 1)

The LLM model is required for Phase 4 (feature selection). You can skip this for now:

```bash
# Create models directory
mkdir models

# Download Llama-3.2-3B-Instruct-Q4_K_M (~2.5 GB)
# Option 1: Using Python script (to be created)
python scripts/download_models.py

# Option 2: Manual download
# 1. Visit: https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF
# 2. Download: Llama-3.2-3B-Instruct-Q4_K_M.gguf
# 3. Place in: models/Llama-3.2-3B-Instruct-Q4_K_M.gguf
```

### 4. Run Application

```bash
python main.py
```

## Troubleshooting

### Issue: `ImportError: No module named 'customtkinter'`

**Solution:**
```bash
pip install customtkinter
```

### Issue: `llama-cpp-python` compilation fails

**Solution:**
```bash
# Install pre-built wheel
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

### Issue: Application window is blank

**Solution:**
- Update graphics drivers
- Try software rendering: Set environment variable `CUSTOMTKINTER_RENDER_MODE=software`

### Issue: High memory usage

**Solution:**
- Close other applications
- Reduce LLM model size (use TinyLlama instead of Llama-3.2)
- Increase Windows virtual memory

## Development Setup

For contributors and developers:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/

# Run linters
black .
flake8 .
mypy .
```

## Next Steps

1. Read [README.md](README.md) for usage instructions
2. Check [PROJECT_SPECIFICATION.md](PROJECT_SPECIFICATION.md) for technical details
3. Explore [docs/examples/](docs/examples/) for sample projects

## Support

If you encounter issues:
1. Check [GitHub Issues](https://github.com/your-org/CiRA-FutureEdge-Studio/issues)
2. Read [docs/user_guide.md](docs/user_guide.md)
3. Contact: support@cira-studio.com

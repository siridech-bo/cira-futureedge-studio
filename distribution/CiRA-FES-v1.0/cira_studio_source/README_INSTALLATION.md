# CiRA Studio - Installation Guide

CiRA Studio is distributed as Python source code for maximum reliability and compatibility.

## Prerequisites

- **Python 3.8 or higher** (Python 3.10 recommended)
- **Internet connection** (for first-time dependency installation)
- **Windows 10/11** (64-bit)

## Installation Steps

### 1. Install Python (if not already installed)

1. Download Python 3.10 from https://www.python.org/downloads/
2. Run the installer
3. **IMPORTANT**: Check "Add Python to PATH" during installation
4. Complete the installation

### 2. Install CiRA Studio Dependencies

Double-click `install.bat` and wait for installation to complete (5-10 minutes).

The script will:
- Check Python installation
- Install all required packages from `requirements.txt`
- Verify installation

If installation fails:
- Check your internet connection
- Try running as Administrator
- Or install manually: `pip install -r requirements.txt`

### 3. Run CiRA Studio

Double-click `run_cira_studio.bat`

CiRA Studio will launch and show the main interface.

## Troubleshooting

### "Python is not installed or not in PATH"

**Solution**: Install Python and make sure "Add Python to PATH" was checked during installation.

To verify: Open Command Prompt and type `python --version`

### "pip is not recognized"

**Solution**: Reinstall Python with "Add Python to PATH" checked.

### Installation takes too long / times out

**Solution**:
1. Check internet connection
2. Try installing in smaller batches:
   ```batch
   pip install customtkinter pandas numpy scipy
   pip install torch
   pip install scikit-learn
   pip install -r requirements.txt
   ```

### "Module not found" error when running

**Solution**: Run `install.bat` again to ensure all dependencies are installed.

### CiRA Studio window doesn't appear

**Solution**:
1. Check Task Manager - CiRA Studio process might be running in background
2. Look for error messages in the console window
3. Try running from command line to see errors:
   ```batch
   cd cira_studio_source
   python main.py
   ```

## What Gets Installed

The `install.bat` script installs these main packages:

**UI Framework**:
- customtkinter (modern UI library)
- pillow (image processing)

**Data Processing**:
- pandas, numpy, scipy
- sqlalchemy, psycopg2

**Machine Learning**:
- scikit-learn (classical ML)
- pyod (anomaly detection)
- imbalanced-learn (handling imbalanced data)

**Deep Learning**:
- torch (PyTorch for TimesNet)
- onnx (model export)

**Feature Engineering**:
- tsfresh (automated feature extraction)
- librosa (audio features - optional)
- pywavelets (wavelet transforms)

**Visualization**:
- matplotlib, plotly, seaborn

**LLM Support**:
- llama-cpp-python (local LLM)
- huggingface-hub

**File Formats**:
- h5py, pyarrow, openpyxl, cbor2

**Utilities**:
- loguru (logging)
- tqdm (progress bars)
- pyyaml, jinja2

Total size after installation: ~3-4 GB

## Updating Dependencies

If you need to update packages:

```batch
pip install --upgrade -r requirements.txt
```

## Uninstalling

To remove CiRA Studio:
1. Delete the `cira_studio_source` folder
2. (Optional) Uninstall Python packages:
   ```batch
   pip uninstall -r requirements.txt -y
   ```

## Source Code Structure

```
cira_studio_source/
├── main.py                 # Main entry point
├── ui/                     # User interface modules
├── core/                   # Core functionality
├── data_sources/           # Data loading and management
├── feature_extraction/     # Feature engineering
├── codegen/                # Code generation
├── llm/                    # LLM integration
├── anomaly_detection/      # Anomaly detection
├── models/                 # Saved models
├── logs/                   # Application logs
├── requirements.txt        # Python dependencies
├── install.bat             # Installation script
└── run_cira_studio.bat     # Launch script
```

## Support

For issues or questions:
- Email: support@cira-fes.com
- Documentation: See User Guide in `docs/` folder
- GitHub Issues: [your-repo-url]

---

**CiRA Studio v1.0** - Python Source Distribution

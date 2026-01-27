# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for CiRA FutureEdge Studio
This builds a standalone Windows executable with all dependencies bundled.
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import sys
import os

block_cipher = None

# Collect all required data files
datas = []

# CustomTkinter theme files
datas += collect_data_files('customtkinter')

# Torch/ONNX models and libraries
datas += collect_data_files('torch')
datas += collect_data_files('onnx')

# TSFresh feature definitions
datas += collect_data_files('tsfresh')

# Librosa audio data
datas += collect_data_files('librosa')

# Plotly templates
datas += collect_data_files('plotly')

# LLM libraries
datas += collect_data_files('llama_cpp')

# Include project-specific data (only if directories exist)
import os
if os.path.exists('models'):
    datas += [('models', 'models')]
if os.path.exists('templates'):
    datas += [('templates', 'templates')]
if os.path.exists('assets'):
    datas += [('assets', 'assets')]

# Include CiRA Studio Python modules (CRITICAL)
# These are not auto-detected because they're in the same directory as main.py
# Only include directories that exist
if os.path.exists('ui'):
    datas += [('ui', 'ui')]
if os.path.exists('core'):
    datas += [('core', 'core')]
if os.path.exists('data_sources'):
    datas += [('data_sources', 'data_sources')]
if os.path.exists('feature_extraction'):
    datas += [('feature_extraction', 'feature_extraction')]
if os.path.exists('codegen'):
    datas += [('codegen', 'codegen')]
if os.path.exists('llm'):
    datas += [('llm', 'llm')]
if os.path.exists('anomaly_detection'):
    datas += [('anomaly_detection', 'anomaly_detection')]

# Collect hidden imports (modules loaded dynamically)
hiddenimports = []

# Core dependencies
hiddenimports += collect_submodules('customtkinter')
hiddenimports += collect_submodules('sklearn')
hiddenimports += collect_submodules('scipy')
hiddenimports += collect_submodules('pandas')
hiddenimports += collect_submodules('numpy')

# Deep learning
hiddenimports += collect_submodules('torch')
hiddenimports += collect_submodules('onnx')
hiddenimports += ['einops']

# Feature engineering
hiddenimports += collect_submodules('tsfresh')
hiddenimports += ['pywavelets', 'pywt']

# Visualization
hiddenimports += collect_submodules('matplotlib')
hiddenimports += collect_submodules('plotly')
hiddenimports += collect_submodules('seaborn')
hiddenimports += ['kaleido']

# File formats
hiddenimports += ['cbor2', 'h5py', 'openpyxl', 'pyarrow']

# LLM support
hiddenimports += ['llama_cpp']

# Utilities
hiddenimports += ['loguru', 'tqdm', 'yaml', 'jinja2']

# Additional dependencies that may be imported dynamically
hiddenimports += ['tkinter', 'tkinter.ttk', 'tkinter.font']
hiddenimports += ['dotenv', 'python_dotenv']
hiddenimports += ['requests', 'urllib3']
hiddenimports += ['psycopg2']
hiddenimports += ['sqlalchemy']

# Windows-specific
if sys.platform == 'win32':
    hiddenimports += ['win32api', 'win32con', 'win32gui', 'pywintypes']

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude development/testing modules to reduce size
        'pytest',
        'pytest_cov',
        'pytest_mock',
        # Exclude Qt bindings (we use CustomTkinter which needs tkinter)
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'gi',  # GTK bindings
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='cira_studio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Hide console window for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/cira_icon.ico' if os.path.exists('assets/cira_icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='cira_studio',
)

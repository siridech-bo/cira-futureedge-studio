# CiRA FES v1.0 - Distribution Summary

## Package Contents

### Binaries
- **bin/pipeline_builder.exe** - Visual pipeline editor for Jetson deployment
- **bin/cira_studio/** - Dataset management and model training application
  - cira_studio.exe (main executable)
  - _internal/ (Python runtime and dependencies: PyTorch, scikit-learn, pandas, etc.)

### Runtime Source Code
- **cira-block-runtime/** - C++ runtime source code for Jetson deployment
  - Automatically compiled on Jetson during first "Setup Device"
  - Or downloaded as precompiled binary if available
  - Includes all block implementations (input/processing/output nodes)

### Documentation
- **README.md** - Main package overview and quick start
- **docs/QuickStart.md** - 5-minute getting started guide
- **docs/UserGuide.md** - Comprehensive user documentation (400+ lines)
- **docs/Troubleshooting.md** - Common issues and solutions
- **LICENSE.txt** - Apache 2.0 license with FREE tier terms

### Examples

#### StandardWave (Synthetic Signal Classification)
- **examples/StandardWave/pipeline.json** - Complete inference pipeline
- **examples/StandardWave/dataset/** - 1,710 windows (train/test split)
  - train/ - 15 CBOR files (1,324 windows)
  - test/ - 5 CBOR files (386 windows)
- **examples/StandardWave/model/timesnet_standardwave.onnx** - Pre-trained TimesNet model
- **Classes**: sawtooth, sine, square, triangular
- **Format**: CiRA CBOR

#### MotionClassification (Real Motion Data)
- **examples/MotionClassification/** - Edge Impulse CBOR dataset
  - training/ - Motion sensor data (idle, shake, etc.)
  - testing/ - Test split
  - info.labels - Class labels metadata
  - README.txt - Dataset description
- **Format**: Edge Impulse CBOR (signed format)

## Distribution Package Structure

```
CiRA-FES-v1.0/
├── bin/
│   ├── pipeline_builder.exe (~15 MB)
│   └── cira_studio/
│       ├── cira_studio.exe (~57 MB)
│       └── _internal/ (PyTorch, ML libraries, ~1.5 GB)
├── cira-block-runtime/
│   ├── src/ (C++ source code)
│   ├── include/ (headers)
│   ├── CMakeLists.txt (build configuration)
│   └── third_party/ (dependencies: IXWebSocket, nlohmann-json, etc.)
├── examples/
│   ├── StandardWave/
│   │   ├── pipeline.json
│   │   ├── dataset/
│   │   │   ├── train/ (15 CBOR files)
│   │   │   └── test/ (5 CBOR files)
│   │   └── model/
│   │       └── timesnet_standardwave.onnx (~2 MB)
│   └── MotionClassification/
│       ├── training/ (CBOR files)
│       ├── testing/ (CBOR files)
│       ├── info.labels
│       └── README.txt
├── docs/
│   ├── QuickStart.md
│   ├── UserGuide.md
│   └── Troubleshooting.md
├── LICENSE.txt
└── README.md
```

## Estimated Sizes
- **CiRA Studio**: ~1.6 GB (includes PyTorch, all ML dependencies)
- **Pipeline Builder**: ~15 MB
- **Runtime Source**: ~50 MB (C++ source + dependencies)
- **StandardWave Example**: ~50 MB (dataset + model)
- **MotionClassification Example**: ~10 MB
- **Documentation**: <1 MB
- **Total (uncompressed)**: ~1.75 GB
- **Total (ZIP compressed)**: ~650-850 MB (estimated)

## Distribution Files Created

1. **CiRA-FES-v1.0/** - Uncompressed distribution folder
2. **CiRA-FES-v1.0.zip** - Compressed archive for distribution

## Key Features Included

### v1.0 Highlights
- ✅ Execution rate configuration (1-1000 Hz)
- ✅ Optimized WebSocket broadcast performance (150× faster)
- ✅ String broadcast change detection
- ✅ Dynamic broadcast throttling during dataset recording
- ✅ Increased trial limits (100 trainings for FREE tier)
- ✅ Support for CiRA CBOR and Edge Impulse CBOR formats
- ✅ Complete StandardWave example (ready to deploy)
- ✅ Real MotionClassification dataset example

### Platform Support
- **Development**: Windows 10/11 (64-bit)
- **Deployment**: NVIDIA Jetson (Nano, Xavier, Orin)
- **Jetson Runtime**: Precompiled binaries via Pipeline Builder Setup Device

## License Terms

### FREE Tier (Included)
- 100 Deep Learning model trainings
- 100 LLM analysis operations
- All core features
- No time restrictions
- Personal and commercial use allowed

### Upgrade Path
- Contact: support@cira-fes.com
- PRO tier: Unlimited trainings, priority support

## Distribution Checklist

- [x] Build Pipeline Builder executable
- [x] Build CiRA Studio executable (PyInstaller)
- [x] Create documentation (Quick Start, User Guide, Troubleshooting)
- [x] Prepare StandardWave example (pipeline + dataset + model)
- [x] Include MotionClassification dataset
- [x] Create LICENSE.txt
- [x] Create main README.md
- [x] Create distribution folder structure
- [x] Copy all files to distribution package
- [x] Create ZIP archive
- [ ] Test on clean Windows machine (user to perform)
- [ ] Create GitHub v1.0.0 release (user to perform)

## Next Steps for Release

1. **Test the distribution**:
   - Extract ZIP on clean Windows machine
   - Launch pipeline_builder.exe
   - Open StandardWave example
   - Deploy to Jetson (if available)
   - Launch cira_studio.exe
   - Load StandardWave dataset

2. **Create GitHub Release**:
   - Tag: v1.0.0
   - Title: "CiRA FES v1.0 - Initial Release"
   - Upload: CiRA-FES-v1.0.zip
   - Release notes: See changelog in README.md

3. **Distribution Channels**:
   - GitHub Releases (primary)
   - Website download page
   - Email to beta customers
   - Optional: Windows installer (future)

## Support Information

- **Email**: support@cira-fes.com
- **GitHub**: [your-repo-url]
- **Documentation**: docs/ folder in package
- **Community**: [Discord/Forum links]

## Build Information

- **Build Date**: 2026-01-26
- **Git Commit**: [Check with: git log -1 --oneline]
- **PyInstaller Version**: 6.16.0
- **Python Version**: 3.10
- **Build Platform**: Windows 10/11

## Known Limitations (v1.0)

1. Single pipeline per project (multi-pipeline in v1.1)
2. No auto-reconnect after Jetson reboot
3. Large ONNX models (>100 MB) slow to upload first time
4. Windows Defender may flag .exe (add exception)

These will be addressed in future releases.

---

## Distribution Complete! 🎉

The CiRA FES v1.0 distribution package is ready for customer release.

**Package Location**: `D:\CiRA FES\distribution\CiRA-FES-v1.0.zip`

**Recommended Next Step**: Test the distribution on a clean Windows machine to ensure everything works as expected, then create the GitHub v1.0.0 release.

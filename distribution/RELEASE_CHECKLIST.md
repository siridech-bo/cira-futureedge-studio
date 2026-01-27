# CiRA FES v1.0 - Release Checklist

## Pre-Release Validation (To Be Done By You)

### 1. Test Distribution Package

- [ ] **Extract ZIP on clean Windows machine**
  - Extract `CiRA-FES-v1.0.zip` to a test directory
  - Verify all folders/files are present

- [ ] **Test Pipeline Builder**
  - Launch `bin\pipeline_builder.exe`
  - Should start without errors
  - Open `examples\StandardWave\pipeline.json`
  - Verify pipeline loads correctly
  - Check all blocks are visible and configured

- [ ] **Test Jetson Deployment** (if Jetson available)
  - In Pipeline Builder, go to Deploy → Setup Device
  - Enter Jetson credentials
  - Click Setup Device (first-time setup, takes 2-3 minutes)
  - Click Deploy to Device
  - Verify runtime starts on Jetson
  - Open Monitor Dashboard
  - Check real-time predictions are working

- [ ] **Test CiRA Studio**
  - Launch `bin\cira_studio\cira_studio.exe`
  - Should start without errors
  - Go to Data Sources tab
  - Click Add Data Source → CiRA CBOR
  - Select `examples\StandardWave\dataset`
  - Verify dataset loads successfully
  - Check train/test split is recognized
  - Verify 4 classes shown (sawtooth, sine, square, triangular)

- [ ] **Test License System**
  - In CiRA Studio, go to Settings → License Info
  - Verify shows: "DL Training: 0/100" and "LLM Analysis: 0/100"
  - Try starting a training (can cancel after it starts)
  - Verify count increments to "1/100"

### 2. Documentation Review

- [ ] **Read README.md**
  - Verify all links work (if any)
  - Check formatting is correct
  - Ensure instructions are clear

- [ ] **Read QuickStart.md**
  - Follow the 5-minute tutorial yourself
  - Verify steps are accurate
  - Check if any steps are missing

- [ ] **Scan UserGuide.md**
  - Verify table of contents
  - Check major sections are present
  - Spot-check a few sections for accuracy

- [ ] **Check Troubleshooting.md**
  - Verify common issues are listed
  - Check solutions are clear

### 3. Package Integrity

- [ ] **Verify file sizes are reasonable**
  ```bash
  # Check ZIP size (should be 600-800 MB)
  ls -lh CiRA-FES-v1.0.zip

  # Check uncompressed size (should be ~1.7 GB)
  du -sh CiRA-FES-v1.0/
  ```

- [ ] **Check all critical files exist**
  - bin/pipeline_builder.exe
  - bin/cira_studio/cira_studio.exe
  - bin/cira_studio/_internal/ (should have many DLLs)
  - examples/StandardWave/pipeline.json
  - examples/StandardWave/dataset/train/ (15 files)
  - examples/StandardWave/dataset/test/ (5 files)
  - examples/StandardWave/model/timesnet_standardwave.onnx
  - examples/MotionClassification/training/ (many CBOR files)
  - docs/QuickStart.md
  - docs/UserGuide.md
  - docs/Troubleshooting.md
  - LICENSE.txt
  - README.md

## GitHub Release Creation

### 1. Prepare Release Notes

Create a release description based on this template:

```markdown
# CiRA FutureEdge Studio v1.0 - Initial Release

Build. Train. Deploy. Edge AI pipelines on NVIDIA Jetson - no coding required.

## What's Included

- **Pipeline Builder**: Visual drag-and-drop pipeline editor
- **CiRA Studio**: Dataset management and TimesNet model training
- **Jetson Runtime**: High-performance C++ execution (100-1000+ Hz)
- **Examples**: StandardWave (synthetic signals) + MotionClassification (real data)
- **FREE Tier**: 100 DL trainings + 100 LLM analyses included

## Key Features

- Execution rate configuration (1-1000 Hz)
- Optimized WebSocket performance (150× faster than v0.9)
- Dataset recording with automatic CBOR format
- TimesNet deep learning for time-series classification
- One-click deployment to Jetson via SSH
- Real-time monitoring dashboard

## Quick Start

1. Extract `CiRA-FES-v1.0.zip`
2. Launch `bin\pipeline_builder.exe`
3. Open `examples\StandardWave\pipeline.json`
4. Deploy to Jetson (Deploy → Setup Device)
5. See [QuickStart.md](docs/QuickStart.md) for details

## System Requirements

**Development**: Windows 10/11 (64-bit), 8GB RAM
**Deployment**: NVIDIA Jetson (Nano/Xavier/Orin), JetPack 4.6+

## Documentation

- [Quick Start Guide](docs/QuickStart.md) - Get started in 5 minutes
- [User Guide](docs/UserGuide.md) - Comprehensive documentation
- [Troubleshooting](docs/Troubleshooting.md) - Common issues and solutions

## Support

- Email: support@cira-fes.com
- GitHub Issues: Report bugs here
- Documentation: See `docs/` folder in package

## License

Apache 2.0 with FREE tier (100 trainings included)

## Changelog

### v1.0.0 (2026-01-26)
- Initial public release
- Pipeline Builder with visual editor
- CiRA Studio with TimesNet training
- Jetson deployment via SSH
- StandardWave and MotionClassification examples
- FREE tier: 100 trainings included
- Comprehensive documentation
```

### 2. Create GitHub Release

- [ ] **Tag the release**
  ```bash
  git tag -a v1.0.0 -m "CiRA FES v1.0 - Initial Release"
  git push origin v1.0.0
  ```

- [ ] **Create release on GitHub**
  - Go to repository → Releases → Draft a new release
  - Tag: `v1.0.0`
  - Title: `CiRA FES v1.0 - Initial Release`
  - Description: Paste the release notes from above
  - Attach file: `CiRA-FES-v1.0.zip`
  - Check "Set as latest release"
  - Click "Publish release"

### 3. Update Repository README

- [ ] **Add release badge** (optional)
  ```markdown
  ![Latest Release](https://img.shields.io/github/v/release/your-org/cira-fes)
  ```

- [ ] **Add download link**
  ```markdown
  ## Download

  **Latest Release**: [CiRA FES v1.0](https://github.com/your-org/cira-fes/releases/tag/v1.0.0)
  ```

## Post-Release Tasks

### 1. Customer Communication

- [ ] **Email beta customers**
  - Announce v1.0 release
  - Include download link
  - Highlight key features
  - Link to Quick Start Guide

- [ ] **Update website** (if applicable)
  - Add download page
  - Update version number
  - Link to documentation

- [ ] **Social media announcement** (if applicable)
  - LinkedIn, Twitter, etc.
  - Share key features and download link

### 2. Support Setup

- [ ] **Monitor GitHub Issues**
  - Be ready to respond to bug reports
  - Track feature requests

- [ ] **Prepare FAQ** (based on initial feedback)
  - Common installation issues
  - Deployment questions
  - License questions

### 3. Collect Feedback

- [ ] **Create feedback form** (optional)
  - Google Forms or similar
  - Ask about user experience
  - Feature requests
  - Pain points

- [ ] **Track usage metrics** (if telemetry enabled)
  - Number of downloads
  - License activations
  - Common workflows

## Rollback Plan (If Critical Issues Found)

If critical bugs are discovered post-release:

1. **Create hotfix branch**
   ```bash
   git checkout -b hotfix/v1.0.1
   ```

2. **Fix the issue**
   - Make minimal changes
   - Test thoroughly

3. **Release v1.0.1**
   - Follow release checklist again
   - Mark as "critical update" in release notes
   - Notify all users who downloaded v1.0.0

## Version 1.1 Planning

Start collecting requirements for v1.1:

- [ ] Multi-pipeline deployment
- [ ] Cloud synchronization
- [ ] Additional ML models (LSTM, etc.)
- [ ] Mobile monitoring app
- [ ] (Add based on user feedback)

---

## Sign-Off

Distribution package created and ready for release!

**Package**: `D:\CiRA FES\distribution\CiRA-FES-v1.0.zip`
**Date**: 2026-01-26
**Git Commit**: [Run: git log -1 --oneline]

**Next Step**: Test the distribution package on a clean Windows machine, then create the GitHub release.

---

Good luck with the v1.0 release! 🚀

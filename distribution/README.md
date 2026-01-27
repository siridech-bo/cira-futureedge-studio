# CiRA FutureEdge Studio v1.0

**Build. Train. Deploy.**

CiRA FES is a complete platform for creating edge AI applications on NVIDIA Jetson devices - no coding required.

![CiRA FES Workflow](https://via.placeholder.com/800x200?text=Pipeline+Builder+%E2%86%92+Train+Models+%E2%86%92+Deploy+to+Jetson)

## What's Included

- **Pipeline Builder**: Visual drag-and-drop pipeline editor for data processing
- **CiRA Studio**: Dataset management and model training (ML/DL/AutoML)
- **Jetson Runtime**: High-performance C++ execution engine (100-1000+ Hz)
- **Example Projects**: StandardWave (signal classification) + MotionClassification (real data)

## Quick Start (5 Minutes)

1. **Extract** the archive
2. **Launch** `bin\pipeline_builder.exe`
3. **Open** `examples\StandardWave\pipeline.json`
4. **Deploy** to your Jetson (Deploy → Setup Device)
5. **Monitor** real-time classification (Deploy → Monitor Dashboard)

**See [Quick Start Guide](docs/QuickStart.md) for detailed instructions.**

## System Requirements

### Development Machine (Windows)
- Windows 10/11 (64-bit)
- 8GB RAM (16GB recommended)
- 5GB free disk space

### Jetson Target Device
- Jetson Nano, Xavier, or Orin
- JetPack 4.6+ or 5.0+
- SSH enabled, network access

## Features

###  Pipeline Builder
- Visual block-based pipeline editor
- 20+ built-in blocks (input/processing/output)
- One-click deployment to Jetson
- Real-time monitoring dashboard

###  CiRA Studio
- Dataset management (CiRA CBOR, Edge Impulse CBOR, CSV)
- TimesNet deep learning for time-series classification
- Classical ML (Random Forest, XGBoost, SVM)
- Automated feature engineering with TSFresh
- ONNX export for Jetson deployment

###  Edge Deployment
- SSH-based deployment workflow
- Precompiled binaries for fast Jetson setup
- 100-1000+ Hz execution rates
- Web dashboard for monitoring

## Example Projects

### StandardWave (Synthetic Signals)
- **What**: 4-class signal classification (sawtooth/sine/square/triangular)
- **Format**: CiRA CBOR
- **Dataset**: 1,710 windows (train/test split)
- **Model**: Pre-trained TimesNet (ready to deploy)
- **Use Case**: Test deployment workflow, learn the system

### MotionClassification (Real Motion Data)
- **What**: Continuous motion recognition (idle/shake/etc.)
- **Format**: Edge Impulse CBOR
- **Dataset**: Real IMU sensor data
- **Use Case**: Train your own model, real-world example

## Typical Workflow

1. **Design** pipeline in Pipeline Builder
   - Drag blocks: Input → Processing → ML Model → Output
   - Configure parameters

2. **Record** dataset with Data Recorder block
   - Deploy to Jetson
   - Record 100+ windows per class
   - Automatic CBOR format

3. **Train** model in CiRA Studio
   - Load dataset (auto-detects format)
   - Configure TimesNet model
   - Train (5-15 minutes)
   - Export ONNX model

4. **Deploy** model to Jetson
   - Add TimesNet block to pipeline
   - Point to trained model
   - One-click deployment
   - Monitor real-time predictions!

## Performance

**Dataset Recording**:
- 100 windows in ~5 minutes (at 100 Hz execution rate)

**Model Training** (TimesNet):
- Small dataset (<1000 windows): 5-10 minutes
- Medium dataset (1000-5000): 15-30 minutes

**Jetson Inference**:
- Jetson Nano: ~10ms per window
- Jetson Xavier: ~3-5ms per window
- TensorRT optimized: 1-3ms

## Documentation

- **[Quick Start Guide](docs/QuickStart.md)** - Get started in 5 minutes
- **[User Guide](docs/UserGuide.md)** - Complete documentation
- **[Troubleshooting](docs/Troubleshooting.md)** - Common issues and solutions

## License

**FREE Tier** (included):
- 100 Deep Learning model trainings
- 100 LLM analysis operations
- All core features
- No time restrictions

**PRO Tier** (upgrade):
- Unlimited trainings and LLM usage
- Priority support
- Advanced features (coming soon)
- Contact: support@cira-fes.com

## Support

- **Email**: support@cira-fes.com
- **GitHub Issues**: [your-github-repo]
- **Documentation**: `docs/` folder
- **Community**: [Discord/Forum link]

## What's New in v1.0

- Execution rate configuration in deployment settings (1-1000 Hz)
- Optimized WebSocket broadcast performance (150× faster)
- String broadcast change detection (eliminates unnecessary updates)
- Dynamic broadcast throttling during dataset recording
- Increased trial limits (10 → 100 for FREE tier)
- Support for both CiRA CBOR and Edge Impulse CBOR formats
- Comprehensive documentation and examples

## Changelog

### v1.0.0 (2026-01-26)
- Initial release
- Pipeline Builder with visual editor
- CiRA Studio with TimesNet training
- Jetson deployment via SSH
- StandardWave and MotionClassification examples
- FREE tier: 100 trainings included

## Roadmap

- **v1.1**: Cloud synchronization, multi-device management
- **v1.2**: Additional ML models (LSTM, Transformer variants)
- **v1.3**: Mobile app for monitoring
- **v2.0**: Multi-pipeline deployment, advanced scheduling

## Credits

**CiRA Team** - Building the future of edge AI

Special thanks to:
- NVIDIA Jetson community
- PyTorch and ONNX teams
- Open source contributors

---

## Getting Started

**Ready to build your first edge AI pipeline?**

1. Launch `bin\pipeline_builder.exe`
2. Open `examples\StandardWave\pipeline.json`
3. Follow the [Quick Start Guide](docs/QuickStart.md)

**Questions?** See [Troubleshooting.md](docs/Troubleshooting.md) or contact support.

---

CiRA FES v1.0 | Copyright © 2026 CiRA Team | Licensed under Apache 2.0

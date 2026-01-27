# CiRA FutureEdge Studio - Quick Start Guide

Welcome to CiRA FES v1.0! This guide will help you get started in minutes.

## System Requirements

### Windows Development Machine
- **OS**: Windows 10/11 (64-bit)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 5GB free space
- **Network**: For Jetson deployment via SSH

### Jetson Target Device
- **Supported**: Jetson Nano, Xavier, Orin
- **JetPack**: 4.6+ or 5.0+
- **Network**: SSH enabled, same network as development machine

## Installation

### 1. Extract CiRA FES Package

```bash
# Extract the downloaded archive
unzip CiRA-FES-v1.0.zip
cd CiRA-FES-v1.0
```

### 2. Launch Applications

**Pipeline Builder** (for creating and deploying pipelines):
```
bin\pipeline_builder.exe
```

**CiRA Studio** (for dataset management and model training):
```
bin\cira_studio.exe
```

## Your First Pipeline (5 minutes)

Let's deploy the StandardWave example to see real-time signal classification on your Jetson.

### Step 1: Open Pipeline Builder

1. Launch `bin\pipeline_builder.exe`
2. Click **File → Open Pipeline**
3. Navigate to `examples\StandardWave\pipeline.json`
4. You'll see a pipeline: Signal Generator → Channel Merge → Sliding Window → TimesNet Model → Web LED

### Step 2: Configure Jetson Connection

1. Click **Deploy → Setup Device**
2. Enter your Jetson details:
   - **IP Address**: `192.168.1.200` (your Jetson's IP)
   - **Username**: `user` (default: nvidia or jetson)
   - **Password**: Your Jetson password
   - **Project Name**: `standardwave_demo`
   - **Execution Rate**: `100` Hz (default)
3. Click **Save Configuration**
4. Click **Setup Device** to install runtime on Jetson

**First-time setup takes 2-3 minutes** (installs dependencies, compiles runtime)

### Step 3: Deploy and Run

1. Click **Deploy → Deploy to Device**
2. Wait for deployment to complete (~30 seconds)
3. The pipeline automatically starts running on Jetson
4. Click **Deploy → Monitor Dashboard** to view real-time results

### Step 4: View Results

The Web Dashboard shows:
- **Live signal visualization** (3-channel waveforms)
- **Real-time predictions** (sawtooth/sine/square/triangular)
- **Confidence scores** (prediction certainty)
- **Execution rate** (should show ~100 Hz)

**Try it**: In Pipeline Builder, select the **Synthetic Signal Generator** node and click the `next_class` button to change the signal type. Watch the TimesNet model classify it in real-time!

## Next Steps

### Train Your Own Model

1. **Record custom dataset**:
   - In Pipeline Builder, add **Data Recorder** block
   - Record 100+ windows per class
   - Dataset saved in CBOR format

2. **Train TimesNet model**:
   - Launch **CiRA Studio**
   - Go to **Data Sources** tab
   - Click **Add Data Source → CiRA CBOR**
   - Select your recorded dataset folder
   - Go to **Deep Learning** tab
   - Click **TimesNet Model**
   - Configure and train (takes 5-15 minutes)
   - Export ONNX model

3. **Deploy your model**:
   - In Pipeline Builder, add **TimesNet Model** block
   - Set `model_path` to your exported .onnx file
   - Deploy to Jetson
   - Test real-time inference!

### Explore Examples

**StandardWave** (`examples/StandardWave/`):
- Synthetic signal classification (4 classes)
- Shows complete workflow: Pipeline + Dataset + Trained Model
- CiRA CBOR format

**MotionClassification** (`examples/MotionClassification/`):
- Real motion sensor data (idle/shake/etc.)
- Edge Impulse CBOR format
- Import into CiRA Studio for training

## Common Issues

**Can't connect to Jetson**:
- Verify Jetson IP with `ping <jetson-ip>`
- Ensure SSH is enabled: `sudo systemctl status ssh`
- Check firewall settings

**Deployment fails**:
- Ensure Jetson has sudo privileges
- Check network connection is stable
- Verify `/home/<user>/cira_projects/` directory permissions

**Slow execution rate**:
- Check Jetson power mode: `sudo nvpmodel -q`
- Set max performance: `sudo nvpmodel -m 0`
- Increase execution rate in deployment settings

**License activation**:
- FREE tier allows 100 DL trainings and 100 LLM analyses
- No time limit on FREE tier
- Upgrade to PRO for unlimited usage

## Support

- **Documentation**: See `docs/UserGuide.md` for detailed information
- **Troubleshooting**: See `docs/Troubleshooting.md` for common issues
- **GitHub Issues**: Report bugs at [your-repo-url]
- **Email**: support@cira-fes.com

## License

CiRA FES v1.0 - FREE Tier
- 100 Deep Learning trainings
- 100 LLM analyses
- All core features included
- No time restrictions

Upgrade to PRO for unlimited usage and priority support.

---

**Congratulations!** You're now ready to build edge AI pipelines with CiRA FES.

Next: Read the [User Guide](UserGuide.md) for comprehensive documentation.

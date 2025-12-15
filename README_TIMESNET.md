# TimesNet Deep Learning Integration - Quick Start Guide

**Status:** ✅ Production Ready | **Version:** 1.0.0 | **Date:** 2025-12-14

---

## What's New?

CiRA FutureEdge Studio now supports **Deep Learning** for time series classification alongside traditional Machine Learning!

### Key Features
- 🧠 **TimesNet** - State-of-the-art temporal pattern recognition
- 🖥️ **GPU Auto-Detection** - Automatically uses NVIDIA GPU when available
- ⚡ **ONNX Export** - Ready for Jetson deployment with TensorRT
- 🎯 **Dual-Pipeline** - Choose ML or DL based on your needs
- 🔒 **Mode Locking** - Prevents accidental pipeline changes mid-project

---

## When to Use Deep Learning vs Traditional ML?

### Use Deep Learning (TimesNet) When:
✅ You have complex temporal patterns in your data
✅ Dataset has periodic or seasonal behavior
✅ You have large datasets (>5,000 samples)
✅ Maximum accuracy is critical
✅ GPU is available for faster training

### Use Traditional ML (sklearn/PyOD) When:
✅ Simple statistical patterns are sufficient
✅ Small datasets (<1,000 samples)
✅ Fast training time is essential
✅ Feature engineering is well-understood
✅ CPU-only environment

---

## Installation

### 1. Install Deep Learning Dependencies
```bash
pip install torch>=2.0.0 einops>=0.7.0 onnx>=1.14.0
```

### 2. Verify Installation
```bash
python -c "from core.deep_models.timesnet import TimesNet; print('✓ TimesNet ready')"
```

---

## Quick Start - Creating a Deep Learning Project

### Step 1: Create Project
```
File → New Project → Enter name
```

### Step 2: Select Pipeline Mode
```
Data Sources → Pipeline Mode → "Deep Learning"
⚠️ This choice will be locked after windowing!
```

### Step 3: Load Data
```
Browse → Select CSV/JSON file
Load Data
```

### Step 4: Create Windows
```
Configure windowing (e.g., size=100, overlap=0%)
Create Windows
🔒 Mode is now locked
```

### Step 5: Navigate to Training
```
Click "Training" in sidebar
(Feature tabs are grayed out - this is expected!)
```

### Step 6: Configure TimesNet
**Algorithm Tab:**
- Model Complexity:
  - **Minimal**: ~50K params, fast CPU training
  - **Efficient**: ~200K params, balanced (recommended)
  - **Comprehensive**: ~800K params, maximum accuracy

**Training Tab:**
- Epochs: 50 (10-200 range)
- Batch Size: 32 (8/16/32/64)
- Learning Rate: 0.001 (0.0001-0.01)

### Step 7: Start Training
```
Click "Start Training"
🖥️ Watch for: "Training Device: GPU: NVIDIA GeForce..." or "CPU (N threads)"
```

### Step 8: Monitor Progress
```
Training log shows:
- Device detected
- Epoch-by-epoch progress
- Validation accuracy
- Early stopping (if triggered)
```

### Step 9: View Results
**Evaluation Tab:**
- ✓ Device used
- ✓ Model parameters
- ✓ Accuracy, Precision, Recall, F1
- ✓ Per-class metrics
- ✓ Confusion matrix
- ✓ ONNX model path

### Step 10: Deploy to Jetson (Optional)
```bash
# On Jetson device
trtexec --onnx=timesnet_model.onnx \
        --saveEngine=timesnet_model.trt \
        --fp16
```

---

## Training Time Estimates

| Dataset Size | GPU (RTX 3060) | CPU (i7) |
|--------------|----------------|----------|
| 1,000 windows | 30-60 seconds | 5-10 minutes |
| 5,000 windows | 2-3 minutes | 30-60 minutes |
| 10,000 windows | 5-10 minutes | 1-2 hours |

**💡 Tip:** Use GPU for >5,000 windows, CPU is fine for smaller datasets

---

## Model Complexity Guide

| Complexity | Parameters | Best For |
|------------|-----------|----------|
| **Minimal** | ~50,000 | CPU training, quick experiments |
| **Efficient** | ~200,000 | 🌟 Recommended default (balanced) |
| **Comprehensive** | ~800,000 | Maximum accuracy, GPU required |

---

## Architecture Comparison

### Traditional ML Pipeline
```
Data → Windows → Feature Extraction → Feature Filtering →
LLM Selection → sklearn/PyOD Training → C++ Code → Deployment
```

### Deep Learning Pipeline
```
Data → Windows → TimesNet Training → ONNX Export →
TensorRT Conversion → Jetson Deployment
```

**Key Difference:** DL learns features automatically, ML requires manual feature engineering

---

## Troubleshooting

### GPU Not Detected
**Problem:** Shows "CPU" but you have NVIDIA GPU
**Check:**
```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
```
**Fix:** Install PyTorch with CUDA support:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

### Training Too Slow on CPU
**Problem:** Training takes hours
**Solutions:**
1. Reduce dataset size for testing
2. Use "Minimal" complexity
3. Reduce batch size to 8 or 16
4. Use GPU instead (Google Colab free GPU option)

### Out of Memory on GPU
**Problem:** CUDA out of memory error
**Solutions:**
1. Reduce batch size: 32 → 16 → 8
2. Use "Minimal" or "Efficient" complexity
3. Reduce window size
4. Close other GPU applications

### Low Accuracy (<70%)
**Problem:** Model not learning well
**Solutions:**
1. Increase epochs: 50 → 100 → 200
2. Use "Comprehensive" complexity
3. Verify data labels are correct
4. Ensure sufficient data per class (>100 samples)
5. Try different learning rate: 0.0001 or 0.01

### ONNX Export Failed
**Problem:** No ONNX file generated
**Check:**
```bash
pip show torch onnx
```
**Fix:**
```bash
pip install --upgrade torch onnx
```

---

## Files and Locations

### After Training, You'll Find:
```
your_project/
├── models/
│   ├── timesnet_model.pth          # PyTorch checkpoint
│   ├── timesnet_encoder.pkl        # Label encoder
│   ├── timesnet_model.onnx         # 🎯 ONNX for Jetson
│   └── timesnet_results.json       # Metrics
```

---

## Deployment Workflow

### Development (Your PC)
1. Train TimesNet model (GPU or CPU)
2. Model auto-exports to ONNX
3. Verify accuracy in Evaluation tab
4. Copy ONNX file to Jetson

### Edge Deployment (Jetson)
1. Convert ONNX → TensorRT
   ```bash
   trtexec --onnx=model.onnx --saveEngine=model.trt --fp16
   ```
2. Load TensorRT engine in C++ application
3. Real-time inference (5-50ms per window)
4. Edge decisions without cloud connectivity

---

## Jetson Performance Estimates

| Jetson Model | Inference Time | Use Case |
|--------------|----------------|----------|
| Nano | 20-50 ms | Standard edge applications |
| Xavier NX | 10-20 ms | Real-time capable |
| Orin Nano | 5-15 ms | High-performance edge |
| Orin AGX | 3-10 ms | Maximum throughput |

---

## FAQ

**Q: Can I switch between ML and DL for the same project?**
A: No, the mode is locked after windowing to ensure data consistency. Create separate projects for ML and DL.

**Q: Do I need a GPU?**
A: No, CPU works fine for small-to-medium datasets (<5,000 windows). GPU speeds up training significantly for larger datasets.

**Q: What's the minimum dataset size?**
A: Aim for at least 500-1,000 windows total, with 100+ samples per class for good results.

**Q: Can I train on my PC and deploy on Jetson?**
A: Yes! This is the recommended workflow. Train anywhere, deploy the ONNX model on Jetson with TensorRT.

**Q: Why are Feature Extraction tabs grayed out?**
A: Deep learning learns features automatically. Feature engineering tabs are only for Traditional ML mode.

**Q: How do I know which mode to use?**
A: Start with Traditional ML for quick prototyping (<1,000 samples). Switch to Deep Learning for complex patterns and larger datasets (>5,000 samples).

---

## Additional Documentation

- **Implementation Details:** [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)
- **Progress Tracking:** [TIMESNET_INTEGRATION_PROGRESS.md](TIMESNET_INTEGRATION_PROGRESS.md)
- **Verification Report:** [FINAL_VERIFICATION_REPORT.md](FINAL_VERIFICATION_REPORT.md)

---

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section above
2. Review detailed documentation in IMPLEMENTATION_COMPLETE.md
3. Verify dependencies are installed correctly

---

**Version:** 1.0.0
**Last Updated:** 2025-12-14
**Status:** ✅ Production Ready

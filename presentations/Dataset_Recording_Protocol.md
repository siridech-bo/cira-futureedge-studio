---
marp: true
theme: default
paginate: true
---

# Dataset Recording Protocol
## TimesNet Training Data Collection

CiRA Pipeline Builder - Windowed CBOR Format

---

## Overview

**Goal**: Record high-quality multi-channel time series data for TimesNet model training

**Target Dataset**:
- 4 waveform classes: sine, sawtooth, square, triangular
- 100+ windows per class (training)
- 50+ windows per class (test) - optional
- Window size: 300 samples × 3 channels = 900 values

**Time Required**: ~30 minutes total

---

## Configuration - Data Recorder

**Before Recording - Configure these settings:**

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `max_samples` | **100** | Number of windows per file |
| `output_format` | **cbor** | Binary format for CiRA Studio |
| `output_dir` | `/home/user/cira_datasets/StandardWave_Final/train` | Save location |
| `window_size` | 300 | Samples per window (default) |
| `num_channels` | 3 | Multi-channel data (default) |

**Important**: `max_samples` = windows, not individual samples!

---

## Configuration - Signal Generator

**Configure these settings:**

| Parameter | Value | Notes |
|-----------|-------|-------|
| `sample_rate` | **100.0** | 100 Hz sampling rate |
| `num_channels` | **3** | Three phase-shifted channels |
| `amplitude` | **1.0** | Signal amplitude |
| `frequency` | **1.0** | 1 Hz waveform |
| `signal_type` | **Change for each class** | See next slide |

---

## Signal Types - Class Mapping

| Signal Type | Class ID | Class Name |
|-------------|----------|------------|
| `sine` | 1 | Sine wave |
| `sawtooth` | 0 | Sawtooth wave |
| `square` | 2 | Square wave |
| `triangular` | 3 | Triangular wave |

**You will change `signal_type` for each recording**

---

## Recording Procedure - Step by Step

### **For EACH waveform (4 total):**

1. **Configure Signal Type**
   - Open Pipeline Builder
   - Select Synthetic Signal Generator node
   - Change `signal_type` to: sine, sawtooth, square, or triangular
   - Click "Save Changes"
   - Click "Deploy"

---

## Recording Procedure (continued)

2. **Record Training Data**
   - Open dashboard: `http://192.168.1.200:8083`
   - Click **"Start Recording"** button
   - **Wait 5 minutes** (auto-stops after 100 windows)
   - Download file from "Saved Datasets"
   - Move to: `D:\CiRA FES\Dataset\StandardWave_Final\train\`

3. **Record Test Data** (Optional)
   - Change `output_dir` to `.../test`
   - Change `max_samples` to 50
   - Record for 2.5 minutes
   - Download and move to test folder

---

## Time Calculation

**Per Window**: 300 samples ÷ 100 Hz = 3 seconds

**Per Recording**:
- 100 windows × 3 seconds = **5 minutes**
- 50 windows × 3 seconds = **2.5 minutes**

**Total Time**:
- Training only (4 classes × 5 min) = **20 minutes**
- Training + Test (4 × 7.5 min) = **30 minutes**

**Do NOT stop recording manually - let it auto-complete!**

---

## Expected File Structure

```
D:\CiRA FES\Dataset\StandardWave_Final\
├── train\
│   ├── sine.1.cbor.*.cbor          (100 windows)
│   ├── sawtooth.1.cbor.*.cbor      (100 windows)
│   ├── square.1.cbor.*.cbor        (100 windows)
│   └── triangular.1.cbor.*.cbor    (100 windows)
└── test\
    ├── sine.1.cbor.*.cbor          (50 windows)
    ├── sawtooth.1.cbor.*.cbor      (50 windows)
    ├── square.1.cbor.*.cbor        (50 windows)
    └── triangular.1.cbor.*.cbor    (50 windows)
```

**Total**: 400 train windows + 200 test windows = 600 windows

---

## Data Format - CBOR Structure

**Each file contains**:
```json
{
  "samples": [
    {
      "class_id": 1,
      "class_name": "sine",
      "timestamp": 1769267409421,
      "data": [900 values in channel-by-channel layout]
    },
    ...
  ]
}
```

**Data layout**: `[ch0_s0...ch0_s299, ch1_s0...ch1_s299, ch2_s0...ch2_s299]`

---

## Verification - Before Training

**Run verification script**:

```bash
cd "D:\CiRA FES"
python verify_complete_dataset.py
```

**Expected output**:
- ✅ 4 classes found
- ✅ 100+ windows per class
- ✅ All data arrays = 900 values
- ✅ All class_ids correct (0,1,2,3)
- ✅ Multi-channel phase offsets working

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| No file created | Recording < 3 seconds | Wait minimum 3 sec for 1 window |
| Small file size | Stopped too early | Let auto-stop after max_samples |
| Wrong class_id | Wrong signal_type | Check generator config |
| Data length ≠ 900 | Wrong window_size | Should be 300 default |
| Training fails | Too few windows | Need 50+ per class minimum |

---

## Best Practices

✅ **DO**:
- Wait for auto-stop (full 5 minutes)
- Verify files after each recording
- Use consistent settings across all recordings
- Record in quiet environment (if using real sensors)

❌ **DON'T**:
- Stop recording manually
- Change settings mid-recording
- Record multiple classes in one file
- Use less than 50 windows per class

---

## Recording Checklist

**Before Starting**:
- [ ] Pipeline Builder configured correctly
- [ ] Data Recorder: max_samples=100, output_format=cbor
- [ ] Signal Generator: sample_rate=100, num_channels=3
- [ ] Output directories created

**For Each Waveform**:
- [ ] Change signal_type
- [ ] Deploy to Jetson
- [ ] Start recording
- [ ] Wait 5 minutes (auto-stop)
- [ ] Download file
- [ ] Verify file (900 values, correct class_id)

---

## After Recording - Next Steps

1. **Verify Dataset**
   ```bash
   python verify_complete_dataset.py
   ```

2. **Load in CiRA Studio**
   - Open new project
   - Load from StandardWave_Final folder
   - Preview data (should show 3-channel waveforms)

3. **Train TimesNet Model**
   - Go to Training tab
   - Configure: 50 epochs, batch_size=32
   - Expected accuracy: >90% with good data

---

## Quality Metrics

**Good Dataset Indicators**:
- Train accuracy: 90-100%
- Test accuracy: 80-95%
- All classes F1 score: >0.8
- No class with F1 = 0.0

**If metrics are low**:
- Record more windows (200+ per class)
- Check data quality (verify waveforms look correct)
- Increase training epochs
- Try different model complexity

---

## Summary

**Key Points**:
1. **100 windows minimum** per class for training
2. **5 minutes** per recording (be patient!)
3. **Verify after each file** (class_id, data length)
4. **Channel-by-channel format** (900 values per window)
5. **4 classes total** (sine, sawtooth, square, triangular)

**Success = Proper configuration + Patience + Verification**

---

# Questions?

**Common Questions**:

**Q: Can I stop recording early?**
A: No - you'll get fewer windows and training will fail

**Q: How many windows do I really need?**
A: Minimum 50, recommended 100-200 per class

**Q: What if I recorded with wrong settings?**
A: Delete and re-record - bad data = bad model

**Q: Can I record multiple files instead of one big file?**
A: Yes, but ensure total windows per class ≥ 100

---

# Thank You

**Ready to Record High-Quality Training Data!**

🤖 Generated with Claude Code


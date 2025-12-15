# TimesNet - Quick Testing Checklist

**⏱️ Time:** 15-20 minutes | **For:** Rapid verification testing

---

## 🚀 Quick Start

### Pre-Test (2 min)
```bash
# 1. Verify dependencies
python -c "import torch, einops, onnx; print('✓ Dependencies OK')"

# 2. Verify modules
python -c "from core.deep_models.timesnet import TimesNet; from core.timeseries_trainer import TimeSeriesTrainer; print('✓ Modules OK')"

# 3. Launch app
python main.py
```

---

## ✅ Core Test Flow (15 min)

### 1. Create DL Project (2 min)
- [ ] File → New Project → `test_dl`
- [ ] Data Sources → Select **"Deep Learning"** mode
- [ ] Verify info label: "DL: Neural network learns features automatically"

### 2. Load Data (2 min)
- [ ] Browse → Select CSV file
- [ ] Load Data
- [ ] Verify data preview shows

### 3. Create Windows (2 min)
- [ ] Window Size: `100`
- [ ] Overlap: `0%`
- [ ] Class Column: Select label column
- [ ] Sensor Columns: Select 2-3 sensor columns
- [ ] Click **Create Windows**
- [ ] ⚠️ **VERIFY:** Pipeline mode now **LOCKED** (grayed out)
- [ ] Try clicking "Traditional ML" → Should show warning

### 4. Check Navigation (1 min)
- [ ] **Grayed out:** Feature Extraction, Feature Filtering, LLM Selection
- [ ] **Enabled:** Training, Embedded Code Generation
- [ ] Click grayed tab → Educational message appears

### 5. Configure Training (2 min)
- [ ] Navigate to **Training** tab
- [ ] Complexity: Select **"Minimal"** (fastest)
- [ ] Epochs: `10` (quick test)
- [ ] Batch Size: `16`
- [ ] Learning Rate: `0.001`

### 6. Train Model (3 min)
- [ ] Click **Start Training**
- [ ] **✅ CRITICAL:** Watch for device message:
  ```
  🖥️  Training Device: GPU: [name] or CPU ([N] threads)
  ```
- [ ] Training progresses through 10 epochs
- [ ] **✅ CRITICAL:** Watch for ONNX export message:
  ```
  ONNX model exported to .../timesnet_model.onnx
  ```
- [ ] Training completes successfully

### 7. Verify Results (2 min)
- [ ] Click **Evaluation** tab
- [ ] **✅ CRITICAL:** Check "Device Used" field shows correct device
- [ ] **✅ CRITICAL:** Check "ONNX Path" field is present
- [ ] Accuracy, Precision, Recall, F1 all displayed
- [ ] Per-class metrics shown

### 8. Verify Files (1 min)
```bash
# Open folder: projects/test_dl/models/
# Check for 4 files:
```
- [ ] `timesnet_model.pth` exists
- [ ] `timesnet_encoder.pkl` exists
- [ ] **✅ `timesnet_model.onnx` exists** (CRITICAL)
- [ ] `timesnet_results.json` exists

---

## 🎯 Critical Requirements Check

### ✅ Requirement 1: GPU/CPU Auto-Detection
**Location:** Training log (step 6)
**Expected:** `🖥️  Training Device: GPU: ... or CPU (...)`
**Status:** [ ] PASS / [ ] FAIL

### ✅ Requirement 2: ONNX Export
**Location:** Files in models/ folder (step 8)
**Expected:** `timesnet_model.onnx` file exists
**Status:** [ ] PASS / [ ] FAIL

### ✅ Requirement 3: Rename to "Embedded Code Generation"
**Location:** Sidebar navigation
**Expected:** Tab labeled "Embedded Code Generation" (not "DSP Generation")
**Status:** [ ] PASS / [ ] FAIL

---

## 🔄 Persistence Test (2 min - Optional)

- [ ] File → Save Project
- [ ] Close application
- [ ] Reopen application
- [ ] File → Open Project → `test_dl`
- [ ] Pipeline mode still shows "Deep Learning" (locked)
- [ ] Training results still visible in Evaluation tab

---

## ✅ Final Verification

**All 3 critical requirements must pass:**
- [ ] ✅ GPU/CPU detection with user reporting
- [ ] ✅ ONNX model exported
- [ ] ✅ "Embedded Code Generation" rename visible

**Additional checks:**
- [ ] No application crashes
- [ ] Training completed successfully
- [ ] All 4 model files created
- [ ] Results displayed correctly

---

## 📊 Quick Test Result

**Date:** _______________
**Time Taken:** _____ minutes
**Result:** [ ] ✅ PASS ALL | [ ] ❌ FAIL

**Issues Found:**
- _______________________________________________
- _______________________________________________

---

## 🐛 Quick Troubleshooting

**Training fails:**
```bash
# Check dependencies
pip install torch einops onnx --upgrade
```

**No ONNX file:**
```bash
# Check ONNX installed
pip show onnx
```

**Slow training:**
- Use "Minimal" complexity
- Reduce epochs to 5-10
- Normal for CPU

---

**For detailed testing:** See [TESTING_GUIDE_TIMESNET.md](TESTING_GUIDE_TIMESNET.md)

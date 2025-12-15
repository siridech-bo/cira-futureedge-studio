# TimesNet Deep Learning - Step-by-Step Testing Guide

**Version:** 1.0.0
**Date:** 2025-12-14
**Estimated Time:** 30-45 minutes

---

## 🎯 Testing Objectives

This guide will verify:
- ✅ Deep Learning mode selection and locking
- ✅ GPU/CPU auto-detection
- ✅ TimesNet model training
- ✅ ONNX export functionality
- ✅ Results display and saving
- ✅ Navigation behavior (grayed tabs)
- ✅ Backward compatibility with ML mode

---

## 📋 Prerequisites

### 1. Verify Dependencies
```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import einops; print('einops: OK')"
python -c "import onnx; print('ONNX: OK')"
```

**Expected Output:**
```
PyTorch: 1.13.1+cpu (or newer)
einops: OK
ONNX: OK
```

**✅ Pass Criteria:** All three imports succeed without errors

---

### 2. Verify Module Imports
```bash
python -c "from core.deep_models.timesnet import TimesNet, create_timesnet_for_classification; print('TimesNet: OK')"
python -c "from core.timeseries_trainer import TimeSeriesTrainer, TimeSeriesConfig; print('Trainer: OK')"
```

**Expected Output:**
```
TimesNet: OK
Trainer: OK
```

**✅ Pass Criteria:** Both imports succeed

---

### 3. Prepare Test Data

You'll need a CSV file with time series data. If you don't have one, create a sample:

**Option A: Use Existing Project Data**
- Use any CSV with multiple columns (sensors) and a label/class column

**Option B: Generate Sample Data**
```python
import pandas as pd
import numpy as np

# Generate synthetic sensor data
np.random.seed(42)
n_samples = 1000
time = np.arange(n_samples)

# 3 sensors with different patterns
sensor1 = np.sin(time * 0.1) + np.random.normal(0, 0.1, n_samples)
sensor2 = np.cos(time * 0.15) + np.random.normal(0, 0.1, n_samples)
sensor3 = np.sin(time * 0.05) * np.cos(time * 0.2) + np.random.normal(0, 0.1, n_samples)

# 4 classes based on patterns
classes = []
for i in range(n_samples):
    if i < 250:
        classes.append('normal')
    elif i < 500:
        classes.append('anomaly_A')
    elif i < 750:
        classes.append('anomaly_B')
    else:
        classes.append('anomaly_C')

# Create DataFrame
df = pd.DataFrame({
    'timestamp': time,
    'sensor1': sensor1,
    'sensor2': sensor2,
    'sensor3': sensor3,
    'class': classes
})

# Save to CSV
df.to_csv('test_timeseries_data.csv', index=False)
print("✓ Test data created: test_timeseries_data.csv")
```

**✅ Pass Criteria:** CSV file created with ~1000 rows, 3 sensor columns, 1 class column

---

## 🧪 Test Suite

---

## **TEST 1: Launch Application**

### Steps:
1. Open terminal/command prompt
2. Navigate to CiRA FES directory:
   ```bash
   cd "d:\CiRA FES"
   ```
3. Launch the application:
   ```bash
   python main.py
   ```

### Expected Result:
- ✅ Application window opens
- ✅ No error messages in console
- ✅ Main window displays with sidebar navigation

### ✅ Pass Criteria:
- Application launches successfully without errors

### ❌ If Failed:
- Check Python version (should be 3.8+)
- Verify all dependencies installed
- Check console for error messages

---

## **TEST 2: Create New Project with Deep Learning Mode**

### Steps:
1. Click **File → New Project** (or use project creation button)
2. Enter project name: `test_dl_project`
3. Click **Create**
4. Navigate to **Data Sources** tab (should auto-open)

### Expected Result:
- ✅ Project created successfully
- ✅ Data Sources panel opens
- ✅ **Pipeline Mode** selector visible with two options:
  - "Traditional ML"
  - "Deep Learning"
- ✅ Default selection is "Traditional ML"
- ✅ Info label shows: "ML: Feature-based classification"

### ✅ Pass Criteria:
- Pipeline mode selector is visible and functional
- Default mode is "Traditional ML"

### Screenshot Location:
![Pipeline Mode Selector - should show segmented button with two options]

---

## **TEST 3: Select Deep Learning Mode**

### Steps:
1. In Data Sources panel, find **Pipeline Mode** section
2. Click **"Deep Learning"** button
3. Observe the info label change

### Expected Result:
- ✅ "Deep Learning" button becomes selected (highlighted)
- ✅ Info label changes to: "DL: Neural network learns features automatically"
- ✅ Warning label shows: "⚠️ Mode can be locked after windowing"
- ✅ No error messages

### ✅ Pass Criteria:
- Mode switches to Deep Learning
- UI updates to reflect DL mode
- Warning about locking is visible

### 📸 Checkpoint:
Take note of the warning message - we'll verify locking later

---

## **TEST 4: Load Data**

### Steps:
1. In Data Sources panel, find **Data Source** section
2. Click **Browse** button
3. Select your test CSV file (e.g., `test_timeseries_data.csv`)
4. Verify file path appears in the field
5. Click **Load Data** button
6. Wait for loading to complete

### Expected Result:
- ✅ File path displayed in text field
- ✅ Loading progress indicator appears
- ✅ Success message: "Data loaded successfully"
- ✅ Data preview table shows loaded data
- ✅ Column selection dropdowns populate with your columns

### ✅ Pass Criteria:
- Data loads without errors
- All columns visible in preview
- Can proceed to windowing

### ❌ If Failed:
- Check CSV file format (must have header row)
- Verify file is not corrupted
- Check console for specific error

---

## **TEST 5: Configure and Create Windows**

### Steps:
1. In **Windowing Configuration** section:
   - Set **Window Size**: `100`
   - Set **Overlap**: `0` (or 50%)
   - Set **Class Column**: Select your class/label column (e.g., `class`)
2. In **Column Selection**:
   - Select sensor columns (e.g., `sensor1`, `sensor2`, `sensor3`)
   - Exclude timestamp and class columns
3. Click **Create Windows** button
4. Wait for processing

### Expected Result:
- ✅ Progress bar appears
- ✅ Success message: "Windows created successfully"
- ✅ Shows: "Created N windows" (should be ~10 for 1000 rows, size 100)
- ✅ **IMPORTANT:** Warning label now shows: "🔒 Mode locked: Deep Learning"
- ✅ Pipeline mode selector becomes **disabled** (grayed out)
- ✅ Attempting to click other mode does nothing or shows warning

### ✅ Pass Criteria:
- Windows created successfully
- **Pipeline mode is now LOCKED** (this is critical)
- Cannot change mode anymore

### 🔍 Critical Check:
Try clicking "Traditional ML" button:
- **Expected:** Warning dialog: "Pipeline mode is locked after windowing"
- **Pass:** Dialog appears and mode stays on "Deep Learning"

---

## **TEST 6: Verify Navigation - Grayed Tabs**

### Steps:
1. Look at the **sidebar navigation** (left side)
2. Observe which tabs are enabled vs disabled
3. Try clicking on **Feature Extraction** tab
4. Try clicking on **Feature Filtering** tab
5. Try clicking on **LLM Selection** tab

### Expected Result:

**Grayed Out (Disabled):**
- ⊘ Feature Extraction (text appears gray/dim)
- ⊘ Feature Filtering (text appears gray/dim)
- ⊘ LLM Selection (text appears gray/dim)

**Enabled (Active):**
- ✓ Data Sources (green/active)
- ✓ Training (clickable)
- ✓ Embedded Code Generation (clickable)
- ✓ Build Firmware (clickable)

**When Clicking Grayed Tab:**
- ✅ Info dialog appears with message:
  ```
  Deep Learning Mode

  [Tab Name] is not needed for Deep Learning.

  TimesNet learns features automatically from raw time series data.
  ```
- ✅ Dialog has "OK" button
- ✅ Clicking OK closes dialog

### ✅ Pass Criteria:
- Correct tabs are grayed out
- Educational message appears when clicking grayed tabs
- Can still click enabled tabs

### 📸 Visual Check:
The grayed tabs should be visually distinct (dimmed, disabled appearance)

---

## **TEST 7: Navigate to Training Panel**

### Steps:
1. Click **Training** tab in sidebar navigation
2. Wait for panel to load

### Expected Result:
- ✅ Training panel opens
- ✅ **Algorithm** tab is visible
- ✅ Deep Learning UI is shown (NOT Traditional ML UI)

**You should see:**
- ✅ **Model Architecture** section with "TimesNet" displayed
- ✅ **Model Complexity** selector with 3 options:
  - Minimal
  - Efficient (default selected)
  - Comprehensive
- ✅ Info text explaining complexity levels

**You should NOT see:**
- ❌ Algorithm dropdown (sklearn/PyOD algorithms)
- ❌ Contamination factor slider
- ❌ ML-specific controls

### ✅ Pass Criteria:
- Training panel shows Deep Learning UI
- Complexity selector visible with 3 options
- No ML-specific controls visible

---

## **TEST 8: Configure Training Parameters**

### Steps:
1. Navigate to **Training** tab within Model panel
2. Configure the following:

   **Model Complexity:**
   - Select **"Minimal"** (for faster testing)

   **Training Parameters:**
   - Epochs: `20` (reduced for testing speed)
   - Batch Size: `16`
   - Learning Rate: `0.001` (default)

### Expected Result:
- ✅ All fields accept input
- ✅ Epochs field accepts numeric value (10-200)
- ✅ Batch Size dropdown has options: 8, 16, 32, 64
- ✅ Learning Rate field accepts decimal value

### ✅ Pass Criteria:
- Can modify all training parameters
- Values are saved when changed

### 📝 Note:
Using "Minimal" complexity and 20 epochs will make training faster for testing

---

## **TEST 9: Start Training - GPU/CPU Detection**

### Steps:
1. Ensure parameters are set (from TEST 8)
2. Click **Start Training** button
3. **IMMEDIATELY** watch the training log/console

### Expected Result - First Few Lines:

**If GPU Available:**
```
Training timesnet deep learning model
Windows shape: (10, 100, 3)
Detected 4 classes: ['normal', 'anomaly_A', 'anomaly_B', 'anomaly_C']
Auto-detected and using GPU: NVIDIA GeForce RTX 3060
GPU memory: 12.0 GB
🖥️  Training Device: GPU: NVIDIA GeForce RTX 3060
Model has 52,340 parameters
Starting training for 20 epochs...
```

**If CPU Only (Current Case):**
```
Training timesnet deep learning model
Windows shape: (10, 100, 3)
Detected 4 classes: ['normal', 'anomaly_A', 'anomaly_B', 'anomaly_C']
No GPU detected, using CPU (10 threads)
🖥️  Training Device: CPU (10 threads)
Model has 52,340 parameters
Starting training for 20 epochs...
```

### ✅ Pass Criteria:
- **CRITICAL:** Must see "🖥️ Training Device: GPU:..." or "🖥️ Training Device: CPU..."
- Device detection message appears early in log
- Training starts without errors

### 🔍 Key Verification:
The **device reporting** is one of the three main requirements. Verify you see the device message!

---

## **TEST 10: Monitor Training Progress**

### Steps:
1. Watch training log as epochs progress
2. Observe progress bars (if shown in UI)
3. Wait for training to complete (should take 1-5 minutes for Minimal/20 epochs)

### Expected Result:

**During Training:**
```
Epoch 1/20: 100%|██████████| 2/2 [00:01<00:00, 1.2it/s, loss=1.3234, acc=45.00%]
Epoch 1/20 - Train Loss: 1.3234, Train Acc: 0.4500, Val Loss: 1.2876, Val Acc: 0.5000

Epoch 2/20: 100%|██████████| 2/2 [00:01<00:00, 1.3it/s, loss=1.2456, acc=52.00%]
Epoch 2/20 - Train Loss: 1.2456, Train Acc: 0.5200, Val Loss: 1.1876, Val Acc: 0.5500

...

Epoch 20/20: 100%|██████████| 2/2 [00:01<00:00, 1.4it/s, loss=0.3456, acc=92.00%]
Epoch 20/20 - Train Loss: 0.3456, Train Acc: 0.9200, Val Loss: 0.4123, Val Acc: 0.8500
```

**After Training Completes:**
```
Training Results - Accuracy: 0.850, Precision: 0.845, Recall: 0.850, F1: 0.847
Per-class F1 scores:
  normal: 0.920
  anomaly_A: 0.810
  anomaly_B: 0.830
  anomaly_C: 0.825

Model saved to d:\CiRA FES\projects\test_dl_project\models\timesnet_model.pth
Label encoder saved to d:\CiRA FES\projects\test_dl_project\models\timesnet_encoder.pkl
ONNX model exported to d:\CiRA FES\projects\test_dl_project\models\timesnet_model.onnx
Results saved to d:\CiRA FES\projects\test_dl_project\models\timesnet_results.json
```

### ✅ Pass Criteria:
- Training progresses through all epochs
- Accuracy improves over time
- Training completes without errors
- **CRITICAL:** See "ONNX model exported to..." message
- All 4 files saved (pth, pkl, onnx, json)

### ⏱️ Expected Time:
- CPU: 2-5 minutes for 20 epochs
- GPU: 30-60 seconds for 20 epochs

---

## **TEST 11: Verify ONNX Export**

### Steps:
1. Open file explorer
2. Navigate to: `d:\CiRA FES\projects\test_dl_project\models\`
3. Check for files

### Expected Result:
You should see **4 files**:
- ✅ `timesnet_model.pth` (PyTorch checkpoint, ~200KB-2MB)
- ✅ `timesnet_encoder.pkl` (Label encoder, ~1-5KB)
- ✅ `timesnet_model.onnx` (ONNX export, ~200KB-2MB)
- ✅ `timesnet_results.json` (Metrics JSON, ~2-5KB)

### ✅ Pass Criteria:
- All 4 files exist
- **CRITICAL:** `timesnet_model.onnx` file exists (required for Jetson deployment)
- Files are not empty (check size > 0 bytes)

### 🔍 Detailed Check:
Open `timesnet_results.json` in a text editor:
```json
{
  "algorithm": "timesnet",
  "model_path": "...",
  "onnx_model_path": "d:\\CiRA FES\\projects\\test_dl_project\\models\\timesnet_model.onnx",
  "device_used": "CPU (10 threads)",
  "accuracy": 0.85,
  ...
}
```

Verify:
- ✅ `onnx_model_path` field is present and not null
- ✅ `device_used` field shows correct device

---

## **TEST 12: View Results in Evaluation Tab**

### Steps:
1. In Training panel, click **Evaluation** tab
2. Scroll through results

### Expected Result:

**Model Information:**
- ✅ Algorithm: TimesNet
- ✅ Device Used: "GPU: NVIDIA..." or "CPU (N threads)"
- ✅ Total Parameters: ~50,000-100,000 (for Minimal)

**Performance Metrics:**
- ✅ Accuracy: 0.XX (decimal value)
- ✅ Precision: 0.XX
- ✅ Recall: 0.XX
- ✅ F1 Score: 0.XX

**Per-Class Metrics Table:**
- ✅ Shows all 4 classes (normal, anomaly_A, anomaly_B, anomaly_C)
- ✅ Each row shows: Precision, Recall, F1, Support

**Files Section:**
- ✅ Model Path: `.../timesnet_model.pth`
- ✅ Encoder Path: `.../timesnet_encoder.pkl`
- ✅ **ONNX Path: `.../timesnet_model.onnx`** (IMPORTANT)
- ✅ Results Path: `.../timesnet_results.json`

### ✅ Pass Criteria:
- All metrics displayed correctly
- **Device Used** field shows correct device (verifies requirement #1)
- **ONNX Path** is displayed (verifies requirement #2)
- Values are reasonable (accuracy 0.5-1.0)

---

## **TEST 13: Verify Project Data Persistence**

### Steps:
1. Click **File → Save Project** (if not auto-saved)
2. Close the application completely
3. Reopen application: `python main.py`
4. Click **File → Open Project**
5. Select `test_dl_project`
6. Navigate to **Data Sources** tab

### Expected Result:
- ✅ Project opens successfully
- ✅ Pipeline mode shows **"Deep Learning"** (selected)
- ✅ Pipeline mode selector is **disabled/grayed out** (locked)
- ✅ Warning shows: "🔒 Mode locked: Deep Learning"
- ✅ Data is still loaded
- ✅ Windows are still created

**Navigate to Training → Evaluation:**
- ✅ Model results are still displayed
- ✅ All metrics preserved
- ✅ ONNX path still shown

### ✅ Pass Criteria:
- Project reopens with DL mode preserved
- Mode remains locked
- Training results persist

---

## **TEST 14: Verify Navigation Persistence**

### Steps:
1. With `test_dl_project` open (from TEST 13)
2. Check sidebar navigation

### Expected Result:
- ✅ Feature Extraction: Still grayed out
- ✅ Feature Filtering: Still grayed out
- ✅ LLM Selection: Still grayed out
- ✅ Training: Active/enabled
- ✅ Embedded Code Generation: Active/enabled

**Click grayed tab:**
- ✅ Educational dialog still appears

### ✅ Pass Criteria:
- Navigation state persists after project reload
- Grayed tabs remain grayed

---

## **TEST 15: Test Model Complexity Variants** (Optional)

### Steps:
1. Create a new DL project: `test_dl_complexity`
2. Load same data and create windows
3. Navigate to Training
4. Select **"Comprehensive"** complexity
5. Set epochs to `10` (faster test)
6. Start training
7. Compare parameter count

### Expected Result:
- ✅ Training starts successfully
- ✅ Model has **~800,000 parameters** (vs ~50,000 for Minimal)
- ✅ Training may be slower
- ✅ ONNX export still works

### ✅ Pass Criteria:
- Different complexity levels work
- Parameter count changes as expected
- All complexities export to ONNX

---

## **TEST 16: Backward Compatibility - Traditional ML Mode**

### Steps:
1. Create a **new** project: `test_ml_mode`
2. In Data Sources, select **"Traditional ML"** mode
3. Load same CSV data
4. Create windows (mode locks to ML)
5. Navigate to **Feature Extraction** tab

### Expected Result:
- ✅ Feature Extraction tab is **enabled** (not grayed)
- ✅ Can access feature extraction UI
- ✅ Feature Filtering tab is **enabled**
- ✅ LLM Selection tab is **enabled**
- ✅ Training tab shows ML UI (sklearn/PyOD dropdowns)

**In Training → Algorithm tab:**
- ✅ Shows algorithm dropdown (Isolation Forest, Random Forest, etc.)
- ✅ Shows contamination factor
- ✅ Does NOT show TimesNet controls

### ✅ Pass Criteria:
- Traditional ML mode still works
- All ML tabs are accessible
- No DL controls shown in ML mode

---

## **TEST 17: Verify "Embedded Code Generation" Rename**

### Steps:
1. With any project open
2. Look at sidebar navigation
3. Find the tab that was previously called "DSP Generation"

### Expected Result:
- ✅ Tab is now labeled **"Embedded Code Generation"**
- ✅ Icon: ⚙️ (gear icon)
- ✅ Tab is clickable
- ✅ Panel title says "Embedded Code Generation"

### ✅ Pass Criteria:
- Rename is complete throughout UI
- No references to "DSP Generation" remain visible

---

## **TEST 18: Error Handling - Invalid Input**

### Steps:
1. Open DL project
2. Go to Training tab
3. Try invalid inputs:
   - Epochs: `-10` or `0` or `1000`
   - Batch Size: Select then manually type `999`
   - Learning Rate: `0` or `10.0` or `abc`
4. Click Start Training

### Expected Result:
- ✅ Validation error appears
- ✅ Error message explains what's wrong
- ✅ Training does not start
- ✅ Application doesn't crash

### ✅ Pass Criteria:
- Invalid inputs are caught
- Helpful error messages shown
- No crashes

---

## **TEST 19: Multi-Class Classification**

### Steps:
1. Verify your test data has 4 classes (normal, anomaly_A, anomaly_B, anomaly_C)
2. After training completes, check per-class metrics

### Expected Result:
- ✅ All 4 classes shown in results
- ✅ Metrics calculated for each class
- ✅ Confusion matrix is 4x4
- ✅ ONNX model supports 4 output classes

### ✅ Pass Criteria:
- Multi-class classification works
- All classes represented in results

---

## **TEST 20: ONNX Verification** (Advanced - Optional)

### Steps:
```bash
python -c "
import onnx
model = onnx.load('projects/test_dl_project/models/timesnet_model.onnx')
print(f'✓ ONNX model loaded')
print(f'Inputs: {[i.name for i in model.graph.input]}')
print(f'Outputs: {[o.name for o in model.graph.output]}')
onnx.checker.check_model(model)
print('✓ ONNX model is valid')
"
```

### Expected Result:
```
✓ ONNX model loaded
Inputs: ['input']
Outputs: ['output']
✓ ONNX model is valid
```

### ✅ Pass Criteria:
- ONNX model loads successfully
- Has expected input/output names
- Passes ONNX validation

---

## 📊 Test Results Summary

Use this checklist to track your testing:

### Core Functionality
- [ ] TEST 1: Application Launch
- [ ] TEST 2: Create DL Project
- [ ] TEST 3: Select DL Mode
- [ ] TEST 4: Load Data
- [ ] TEST 5: Create Windows & Mode Lock
- [ ] TEST 6: Grayed Tabs Verification
- [ ] TEST 7: Training Panel Navigation
- [ ] TEST 8: Configure Training
- [ ] TEST 9: GPU/CPU Detection ⭐ (CRITICAL)
- [ ] TEST 10: Training Progress
- [ ] TEST 11: ONNX Export ⭐ (CRITICAL)
- [ ] TEST 12: Results Display
- [ ] TEST 13: Project Persistence
- [ ] TEST 14: Navigation Persistence

### Extended Testing
- [ ] TEST 15: Complexity Variants
- [ ] TEST 16: ML Mode Compatibility
- [ ] TEST 17: Rename Verification ⭐ (CRITICAL)
- [ ] TEST 18: Error Handling
- [ ] TEST 19: Multi-Class Classification
- [ ] TEST 20: ONNX Validation

### Critical Requirements Verification
- [ ] ✅ Requirement 1: GPU/CPU auto-detection with user reporting (TEST 9)
- [ ] ✅ Requirement 2: ONNX model output (TEST 11)
- [ ] ✅ Requirement 3: "Embedded Code Generation" rename (TEST 17)

---

## ⚠️ Common Issues & Solutions

### Issue 1: "Module not found: torch"
**Solution:**
```bash
pip install torch>=2.0.0
```

### Issue 2: Training very slow on CPU
**Solution:**
- Use "Minimal" complexity
- Reduce epochs to 10-20
- Reduce dataset size for testing
- This is expected behavior - document it

### Issue 3: ONNX file not created
**Check:**
1. Training completed successfully?
2. Look for ONNX export message in log
3. Check if ONNX library is installed: `pip show onnx`

### Issue 4: Grayed tabs not showing
**Check:**
1. Is pipeline mode set to "Deep Learning"?
2. Did you create windows (mode locked)?
3. Try closing and reopening project

### Issue 5: Can't change pipeline mode
**This is expected!**
- Mode locks after windowing
- This is intentional design
- Create new project to test other mode

---

## 📝 Test Report Template

After completing tests, fill out this report:

```
TIMESNET TESTING REPORT
=======================

Date: _____________
Tester: _____________
Environment:
- OS: Windows/Linux/Mac
- Python: _______
- PyTorch: _______
- GPU: Yes/No (Model: _______)

TEST RESULTS:
-------------
Total Tests: 20
Passed: ___
Failed: ___
Skipped: ___

CRITICAL REQUIREMENTS:
----------------------
[✓/✗] GPU/CPU Auto-Detection: __________
[✓/✗] ONNX Export: __________
[✓/✗] Rename to "Embedded Code": __________

FAILED TESTS (if any):
----------------------
Test #: ___
Issue: _______________
Error: _______________

PERFORMANCE NOTES:
------------------
Training Time (20 epochs, Minimal): _____ seconds
Device Used: _____________
Model Accuracy: _____________

RECOMMENDATION:
---------------
[✓] PASS - Ready for production
[ ] FAIL - Issues found (see above)
[ ] PARTIAL - Minor issues, acceptable for release

Tester Signature: _____________
```

---

## 🎯 Success Criteria

The feature is **READY FOR PRODUCTION** if:

1. ✅ All CRITICAL tests pass (9, 11, 17)
2. ✅ At least 80% of core tests pass (1-14)
3. ✅ No application crashes during testing
4. ✅ ONNX file is created and valid
5. ✅ Device detection works correctly
6. ✅ ML mode still works (backward compatibility)

---

## 📞 Support

If you encounter issues during testing:
1. Check console/log output for specific errors
2. Review [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md) troubleshooting section
3. Verify all dependencies installed correctly
4. Document the issue with screenshots and error messages

---

**Estimated Total Testing Time:** 30-45 minutes
**Last Updated:** 2025-12-14
**Version:** 1.0.0

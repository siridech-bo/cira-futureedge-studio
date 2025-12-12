# Multi-Class Classification Implementation Status

**Date:** 2025-12-12
**Feature:** Filename-based Class Extraction + Multi-Class Classification Support

---

## ✅ **Completed Tasks (Sprint 1 - Core Foundation)**

### 1. **Project Configuration Updates**
- ✅ **[project.py]** Updated `ProjectData` dataclass with classification fields:
  - `task_type`: "anomaly_detection" or "classification"
  - `class_mapping`: Dict mapping class names to integers
  - `num_classes`: Number of detected classes
  - `class_distribution`: Sample count per class
  - `label_extraction_enabled`: Toggle for label extraction
  - `label_pattern`: Pattern type (prefix, suffix, folder, regex)
  - `window_labels`: List of labels for each window

- ✅ **[project.py]** Updated `ProjectModel` dataclass with classification fields:
  - `model_type`: "anomaly" or "classifier"
  - `num_classes`: Number of classes for classification
  - `class_names`: List of class names
  - `label_encoder_path`: Path to label encoder pickle
  - `confusion_matrix`: Confusion matrix for multi-class results
  - `per_class_metrics`: Per-class precision/recall/F1

### 2. **Label Extraction Utility**
- ✅ **[data_sources/label_extractor.py]** Created complete `LabelExtractor` class with:
  - `extract_from_filename()`: Extract labels using multiple patterns
  - `extract_from_path()`: Extract from full file paths
  - `detect_classes_in_files()`: Scan files and build class distribution
  - `create_class_mapping()`: Generate integer mapping for classes
  - `validate_class_distribution()`: Check if distribution is suitable for training
  - `suggest_pattern()`: Auto-detect best extraction pattern

**Supported Patterns:**
- **Prefix**: `idle.1.cbor` → "idle"
- **Suffix**: `sample_001_snake.cbor` → "snake"
- **Folder**: `/data/idle/sample1.cbor` → "idle"
- **Regex**: Custom regex patterns

---

## 🔨 **In Progress (Current Sprint)**

### 3. **Data Source Loader Modifications**
- 🔄 **Edge Impulse Loader** - Need to add:
  - Label extraction toggle in config parameters
  - `_extract_label_from_filename()` method
  - Append 'class_label' column to loaded DataFrame
  - Track detected classes per file

- ⏸️ **CSV Loader** - Same modifications as Edge Impulse

---

## 📋 **Remaining Tasks (Sprint 2 & 3)**

### Sprint 2: Windowing & Training

**Task 4: Update WindowingEngine**
- Modify `segment_data()` to accept `label_column` parameter
- Implement majority voting for window labels
- Add `get_window_labels()` method
- **File:** `core/windowing.py`

**Task 5: Update Project Window Saving**
- Modify `save_windows()` to include labels parameter
- Save labels alongside windows in pickle file
- **File:** `core/project.py`

**Task 6: Create ClassificationTrainer**
- Create new `core/classification_trainer.py`
- Implement sklearn classifiers: Random Forest, Gradient Boosting, SVM, MLP
- Add `ClassificationResults` dataclass
- Support stratified train/test split
- Generate per-class metrics and confusion matrix
- **Dependencies:** sklearn (already installed)

---

### Sprint 3: UI Integration

**Task 7: Add Mode Toggle to Data Panel**
- Add task mode selection widget (Anomaly Detection vs Classification)
- Add classification settings frame (label extraction options)
- Show detected classes after data load
- Display class distribution chart
- **File:** `ui/data_panel.py`

**Task 8: Update Model Panel**
- Detect task mode from project config
- Show classification algorithms when in classification mode
- Replace anomaly metrics with classification metrics
- Add confusion matrix visualization
- **File:** `ui/model_panel.py`

**Task 9: Create Confusion Matrix Widget**
- Build heatmap visualization using tkinter canvas
- Color code cells (green=correct, red=errors)
- **File:** `ui/widgets/confusion_matrix.py` (new)

---

### Sprint 4: DSP & Build Integration

**Task 10: Update DSP Generator**
- Add classification-specific C++ code templates
- Generate `classify_window()` function
- **File:** `core/dsp_generator.py`

**Task 11: Update Build System**
- Handle both anomaly and classification model types
- Adjust firmware generation accordingly
- **File:** `ui/build_panel.py`

---

## 🎯 **Testing Plan**

### Test Case 1: Load Labeled Dataset
```
Dataset: D:\CiRA FES\Dataset\Motion+Classification\training\
Files: idle.*.cbor, snake.*.cbor, ingestion.*.cbor

Steps:
1. Create new project
2. Select "Edge Impulse CBOR" data source
3. Switch to "Classification" mode
4. Enable "Extract labels from filenames"
5. Select pattern: "prefix"
6. Load data → Should detect 3 classes
```

**Expected Results:**
- Classes detected: idle, snake, ingestion
- Class distribution shown in UI
- Labels preserved through windowing

### Test Case 2: Train Classifier
```
Steps:
1. Continue from Test Case 1
2. Extract features (tsfresh)
3. Select features (LLM or manual)
4. Go to Model Training
5. Select "Random Forest" classifier
6. Train model
```

**Expected Results:**
- Model trains on labeled windows
- Confusion matrix displayed
- Per-class precision/recall/F1 shown
- Model saved with label encoder

### Test Case 3: Backward Compatibility
```
Steps:
1. Open existing anomaly detection project
2. Verify it still works in anomaly mode
```

**Expected Results:**
- Old projects load without errors
- Anomaly detection workflow unchanged
- No breaking changes

---

## 📦 **Dependencies**

### Already Installed:
- ✅ scikit-learn (for classifiers)
- ✅ numpy, pandas
- ✅ pyod (for anomaly detection)

### May Need (Optional):
- matplotlib (for confusion matrix visualization)
- seaborn (for better heatmaps)

```bash
pip install matplotlib seaborn
```

---

## 🚀 **Next Steps**

1. ✅ Complete Edge Impulse loader modifications
2. ✅ Complete CSV loader modifications
3. ⏭️ Update WindowingEngine for label preservation
4. ⏭️ Create ClassificationTrainer class
5. ⏭️ Add UI mode toggle

---

## 📝 **Notes**

- All changes maintain backward compatibility
- Existing anomaly projects continue to work
- Classification is an opt-in feature via task_type selection
- Label extraction happens at data loading stage
- Labels propagate through: Load → Window → Features → Training

---

## 🔗 **Related Files**

**Modified:**
- `core/project.py` - Project data models
- `data_sources/label_extractor.py` - NEW utility

**To Modify:**
- `data_sources/edgeimpulse_loader.py`
- `data_sources/csv_loader.py`
- `core/windowing.py`
- `ui/data_panel.py`
- `ui/model_panel.py`

**To Create:**
- `core/classification_trainer.py`
- `ui/widgets/confusion_matrix.py`

# Phase 6 - Training Panel Integration Progress

**Session Date:** 2025-12-14
**Status:** PARTIALLY COMPLETE - UI Components Added

---

## ✅ **Completed in This Session**

### 1. **Algorithm Tab - DL Mode UI** (`ui/model_panel.py:60-307`)

**Changes:**
- Split `_create_algorithm_tab()` to detect pipeline mode
- Added `_create_ml_algorithm_ui()` - existing ML algorithm selection
- Added `_create_dl_algorithm_ui()` - new DL configuration UI

**DL UI Components:**
```python
# Data Info Display
- Windows count
- Window size
- Number of sensors

# Model Complexity Selector
- Segmented button: Minimal | Efficient | Comprehensive
- Descriptions of each complexity level
- Parameter counts displayed

# Info Panel
- TimesNet explanation
- Key features
- Deployment workflow
```

**Code Location:** [ui/model_panel.py:191-307](ui/model_panel.py#L191)

---

### 2. **Training Tab - DL Controls** (`ui/model_panel.py:309-432`)

**Added DL-Specific Controls:**
```python
# Deep Learning Parameters
self.epochs_var = ctk.StringVar(value="50")
self.epochs_entry = ctk.CTkEntry(...)  # 10-200 epochs

self.batch_var = ctk.StringVar(value="32")
self.batch_menu = ctk.CTkOptionMenu(values=["8", "16", "32", "64"])

self.lr_var = ctk.StringVar(value="0.001")
self.lr_entry = ctk.CTkEntry(...)  # Learning rate 0.0001-0.01
```

**Preserved ML Controls:**
```python
# ML-Only (need to hide in DL mode)
self.contamination_var = ctk.StringVar(value="0.1")
self.contam_entry = ctk.CTkEntry(...)
```

**Code Location:** [ui/model_panel.py:362-391](ui/model_panel.py#L362)

---

## ⏳ **REMAINING WORK**

### 1. **Show/Hide Control Logic** (NEXT STEP)

**Need to Add:**
```python
def _update_training_controls_for_pipeline_mode(self):
    """Show/hide controls based on pipeline mode."""
    project = self.project_manager.current_project
    if not project:
        return

    pipeline_mode = getattr(project.data, 'pipeline_mode', 'ml')

    if pipeline_mode == "dl":
        # Hide ML controls
        self.contam_label1.grid_remove()
        self.contam_entry.grid_remove()
        self.contam_label2.grid_remove()

        # Show DL controls
        self.epochs_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.epochs_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")
        self.epochs_help.grid(row=4, column=0, columnspan=2, padx=10, pady=(0, 5), sticky="w")

        self.batch_label.grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.batch_menu.grid(row=5, column=1, padx=10, pady=5, sticky="w")

        self.lr_label.grid(row=6, column=0, padx=10, pady=5, sticky="w")
        self.lr_entry.grid(row=6, column=1, padx=10, pady=5, sticky="w")
        self.lr_help.grid(row=7, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")

        # Update normalize label
        self.normalize_check.configure(text="Normalize data (recommended)")

    else:
        # Show ML controls
        self.contam_label1.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.contam_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")
        self.contam_label2.grid(row=4, column=0, columnspan=2, padx=10, pady=(0, 5), sticky="w")

        # Hide DL controls
        self.epochs_label.grid_remove()
        self.epochs_entry.grid_remove()
        self.epochs_help.grid_remove()
        self.batch_label.grid_remove()
        self.batch_menu.grid_remove()
        self.lr_label.grid_remove()
        self.lr_entry.grid_remove()
        self.lr_help.grid_remove()
```

**Call this method:**
- In `__init__()` after creating tabs
- When switching to model panel (if pipeline mode changed)

---

### 2. **Load Windows Data for DL** (CRITICAL)

**Need to Add in Data Loading:**
```python
def _load_data_for_training(self):
    """Load features (ML) or windows (DL) based on pipeline mode."""
    project = self.project_manager.current_project
    if not project:
        return

    pipeline_mode = getattr(project.data, 'pipeline_mode', 'ml')

    if pipeline_mode == "dl":
        # Load windows for deep learning
        import pickle

        if project.data.train_test_split_type == "manual":
            # Load train/test windows separately
            with open(project.data.train_windows_file, 'rb') as f:
                train_windows = pickle.load(f)
            with open(project.data.test_windows_file, 'rb') as f:
                test_windows = pickle.load(f)

            # Convert to numpy arrays
            self.train_windows = np.array([w.data for w in train_windows])
            self.train_labels = [w.class_label for w in train_windows]
            self.test_windows = np.array([w.data for w in test_windows])
            self.test_labels = [w.class_label for w in test_windows]
        else:
            # Load single windows file
            with open(project.data.windows_file, 'rb') as f:
                windows = pickle.load(f)

            # Convert to numpy array (n_windows, seq_len, n_sensors)
            self.windows = np.array([w.data for w in windows])
            self.window_labels = [w.class_label for w in windows]

        # Update UI labels
        self.windows_info_label.configure(
            text=f"{len(self.windows)} windows",
            text_color="green"
        )
        self.window_size_label.configure(
            text=f"{self.windows.shape[1]} samples",
            text_color="green"
        )
        self.sensors_info_label.configure(
            text=f"{self.windows.shape[2]} sensors",
            text_color="green"
        )
    else:
        # Existing ML feature loading (ALREADY IMPLEMENTED)
        # ... current feature loading code ...
        pass
```

---

### 3. **Update `_start_training()` Method** (MAJOR)

**Find existing `_start_training` and update:**
```python
def _start_training(self):
    """Start training based on pipeline mode."""
    project = self.project_manager.current_project
    if not project:
        return

    pipeline_mode = getattr(project.data, 'pipeline_mode', 'ml')

    if pipeline_mode == "dl":
        self._start_dl_training()
    else:
        self._start_ml_training()  # Existing implementation

def _start_dl_training(self):
    """Start deep learning training with TimesNet."""
    project = self.project_manager.current_project

    # Validate data
    if self.windows is None or self.window_labels is None:
        messagebox.showerror("Error", "No window data loaded")
        return

    # Get configuration
    complexity = self.complexity_var.get().lower()
    epochs = int(self.epochs_var.get())
    batch_size = int(self.batch_var.get())
    lr = float(self.lr_var.get())
    test_size = float(self.test_size_var.get())
    random_state = int(self.random_state_var.get())

    # Create config
    config = TimeSeriesConfig(
        algorithm='timesnet',
        test_size=test_size,
        random_state=random_state,
        device='auto',  # Auto-detect GPU/CPU
        complexity=complexity,
        batch_size=batch_size,
        epochs=epochs,
        learning_rate=lr,
        params={}
    )

    # Get output directory
    model_dir = project.get_project_dir() / "models"
    model_dir.mkdir(parents=True, exist_ok=True)

    # Train in thread
    def train_thread():
        try:
            self._log_training("Starting TimesNet training...")
            self._log_training(f"Device: Auto-detecting GPU/CPU...")

            results = self.timeseries_trainer.train(
                windows=self.windows,
                labels=np.array(self.window_labels),
                config=config,
                output_dir=model_dir
            )

            # Update project
            project.model.trained = True
            project.model.is_deep_learning = True
            project.model.dl_architecture = 'timesnet'
            project.model.dl_device_used = results.device_used
            project.model.model_path = results.model_path
            project.model.onnx_model_path = results.onnx_model_path
            project.model.label_encoder_path = results.label_encoder_path
            project.model.model_type = "classifier"
            project.model.num_classes = results.n_classes
            project.model.class_names = results.class_names
            project.model.metrics = {
                'accuracy': results.accuracy,
                'precision_macro': results.precision_macro,
                'recall_macro': results.recall_macro,
                'f1_macro': results.f1_macro
            }
            project.model.confusion_matrix = results.confusion_matrix
            project.model.per_class_metrics = {
                'precision': results.per_class_precision,
                'recall': results.per_class_recall,
                'f1': results.per_class_f1
            }

            project.mark_stage_completed("model")
            project.save()

            self.training_results = results
            self._log_training(f"✓ Training complete!")
            self._log_training(f"Device used: {results.device_used}")
            self._log_training(f"Accuracy: {results.accuracy:.3f}")

            # Update evaluation tab
            self._update_evaluation_display()

        except Exception as e:
            self._log_training(f"Error: {str(e)}")
            logger.error(f"DL training failed: {e}")

    thread = threading.Thread(target=train_thread, daemon=True)
    thread.start()
```

---

### 4. **Update Evaluation Display** (MINOR)

**Modify evaluation tab to show DL results:**
- Check if `is_deep_learning` flag
- Display device used
- Show ONNX export path
- Link to TensorRT deployment docs

---

## 📊 **Current Progress**

| Component | Status | Completeness |
|-----------|--------|--------------|
| Algorithm Tab UI | ✅ Complete | 100% |
| Training Tab Controls | ✅ Added | 100% |
| Show/Hide Logic | ⏳ Pending | 0% |
| Data Loading | ⏳ Pending | 0% |
| Training Execution | ⏳ Pending | 0% |
| Results Display | ⏳ Pending | 0% |

**Overall Phase 6 Progress: ~40%**

---

## 🎯 **Next Steps (In Order)**

1. Add `_update_training_controls_for_pipeline_mode()` method
2. Call it in `__init__` and when panel loads
3. Implement `_load_data_for_training()` for windows
4. Update `_start_training()` to branch ML/DL
5. Implement `_start_dl_training()` with TimesNetTrainer
6. Test end-to-end DL training workflow
7. Update evaluation tab for DL results

---

## 💡 **Implementation Tips**

### Finding Existing Code
```bash
# Find _start_training method
grep -n "def _start_training" ui/model_panel.py

# Find data loading code
grep -n "Load features" ui/model_panel.py

# Find evaluation update
grep -n "_update_evaluation" ui/model_panel.py
```

### Testing DL Mode
1. Create new project
2. Select "Deep Learning" in Data Sources
3. Load data and create windows
4. Go to Training panel
5. Should see: TimesNet in Algorithm tab
6. Should see: Epochs, Batch Size, LR in Training tab
7. Train model
8. Check ONNX export in output folder

---

## 📁 **Files Needing Modification**

| File | Lines to Modify | Priority | Difficulty |
|------|----------------|----------|------------|
| `ui/model_panel.py` | 56-58 (add init call) | High | Easy |
| `ui/model_panel.py` | 432+ (add show/hide method) | High | Easy |
| `ui/model_panel.py` | 560+ (update _start_training) | Critical | Medium |
| `ui/model_panel.py` | New method (_start_dl_training) | Critical | Medium |
| `ui/model_panel.py` | 1340+ (update data loading) | Critical | Medium |
| `ui/model_panel.py` | Evaluation tab (update display) | Medium | Easy |

---

**Estimated Time to Complete Phase 6:** 2-3 hours
**Blockers:** None - all infrastructure ready
**Risk:** Low - well-defined tasks

---

**Last Updated:** 2025-12-14
**Resume Point:** Implement show/hide logic for controls

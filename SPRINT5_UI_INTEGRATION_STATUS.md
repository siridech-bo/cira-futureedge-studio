# 🎨 Sprint 5: UI Integration - PARTIAL COMPLETE

**Date:** 2025-12-12
**Status:** IN PROGRESS (Data Panel Complete, Model Panel Pending)

---

## ✅ **COMPLETED: Data Panel Task Mode Selection**

### **1. Task Mode Selector Added**
**Location:** [ui/data_panel.py:81-108](ui/data_panel.py#L81-L108)

**UI Components Added:**
- ✅ Segmented button for "Anomaly Detection" vs "Classification"
- ✅ Info label that updates based on mode
- ✅ Callback handler `_on_task_mode_change()`

**Code:**
```python
# Task Mode selection (NEW - Classification vs Anomaly Detection)
task_mode_frame = ctk.CTkFrame(tab, fg_color=("gray90", "gray20"))
task_mode_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
task_mode_frame.grid_columnconfigure(1, weight=1)

ctk.CTkLabel(
    task_mode_frame,
    text="🎯 Task Mode:",
    font=("Segoe UI", 14, "bold")
).grid(row=0, column=0, padx=10, pady=10, sticky="w")

self.task_mode_var = ctk.StringVar(value="anomaly_detection")
task_mode_selector = ctk.CTkSegmentedButton(
    task_mode_frame,
    variable=self.task_mode_var,
    values=["Anomaly Detection", "Classification"],
    command=self._on_task_mode_change
)
task_mode_selector.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

# Info label for task mode
self.task_mode_info = ctk.CTkLabel(
    task_mode_frame,
    text="ℹ️ Detects unusual patterns in unlabeled data",
    font=("Segoe UI", 10),
    text_color=("gray50", "gray60")
)
self.task_mode_info.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")
```

**Callback Handler:**
```python
def _on_task_mode_change(self, choice: str) -> None:
    """Handle task mode change between Anomaly Detection and Classification."""
    mode = "classification" if choice == "Classification" else "anomaly_detection"
    logger.info(f"Task mode changed to: {mode}")

    # Update project task type
    if self.project_manager.current_project:
        self.project_manager.current_project.data.task_type = mode
        self.project_manager.save_current_project()

    # Update info text
    if mode == "classification":
        self.task_mode_info.configure(
            text="ℹ️ Trains models to categorize data into predefined classes (requires labeled data)"
        )
    else:
        self.task_mode_info.configure(
            text="ℹ️ Detects unusual patterns in unlabeled data"
        )
```

**Functionality:**
- ✅ Updates `project.data.task_type` to "classification" or "anomaly_detection"
- ✅ Saves project automatically
- ✅ Updates info text to explain current mode

---

## ⏳ **PENDING: Model Panel Integration**

The Model Panel ([ui/model_panel.py](ui/model_panel.py)) currently only supports anomaly detection with PyOD algorithms. It needs to be updated to support both modes.

### **Required Changes:**

#### **1. Import ClassificationTrainer**
**Location:** Top of [ui/model_panel.py](ui/model_panel.py)

```python
from core.model_trainer import ModelTrainer, TrainingConfig, ALGORITHMS
from core.classification_trainer import ClassificationTrainer, ClassificationConfig, CLASSIFIERS  # ADD THIS
```

#### **2. Add Mode Detection**
**Location:** `ModelPanel.__init__()`

```python
def __init__(self, parent, project_manager: ProjectManager):
    """Initialize the model panel."""
    super().__init__(parent)
    self.project_manager = project_manager

    # Initialize both trainers
    self.anomaly_trainer = ModelTrainer()
    self.classification_trainer = ClassificationTrainer()  # NEW

    self.training_results = None
    self.features_df = None
    self.selected_features = []
```

#### **3. Update Algorithm Tab**
**Location:** `_create_algorithm_tab()`

The title and algorithm selection needs to be dynamic based on task mode:

```python
def _create_algorithm_tab(self):
    """Create algorithm selection tab."""
    tab = self.notebook.tab("Algorithm")
    tab.grid_columnconfigure(0, weight=1)

    # Check task mode from project
    task_mode = self.project_manager.current_project.data.task_type if self.project_manager.current_project else "anomaly_detection"

    # Title (dynamic)
    if task_mode == "classification":
        title_text = "Select Classification Algorithm"
    else:
        title_text = "Select Anomaly Detection Algorithm"

    title = ctk.CTkLabel(
        tab,
        text=title_text,
        font=ctk.CTkFont(size=16, weight="bold")
    )
    title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

    # ... rest of algorithm selection ...
    # Show ALGORITHMS (anomaly) or CLASSIFIERS (classification) based on mode
```

#### **4. Create Algorithm Cards Dynamically**
**Location:** `_create_algorithm_tab()`

Currently creates cards for `ALGORITHMS` (PyOD). Need to check task mode and create cards from `CLASSIFIERS` if in classification mode:

```python
# Get algorithms based on task mode
if task_mode == "classification":
    algorithms = CLASSIFIERS
else:
    algorithms = ALGORITHMS

# Create algorithm cards
for algo_key, algo_info in algorithms.items():
    card = self._create_algorithm_card(
        selection_frame,
        algo_key,
        algo_info,
        task_mode  # Pass task mode
    )
    card.pack(fill="x", padx=10, pady=5)
```

#### **5. Update Training Logic**
**Location:** `_train_model()` method

Need to branch training based on task mode:

```python
def _train_model(self):
    """Train the model."""
    # ... load features and selected features ...

    task_mode = self.project_manager.current_project.data.task_type

    if task_mode == "classification":
        # Get window labels
        windows = self.project_manager.current_project.load_windows()
        labels = np.array([w.class_label for w in windows])

        # Create classification config
        config = ClassificationConfig(
            algorithm=self.selected_algorithm,
            test_size=0.3,
            normalize=True
        )

        # Train classifier
        results = self.classification_trainer.train(
            features_df=self.features_df,
            selected_features=self.selected_features,
            labels=labels,
            config=config,
            output_dir=self.project_manager.current_project.get_models_dir()
        )

        # Save results to project
        self.project_manager.current_project.model.model_type = "classifier"
        self.project_manager.current_project.model.num_classes = results.n_classes
        self.project_manager.current_project.model.class_names = results.class_names
        self.project_manager.current_project.model.confusion_matrix = results.confusion_matrix
        self.project_manager.current_project.model.per_class_metrics = {
            "precision": results.per_class_precision,
            "recall": results.per_class_recall,
            "f1": results.per_class_f1
        }

    else:
        # Existing anomaly detection training
        config = TrainingConfig(
            algorithm=self.selected_algorithm,
            contamination=0.1
        )

        results = self.anomaly_trainer.train(
            features_df=self.features_df,
            selected_features=self.selected_features,
            config=config,
            output_dir=self.project_manager.current_project.get_models_dir()
        )
```

#### **6. Update Evaluation Tab**
**Location:** `_create_evaluation_tab()`

Need to show different metrics based on task mode:

**For Anomaly Detection:**
- Precision
- Recall
- F1-Score
- Number of anomalies detected

**For Classification:**
- Accuracy
- Per-class Precision/Recall/F1
- Confusion Matrix Heatmap (use `ConfusionMatrixWidget`)
- Feature Importance Chart (use `FeatureImportanceChart`)

```python
def _create_evaluation_tab(self):
    """Create evaluation tab."""
    tab = self.notebook.tab("Evaluation")
    tab.grid_columnconfigure(0, weight=1)
    tab.grid_rowconfigure(1, weight=1)

    task_mode = self.project_manager.current_project.data.task_type if self.project_manager.current_project else "anomaly_detection"

    if task_mode == "classification":
        # Classification metrics
        metrics_frame = ctk.CTkFrame(tab)
        metrics_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=10)

        # Overall metrics
        self.accuracy_label = ctk.CTkLabel(metrics_frame, text="Accuracy: -")
        self.precision_label = ctk.CTkLabel(metrics_frame, text="Precision (macro): -")
        self.recall_label = ctk.CTkLabel(metrics_frame, text="Recall (macro): -")
        self.f1_label = ctk.CTkLabel(metrics_frame, text="F1 Score (macro): -")

        # Confusion Matrix Widget
        from ui.widgets import ConfusionMatrixWidget
        self.confusion_matrix_widget = ConfusionMatrixWidget(tab, width=500, height=500)
        self.confusion_matrix_widget.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

    else:
        # Existing anomaly detection metrics
        # ...existing code...
```

#### **7. Add Feature Importance Visualization**
**Location:** Add new tab or section in Evaluation tab

```python
from ui.widgets import FeatureImportanceChart

# In evaluation tab for classification mode
if self.training_results and self.training_results.feature_importances:
    importance_chart = FeatureImportanceChart(tab, width=600, height=400)
    importance_chart.grid(row=2, column=0, sticky="ew", padx=20, pady=10)

    feature_names = list(self.training_results.feature_importances.keys())
    importances = np.array(list(self.training_results.feature_importances.values()))

    importance_chart.plot_importance(feature_names, importances, top_n=20)
```

---

## 📊 **Files Modified**

### **Completed:**
1. ✅ [ui/data_panel.py](ui/data_panel.py) - Added task mode selector

### **Pending:**
2. ⏳ [ui/model_panel.py](ui/model_panel.py) - Needs classification support
3. ⏳ Integration of visualization widgets

---

## 🚀 **Next Steps (In Order)**

### **Step 1: Update Model Panel Imports**
Add `ClassificationTrainer` and `CLASSIFIERS` imports

### **Step 2: Make Algorithm Tab Dynamic**
- Check `project.data.task_mode`
- Show appropriate algorithms (ALGORITHMS vs CLASSIFIERS)
- Update title and descriptions

### **Step 3: Update Training Logic**
- Branch on task_mode in `_train_model()`
- Use `ClassificationTrainer` for classification mode
- Extract labels from windows for classification

### **Step 4: Update Evaluation Tab**
- Show classification metrics when in classification mode
- Integrate `ConfusionMatrixWidget`
- Integrate `FeatureImportanceChart`

### **Step 5: Add Class Distribution Visualization to Data Panel**
- In Data Panel preview tab, show class distribution bar chart when windowing creates labeled windows
- Use `ClassDistributionChart` widget

### **Step 6: Test End-to-End**
- Load your motion dataset (idle/snake/ingestion)
- Select "Classification" mode
- Load data with label extraction
- Create windows (labels preserved via majority voting)
- Extract features
- Train Random Forest classifier
- View confusion matrix and metrics

---

## 💡 **Design Decisions**

1. **Segmented Button for Mode Selection**
   - Provides clear visual distinction between modes
   - Located at top of Data Panel for visibility

2. **Single Model Panel for Both Modes**
   - Avoids code duplication
   - Dynamic content based on `project.data.task_type`

3. **Automatic Project Save**
   - Task mode changes immediately save to project
   - Ensures consistency across sessions

4. **Reuse Visualization Widgets**
   - `ConfusionMatrixWidget` - already created in Sprint 3
   - `FeatureImportanceChart` - already created in Sprint 3
   - No new widgets needed!

---

## 📝 **Implementation Template**

For quick copy-paste, here's a template for the model panel training logic:

```python
def _train_model(self):
    """Train model (anomaly detection or classification based on task mode)."""
    if not self.features_df or not self.selected_features:
        messagebox.showerror("Error", "Features not loaded")
        return

    project = self.project_manager.current_project
    if not project:
        messagebox.showerror("Error", "No project loaded")
        return

    task_mode = project.data.task_type
    logger.info(f"Training in {task_mode} mode")

    try:
        if task_mode == "classification":
            # CLASSIFICATION MODE
            windows = project.load_windows()
            if not windows:
                messagebox.showerror("Error", "No windows found")
                return

            labels = np.array([w.class_label for w in windows])
            if labels[0] is None:
                messagebox.showerror("Error", "No class labels found in windows. Enable label extraction in Data panel.")
                return

            config = ClassificationConfig(
                algorithm=self.selected_algorithm,
                test_size=0.3,
                normalize=True,
                params={}  # Use defaults
            )

            results = self.classification_trainer.train(
                features_df=self.features_df,
                selected_features=self.selected_features,
                labels=labels,
                config=config,
                output_dir=project.get_models_dir()
            )

            # Update project
            project.model.model_type = "classifier"
            project.model.algorithm = results.algorithm
            project.model.model_path = results.model_path
            project.model.scaler_path = results.scaler_path
            project.model.label_encoder_path = results.label_encoder_path
            project.model.num_classes = results.n_classes
            project.model.class_names = results.class_names
            project.model.confusion_matrix = results.confusion_matrix
            project.model.per_class_metrics = {
                "precision": results.per_class_precision,
                "recall": results.per_class_recall,
                "f1": results.per_class_f1
            }
            project.model.metrics = {
                "accuracy": results.accuracy,
                "precision_macro": results.precision_macro,
                "recall_macro": results.recall_macro,
                "f1_macro": results.f1_macro
            }
            project.model.trained = True

            # Update UI
            self.accuracy_label.configure(text=f"Accuracy: {results.accuracy:.1%}")
            self.precision_label.configure(text=f"Precision: {results.precision_macro:.1%}")
            self.recall_label.configure(text=f"Recall: {results.recall_macro:.1%}")
            self.f1_label.configure(text=f"F1 Score: {results.f1_macro:.1%}")

            # Plot confusion matrix
            if hasattr(self, 'confusion_matrix_widget'):
                self.confusion_matrix_widget.plot_confusion_matrix(
                    confusion_matrix=np.array(results.confusion_matrix),
                    class_names=results.class_names
                )

            messagebox.showinfo("Success", f"Classification model trained!\nAccuracy: {results.accuracy:.1%}")

        else:
            # ANOMALY DETECTION MODE (existing code)
            config = TrainingConfig(
                algorithm=self.selected_algorithm,
                contamination=0.1
            )

            results = self.anomaly_trainer.train(
                features_df=self.features_df,
                selected_features=self.selected_features,
                config=config,
                output_dir=project.get_models_dir()
            )

            # ... existing anomaly detection result handling ...

    except Exception as e:
        logger.error(f"Training failed: {e}")
        messagebox.showerror("Training Error", str(e))
```

---

## 🎯 **Success Criteria**

Sprint 5 will be **100% complete** when:

- ✅ Task mode selector works in Data Panel (DONE)
- ⏳ Model Panel shows classifiers when in classification mode
- ⏳ Training logic branches correctly based on task mode
- ⏳ Confusion matrix displays after classification training
- ⏳ Feature importance chart displays (for tree-based classifiers)
- ⏳ End-to-end test with user's motion dataset succeeds

---

**Current Progress: 20%** (Data Panel complete, Model Panel pending)

**Estimated Time to Complete:** 2-3 hours for remaining Model Panel integration

---

For questions or to continue implementation, reference this document and the Sprint 4 documentation ([SPRINT4_CLASSIFICATION_COMPLETE.md](SPRINT4_CLASSIFICATION_COMPLETE.md)).

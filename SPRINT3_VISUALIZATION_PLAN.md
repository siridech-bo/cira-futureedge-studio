# Sprint 3: Visualization Implementation Plan

**Library Choice:** Matplotlib + Seaborn (Modern Style)
**Status:** IN PROGRESS

---

## 🎨 **Modern Plot Styling**

All plots will use a consistent modern style:

```python
# Dark theme-aware colors
COLORS = {
    'primary': '#3B82F6',      # Blue
    'success': '#10B981',      # Green
    'warning': '#F59E0B',      # Amber
    'danger': '#EF4444',       # Red
    'purple': '#8B5CF6',
    'pink': '#EC4899',
    'teal': '#14B8A6',
}

# Plot style
plt.style.use('seaborn-v0_8-darkgrid')
matplotlib.rcParams.update({
    'figure.facecolor': '#1E1E1E',  # Dark background
    'axes.facecolor': '#2D2D2D',
    'axes.edgecolor': '#666666',
    'axes.labelcolor': '#E0E0E0',
    'text.color': '#E0E0E0',
    'xtick.color': '#E0E0E0',
    'ytick.color': '#E0E0E0',
    'grid.color': '#444444',
    'grid.alpha': 0.3,
})
```

---

## 📊 **Widget 1: SensorPlotWidget**

**File:** `ui/widgets/sensor_plot.py`
**Purpose:** Multi-sensor time-series visualization with interactive features

### Features:
- ✅ Multiple sensor traces on same plot
- ✅ Color-coded legend
- ✅ Interactive zoom/pan (matplotlib navigation toolbar)
- ✅ Window selection tool (rectangle selector)
- ✅ Responsive to theme changes

### Implementation:
```python
class SensorPlotWidget(ctk.CTkFrame):
    def __init__(self, parent, width=800, height=400):
        # Create matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(10, 5))

        # Embed in CustomTkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self)

    def plot_sensors(self, df, sensor_columns, time_column=None):
        # Plot each sensor with different color
        for i, sensor in enumerate(sensor_columns):
            self.ax.plot(df.index, df[sensor], label=sensor,
                        color=COLORS[i % len(COLORS)])

        self.ax.legend()
        self.ax.set_xlabel('Sample Index')
        self.ax.set_ylabel('Sensor Value')
        self.canvas.draw()
```

---

## 📊 **Widget 2: ClassDistributionChart**

**File:** `ui/widgets/class_distribution.py`
**Purpose:** Bar chart showing sample count per class

### Features:
- ✅ Horizontal bar chart
- ✅ Color-coded by class
- ✅ Annotated with exact counts
- ✅ Sorted by count (descending)

### Implementation:
```python
class ClassDistributionChart(ctk.CTkFrame):
    def plot_distribution(self, class_counts: Dict[str, int]):
        # Sort by count
        sorted_classes = sorted(class_counts.items(),
                               key=lambda x: x[1], reverse=True)

        classes = [c[0] for c in sorted_classes]
        counts = [c[1] for c in sorted_classes]

        # Horizontal bar chart
        bars = self.ax.barh(classes, counts, color=COLORS['primary'])

        # Annotate with counts
        for i, (cls, count) in enumerate(zip(classes, counts)):
            self.ax.text(count + max(counts)*0.01, i, str(count),
                        va='center', fontweight='bold')
```

---

## 📊 **Widget 3: WindowingVisualization**

**File:** `ui/widgets/windowing_viz.py`
**Purpose:** Show how continuous data is segmented into windows

### Features:
- ✅ Timeline view with window boxes
- ✅ Overlap regions highlighted
- ✅ Color-coded by class label (if classification mode)
- ✅ Interactive window selection

### Implementation:
```python
class WindowingVisualization(ctk.CTkFrame):
    def plot_windows(self, data_length, window_size, overlap, labels=None):
        # Calculate window start positions
        step = int(window_size * (1 - overlap))
        window_starts = range(0, data_length - window_size + 1, step)

        # Draw each window as a rectangle
        for i, start in enumerate(window_starts):
            color = self._get_color_for_label(labels[i]) if labels else 'blue'
            rect = Rectangle((start, i), window_size, 0.8,
                           facecolor=color, alpha=0.6)
            self.ax.add_patch(rect)
```

---

## 📊 **Widget 4: ConfusionMatrixWidget**

**File:** `ui/widgets/confusion_matrix.py`
**Purpose:** Heatmap for classification results

### Features:
- ✅ Seaborn heatmap
- ✅ Annotated with counts
- ✅ Color gradient (green=high, red=low on diagonal)
- ✅ Percentage and count display

### Implementation:
```python
class ConfusionMatrixWidget(ctk.CTkFrame):
    def plot_confusion_matrix(self, cm, class_names):
        # Create heatmap
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                   xticklabels=class_names, yticklabels=class_names,
                   cbar_kws={'label': 'Count'},
                   linewidths=1, linecolor='gray')

        # Add labels
        self.ax.set_xlabel('Predicted Class', fontsize=12)
        self.ax.set_ylabel('True Class', fontsize=12)
        self.ax.set_title('Confusion Matrix', fontsize=14, fontweight='bold')
```

---

## 📊 **Widget 5: FeatureImportanceChart**

**File:** `ui/widgets/feature_importance.py`
**Purpose:** Bar chart of feature importance scores

### Features:
- ✅ Top N features (default 20)
- ✅ Horizontal bar chart
- ✅ Color gradient by importance
- ✅ Sorted descending

### Implementation:
```python
class FeatureImportanceChart(ctk.CTkFrame):
    def plot_importance(self, feature_names, importances, top_n=20):
        # Sort and take top N
        indices = np.argsort(importances)[::-1][:top_n]
        top_features = [feature_names[i] for i in indices]
        top_importances = [importances[i] for i in indices]

        # Horizontal bar chart
        colors = plt.cm.viridis(np.linspace(0, 1, len(top_features)))
        self.ax.barh(range(len(top_features)), top_importances,
                    color=colors)
        self.ax.set_yticks(range(len(top_features)))
        self.ax.set_yticklabels(top_features)
```

---

## 🔧 **Integration into data_panel.py**

### Add Preview Tab with Graphs:

```python
def _setup_preview_tab(self):
    # Existing info labels...

    # NEW: Add sensor plot
    plot_frame = ctk.CTkFrame(tab)
    plot_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

    self.sensor_plot = SensorPlotWidget(plot_frame, width=800, height=400)
    self.sensor_plot.pack(fill="both", expand=True)

    # NEW: Add class distribution (if classification mode)
    if project.data.task_type == "classification":
        dist_frame = ctk.CTkFrame(tab)
        dist_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)

        self.class_dist_chart = ClassDistributionChart(dist_frame)
        self.class_dist_chart.pack(fill="both", expand=True)
```

### Update _update_preview() method:

```python
def _update_preview(self):
    # ... existing preview code ...

    # NEW: Plot sensor data
    sensor_columns = self.current_data_source.detect_sensor_columns()
    self.sensor_plot.plot_sensors(
        self.loaded_data,
        sensor_columns,
        time_column=self.current_data_source.detect_time_column()
    )

    # NEW: Plot class distribution if labels exist
    if 'class_label' in self.loaded_data.columns:
        class_counts = self.loaded_data['class_label'].value_counts().to_dict()
        self.class_dist_chart.plot_distribution(class_counts)
```

---

## 🔧 **Integration into model_panel.py**

### Add to Evaluation Tab:

```python
def _display_results(self, results):
    # ... existing metric labels ...

    # NEW: Add confusion matrix if classification
    if results.confusion_matrix:
        cm_frame = ctk.CTkFrame(self.results_container)
        cm_frame.grid(row=row, column=0, padx=10, pady=10, sticky="ew")

        cm_widget = ConfusionMatrixWidget(cm_frame)
        cm_widget.plot_confusion_matrix(
            np.array(results.confusion_matrix),
            results.class_names
        )
        cm_widget.pack(fill="both", expand=True)
```

---

## ⚙️ **Theme Integration**

Make plots respect CustomTkinter theme (dark/light):

```python
def _apply_theme_to_plots(self, theme='dark'):
    if theme == 'dark':
        plt.style.use('dark_background')
        bg_color = '#1E1E1E'
        text_color = '#E0E0E0'
    else:
        plt.style.use('default')
        bg_color = '#FFFFFF'
        text_color = '#000000'

    matplotlib.rcParams.update({
        'figure.facecolor': bg_color,
        'axes.facecolor': bg_color,
        'text.color': text_color,
    })
```

---

## 📦 **Files to Create**

1. ✅ `ui/widgets/__init__.py`
2. ⏳ `ui/widgets/sensor_plot.py` (300 lines)
3. ⏳ `ui/widgets/class_distribution.py` (150 lines)
4. ⏳ `ui/widgets/windowing_viz.py` (250 lines)
5. ⏳ `ui/widgets/confusion_matrix.py` (200 lines)
6. ⏳ `ui/widgets/feature_importance.py` (150 lines)

**Total: ~1050 lines of visualization code**

---

## 🎯 **Implementation Order**

1. ✅ Create widgets directory structure
2. ✅ Create plot style configuration
3. Create SensorPlotWidget (PRIORITY 1)
4. Create ClassDistributionChart (PRIORITY 2)
5. Create ConfusionMatrixWidget (PRIORITY 3)
6. Create FeatureImportanceChart
7. Create WindowingVisualization
8. Integrate into data_panel.py
9. Integrate into model_panel.py
10. Test with sample data

---

**Status:** Directory created, starting widget implementation...
**Next:** Implement SensorPlotWidget for time-series visualization

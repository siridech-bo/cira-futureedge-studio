# TimesNet Period Configuration Implementation Plan

## Overview

Implement a new "Period Configuration" tab in CiRA FES between "Algorithm" and "Training" tabs to provide frequency analysis and period configuration selection for ONNX-compatible TimesNet models.

---

## Implementation Phases

### **Phase 1: Backend - Frequency Analysis Engine**
**Estimated Time**: 4-6 hours

#### 1.1 Create Frequency Analyzer Module
**File**: `D:\CiRA FES\core\frequency_analyzer.py`

```python
"""
Frequency Analysis Module for TimesNet Period Configuration

Analyzes time series data to determine dominant frequencies and
recommend optimal period configurations for ONNX deployment.
"""

import numpy as np
import pickle
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import pandas as pd


@dataclass
class FrequencyStats:
    """Statistics for a single class's frequency distribution."""
    class_name: str
    dominant_freq: float  # Hz
    freq_range: Tuple[float, float]  # (min_hz, max_hz)
    spectral_centroid: float  # Hz
    spectral_bandwidth: float  # Hz
    energy_distribution: Dict[str, float]  # {band_name: energy_percentage}
    sample_count: int


@dataclass
class PeriodConfig:
    """Configuration profile for TimesNet periods."""
    id: str  # 'A', 'B', 'C', etc.
    name: str
    periods: List[int]
    description: str
    best_for: str
    freq_range: Tuple[float, float]  # (min_hz, max_hz)
    color: str  # For UI visualization


class FrequencyAnalyzer:
    """Analyzes time series data frequency characteristics."""

    # Pre-defined period configurations
    STANDARD_CONFIGS = {
        'A': PeriodConfig(
            id='A',
            name='Low Frequency',
            periods=[100, 75, 50, 40, 33],
            description='Optimized for slow movements and postural changes',
            best_for='Idle detection, slow gestures, drift monitoring',
            freq_range=(0.1, 1.0),
            color='#3498db'  # Blue
        ),
        'B': PeriodConfig(
            id='B',
            name='Balanced',
            periods=[100, 50, 25, 20, 16],
            description='General-purpose configuration for mixed gestures',
            best_for='Mixed gesture types, general motion classification',
            freq_range=(0.5, 3.0),
            color='#2ecc71'  # Green
        ),
        'C': PeriodConfig(
            id='C',
            name='High Frequency',
            periods=[50, 25, 12, 8, 6],
            description='Optimized for rapid movements and vibrations',
            best_for='Shaking, rapid gestures, high-frequency patterns',
            freq_range=(2.0, 8.0),
            color='#e74c3c'  # Red
        ),
    }

    def __init__(self, sample_rate: float = 100.0):
        """
        Initialize frequency analyzer.

        Args:
            sample_rate: Sampling rate in Hz (default: 100 Hz)
        """
        self.sample_rate = sample_rate

    def analyze_windows(self, windows_file: Path) -> Dict[str, FrequencyStats]:
        """
        Analyze frequency characteristics of windowed data.

        Args:
            windows_file: Path to pickled windows file (train_windows.pkl or test_windows.pkl)

        Returns:
            Dictionary mapping class names to FrequencyStats
        """
        # Load windows
        with open(windows_file, 'rb') as f:
            windows = pickle.load(f)

        # Group by class
        class_windows = {}
        for w in windows:
            class_name = w.class_label
            if class_name not in class_windows:
                class_windows[class_name] = []

            # Extract numeric sensor data
            if hasattr(w.data, 'select_dtypes'):
                numeric_cols = w.data.select_dtypes(include=[np.number]).columns.tolist()
                sensor_cols = [col for col in numeric_cols if col.lower() not in ['time', 'timestamp']]
                window_array = w.data[sensor_cols].values.astype(np.float32)
            else:
                window_array = np.array(w.data, dtype=np.float32)

            class_windows[class_name].append(window_array)

        # Analyze each class
        results = {}
        for class_name, windows_list in class_windows.items():
            results[class_name] = self._analyze_class(class_name, windows_list)

        return results

    def _analyze_class(self, class_name: str, windows: List[np.ndarray]) -> FrequencyStats:
        """Analyze frequency characteristics for a single class."""
        all_freqs = []
        all_powers = []

        for window in windows:
            # Compute FFT for each channel, average across channels
            fft_results = []
            for channel in range(window.shape[1]):
                signal = window[:, channel]
                fft = np.fft.rfft(signal)
                power = np.abs(fft) ** 2
                fft_results.append(power)

            # Average power across channels
            avg_power = np.mean(fft_results, axis=0)

            # Frequency bins
            freqs = np.fft.rfftfreq(len(signal), d=1.0/self.sample_rate)

            all_freqs.append(freqs)
            all_powers.append(avg_power)

        # Average power spectrum across all windows
        avg_power_spectrum = np.mean(all_powers, axis=0)
        freqs = all_freqs[0]  # Same for all windows

        # Compute statistics
        dominant_idx = np.argmax(avg_power_spectrum[1:]) + 1  # Skip DC component
        dominant_freq = freqs[dominant_idx]

        # Spectral centroid
        spectral_centroid = np.sum(freqs * avg_power_spectrum) / np.sum(avg_power_spectrum)

        # Find frequency range (where power > 5% of max)
        threshold = 0.05 * np.max(avg_power_spectrum)
        active_freqs = freqs[avg_power_spectrum > threshold]
        if len(active_freqs) > 0:
            freq_range = (active_freqs[0], active_freqs[-1])
        else:
            freq_range = (0.0, 0.0)

        # Spectral bandwidth
        spectral_bandwidth = freq_range[1] - freq_range[0]

        # Energy distribution in frequency bands
        bands = {
            'Very Low (0-0.5 Hz)': (0.0, 0.5),
            'Low (0.5-1.5 Hz)': (0.5, 1.5),
            'Medium (1.5-3.0 Hz)': (1.5, 3.0),
            'High (3.0-5.0 Hz)': (3.0, 5.0),
            'Very High (5.0+ Hz)': (5.0, np.inf),
        }

        energy_distribution = {}
        total_energy = np.sum(avg_power_spectrum)

        for band_name, (low, high) in bands.items():
            mask = (freqs >= low) & (freqs < high)
            band_energy = np.sum(avg_power_spectrum[mask])
            energy_distribution[band_name] = (band_energy / total_energy) * 100

        return FrequencyStats(
            class_name=class_name,
            dominant_freq=dominant_freq,
            freq_range=freq_range,
            spectral_centroid=spectral_centroid,
            spectral_bandwidth=spectral_bandwidth,
            energy_distribution=energy_distribution,
            sample_count=len(windows)
        )

    def recommend_config(self, freq_stats: Dict[str, FrequencyStats]) -> Tuple[str, float]:
        """
        Recommend optimal period configuration based on frequency analysis.

        Args:
            freq_stats: Dictionary of frequency statistics per class

        Returns:
            Tuple of (recommended_config_id, confidence_score)
        """
        # Compute overall frequency range weighted by sample count
        total_samples = sum(stats.sample_count for stats in freq_stats.values())

        weighted_min_freq = 0.0
        weighted_max_freq = 0.0

        for stats in freq_stats.values():
            weight = stats.sample_count / total_samples
            weighted_min_freq += stats.freq_range[0] * weight
            weighted_max_freq += stats.freq_range[1] * weight

        overall_range = (weighted_min_freq, weighted_max_freq)
        overall_centroid = sum(
            stats.spectral_centroid * (stats.sample_count / total_samples)
            for stats in freq_stats.values()
        )

        # Score each configuration
        scores = {}
        for config_id, config in self.STANDARD_CONFIGS.items():
            # Check overlap between data range and config range
            overlap_min = max(overall_range[0], config.freq_range[0])
            overlap_max = min(overall_range[1], config.freq_range[1])

            if overlap_max > overlap_min:
                overlap = overlap_max - overlap_min
                config_span = config.freq_range[1] - config.freq_range[0]
                data_span = overall_range[1] - overall_range[0]

                # Overlap score (higher = better)
                overlap_score = overlap / max(config_span, data_span)

                # Centroid score (1.0 if centroid in config range, decays outside)
                if config.freq_range[0] <= overall_centroid <= config.freq_range[1]:
                    centroid_score = 1.0
                else:
                    dist_to_range = min(
                        abs(overall_centroid - config.freq_range[0]),
                        abs(overall_centroid - config.freq_range[1])
                    )
                    centroid_score = np.exp(-dist_to_range)

                # Combined score
                scores[config_id] = 0.6 * overlap_score + 0.4 * centroid_score
            else:
                scores[config_id] = 0.0

        # Get best config
        best_config_id = max(scores, key=scores.get)
        confidence = scores[best_config_id]

        return best_config_id, confidence

    def get_config(self, config_id: str) -> PeriodConfig:
        """Get period configuration by ID."""
        return self.STANDARD_CONFIGS.get(config_id)

    def get_all_configs(self) -> Dict[str, PeriodConfig]:
        """Get all available period configurations."""
        return self.STANDARD_CONFIGS.copy()


def generate_frequency_report(
    windows_file: Path,
    sample_rate: float = 100.0
) -> Tuple[Dict[str, FrequencyStats], str, float]:
    """
    Generate frequency analysis report for windowed data.

    Args:
        windows_file: Path to pickled windows file
        sample_rate: Sampling rate in Hz

    Returns:
        Tuple of (freq_stats, recommended_config_id, confidence)
    """
    analyzer = FrequencyAnalyzer(sample_rate=sample_rate)
    freq_stats = analyzer.analyze_windows(windows_file)
    recommended_config, confidence = analyzer.recommend_config(freq_stats)

    return freq_stats, recommended_config, confidence
```

**Tasks**:
- [ ] Create `core/frequency_analyzer.py`
- [ ] Implement `FrequencyAnalyzer` class with FFT analysis
- [ ] Define 3 standard period configurations (A, B, C)
- [ ] Implement recommendation algorithm
- [ ] Add unit tests for frequency analysis

---

### **Phase 2: UI - Period Configuration Tab**
**Estimated Time**: 8-10 hours

#### 2.1 Create Period Config Panel
**File**: `D:\CiRA FES\ui\period_config_panel.py`

```python
"""
Period Configuration Panel for TimesNet

Provides UI for frequency analysis, visualization, and period configuration selection.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from pathlib import Path
from typing import Optional, Dict

from core.frequency_analyzer import (
    FrequencyAnalyzer, FrequencyStats, PeriodConfig,
    generate_frequency_report
)


class PeriodConfigPanel(ttk.Frame):
    """Panel for period configuration selection and frequency analysis."""

    def __init__(self, parent, project):
        super().__init__(parent)
        self.project = project
        self.analyzer = FrequencyAnalyzer(sample_rate=100.0)

        # Analysis results
        self.freq_stats: Optional[Dict[str, FrequencyStats]] = None
        self.recommended_config_id: Optional[str] = None
        self.recommended_confidence: float = 0.0
        self.selected_config_id: str = 'B'  # Default to Balanced

        self._create_widgets()
        self._load_analysis()

    def _create_widgets(self):
        """Create UI widgets."""
        # Main container
        main_container = ttk.Frame(self, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(1, weight=1)

        # Title
        title_frame = ttk.Frame(main_container)
        title_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        title = ttk.Label(
            title_frame,
            text="Period Configuration for ONNX Deployment",
            font=('Segoe UI', 12, 'bold')
        )
        title.pack(side=tk.LEFT)

        # Info button
        info_btn = ttk.Button(
            title_frame,
            text="ℹ Info",
            command=self._show_info,
            width=8
        )
        info_btn.pack(side=tk.RIGHT)

        # Main content - split into left (analysis) and right (config selection)
        content_paned = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        content_paned.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Left panel - Frequency analysis
        self._create_analysis_panel(content_paned)

        # Right panel - Configuration selection
        self._create_config_panel(content_paned)

        # Bottom status bar
        status_frame = ttk.Frame(main_container)
        status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

        self.status_label = ttk.Label(
            status_frame,
            text="Ready",
            foreground='green'
        )
        self.status_label.pack(side=tk.LEFT)

        # Refresh button
        refresh_btn = ttk.Button(
            status_frame,
            text="🔄 Refresh Analysis",
            command=self._refresh_analysis
        )
        refresh_btn.pack(side=tk.RIGHT)

    def _create_analysis_panel(self, parent):
        """Create frequency analysis visualization panel."""
        analysis_frame = ttk.LabelFrame(parent, text="Frequency Analysis", padding="10")
        parent.add(analysis_frame, weight=2)

        # Analysis status
        self.analysis_status = ttk.Label(
            analysis_frame,
            text="No analysis available. Please create windows first.",
            foreground='gray'
        )
        self.analysis_status.pack(pady=10)

        # Matplotlib figure for frequency visualization
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=analysis_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Class details text
        details_frame = ttk.LabelFrame(analysis_frame, text="Per-Class Statistics", padding="10")
        details_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # Scrollable text widget
        text_scroll = ttk.Scrollbar(details_frame)
        text_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.details_text = tk.Text(
            details_frame,
            height=8,
            wrap=tk.WORD,
            yscrollcommand=text_scroll.set,
            font=('Consolas', 9)
        )
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_scroll.config(command=self.details_text.yview)

    def _create_config_panel(self, parent):
        """Create configuration selection panel."""
        config_frame = ttk.LabelFrame(parent, text="Period Configuration", padding="10")
        parent.add(config_frame, weight=1)

        # Recommendation section
        rec_frame = ttk.LabelFrame(config_frame, text="Recommended Configuration", padding="10")
        rec_frame.pack(fill=tk.X, pady=(0, 10))

        self.rec_config_label = ttk.Label(
            rec_frame,
            text="Config B: Balanced",
            font=('Segoe UI', 11, 'bold'),
            foreground='green'
        )
        self.rec_config_label.pack(anchor=tk.W)

        self.rec_confidence_label = ttk.Label(
            rec_frame,
            text="Confidence: N/A",
            foreground='gray'
        )
        self.rec_confidence_label.pack(anchor=tk.W)

        self.rec_reason_label = ttk.Label(
            rec_frame,
            text="Reason: Not yet analyzed",
            wraplength=300,
            justify=tk.LEFT
        )
        self.rec_reason_label.pack(anchor=tk.W, pady=(5, 0))

        # Manual selection section
        select_frame = ttk.LabelFrame(config_frame, text="Manual Selection", padding="10")
        select_frame.pack(fill=tk.BOTH, expand=True)

        # Radio buttons for config selection
        self.config_var = tk.StringVar(value='B')

        for config_id, config in self.analyzer.get_all_configs().items():
            radio_frame = ttk.Frame(select_frame)
            radio_frame.pack(fill=tk.X, pady=5)

            radio = ttk.Radiobutton(
                radio_frame,
                text=f"Config {config.id}: {config.name}",
                variable=self.config_var,
                value=config.id,
                command=self._on_config_selected
            )
            radio.pack(anchor=tk.W)

            # Config details
            details = ttk.Label(
                radio_frame,
                text=f"  Periods: {config.periods}\n  {config.description}\n  Frequency: {config.freq_range[0]}-{config.freq_range[1]} Hz",
                foreground='gray',
                font=('Segoe UI', 8)
            )
            details.pack(anchor=tk.W, padx=(20, 0))

            ttk.Separator(select_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # Custom config (future feature)
        custom_frame = ttk.Frame(select_frame)
        custom_frame.pack(fill=tk.X, pady=5)

        custom_label = ttk.Label(
            custom_frame,
            text="Custom periods (comma-separated):",
            foreground='gray'
        )
        custom_label.pack(anchor=tk.W)

        self.custom_periods_entry = ttk.Entry(custom_frame, state='disabled')
        self.custom_periods_entry.pack(fill=tk.X)

        custom_hint = ttk.Label(
            custom_frame,
            text="(Coming in future version)",
            foreground='lightgray',
            font=('Segoe UI', 8)
        )
        custom_hint.pack(anchor=tk.W)

    def _load_analysis(self):
        """Load frequency analysis from windows data."""
        if not self.project.data.train_windows_file:
            self.analysis_status.config(
                text="No training data available. Please create windows first.",
                foreground='orange'
            )
            return

        try:
            # Run frequency analysis
            self.freq_stats, self.recommended_config_id, self.recommended_confidence = \
                generate_frequency_report(
                    Path(self.project.data.train_windows_file),
                    sample_rate=100.0
                )

            # Update UI
            self._update_analysis_display()
            self._update_recommendation_display()

            self.status_label.config(
                text=f"Analysis complete: {len(self.freq_stats)} classes analyzed",
                foreground='green'
            )

        except Exception as e:
            messagebox.showerror("Analysis Error", f"Failed to analyze frequency data:\n{str(e)}")
            self.status_label.config(
                text="Analysis failed",
                foreground='red'
            )

    def _update_analysis_display(self):
        """Update frequency analysis visualization."""
        if not self.freq_stats:
            return

        self.analysis_status.config(
            text=f"Analyzed {len(self.freq_stats)} classes from {sum(s.sample_count for s in self.freq_stats.values())} samples",
            foreground='green'
        )

        # Clear previous plots
        self.fig.clear()

        # Create subplots
        ax1 = self.fig.add_subplot(211)  # Energy distribution
        ax2 = self.fig.add_subplot(212)  # Frequency ranges

        # Plot 1: Energy distribution by frequency band
        classes = list(self.freq_stats.keys())
        bands = ['Very Low (0-0.5 Hz)', 'Low (0.5-1.5 Hz)', 'Medium (1.5-3.0 Hz)',
                'High (3.0-5.0 Hz)', 'Very High (5.0+ Hz)']

        x = np.arange(len(classes))
        width = 0.15

        for i, band in enumerate(bands):
            energies = [self.freq_stats[cls].energy_distribution[band] for cls in classes]
            offset = (i - 2) * width
            ax1.bar(x + offset, energies, width, label=band)

        ax1.set_xlabel('Class')
        ax1.set_ylabel('Energy (%)')
        ax1.set_title('Energy Distribution by Frequency Band')
        ax1.set_xticks(x)
        ax1.set_xticklabels(classes, rotation=45, ha='right')
        ax1.legend(fontsize=8, loc='upper right')
        ax1.grid(True, alpha=0.3)

        # Plot 2: Frequency ranges with config overlays
        for i, cls in enumerate(classes):
            stats = self.freq_stats[cls]
            # Dominant frequency
            ax2.plot(i, stats.dominant_freq, 'ro', markersize=8, label='Dominant' if i == 0 else '')
            # Frequency range
            ax2.plot([i, i], stats.freq_range, 'b-', linewidth=2, label='Range' if i == 0 else '')

        # Overlay config ranges
        configs = self.analyzer.get_all_configs()
        for config_id, config in configs.items():
            ax2.axhspan(config.freq_range[0], config.freq_range[1],
                       alpha=0.2, color=config.color,
                       label=f'Config {config.id} ({config.name})')

        ax2.set_xlabel('Class')
        ax2.set_ylabel('Frequency (Hz)')
        ax2.set_title('Frequency Ranges vs Configuration Coverage')
        ax2.set_xticks(range(len(classes)))
        ax2.set_xticklabels(classes, rotation=45, ha='right')
        ax2.legend(fontsize=8, loc='upper right')
        ax2.grid(True, alpha=0.3)

        self.fig.tight_layout()
        self.canvas.draw()

        # Update details text
        self.details_text.delete('1.0', tk.END)
        for cls, stats in self.freq_stats.items():
            self.details_text.insert(tk.END, f"{'='*50}\n")
            self.details_text.insert(tk.END, f"Class: {cls} ({stats.sample_count} samples)\n")
            self.details_text.insert(tk.END, f"  Dominant Frequency: {stats.dominant_freq:.2f} Hz\n")
            self.details_text.insert(tk.END, f"  Frequency Range: {stats.freq_range[0]:.2f} - {stats.freq_range[1]:.2f} Hz\n")
            self.details_text.insert(tk.END, f"  Spectral Centroid: {stats.spectral_centroid:.2f} Hz\n")
            self.details_text.insert(tk.END, f"  Bandwidth: {stats.spectral_bandwidth:.2f} Hz\n\n")

    def _update_recommendation_display(self):
        """Update recommendation display."""
        if not self.recommended_config_id:
            return

        config = self.analyzer.get_config(self.recommended_config_id)

        self.rec_config_label.config(
            text=f"Config {config.id}: {config.name}",
            foreground=config.color
        )

        confidence_pct = self.recommended_confidence * 100
        confidence_text = f"Confidence: {confidence_pct:.1f}%"
        if confidence_pct >= 80:
            confidence_color = 'green'
        elif confidence_pct >= 60:
            confidence_color = 'orange'
        else:
            confidence_color = 'red'

        self.rec_confidence_label.config(
            text=confidence_text,
            foreground=confidence_color
        )

        # Generate reason
        if self.freq_stats:
            total_samples = sum(s.sample_count for s in self.freq_stats.values())
            weighted_min = sum(s.freq_range[0] * s.sample_count / total_samples for s in self.freq_stats.values())
            weighted_max = sum(s.freq_range[1] * s.sample_count / total_samples for s in self.freq_stats.values())

            reason = (f"Your data spans {weighted_min:.2f}-{weighted_max:.2f} Hz, "
                     f"which aligns well with {config.name} ({config.freq_range[0]}-{config.freq_range[1]} Hz). "
                     f"{config.best_for}.")
        else:
            reason = "No analysis data available."

        self.rec_reason_label.config(text=f"Reason: {reason}")

        # Auto-select recommended config
        self.config_var.set(self.recommended_config_id)
        self.selected_config_id = self.recommended_config_id

        # Update project
        if hasattr(self.project, 'timesnet_config'):
            config_obj = self.analyzer.get_config(self.selected_config_id)
            self.project.timesnet_config = {
                'config_id': config_obj.id,
                'config_name': config_obj.name,
                'periods': config_obj.periods
            }

    def _on_config_selected(self):
        """Handle manual config selection."""
        self.selected_config_id = self.config_var.get()
        config = self.analyzer.get_config(self.selected_config_id)

        # Update project
        if hasattr(self.project, 'timesnet_config'):
            self.project.timesnet_config = {
                'config_id': config.id,
                'config_name': config.name,
                'periods': config.periods
            }

        # Show info if user overrides recommendation
        if self.selected_config_id != self.recommended_config_id and self.recommended_config_id:
            self.status_label.config(
                text=f"Manual override: Config {config.id} selected (recommended: {self.recommended_config_id})",
                foreground='orange'
            )
        else:
            self.status_label.config(
                text=f"Config {config.id} selected",
                foreground='green'
            )

    def _refresh_analysis(self):
        """Refresh frequency analysis."""
        self._load_analysis()

    def _show_info(self):
        """Show information dialog."""
        info_text = """Period Configuration for ONNX Deployment

TimesNet uses multi-scale temporal processing with different period lengths.
For ONNX compatibility, we use fixed period configurations instead of adaptive
FFT-based period detection.

This tool analyzes your data's frequency characteristics and recommends the
optimal period configuration for your specific use case.

Configurations:
• Config A (Low Frequency): Best for slow movements, idle detection
• Config B (Balanced): General-purpose, works for most gesture types
• Config C (High Frequency): Best for rapid movements, shaking, vibrations

The frequency analysis shows:
1. Energy distribution across frequency bands for each class
2. Dominant frequencies and ranges per class
3. How well each configuration matches your data

You can manually override the recommendation if you have domain knowledge
about your specific application."""

        messagebox.showinfo("Period Configuration Info", info_text)

    def get_selected_config(self) -> PeriodConfig:
        """Get currently selected period configuration."""
        return self.analyzer.get_config(self.selected_config_id)
```

**Tasks**:
- [ ] Create `ui/period_config_panel.py`
- [ ] Implement frequency visualization with matplotlib
- [ ] Add config selection UI with radio buttons
- [ ] Integrate recommendation display
- [ ] Add info/help dialogs

---

#### 2.2 Integrate into Model Panel Tabs
**File**: `D:\CiRA FES\ui\model_panel.py`

**Modifications**:

```python
# At the top, add import
from ui.period_config_panel import PeriodConfigPanel

# In ModelPanel.__init__, modify tab creation:
def _create_tabs(self):
    """Create tabbed interface for model configuration."""
    self.notebook = ttk.Notebook(self.main_frame)
    self.notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

    # Algorithm tab
    self.algo_frame = ttk.Frame(self.notebook, padding="10")
    self.notebook.add(self.algo_frame, text="Algorithm")
    self._create_algorithm_tab()

    # ✓ NEW: Period Configuration tab (only for TimesNet)
    if self.project.model_config.algorithm == 'timesnet':
        self.period_config_panel = PeriodConfigPanel(self.notebook, self.project)
        self.notebook.add(self.period_config_panel, text="Period Config")

    # Training tab
    self.training_frame = ttk.Frame(self.notebook, padding="10")
    self.notebook.add(self.training_frame, text="Training")
    self._create_training_tab()

    # Evaluation tab
    self.eval_frame = ttk.Frame(self.notebook, padding="10")
    self.notebook.add(self.eval_frame, text="Evaluation")
    self._create_evaluation_tab()

# In _start_dl_training, use selected config:
def _start_dl_training(self):
    # ... existing code ...

    # ✓ NEW: Get selected period configuration
    if hasattr(self, 'period_config_panel'):
        selected_config = self.period_config_panel.get_selected_config()
        periods = selected_config.periods
        print(f"Using period configuration: {selected_config.name} {periods}")
    else:
        # Default periods if panel not available
        periods = [100, 50, 25, 20, 16]

    # Pass periods to trainer config
    config = TimeSeriesConfig(
        # ... existing params ...
        params={'fixed_periods': periods}  # ✓ NEW
    )

    # ... rest of training code ...
```

**Tasks**:
- [ ] Modify `ui/model_panel.py` to add Period Config tab
- [ ] Add conditional tab creation (only for TimesNet)
- [ ] Pass selected config to training process
- [ ] Save selected config in project file

---

### **Phase 3: Backend - Period Configuration in Training**
**Estimated Time**: 2-3 hours

#### 3.1 Update TimesNet Layers to Accept Custom Periods
**File**: `D:\CiRA FES\core\deep_models\layers.py`

**Modifications**:

```python
class TimesBlock(nn.Module):
    """TimesNet temporal modeling block with configurable periods."""

    def __init__(
        self,
        seq_len: int,
        d_model: int,
        d_ff: int,
        num_kernels: int = 6,
        top_k: int = 5,
        fixed_periods: Optional[List[int]] = None  # ✓ NEW
    ):
        super().__init__()
        self.seq_len = seq_len
        self.top_k = top_k

        # ✓ NEW: Store custom periods
        if fixed_periods is not None:
            self.fixed_periods = fixed_periods
        else:
            # Default periods (balanced config)
            self.fixed_periods = [seq_len, seq_len // 2, seq_len // 4,
                                 seq_len // 8, seq_len // 16]

        # Rest of initialization...

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # ... existing FFT code ...

        # ✓ MODIFIED: Use self.fixed_periods instead of hardcoded
        for k in range(min(self.top_k, len(self.fixed_periods))):
            period = max(self.fixed_periods[k], 2)
            # ... rest of processing ...
```

**Tasks**:
- [ ] Modify `TimesBlock.__init__` to accept `fixed_periods` parameter
- [ ] Update `forward()` to use custom periods
- [ ] Add validation for period values

---

#### 3.2 Update TimesNet Model to Pass Periods
**File**: `D:\CiRA FES\core\deep_models\timesnet.py`

**Modifications**:

```python
def create_timesnet_for_classification(
    # ... existing params ...
    fixed_periods: Optional[List[int]] = None  # ✓ NEW
) -> Tuple[TimesNet, TimesNetConfig, str]:
    # ... existing code ...

    # ✓ NEW: Store periods in config
    config.fixed_periods = fixed_periods

    # ... create model ...

    # ✓ MODIFIED: Pass periods to layers
    layers = nn.ModuleList([
        TimesBlock(
            config.seq_len,
            config.d_model,
            config.d_ff,
            config.num_kernels,
            config.top_k,
            fixed_periods=fixed_periods  # ✓ NEW
        )
        for _ in range(config.e_layers)
    ])
```

**Tasks**:
- [ ] Update `create_timesnet_for_classification()` signature
- [ ] Pass `fixed_periods` to `TimesBlock` instances
- [ ] Store periods in saved model config

---

#### 3.3 Update Trainer to Use Config Periods
**File**: `D:\CiRA FES\core\timeseries_trainer.py`

**Modifications**:

```python
def train(self, windows, labels, config, output_dir, progress_callback=None):
    # ... existing code ...

    # ✓ NEW: Extract period configuration
    fixed_periods = config.params.get('fixed_periods', None)
    if fixed_periods:
        logger.info(f"Using custom period configuration: {fixed_periods}")

    # Create model with custom periods
    self.model, model_config, device_desc = create_timesnet_for_classification(
        # ... existing params ...
        fixed_periods=fixed_periods  # ✓ NEW
    )

    # ... rest of training ...
```

**Tasks**:
- [ ] Extract `fixed_periods` from config
- [ ] Pass to model creation
- [ ] Log selected configuration
- [ ] Save in model checkpoint

---

### **Phase 4: Project File Integration**
**Estimated Time**: 2-3 hours

#### 4.1 Update Project Data Model
**File**: `D:\CiRA FES\core\project.py`

**Modifications**:

```python
@dataclass
class ModelConfig:
    """Model configuration."""
    algorithm: str = 'random_forest'
    # ... existing fields ...

    # ✓ NEW: TimesNet period configuration
    timesnet_period_config: Optional[Dict[str, Any]] = None
    # Structure: {
    #     'config_id': 'B',
    #     'config_name': 'Balanced',
    #     'periods': [100, 50, 25, 20, 16],
    #     'auto_selected': True,
    #     'confidence': 0.85
    # }

# In Project class:
def save(self, filepath: str = None):
    # ... existing save code ...

    # ✓ NEW: Include period config in save
    if hasattr(self, 'timesnet_config'):
        self.model_config.timesnet_period_config = self.timesnet_config

    # ... rest of save ...

def load(filepath: str) -> 'Project':
    # ... existing load code ...

    # ✓ NEW: Restore period config
    if hasattr(project.model_config, 'timesnet_period_config'):
        project.timesnet_config = project.model_config.timesnet_period_config

    # ... rest of load ...
```

**Tasks**:
- [ ] Add `timesnet_period_config` field to `ModelConfig`
- [ ] Save/load period config in project file
- [ ] Ensure backward compatibility with old projects

---

### **Phase 5: Testing & Documentation**
**Estimated Time**: 3-4 hours

#### 5.1 Unit Tests
**File**: `D:\CiRA FES\tests\test_frequency_analyzer.py`

```python
import unittest
import numpy as np
from pathlib import Path
from core.frequency_analyzer import FrequencyAnalyzer, generate_frequency_report


class TestFrequencyAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = FrequencyAnalyzer(sample_rate=100.0)

    def test_config_recommendation_low_freq(self):
        """Test recommendation for low-frequency data."""
        # Create mock frequency stats with low-frequency content
        # ...

    def test_config_recommendation_high_freq(self):
        """Test recommendation for high-frequency data."""
        # ...

    def test_fft_analysis(self):
        """Test FFT analysis on synthetic signals."""
        # ...
```

**Tasks**:
- [ ] Create unit tests for `FrequencyAnalyzer`
- [ ] Test recommendation algorithm with synthetic data
- [ ] Test UI components (if feasible)
- [ ] Create integration test with full pipeline

---

#### 5.2 User Documentation
**File**: `D:\CiRA FES\docs\PERIOD_CONFIGURATION_GUIDE.md`

```markdown
# Period Configuration Guide

## Overview
Period configuration allows you to optimize TimesNet for your specific
motion classification task while maintaining ONNX compatibility.

## How It Works
1. CiRA FES analyzes frequency content of your training data
2. Recommends optimal period configuration (A, B, or C)
3. You can accept recommendation or manually override
4. Selected configuration is used for training and ONNX export

## When to Use Each Configuration

### Config A: Low Frequency
- **Best for**: Idle detection, slow movements, postural changes
- **Frequency range**: 0.1 - 1.0 Hz
- **Example use cases**: Sleep monitoring, fall detection, orientation tracking

### Config B: Balanced (Default)
- **Best for**: General-purpose motion classification
- **Frequency range**: 0.5 - 3.0 Hz
- **Example use cases**: Gesture recognition, activity tracking, most applications

### Config C: High Frequency
- **Best for**: Rapid movements, vibrations, shaking
- **Frequency range**: 2.0 - 8.0 Hz
- **Example use cases**: Shake detection, vibration monitoring, rapid gestures

## Workflow
1. Load data and create windows (Data tab)
2. Select TimesNet algorithm (Model tab → Algorithm)
3. View frequency analysis (Model tab → Period Config)
4. Accept recommended config or manually select
5. Proceed to Training tab
```

**Tasks**:
- [ ] Write user guide for period configuration
- [ ] Add screenshots of UI
- [ ] Create troubleshooting section
- [ ] Update main README with new feature

---

## Implementation Timeline

### **Sprint 1 (Week 1): Backend Foundation**
- Days 1-2: Implement `FrequencyAnalyzer` class
- Days 3-4: Update `TimesBlock` and `TimesNet` for custom periods
- Day 5: Testing and bug fixes

### **Sprint 2 (Week 2): UI Development**
- Days 1-3: Build `PeriodConfigPanel` UI
- Day 4: Integrate into `ModelPanel` tabs
- Day 5: UI polish and testing

### **Sprint 3 (Week 3): Integration & Testing**
- Days 1-2: Project file integration
- Days 3-4: End-to-end testing
- Day 5: Documentation and user guide

---

## Testing Checklist

### Functional Testing
- [ ] Frequency analysis runs on windows data
- [ ] Recommendation algorithm selects appropriate config
- [ ] Manual config selection works
- [ ] Selected config persists in project file
- [ ] Training uses selected periods
- [ ] ONNX export includes correct periods
- [ ] Deployed model uses configured periods

### UI Testing
- [ ] Tab appears between Algorithm and Training (TimesNet only)
- [ ] Frequency plots render correctly
- [ ] Per-class statistics display properly
- [ ] Recommendation updates when data changes
- [ ] Manual selection overrides recommendation
- [ ] Info dialog displays

### Edge Cases
- [ ] No training data available
- [ ] Single class (no comparison)
- [ ] All classes same frequency range
- [ ] Very noisy data (no clear peaks)
- [ ] Missing windows file
- [ ] Corrupted data

---

## Success Criteria

1. **Feature Complete**: Period Config tab functional with all UI elements
2. **Accurate Analysis**: Recommendation matches expected config for test datasets
3. **ONNX Compatible**: All configs export cleanly with <1e-5 logit difference
4. **User-Friendly**: Clear visualization and guidance for non-experts
5. **Well-Documented**: User guide with examples and screenshots
6. **Tested**: >90% code coverage, all edge cases handled

---

## Future Enhancements (Post-MVP)

### Phase 4: Advanced Features (Optional)
- [ ] Custom period definition (user-specified periods)
- [ ] Auto-selector generation (lightweight classifier)
- [ ] Multi-config comparison (train all 3, show results)
- [ ] Export multiple ONNX models (one per config)
- [ ] Frequency tracking over time (temporal drift detection)

### Phase 5: Analytics Dashboard
- [ ] Historical config performance tracking
- [ ] Dataset frequency distribution trends
- [ ] Recommended vs actual config effectiveness
- [ ] A/B testing framework for configs

---

## Dependencies

### Required Python Packages
```
numpy>=1.21.0
matplotlib>=3.5.0
scipy>=1.7.0  (for advanced FFT features)
```

### UI Framework
```
tkinter (built-in)
```

### Existing CiRA FES Modules
```
core/project.py
core/timeseries_trainer.py
core/deep_models/timesnet.py
core/deep_models/layers.py
ui/model_panel.py
```

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| FFT analysis too slow | Medium | Cache results, background processing |
| Recommendation inaccurate | High | Allow manual override, show confidence |
| UI complexity confuses users | Medium | Add tooltips, info dialogs, defaults |
| Breaks existing projects | High | Backward compatibility, default config |
| ONNX export still fails | Critical | Extensive validation, multiple test cases |

---

## Rollout Plan

### Phase A: Internal Testing (Week 1)
- Deploy to development environment
- Test with synthetic datasets
- Validate ONNX export

### Phase B: Beta Testing (Week 2)
- Release to select users
- Gather feedback on UI/UX
- Monitor for bugs

### Phase C: Production Release (Week 3)
- Update documentation
- Announce feature
- Provide migration guide

---

## Questions for Discussion

1. **Default Behavior**: Should we auto-select recommended config or let user choose?
   - Proposal: Auto-select with clear indication and easy override

2. **Custom Periods**: Include in MVP or defer to future?
   - Proposal: Defer to Phase 4, focus on 3 standard configs first

3. **Naming Convention**: "Period Config" vs "Frequency Config"?
   - Proposal: "Period Config" (consistent with TimesNet terminology)

4. **Tab Placement**: Before or after Training?
   - Proposal: Before Training (logical flow: Algorithm → Config → Train)

---

*End of Implementation Plan*

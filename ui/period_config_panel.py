"""
Period Configuration Panel for TimesNet

Provides UI for frequency analysis, visualization, and period configuration selection.
"""

import customtkinter as ctk
from tkinter import messagebox
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

# Configure matplotlib for dark theme
plt.style.use('dark_background')


class PeriodConfigPanel(ctk.CTkScrollableFrame):
    """Panel for period configuration selection and frequency analysis."""

    def __init__(self, parent, project):
        super().__init__(parent, fg_color="transparent")
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
        # Configure grid weights for horizontal layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Title section
        self._create_title_section()

        # Left panel - Frequency analysis
        self._create_analysis_panel()

        # Right panel - Configuration selection
        self._create_config_panel()

        # Bottom status bar
        self._create_status_bar()

    def _create_title_section(self):
        """Create title and info section."""
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        title = ctk.CTkLabel(
            title_frame,
            text="Period Configuration for ONNX Deployment",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(side="left")

        info_btn = ctk.CTkButton(
            title_frame,
            text="ℹ Info",
            command=self._show_info,
            width=80,
            height=28
        )
        info_btn.pack(side="right")

    def _create_analysis_panel(self):
        """Create frequency analysis visualization panel."""
        analysis_frame = ctk.CTkFrame(self)
        analysis_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        analysis_frame.grid_columnconfigure(0, weight=1)

        # Title
        ctk.CTkLabel(
            analysis_frame,
            text="Frequency Analysis",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        # Analysis status
        self.analysis_status = ctk.CTkLabel(
            analysis_frame,
            text="No analysis available. Please create windows first.",
            text_color="gray",
            font=ctk.CTkFont(size=11)
        )
        self.analysis_status.grid(row=1, column=0, sticky="w", padx=10, pady=5)

        # Container for matplotlib canvas
        canvas_container = ctk.CTkFrame(analysis_frame, fg_color="#2b2b2b")
        canvas_container.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        # Matplotlib figure - side by side plots (1 row, 2 columns)
        # Wider figure to accommodate two plots side by side
        self.fig = Figure(figsize=(14, 5), dpi=100, facecolor='#2b2b2b')
        self.canvas = FigureCanvasTkAgg(self.fig, master=canvas_container)
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.configure(bg='#2b2b2b')
        canvas_widget.pack(padx=5, pady=5)

        # Class details text
        details_label = ctk.CTkLabel(
            analysis_frame,
            text="Per-Class Statistics",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        details_label.grid(row=3, column=0, sticky="w", padx=10, pady=(10, 5))

        self.details_text = ctk.CTkTextbox(
            analysis_frame,
            height=150,
            font=ctk.CTkFont(family='Consolas', size=11)
        )
        self.details_text.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 10))

    def _create_config_panel(self):
        """Create configuration selection panel."""
        config_frame = ctk.CTkFrame(self)
        config_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        config_frame.grid_columnconfigure(0, weight=1)
        config_frame.grid_columnconfigure(1, weight=2)

        # Title
        ctk.CTkLabel(
            config_frame,
            text="Period Configuration",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))

        # Recommendation section (left side)
        rec_container = ctk.CTkFrame(config_frame)
        rec_container.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=5)

        ctk.CTkLabel(
            rec_container,
            text="Recommended Configuration",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        self.rec_config_label = ctk.CTkLabel(
            rec_container,
            text="Config B: Balanced",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="green"
        )
        self.rec_config_label.pack(anchor="w", padx=10, pady=(5, 2))

        self.rec_confidence_label = ctk.CTkLabel(
            rec_container,
            text="Confidence: N/A",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.rec_confidence_label.pack(anchor="w", padx=10, pady=2)

        self.rec_reason_label = ctk.CTkLabel(
            rec_container,
            text="Reason: Not yet analyzed",
            font=ctk.CTkFont(size=11),
            wraplength=350,
            justify="left"
        )
        self.rec_reason_label.pack(anchor="w", padx=10, pady=(5, 10))

        # Manual selection section (right side)
        select_container = ctk.CTkFrame(config_frame)
        select_container.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=5)

        ctk.CTkLabel(
            select_container,
            text="Manual Selection",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        # Radio buttons for config selection - horizontal layout
        self.config_var = ctk.StringVar(value='B')

        for config_id, config in self.analyzer.get_all_configs().items():
            config_item = ctk.CTkFrame(select_container, fg_color="transparent")
            config_item.pack(fill="x", padx=10, pady=5)

            radio = ctk.CTkRadioButton(
                config_item,
                text=f"Config {config.id}: {config.name}",
                variable=self.config_var,
                value=config.id,
                command=self._on_config_selected,
                font=ctk.CTkFont(size=12, weight="bold")
            )
            radio.pack(anchor="w")

            # Config details
            details_text = f"Periods: {config.periods}\n{config.description}\nFrequency: {config.freq_range[0]}-{config.freq_range[1]} Hz"
            details = ctk.CTkLabel(
                config_item,
                text=details_text,
                text_color="gray",
                font=ctk.CTkFont(size=10),
                justify="left"
            )
            details.pack(anchor="w", padx=(25, 0))

    def _create_status_bar(self):
        """Create bottom status bar."""
        status_frame = ctk.CTkFrame(self, fg_color="transparent")
        status_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))

        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Ready",
            text_color="green",
            font=ctk.CTkFont(size=11)
        )
        self.status_label.pack(side="left")

        refresh_btn = ctk.CTkButton(
            status_frame,
            text="🔄 Refresh Analysis",
            command=self._refresh_analysis,
            height=32,
            font=ctk.CTkFont(size=12)
        )
        refresh_btn.pack(side="right")

    def _load_analysis(self):
        """Load frequency analysis from windows data."""
        if not self.project.data.train_windows_file:
            self.analysis_status.configure(
                text="No training data available. Please create windows first.",
                text_color='orange'
            )
            self.status_label.configure(
                text="Ready (no training data)",
                text_color='gray'
            )
            return

        windows_path = Path(self.project.data.train_windows_file)
        if not windows_path.exists():
            self.analysis_status.configure(
                text=f"Training windows file not found: {windows_path.name}",
                text_color='red'
            )
            self.status_label.configure(
                text="Ready (file not found)",
                text_color='gray'
            )
            return

        try:
            # Run frequency analysis
            self.freq_stats, self.recommended_config_id, self.recommended_confidence = \
                generate_frequency_report(
                    windows_path,
                    sample_rate=100.0
                )

            # Update UI
            self._update_analysis_display()
            self._update_recommendation_display()

            self.status_label.configure(
                text=f"Analysis complete: {len(self.freq_stats)} classes analyzed",
                text_color='green'
            )

        except Exception as e:
            messagebox.showerror("Analysis Error", f"Failed to analyze frequency data:\n{str(e)}")
            self.status_label.configure(
                text="Analysis failed",
                text_color='red'
            )

    def _update_analysis_display(self):
        """Update frequency analysis visualization."""
        if not self.freq_stats:
            return

        total_samples = sum(s.sample_count for s in self.freq_stats.values())
        self.analysis_status.configure(
            text=f"Analyzed {len(self.freq_stats)} classes from {total_samples} samples",
            text_color='green'
        )

        # Clear previous plots
        self.fig.clear()

        # Create subplots side by side (1 row, 2 columns)
        ax1 = self.fig.add_subplot(121)  # Energy distribution (left)
        ax2 = self.fig.add_subplot(122)  # Frequency ranges (right)

        # Adjust subplot spacing for side-by-side layout
        self.fig.subplots_adjust(left=0.06, right=0.98, top=0.92, bottom=0.15, wspace=0.25)

        # Plot 1: Energy distribution by frequency band
        classes = list(self.freq_stats.keys())
        bands = ['Very Low (0-0.5 Hz)', 'Low (0.5-1.5 Hz)', 'Medium (1.5-3.0 Hz)',
                'High (3.0-5.0 Hz)', 'Very High (5.0+ Hz)']

        x = np.arange(len(classes))
        width = 0.16

        for i, band in enumerate(bands):
            energies = [self.freq_stats[cls].energy_distribution[band] for cls in classes]
            offset = (i - 2) * width
            ax1.bar(x + offset, energies, width, label=band, alpha=0.9)

        ax1.set_xlabel('Class', fontsize=11)
        ax1.set_ylabel('Energy (%)', fontsize=11)
        ax1.set_title('Energy Distribution by Frequency Band', fontsize=12, fontweight='bold', pad=10)
        ax1.set_xticks(x)
        ax1.set_xticklabels(classes, rotation=45, ha='right', fontsize=10)
        ax1.tick_params(axis='y', labelsize=10)
        ax1.legend(fontsize=8, loc='upper left', ncol=2, framealpha=0.9)
        ax1.grid(True, alpha=0.3)

        # Plot 2: Frequency ranges with config overlays
        for i, cls in enumerate(classes):
            stats = self.freq_stats[cls]
            ax2.plot(i, stats.dominant_freq, 'ro', markersize=10, label='Dominant' if i == 0 else '')
            ax2.plot([i, i], stats.freq_range, 'b-', linewidth=3, label='Range' if i == 0 else '')

        # Overlay config ranges
        configs = self.analyzer.get_all_configs()
        for config_id, config in configs.items():
            ax2.axhspan(config.freq_range[0], config.freq_range[1],
                       alpha=0.2, color=config.color,
                       label=f'Config {config.id} ({config.name})')

        ax2.set_xlabel('Class', fontsize=11)
        ax2.set_ylabel('Frequency (Hz)', fontsize=11)
        ax2.set_title('Frequency Ranges vs Configuration Coverage', fontsize=12, fontweight='bold', pad=10)
        ax2.set_xticks(range(len(classes)))
        ax2.set_xticklabels(classes, rotation=45, ha='right', fontsize=10)
        ax2.tick_params(axis='y', labelsize=10)
        ax2.legend(fontsize=8, loc='upper left', framealpha=0.9)
        ax2.grid(True, alpha=0.3)

        # Draw canvas
        self.canvas.draw()

        # Update details text
        self.details_text.delete("1.0", "end")
        for cls, stats in self.freq_stats.items():
            self.details_text.insert("end", f"{'='*50}\n")
            self.details_text.insert("end", f"Class: {cls} ({stats.sample_count} samples)\n")
            self.details_text.insert("end", f"  Dominant Frequency: {stats.dominant_freq:.2f} Hz\n")
            self.details_text.insert("end", f"  Frequency Range: {stats.freq_range[0]:.2f} - {stats.freq_range[1]:.2f} Hz\n")
            self.details_text.insert("end", f"  Spectral Centroid: {stats.spectral_centroid:.2f} Hz\n")
            self.details_text.insert("end", f"  Bandwidth: {stats.spectral_bandwidth:.2f} Hz\n\n")

    def _update_recommendation_display(self):
        """Update recommendation display."""
        if not self.recommended_config_id:
            return

        config = self.analyzer.get_config(self.recommended_config_id)

        self.rec_config_label.configure(
            text=f"Config {config.id}: {config.name}",
            text_color=config.color
        )

        confidence_pct = self.recommended_confidence * 100
        confidence_text = f"Confidence: {confidence_pct:.1f}%"
        if confidence_pct >= 80:
            confidence_color = 'green'
        elif confidence_pct >= 60:
            confidence_color = 'orange'
        else:
            confidence_color = 'red'

        self.rec_confidence_label.configure(
            text=confidence_text,
            text_color=confidence_color
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

        self.rec_reason_label.configure(text=f"Reason: {reason}")

        # Auto-select recommended config
        self.config_var.set(self.recommended_config_id)
        self.selected_config_id = self.recommended_config_id

        # Update project
        self._save_config_to_project()

    def _on_config_selected(self):
        """Handle manual config selection."""
        self.selected_config_id = self.config_var.get()
        self._save_config_to_project()

        config = self.analyzer.get_config(self.selected_config_id)

        # Show info if user overrides recommendation
        if self.selected_config_id != self.recommended_config_id and self.recommended_config_id:
            self.status_label.configure(
                text=f"Manual override: Config {config.id} selected (recommended: {self.recommended_config_id})",
                text_color='orange'
            )
        else:
            self.status_label.configure(
                text=f"Config {config.id} selected",
                text_color='green'
            )

    def _save_config_to_project(self):
        """Save selected config to project."""
        config = self.analyzer.get_config(self.selected_config_id)
        self.project.timesnet_config = {
            'config_id': config.id,
            'config_name': config.name,
            'periods': config.periods,
            'auto_selected': (self.selected_config_id == self.recommended_config_id),
            'confidence': self.recommended_confidence
        }

    def _refresh_analysis(self):
        """Refresh frequency analysis."""
        self.status_label.configure(text="Analyzing...", text_color="orange")
        try:
            self._load_analysis()
        except Exception as e:
            messagebox.showerror("Refresh Error", f"Failed to refresh analysis:\n{str(e)}")
            self.status_label.configure(text="Refresh failed", text_color="red")

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

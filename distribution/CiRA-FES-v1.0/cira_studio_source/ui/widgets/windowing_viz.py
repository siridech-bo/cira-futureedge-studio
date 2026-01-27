"""
Windowing Visualization Widget

Shows how continuous data is segmented into windows with overlaps.
"""

import customtkinter as ctk
from typing import List, Optional, Dict
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
import numpy as np
from loguru import logger


class WindowingVisualization(ctk.CTkFrame):
    """
    Windowing visualization widget.

    Features:
    - Timeline view with window boxes
    - Overlap regions highlighted
    - Color-coded by class label (if classification mode)
    - Interactive window selection
    """

    # Color palette
    COLORS = {
        'default': '#3B82F6',
        'idle': '#10B981',
        'snake': '#F59E0B',
        'ingestion': '#EF4444',
        'overlap': '#8B5CF6'
    }

    def __init__(self, parent, width=800, height=300, **kwargs):
        """
        Initialize the windowing visualization.

        Args:
            parent: Parent CustomTkinter widget
            width: Chart width in pixels
            height: Chart height in pixels
        """
        super().__init__(parent, **kwargs)

        self.width = width
        self.height = height

        self._setup_plot()
        self._apply_modern_style()

    def _setup_plot(self):
        """Setup matplotlib figure and canvas."""
        self.fig = Figure(figsize=(self.width/100, self.height/100), dpi=100)
        self.ax = self.fig.add_subplot(111)

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

        self.fig.tight_layout()

    def _apply_modern_style(self, theme='dark'):
        """Apply modern styling."""
        if theme == 'dark':
            bg_color = '#1E1E1E'
            fg_color = '#2D2D2D'
            text_color = '#E0E0E0'
            grid_color = '#444444'
        else:
            bg_color = '#FFFFFF'
            fg_color = '#F5F5F5'
            text_color = '#000000'
            grid_color = '#CCCCCC'

        self.fig.patch.set_facecolor(bg_color)
        self.ax.set_facecolor(fg_color)
        self.ax.tick_params(colors=text_color)
        self.ax.xaxis.label.set_color(text_color)
        self.ax.yaxis.label.set_color(text_color)
        self.ax.title.set_color(text_color)
        self.ax.spines['bottom'].set_color(grid_color)
        self.ax.spines['top'].set_color(grid_color)
        self.ax.spines['left'].set_color(grid_color)
        self.ax.spines['right'].set_color(grid_color)

    def plot_windows(
        self,
        data_length: int,
        window_size: int,
        overlap: float = 0.0,
        window_labels: Optional[List[str]] = None,
        title: str = "Window Segmentation"
    ):
        """
        Plot window segmentation visualization.

        Args:
            data_length: Total length of data
            window_size: Size of each window
            overlap: Overlap ratio (0.0 to 1.0)
            window_labels: Optional list of class labels for each window
            title: Plot title
        """
        # Clear previous plot
        self.ax.clear()

        # Calculate window positions
        step = int(window_size * (1 - overlap))
        if step == 0:
            step = 1  # Avoid division by zero

        window_starts = list(range(0, data_length - window_size + 1, step))

        if len(window_starts) == 0:
            self.ax.text(0.5, 0.5, 'Window size larger than data length',
                        ha='center', va='center', transform=self.ax.transAxes,
                        fontsize=12, color='gray')
            self.canvas.draw()
            return

        # Draw timeline
        self.ax.plot([0, data_length], [0, 0], 'k-', linewidth=2, alpha=0.5)

        # Draw each window as a rectangle
        max_overlap_count = 1
        for i, start in enumerate(window_starts):
            end = start + window_size

            # Determine color
            if window_labels and i < len(window_labels):
                label = window_labels[i]
                color = self.COLORS.get(label, self.COLORS['default'])
            else:
                color = self.COLORS['default']

            # Calculate vertical position (stack overlapping windows)
            y_pos = i % 5  # Stack in rows of 5

            # Draw window rectangle
            rect = Rectangle(
                (start, y_pos - 0.4),
                window_size,
                0.8,
                facecolor=color,
                edgecolor='white',
                alpha=0.7,
                linewidth=2
            )
            self.ax.add_patch(rect)

            # Add window number annotation
            self.ax.text(
                start + window_size / 2,
                y_pos,
                str(i),
                ha='center',
                va='center',
                fontsize=8,
                fontweight='bold',
                color='white'
            )

            # Track max overlap
            max_overlap_count = max(max_overlap_count, y_pos + 1)

        # Highlight overlap regions if overlap > 0
        if overlap > 0:
            for i in range(len(window_starts) - 1):
                overlap_start = window_starts[i + 1]
                overlap_end = window_starts[i] + window_size

                if overlap_start < overlap_end:
                    # Draw overlap highlight
                    overlap_rect = Rectangle(
                        (overlap_start, -1),
                        overlap_end - overlap_start,
                        max_overlap_count + 1,
                        facecolor=self.COLORS['overlap'],
                        alpha=0.15,
                        linewidth=0
                    )
                    self.ax.add_patch(overlap_rect)

        # Configure axes
        self.ax.set_xlim(-window_size * 0.1, data_length + window_size * 0.1)
        self.ax.set_ylim(-1.5, max_overlap_count + 0.5)
        self.ax.set_xlabel('Sample Index', fontsize=11, fontweight='bold')
        self.ax.set_ylabel('Window Layer', fontsize=11, fontweight='bold')
        self.ax.set_title(title, fontsize=13, fontweight='bold', pad=15)

        # Add subtitle with window info
        subtitle = f'{len(window_starts)} windows | Size: {window_size} | Overlap: {overlap*100:.0f}% ({int(window_size*overlap)} samples)'
        self.ax.text(
            0.5, 1.02, subtitle,
            ha='center', va='bottom',
            transform=self.ax.transAxes,
            fontsize=9, style='italic', alpha=0.7
        )

        # Create legend if labels exist
        if window_labels:
            unique_labels = sorted(set(window_labels))
            handles = [
                Rectangle((0, 0), 1, 1, facecolor=self.COLORS.get(label, self.COLORS['default']), alpha=0.7)
                for label in unique_labels
            ]
            self.ax.legend(handles, unique_labels, loc='upper right', framealpha=0.9)

        # Reapply theme
        self._apply_modern_style()

        # Tight layout
        self.fig.tight_layout()
        self.canvas.draw()

        logger.info(f"Plotted windowing visualization: {len(window_starts)} windows")

    def clear_plot(self):
        """Clear the plot."""
        self.ax.clear()
        self._apply_modern_style()
        self.canvas.draw()

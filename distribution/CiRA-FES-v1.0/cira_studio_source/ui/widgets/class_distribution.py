"""
Class Distribution Chart Widget

Bar chart showing sample count per class for classification tasks.
"""

import customtkinter as ctk
from typing import Dict
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from loguru import logger


class ClassDistributionChart(ctk.CTkFrame):
    """
    Bar chart widget for class distribution visualization.

    Features:
    - Horizontal bar chart
    - Color-coded by class
    - Annotated with exact counts
    - Sorted by frequency
    """

    # Color palette
    COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
              '#EC4899', '#14B8A6', '#F97316']

    def __init__(self, parent, width=600, height=300, **kwargs):
        """
        Initialize the class distribution chart.

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
        # Create figure
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
        self.ax.grid(True, alpha=0.3, color=grid_color, axis='x')

    def plot_distribution(
        self,
        class_counts: Dict[str, int],
        title: str = "Class Distribution"
    ):
        """
        Plot class distribution as horizontal bar chart.

        Args:
            class_counts: Dictionary mapping class names to sample counts
            title: Chart title
        """
        # Clear previous plot
        self.ax.clear()

        if not class_counts:
            self.ax.text(0.5, 0.5, 'No class data available',
                        ha='center', va='center', transform=self.ax.transAxes,
                        fontsize=12, color='gray')
            self.canvas.draw()
            return

        # Sort by count (descending)
        sorted_items = sorted(class_counts.items(), key=lambda x: x[1], reverse=True)
        classes = [item[0] for item in sorted_items]
        counts = [item[1] for item in sorted_items]

        # Assign colors
        colors = [self.COLORS[i % len(self.COLORS)] for i in range(len(classes))]

        # Create horizontal bar chart
        y_pos = np.arange(len(classes))
        bars = self.ax.barh(y_pos, counts, color=colors, alpha=0.8, edgecolor='white', linewidth=1.5)

        # Annotate with counts
        max_count = max(counts) if counts else 1
        for i, (bar, count) in enumerate(zip(bars, counts)):
            # Add count text at end of bar
            self.ax.text(
                count + max_count * 0.02,
                i,
                f' {count}',
                va='center',
                fontweight='bold',
                fontsize=10
            )

        # Configure axes
        self.ax.set_yticks(y_pos)
        self.ax.set_yticklabels(classes, fontsize=10)
        self.ax.set_xlabel('Sample Count', fontsize=11, fontweight='bold')
        self.ax.set_title(title, fontsize=13, fontweight='bold', pad=15)

        # Add grid for x-axis only
        self.ax.grid(True, alpha=0.3, axis='x', linestyle='--')

        # Calculate total and add subtitle
        total = sum(counts)
        num_classes = len(classes)
        subtitle = f'{num_classes} classes, {total} total samples'
        self.ax.text(
            0.5, 1.02, subtitle,
            ha='center', va='bottom',
            transform=self.ax.transAxes,
            fontsize=9, style='italic', alpha=0.7
        )

        # Reapply theme
        self._apply_modern_style()

        # Tight layout and redraw
        self.fig.tight_layout()
        self.canvas.draw()

        logger.info(f"Plotted class distribution: {num_classes} classes, {total} samples")

    def clear_plot(self):
        """Clear the plot."""
        self.ax.clear()
        self._apply_modern_style()
        self.canvas.draw()

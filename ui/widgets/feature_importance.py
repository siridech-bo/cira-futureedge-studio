"""
Feature Importance Chart Widget

Bar chart showing feature importance scores from trained models.
"""

import customtkinter as ctk
from typing import List
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from loguru import logger


class FeatureImportanceChart(ctk.CTkFrame):
    """
    Feature importance bar chart widget.

    Features:
    - Top N features display
    - Horizontal bar chart
    - Color gradient by importance
    - Sorted descending
    """

    def __init__(self, parent, width=600, height=400, **kwargs):
        """
        Initialize the feature importance chart.

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
        self.ax.grid(True, alpha=0.3, color=grid_color, axis='x')

    def plot_importance(
        self,
        feature_names: List[str],
        importances: np.ndarray,
        top_n: int = 20,
        title: str = "Feature Importance"
    ):
        """
        Plot feature importance as horizontal bar chart.

        Args:
            feature_names: List of feature names
            importances: Array of importance scores
            top_n: Number of top features to display
            title: Chart title
        """
        # Clear previous plot
        self.ax.clear()

        if len(feature_names) == 0 or len(importances) == 0:
            self.ax.text(0.5, 0.5, 'No feature importance data',
                        ha='center', va='center', transform=self.ax.transAxes,
                        fontsize=12, color='gray')
            self.canvas.draw()
            return

        # Sort by importance (descending) and take top N
        indices = np.argsort(importances)[::-1][:top_n]
        top_features = [feature_names[i] for i in indices]
        top_importances = [importances[i] for i in indices]

        # Reverse for bottom-to-top display
        top_features = top_features[::-1]
        top_importances = top_importances[::-1]

        # Create color gradient (viridis colormap)
        colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(top_features)))

        # Create horizontal bar chart
        y_pos = np.arange(len(top_features))
        bars = self.ax.barh(
            y_pos,
            top_importances,
            color=colors,
            alpha=0.8,
            edgecolor='white',
            linewidth=1.5
        )

        # Annotate with values
        max_importance = max(top_importances) if top_importances else 1
        for i, (bar, importance) in enumerate(zip(bars, top_importances)):
            self.ax.text(
                importance + max_importance * 0.02,
                i,
                f' {importance:.4f}',
                va='center',
                fontsize=9,
                fontweight='bold'
            )

        # Configure axes
        self.ax.set_yticks(y_pos)
        self.ax.set_yticklabels(top_features, fontsize=9)
        self.ax.set_xlabel('Importance Score', fontsize=11, fontweight='bold')
        self.ax.set_title(title, fontsize=13, fontweight='bold', pad=15)

        # Grid
        self.ax.grid(True, alpha=0.3, axis='x', linestyle='--')

        # Add subtitle
        subtitle = f'Top {len(top_features)} features (out of {len(feature_names)} total)'
        self.ax.text(
            0.5, 1.02, subtitle,
            ha='center', va='bottom',
            transform=self.ax.transAxes,
            fontsize=9, style='italic', alpha=0.7
        )

        # Reapply theme
        self._apply_modern_style()

        # Tight layout
        self.fig.tight_layout()
        self.canvas.draw()

        logger.info(f"Plotted feature importance: top {len(top_features)} features")

    def clear_plot(self):
        """Clear the plot."""
        self.ax.clear()
        self._apply_modern_style()
        self.canvas.draw()

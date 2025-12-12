"""
Sensor Plot Widget

Multi-sensor time-series visualization with interactive features.
Uses Matplotlib embedded in CustomTkinter.
"""

import customtkinter as ctk
import pandas as pd
import numpy as np
from typing import List, Optional, Dict
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.widgets import RectangleSelector
from matplotlib.figure import Figure
from loguru import logger


class SensorPlotWidget(ctk.CTkFrame):
    """
    Interactive multi-sensor time-series plot widget.

    Features:
    - Multiple sensor traces on same plot
    - Color-coded legend
    - Interactive zoom/pan (matplotlib toolbar)
    - Window selection tool
    - Theme-aware styling
    """

    # Modern color palette (suitable for dark theme)
    COLORS = [
        '#3B82F6',  # Blue
        '#10B981',  # Green
        '#F59E0B',  # Amber
        '#EF4444',  # Red
        '#8B5CF6',  # Purple
        '#EC4899',  # Pink
        '#14B8A6',  # Teal
        '#F97316',  # Orange
    ]

    def __init__(self, parent, width=800, height=400, **kwargs):
        """
        Initialize the sensor plot widget.

        Args:
            parent: Parent CustomTkinter widget
            width: Plot width in pixels
            height: Plot height in pixels
        """
        super().__init__(parent, **kwargs)

        self.width = width
        self.height = height
        self.data = None
        self.sensor_columns = []
        self.time_column = None
        self.window_selector = None
        self.selected_window_callback = None

        self._setup_plot()
        self._apply_modern_style()

    def _setup_plot(self):
        """Setup matplotlib figure and canvas."""
        # Create figure with tight layout
        self.fig = Figure(figsize=(self.width/100, self.height/100), dpi=100)
        self.ax = self.fig.add_subplot(111)

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()

        # Add navigation toolbar
        self.toolbar_frame = ctk.CTkFrame(self)
        self.toolbar_frame.pack(side="top", fill="x", padx=5, pady=5)

        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()

        # Pack canvas
        self.canvas.get_tk_widget().pack(side="top", fill="both", expand=True, padx=5, pady=5)

        # Tight layout
        self.fig.tight_layout()

    def _apply_modern_style(self, theme='dark'):
        """
        Apply modern styling to the plot.

        Args:
            theme: 'dark' or 'light'
        """
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
        self.ax.grid(True, alpha=0.3, color=grid_color)

    def plot_sensors(
        self,
        data: pd.DataFrame,
        sensor_columns: List[str],
        time_column: Optional[str] = None,
        title: str = "Sensor Data",
        xlabel: str = "Sample Index",
        ylabel: str = "Value"
    ):
        """
        Plot multiple sensor traces.

        Args:
            data: DataFrame containing sensor data
            sensor_columns: List of column names to plot
            time_column: Optional time column for x-axis
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
        """
        self.data = data
        self.sensor_columns = sensor_columns
        self.time_column = time_column

        # Clear previous plot
        self.ax.clear()

        # Determine x-axis data
        if time_column and time_column in data.columns:
            x_data = data[time_column].values
            xlabel = time_column
        else:
            x_data = np.arange(len(data))

        # Plot each sensor
        for i, sensor in enumerate(sensor_columns):
            if sensor in data.columns:
                color = self.COLORS[i % len(self.COLORS)]
                self.ax.plot(
                    x_data,
                    data[sensor].values,
                    label=sensor,
                    color=color,
                    linewidth=1.5,
                    alpha=0.9
                )
            else:
                logger.warning(f"Column '{sensor}' not found in DataFrame")

        # Add legend
        if len(sensor_columns) > 0:
            self.ax.legend(
                loc='upper right',
                framealpha=0.9,
                fancybox=True,
                shadow=True
            )

        # Labels and title
        self.ax.set_xlabel(xlabel, fontsize=11, fontweight='bold')
        self.ax.set_ylabel(ylabel, fontsize=11, fontweight='bold')
        self.ax.set_title(title, fontsize=13, fontweight='bold', pad=15)

        # Grid
        self.ax.grid(True, alpha=0.3, linestyle='--')

        # Reapply theme
        self._apply_modern_style()

        # Redraw
        self.fig.tight_layout()
        self.canvas.draw()

        logger.info(f"Plotted {len(sensor_columns)} sensors with {len(data)} samples")

    def enable_window_selector(self, callback=None):
        """
        Enable interactive window selection tool.

        Args:
            callback: Function to call when window is selected.
                     Receives (start_index, end_index) as arguments.
        """
        self.selected_window_callback = callback

        def on_select(eclick, erelease):
            """Handle rectangle selection."""
            x1, x2 = int(eclick.xdata), int(erelease.xdata)

            # Ensure x1 < x2
            start_idx = min(x1, x2)
            end_idx = max(x1, x2)

            logger.info(f"Window selected: [{start_idx}, {end_idx}]")

            if self.selected_window_callback:
                self.selected_window_callback(start_idx, end_idx)

        # Create rectangle selector
        self.window_selector = RectangleSelector(
            self.ax,
            on_select,
            useblit=True,
            button=[1],  # Left mouse button
            minspanx=5,
            minspany=5,
            spancoords='pixels',
            interactive=True,
            props=dict(facecolor='blue', alpha=0.3, edgecolor='blue', linewidth=2)
        )

        logger.info("Window selector enabled")

    def disable_window_selector(self):
        """Disable window selection tool."""
        if self.window_selector:
            self.window_selector.set_active(False)
            self.window_selector = None
            logger.info("Window selector disabled")

    def highlight_windows(self, window_starts: List[int], window_size: int, overlap: float = 0.0):
        """
        Highlight window regions on the plot.

        Args:
            window_starts: List of window start indices
            window_size: Size of each window
            overlap: Overlap ratio (0.0 to 1.0)
        """
        # Remove previous highlights
        for patch in list(self.ax.patches):
            patch.remove()

        # Add window rectangles
        y_min, y_max = self.ax.get_ylim()

        for i, start in enumerate(window_starts):
            end = start + window_size

            # Alternate colors for visibility
            color = self.COLORS[i % len(self.COLORS)]
            alpha = 0.15

            # Draw rectangle
            rect = plt.Rectangle(
                (start, y_min),
                window_size,
                y_max - y_min,
                facecolor=color,
                alpha=alpha,
                edgecolor=color,
                linewidth=1.5
            )
            self.ax.add_patch(rect)

        # Redraw
        self.canvas.draw()

        logger.info(f"Highlighted {len(window_starts)} windows")

    def clear_plot(self):
        """Clear the plot."""
        self.ax.clear()
        self._apply_modern_style()
        self.canvas.draw()

    def export_plot(self, filepath: str, dpi: int = 300):
        """
        Export plot to file.

        Args:
            filepath: Output file path (supports .png, .pdf, .svg)
            dpi: Resolution in dots per inch
        """
        try:
            self.fig.savefig(filepath, dpi=dpi, bbox_inches='tight', facecolor=self.fig.get_facecolor())
            logger.info(f"Plot exported to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export plot: {e}")
            return False

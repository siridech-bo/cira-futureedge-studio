"""
Confusion Matrix Widget

Heatmap visualization for classification results using Seaborn.
"""

import customtkinter as ctk
from typing import List
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import seaborn as sns
from loguru import logger


class ConfusionMatrixWidget(ctk.CTkFrame):
    """
    Confusion matrix heatmap widget for classification evaluation.

    Features:
    - Seaborn heatmap with annotations
    - Color gradient visualization
    - Percentage and count display
    - Per-class accuracy highlighting
    """

    def __init__(self, parent, width=500, height=500, **kwargs):
        """
        Initialize the confusion matrix widget.

        Args:
            parent: Parent CustomTkinter widget
            width: Chart width in pixels
            height: Chart height in pixels
        """
        super().__init__(parent, **kwargs)

        self.width = width
        self.height = height

        self._setup_plot()

    def _setup_plot(self):
        """Setup matplotlib figure and canvas."""
        # Create square figure for confusion matrix
        size = min(self.width, self.height) / 100
        self.fig = Figure(figsize=(size, size), dpi=100)
        self.ax = self.fig.add_subplot(111)

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

        self.fig.tight_layout()

    def plot_confusion_matrix(
        self,
        confusion_matrix: np.ndarray,
        class_names: List[str],
        title: str = "Confusion Matrix",
        show_percentages: bool = True
    ):
        """
        Plot confusion matrix as heatmap.

        Args:
            confusion_matrix: 2D array of shape (n_classes, n_classes)
            class_names: List of class names
            title: Plot title
            show_percentages: Show percentages alongside counts
        """
        # Clear previous plot
        self.ax.clear()

        if confusion_matrix is None or len(confusion_matrix) == 0:
            self.ax.text(0.5, 0.5, 'No confusion matrix data',
                        ha='center', va='center', transform=self.ax.transAxes,
                        fontsize=12, color='gray')
            self.canvas.draw()
            return

        # Convert to numpy array
        cm = np.array(confusion_matrix)

        # Calculate percentages
        cm_percent = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis] * 100

        # Create annotations
        if show_percentages:
            annot = np.empty_like(cm).astype(str)
            for i in range(cm.shape[0]):
                for j in range(cm.shape[1]):
                    count = cm[i, j]
                    percent = cm_percent[i, j]
                    annot[i, j] = f'{count}\n({percent:.1f}%)'
        else:
            annot = cm

        # Create heatmap
        sns.heatmap(
            cm,
            annot=annot,
            fmt='',
            cmap='Blues',
            xticklabels=class_names,
            yticklabels=class_names,
            cbar_kws={'label': 'Count'},
            linewidths=2,
            linecolor='white',
            square=True,
            ax=self.ax,
            cbar=True,
            annot_kws={'fontsize': 10, 'fontweight': 'bold'}
        )

        # Labels and title
        self.ax.set_xlabel('Predicted Class', fontsize=12, fontweight='bold')
        self.ax.set_ylabel('True Class', fontsize=12, fontweight='bold')
        self.ax.set_title(title, fontsize=14, fontweight='bold', pad=15)

        # Rotate labels for better readability
        self.ax.set_xticklabels(self.ax.get_xticklabels(), rotation=45, ha='right')
        self.ax.set_yticklabels(self.ax.get_yticklabels(), rotation=0)

        # Calculate overall accuracy
        accuracy = np.trace(cm) / np.sum(cm) * 100

        # Add accuracy subtitle
        subtitle = f'Overall Accuracy: {accuracy:.2f}%'
        self.ax.text(
            0.5, 1.02, subtitle,
            ha='center', va='bottom',
            transform=self.ax.transAxes,
            fontsize=10, fontweight='bold', color='green'
        )

        # Tight layout
        self.fig.tight_layout()
        self.canvas.draw()

        logger.info(f"Plotted confusion matrix: {len(class_names)} classes, accuracy={accuracy:.2f}%")

    def clear_plot(self):
        """Clear the plot."""
        self.ax.clear()
        self.canvas.draw()

"""
CiRA FutureEdge Studio - Model Training Panel
UI for training anomaly detection models (PyOD) and classification models (sklearn)
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from pathlib import Path
from typing import Optional, List, Dict, Any
import threading
import pickle

import pandas as pd
import numpy as np

from core.project import ProjectManager
from core.model_trainer import ModelTrainer, TrainingConfig, ALGORITHMS
from core.classification_trainer import ClassificationTrainer, ClassificationConfig, CLASSIFIERS
from core.timeseries_trainer import TimeSeriesTrainer, TimeSeriesConfig
from core.license_manager import get_license_manager
from ui.widgets import ConfusionMatrixWidget, FeatureImportanceChart
from loguru import logger


class ModelPanel(ctk.CTkFrame):
    """Panel for model training (anomaly detection and classification)."""

    def __init__(self, parent, project_manager: ProjectManager):
        """Initialize the model panel."""
        super().__init__(parent)
        self.project_manager = project_manager
        self.anomaly_trainer = ModelTrainer()
        self.classification_trainer = ClassificationTrainer()
        self.timeseries_trainer = TimeSeriesTrainer()  # Deep learning trainer
        self.training_results = None
        self.features_df = None
        self.selected_features = []
        self.windows = None  # For DL mode
        self.window_labels = None  # For DL mode

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create notebook for tabs
        self.notebook = ctk.CTkTabview(self)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Add tabs
        self.notebook.add("Algorithm")
        self.notebook.add("Training")
        self.notebook.add("Evaluation")
        self.notebook.add("Explorer")
        self.notebook.add("Export")

        self._create_algorithm_tab()
        self._create_training_tab()
        self._create_evaluation_tab()
        self._create_explorer_tab()
        self._create_export_tab()

        # Update controls based on pipeline mode
        self._update_training_controls_for_pipeline_mode()

        # Load data (features or windows) based on pipeline mode
        self._load_data_for_training()

    def _create_algorithm_tab(self):
        """Create algorithm selection tab."""
        tab = self.notebook.tab("Algorithm")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Get pipeline mode and task mode from project
        pipeline_mode = "ml"
        task_mode = "anomaly_detection"
        if self.project_manager.current_project:
            pipeline_mode = getattr(self.project_manager.current_project.data, 'pipeline_mode', 'ml')
            task_mode = self.project_manager.current_project.data.task_type

        # Branch based on pipeline mode
        if pipeline_mode == "dl":
            self._create_dl_algorithm_ui(tab)
        else:
            self._create_ml_algorithm_ui(tab, task_mode)

    def _create_ml_algorithm_ui(self, tab, task_mode):
        """Create ML algorithm selection UI."""
        # Title (dynamic based on task mode) - spans both columns
        title_text = "Select Classification Algorithm" if task_mode == "classification" else "Select Anomaly Detection Algorithm"
        self.title_label = ctk.CTkLabel(
            tab,
            text=title_text,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.title_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="w")

        # LEFT COLUMN: Algorithm selection
        left_column = ctk.CTkFrame(tab)
        left_column.grid(row=1, column=0, padx=(20, 5), pady=10, sticky="nsew")
        left_column.grid_columnconfigure(0, weight=1)
        left_column.grid_rowconfigure(1, weight=1)

        # Algorithm info frame (in left column)
        info_frame = ctk.CTkFrame(left_column)
        info_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        info_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(info_frame, text="Selected Features:").grid(
            row=0, column=0, padx=10, pady=5, sticky="w"
        )
        self.features_info_label = ctk.CTkLabel(
            info_frame, text="Loading...", text_color="gray"
        )
        self.features_info_label.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(info_frame, text="Data Samples:").grid(
            row=1, column=0, padx=10, pady=5, sticky="w"
        )
        self.samples_info_label = ctk.CTkLabel(
            info_frame, text="Loading...", text_color="gray"
        )
        self.samples_info_label.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(info_frame, text="Recommendation:").grid(
            row=2, column=0, padx=10, pady=5, sticky="w"
        )
        self.recommendation_label = ctk.CTkLabel(
            info_frame, text="Loading...", text_color="blue"
        )
        self.recommendation_label.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        # Algorithm selection list (in left column)
        selection_frame = ctk.CTkFrame(left_column)
        selection_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        selection_frame.grid_columnconfigure(0, weight=1)
        selection_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            selection_frame,
            text="Available Algorithms:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # Scrollable frame for algorithms
        scroll_frame = ctk.CTkScrollableFrame(selection_frame)
        scroll_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        scroll_frame.grid_columnconfigure(0, weight=1)

        # Algorithm radio buttons (dynamic based on task mode)
        algorithms = CLASSIFIERS if task_mode == "classification" else ALGORITHMS
        default_algo = "random_forest" if task_mode == "classification" else "iforest"
        self.algorithm_var = ctk.StringVar(value=default_algo)
        row = 0

        for algo_id, algo_info in algorithms.items():
            frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            frame.grid(row=row, column=0, padx=5, pady=5, sticky="ew")
            frame.grid_columnconfigure(1, weight=1)

            radio = ctk.CTkRadioButton(
                frame,
                text=algo_info['name'],
                variable=self.algorithm_var,
                value=algo_id,
                command=self._on_algorithm_change
            )
            radio.grid(row=0, column=0, padx=5, sticky="w")

            desc = ctk.CTkLabel(
                frame,
                text=f"{algo_info['description']}",
                text_color="gray",
                wraplength=350,
                justify="left"
            )
            desc.grid(row=0, column=1, padx=10, sticky="w")

            row += 1

        # RIGHT COLUMN: Algorithm details
        right_column = ctk.CTkFrame(tab)
        right_column.grid(row=1, column=1, padx=(5, 20), pady=10, sticky="nsew")
        right_column.grid_columnconfigure(0, weight=1)
        right_column.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            right_column,
            text="Algorithm Details:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.algo_details_text = ctk.CTkTextbox(right_column)
        self.algo_details_text.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

        self._on_algorithm_change()

    def _create_dl_algorithm_ui(self, tab):
        """Create DL algorithm configuration UI."""
        # Title
        title_label = ctk.CTkLabel(
            tab,
            text="🧠 Deep Learning Model - TimesNet",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="w")

        # LEFT COLUMN: Data info
        left_column = ctk.CTkFrame(tab)
        left_column.grid(row=1, column=0, padx=(20, 5), pady=10, sticky="nsew")
        left_column.grid_columnconfigure(0, weight=1)

        # Data info frame
        info_frame = ctk.CTkFrame(left_column)
        info_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        info_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(info_frame, text="Windows:").grid(
            row=0, column=0, padx=10, pady=5, sticky="w"
        )
        self.windows_info_label = ctk.CTkLabel(
            info_frame, text="Loading...", text_color="gray"
        )
        self.windows_info_label.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(info_frame, text="Window Size:").grid(
            row=1, column=0, padx=10, pady=5, sticky="w"
        )
        self.window_size_label = ctk.CTkLabel(
            info_frame, text="Loading...", text_color="gray"
        )
        self.window_size_label.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(info_frame, text="Sensors:").grid(
            row=2, column=0, padx=10, pady=5, sticky="w"
        )
        self.sensors_info_label = ctk.CTkLabel(
            info_frame, text="Loading...", text_color="gray"
        )
        self.sensors_info_label.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        # Model complexity
        complexity_frame = ctk.CTkFrame(left_column)
        complexity_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        complexity_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            complexity_frame,
            text="Model Complexity:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.complexity_var = ctk.StringVar(value="efficient")
        complexity_selector = ctk.CTkSegmentedButton(
            complexity_frame,
            variable=self.complexity_var,
            values=["Minimal", "Efficient", "Comprehensive"]
        )
        complexity_selector.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")

        # Complexity descriptions
        complexity_info = ctk.CTkTextbox(complexity_frame, height=120)
        complexity_info.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        complexity_info.insert("1.0",
            "• Minimal: Fast training, good for CPU\n"
            "  - d_model=16, 1 layer, 2 kernels\n"
            "  - ~50K parameters\n\n"
            "• Efficient: Balanced (recommended)\n"
            "  - d_model=32, 2 layers, 4 kernels\n"
            "  - ~200K parameters\n\n"
            "• Comprehensive: Maximum accuracy\n"
            "  - d_model=64, 3 layers, 6 kernels\n"
            "  - ~800K parameters"
        )
        complexity_info.configure(state="disabled")

        # RIGHT COLUMN: Info
        right_column = ctk.CTkFrame(tab)
        right_column.grid(row=1, column=1, padx=(5, 20), pady=10, sticky="nsew")
        right_column.grid_columnconfigure(0, weight=1)
        right_column.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            right_column,
            text="About TimesNet:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        info_text = ctk.CTkTextbox(right_column)
        info_text.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        info_text.insert("1.0",
            "TimesNet is a state-of-the-art deep learning model for time series analysis.\n\n"
            "KEY FEATURES:\n"
            "• FFT-based period detection\n"
            "• Multi-scale temporal feature extraction\n"
            "• Handles complex temporal patterns\n"
            "• GPU/CPU auto-detection\n"
            "• ONNX export for Jetson deployment\n\n"
            "ADVANTAGES:\n"
            "• No manual feature engineering needed\n"
            "• Learns features automatically from raw data\n"
            "• Excellent for periodic sensor data\n"
            "• Captures long-range dependencies\n\n"
            "DEPLOYMENT:\n"
            "• Trains on PC (GPU or CPU)\n"
            "• Exports to ONNX format\n"
            "• Converts to TensorRT on Jetson\n"
            "• Optimized inference on edge devices\n\n"
            "Use this for complex temporal patterns in your sensor data."
        )
        info_text.configure(state="disabled")

        # Store algorithm var for compatibility
        self.algorithm_var = ctk.StringVar(value="timesnet")

    def _create_training_tab(self):
        """Create training configuration tab."""
        tab = self.notebook.tab("Training")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Title
        title = ctk.CTkLabel(
            tab,
            text="Training Configuration",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="w")

        # LEFT COLUMN: Configuration
        config_frame = ctk.CTkFrame(tab)
        config_frame.grid(row=1, column=0, padx=(20, 10), pady=10, sticky="nsew")
        config_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            config_frame,
            text="Parameters",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        # Test size (common for both ML and DL)
        ctk.CTkLabel(config_frame, text="Test Size:").grid(
            row=1, column=0, padx=10, pady=5, sticky="w"
        )
        self.test_size_var = ctk.StringVar(value="0.3")
        test_size_entry = ctk.CTkEntry(config_frame, textvariable=self.test_size_var, width=100)
        test_size_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(config_frame, text="(0.1-0.5)", text_color="gray", font=ctk.CTkFont(size=10)).grid(
            row=2, column=0, columnspan=2, padx=10, pady=(0, 5), sticky="w"
        )

        # ML-only: Contamination
        self.contam_label1 = ctk.CTkLabel(config_frame, text="Contamination:")
        self.contam_label1.grid(row=3, column=0, padx=10, pady=5, sticky="w")

        self.contamination_var = ctk.StringVar(value="0.1")
        self.contam_entry = ctk.CTkEntry(config_frame, textvariable=self.contamination_var, width=100)
        self.contam_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        self.contam_label2 = ctk.CTkLabel(
            config_frame,
            text="Expected anomaly rate (0.01-0.5)",
            text_color="gray",
            font=ctk.CTkFont(size=10)
        )
        self.contam_label2.grid(row=4, column=0, columnspan=2, padx=10, pady=(0, 5), sticky="w")

        # DL-only: Epochs
        self.epochs_label = ctk.CTkLabel(config_frame, text="Epochs:")
        self.epochs_var = ctk.StringVar(value="50")
        self.epochs_entry = ctk.CTkEntry(config_frame, textvariable=self.epochs_var, width=100)
        self.epochs_help = ctk.CTkLabel(
            config_frame,
            text="Training iterations (10-200)",
            text_color="gray",
            font=ctk.CTkFont(size=10)
        )

        # DL-only: Batch size
        self.batch_label = ctk.CTkLabel(config_frame, text="Batch Size:")
        self.batch_var = ctk.StringVar(value="32")
        self.batch_menu = ctk.CTkOptionMenu(
            config_frame,
            variable=self.batch_var,
            values=["8", "16", "32", "64"]
        )

        # DL-only: Learning rate
        self.lr_label = ctk.CTkLabel(config_frame, text="Learning Rate:")
        self.lr_var = ctk.StringVar(value="0.001")
        self.lr_entry = ctk.CTkEntry(config_frame, textvariable=self.lr_var, width=100)
        self.lr_help = ctk.CTkLabel(
            config_frame,
            text="(0.0001-0.01)",
            text_color="gray",
            font=ctk.CTkFont(size=10)
        )

        # Normalize (common, but label different)
        self.normalize_var = ctk.BooleanVar(value=True)
        self.normalize_check = ctk.CTkCheckBox(
            config_frame,
            text="Normalize features (recommended)",
            variable=self.normalize_var
        )
        self.normalize_check.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        # Random state (common)
        ctk.CTkLabel(config_frame, text="Random Seed:").grid(
            row=6, column=0, padx=10, pady=5, sticky="w"
        )
        self.random_state_var = ctk.StringVar(value="42")
        random_entry = ctk.CTkEntry(config_frame, textvariable=self.random_state_var, width=100)
        random_entry.grid(row=6, column=1, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(
            config_frame,
            text="For reproducibility",
            text_color="gray",
            font=ctk.CTkFont(size=10)
        ).grid(row=7, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")

        # Training button
        self.train_btn = ctk.CTkButton(
            config_frame,
            text="Start Training",
            command=self._start_training,
            fg_color="green",
            hover_color="darkgreen",
            height=40
        )
        self.train_btn.grid(row=8, column=0, columnspan=2, padx=10, pady=10)

        self.progress_label = ctk.CTkLabel(
            config_frame,
            text="",
            text_color="blue"
        )
        self.progress_label.grid(row=9, column=0, columnspan=2, padx=10, pady=(0, 10))

        # RIGHT COLUMN: Training status
        status_frame = ctk.CTkFrame(tab)
        status_frame.grid(row=1, column=1, padx=(10, 20), pady=10, sticky="nsew")
        status_frame.grid_columnconfigure(0, weight=1)
        status_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            status_frame,
            text="Training Log:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.training_log = ctk.CTkTextbox(status_frame, height=200)
        self.training_log.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    def _create_evaluation_tab(self):
        """Create evaluation results tab."""
        tab = self.notebook.tab("Evaluation")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Title
        title = ctk.CTkLabel(
            tab,
            text="Model Evaluation Results",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Results frame
        results_frame = ctk.CTkScrollableFrame(tab)
        results_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        results_frame.grid_columnconfigure(0, weight=1)

        self.results_container = results_frame

        # Placeholder
        self.no_results_label = ctk.CTkLabel(
            results_frame,
            text="No training results yet. Train a model first.",
            text_color="gray"
        )
        self.no_results_label.grid(row=0, column=0, pady=50)

    def _create_explorer_tab(self):
        """Create feature explorer tab with 3D visualization."""
        tab = self.notebook.tab("Explorer")
        tab.grid_columnconfigure(0, weight=0)  # Left column fixed width
        tab.grid_columnconfigure(1, weight=1)  # Right column expands
        tab.grid_rowconfigure(0, weight=1)

        # LEFT COLUMN: All settings and controls
        left_column = ctk.CTkFrame(tab)
        left_column.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)

        # Feature selection
        ctk.CTkLabel(
            left_column,
            text="Select 3 features:",
            font=("Segoe UI", 12, "bold")
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        # X-Axis
        ctk.CTkLabel(left_column, text="X-Axis:", font=("Segoe UI", 10)).grid(row=1, column=0, padx=10, pady=3, sticky="w")
        self.explorer_x_var = ctk.StringVar(value="No features available")
        self.explorer_x_menu = ctk.CTkOptionMenu(left_column, variable=self.explorer_x_var, values=["No features available"], width=200)
        self.explorer_x_menu.grid(row=2, column=0, padx=10, pady=3, sticky="ew")

        # Y-Axis
        ctk.CTkLabel(left_column, text="Y-Axis:", font=("Segoe UI", 10)).grid(row=3, column=0, padx=10, pady=3, sticky="w")
        self.explorer_y_var = ctk.StringVar(value="No features available")
        self.explorer_y_menu = ctk.CTkOptionMenu(left_column, variable=self.explorer_y_var, values=["No features available"], width=200)
        self.explorer_y_menu.grid(row=4, column=0, padx=10, pady=3, sticky="ew")

        # Z-Axis
        ctk.CTkLabel(left_column, text="Z-Axis:", font=("Segoe UI", 10)).grid(row=5, column=0, padx=10, pady=3, sticky="w")
        self.explorer_z_var = ctk.StringVar(value="No features available")
        self.explorer_z_menu = ctk.CTkOptionMenu(left_column, variable=self.explorer_z_var, values=["No features available"], width=200)
        self.explorer_z_menu.grid(row=6, column=0, padx=10, pady=3, sticky="ew")

        # Visualize button
        self.explorer_visualize_btn = ctk.CTkButton(
            left_column,
            text="🚀 Visualize in 3D",
            command=self._visualize_3d_explorer,
            height=40,
            font=("Segoe UI", 12, "bold"),
            fg_color="green",
            hover_color="darkgreen"
        )
        self.explorer_visualize_btn.grid(row=7, column=0, padx=10, pady=(10, 5), sticky="ew")

        # Separator
        ctk.CTkLabel(left_column, text="─" * 30, text_color="gray").grid(row=8, column=0, pady=5)

        # Control buttons
        ctk.CTkLabel(
            left_column,
            text="Zoom Controls:",
            font=("Segoe UI", 11, "bold")
        ).grid(row=9, column=0, sticky="w", padx=10, pady=(5, 3))

        zoom_frame = ctk.CTkFrame(left_column, fg_color="transparent")
        zoom_frame.grid(row=10, column=0, padx=10, pady=2, sticky="ew")

        self.zoom_in_btn = ctk.CTkButton(zoom_frame, text="➕ In", width=65, height=28, font=("Segoe UI", 9),
                                          command=self._zoom_in_3d, fg_color="#2B7A0B", hover_color="#1F5A08")
        self.zoom_in_btn.pack(side="left", padx=2)

        self.zoom_out_btn = ctk.CTkButton(zoom_frame, text="➖ Out", width=65, height=28, font=("Segoe UI", 9),
                                           command=self._zoom_out_3d, fg_color="#1F538D", hover_color="#14375E")
        self.zoom_out_btn.pack(side="left", padx=2)

        self.zoom_reset_btn = ctk.CTkButton(zoom_frame, text="↻", width=45, height=28, font=("Segoe UI", 12),
                                             command=self._reset_zoom_3d, fg_color="#555555", hover_color="#333333")
        self.zoom_reset_btn.pack(side="left", padx=2)

        # RIGHT COLUMN: 3D plot only
        plot_frame = ctk.CTkFrame(tab)
        plot_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        plot_frame.grid_columnconfigure(0, weight=1)
        plot_frame.grid_rowconfigure(0, weight=1)

        # Import matplotlib for embedded 3D plot
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
        from matplotlib.figure import Figure

        # Create figure that will resize with window
        self.explorer_fig = Figure(dpi=100)
        # Minimize all margins to eliminate whitespace
        self.explorer_fig.subplots_adjust(left=0.0, right=1.0, top=0.98, bottom=0.0)

        self.explorer_ax = self.explorer_fig.add_subplot(111, projection='3d')
        # No title to maximize graph space
        self.explorer_ax.set_xlabel("X")
        self.explorer_ax.set_ylabel("Y")
        self.explorer_ax.set_zlabel("Z")

        # Force cubic aspect ratio for better 3D visualization
        self.explorer_ax.set_box_aspect([1, 1, 1])

        # Store initial view limits for zoom
        self.explorer_zoom_level = 1.0

        self.explorer_canvas = FigureCanvasTkAgg(self.explorer_fig, master=plot_frame)
        self.explorer_canvas.draw()
        # Pack instead of grid to allow responsive resizing
        self.explorer_canvas.get_tk_widget().pack(fill="both", expand=True)

    def _create_export_tab(self):
        """Create model export tab."""
        tab = self.notebook.tab("Export")
        tab.grid_columnconfigure(0, weight=1)

        # Title
        title = ctk.CTkLabel(
            tab,
            text="Export Trained Model",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Status
        status_frame = ctk.CTkFrame(tab)
        status_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        status_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(status_frame, text="Model Status:").grid(
            row=0, column=0, padx=10, pady=10, sticky="w"
        )
        self.export_status_label = ctk.CTkLabel(
            status_frame,
            text="No model trained yet",
            text_color="gray"
        )
        self.export_status_label.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # Export options
        options_frame = ctk.CTkFrame(tab)
        options_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(
            options_frame,
            text="Model files are automatically saved to the project's 'models' directory:",
            wraplength=500
        ).pack(padx=10, pady=10, anchor="w")

        self.model_path_label = ctk.CTkLabel(
            options_frame,
            text="",
            text_color="blue",
            wraplength=500
        )
        self.model_path_label.pack(padx=10, pady=5, anchor="w")

        # Export button
        export_btn = ctk.CTkButton(
            tab,
            text="Open Model Directory",
            command=self._open_model_dir,
            state="disabled"
        )
        export_btn.grid(row=3, column=0, padx=20, pady=20)
        self.open_dir_btn = export_btn

        # Mark stage complete button
        complete_btn = ctk.CTkButton(
            tab,
            text="Save & Continue to DSP Stage",
            command=self._mark_complete,
            fg_color="green",
            hover_color="darkgreen",
            height=40,
            state="disabled"
        )
        complete_btn.grid(row=4, column=0, padx=20, pady=10)
        self.complete_btn = complete_btn

    def _on_algorithm_change(self):
        """Handle algorithm selection change."""
        algo_id = self.algorithm_var.get()

        # Get task mode to determine which algorithm dict to use
        task_mode = "anomaly_detection"
        if self.project_manager.current_project:
            task_mode = self.project_manager.current_project.data.task_type

        # Get algorithm info from correct dictionary
        algorithms = CLASSIFIERS if task_mode == "classification" else ALGORITHMS
        algo_info = algorithms.get(algo_id, algorithms[list(algorithms.keys())[0]])

        # Update details with better formatting
        details = f"═══ {algo_info['name']} ═══\n\n"
        details += f"📝 Description:\n{algo_info['description']}\n\n"
        details += f"🎯 Recommended for:\n{algo_info['recommended_for']}\n\n"
        details += f"⚙️ Default Parameters:\n"

        # Format parameters nicely
        if isinstance(algo_info['params'], dict):
            for key, value in algo_info['params'].items():
                details += f"  • {key}: {value}\n"
        else:
            details += f"{algo_info['params']}\n"

        self.algo_details_text.delete("1.0", "end")
        self.algo_details_text.insert("1.0", details)

    def _update_training_controls_for_pipeline_mode(self):
        """Show/hide training controls based on pipeline mode."""
        project = self.project_manager.current_project
        if not project:
            return

        pipeline_mode = getattr(project.data, 'pipeline_mode', 'ml')

        if pipeline_mode == "dl":
            # Hide ML-only controls
            self.contam_label1.grid_remove()
            self.contam_entry.grid_remove()
            self.contam_label2.grid_remove()

            # Show DL controls in their positions
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

            # Restore normalize label
            self.normalize_check.configure(text="Normalize features (recommended)")

    def _start_dl_training(self):
        """Start deep learning training with TimesNet."""
        # Check license
        license_mgr = get_license_manager()
        if not license_mgr.check_feature("dl"):
            messagebox.showerror(
                "Feature Locked",
                "Deep Learning training requires a PRO or ENTERPRISE license.\n\n"
                "Current tier: FREE (Community)\n\n"
                "Please upgrade your license to access this feature.\n"
                "Go to Settings > License to activate your license key."
            )
            return

        project = self.project_manager.current_project

        # Validate data
        if not hasattr(self, 'windows') or self.windows is None:
            messagebox.showerror("Error", "No window data loaded. Please ensure data and windows are created.")
            return

        if not hasattr(self, 'window_labels') or self.window_labels is None:
            messagebox.showerror("Error", "No window labels found. Ensure data has class labels.")
            return

        # Validate inputs
        try:
            test_size = float(self.test_size_var.get())
            if not 0.1 <= test_size <= 0.5:
                raise ValueError("Test size must be between 0.1 and 0.5")

            epochs = int(self.epochs_var.get())
            if not 10 <= epochs <= 200:
                raise ValueError("Epochs must be between 10 and 200")

            batch_size = int(self.batch_var.get())
            lr = float(self.lr_var.get())
            if not 0.0001 <= lr <= 0.01:
                raise ValueError("Learning rate must be between 0.0001 and 0.01")

            random_state = int(self.random_state_var.get())
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
            return

        # Get complexity
        complexity_map = {"Minimal": "minimal", "Efficient": "efficient", "Comprehensive": "comprehensive"}
        complexity = complexity_map.get(self.complexity_var.get(), "efficient")

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

        # Disable controls
        self.train_btn.configure(state="disabled")
        self.progress_label.configure(text="Training in progress...")
        self.training_log.delete("1.0", "end")

        # Get output directory
        model_dir = project.get_project_dir() / "models"
        model_dir.mkdir(parents=True, exist_ok=True)

        # Run in thread
        def training_thread():
            try:
                self._log_training("=" * 50)
                self._log_training("DEEP LEARNING TRAINING - TimesNet")
                self._log_training("=" * 50)
                self._log_training(f"Windows: {len(self.windows)}")
                self._log_training(f"Window size: {self.windows.shape[1]}")
                self._log_training(f"Sensors: {self.windows.shape[2]}")
                self._log_training(f"Classes: {len(set(self.window_labels))}")
                self._log_training(f"Complexity: {complexity}")
                self._log_training(f"Epochs: {epochs}, Batch: {batch_size}, LR: {lr}")
                self._log_training("")
                self._log_training("🖥️  Detecting GPU/CPU...")
                self._log_training("")

                # Define progress callback
                def on_epoch_end(progress):
                    epoch = progress['epoch']
                    total = progress['total_epochs']
                    train_loss = progress['train_loss']
                    train_acc = progress['train_acc']
                    val_loss = progress['val_loss']
                    val_acc = progress['val_acc']

                    msg = (f"Epoch {epoch}/{total} - "
                           f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2%} | "
                           f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2%}")
                    self._log_training(msg)

                    # Update progress label
                    def update_label():
                        progress_pct = (epoch / total) * 100
                        self.progress_label.configure(
                            text=f"Training: Epoch {epoch}/{total} ({progress_pct:.0f}%) - Acc: {val_acc:.1%}",
                            text_color="orange"
                        )
                    self.after(0, update_label)

                results = self.timeseries_trainer.train(
                    windows=self.windows,
                    labels=self.window_labels,
                    config=config,
                    output_dir=model_dir,
                    progress_callback=on_epoch_end
                )

                self._log_training("")
                self._log_training("=" * 50)
                self._log_training("TRAINING COMPLETE!")
                self._log_training("=" * 50)
                self._log_training(f"✓ Device used: {results.device_used}")
                self._log_training(f"✓ Model parameters: {results.total_parameters:,}")
                self._log_training(f"✓ Accuracy: {results.accuracy:.3f}")
                self._log_training(f"✓ Precision: {results.precision_macro:.3f}")
                self._log_training(f"✓ Recall: {results.recall_macro:.3f}")
                self._log_training(f"✓ F1 Score: {results.f1_macro:.3f}")
                self._log_training("")
                self._log_training("Per-class F1 scores:")
                for class_name, f1 in results.per_class_f1.items():
                    self._log_training(f"  {class_name}: {f1:.3f}")
                self._log_training("")
                self._log_training(f"✓ Model saved: {results.model_path}")
                if results.onnx_model_path:
                    self._log_training(f"✓ ONNX exported: {results.onnx_model_path}")
                    self._log_training("  Ready for TensorRT conversion on Jetson!")

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
                project.model.dl_config = {
                    'complexity': complexity,
                    'epochs': epochs,
                    'batch_size': batch_size,
                    'learning_rate': lr,
                    'model_info': results.model_params
                }

                project.mark_stage_completed("model")
                project.save()

                self.training_results = results

                # Re-enable controls
                self.train_btn.configure(state="normal")
                self.progress_label.configure(text="Training complete!", text_color="green")

                # Update evaluation tab
                self.after(100, self._update_evaluation_display)

                # Update export tab
                self.export_status_label.configure(
                    text=f"✓ {results.algorithm} model trained successfully",
                    text_color="green"
                )
                self.model_path_label.configure(text=results.model_path)
                self.open_dir_btn.configure(state="normal")
                self.complete_btn.configure(state="normal")

                messagebox.showinfo(
                    "Training Complete",
                    f"TimesNet training successful!\n\n"
                    f"Device: {results.device_used}\n"
                    f"Accuracy: {results.accuracy:.1%}\n"
                    f"Model saved to: models/"
                )

            except Exception as e:
                self._log_training(f"\n❌ ERROR: {str(e)}")
                logger.error(f"DL training failed: {e}", exc_info=True)

                self.train_btn.configure(state="normal")
                self.progress_label.configure(text="Training failed!", text_color="red")

                messagebox.showerror(
                    "Training Error",
                    f"Deep learning training failed:\n\n{str(e)}\n\nCheck logs for details."
                )

        thread = threading.Thread(target=training_thread, daemon=True)
        thread.start()

    def _load_data_for_training(self):
        """Load features (ML) or windows (DL) based on pipeline mode."""
        project = self.project_manager.current_project
        if not project:
            return

        pipeline_mode = getattr(project.data, 'pipeline_mode', 'ml')

        if pipeline_mode == "dl":
            # Load windows for deep learning
            try:
                import pickle

                if project.data.train_test_split_type == "manual":
                    # Load train/test windows separately
                    with open(project.data.train_windows_file, 'rb') as f:
                        train_windows = pickle.load(f)

                    # Convert to numpy arrays
                    # Force conversion to float32 and filter out non-numeric columns
                    windows_list = []
                    for w in train_windows:
                        if isinstance(w.data, pd.DataFrame):
                            # Extract only numeric sensor columns (exclude time, _source_file, etc.)
                            numeric_cols = w.data.select_dtypes(include=[np.number]).columns.tolist()
                            # Further filter to exclude 'time' if present
                            sensor_cols = [col for col in numeric_cols if col.lower() not in ['time', 'timestamp']]
                            window_array = w.data[sensor_cols].values.astype(np.float32)
                        else:
                            # Already numpy array
                            window_array = np.array(w.data, dtype=np.float32)
                        windows_list.append(window_array)

                    self.windows = np.array(windows_list, dtype=np.float32)
                    self.window_labels = np.array([w.class_label for w in train_windows])

                    # Update UI labels
                    if hasattr(self, 'windows_info_label'):
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

                    logger.info(f"Loaded {len(self.windows)} windows for DL training")

                else:
                    # Load single windows file
                    if project.data.windows_file:
                        with open(project.data.windows_file, 'rb') as f:
                            windows = pickle.load(f)

                        # Convert to numpy array (n_windows, seq_len, n_sensors)
                        # Force conversion to float32 and filter out non-numeric columns
                        windows_list = []
                        for w in windows:
                            if isinstance(w.data, pd.DataFrame):
                                # Extract only numeric sensor columns (exclude time, _source_file, etc.)
                                numeric_cols = w.data.select_dtypes(include=[np.number]).columns.tolist()
                                # Further filter to exclude 'time' if present
                                sensor_cols = [col for col in numeric_cols if col.lower() not in ['time', 'timestamp']]
                                window_array = w.data[sensor_cols].values.astype(np.float32)
                            else:
                                # Already numpy array
                                window_array = np.array(w.data, dtype=np.float32)
                            windows_list.append(window_array)

                        self.windows = np.array(windows_list, dtype=np.float32)
                        self.window_labels = np.array([w.class_label if hasattr(w, 'class_label') else str(w.label) for w in windows])

                        # Update UI labels
                        if hasattr(self, 'windows_info_label'):
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

                        logger.info(f"Loaded {len(self.windows)} windows for DL training")

            except Exception as e:
                logger.error(f"Failed to load windows for DL: {e}")
                if hasattr(self, 'windows_info_label'):
                    self.windows_info_label.configure(
                        text="Error loading windows",
                        text_color="red"
                    )
        else:
            # Load features for ML (existing code path)
            # This is handled by _load_features_thread() which is called elsewhere
            pass

    def _start_training(self):
        """Start model training in background thread."""
        project = self.project_manager.current_project
        if not project:
            messagebox.showerror("Error", "No project loaded")
            return

        # Branch based on pipeline mode
        pipeline_mode = getattr(project.data, 'pipeline_mode', 'ml')

        if pipeline_mode == "dl":
            self._start_dl_training()
        else:
            self._start_ml_training()

    def _start_ml_training(self):
        """Start traditional ML training (existing implementation)."""
        project = self.project_manager.current_project

        # Validate inputs
        try:
            test_size = float(self.test_size_var.get())
            if not 0.1 <= test_size <= 0.5:
                raise ValueError("Test size must be between 0.1 and 0.5")

            contamination = float(self.contamination_var.get())
            if not 0.01 <= contamination <= 0.5:
                raise ValueError("Contamination must be between 0.01 and 0.5")

            random_state = int(self.random_state_var.get())
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
            return

        # Build configuration
        config = TrainingConfig(
            algorithm=self.algorithm_var.get(),
            test_size=test_size,
            contamination=contamination,
            random_state=random_state,
            normalize=self.normalize_var.get(),
            params={'contamination': contamination}  # Pass to model
        )

        # Disable controls
        self.train_btn.configure(state="disabled")
        self.progress_label.configure(text="Training in progress...")
        self.training_log.delete("1.0", "end")

        # Run in thread
        def training_thread():
            try:
                self._log_training("Loading features...")

                # Load features
                features_path = Path(project.features.extracted_features)
                with open(features_path, 'rb') as f:
                    self.features_df = pickle.load(f)

                self.selected_features = project.llm.selected_features
                self._log_training(f"Loaded {len(self.selected_features)} selected features")

                # Get output directory
                model_dir = project.get_project_dir() / "models"
                model_dir.mkdir(parents=True, exist_ok=True)

                # Get task mode
                task_mode = project.data.task_type

                self._log_training(f"Task Mode: {task_mode}")
                self._log_training(f"Training {config.algorithm}...")

                # Branch based on task mode
                if task_mode == "classification":
                    # CLASSIFICATION MODE

                    # Check if manual train/test split
                    if project.data.train_test_split_type == "manual":
                        self._log_training("Using manual train/test split from separate datasets...")

                        # Load train features and windows
                        train_features_path = project.get_features_dir() / "train_features.pkl"
                        with open(train_features_path, 'rb') as f:
                            train_features = pickle.load(f)

                        with open(project.data.train_windows_file, 'rb') as f:
                            train_windows = pickle.load(f)

                        train_labels = [w.class_label for w in train_windows]
                        self._log_training(f"Train: {len(train_labels)} samples")

                        # Load test features and windows if available
                        test_features = None
                        test_labels = None
                        if project.data.test_windows_file:
                            test_features_path = project.get_features_dir() / "test_features.pkl"
                            with open(test_features_path, 'rb') as f:
                                test_features = pickle.load(f)

                            with open(project.data.test_windows_file, 'rb') as f:
                                test_windows = pickle.load(f)

                            test_labels = [w.class_label for w in test_windows]
                            self._log_training(f"Test: {len(test_labels)} samples")

                        self._log_training(f"Found {len(set(train_labels))} classes: {sorted(set(train_labels))}")

                        # Create classification config with manual split
                        class_config = ClassificationConfig(
                            algorithm=config.algorithm,
                            test_size=test_size,
                            normalize=self.normalize_var.get(),
                            random_state=random_state,
                            params={},
                            train_features=train_features,
                            train_labels=train_labels,
                            test_features=test_features,
                            test_labels=test_labels
                        )

                        # Use combined features for compatibility (but train/test already split in config)
                        features_combined = self.features_df
                        labels_combined = train_labels + (test_labels if test_labels else [])

                        # Train classifier
                        results = self.classification_trainer.train(
                            features_combined,
                            self.selected_features,
                            labels_combined,
                            class_config,
                            model_dir
                        )

                    else:
                        # Automatic train/test split
                        self._log_training("Loading windows to extract labels...")
                        windows = project.load_windows()
                        if not windows:
                            raise ValueError("No windows found. Please segment data in the Data panel first.")

                        labels = np.array([w.class_label for w in windows])
                        if labels[0] is None:
                            raise ValueError("No class labels found in windows. Enable label extraction in Data panel.")

                        self._log_training(f"Found {len(set(labels))} classes: {sorted(set(labels))}")

                        # Create classification config
                        class_config = ClassificationConfig(
                            algorithm=config.algorithm,
                            test_size=test_size,
                            normalize=self.normalize_var.get(),
                            random_state=random_state,
                            params={}
                        )

                        # Train classifier
                        results = self.classification_trainer.train(
                            self.features_df,
                            self.selected_features,
                            labels,
                            class_config,
                            model_dir
                        )

                else:
                    # ANOMALY DETECTION MODE (existing code)
                    results = self.anomaly_trainer.train(
                        self.features_df,
                        self.selected_features,
                        config,
                        model_dir
                    )

                self.training_results = results

                # Update UI on main thread
                self.after(0, lambda: self._training_complete(results, task_mode))

            except Exception as e:
                logger.error(f"Training failed: {e}")
                self.after(0, lambda: self._training_failed(str(e)))

        thread = threading.Thread(target=training_thread, daemon=True)
        thread.start()

    def _log_training(self, message: str):
        """Add message to training log."""
        def update():
            self.training_log.insert("end", f"{message}\n")
            self.training_log.see("end")

        self.after(0, update)

    def _training_complete(self, results, task_mode="anomaly_detection"):
        """Handle training completion."""
        self.train_btn.configure(state="normal")
        self.progress_label.configure(text="✓ Training completed", text_color="green")

        self._log_training("\n" + "="*50)
        self._log_training("TRAINING COMPLETED")
        self._log_training("="*50)
        self._log_training(f"Algorithm: {results.algorithm}")
        self._log_training(f"Training samples: {results.train_samples}")
        self._log_training(f"Test samples: {results.test_samples}")
        self._log_training(f"Features: {results.n_features}")

        if task_mode == "classification":
            # Classification metrics
            self._log_training(f"\nClassification Metrics:")
            self._log_training(f"Accuracy: {results.accuracy:.1%}")
            self._log_training(f"Precision (macro): {results.precision_macro:.3f}")
            self._log_training(f"Recall (macro): {results.recall_macro:.3f}")
            self._log_training(f"F1 Score (macro): {results.f1_macro:.3f}")
            self._log_training(f"\nClasses: {', '.join(results.class_names)}")

            message_text = f"Classifier trained successfully!\n\nAccuracy: {results.accuracy:.1%}\nModel saved to: {results.model_path}"
        else:
            # Anomaly detection metrics
            self._log_training(f"Train anomaly rate: {results.train_anomaly_rate:.1%}")
            self._log_training(f"Test anomaly rate: {results.test_anomaly_rate:.1%}")

            if results.has_labels:
                self._log_training(f"\nSupervised Metrics:")
                self._log_training(f"Precision: {results.precision:.3f}")
                self._log_training(f"Recall: {results.recall:.3f}")
                self._log_training(f"F1 Score: {results.f1_score:.3f}")
                self._log_training(f"ROC-AUC: {results.roc_auc:.3f}")

            message_text = f"Model trained successfully!\n\nTest anomaly rate: {results.test_anomaly_rate:.1%}\nModel saved to: {results.model_path}"

        # Update evaluation tab
        self._display_results(results, task_mode)

        # Switch to Evaluation tab to show results
        self.notebook.set("Evaluation")

        # Update export tab
        self.export_status_label.configure(
            text=f"✓ {results.algorithm} model trained successfully",
            text_color="green"
        )
        self.model_path_label.configure(text=results.model_path)
        self.open_dir_btn.configure(state="normal")
        self.complete_btn.configure(state="normal")

        # Save to project
        project = self.project_manager.current_project
        project.model.algorithm = results.algorithm
        project.model.model_path = results.model_path
        project.model.trained = True

        if task_mode == "classification":
            project.model.model_type = "classifier"
            project.model.num_classes = results.n_classes
            project.model.class_names = results.class_names
            project.model.confusion_matrix = results.confusion_matrix
            project.model.label_encoder_path = results.label_encoder_path
            project.model.metrics = {
                "accuracy": results.accuracy,
                "precision_macro": results.precision_macro,
                "recall_macro": results.recall_macro,
                "f1_macro": results.f1_macro
            }

        # Update Explorer tab with feature dropdowns
        if task_mode == "classification" and hasattr(results, 'feature_importances') and hasattr(results, 'feature_names'):
            # Update feature dropdowns
            self.explorer_x_menu.configure(values=results.feature_names)
            self.explorer_y_menu.configure(values=results.feature_names)
            self.explorer_z_menu.configure(values=results.feature_names)

            # Auto-select top 3 features by importance
            num_features = min(3, len(results.feature_names))
            if num_features >= 3:
                sorted_indices = np.argsort(results.feature_importances)[::-1]
                top_features = [results.feature_names[i] for i in sorted_indices[:num_features]]

                if len(top_features) >= 1:
                    self.explorer_x_var.set(top_features[0])
                if len(top_features) >= 2:
                    self.explorer_y_var.set(top_features[1])
                if len(top_features) >= 3:
                    self.explorer_z_var.set(top_features[2])

                logger.info(f"Explorer tab updated with top {num_features} features: {top_features}")

        project.save()

        messagebox.showinfo("Training Complete", message_text)

    def _training_failed(self, error: str):
        """Handle training failure."""
        self.train_btn.configure(state="normal")
        self.progress_label.configure(text="✗ Training failed", text_color="red")
        self._log_training(f"\nERROR: {error}")

        messagebox.showerror("Training Failed", f"Training failed:\n{error}")

    def _update_evaluation_display(self):
        """Update evaluation display after DL training completes."""
        if hasattr(self, 'training_results') and self.training_results:
            # Display the results in the Evaluation tab
            self._display_results(self.training_results, task_mode="classification")
            # Switch to Evaluation tab to show results
            self.notebook.set("Evaluation")
        else:
            logger.warning("No training results available to display")

    def _display_results(self, results, task_mode="anomaly_detection"):
        """Display evaluation results."""
        # Clear previous results (this also removes no_results_label)
        for widget in self.results_container.winfo_children():
            widget.destroy()

        row = 0

        # CLASSIFICATION MODE DISPLAY
        if task_mode == "classification":
            # Model info
            info_frame = ctk.CTkFrame(self.results_container)
            info_frame.grid(row=row, column=0, padx=10, pady=10, sticky="ew")
            info_frame.grid_columnconfigure(1, weight=1)
            row += 1

            ctk.CTkLabel(
                info_frame,
                text="Classification Model Information",
                font=ctk.CTkFont(size=14, weight="bold")
            ).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")

            # Get test dataset folder path if using manual split
            project = self.project_manager.current_project
            test_folder_info = ""
            if project and project.data.train_test_split_type == "manual":
                if project.data.test_folder_path:
                    # Use the original test folder path
                    test_folder = project.data.test_folder_path
                    # Show last 60 characters if path is long
                    if len(test_folder) > 60:
                        test_folder_info = f" (from: ...{test_folder[-60:]})"
                    else:
                        test_folder_info = f" (from: {test_folder})"

            # Build labels based on result type (ML vs DL)
            labels = [
                ("Algorithm:", results.algorithm),
                ("Training Samples:", str(results.train_samples)),
                ("Test Samples:", str(results.test_samples) + test_folder_info),
            ]

            # Add features/sensors info based on result type
            if hasattr(results, 'n_features'):
                # ML results
                labels.append(("Features:", str(results.n_features)))
            elif hasattr(results, 'n_sensors'):
                # DL results
                labels.append(("Window Size:", str(results.window_size)))
                labels.append(("Sensors:", str(results.n_sensors)))
                labels.append(("Model Parameters:", f"{results.total_parameters:,}"))

            labels.append(("Classes:", str(results.n_classes)))

            for i, (label, value) in enumerate(labels, start=1):
                ctk.CTkLabel(info_frame, text=label).grid(
                    row=i, column=0, padx=10, pady=5, sticky="w"
                )
                # Make test samples label wrap if it's long
                test_label = ctk.CTkLabel(info_frame, text=value, text_color="blue")
                if "from:" in value:
                    test_label.configure(wraplength=600, justify="left")
                test_label.grid(row=i, column=1, padx=10, pady=5, sticky="w")

            # Overall metrics
            metrics_frame = ctk.CTkFrame(self.results_container)
            metrics_frame.grid(row=row, column=0, padx=10, pady=10, sticky="ew")
            metrics_frame.grid_columnconfigure(1, weight=1)
            row += 1

            ctk.CTkLabel(
                metrics_frame,
                text="Overall Performance Metrics",
                font=ctk.CTkFont(size=14, weight="bold")
            ).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")

            metrics = [
                ("Accuracy:", f"{results.accuracy:.1%}"),
                ("Precision (macro):", f"{results.precision_macro:.3f}"),
                ("Recall (macro):", f"{results.recall_macro:.3f}"),
                ("F1 Score (macro):", f"{results.f1_macro:.3f}"),
            ]

            for i, (label, value) in enumerate(metrics, start=1):
                ctk.CTkLabel(metrics_frame, text=label).grid(
                    row=i, column=0, padx=10, pady=5, sticky="w"
                )
                ctk.CTkLabel(metrics_frame, text=value, text_color="green" if "Accuracy" in label else "blue").grid(
                    row=i, column=1, padx=10, pady=5, sticky="w"
                )

            # Device info for DL results
            if hasattr(results, 'device_used'):
                device_frame = ctk.CTkFrame(self.results_container)
                device_frame.grid(row=row, column=0, padx=10, pady=10, sticky="ew")
                device_frame.grid_columnconfigure(1, weight=1)
                row += 1

                ctk.CTkLabel(
                    device_frame,
                    text="Training Information",
                    font=ctk.CTkFont(size=14, weight="bold")
                ).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")

                ctk.CTkLabel(device_frame, text="Device:").grid(
                    row=1, column=0, padx=10, pady=5, sticky="w"
                )
                ctk.CTkLabel(device_frame, text=results.device_used, text_color="blue").grid(
                    row=1, column=1, padx=10, pady=5, sticky="w"
                )

            # Confusion Matrix
            if results.confusion_matrix:
                cm_frame = ctk.CTkFrame(self.results_container)
                cm_frame.grid(row=row, column=0, padx=10, pady=10, sticky="ew")
                cm_frame.grid_columnconfigure(0, weight=1)
                row += 1

                ctk.CTkLabel(
                    cm_frame,
                    text="Confusion Matrix",
                    font=ctk.CTkFont(size=14, weight="bold")
                ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

                cm_widget = ConfusionMatrixWidget(cm_frame, width=800, height=600)
                cm_widget.grid(row=1, column=0, padx=10, pady=10)

                cm_widget.plot_confusion_matrix(
                    confusion_matrix=np.array(results.confusion_matrix),
                    class_names=results.class_names
                )

            # Feature Importance (only for ML results)
            if hasattr(results, 'feature_importances') and results.feature_importances:
                fi_frame = ctk.CTkFrame(self.results_container)
                fi_frame.grid(row=row, column=0, padx=10, pady=10, sticky="ew")
                fi_frame.grid_columnconfigure(0, weight=1)
                row += 1

                ctk.CTkLabel(
                    fi_frame,
                    text="Feature Importance",
                    font=ctk.CTkFont(size=14, weight="bold")
                ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

                fi_widget = FeatureImportanceChart(fi_frame, width=900, height=500)
                fi_widget.grid(row=1, column=0, padx=10, pady=10)

                feature_names = list(results.feature_importances.keys())
                importances = np.array(list(results.feature_importances.values()))

                fi_widget.plot_importance(feature_names, importances, top_n=20)

            return  # Exit early for classification mode

        # ANOMALY DETECTION MODE DISPLAY (existing code below)
        row = 0

        # Model info
        info_frame = ctk.CTkFrame(self.results_container)
        info_frame.grid(row=row, column=0, padx=10, pady=10, sticky="ew")
        info_frame.grid_columnconfigure(1, weight=1)
        row += 1

        ctk.CTkLabel(
            info_frame,
            text="Model Information",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        labels = [
            ("Algorithm:", results.algorithm),
            ("Training Samples:", str(results.train_samples)),
            ("Test Samples:", str(results.test_samples)),
            ("Features:", str(results.n_features)),
        ]

        for i, (label, value) in enumerate(labels, start=1):
            ctk.CTkLabel(info_frame, text=label).grid(
                row=i, column=0, padx=10, pady=5, sticky="w"
            )
            ctk.CTkLabel(info_frame, text=value, text_color="blue").grid(
                row=i, column=1, padx=10, pady=5, sticky="w"
            )

        # Anomaly rates
        rates_frame = ctk.CTkFrame(self.results_container)
        rates_frame.grid(row=row, column=0, padx=10, pady=10, sticky="ew")
        rates_frame.grid_columnconfigure(1, weight=1)
        row += 1

        ctk.CTkLabel(
            rates_frame,
            text="Anomaly Detection Rates",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(rates_frame, text="Training Set:").grid(
            row=1, column=0, padx=10, pady=5, sticky="w"
        )
        ctk.CTkLabel(
            rates_frame,
            text=f"{results.train_anomaly_rate:.1%}",
            text_color="blue"
        ).grid(row=1, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(rates_frame, text="Test Set:").grid(
            row=2, column=0, padx=10, pady=5, sticky="w"
        )
        ctk.CTkLabel(
            rates_frame,
            text=f"{results.test_anomaly_rate:.1%}",
            text_color="blue"
        ).grid(row=2, column=1, padx=10, pady=5, sticky="w")

        # Supervised metrics if available
        if results.has_labels:
            metrics_frame = ctk.CTkFrame(self.results_container)
            metrics_frame.grid(row=row, column=0, padx=10, pady=10, sticky="ew")
            metrics_frame.grid_columnconfigure(1, weight=1)
            row += 1

            ctk.CTkLabel(
                metrics_frame,
                text="Performance Metrics (with ground truth)",
                font=ctk.CTkFont(size=14, weight="bold")
            ).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")

            metrics = [
                ("Precision:", f"{results.precision:.3f}"),
                ("Recall:", f"{results.recall:.3f}"),
                ("F1 Score:", f"{results.f1_score:.3f}"),
                ("ROC-AUC:", f"{results.roc_auc:.3f}"),
            ]

            for i, (label, value) in enumerate(metrics, start=1):
                ctk.CTkLabel(metrics_frame, text=label).grid(
                    row=i, column=0, padx=10, pady=5, sticky="w"
                )
                ctk.CTkLabel(metrics_frame, text=value, text_color="blue").grid(
                    row=i, column=1, padx=10, pady=5, sticky="w"
                )

        # Feature list
        features_frame = ctk.CTkFrame(self.results_container)
        features_frame.grid(row=row, column=0, padx=10, pady=10, sticky="ew")
        features_frame.grid_columnconfigure(0, weight=1)
        row += 1

        ctk.CTkLabel(
            features_frame,
            text=f"Selected Features ({results.n_features}):",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        features_text = ctk.CTkTextbox(features_frame, height=100)
        features_text.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        features_text.insert("1.0", "\n".join(f"{i+1}. {f}" for i, f in enumerate(results.feature_names)))
        features_text.configure(state="disabled")

    def _visualize_3d_explorer(self):
        """Create 3D visualization using Matplotlib (embedded)."""
        project = self.project_manager.current_project
        if not project:
            messagebox.showerror("No Project", "No project loaded.")
            return

        # Get selected features
        x_feature = self.explorer_x_var.get()
        y_feature = self.explorer_y_var.get()
        z_feature = self.explorer_z_var.get()

        if x_feature == "No features available":
            messagebox.showwarning("No Features", "Train model first to visualize features.")
            return

        # Check if features are different
        if len({x_feature, y_feature, z_feature}) < 3:
            messagebox.showwarning("Duplicate Features", "Please select 3 different features.")
            return

        try:
            # Load features
            if self.features_df is None or self.features_df.empty:
                messagebox.showwarning("No Features", "No feature data loaded. Train model first.")
                return

            # Load windows to get labels
            windows = []
            if project.data.train_test_split_type == "manual":
                # Load train and test windows
                if project.data.train_windows_file and project.data.test_windows_file:
                    with open(project.data.train_windows_file, 'rb') as f:
                        windows.extend(pickle.load(f))
                    with open(project.data.test_windows_file, 'rb') as f:
                        windows.extend(pickle.load(f))
            else:
                # Load single windows file
                if project.data.windows_file:
                    with open(project.data.windows_file, 'rb') as f:
                        windows = pickle.load(f)

            if not windows:
                messagebox.showwarning("No Windows", "No window data found.")
                return

            # Get labels from windows
            labels = [w.class_label if hasattr(w, 'class_label') and w.class_label else str(w.label) for w in windows]

            # Get feature data
            x_data = self.features_df[x_feature].values
            y_data = self.features_df[y_feature].values
            z_data = self.features_df[z_feature].values

            # Clear previous plot
            self.explorer_ax.clear()

            # Get unique labels and assign colors
            unique_labels = sorted(set(labels))
            colors_list = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']

            # Plot each class
            for idx, label in enumerate(unique_labels):
                mask = [l == label for l in labels]
                color = colors_list[idx % len(colors_list)]
                self.explorer_ax.scatter(
                    x_data[mask],
                    y_data[mask],
                    z_data[mask],
                    c=color,
                    label=label,
                    s=30,
                    alpha=0.6
                )

            self.explorer_ax.set_xlabel(x_feature, fontsize=10)
            self.explorer_ax.set_ylabel(y_feature, fontsize=10)
            self.explorer_ax.set_zlabel(z_feature, fontsize=10)
            # No title to maximize graph space
            self.explorer_ax.legend(loc='upper right', fontsize=9)

            # Redraw canvas
            self.explorer_canvas.draw()

            logger.info(f"3D visualization created with features: {x_feature}, {y_feature}, {z_feature}")

        except Exception as e:
            logger.error(f"Failed to create 3D visualization: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Visualization Error", f"Failed to create visualization:\n{str(e)}")

    def _zoom_in_3d(self):
        """Zoom in on 3D plot."""
        try:
            # Get current axis limits
            xlim = self.explorer_ax.get_xlim()
            ylim = self.explorer_ax.get_ylim()
            zlim = self.explorer_ax.get_zlim()

            # Calculate zoom factor (zoom in by 20%)
            zoom_factor = 0.8

            # Calculate centers
            x_center = (xlim[0] + xlim[1]) / 2
            y_center = (ylim[0] + ylim[1]) / 2
            z_center = (zlim[0] + zlim[1]) / 2

            # Calculate new ranges
            x_range = (xlim[1] - xlim[0]) * zoom_factor / 2
            y_range = (ylim[1] - ylim[0]) * zoom_factor / 2
            z_range = (zlim[1] - zlim[0]) * zoom_factor / 2

            # Set new limits
            self.explorer_ax.set_xlim(x_center - x_range, x_center + x_range)
            self.explorer_ax.set_ylim(y_center - y_range, y_center + y_range)
            self.explorer_ax.set_zlim(z_center - z_range, z_center + z_range)

            self.explorer_canvas.draw()
            logger.info("Zoomed in on 3D plot")

        except Exception as e:
            logger.error(f"Failed to zoom in: {e}")

    def _zoom_out_3d(self):
        """Zoom out on 3D plot."""
        try:
            # Get current axis limits
            xlim = self.explorer_ax.get_xlim()
            ylim = self.explorer_ax.get_ylim()
            zlim = self.explorer_ax.get_zlim()

            # Calculate zoom factor (zoom out by 20%)
            zoom_factor = 1.25

            # Calculate centers
            x_center = (xlim[0] + xlim[1]) / 2
            y_center = (ylim[0] + ylim[1]) / 2
            z_center = (zlim[0] + zlim[1]) / 2

            # Calculate new ranges
            x_range = (xlim[1] - xlim[0]) * zoom_factor / 2
            y_range = (ylim[1] - ylim[0]) * zoom_factor / 2
            z_range = (zlim[1] - zlim[0]) * zoom_factor / 2

            # Set new limits
            self.explorer_ax.set_xlim(x_center - x_range, x_center + x_range)
            self.explorer_ax.set_ylim(y_center - y_range, y_center + y_range)
            self.explorer_ax.set_zlim(z_center - z_range, z_center + z_range)

            self.explorer_canvas.draw()
            logger.info("Zoomed out on 3D plot")

        except Exception as e:
            logger.error(f"Failed to zoom out: {e}")

    def _reset_zoom_3d(self):
        """Reset zoom to original view."""
        try:
            # Redraw the current visualization to reset zoom
            self._visualize_3d_explorer()
            logger.info("Reset zoom on 3D plot")

        except Exception as e:
            logger.error(f"Failed to reset zoom: {e}")

    def _rotate_left_3d(self):
        """Rotate 3D plot to the left."""
        try:
            elev, azim = self.explorer_ax.elev, self.explorer_ax.azim
            self.explorer_ax.view_init(elev=elev, azim=azim - 15)
            self.explorer_canvas.draw()
            logger.info(f"Rotated 3D plot left (azim={azim - 15})")

        except Exception as e:
            logger.error(f"Failed to rotate left: {e}")

    def _rotate_right_3d(self):
        """Rotate 3D plot to the right."""
        try:
            elev, azim = self.explorer_ax.elev, self.explorer_ax.azim
            self.explorer_ax.view_init(elev=elev, azim=azim + 15)
            self.explorer_canvas.draw()
            logger.info(f"Rotated 3D plot right (azim={azim + 15})")

        except Exception as e:
            logger.error(f"Failed to rotate right: {e}")

    def _rotate_up_3d(self):
        """Rotate 3D plot upward."""
        try:
            elev, azim = self.explorer_ax.elev, self.explorer_ax.azim
            new_elev = min(elev + 15, 90)  # Limit to 90 degrees
            self.explorer_ax.view_init(elev=new_elev, azim=azim)
            self.explorer_canvas.draw()
            logger.info(f"Rotated 3D plot up (elev={new_elev})")

        except Exception as e:
            logger.error(f"Failed to rotate up: {e}")

    def _rotate_down_3d(self):
        """Rotate 3D plot downward."""
        try:
            elev, azim = self.explorer_ax.elev, self.explorer_ax.azim
            new_elev = max(elev - 15, -90)  # Limit to -90 degrees
            self.explorer_ax.view_init(elev=new_elev, azim=azim)
            self.explorer_canvas.draw()
            logger.info(f"Rotated 3D plot down (elev={new_elev})")

        except Exception as e:
            logger.error(f"Failed to rotate down: {e}")

    def _pan_left_3d(self):
        """Pan 3D plot to the left (move view left along X axis)."""
        try:
            xlim = self.explorer_ax.get_xlim()
            x_range = xlim[1] - xlim[0]
            pan_amount = x_range * 0.1  # Pan by 10% of range

            self.explorer_ax.set_xlim(xlim[0] - pan_amount, xlim[1] - pan_amount)
            self.explorer_canvas.draw()
            logger.info("Panned 3D plot left")

        except Exception as e:
            logger.error(f"Failed to pan left: {e}")

    def _pan_right_3d(self):
        """Pan 3D plot to the right (move view right along X axis)."""
        try:
            xlim = self.explorer_ax.get_xlim()
            x_range = xlim[1] - xlim[0]
            pan_amount = x_range * 0.1  # Pan by 10% of range

            self.explorer_ax.set_xlim(xlim[0] + pan_amount, xlim[1] + pan_amount)
            self.explorer_canvas.draw()
            logger.info("Panned 3D plot right")

        except Exception as e:
            logger.error(f"Failed to pan right: {e}")

    def _pan_up_3d(self):
        """Pan 3D plot upward (move view up along Y axis)."""
        try:
            ylim = self.explorer_ax.get_ylim()
            y_range = ylim[1] - ylim[0]
            pan_amount = y_range * 0.1  # Pan by 10% of range

            self.explorer_ax.set_ylim(ylim[0] + pan_amount, ylim[1] + pan_amount)
            self.explorer_canvas.draw()
            logger.info("Panned 3D plot up")

        except Exception as e:
            logger.error(f"Failed to pan up: {e}")

    def _pan_down_3d(self):
        """Pan 3D plot downward (move view down along Y axis)."""
        try:
            ylim = self.explorer_ax.get_ylim()
            y_range = ylim[1] - ylim[0]
            pan_amount = y_range * 0.1  # Pan by 10% of range

            self.explorer_ax.set_ylim(ylim[0] - pan_amount, ylim[1] - pan_amount)
            self.explorer_canvas.draw()
            logger.info("Panned 3D plot down")

        except Exception as e:
            logger.error(f"Failed to pan down: {e}")

    def _open_model_dir(self):
        """Open the model directory in file explorer."""
        project = self.project_manager.current_project
        if project and project.model.model_path:
            model_path = Path(project.model.model_path)
            model_dir = model_path.parent
            import subprocess
            subprocess.Popen(['explorer', str(model_dir)])

    def _mark_complete(self):
        """Mark model stage as complete."""
        project = self.project_manager.current_project
        if not project:
            return

        project.mark_stage_completed("model")
        self.project_manager.save_project()

        messagebox.showinfo(
            "Stage Complete",
            "Anomaly model training completed!\n\n"
            "Proceed to DSP stage to configure signal processing parameters."
        )

    def refresh(self):
        """Refresh panel with current project data."""
        project = self.project_manager.current_project
        if not project:
            return

        # Load feature info asynchronously
        def load_thread():
            try:
                if project.llm.selected_features:
                    self.selected_features = project.llm.selected_features
                    self.features_info_label.configure(
                        text=f"{len(self.selected_features)} features selected",
                        text_color="green"
                    )

                    # Load features to get sample count
                    if project.features.extracted_features:
                        features_path = Path(project.features.extracted_features)
                        file_size = features_path.stat().st_size

                        # Update loading status
                        self.samples_info_label.configure(
                            text=f"Loading {file_size/(1024*1024):.1f} MB...",
                            text_color="blue"
                        )

                        with open(features_path, 'rb') as f:
                            self.features_df = pickle.load(f)

                        n_samples = len(self.features_df)
                        self.samples_info_label.configure(
                            text=f"{n_samples} samples",
                            text_color="green"
                        )

                        # Get task mode for recommendation
                        task_mode = project.data.task_type

                        # Get recommendation based on task mode
                        if task_mode == "classification":
                            # For classification, recommend Random Forest as default
                            recommended = "random_forest"
                            algo_name = CLASSIFIERS[recommended]['name']
                        else:
                            recommended = ModelTrainer.recommend_algorithm(
                                n_samples=n_samples,
                                n_features=len(self.selected_features)
                            )
                            algo_name = ALGORITHMS[recommended]['name']

                        self.recommendation_label.configure(
                            text=f"{algo_name} ({recommended})",
                            text_color="blue"
                        )
                        self.algorithm_var.set(recommended)
                        self._on_algorithm_change()

            except Exception as e:
                logger.error(f"Error loading feature info: {e}")
                self.samples_info_label.configure(
                    text="Error loading features",
                    text_color="red"
                )

        # Run in thread
        threading.Thread(target=load_thread, daemon=True).start()

        # Check if model already trained
        if project.model.trained and project.model.model_path:
            logger.info(f"Loading existing trained model: {project.model.model_path}")

            # Find all trained models (classifiers or anomaly models)
            model_dir = project.get_project_dir() / "models"
            if model_dir.exists():
                # Look for both classifier and anomaly model patterns
                models = list(model_dir.glob("*_classifier.pkl")) + list(model_dir.glob("*_model.pkl"))
                if models:
                    logger.info(f"Found {len(models)} trained model(s)")

                    # Update Training tab - show trained status
                    self.progress_label.configure(
                        text="✓ Model already trained",
                        text_color="green"
                    )
                    self.train_btn.configure(state="normal", text="Re-train Model")

                    # Load and display training metrics if available
                    if project.model.metrics:
                        metrics_text = "Training Metrics:\n"
                        for key, value in project.model.metrics.items():
                            metrics_text += f"  {key}: {value:.4f}\n"
                        self._log_training(metrics_text)

                    # Update Export tab
                    self.export_status_label.configure(
                        text=f"✓ {len(models)} model(s) trained",
                        text_color="green"
                    )
                    # Show all models in the label
                    model_names = [m.stem.replace('_classifier', '').replace('_model', '') for m in models]
                    self.model_path_label.configure(
                        text=f"Algorithms: {', '.join(model_names)}"
                    )
                    self.open_dir_btn.configure(state="normal")
                    self.complete_btn.configure(state="normal")

                    # Load model to populate Explorer tab (classification only)
                    if project.data.task_type == "classification":
                        self._load_existing_model_for_explorer(models[0])
                else:
                    logger.warning(f"Model marked as trained but no model files found in {model_dir}")
            else:
                logger.warning(f"Model marked as trained but model directory doesn't exist: {model_dir}")

    def _load_existing_model_for_explorer(self, model_path: Path):
        """Load existing trained model and populate Explorer tab."""
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)

            # Extract feature importances if available
            model = model_data.get('model')
            feature_names = model_data.get('feature_names', [])

            if model and hasattr(model, 'feature_importances_') and feature_names:
                importances = model.feature_importances_

                # Update feature dropdowns
                self.explorer_x_menu.configure(values=feature_names)
                self.explorer_y_menu.configure(values=feature_names)
                self.explorer_z_menu.configure(values=feature_names)

                # Auto-select top 3 features
                num_features = min(3, len(feature_names))
                if num_features >= 3:
                    sorted_indices = np.argsort(importances)[::-1]
                    top_features = [feature_names[i] for i in sorted_indices[:num_features]]

                    if len(top_features) >= 1:
                        self.explorer_x_var.set(top_features[0])
                    if len(top_features) >= 2:
                        self.explorer_y_var.set(top_features[1])
                    if len(top_features) >= 3:
                        self.explorer_z_var.set(top_features[2])

                    logger.info(f"Explorer tab loaded with top {num_features} features from existing model: {top_features}")

        except Exception as e:
            logger.warning(f"Could not load model for Explorer tab: {e}")

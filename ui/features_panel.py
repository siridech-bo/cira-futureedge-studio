"""
Feature Extraction Panel

UI for feature extraction configuration and execution with support for:
- Operation mode selection (Anomaly Detection / Forecasting)
- 3-level complexity settings
- 3-mode configuration (Simple / Advanced / Per-Sensor)
- Rolling configuration for forecasting
- Feature filtering and visualization
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from pathlib import Path
from typing import Optional, List
import pandas as pd
from loguru import logger
import threading

from core.project import ProjectManager
from core.feature_config import (
    FeatureExtractionConfig,
    ComplexityLevel,
    ConfigurationMode,
    OperationMode,
    RollingConfig,
    FilteringConfig
)
from core.feature_extraction import FeatureExtractionEngine


class FeaturesPanel(ctk.CTkFrame):
    """Panel for feature extraction configuration and execution."""

    def __init__(self, parent, project_manager: ProjectManager, **kwargs):
        """
        Initialize features panel.

        Args:
            parent: Parent widget
            project_manager: Project manager instance
        """
        super().__init__(parent, **kwargs)

        self.project_manager = project_manager
        self.config = FeatureExtractionConfig()
        self.extraction_engine: Optional[FeatureExtractionEngine] = None
        self.extracted_features: Optional[pd.DataFrame] = None

        self._setup_ui()
        self._load_project_features()  # Load existing features if available

    def _setup_ui(self) -> None:
        """Setup UI components."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        title = ctk.CTkLabel(
            header,
            text="🔬 Feature Extraction",
            font=("Segoe UI", 24, "bold")
        )
        title.pack(side="left")

        # Main content with tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

        # Add tabs
        self.tabview.add("Configuration")
        self.tabview.add("Extraction")
        self.tabview.add("Filtering")
        self.tabview.add("Results")

        # Setup each tab
        self._setup_config_tab()
        self._setup_extraction_tab()
        self._setup_filtering_tab()
        self._setup_results_tab()

    def _setup_config_tab(self) -> None:
        """Setup configuration tab."""
        tab = self.tabview.tab("Configuration")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        # Main container frame (no scrolling)
        container = ctk.CTkFrame(tab, fg_color="transparent")
        container.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=20, pady=20)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

        # LEFT COLUMN: Operation Mode Section
        mode_frame = ctk.CTkFrame(container)
        mode_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 10), pady=0)
        mode_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            mode_frame,
            text="Operation Mode:",
            font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        # Auto-detect mode from project
        default_mode = "anomaly_detection"
        if self.project_manager.has_project():
            project = self.project_manager.current_project
            if hasattr(project.data, 'task_type'):
                default_mode = project.data.task_type

        self.mode_var = ctk.StringVar(value=default_mode)

        anomaly_radio = ctk.CTkRadioButton(
            mode_frame,
            text="⚠️ Anomaly Detection - Detect abnormal patterns",
            variable=self.mode_var,
            value="anomaly_detection",
            command=self._on_mode_change
        )
        anomaly_radio.grid(row=1, column=0, sticky="w", padx=30, pady=5)

        classification_radio = ctk.CTkRadioButton(
            mode_frame,
            text="🎓 Classification - Categorize sensor patterns",
            variable=self.mode_var,
            value="classification",
            command=self._on_mode_change
        )
        classification_radio.grid(row=2, column=0, sticky="w", padx=30, pady=5)

        forecast_radio = ctk.CTkRadioButton(
            mode_frame,
            text="📈 Time Series Forecasting - Predict future values",
            variable=self.mode_var,
            value="forecasting",
            command=self._on_mode_change
        )
        forecast_radio.grid(row=3, column=0, sticky="w", padx=30, pady=(5, 15))

        # Info text at bottom of Operation Mode
        mode_info = ctk.CTkLabel(
            mode_frame,
            text="Select the appropriate mode based on your\nproject task type configured in Data Sources.",
            font=("Segoe UI", 10),
            text_color="gray",
            justify="left",
            wraplength=300
        )
        mode_info.grid(row=4, column=0, sticky="w", padx=30, pady=(10, 10))

        # RIGHT COLUMN TOP: Complexity Level Section
        complexity_frame = ctk.CTkFrame(container)
        complexity_frame.grid(row=0, column=1, sticky="new", padx=(10, 0), pady=0)
        complexity_frame.grid_columnconfigure(0, weight=0)
        complexity_frame.grid_columnconfigure(1, weight=0)

        ctk.CTkLabel(
            complexity_frame,
            text="Feature Complexity:",
            font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, sticky="w", padx=10, pady=10)

        self.complexity_var = ctk.StringVar(value="efficient")
        complexity_menu = ctk.CTkOptionMenu(
            complexity_frame,
            variable=self.complexity_var,
            values=["minimal", "efficient", "comprehensive"],
            command=self._on_complexity_change,
            width=250
        )
        complexity_menu.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # Complexity descriptions
        ctk.CTkLabel(
            complexity_frame,
            text="• Minimal: ~50 features, fastest\n"
                 "• Efficient: ~300 features, balanced (recommended)\n"
                 "• Comprehensive: 700+ features, slowest",
            font=("Segoe UI", 11),
            text_color="lightgray",
            justify="left"
        ).grid(row=1, column=0, columnspan=2, sticky="w", padx=30, pady=(5, 10))

        # RIGHT COLUMN BOTTOM: Configuration Mode Section
        config_mode_frame = ctk.CTkFrame(container)
        config_mode_frame.grid(row=1, column=1, sticky="new", padx=(10, 0), pady=(20, 0))
        config_mode_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            config_mode_frame,
            text="Configuration Mode:",
            font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))

        self.config_mode_var = ctk.StringVar(value="simple")

        simple_radio = ctk.CTkRadioButton(
            config_mode_frame,
            text="Simple - Use preset defaults (for the lazy)",
            variable=self.config_mode_var,
            value="simple",
            command=self._on_config_mode_change
        )
        simple_radio.grid(row=1, column=0, columnspan=2, sticky="w", padx=30, pady=5)

        advanced_radio = ctk.CTkRadioButton(
            config_mode_frame,
            text="Advanced - Global custom settings (for the advanced)",
            variable=self.config_mode_var,
            value="advanced",
            command=self._on_config_mode_change
        )
        advanced_radio.grid(row=2, column=0, columnspan=2, sticky="w", padx=30, pady=5)

        per_sensor_radio = ctk.CTkRadioButton(
            config_mode_frame,
            text="Per-Sensor - Different settings per sensor (for the ambitious)",
            variable=self.config_mode_var,
            value="per_sensor",
            command=self._on_config_mode_change
        )
        per_sensor_radio.grid(row=3, column=0, columnspan=2, sticky="w", padx=30, pady=(5, 10))

        # BOTTOM ROW: Rolling Configuration (for forecasting) - spans both columns
        self.rolling_frame = ctk.CTkFrame(container)
        self.rolling_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=0, pady=(20, 0))
        self.rolling_frame.grid_columnconfigure(1, weight=1)
        self.rolling_frame.grid_remove()  # Hidden by default

        ctk.CTkLabel(
            self.rolling_frame,
            text="Rolling Configuration:",
            font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=10)

        # Max timeshift
        ctk.CTkLabel(
            self.rolling_frame,
            text="Max Timeshift (lookback):",
            font=("Segoe UI", 12)
        ).grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.max_timeshift_var = ctk.StringVar(value="100")
        max_timeshift_entry = ctk.CTkEntry(
            self.rolling_frame,
            textvariable=self.max_timeshift_var,
            width=150
        )
        max_timeshift_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # Min timeshift
        ctk.CTkLabel(
            self.rolling_frame,
            text="Min Timeshift (min history):",
            font=("Segoe UI", 12)
        ).grid(row=2, column=0, padx=10, pady=5, sticky="w")

        self.min_timeshift_var = ctk.StringVar(value="10")
        min_timeshift_entry = ctk.CTkEntry(
            self.rolling_frame,
            textvariable=self.min_timeshift_var,
            width=150
        )
        min_timeshift_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        # Target column
        ctk.CTkLabel(
            self.rolling_frame,
            text="Target Column to Predict:",
            font=("Segoe UI", 12)
        ).grid(row=3, column=0, padx=10, pady=5, sticky="w")

        self.target_column_var = ctk.StringVar(value="")
        self.target_column_menu = ctk.CTkOptionMenu(
            self.rolling_frame,
            variable=self.target_column_var,
            values=["(select after loading data)"]
        )
        self.target_column_menu.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        # Prediction horizon
        ctk.CTkLabel(
            self.rolling_frame,
            text="Prediction Horizon:",
            font=("Segoe UI", 12)
        ).grid(row=4, column=0, padx=10, pady=5, sticky="w")

        self.prediction_horizon_var = ctk.StringVar(value="1")
        horizon_entry = ctk.CTkEntry(
            self.rolling_frame,
            textvariable=self.prediction_horizon_var,
            width=150
        )
        horizon_entry.grid(row=4, column=1, padx=10, pady=(5, 10), sticky="w")

        # BOTTOM: Computation Settings - spans both columns
        compute_frame = ctk.CTkFrame(container)
        compute_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=0, pady=(20, 0))
        compute_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            compute_frame,
            text="Computation Settings:",
            font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=10)

        # Number of parallel jobs
        ctk.CTkLabel(
            compute_frame,
            text="Parallel Jobs:",
            font=("Segoe UI", 12)
        ).grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.n_jobs_var = ctk.StringVar(value="4")
        n_jobs_entry = ctk.CTkEntry(
            compute_frame,
            textvariable=self.n_jobs_var,
            width=150
        )
        n_jobs_entry.grid(row=1, column=1, padx=10, pady=(5, 10), sticky="w")

    def _setup_extraction_tab(self) -> None:
        """Setup extraction tab."""
        tab = self.tabview.tab("Extraction")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Info frame
        info_frame = ctk.CTkFrame(tab)
        info_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.extraction_info_label = ctk.CTkLabel(
            info_frame,
            text="Configure extraction settings in Configuration tab",
            font=("Segoe UI", 12),
            text_color="gray"
        )
        self.extraction_info_label.pack(padx=20, pady=20)

        # Extract button
        extract_frame = ctk.CTkFrame(tab, fg_color="transparent")
        extract_frame.grid(row=1, column=0, pady=20)

        self.extract_btn = ctk.CTkButton(
            extract_frame,
            text="🚀 Extract Features",
            command=self._extract_features,
            width=200,
            height=50,
            font=("Segoe UI", 16, "bold"),
            state="disabled"
        )
        self.extract_btn.pack()

        # Progress bar
        self.extraction_progress = ctk.CTkProgressBar(
            tab,
            width=400,
            mode="indeterminate"
        )
        self.extraction_progress.grid(row=2, column=0, pady=10)
        self.extraction_progress.grid_remove()  # Hidden by default

        # Progress info
        self.progress_label = ctk.CTkLabel(
            tab,
            text="",
            font=("Segoe UI", 11),
            text_color="gray"
        )
        self.progress_label.grid(row=3, column=0, pady=5)

        # Status
        self.extraction_status_label = ctk.CTkLabel(
            tab,
            text="",
            font=("Segoe UI", 11)
        )
        self.extraction_status_label.grid(row=4, column=0, pady=5)

    def _setup_filtering_tab(self) -> None:
        """Setup filtering tab."""
        tab = self.tabview.tab("Filtering")
        tab.grid_columnconfigure(0, weight=1)

        # Filtering settings
        filter_frame = ctk.CTkFrame(tab)
        filter_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        filter_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            filter_frame,
            text="Feature Filtering Settings:",
            font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=10)

        # Enable filtering
        self.enable_filtering_var = ctk.BooleanVar(value=True)
        filtering_check = ctk.CTkCheckBox(
            filter_frame,
            text="Enable statistical filtering",
            variable=self.enable_filtering_var
        )
        filtering_check.grid(row=1, column=0, columnspan=2, sticky="w", padx=30, pady=5)

        # P-value threshold
        ctk.CTkLabel(
            filter_frame,
            text="P-value Threshold:",
            font=("Segoe UI", 12)
        ).grid(row=2, column=0, padx=30, pady=5, sticky="w")

        self.p_value_var = ctk.StringVar(value="0.05")
        p_value_entry = ctk.CTkEntry(
            filter_frame,
            textvariable=self.p_value_var,
            width=150
        )
        p_value_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        # FDR level
        ctk.CTkLabel(
            filter_frame,
            text="FDR Level:",
            font=("Segoe UI", 12)
        ).grid(row=3, column=0, padx=30, pady=5, sticky="w")

        self.fdr_level_var = ctk.StringVar(value="0.05")
        fdr_entry = ctk.CTkEntry(
            filter_frame,
            textvariable=self.fdr_level_var,
            width=150
        )
        fdr_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        # Additional filtering
        self.remove_low_var_var = ctk.BooleanVar(value=True)
        low_var_check = ctk.CTkCheckBox(
            filter_frame,
            text="Remove low variance features",
            variable=self.remove_low_var_var
        )
        low_var_check.grid(row=4, column=0, columnspan=2, sticky="w", padx=30, pady=5)

        self.remove_corr_var = ctk.BooleanVar(value=True)
        corr_check = ctk.CTkCheckBox(
            filter_frame,
            text="Remove highly correlated features (>0.95)",
            variable=self.remove_corr_var
        )
        corr_check.grid(row=5, column=0, columnspan=2, sticky="w", padx=30, pady=(5, 10))

    def _setup_results_tab(self) -> None:
        """Setup results tab - simple and fast."""
        tab = self.tabview.tab("Results")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Info frame
        info_frame = ctk.CTkFrame(tab)
        info_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.results_info_label = ctk.CTkLabel(
            info_frame,
            text="No features extracted yet",
            font=("Segoe UI", 12),
            text_color="gray"
        )
        self.results_info_label.pack(padx=20, pady=20)

        # Results display (simple textbox for fast rendering)
        results_frame = ctk.CTkScrollableFrame(tab)
        results_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        results_frame.grid_columnconfigure(0, weight=1)

        self.results_text = ctk.CTkTextbox(
            results_frame,
            font=("Consolas", 10),
            wrap="none"
        )
        self.results_text.pack(fill="both", expand=True)

        # Export button
        export_frame = ctk.CTkFrame(tab, fg_color="transparent")
        export_frame.grid(row=2, column=0, pady=10)

        self.export_btn = ctk.CTkButton(
            export_frame,
            text="💾 Export Features",
            command=self._export_features,
            state="disabled"
        )
        self.export_btn.pack()

    def _on_mode_change(self) -> None:
        """Handle operation mode change."""
        mode = self.mode_var.get()
        logger.info(f"Operation mode changed to: {mode}")

        if mode == "forecasting":
            self.rolling_frame.grid()
        else:
            self.rolling_frame.grid_remove()

        self._update_extraction_info()

    def _on_complexity_change(self, choice: str) -> None:
        """Handle complexity change."""
        logger.info(f"Complexity changed to: {choice}")
        self._update_extraction_info()

    def _on_config_mode_change(self) -> None:
        """Handle configuration mode change."""
        mode = self.config_mode_var.get()
        logger.info(f"Configuration mode changed to: {mode}")
        # TODO: Show/hide appropriate configuration panels

    def _update_extraction_info(self) -> None:
        """Update extraction info label."""
        if not self.project_manager.has_project():
            self.extraction_info_label.configure(
                text="⚠️ No project loaded. Create or open a project first."
            )
            self.extract_btn.configure(state="disabled")
            return

        project = self.project_manager.current_project

        # Check if data stage is completed
        if not project.is_stage_completed("data"):
            self.extraction_info_label.configure(
                text="⚠️ Complete Data Sources stage first"
            )
            self.extract_btn.configure(state="disabled")
            return

        # Check if windows exist
        if not project.data.num_windows or project.data.num_windows == 0:
            self.extraction_info_label.configure(
                text="⚠️ No windows created. Create windows in Data Sources stage."
            )
            self.extract_btn.configure(state="disabled")
            return

        # Ready to extract
        mode = self.mode_var.get()
        complexity = self.complexity_var.get()
        num_windows = project.data.num_windows

        info_text = f"✓ Ready to extract features\n"
        info_text += f"  Mode: {mode}\n"
        info_text += f"  Complexity: {complexity}\n"
        info_text += f"  Windows: {num_windows}"

        self.extraction_info_label.configure(text=info_text)
        self.extract_btn.configure(state="normal")

    def _extract_features(self) -> None:
        """Extract features from windows."""
        if not self.project_manager.has_project():
            messagebox.showwarning("No Project", "Please create or open a project first.")
            return

        try:
            # Build configuration
            self.config = self._build_config()

            # Get project data
            project = self.project_manager.current_project

            # Check if we have separate train/test windows
            if project.data.train_test_split_type == "manual":
                # Load train and test windows separately
                import pickle

                if not project.data.train_windows_file:
                    messagebox.showwarning("No Data", "No training windows available. Create windows first.")
                    return

                with open(project.data.train_windows_file, 'rb') as f:
                    train_windows = pickle.load(f)

                test_windows = []
                if project.data.test_windows_file:
                    with open(project.data.test_windows_file, 'rb') as f:
                        test_windows = pickle.load(f)

                windows = None  # Not used in manual split mode
            else:
                # Load combined windows
                windows = project.load_windows()
                train_windows = None
                test_windows = None

                if not windows:
                    messagebox.showwarning("No Data", "No windows available. Create windows first.")
                    return

            sensor_columns = project.data.sensor_columns

            # Disable extract button and show progress
            self.extract_btn.configure(state="disabled")
            self.extraction_progress.grid()
            self.extraction_progress.start()
            self.progress_label.configure(text="🔄 Extracting features... (this may take several minutes)")
            self.extraction_status_label.configure(text="")

            # Run extraction in thread
            def extraction_thread():
                try:
                    self.extraction_engine = FeatureExtractionEngine(self.config)

                    if self.config.is_forecasting_mode():
                        # TODO: Implement rolling extraction
                        self._show_error("Forecasting mode not yet implemented")
                        return
                    else:
                        # Check if manual train/test split
                        if project.data.train_test_split_type == "manual":
                            # Extract features separately for train and test
                            total_train = len(train_windows)
                            total_test = len(test_windows) if test_windows else 0

                            logger.info(f"Extracting features from {total_train} train windows")
                            self.after(0, lambda: self.progress_label.configure(
                                text=f"🔄 Extracting features from training data ({total_train} windows)..."
                            ))

                            train_features = self.extraction_engine.extract_from_windows(
                                train_windows,
                                sensor_columns
                            )

                            test_features = None
                            if test_windows:
                                logger.info(f"Extracting features from {total_test} test windows")
                                self.after(0, lambda: self.progress_label.configure(
                                    text=f"🔄 Extracting features from testing data ({total_test} windows)..."
                                ))

                                test_features = self.extraction_engine.extract_from_windows(
                                    test_windows,
                                    sensor_columns
                                )

                            # Store train and test features separately
                            self.train_features = train_features
                            self.test_features = test_features

                            # For display, combine features
                            if test_features is not None:
                                features = pd.concat([train_features, test_features], ignore_index=True)
                            else:
                                features = train_features
                        else:
                            # Standard extraction
                            num_windows = len(windows) if windows else 0
                            self.after(0, lambda: self.progress_label.configure(
                                text=f"🔄 Extracting features from {num_windows} windows..."
                            ))

                            features = self.extraction_engine.extract_from_windows(
                                windows,
                                sensor_columns
                            )

                    self.extracted_features = features

                    # Update UI (must use after() for thread safety)
                    self.after(0, self._extraction_complete, features)

                except Exception as e:
                    self.after(0, self._extraction_error, str(e))

            thread = threading.Thread(target=extraction_thread, daemon=True)
            thread.start()

        except Exception as e:
            logger.error(f"Failed to start extraction: {e}")
            messagebox.showerror("Error", f"Failed to start extraction:\n{e}")
            self.extract_btn.configure(state="normal")

    def _extraction_complete(self, features: pd.DataFrame) -> None:
        """Handle extraction completion."""
        # Stop and hide progress
        self.extraction_progress.stop()
        self.extraction_progress.grid_remove()
        self.progress_label.configure(text="")

        self.extraction_status_label.configure(
            text=f"✓ Extracted {features.shape[1]} features from {features.shape[0]} windows",
            text_color="green"
        )
        self.extract_btn.configure(state="normal")
        self.export_btn.configure(state="normal")

        # Update results
        self._display_results()

        # Save features to disk
        project = self.project_manager.current_project
        features_dir = project.get_features_dir()
        features_dir.mkdir(parents=True, exist_ok=True)

        import pickle

        # Save train/test features separately if manual split
        if project.data.train_test_split_type == "manual":
            # Save training features
            train_features_file = features_dir / "train_features.pkl"
            with open(train_features_file, 'wb') as f:
                pickle.dump(self.train_features, f)
            logger.info(f"Saved {self.train_features.shape[1]} train features to {train_features_file}")

            # Save test features if available
            if self.test_features is not None:
                test_features_file = features_dir / "test_features.pkl"
                with open(test_features_file, 'wb') as f:
                    pickle.dump(self.test_features, f)
                logger.info(f"Saved {self.test_features.shape[1]} test features to {test_features_file}")

        # Also save combined features for compatibility
        features_file = features_dir / "extracted.pkl"
        with open(features_file, 'wb') as f:
            pickle.dump(features, f)

        logger.info(f"Saved {features.shape[1]} features to {features_file}")

        # Update project metadata
        project.features.extracted = True
        project.features.feature_names = list(features.columns)
        project.features.num_features_extracted = features.shape[1]
        project.features.extracted_features = str(features_file)
        project.mark_stage_completed("features")
        project.save()

        logger.info("Feature extraction completed successfully")

    def _extraction_error(self, error: str) -> None:
        """Handle extraction error."""
        # Stop and hide progress bar
        self.extraction_progress.stop()
        self.extraction_progress.grid_remove()
        self.progress_label.configure(text="")

        self.extraction_status_label.configure(
            text=f"✗ Error: {error}",
            text_color="red"
        )
        self.extract_btn.configure(state="normal")
        messagebox.showerror("Extraction Error", f"Feature extraction failed:\n{error}")

    def _show_error(self, message: str) -> None:
        """Show error message (thread-safe)."""
        self.after(0, lambda: messagebox.showerror("Error", message))
        self.after(0, lambda: self.extract_btn.configure(state="normal"))
        self.after(0, lambda: self.extraction_progress.stop())
        self.after(0, lambda: self.extraction_progress.grid_remove())
        self.after(0, lambda: self.progress_label.configure(text=""))

    def _build_config(self) -> FeatureExtractionConfig:
        """Build configuration from UI values."""
        config = FeatureExtractionConfig()

        # Operation mode
        config.operation_mode = OperationMode(self.mode_var.get())

        # Complexity
        config.complexity_level = ComplexityLevel(self.complexity_var.get())

        # Configuration mode
        config.configuration_mode = ConfigurationMode(self.config_mode_var.get())

        # Rolling config (if forecasting)
        if config.operation_mode == OperationMode.FORECASTING:
            config.rolling_config = RollingConfig(
                enabled=True,
                max_timeshift=int(self.max_timeshift_var.get()),
                min_timeshift=int(self.min_timeshift_var.get()),
                target_column=self.target_column_var.get(),
                prediction_horizon=int(self.prediction_horizon_var.get())
            )

        # Filtering config
        config.filtering_config = FilteringConfig(
            enabled=self.enable_filtering_var.get(),
            p_value_threshold=float(self.p_value_var.get()),
            fdr_level=float(self.fdr_level_var.get()),
            remove_low_variance=self.remove_low_var_var.get(),
            remove_highly_correlated=self.remove_corr_var.get()
        )

        # Computation
        config.n_jobs = int(self.n_jobs_var.get())

        return config

    def _display_results(self) -> None:
        """Display extraction results - simple text format."""
        if self.extracted_features is None:
            return

        # Get statistics
        stats = self.extraction_engine.get_feature_statistics()

        # Build simple text results
        results = f"✓ Extraction Complete!\n\n"
        results += f"Total Features: {stats['total_features']}\n"
        results += f"Samples: {stats['num_samples']}\n"
        results += f"Memory Usage: {stats['memory_usage_mb']:.2f} MB\n\n"

        if 'filtered_features' in stats:
            results += f"Filtered Features: {stats['filtered_features']}\n"
            results += f"Reduction: {stats['reduction_percent']:.1f}%\n\n"

        results += "=" * 80 + "\n"
        results += "Feature Names:\n"
        results += "=" * 80 + "\n\n"

        # List all features (no limit)
        for i, name in enumerate(stats['feature_names'], 1):
            results += f"{i:4d}. {name}\n"

        # Display in textbox
        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", results)

        self.results_info_label.configure(
            text=f"✓ Extracted {stats['total_features']} features from {stats['num_samples']} samples",
            text_color="green"
        )

    def _export_features(self) -> None:
        """Export features to file."""
        if self.extracted_features is None:
            messagebox.showwarning("No Features", "No features to export.")
            return

        filename = filedialog.asksaveasfilename(
            title="Export Features",
            defaultextension=".parquet",
            filetypes=[
                ("Parquet files", "*.parquet"),
                ("CSV files", "*.csv"),
                ("HDF5 files", "*.h5"),
                ("All files", "*.*")
            ]
        )

        if filename:
            try:
                path = Path(filename)
                format = path.suffix[1:]  # Remove dot

                self.extraction_engine.export_features(path, format)
                messagebox.showinfo("Success", f"Features exported to:\n{filename}")
                logger.info(f"Features exported to {filename}")

            except Exception as e:
                logger.error(f"Failed to export features: {e}")
                messagebox.showerror("Error", f"Failed to export features:\n{e}")

    def _setup_explorer_tab(self) -> None:
        """Setup feature explorer tab for 3D visualization."""
        tab = self.tabview.tab("Explorer")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Scrollable frame
        scroll = ctk.CTkScrollableFrame(tab)
        scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scroll.grid_columnconfigure(0, weight=1)

        # Title
        title_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        ctk.CTkLabel(
            title_frame,
            text="🔍 Feature Explorer - 3D Visualization",
            font=("Segoe UI", 16, "bold")
        ).pack(side="left")

        # Info label
        info_text = "Visualize how features separate your classes in 3D space. Select 3 features to plot as X, Y, and Z axes."
        ctk.CTkLabel(
            scroll,
            text=info_text,
            font=("Segoe UI", 10),
            text_color="gray",
            wraplength=600,
            justify="left"
        ).grid(row=1, column=0, sticky="w", padx=10, pady=(0, 20))

        # Feature selection frame
        selection_frame = ctk.CTkFrame(scroll)
        selection_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        selection_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            selection_frame,
            text="Select 3 Features:",
            font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        # X-axis selection
        ctk.CTkLabel(
            selection_frame,
            text="X-Axis:",
            font=("Segoe UI", 12)
        ).grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.explorer_x_var = ctk.StringVar(value="No features available")
        self.explorer_x_menu = ctk.CTkOptionMenu(
            selection_frame,
            variable=self.explorer_x_var,
            values=["No features available"],
            width=400
        )
        self.explorer_x_menu.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # Y-axis selection
        ctk.CTkLabel(
            selection_frame,
            text="Y-Axis:",
            font=("Segoe UI", 12)
        ).grid(row=2, column=0, padx=10, pady=5, sticky="w")

        self.explorer_y_var = ctk.StringVar(value="No features available")
        self.explorer_y_menu = ctk.CTkOptionMenu(
            selection_frame,
            variable=self.explorer_y_var,
            values=["No features available"],
            width=400
        )
        self.explorer_y_menu.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        # Z-axis selection
        ctk.CTkLabel(
            selection_frame,
            text="Z-Axis:",
            font=("Segoe UI", 12)
        ).grid(row=3, column=0, padx=10, pady=5, sticky="w")

        self.explorer_z_var = ctk.StringVar(value="No features available")
        self.explorer_z_menu = ctk.CTkOptionMenu(
            selection_frame,
            variable=self.explorer_z_var,
            values=["No features available"],
            width=400
        )
        self.explorer_z_menu.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        # Quick action buttons
        button_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        button_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)

        self.use_top3_btn = ctk.CTkButton(
            button_frame,
            text="📊 Use Top 3 Important Features",
            command=self._use_top3_features,
            width=200,
            fg_color="green",
            hover_color="darkgreen"
        )
        self.use_top3_btn.pack(side="left", padx=5)

        self.randomize_btn = ctk.CTkButton(
            button_frame,
            text="🎲 Randomize Features",
            command=self._randomize_features,
            width=180
        )
        self.randomize_btn.pack(side="left", padx=5)

        # Visualize button
        visualize_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        visualize_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=20)

        self.visualize_btn = ctk.CTkButton(
            visualize_frame,
            text="🚀 Visualize in 3D",
            command=self._visualize_3d,
            width=300,
            height=40,
            font=("Segoe UI", 14, "bold"),
            fg_color="#1f6aa5",
            hover_color="#144870"
        )
        self.visualize_btn.pack()

        # Status label
        self.explorer_status_label = ctk.CTkLabel(
            scroll,
            text="Extract features first to enable visualization",
            font=("Segoe UI", 11),
            text_color="orange"
        )
        self.explorer_status_label.grid(row=5, column=0, padx=10, pady=10)

    def _use_top3_features(self):
        """Auto-populate dropdowns with top 3 most important features."""
        if self.extracted_features is None or self.extracted_features.shape[1] < 3:
            messagebox.showwarning("No Features", "Extract features first or need at least 3 features.")
            return

        # Get feature names
        feature_names = list(self.extracted_features.columns)

        # Check if we have feature importances from trained model
        project = self.project_manager.current_project
        if project and hasattr(project, 'model') and hasattr(project.model, 'feature_importances'):
            # Use model's feature importance if available
            try:
                import pickle
                model_path = project.model.model_path
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)

                if hasattr(model, 'feature_importances_'):
                    importances = model.feature_importances_
                    # Sort features by importance
                    sorted_indices = importances.argsort()[::-1]
                    sorted_features = [feature_names[i] for i in sorted_indices[:3]]

                    self.explorer_x_var.set(sorted_features[0])
                    self.explorer_y_var.set(sorted_features[1])
                    self.explorer_z_var.set(sorted_features[2])

                    self.explorer_status_label.configure(
                        text=f"✓ Selected top 3 features by importance",
                        text_color="green"
                    )
                    return
            except Exception as e:
                logger.warning(f"Could not load feature importances: {e}")

        # Fallback: just use first 3 features
        self.explorer_x_var.set(feature_names[0])
        self.explorer_y_var.set(feature_names[1])
        self.explorer_z_var.set(feature_names[2])

        self.explorer_status_label.configure(
            text="✓ Selected first 3 features (train model to see importance-based selection)",
            text_color="blue"
        )

    def _randomize_features(self):
        """Randomly select 3 features."""
        if not self.extracted_features or self.extracted_features.shape[1] < 3:
            messagebox.showwarning("No Features", "Extract features first.")
            return

        import random
        feature_names = list(self.extracted_features.columns)
        random_features = random.sample(feature_names, 3)

        self.explorer_x_var.set(random_features[0])
        self.explorer_y_var.set(random_features[1])
        self.explorer_z_var.set(random_features[2])

        self.explorer_status_label.configure(
            text="✓ Randomly selected 3 features",
            text_color="blue"
        )

    def _visualize_3d(self):
        """Create 3D visualization using Plotly."""
        if self.extracted_features is None:
            messagebox.showwarning("No Features", "Please extract features first.")
            return

        # Get selected features
        x_feature = self.explorer_x_var.get()
        y_feature = self.explorer_y_var.get()
        z_feature = self.explorer_z_var.get()

        if x_feature == "No features available":
            messagebox.showwarning("No Features", "Please extract features first.")
            return

        # Check if features are the same
        if len({x_feature, y_feature, z_feature}) < 3:
            messagebox.showwarning("Duplicate Features", "Please select 3 different features.")
            return

        try:
            # Get project and windows for labels
            project = self.project_manager.current_project
            if not project:
                messagebox.showerror("No Project", "No project loaded.")
                return

            # Load windows to get labels
            if project.data.train_test_split_type == "manual":
                # Load combined windows
                import pickle
                if project.data.train_windows_file:
                    with open(project.data.train_windows_file, 'rb') as f:
                        train_windows = pickle.load(f)
                    windows = train_windows

                    if project.data.test_windows_file:
                        with open(project.data.test_windows_file, 'rb') as f:
                            test_windows = pickle.load(f)
                        windows = train_windows + test_windows
                else:
                    windows = project.load_windows()
            else:
                windows = project.load_windows()

            if not windows:
                messagebox.showwarning("No Windows", "No windows found. Create windows first.")
                return

            # Extract labels
            labels = [w.class_label if hasattr(w, 'class_label') and w.class_label else "unlabeled" for w in windows]

            # Create 3D visualization with Plotly
            try:
                import plotly.graph_objects as go
                import webbrowser
                import tempfile
                import os

                # Get data
                x_data = self.extracted_features[x_feature].values
                y_data = self.extracted_features[y_feature].values
                z_data = self.extracted_features[z_feature].values

                # Create scatter plot for each class
                unique_labels = sorted(set(labels))
                traces = []

                colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                         '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

                for idx, label in enumerate(unique_labels):
                    mask = [l == label for l in labels]
                    trace = go.Scatter3d(
                        x=x_data[mask],
                        y=y_data[mask],
                        z=z_data[mask],
                        mode='markers',
                        name=label,
                        marker=dict(
                            size=5,
                            color=colors[idx % len(colors)],
                            opacity=0.8,
                            line=dict(color='white', width=0.5)
                        )
                    )
                    traces.append(trace)

                # Create figure
                fig = go.Figure(data=traces)

                fig.update_layout(
                    title=f"Feature Explorer ({len(labels)} samples)",
                    scene=dict(
                        xaxis_title=x_feature,
                        yaxis_title=y_feature,
                        zaxis_title=z_feature,
                        xaxis=dict(backgroundcolor="rgb(230, 230,230)"),
                        yaxis=dict(backgroundcolor="rgb(230, 230,230)"),
                        zaxis=dict(backgroundcolor="rgb(230, 230,230)"),
                    ),
                    width=1200,
                    height=800,
                    hovermode='closest'
                )

                # Save to temp HTML file and open in browser
                temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False)
                fig.write_html(temp_file.name)
                temp_file.close()

                webbrowser.open('file://' + os.path.realpath(temp_file.name))

                self.explorer_status_label.configure(
                    text=f"✓ 3D visualization opened in browser ({len(unique_labels)} classes)",
                    text_color="green"
                )

                logger.info(f"Feature Explorer: Visualized {x_feature} vs {y_feature} vs {z_feature}")

            except ImportError:
                messagebox.showerror(
                    "Missing Library",
                    "Plotly is required for 3D visualization.\n\nInstall with:\npip install plotly"
                )

        except Exception as e:
            logger.error(f"Failed to create 3D visualization: {e}")
            messagebox.showerror("Visualization Error", f"Failed to create visualization:\n{e}")

    def _load_project_features(self) -> None:
        """Load and display existing extracted features if available."""
        if not self.project_manager.has_project():
            return

        project = self.project_manager.current_project

        # Check if features were extracted
        if project.features.extracted and project.features.extracted_features:
            try:
                import pickle
                from pathlib import Path

                features_path = Path(project.features.extracted_features)

                # Load features from pickle file
                if features_path.exists():
                    with open(features_path, 'rb') as f:
                        self.extracted_features = pickle.load(f)

                    # Create a mock extraction engine with the loaded features
                    from core.feature_extraction import FeatureExtractionEngine
                    self.extraction_engine = FeatureExtractionEngine(FeatureExtractionConfig())
                    self.extraction_engine.extracted_features = self.extracted_features
                    self.extraction_engine.feature_names = list(self.extracted_features.columns)

                    # Enable export button
                    self.export_btn.configure(state="normal")

                    # Display results
                    self._display_results()

                    num_features = len(project.features.feature_names)
                    num_samples = len(self.extracted_features)
                    logger.info(f"Loaded extracted features: {num_features} features, {num_samples} samples")
                else:
                    logger.warning(f"Features file not found: {features_path}")

            except Exception as e:
                logger.error(f"Error loading features: {e}")
                import traceback
                traceback.print_exc()

    def refresh(self) -> None:
        """Refresh panel with current project data."""
        self._update_extraction_info()

        # Auto-select operation mode from project task_type
        if self.project_manager.has_project():
            project = self.project_manager.current_project

            # Update mode selector
            if hasattr(project.data, 'task_type'):
                self.mode_var.set(project.data.task_type)
                self._on_mode_change()  # Update UI based on mode

            # Update target column options if in forecasting mode
            if hasattr(project.data, 'sensor_columns') and project.data.sensor_columns:
                self.target_column_menu.configure(values=project.data.sensor_columns)

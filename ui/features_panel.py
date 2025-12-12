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

        # Scrollable frame
        scroll = ctk.CTkScrollableFrame(tab)
        scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scroll.grid_columnconfigure(0, weight=1)

        # Operation Mode Section
        mode_frame = ctk.CTkFrame(scroll)
        mode_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        mode_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            mode_frame,
            text="Operation Mode:",
            font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))

        self.mode_var = ctk.StringVar(value="anomaly_detection")

        anomaly_radio = ctk.CTkRadioButton(
            mode_frame,
            text="⚠️ Anomaly Detection - Detect abnormal patterns",
            variable=self.mode_var,
            value="anomaly_detection",
            command=self._on_mode_change
        )
        anomaly_radio.grid(row=1, column=0, columnspan=2, sticky="w", padx=30, pady=5)

        forecast_radio = ctk.CTkRadioButton(
            mode_frame,
            text="📈 Time Series Forecasting - Predict future values",
            variable=self.mode_var,
            value="forecasting",
            command=self._on_mode_change
        )
        forecast_radio.grid(row=2, column=0, columnspan=2, sticky="w", padx=30, pady=(5, 10))

        # Complexity Level Section
        complexity_frame = ctk.CTkFrame(scroll)
        complexity_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        complexity_frame.grid_columnconfigure(1, weight=1)

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
            command=self._on_complexity_change
        )
        complexity_menu.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # Complexity descriptions
        ctk.CTkLabel(
            complexity_frame,
            text="• Minimal: ~50 features, fastest\n"
                 "• Efficient: ~300 features, balanced (recommended)\n"
                 "• Comprehensive: 700+ features, slowest",
            font=("Segoe UI", 10),
            text_color="gray",
            justify="left"
        ).grid(row=1, column=0, columnspan=2, sticky="w", padx=30, pady=(0, 10))

        # Configuration Mode Section
        config_mode_frame = ctk.CTkFrame(scroll)
        config_mode_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
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

        # Rolling Configuration (for forecasting)
        self.rolling_frame = ctk.CTkFrame(scroll)
        self.rolling_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
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

        # Computation Settings
        compute_frame = ctk.CTkFrame(scroll)
        compute_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=10)
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

        # Progress info
        self.progress_label = ctk.CTkLabel(
            tab,
            text="",
            font=("Segoe UI", 11),
            text_color="gray"
        )
        self.progress_label.grid(row=2, column=0, pady=5)

        # Status
        self.extraction_status_label = ctk.CTkLabel(
            tab,
            text="",
            font=("Segoe UI", 11)
        )
        self.extraction_status_label.grid(row=3, column=0, pady=5)

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
        """Setup results tab."""
        tab = self.tabview.tab("Results")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Results info
        results_info_frame = ctk.CTkFrame(tab)
        results_info_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.results_info_label = ctk.CTkLabel(
            results_info_frame,
            text="No features extracted yet",
            font=("Segoe UI", 12),
            text_color="gray"
        )
        self.results_info_label.pack(padx=20, pady=20)

        # Results display
        results_frame = ctk.CTkScrollableFrame(tab)
        results_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        results_frame.grid_columnconfigure(0, weight=1)

        self.results_text = ctk.CTkTextbox(
            results_frame,
            font=("Courier New", 10),
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

            # Load windows from disk
            windows = project.load_windows()
            sensor_columns = project.data.sensor_columns

            if not windows:
                messagebox.showwarning("No Data", "No windows available. Create windows first.")
                return

            # Disable extract button
            self.extract_btn.configure(state="disabled")
            self.progress_label.configure(text="Extracting features...")

            # Run extraction in thread
            def extraction_thread():
                try:
                    self.extraction_engine = FeatureExtractionEngine(self.config)

                    if self.config.is_forecasting_mode():
                        # TODO: Implement rolling extraction
                        self._show_error("Forecasting mode not yet implemented")
                        return
                    else:
                        # Anomaly detection mode
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

        features_file = features_dir / "extracted.pkl"
        import pickle
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
        """Display extraction results."""
        if self.extracted_features is None:
            return

        # Get statistics
        stats = self.extraction_engine.get_feature_statistics()

        # Build results text
        results = "=" * 60 + "\n"
        results += "Feature Extraction Results\n"
        results += "=" * 60 + "\n\n"

        results += f"Total Features: {stats['total_features']}\n"
        results += f"Samples: {stats['num_samples']}\n"
        results += f"Memory Usage: {stats['memory_usage_mb']:.2f} MB\n\n"

        if 'filtered_features' in stats:
            results += f"Filtered Features: {stats['filtered_features']}\n"
            results += f"Reduction: {stats['reduction_percent']:.1f}%\n\n"

        results += "-" * 60 + "\n"
        results += "Feature Names (first 50):\n"
        results += "-" * 60 + "\n"
        for i, name in enumerate(stats['feature_names'][:50]):
            results += f"{i+1:3d}. {name}\n"

        if len(stats['feature_names']) > 50:
            results += f"... and {len(stats['feature_names']) - 50} more\n"

        # Display
        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", results)

        self.results_info_label.configure(
            text=f"✓ Extracted {stats['total_features']} features",
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

    def refresh(self) -> None:
        """Refresh panel with current project data."""
        self._update_extraction_info()

        # Update target column options if in forecasting mode
        if self.project_manager.has_project():
            project = self.project_manager.current_project
            if hasattr(project.data, 'sensor_columns') and project.data.sensor_columns:
                self.target_column_menu.configure(values=project.data.sensor_columns)

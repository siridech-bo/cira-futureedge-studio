"""
Feature Filtering Panel

UI for filtering extracted features with multiple strategies:
- Basic filtering (constant, low-variance, NaN)
- tsfresh hypothesis testing
- Mutual Information filtering
"""

import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
from typing import Optional, List, Dict
import threading
from loguru import logger
import pickle

from core.project import ProjectManager
from core.feature_filtering import FeatureFilter


class FilteringPanel(ctk.CTkFrame):
    """Panel for feature filtering."""

    def __init__(self, parent, project_manager: ProjectManager, **kwargs):
        """
        Initialize filtering panel.

        Args:
            parent: Parent widget
            project_manager: Project manager instance
        """
        super().__init__(parent, **kwargs)

        self.project_manager = project_manager
        self.filter_engine = FeatureFilter()
        self.current_stats: Optional[Dict] = None

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
            text="🔍 Feature Filtering",
            font=("Segoe UI", 24, "bold")
        )
        title.pack(side="left")

        # Main content with tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

        # Add tabs
        self.tabview.add("Quality Analysis")
        self.tabview.add("Filter Settings")
        self.tabview.add("Results")

        # Setup each tab
        self._setup_analysis_tab()
        self._setup_filter_tab()
        self._setup_results_tab()

    def _setup_analysis_tab(self) -> None:
        """Setup quality analysis tab."""
        tab = self.tabview.tab("Quality Analysis")
        tab.grid_columnconfigure(0, weight=1)

        # Info label
        self.analysis_info_label = ctk.CTkLabel(
            tab,
            text="",
            font=("Segoe UI", 12),
            justify="left"
        )
        self.analysis_info_label.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        # Analyze button
        self.analyze_btn = ctk.CTkButton(
            tab,
            text="📊 Analyze Feature Quality",
            command=self._analyze_features,
            font=("Segoe UI", 14, "bold"),
            height=40
        )
        self.analyze_btn.grid(row=1, column=0, padx=10, pady=10)

        # Results display
        self.analysis_text = ctk.CTkTextbox(
            tab,
            font=("Consolas", 10),
            wrap="none"
        )
        self.analysis_text.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        tab.grid_rowconfigure(2, weight=1)

    def _setup_filter_tab(self) -> None:
        """Setup filter settings tab."""
        tab = self.tabview.tab("Filter Settings")
        tab.grid_columnconfigure(0, weight=1)

        # Filtering method selection
        method_frame = ctk.CTkFrame(tab)
        method_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        ctk.CTkLabel(
            method_frame,
            text="Filtering Method:",
            font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.method_var = ctk.StringVar(value="basic")
        methods = [
            ("Basic (Constant, Low-Variance, NaN)", "basic"),
            ("tsfresh Hypothesis Testing", "tsfresh"),
            ("Mutual Information", "mutual_info")
        ]

        for i, (label, value) in enumerate(methods):
            ctk.CTkRadioButton(
                method_frame,
                text=label,
                variable=self.method_var,
                value=value,
                command=self._update_filter_options,
                font=("Segoe UI", 12)
            ).grid(row=i+1, column=0, padx=30, pady=5, sticky="w")

        # Options frame (dynamic based on method)
        self.options_frame = ctk.CTkFrame(tab)
        self.options_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.options_frame.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        self._setup_basic_options()

        # Filter button
        filter_btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        filter_btn_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)

        self.filter_btn = ctk.CTkButton(
            filter_btn_frame,
            text="🔍 Apply Filter",
            command=self._apply_filter,
            font=("Segoe UI", 16, "bold"),
            height=50,
            fg_color=("green", "darkgreen")
        )
        self.filter_btn.pack(pady=10)

        self.filter_progress_label = ctk.CTkLabel(
            filter_btn_frame,
            text="",
            font=("Segoe UI", 12)
        )
        self.filter_progress_label.pack(pady=5)

    def _setup_basic_options(self) -> None:
        """Setup options for basic filtering."""
        # Clear existing options
        for widget in self.options_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self.options_frame,
            text="Basic Filtering Options",
            font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        # Remove constant features
        self.remove_constant_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            self.options_frame,
            text="Remove constant features (std = 0)",
            variable=self.remove_constant_var,
            font=("Segoe UI", 12)
        ).grid(row=1, column=0, columnspan=2, padx=20, pady=5, sticky="w")

        # Remove NaN features
        self.remove_nan_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            self.options_frame,
            text="Remove features with NaN values",
            variable=self.remove_nan_var,
            font=("Segoe UI", 12)
        ).grid(row=2, column=0, columnspan=2, padx=20, pady=5, sticky="w")

        # Variance threshold
        ctk.CTkLabel(
            self.options_frame,
            text="Variance Threshold:",
            font=("Segoe UI", 12)
        ).grid(row=3, column=0, padx=20, pady=10, sticky="w")

        self.variance_threshold_var = ctk.StringVar(value="0.01")
        ctk.CTkEntry(
            self.options_frame,
            textvariable=self.variance_threshold_var,
            font=("Segoe UI", 12),
            width=150
        ).grid(row=3, column=1, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(
            self.options_frame,
            text="Features with variance below this threshold will be removed",
            font=("Segoe UI", 10),
            text_color="gray"
        ).grid(row=4, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="w")

    def _setup_tsfresh_options(self) -> None:
        """Setup options for tsfresh filtering."""
        # Clear existing options
        for widget in self.options_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self.options_frame,
            text="tsfresh Hypothesis Testing Options",
            font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        # FDR level
        ctk.CTkLabel(
            self.options_frame,
            text="FDR Level:",
            font=("Segoe UI", 12)
        ).grid(row=1, column=0, padx=20, pady=10, sticky="w")

        self.fdr_level_var = ctk.StringVar(value="0.05")
        ctk.CTkEntry(
            self.options_frame,
            textvariable=self.fdr_level_var,
            font=("Segoe UI", 12),
            width=150
        ).grid(row=1, column=1, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(
            self.options_frame,
            text="False Discovery Rate threshold (typically 0.01-0.05)",
            font=("Segoe UI", 10),
            text_color="gray"
        ).grid(row=2, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="w")

        # Hypotheses independence
        self.hypotheses_independent_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self.options_frame,
            text="Treat hypotheses as independent (less conservative)",
            variable=self.hypotheses_independent_var,
            font=("Segoe UI", 12)
        ).grid(row=3, column=0, columnspan=2, padx=20, pady=5, sticky="w")

        # Info
        info_text = (
            "tsfresh uses statistical hypothesis testing to identify relevant features.\n"
            "Lower FDR = more conservative filtering (fewer features kept).\n"
            "This method is recommended by tsfresh documentation for feature selection."
        )
        ctk.CTkLabel(
            self.options_frame,
            text=info_text,
            font=("Segoe UI", 10),
            text_color="lightblue",
            justify="left"
        ).grid(row=4, column=0, columnspan=2, padx=20, pady=10, sticky="w")

    def _setup_mi_options(self) -> None:
        """Setup options for mutual information filtering."""
        # Clear existing options
        for widget in self.options_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self.options_frame,
            text="Mutual Information Filtering Options",
            font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        # Selection mode
        ctk.CTkLabel(
            self.options_frame,
            text="Selection Mode:",
            font=("Segoe UI", 12)
        ).grid(row=1, column=0, padx=20, pady=10, sticky="w")

        self.mi_mode_var = ctk.StringVar(value="threshold")
        mode_menu = ctk.CTkOptionMenu(
            self.options_frame,
            values=["Threshold", "Top K Features"],
            variable=self.mi_mode_var,
            command=self._update_mi_mode,
            font=("Segoe UI", 12)
        )
        mode_menu.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # Threshold input
        self.mi_threshold_label = ctk.CTkLabel(
            self.options_frame,
            text="MI Threshold:",
            font=("Segoe UI", 12)
        )
        self.mi_threshold_label.grid(row=2, column=0, padx=20, pady=10, sticky="w")

        self.mi_threshold_var = ctk.StringVar(value="0.01")
        self.mi_threshold_entry = ctk.CTkEntry(
            self.options_frame,
            textvariable=self.mi_threshold_var,
            font=("Segoe UI", 12),
            width=150
        )
        self.mi_threshold_entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        # Top K input (hidden by default)
        self.mi_topk_label = ctk.CTkLabel(
            self.options_frame,
            text="Top K Features:",
            font=("Segoe UI", 12)
        )
        self.mi_topk_var = ctk.StringVar(value="100")
        self.mi_topk_entry = ctk.CTkEntry(
            self.options_frame,
            textvariable=self.mi_topk_var,
            font=("Segoe UI", 12),
            width=150
        )

        # Info
        self.mi_info_label = ctk.CTkLabel(
            self.options_frame,
            text="Features with MI score above this threshold will be kept",
            font=("Segoe UI", 10),
            text_color="gray"
        )
        self.mi_info_label.grid(row=3, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="w")

    def _update_mi_mode(self, mode: str) -> None:
        """Update MI filtering mode UI."""
        if mode == "Threshold":
            self.mi_threshold_label.grid(row=2, column=0, padx=20, pady=10, sticky="w")
            self.mi_threshold_entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")
            self.mi_topk_label.grid_forget()
            self.mi_topk_entry.grid_forget()
            self.mi_info_label.configure(text="Features with MI score above this threshold will be kept")
        else:  # Top K
            self.mi_topk_label.grid(row=2, column=0, padx=20, pady=10, sticky="w")
            self.mi_topk_entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")
            self.mi_threshold_label.grid_forget()
            self.mi_threshold_entry.grid_forget()
            self.mi_info_label.configure(text="Keep top K features with highest MI scores")

    def _update_filter_options(self) -> None:
        """Update filter options based on selected method."""
        method = self.method_var.get()

        if method == "basic":
            self._setup_basic_options()
        elif method == "tsfresh":
            self._setup_tsfresh_options()
        elif method == "mutual_info":
            self._setup_mi_options()

    def _setup_results_tab(self) -> None:
        """Setup results tab."""
        tab = self.tabview.tab("Results")
        tab.grid_columnconfigure(0, weight=1)

        # Info label
        self.results_info_label = ctk.CTkLabel(
            tab,
            text="",
            font=("Segoe UI", 12)
        )
        self.results_info_label.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        # Results display
        self.results_text = ctk.CTkTextbox(
            tab,
            font=("Consolas", 10),
            wrap="word"
        )
        self.results_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        tab.grid_rowconfigure(1, weight=1)

        # Save button
        self.save_btn = ctk.CTkButton(
            tab,
            text="💾 Save Filtered Features",
            command=self._save_filtered_features,
            font=("Segoe UI", 14, "bold"),
            height=40,
            state="disabled"
        )
        self.save_btn.grid(row=2, column=0, padx=10, pady=10)

    def _analyze_features(self) -> None:
        """Analyze feature quality."""
        if not self.project_manager.has_project():
            messagebox.showwarning("No Project", "Please create or open a project first.")
            return

        project = self.project_manager.current_project

        if not project.features.extracted:
            messagebox.showwarning("No Features", "Please extract features first.")
            return

        self.analyze_btn.configure(state="disabled")
        self.analysis_info_label.configure(text="Analyzing features...", text_color="blue")

        def analysis_thread():
            try:
                # Load features
                features_path = Path(project.features.extracted_features)
                with open(features_path, 'rb') as f:
                    features_df = pickle.load(f)

                # Load labels
                if project.data.train_test_split_type == "manual":
                    if project.data.train_windows_file:
                        with open(project.data.train_windows_file, 'rb') as f:
                            train_windows = pickle.load(f)
                        windows = train_windows
                        if project.data.test_windows_file:
                            with open(project.data.test_windows_file, 'rb') as f:
                                test_windows = pickle.load(f)
                            windows = train_windows + test_windows
                    else:
                        windows = []
                else:
                    windows = project.load_windows()

                labels = [w.class_label if hasattr(w, 'class_label') and w.class_label else "unknown" for w in windows]

                # Analyze
                logger.info("Analyzing feature quality...")
                stats = self.filter_engine.analyze_feature_quality(features_df, labels)
                self.current_stats = stats

                self.after(0, lambda: self._display_analysis(stats))

            except Exception as e:
                logger.error(f"Analysis failed: {e}")
                self.after(0, lambda: self._analysis_error(str(e)))

        thread = threading.Thread(target=analysis_thread, daemon=True)
        thread.start()

    def _display_analysis(self, stats: Dict) -> None:
        """Display analysis results."""
        self.analysis_info_label.configure(
            text="✓ Analysis complete",
            text_color="green"
        )
        self.analyze_btn.configure(state="normal")

        # Build report
        report = "Feature Quality Analysis\n"
        report += "=" * 80 + "\n\n"
        report += f"Total Features: {stats['total_features']}\n"
        report += f"Total Samples: {stats['total_samples']}\n\n"

        report += "Issues Found:\n"
        report += "-" * 80 + "\n"
        report += f"Constant features (no variation): {stats['constant_features']}\n"
        report += f"Features with NaN values: {stats['nan_features']} ({stats['nan_percentage']:.2f}%)\n"
        report += f"Low variance features (< 0.01): {stats['low_variance_features']}\n\n"

        report += "Variance Statistics:\n"
        report += "-" * 80 + "\n"
        var_stats = stats['variance_stats']
        report += f"Min variance: {var_stats['min']:.6f}\n"
        report += f"Max variance: {var_stats['max']:.6e}\n"
        report += f"Mean variance: {var_stats['mean']:.6e}\n"
        report += f"Median variance: {var_stats['median']:.6e}\n\n"

        if stats.get('mi_stats'):
            mi = stats['mi_stats']
            report += "Mutual Information Statistics:\n"
            report += "-" * 80 + "\n"
            report += f"Sampled features: {mi['sampled_features']}\n"
            report += f"Min MI score: {mi['min']:.6f}\n"
            report += f"Max MI score: {mi['max']:.6f}\n"
            report += f"Mean MI score: {mi['mean']:.6f}\n"
            report += f"Median MI score: {mi['median']:.6f}\n\n"
            report += f"Features with MI > 0.01: {mi['features_with_mi_gt_0.01']}\n"
            report += f"Features with MI > 0.05: {mi['features_with_mi_gt_0.05']}\n"
            report += f"Features with MI > 0.10: {mi['features_with_mi_gt_0.10']}\n\n"

        report += "\nRecommendations:\n"
        report += "-" * 80 + "\n"
        if stats['constant_features'] > 0:
            report += f"• Remove {stats['constant_features']} constant features (no discriminative power)\n"
        if stats['nan_features'] > 0:
            report += f"• Remove {stats['nan_features']} features with NaN values\n"
        if stats['low_variance_features'] > 0:
            report += f"• Consider removing {stats['low_variance_features']} low-variance features\n"

        if stats.get('mi_stats'):
            good_features = stats['mi_stats']['features_with_mi_gt_0.01']
            if good_features < stats['total_features'] * 0.1:
                report += f"⚠ Warning: Only {good_features} features have MI > 0.01\n"
                report += "  This suggests many features may not be useful for classification.\n"
                report += "  Consider using tsfresh or MI filtering to remove irrelevant features.\n"

        self.analysis_text.delete("1.0", "end")
        self.analysis_text.insert("1.0", report)

    def _analysis_error(self, error: str) -> None:
        """Handle analysis error."""
        self.analysis_info_label.configure(
            text=f"✗ Error: {error}",
            text_color="red"
        )
        self.analyze_btn.configure(state="normal")
        messagebox.showerror("Analysis Error", f"Failed to analyze features:\n{error}")

    def _apply_filter(self) -> None:
        """Apply selected filter."""
        if not self.project_manager.has_project():
            messagebox.showwarning("No Project", "Please create or open a project first.")
            return

        project = self.project_manager.current_project

        if not project.features.extracted:
            messagebox.showwarning("No Features", "Please extract features first.")
            return

        method = self.method_var.get()
        self.filter_btn.configure(state="disabled")
        self.filter_progress_label.configure(text=f"Applying {method} filter...", text_color="blue")

        def filter_thread():
            try:
                # Load features
                features_path = Path(project.features.extracted_features)
                with open(features_path, 'rb') as f:
                    features_df = pickle.load(f)

                # Load labels (needed for tsfresh and MI)
                if method in ["tsfresh", "mutual_info"]:
                    if project.data.train_test_split_type == "manual":
                        if project.data.train_windows_file:
                            with open(project.data.train_windows_file, 'rb') as f:
                                train_windows = pickle.load(f)
                            windows = train_windows
                            if project.data.test_windows_file:
                                with open(project.data.test_windows_file, 'rb') as f:
                                    test_windows = pickle.load(f)
                                windows = train_windows + test_windows
                        else:
                            windows = []
                    else:
                        windows = project.load_windows()

                    labels = [w.class_label if hasattr(w, 'class_label') and w.class_label else "unknown" for w in windows]
                else:
                    labels = None

                # Apply filter based on method
                if method == "basic":
                    variance_threshold = float(self.variance_threshold_var.get())
                    result = self.filter_engine.filter_basic(
                        features_df,
                        variance_threshold=variance_threshold,
                        remove_constant=self.remove_constant_var.get(),
                        remove_nan=self.remove_nan_var.get()
                    )
                elif method == "tsfresh":
                    fdr_level = float(self.fdr_level_var.get())
                    result = self.filter_engine.filter_tsfresh(
                        features_df,
                        labels,
                        fdr_level=fdr_level,
                        hypotheses_independent=self.hypotheses_independent_var.get()
                    )
                elif method == "mutual_info":
                    if self.mi_mode_var.get() == "Threshold":
                        threshold = float(self.mi_threshold_var.get())
                        result = self.filter_engine.filter_mutual_information(
                            features_df,
                            labels,
                            threshold=threshold
                        )
                    else:  # Top K
                        top_k = int(self.mi_topk_var.get())
                        result = self.filter_engine.filter_mutual_information(
                            features_df,
                            labels,
                            top_k=top_k
                        )

                # Store result
                self.filtering_result = result

                self.after(0, lambda: self._filter_complete(result))

            except Exception as e:
                logger.error(f"Filtering failed: {e}")
                self.after(0, lambda: self._filter_error(str(e)))

        thread = threading.Thread(target=filter_thread, daemon=True)
        thread.start()

    def _filter_complete(self, result) -> None:
        """Handle successful filtering."""
        self.filter_progress_label.configure(
            text=f"✓ Filtered: {result.filtering_stats['original_features']} → {result.filtering_stats['filtered_features']} features",
            text_color="green"
        )
        self.filter_btn.configure(state="normal")

        # Display results
        self.results_info_label.configure(
            text=f"✓ {result.filtering_stats['filtered_features']} features remaining"
        )

        report = "Feature Filtering Results\n"
        report += "=" * 80 + "\n\n"
        report += f"Method: {result.method}\n"
        report += f"Original features: {result.filtering_stats['original_features']}\n"
        report += f"Filtered features: {result.filtering_stats['filtered_features']}\n"
        report += f"Removed features: {result.filtering_stats['removed_features']}\n"
        report += f"Retention rate: {result.filtering_stats['filtered_features'] / result.filtering_stats['original_features'] * 100:.1f}%\n\n"

        # Method-specific stats
        if result.method == "basic":
            report += "Removal Breakdown:\n"
            report += "-" * 80 + "\n"
            if 'constant_features' in result.filtering_stats:
                report += f"Constant features: {result.filtering_stats['constant_features']}\n"
            if 'low_variance_features' in result.filtering_stats:
                report += f"Low variance features: {result.filtering_stats['low_variance_features']}\n"
            if 'nan_features' in result.filtering_stats:
                report += f"NaN features: {result.filtering_stats['nan_features']}\n"

        elif result.method == "mutual_information":
            report += "MI Score Statistics:\n"
            report += "-" * 80 + "\n"
            report += f"Min MI score: {result.filtering_stats['min_mi_score']:.4f}\n"
            report += f"Max MI score: {result.filtering_stats['max_mi_score']:.4f}\n"
            report += f"Mean MI score: {result.filtering_stats['mean_mi_score']:.4f}\n"

        report += f"\n\nNext Steps:\n"
        report += "-" * 80 + "\n"
        report += "Click 'Save Filtered Features' to save these features and proceed to LLM Selection.\n"

        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", report)

        self.save_btn.configure(state="normal")
        self.tabview.set("Results")

    def _filter_error(self, error: str) -> None:
        """Handle filter error."""
        self.filter_progress_label.configure(
            text=f"✗ Error: {error}",
            text_color="red"
        )
        self.filter_btn.configure(state="normal")
        messagebox.showerror("Filtering Error", f"Failed to filter features:\n{error}")

    def _save_filtered_features(self) -> None:
        """Save filtered features to project."""
        if not hasattr(self, 'filtering_result'):
            messagebox.showwarning("No Results", "No filtering results to save.")
            return

        project = self.project_manager.current_project
        result = self.filtering_result

        # Save filtered features
        output_dir = Path(project.project_path).parent / "output" / project.name
        output_dir.mkdir(parents=True, exist_ok=True)

        filtered_path = output_dir / "filtered_features.pkl"
        with open(filtered_path, 'wb') as f:
            pickle.dump(result.filtered_features, f)

        # Update project
        project.features.filtered_features = str(filtered_path)
        project.features.num_features_selected = len(result.selected_feature_names)
        self.project_manager.save_project()

        messagebox.showinfo(
            "Saved",
            f"Filtered features saved!\n\n"
            f"Original: {result.filtering_stats['original_features']} features\n"
            f"Filtered: {result.filtering_stats['filtered_features']} features\n\n"
            f"Proceed to LLM Selection to select final features."
        )
        logger.info(f"Filtered features saved to {filtered_path}")

    def refresh(self) -> None:
        """Refresh panel with current project data."""
        if not self.project_manager.has_project():
            self.analysis_info_label.configure(
                text="⚠️ No project loaded. Create or open a project first."
            )
            return

        project = self.project_manager.current_project

        if not project.features.extracted:
            self.analysis_info_label.configure(
                text="⚠️ Extract features first in Feature Extraction stage"
            )
            return

        self.analysis_info_label.configure(
            text=f"✓ Ready to filter {project.features.num_features_extracted} extracted features"
        )

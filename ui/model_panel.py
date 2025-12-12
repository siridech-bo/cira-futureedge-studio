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
        self.training_results = None
        self.features_df = None
        self.selected_features = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create notebook for tabs
        self.notebook = ctk.CTkTabview(self)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Add tabs
        self.notebook.add("Algorithm")
        self.notebook.add("Training")
        self.notebook.add("Evaluation")
        self.notebook.add("Export")

        self._create_algorithm_tab()
        self._create_training_tab()
        self._create_evaluation_tab()
        self._create_export_tab()

    def _create_algorithm_tab(self):
        """Create algorithm selection tab."""
        tab = self.notebook.tab("Algorithm")
        tab.grid_columnconfigure(0, weight=1)

        # Get task mode from project
        task_mode = "anomaly_detection"
        if self.project_manager.current_project:
            task_mode = self.project_manager.current_project.data.task_type

        # Title (dynamic based on task mode)
        title_text = "Select Classification Algorithm" if task_mode == "classification" else "Select Anomaly Detection Algorithm"
        self.title_label = ctk.CTkLabel(
            tab,
            text=title_text,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Algorithm info frame
        info_frame = ctk.CTkFrame(tab)
        info_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
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

        # Algorithm selection
        selection_frame = ctk.CTkFrame(tab)
        selection_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        selection_frame.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            selection_frame,
            text="Available Algorithms:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # Scrollable frame for algorithms
        scroll_frame = ctk.CTkScrollableFrame(selection_frame, height=300)
        scroll_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        scroll_frame.grid_columnconfigure(0, weight=1)
        selection_frame.grid_rowconfigure(1, weight=1)

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
                text=f"{algo_info['description']} • {algo_info['recommended_for']}",
                text_color="gray",
                wraplength=400,
                justify="left"
            )
            desc.grid(row=0, column=1, padx=10, sticky="w")

            row += 1

        # Algorithm details
        details_frame = ctk.CTkFrame(tab)
        details_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        details_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            details_frame,
            text="Algorithm Details:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.algo_details_text = ctk.CTkTextbox(details_frame, height=100)
        self.algo_details_text.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self._on_algorithm_change()

    def _create_training_tab(self):
        """Create training configuration tab."""
        tab = self.notebook.tab("Training")
        tab.grid_columnconfigure(0, weight=1)

        # Title
        title = ctk.CTkLabel(
            tab,
            text="Training Configuration",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Configuration frame
        config_frame = ctk.CTkFrame(tab)
        config_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        config_frame.grid_columnconfigure(1, weight=1)

        # Test size
        ctk.CTkLabel(config_frame, text="Test Size:").grid(
            row=0, column=0, padx=10, pady=10, sticky="w"
        )
        self.test_size_var = ctk.StringVar(value="0.3")
        test_size_entry = ctk.CTkEntry(config_frame, textvariable=self.test_size_var, width=100)
        test_size_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(config_frame, text="(0.1-0.5)", text_color="gray").grid(
            row=0, column=2, padx=5, pady=10, sticky="w"
        )

        # Contamination
        ctk.CTkLabel(config_frame, text="Contamination:").grid(
            row=1, column=0, padx=10, pady=10, sticky="w"
        )
        self.contamination_var = ctk.StringVar(value="0.1")
        contam_entry = ctk.CTkEntry(config_frame, textvariable=self.contamination_var, width=100)
        contam_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(
            config_frame,
            text="Expected anomaly rate (0.01-0.5)",
            text_color="gray"
        ).grid(row=1, column=2, padx=5, pady=10, sticky="w")

        # Normalize
        self.normalize_var = ctk.BooleanVar(value=True)
        normalize_check = ctk.CTkCheckBox(
            config_frame,
            text="Normalize features (recommended)",
            variable=self.normalize_var
        )
        normalize_check.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="w")

        # Random state
        ctk.CTkLabel(config_frame, text="Random Seed:").grid(
            row=3, column=0, padx=10, pady=10, sticky="w"
        )
        self.random_state_var = ctk.StringVar(value="42")
        random_entry = ctk.CTkEntry(config_frame, textvariable=self.random_state_var, width=100)
        random_entry.grid(row=3, column=1, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(
            config_frame,
            text="For reproducibility",
            text_color="gray"
        ).grid(row=3, column=2, padx=5, pady=10, sticky="w")

        # Training controls
        controls_frame = ctk.CTkFrame(tab)
        controls_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.train_btn = ctk.CTkButton(
            controls_frame,
            text="Start Training",
            command=self._start_training,
            fg_color="green",
            hover_color="darkgreen",
            height=40
        )
        self.train_btn.pack(side="left", padx=10, pady=10)

        self.progress_label = ctk.CTkLabel(
            controls_frame,
            text="",
            text_color="blue"
        )
        self.progress_label.pack(side="left", padx=10, pady=10)

        # Training status
        status_frame = ctk.CTkFrame(tab)
        status_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        status_frame.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(
            status_frame,
            text="Training Log:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.training_log = ctk.CTkTextbox(status_frame, height=200)
        self.training_log.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        status_frame.grid_rowconfigure(1, weight=1)

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

        # Update details
        details = f"Algorithm: {algo_info['name']}\n\n"
        details += f"Description: {algo_info['description']}\n\n"
        details += f"Recommended for: {algo_info['recommended_for']}\n\n"
        details += f"Default parameters: {algo_info['params']}"

        self.algo_details_text.delete("1.0", "end")
        self.algo_details_text.insert("1.0", details)

    def _start_training(self):
        """Start model training in background thread."""
        project = self.project_manager.current_project
        if not project:
            messagebox.showerror("Error", "No project loaded")
            return

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
        project.save()

        messagebox.showinfo("Training Complete", message_text)

    def _training_failed(self, error: str):
        """Handle training failure."""
        self.train_btn.configure(state="normal")
        self.progress_label.configure(text="✗ Training failed", text_color="red")
        self._log_training(f"\nERROR: {error}")

        messagebox.showerror("Training Failed", f"Training failed:\n{error}")

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

            labels = [
                ("Algorithm:", results.algorithm),
                ("Training Samples:", str(results.train_samples)),
                ("Test Samples:", str(results.test_samples)),
                ("Features:", str(results.n_features)),
                ("Classes:", str(results.n_classes)),
            ]

            for i, (label, value) in enumerate(labels, start=1):
                ctk.CTkLabel(info_frame, text=label).grid(
                    row=i, column=0, padx=10, pady=5, sticky="w"
                )
                ctk.CTkLabel(info_frame, text=value, text_color="blue").grid(
                    row=i, column=1, padx=10, pady=5, sticky="w"
                )

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

                cm_widget = ConfusionMatrixWidget(cm_frame, width=500, height=400)
                cm_widget.grid(row=1, column=0, padx=10, pady=10)

                cm_widget.plot_confusion_matrix(
                    confusion_matrix=np.array(results.confusion_matrix),
                    class_names=results.class_names
                )

            # Feature Importance
            if results.feature_importances:
                fi_frame = ctk.CTkFrame(self.results_container)
                fi_frame.grid(row=row, column=0, padx=10, pady=10, sticky="ew")
                fi_frame.grid_columnconfigure(0, weight=1)
                row += 1

                ctk.CTkLabel(
                    fi_frame,
                    text="Feature Importance",
                    font=ctk.CTkFont(size=14, weight="bold")
                ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

                fi_widget = FeatureImportanceChart(fi_frame, width=600, height=400)
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
            # Find all trained models
            model_dir = project.get_project_dir() / "models"
            if model_dir.exists():
                models = list(model_dir.glob("*_model.pkl"))
                if models:
                    self.export_status_label.configure(
                        text=f"✓ {len(models)} model(s) trained",
                        text_color="green"
                    )
                    # Show all models in the label
                    model_names = [m.stem.replace('_model', '') for m in models]
                    self.model_path_label.configure(
                        text=f"Algorithms: {', '.join(model_names)}"
                    )
                    self.open_dir_btn.configure(state="normal")
                    self.complete_btn.configure(state="normal")

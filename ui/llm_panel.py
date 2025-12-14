"""
LLM Feature Selection Panel

UI for LLM-assisted intelligent feature selection with:
- Model download/management
- Feature selection with constraints
- Feature explanation
- Fallback to statistical methods
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from pathlib import Path
from typing import Optional, List, Dict
import threading
from loguru import logger

from core.project import ProjectManager
from core.llm_manager import LLMManager, LLMConfig, LLAMA_CPP_AVAILABLE
from core.feature_names import FeatureNameDecoder


class LLMPanel(ctk.CTkFrame):
    """Panel for LLM-assisted feature selection."""

    def __init__(self, parent, project_manager: ProjectManager, **kwargs):
        """
        Initialize LLM panel.

        Args:
            parent: Parent widget
            project_manager: Project manager instance
        """
        super().__init__(parent, **kwargs)

        self.project_manager = project_manager
        self.llm_manager: Optional[LLMManager] = None
        self.selected_features: List[str] = []
        self.feature_stats_cache: Optional[Dict[str, Dict]] = None  # Cache for displaying in results
        self.feature_importance_cache: Optional[Dict[str, float]] = None

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
            text="🤖 LLM Feature Selection",
            font=("Segoe UI", 24, "bold")
        )
        title.pack(side="left")

        # Main content with tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

        # Add tabs
        self.tabview.add("Model Setup")
        self.tabview.add("Feature Selection")
        self.tabview.add("Results")
        self.tabview.add("LLM Analysis")

        # Setup each tab
        self._setup_model_tab()
        self._setup_selection_tab()
        self._setup_results_tab()
        self._setup_analysis_tab()

    def _setup_model_tab(self) -> None:
        """Setup model management tab."""
        tab = self.tabview.tab("Model Setup")
        tab.grid_columnconfigure(0, weight=1)

        # LLM availability check
        if not LLAMA_CPP_AVAILABLE:
            warning_frame = ctk.CTkFrame(tab, fg_color=("gray80", "gray20"))
            warning_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

            ctk.CTkLabel(
                warning_frame,
                text="⚠️ llama-cpp-python not installed\n\n"
                     "Install with: pip install llama-cpp-python\n"
                     "Fallback statistical selection will be used.",
                font=("Segoe UI", 12),
                justify="center"
            ).pack(padx=20, pady=20)

        # Model path
        model_frame = ctk.CTkFrame(tab)
        model_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        model_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            model_frame,
            text="Model Path:",
            font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.model_path_entry = ctk.CTkEntry(
            model_frame,
            placeholder_text="Path to Llama-3.2-3B-Instruct-Q4_K_M.gguf"
        )
        self.model_path_entry.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

        # Auto-fill from config
        if self.project_manager.has_project():
            project = self.project_manager.current_project
            model_path = Path.cwd() / "models" / project.llm.model_name
            if model_path.exists():
                self.model_path_entry.insert(0, str(model_path))

        browse_btn = ctk.CTkButton(
            model_frame,
            text="Browse...",
            command=self._browse_model,
            width=100
        )
        browse_btn.grid(row=0, column=2, padx=10, pady=10)

        # Model info
        self.model_info_label = ctk.CTkLabel(
            model_frame,
            text="",
            font=("Segoe UI", 10),
            text_color="gray"
        )
        self.model_info_label.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="w")

        # Load model button
        load_frame = ctk.CTkFrame(tab, fg_color="transparent")
        load_frame.grid(row=2, column=0, pady=20)

        self.load_btn = ctk.CTkButton(
            load_frame,
            text="🚀 Load Model",
            command=self._load_model,
            width=200,
            height=50,
            font=("Segoe UI", 16, "bold"),
            state="disabled" if not LLAMA_CPP_AVAILABLE else "normal"
        )
        self.load_btn.pack()

        # Status
        self.load_status_label = ctk.CTkLabel(
            tab,
            text="",
            font=("Segoe UI", 11)
        )
        self.load_status_label.grid(row=3, column=0, pady=5)

        # Download instructions
        instructions_frame = ctk.CTkFrame(tab)
        instructions_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=10)

        ctk.CTkLabel(
            instructions_frame,
            text="📥 To download Llama-3.2-3B model (~2.5GB):\n\n"
                 "1. Visit: https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF\n"
                 "2. Download: Llama-3.2-3B-Instruct-Q4_K_M.gguf\n"
                 "3. Place in: models/ folder\n"
                 "4. Click 'Load Model' above",
            font=("Segoe UI", 10),
            justify="left",
            text_color="gray"
        ).pack(padx=20, pady=20)

    def _setup_selection_tab(self) -> None:
        """Setup feature selection tab."""
        tab = self.tabview.tab("Feature Selection")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=2)  # Prompt column wider
        tab.grid_rowconfigure(1, weight=1)  # Make main content expandable

        # Info
        self.selection_info_label = ctk.CTkLabel(
            tab,
            text="Extract features first in Feature Extraction stage",
            font=("Segoe UI", 12),
            text_color="gray"
        )
        self.selection_info_label.grid(row=0, column=0, columnspan=2, padx=20, pady=10)

        # LEFT COLUMN: Selection parameters
        params_frame = ctk.CTkFrame(tab)
        params_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=10)
        params_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            params_frame,
            text="Selection Parameters:",
            font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=10)

        # Number of features
        ctk.CTkLabel(
            params_frame,
            text="Features to Select:",
            font=("Segoe UI", 12)
        ).grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.feature_count_var = ctk.StringVar(value="5")
        count_entry = ctk.CTkEntry(
            params_frame,
            textvariable=self.feature_count_var,
            width=150
        )
        count_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # Platform constraints
        ctk.CTkLabel(
            params_frame,
            text="Target Platform:",
            font=("Segoe UI", 12)
        ).grid(row=2, column=0, padx=10, pady=5, sticky="w")

        self.platform_var = ctk.StringVar(value="Cortex-M4")
        platform_menu = ctk.CTkOptionMenu(
            params_frame,
            variable=self.platform_var,
            values=["Cortex-M4", "Cortex-M7", "ESP32", "x86"]
        )
        platform_menu.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        # Memory constraint
        ctk.CTkLabel(
            params_frame,
            text="Available Memory (KB):",
            font=("Segoe UI", 12)
        ).grid(row=3, column=0, padx=10, pady=5, sticky="w")

        self.memory_var = ctk.StringVar(value="256")
        memory_entry = ctk.CTkEntry(
            params_frame,
            textvariable=self.memory_var,
            width=150
        )
        memory_entry.grid(row=3, column=1, padx=10, pady=(5, 10), sticky="w")

        # Select button (in left column, below parameters)
        select_frame = ctk.CTkFrame(params_frame, fg_color="transparent")
        select_frame.grid(row=4, column=0, columnspan=2, pady=20)

        self.select_btn = ctk.CTkButton(
            select_frame,
            text="🎯 Select Features",
            command=self._select_features,
            width=200,
            height=50,
            font=("Segoe UI", 16, "bold"),
            state="disabled"
        )
        self.select_btn.pack()

        # Progress (in left column)
        self.selection_progress_label = ctk.CTkLabel(
            params_frame,
            text="",
            font=("Segoe UI", 11)
        )
        self.selection_progress_label.grid(row=5, column=0, columnspan=2, pady=5)

        # RIGHT COLUMN: Prompt Editor
        prompt_frame = ctk.CTkFrame(tab)
        prompt_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=10)
        prompt_frame.grid_columnconfigure(0, weight=1)
        prompt_frame.grid_rowconfigure(1, weight=1)

        # Prompt header with buttons
        prompt_header = ctk.CTkFrame(prompt_frame, fg_color="transparent")
        prompt_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        prompt_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            prompt_header,
            text="📝 Prompt Template",
            font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, sticky="w")

        prompt_btn_frame = ctk.CTkFrame(prompt_header, fg_color="transparent")
        prompt_btn_frame.grid(row=0, column=1, sticky="e")

        self.reset_prompt_btn = ctk.CTkButton(
            prompt_btn_frame,
            text="↺ Reset",
            command=self._reset_prompt,
            width=80,
            height=28,
            font=("Segoe UI", 11)
        )
        self.reset_prompt_btn.pack(side="left", padx=5)

        self.save_prompt_btn = ctk.CTkButton(
            prompt_btn_frame,
            text="💾 Save",
            command=self._save_prompt,
            width=80,
            height=28,
            font=("Segoe UI", 11),
            fg_color="green",
            hover_color="darkgreen"
        )
        self.save_prompt_btn.pack(side="left", padx=5)

        # Prompt textbox
        self.prompt_textbox = ctk.CTkTextbox(
            prompt_frame,
            font=("Consolas", 9),
            wrap="word"
        )
        self.prompt_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        # Load default prompt
        self._load_default_prompt()

    def _setup_results_tab(self) -> None:
        """Setup results tab."""
        tab = self.tabview.tab("Results")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Results info
        self.results_info_label = ctk.CTkLabel(
            tab,
            text="No features selected yet",
            font=("Segoe UI", 12),
            text_color="gray"
        )
        self.results_info_label.grid(row=0, column=0, padx=20, pady=20)

        # Results display
        results_frame = ctk.CTkScrollableFrame(tab)
        results_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        results_frame.grid_columnconfigure(0, weight=1)

        self.results_text = ctk.CTkTextbox(
            results_frame,
            font=("Courier New", 12),  # Increased from 10 to 12
            wrap="word"
        )
        self.results_text.pack(fill="both", expand=True)

        # Export button
        export_frame = ctk.CTkFrame(tab, fg_color="transparent")
        export_frame.grid(row=2, column=0, pady=10)

        self.export_btn = ctk.CTkButton(
            export_frame,
            text="💾 Save & Continue",
            command=self._save_selection,
            state="disabled"
        )
        self.export_btn.pack()

    def _setup_analysis_tab(self) -> None:
        """Setup LLM Analysis tab for AI-powered recommendations."""
        tab = self.tabview.tab("LLM Analysis")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Info label
        self.analysis_info_label = ctk.CTkLabel(
            tab,
            text="",
            font=("Segoe UI", 12),
            text_color="gray"
        )
        self.analysis_info_label.grid(row=0, column=0, padx=20, pady=10)

        # Analysis display
        analysis_frame = ctk.CTkScrollableFrame(tab)
        analysis_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        analysis_frame.grid_columnconfigure(0, weight=1)

        self.analysis_text = ctk.CTkTextbox(
            analysis_frame,
            font=("Segoe UI", 12),
            wrap="word"
        )
        self.analysis_text.pack(fill="both", expand=True)

        # Analyze button
        button_frame = ctk.CTkFrame(tab, fg_color="transparent")
        button_frame.grid(row=2, column=0, pady=10)

        self.analyze_btn = ctk.CTkButton(
            button_frame,
            text="🤖 Generate LLM Analysis",
            command=self._generate_llm_analysis,
            font=("Segoe UI", 14, "bold"),
            height=40,
            state="disabled"
        )
        self.analyze_btn.pack()

    def _browse_model(self) -> None:
        """Browse for model file."""
        filename = filedialog.askopenfilename(
            title="Select LLM Model",
            filetypes=[
                ("GGUF models", "*.gguf"),
                ("All files", "*.*")
            ]
        )

        if filename:
            self.model_path_entry.delete(0, "end")
            self.model_path_entry.insert(0, filename)

            # Show file info
            path = Path(filename)
            size_mb = path.stat().st_size / 1024 / 1024
            self.model_info_label.configure(
                text=f"✓ Model file: {path.name} ({size_mb:.1f} MB)"
            )

    def _load_model(self) -> None:
        """Load LLM model."""
        model_path_str = self.model_path_entry.get().strip()

        if not model_path_str:
            messagebox.showwarning("No Model", "Please select a model file first.")
            return

        model_path = Path(model_path_str)

        if not model_path.exists():
            messagebox.showerror("File Not Found", f"Model file not found:\n{model_path}")
            return

        self.load_btn.configure(state="disabled")
        self.load_status_label.configure(text="Loading model...")

        def load_thread():
            try:
                config = LLMConfig(
                    model_path=model_path,
                    n_ctx=2048,
                    n_threads=4,
                    temperature=0.3
                )

                self.llm_manager = LLMManager(config)
                success = self.llm_manager.load_model()

                if success:
                    self.after(0, self._model_loaded)
                else:
                    self.after(0, lambda: self._model_load_error("Failed to load model"))

            except Exception as e:
                self.after(0, lambda: self._model_load_error(str(e)))

        thread = threading.Thread(target=load_thread, daemon=True)
        thread.start()

    def _model_loaded(self) -> None:
        """Handle successful model load."""
        self.load_status_label.configure(
            text="✓ Model loaded successfully",
            text_color="green"
        )
        self.load_btn.configure(state="normal")
        self._update_selection_info()
        messagebox.showinfo("Success", "LLM model loaded successfully!")
        logger.info("LLM model loaded by user")

    def _model_load_error(self, error: str) -> None:
        """Handle model load error."""
        self.load_status_label.configure(
            text=f"✗ Error: {error}",
            text_color="red"
        )
        self.load_btn.configure(state="normal")
        messagebox.showerror("Load Error", f"Failed to load model:\n{error}")

    def _get_default_prompt_template(self) -> str:
        """Get the default prompt template."""
        return """<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are an expert in embedded systems and machine learning feature engineering. Your task is to select the most effective features for anomaly detection on resource-constrained embedded devices.

<|eot_id|><|start_header_id|>user<|end_header_id|>

I need to select the top {target_count} features for anomaly detection in {domain_context}.

Application Domain: {domain}
{constraints_text}
Available Features (sorted by statistical importance):
{feature_text}

Requirements:
1. Select exactly {target_count} features
2. Prioritize features that:
   - Are computationally efficient (avoid complex transforms)
   - Have high discriminative power
   - Are robust to noise
   - Complement each other (low correlation)
   - Are interpretable for embedded deployment

3. Consider:
   - Statistical features (mean, std, variance) are very fast
   - FFT and spectral features are moderately expensive
   - Time-domain features are generally fast
   - Avoid highly correlated features

Provide your selection in this format:
<selection>
1. feature_name_1
2. feature_name_2
...
{target_count}. feature_name_{target_count}
</selection>

Reasoning:
[Brief explanation of why these features were selected]

<|eot_id|><|start_header_id|>assistant<|end_header_id|>

<selection>"""

    def _load_default_prompt(self) -> None:
        """Load the default prompt template into the textbox."""
        default_prompt = self._get_default_prompt_template()
        self.prompt_textbox.delete("1.0", "end")
        self.prompt_textbox.insert("1.0", default_prompt)

    def _reset_prompt(self) -> None:
        """Reset prompt to default template."""
        if messagebox.askyesno("Reset Prompt", "Reset prompt to default template? Your custom changes will be lost."):
            self._load_default_prompt()
            messagebox.showinfo("Success", "Prompt reset to default template")

    def _save_prompt(self) -> None:
        """Save the current prompt template to project."""
        if not self.project_manager.has_project():
            messagebox.showwarning("No Project", "Please create or open a project first.")
            return

        prompt_text = self.prompt_textbox.get("1.0", "end-1c")

        # Save to project
        project = self.project_manager.current_project
        if not hasattr(project, 'llm'):
            from dataclasses import dataclass, field
            @dataclass
            class LLMConfig:
                custom_prompt: str = ""
            project.llm = LLMConfig()

        project.llm.custom_prompt = prompt_text
        project.save()

        messagebox.showinfo("Success", "Prompt template saved to project")
        logger.info("LLM prompt template saved to project")

    def _select_features(self) -> None:
        """Select features using LLM."""
        # Get parameters
        try:
            target_count = int(self.feature_count_var.get())
            memory_kb = int(self.memory_var.get())
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter valid numbers.")
            return

        project = self.project_manager.current_project

        # Load extracted features from project
        if not project.features.extracted_features:
            messagebox.showwarning(
                "No Features",
                "No features extracted yet. Please extract features first in Feature Extraction stage."
            )
            return

        self.select_btn.configure(state="disabled")
        self.selection_progress_label.configure(
            text="🔄 Loading features and selecting...",
            text_color="gray"
        )

        def selection_thread():
            try:
                import pickle
                from pathlib import Path

                # Load features (use filtered features if available, otherwise extracted features)
                if project.features.filtered_features:
                    features_path = Path(project.features.filtered_features)
                    logger.info("Using filtered features")
                else:
                    features_path = Path(project.features.extracted_features)
                    logger.info("Using extracted features (no filtering applied)")

                with open(features_path, 'rb') as f:
                    features_df = pickle.load(f)

                feature_names = list(features_df.columns)
                logger.info(f"Loaded {len(feature_names)} features for selection")

                # Load windows to get class labels
                if project.data.train_test_split_type == "manual":
                    # Load combined windows for labels
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

                # Extract labels from windows
                labels = [w.class_label if hasattr(w, 'class_label') and w.class_label else "unknown" for w in windows]
                logger.info(f"Loaded {len(labels)} labels from windows")

                # Calculate rich feature statistics
                import numpy as np
                from sklearn.feature_selection import mutual_info_classif
                from sklearn.preprocessing import LabelEncoder

                feature_importance = {}
                feature_stats_per_class = {}

                # Calculate per-class statistics
                unique_labels = sorted(set(labels))
                logger.info(f"Computing statistics for {len(unique_labels)} classes")

                for col in feature_names:
                    # Overall importance (mean absolute value)
                    feature_importance[col] = features_df[col].abs().mean()

                    # Per-class statistics
                    class_stats = {}
                    for label in unique_labels:
                        label_mask = [l == label for l in labels]
                        class_data = features_df[col][label_mask]
                        class_stats[label] = {
                            'mean': float(class_data.mean()),
                            'std': float(class_data.std()),
                            'min': float(class_data.min()),
                            'max': float(class_data.max())
                        }
                    feature_stats_per_class[col] = class_stats

                # Calculate mutual information (class separation power) for top 100 features
                sorted_features = sorted(feature_names, key=lambda x: feature_importance.get(x, 0), reverse=True)[:100]
                X_top = features_df[sorted_features].values
                le = LabelEncoder()
                y_encoded = le.fit_transform(labels)

                mi_scores = mutual_info_classif(X_top, y_encoded, random_state=42)
                for feat, mi_score in zip(sorted_features, mi_scores):
                    feature_stats_per_class[feat]['mi_score'] = float(mi_score)

                logger.info("Calculated per-class statistics and mutual information scores")

                # Build platform constraints
                platform_constraints = {
                    'mcu': self.platform_var.get(),
                    'memory_kb': memory_kb
                }

                # Get custom prompt template from textbox
                custom_prompt_template = self.prompt_textbox.get("1.0", "end-1c")

                # Select features
                if self.llm_manager and self.llm_manager.is_loaded:
                    selection = self.llm_manager.select_features(
                        features=feature_names,
                        feature_importance=feature_importance,
                        domain=project.domain,
                        target_count=target_count,
                        platform_constraints=platform_constraints,
                        custom_prompt_template=custom_prompt_template,
                        feature_stats_per_class=feature_stats_per_class
                    )
                else:
                    # Use fallback
                    from core.llm_manager import LLMManager, LLMConfig
                    dummy_config = LLMConfig(model_path=Path("dummy"))
                    dummy_manager = LLMManager(dummy_config)
                    selection = dummy_manager._fallback_selection(
                        feature_names, feature_importance, target_count
                    )

                self.selected_features = selection.selected_features
                self.feature_stats_cache = feature_stats_per_class  # Store for results display
                self.feature_importance_cache = feature_importance

                # Save to project
                project.llm.selected_features = self.selected_features
                project.llm.num_selected = len(self.selected_features)
                project.llm.selection_reasoning = selection.reasoning
                project.llm.used_llm = not selection.fallback_used

                self.after(0, lambda: self._selection_complete(selection))

            except Exception as e:
                logger.error(f"Feature selection failed: {e}")
                self.after(0, lambda: self._selection_error(str(e)))

        thread = threading.Thread(target=selection_thread, daemon=True)
        thread.start()

    def _selection_complete(self, selection) -> None:
        """Handle successful feature selection."""
        self.selection_progress_label.configure(
            text=f"✓ Selected {len(selection.selected_features)} features",
            text_color="green"
        )
        self.select_btn.configure(state="normal")

        # Display results
        self.results_info_label.configure(
            text=f"✓ Selected {len(selection.selected_features)} features"
        )

        # Build results text
        results_text = f"Feature Selection Results\n"
        results_text += f"{'=' * 80}\n\n"
        results_text += f"Method: {'LLM-based' if not selection.fallback_used else 'Statistical fallback'}\n"
        results_text += f"Features selected: {len(selection.selected_features)}\n"
        results_text += f"Confidence: {selection.confidence:.2f}\n\n"

        results_text += f"Selected Features with Statistics:\n"
        results_text += f"{'-' * 80}\n\n"

        # Display detailed statistics for each selected feature
        decoder = FeatureNameDecoder()

        for i, feat in enumerate(selection.selected_features, 1):
            results_text += f"{i}. {feat}\n"

            # Add feature explanation
            try:
                feature_desc = decoder.get_short_description(feat)
                results_text += f"   📝 {feature_desc}\n"
            except Exception as e:
                logger.debug(f"Could not decode feature name: {e}")

            # Add importance score if available
            if self.feature_importance_cache and feat in self.feature_importance_cache:
                importance = self.feature_importance_cache[feat]
                results_text += f"   Importance: {importance:.4f}\n"

            # Add detailed statistics if available
            if self.feature_stats_cache and feat in self.feature_stats_cache:
                stats = self.feature_stats_cache[feat]

                # Mutual Information score
                if 'mi_score' in stats:
                    mi_score = stats['mi_score']
                    results_text += f"   Mutual Information: {mi_score:.4f}\n"

                # Per-class statistics
                results_text += f"   Class Statistics:\n"
                class_labels = [k for k in stats.keys() if k != 'mi_score']

                for class_label in sorted(class_labels):
                    class_stat = stats[class_label]
                    mean = class_stat['mean']
                    std = class_stat['std']
                    min_val = class_stat['min']
                    max_val = class_stat['max']
                    results_text += f"      {class_label}: mean={mean:.4f}, std={std:.4f}, min={min_val:.4f}, max={max_val:.4f}\n"

                # Calculate and show class separation (difference between max and min means)
                if len(class_labels) >= 2:
                    means = [stats[label]['mean'] for label in class_labels]
                    separation = max(means) - min(means)
                    if min(means) != 0:
                        separation_ratio = max(means) / min(means) if min(means) > 0 else float('inf')
                        results_text += f"   → Class separation: {separation:.4f} (ratio: {separation_ratio:.2f}x)\n"
                    else:
                        results_text += f"   → Class separation: {separation:.4f}\n"

            results_text += "\n"

        results_text += f"\nReasoning:\n"
        results_text += f"{'-' * 80}\n"
        results_text += f"{selection.reasoning}\n"

        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", results_text)

        self.export_btn.configure(state="normal")

        # Enable LLM analysis button if LLM is loaded
        if self.llm_manager and self.llm_manager.is_loaded:
            self.analyze_btn.configure(state="normal")
            self.analysis_info_label.configure(
                text="✓ Ready to generate LLM analysis and recommendations",
                text_color="green"
            )

        # Switch to Results tab
        self.tabview.set("Results")

        logger.info(f"Feature selection complete: {len(selection.selected_features)} features")

    def _selection_error(self, error: str) -> None:
        """Handle feature selection error."""
        self.selection_progress_label.configure(
            text=f"✗ Error: {error}",
            text_color="red"
        )
        self.select_btn.configure(state="normal")
        messagebox.showerror("Selection Error", f"Failed to select features:\n{error}")

    def _save_selection(self) -> None:
        """Save selected features to project."""
        if not self.selected_features:
            messagebox.showwarning("No Selection", "No features selected yet.")
            return

        project = self.project_manager.current_project

        # Mark stage as completed
        project.mark_stage_completed("llm")
        self.project_manager.save_project()

        messagebox.showinfo(
            "Saved",
            f"Feature selection saved!\n\n"
            f"Selected {len(self.selected_features)} features.\n"
            f"Proceed to Anomaly Model stage to train your model."
        )
        logger.info("Feature selection saved to project")

    def _update_selection_info(self) -> None:
        """Update selection info label."""
        if not self.project_manager.has_project():
            self.selection_info_label.configure(
                text="⚠️ No project loaded. Create or open a project first."
            )
            self.select_btn.configure(state="disabled")
            return

        project = self.project_manager.current_project

        # Check if features extracted
        if not project.features.extracted:
            self.selection_info_label.configure(
                text="⚠️ Extract features first in Feature Extraction stage"
            )
            self.select_btn.configure(state="disabled")
            return

        # Check if LLM loaded
        if not self.llm_manager or not self.llm_manager.is_loaded:
            self.selection_info_label.configure(
                text="⚠️ Load LLM model first (or use fallback selection)"
            )

        # Ready
        info_text = f"✓ Ready for feature selection\n"

        # Show filtered or extracted feature count
        if project.features.filtering_applied and project.features.num_features_filtered > 0:
            info_text += f"  Available features: {project.features.num_features_filtered} (filtered from {project.features.num_features_extracted})\n"
        else:
            info_text += f"  Available features: {project.features.num_features_extracted}\n"

        info_text += f"  LLM: {'Loaded' if self.llm_manager and self.llm_manager.is_loaded else 'Fallback mode'}"

        self.selection_info_label.configure(text=info_text)
        self.select_btn.configure(state="normal")

    def _generate_llm_analysis(self) -> None:
        """Generate LLM-powered analysis and recommendations for selected features."""
        if not self.selected_features:
            messagebox.showwarning("No Features", "Please select features first.")
            return

        if not self.llm_manager or not self.llm_manager.is_loaded:
            messagebox.showwarning("No LLM", "Please load the LLM model first.")
            return

        self.analyze_btn.configure(state="disabled")
        self.analysis_info_label.configure(text="Generating analysis...", text_color="blue")

        def analysis_thread():
            try:
                project = self.project_manager.current_project

                # Build feature summary with statistics
                feature_summary = []
                for i, feat in enumerate(self.selected_features, 1):
                    summary = f"{i}. {feat}"

                    if self.feature_importance_cache and feat in self.feature_importance_cache:
                        importance = self.feature_importance_cache[feat]
                        summary += f" (Importance: {importance:.4f})"

                    if self.feature_stats_cache and feat in self.feature_stats_cache:
                        stats = self.feature_stats_cache[feat]
                        if 'mi_score' in stats:
                            mi_score = stats['mi_score']
                            summary += f" (MI: {mi_score:.4f})"

                        # Add class means
                        class_labels = [k for k in stats.keys() if k != 'mi_score']
                        if len(class_labels) >= 2:
                            means = {label: stats[label]['mean'] for label in class_labels}
                            summary += f" [Means: {', '.join([f'{k}={v:.2f}' for k, v in means.items()])}]"

                    feature_summary.append(summary)

                # Build analysis prompt
                analysis_prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are an expert in embedded machine learning and time series analysis. Analyze the selected features and provide actionable recommendations.

<|eot_id|><|start_header_id|>user<|end_header_id|>

I have selected the following {len(self.selected_features)} features for anomaly detection:

{chr(10).join(feature_summary)}

Application Domain: {project.domain}
Target Platform: Resource-constrained embedded device (Cortex-M4, 256KB RAM)

Please provide a comprehensive analysis covering:

1. **Feature Quality Assessment**
   - Evaluate the MI (Mutual Information) scores
   - Assess class separation capability
   - Identify any potential issues or concerns

2. **Recommendations**
   - Are these features suitable for the application?
   - What improvements could be made?
   - Should we try different filtering thresholds?
   - Are there any redundant features?

3. **Next Steps**
   - What should the user do next?
   - Any specific actions to improve results?
   - Expected model performance with these features

4. **Risk Assessment**
   - Potential problems with current selection
   - Suggestions for validation
   - Alternative approaches to consider

Be specific, actionable, and explain your reasoning clearly.

<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

                # Generate analysis with LLM
                logger.info("Generating LLM analysis...")
                response = self.llm_manager.llm(
                    analysis_prompt,
                    max_tokens=2048,
                    temperature=0.7,
                    stop=["<|eot_id|>", "<|end_of_text|>"]
                )

                analysis_text = response['choices'][0]['text'].strip()

                self.after(0, lambda: self._display_analysis(analysis_text))

            except Exception as e:
                logger.error(f"LLM analysis failed: {e}")
                self.after(0, lambda: self._analysis_error(str(e)))

        thread = threading.Thread(target=analysis_thread, daemon=True)
        thread.start()

    def _display_analysis(self, analysis_text: str) -> None:
        """Display LLM analysis results."""
        self.analysis_info_label.configure(
            text="✓ Analysis complete",
            text_color="green"
        )
        self.analyze_btn.configure(state="normal")

        # Format the analysis text
        formatted_text = "LLM Feature Analysis & Recommendations\n"
        formatted_text += "=" * 80 + "\n\n"
        formatted_text += analysis_text

        self.analysis_text.delete("1.0", "end")
        self.analysis_text.insert("1.0", formatted_text)

        # Switch to Analysis tab
        self.tabview.set("LLM Analysis")

        logger.info("LLM analysis displayed")

    def _analysis_error(self, error: str) -> None:
        """Handle analysis error."""
        self.analysis_info_label.configure(
            text=f"✗ Error: {error}",
            text_color="red"
        )
        self.analyze_btn.configure(state="normal")
        messagebox.showerror("Analysis Error", f"Failed to generate analysis:\n{error}")

    def refresh(self) -> None:
        """Refresh panel with current project data."""
        # Auto-fill model path if exists and not already filled
        if not self.model_path_entry.get():
            model_path = Path.cwd() / "models" / "Llama-3.2-3B-Instruct-Q4_K_M.gguf"
            if model_path.exists():
                self.model_path_entry.delete(0, "end")
                self.model_path_entry.insert(0, str(model_path))
                self.model_info_label.configure(
                    text=f"✓ Model found ({model_path.stat().st_size / 1024 / 1024:.0f} MB) - Click 'Load Model' to use it",
                    text_color="green"
                )

        # Load previous results if they exist
        project = self.project_manager.current_project
        if project and project.llm.selected_features:
            self.selected_features = project.llm.selected_features

            # Create a mock selection result to display
            from core.llm_manager import FeatureSelection
            selection = FeatureSelection(
                selected_features=project.llm.selected_features,
                reasoning=project.llm.selection_reasoning or "Previously selected features",
                confidence=0.0,  # No confidence score saved
                fallback_used=project.llm.fallback_used
            )
            self._selection_complete(selection)

        self._update_selection_info()

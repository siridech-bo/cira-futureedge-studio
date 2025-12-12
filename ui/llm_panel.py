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

        # Setup each tab
        self._setup_model_tab()
        self._setup_selection_tab()
        self._setup_results_tab()

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

        # Info
        self.selection_info_label = ctk.CTkLabel(
            tab,
            text="Extract features first in Feature Extraction stage",
            font=("Segoe UI", 12),
            text_color="gray"
        )
        self.selection_info_label.grid(row=0, column=0, padx=20, pady=20)

        # Selection parameters
        params_frame = ctk.CTkFrame(tab)
        params_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
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

        # Select button
        select_frame = ctk.CTkFrame(tab, fg_color="transparent")
        select_frame.grid(row=2, column=0, pady=20)

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

        # Progress
        self.selection_progress_label = ctk.CTkLabel(
            tab,
            text="",
            font=("Segoe UI", 11)
        )
        self.selection_progress_label.grid(row=3, column=0, pady=5)

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
            font=("Courier New", 10),
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

                # Load extracted features
                features_path = Path(project.features.extracted_features)
                with open(features_path, 'rb') as f:
                    features_df = pickle.load(f)

                feature_names = list(features_df.columns)
                logger.info(f"Loaded {len(feature_names)} extracted features")

                # Calculate feature importance (mean absolute value)
                feature_importance = {}
                for col in feature_names:
                    feature_importance[col] = features_df[col].abs().mean()

                # Build platform constraints
                platform_constraints = {
                    'mcu': self.platform_var.get(),
                    'memory_kb': memory_kb
                }

                # Select features
                if self.llm_manager and self.llm_manager.is_loaded:
                    selection = self.llm_manager.select_features(
                        features=feature_names,
                        feature_importance=feature_importance,
                        domain=project.domain,
                        target_count=target_count,
                        platform_constraints=platform_constraints
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
        results_text += f"{'=' * 60}\n\n"
        results_text += f"Method: {'LLM-based' if not selection.fallback_used else 'Statistical fallback'}\n"
        results_text += f"Features selected: {len(selection.selected_features)}\n"
        results_text += f"Confidence: {selection.confidence:.2f}\n\n"

        results_text += f"Selected Features:\n"
        results_text += f"{'-' * 60}\n"
        for i, feat in enumerate(selection.selected_features, 1):
            results_text += f"{i}. {feat}\n"

        results_text += f"\nReasoning:\n"
        results_text += f"{'-' * 60}\n"
        results_text += f"{selection.reasoning}\n"

        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", results_text)

        self.export_btn.configure(state="normal")

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
        info_text += f"  Available features: {project.features.num_features_extracted}\n"
        info_text += f"  LLM: {'Loaded' if self.llm_manager and self.llm_manager.is_loaded else 'Fallback mode'}"

        self.selection_info_label.configure(text=info_text)
        self.select_btn.configure(state="normal")

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

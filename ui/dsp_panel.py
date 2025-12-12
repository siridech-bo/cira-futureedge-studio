"""
CiRA FutureEdge Studio - DSP Code Generation Panel
UI for configuring and generating embedded C++ code
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from pathlib import Path
from typing import Optional
import threading
import subprocess

from core.project import ProjectManager
from core.dsp_generator import DSPGenerator, DSPConfig
from loguru import logger


class DSPPanel(ctk.CTkFrame):
    """Panel for DSP code generation and configuration."""

    def __init__(self, parent, project_manager: ProjectManager):
        """Initialize the DSP panel."""
        super().__init__(parent)
        self.project_manager = project_manager
        self.generated_code = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create notebook for tabs
        self.notebook = ctk.CTkTabview(self)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Add tabs
        self.notebook.add("Platform")
        self.notebook.add("Generation")
        self.notebook.add("Preview")
        self.notebook.add("Export")

        self._create_platform_tab()
        self._create_generation_tab()
        self._create_preview_tab()
        self._create_export_tab()

    def _create_platform_tab(self):
        """Create platform configuration tab."""
        tab = self.notebook.tab("Platform")
        tab.grid_columnconfigure(0, weight=1)

        # Title
        title = ctk.CTkLabel(
            tab,
            text="Target Platform Configuration",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Platform selection
        platform_frame = ctk.CTkFrame(tab)
        platform_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        platform_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(platform_frame, text="Target Platform:").grid(
            row=0, column=0, padx=10, pady=10, sticky="w"
        )

        self.platform_var = ctk.StringVar(value="cortex-m4")
        platform_menu = ctk.CTkOptionMenu(
            platform_frame,
            variable=self.platform_var,
            values=["cortex-m4", "cortex-m7", "esp32", "esp32-s3", "x86"],
            command=self._on_platform_change
        )
        platform_menu.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        self.platform_info_label = ctk.CTkLabel(
            platform_frame,
            text="32-bit ARM Cortex-M4, 64KB RAM typical",
            text_color="gray"
        )
        self.platform_info_label.grid(row=0, column=2, padx=10, pady=10, sticky="w")

        # Memory settings
        memory_frame = ctk.CTkFrame(tab)
        memory_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        memory_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(memory_frame, text="RAM Limit (KB):").grid(
            row=0, column=0, padx=10, pady=10, sticky="w"
        )
        self.ram_limit_var = ctk.StringVar(value="64")
        ram_entry = ctk.CTkEntry(memory_frame, textvariable=self.ram_limit_var, width=100)
        ram_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(memory_frame, text="Window Size:").grid(
            row=1, column=0, padx=10, pady=10, sticky="w"
        )
        self.window_size_var = ctk.StringVar(value="128")
        window_entry = ctk.CTkEntry(memory_frame, textvariable=self.window_size_var, width=100)
        window_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(memory_frame, text="Sample Rate (Hz):").grid(
            row=2, column=0, padx=10, pady=10, sticky="w"
        )
        self.sample_rate_var = ctk.StringVar(value="1000")
        rate_entry = ctk.CTkEntry(memory_frame, textvariable=self.sample_rate_var, width=100)
        rate_entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        # Optimization settings
        opt_frame = ctk.CTkFrame(tab)
        opt_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(
            opt_frame,
            text="Optimizations:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.fixed_point_var = ctk.BooleanVar(value=True)
        fixed_point_check = ctk.CTkCheckBox(
            opt_frame,
            text="Use fixed-point arithmetic (faster on MCU)",
            variable=self.fixed_point_var
        )
        fixed_point_check.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.optimize_size_var = ctk.BooleanVar(value=True)
        size_check = ctk.CTkCheckBox(
            opt_frame,
            text="Optimize for code size (vs speed)",
            variable=self.optimize_size_var
        )
        size_check.grid(row=2, column=0, padx=10, pady=5, sticky="w")

    def _create_generation_tab(self):
        """Create code generation tab."""
        tab = self.notebook.tab("Generation")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        # Title
        title = ctk.CTkLabel(
            tab,
            text="Generate Embedded C++ Code",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Model selection
        model_select_frame = ctk.CTkFrame(tab)
        model_select_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        model_select_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(model_select_frame, text="Select Model:").grid(
            row=0, column=0, padx=10, pady=10, sticky="w"
        )

        self.model_var = ctk.StringVar(value="No models available")
        self.model_menu = ctk.CTkOptionMenu(
            model_select_frame,
            variable=self.model_var,
            values=["No models available"],
            command=self._on_model_change
        )
        self.model_menu.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        self.model_menu.configure(state="disabled")

        # Status
        status_frame = ctk.CTkFrame(tab)
        status_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        status_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(status_frame, text="Algorithm:").grid(
            row=0, column=0, padx=10, pady=5, sticky="w"
        )
        self.model_status_label = ctk.CTkLabel(
            status_frame,
            text="No model selected",
            text_color="gray"
        )
        self.model_status_label.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(status_frame, text="Features:").grid(
            row=1, column=0, padx=10, pady=5, sticky="w"
        )
        self.features_status_label = ctk.CTkLabel(
            status_frame,
            text="0 features",
            text_color="gray"
        )
        self.features_status_label.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # Generate button
        self.generate_btn = ctk.CTkButton(
            tab,
            text="Generate C++ Code",
            command=self._generate_code,
            fg_color="green",
            hover_color="darkgreen",
            height=40,
            state="disabled"
        )
        self.generate_btn.grid(row=2, column=0, padx=20, pady=20)

        self.generate_status_label = ctk.CTkLabel(tab, text="")
        self.generate_status_label.grid(row=3, column=0, padx=20, pady=5)

        # Log
        log_frame = ctk.CTkFrame(tab)
        log_frame.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            log_frame,
            text="Generation Log:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.generation_log = ctk.CTkTextbox(log_frame, height=150)
        self.generation_log.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    def _create_preview_tab(self):
        """Create code preview tab."""
        tab = self.notebook.tab("Preview")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Title
        title = ctk.CTkLabel(
            tab,
            text="Generated Code Preview",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # File selector
        file_frame = ctk.CTkFrame(tab)
        file_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(file_frame, text="File:").pack(side="left", padx=10)

        self.preview_file_var = ctk.StringVar(value="anomaly_detector.h")
        file_menu = ctk.CTkOptionMenu(
            file_frame,
            variable=self.preview_file_var,
            values=["anomaly_detector.h", "anomaly_detector.cpp", "features.cpp", "config.h"],
            command=self._on_preview_file_change
        )
        file_menu.pack(side="left", padx=10)

        # Preview
        preview_frame = ctk.CTkFrame(tab)
        preview_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(0, weight=1)

        self.preview_text = ctk.CTkTextbox(preview_frame, wrap="none")
        self.preview_text.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.preview_text.insert("1.0", "Generate code first to see preview...")
        self.preview_text.configure(state="disabled")

    def _create_export_tab(self):
        """Create export tab."""
        tab = self.notebook.tab("Export")
        tab.grid_columnconfigure(0, weight=1)

        # Title
        title = ctk.CTkLabel(
            tab,
            text="Export Generated Code",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Status
        status_frame = ctk.CTkFrame(tab)
        status_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        status_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(status_frame, text="Status:").grid(
            row=0, column=0, padx=10, pady=10, sticky="w"
        )
        self.export_status_label = ctk.CTkLabel(
            status_frame,
            text="No code generated yet",
            text_color="gray"
        )
        self.export_status_label.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(status_frame, text="Output:").grid(
            row=1, column=0, padx=10, pady=10, sticky="w"
        )
        self.output_path_label = ctk.CTkLabel(
            status_frame,
            text="",
            text_color="blue"
        )
        self.output_path_label.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # Estimates
        est_frame = ctk.CTkFrame(tab)
        est_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        est_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            est_frame,
            text="Resource Estimates:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(est_frame, text="Code Size:").grid(
            row=1, column=0, padx=10, pady=5, sticky="w"
        )
        self.code_size_label = ctk.CTkLabel(est_frame, text="-", text_color="blue")
        self.code_size_label.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(est_frame, text="RAM Usage:").grid(
            row=2, column=0, padx=10, pady=5, sticky="w"
        )
        self.ram_usage_label = ctk.CTkLabel(est_frame, text="-", text_color="blue")
        self.ram_usage_label.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        # Buttons
        btn_frame = ctk.CTkFrame(tab)
        btn_frame.grid(row=3, column=0, padx=20, pady=20, sticky="ew")

        self.open_folder_btn = ctk.CTkButton(
            btn_frame,
            text="Open Output Folder",
            command=self._open_output_folder,
            state="disabled"
        )
        self.open_folder_btn.pack(side="left", padx=10)

        self.complete_btn = ctk.CTkButton(
            btn_frame,
            text="Save & Continue to Build",
            command=self._mark_complete,
            fg_color="green",
            hover_color="darkgreen",
            state="disabled"
        )
        self.complete_btn.pack(side="left", padx=10)

    def _on_platform_change(self, platform: str):
        """Handle platform selection change."""
        info = {
            "cortex-m4": "32-bit ARM Cortex-M4, 64KB RAM typical",
            "cortex-m7": "32-bit ARM Cortex-M7, 256KB RAM typical",
            "esp32": "32-bit Xtensa LX6, 320KB RAM",
            "esp32-s3": "32-bit Xtensa LX7, 512KB RAM",
            "x86": "x86/x64 desktop, unlimited RAM"
        }
        self.platform_info_label.configure(text=info.get(platform, ""))

    def _on_model_change(self, model_name: str):
        """Handle model selection change."""
        if model_name and model_name != "No models available":
            self.model_status_label.configure(
                text=f"{model_name.upper()}",
                text_color="green"
            )
            self.generate_btn.configure(state="normal")
        else:
            self.model_status_label.configure(
                text="No model selected",
                text_color="gray"
            )
            self.generate_btn.configure(state="disabled")

    def _on_preview_file_change(self, filename: str):
        """Handle preview file selection change."""
        if not self.generated_code:
            return

        file_map = {
            "anomaly_detector.h": self.generated_code.header_file,
            "anomaly_detector.cpp": self.generated_code.source_file,
            "features.cpp": self.generated_code.features_file,
            "config.h": self.generated_code.config_file
        }

        file_path = file_map.get(filename)
        if file_path and Path(file_path).exists():
            content = Path(file_path).read_text()
            self.preview_text.configure(state="normal")
            self.preview_text.delete("1.0", "end")
            self.preview_text.insert("1.0", content)
            self.preview_text.configure(state="disabled")

    def _generate_code(self):
        """Generate C++ code in background thread."""
        project = self.project_manager.current_project
        if not project or not project.model.trained:
            messagebox.showerror("Error", "No trained model found")
            return

        # Validate inputs
        try:
            ram_limit = int(self.ram_limit_var.get())
            window_size = int(self.window_size_var.get())
            sample_rate = int(self.sample_rate_var.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers")
            return

        # Build config
        config = DSPConfig(
            target_platform=self.platform_var.get(),
            use_fixed_point=self.fixed_point_var.get(),
            optimize_size=self.optimize_size_var.get(),
            window_size=window_size,
            sample_rate=sample_rate,
            memory_limit_kb=ram_limit
        )

        # Disable button
        self.generate_btn.configure(state="disabled")
        self.generate_status_label.configure(text="Generating...", text_color="blue")
        self.generation_log.delete("1.0", "end")

        def generation_thread():
            try:
                self._log("Starting code generation...")

                # Get selected model name
                selected_model = self.model_var.get()
                if not selected_model or selected_model == "No models available":
                    raise ValueError("No model selected")

                # Get paths for selected model
                model_dir = project.get_project_dir() / "models"
                model_path = model_dir / f"{selected_model}_model.pkl"
                scaler_path = model_dir / f"{selected_model}_scaler.pkl"

                if not model_path.exists():
                    raise ValueError(f"Model file not found: {model_path}")

                # Check if scaler exists
                if not scaler_path.exists():
                    scaler_path = None

                output_dir = project.get_project_dir() / "dsp" / selected_model

                self._log(f"Model: {selected_model}")
                self._log(f"Features: {len(project.llm.selected_features)}")
                self._log(f"Platform: {config.target_platform}")

                # Generate
                generator = DSPGenerator()
                self.generated_code = generator.generate(
                    model_path,
                    scaler_path,
                    project.llm.selected_features,
                    config,
                    output_dir
                )

                self.after(0, lambda: self._generation_complete(self.generated_code))

            except Exception as e:
                logger.error(f"Code generation failed: {e}")
                self.after(0, lambda: self._generation_failed(str(e)))

        thread = threading.Thread(target=generation_thread, daemon=True)
        thread.start()

    def _log(self, message: str):
        """Add message to generation log."""
        def update():
            self.generation_log.insert("end", f"{message}\n")
            self.generation_log.see("end")

        self.after(0, update)

    def _generation_complete(self, result):
        """Handle generation completion."""
        self.generate_btn.configure(state="normal")
        self.generate_status_label.configure(text="✓ Generation complete", text_color="green")

        self._log("\n" + "="*50)
        self._log("GENERATION COMPLETE")
        self._log("="*50)
        self._log(f"Algorithm: {result.algorithm}")
        self._log(f"Features: {result.num_features}")
        self._log(f"Code size: {result.code_size_estimate:,} bytes")
        self._log(f"RAM usage: {result.ram_usage_estimate:,} bytes")

        # Update export tab
        self.export_status_label.configure(
            text=f"✓ Generated {result.algorithm} code",
            text_color="green"
        )
        self.output_path_label.configure(text=str(Path(result.header_file).parent))
        self.code_size_label.configure(text=f"{result.code_size_estimate / 1024:.1f} KB")
        self.ram_usage_label.configure(text=f"{result.ram_usage_estimate / 1024:.1f} KB")
        self.open_folder_btn.configure(state="normal")
        self.complete_btn.configure(state="normal")

        # Update preview
        self._on_preview_file_change(self.preview_file_var.get())

        # Switch to preview tab
        self.notebook.set("Preview")

        messagebox.showinfo(
            "Generation Complete",
            f"Generated C++ code for {result.algorithm}\n\n"
            f"Files: 4\n"
            f"Code size: ~{result.code_size_estimate / 1024:.1f} KB\n"
            f"RAM usage: ~{result.ram_usage_estimate / 1024:.1f} KB"
        )

    def _generation_failed(self, error: str):
        """Handle generation failure."""
        self.generate_btn.configure(state="normal")
        self.generate_status_label.configure(text="✗ Generation failed", text_color="red")
        self._log(f"\nERROR: {error}")

        messagebox.showerror("Generation Failed", f"Code generation failed:\n{error}")

    def _open_output_folder(self):
        """Open the output folder in file explorer."""
        project = self.project_manager.current_project
        if not project:
            return

        # If code was just generated, use that path
        if self.generated_code:
            folder = Path(self.generated_code.header_file).parent
        else:
            # Otherwise, use the selected model's DSP directory
            selected_model = self.model_var.get()
            if not selected_model or selected_model == "No models available":
                return
            folder = project.get_project_dir() / "dsp" / selected_model

        if folder.exists():
            subprocess.Popen(['explorer', str(folder)])

    def _mark_complete(self):
        """Mark DSP stage as complete."""
        project = self.project_manager.current_project
        if not project:
            return

        project.mark_stage_completed("dsp")
        self.project_manager.save_project()

        messagebox.showinfo(
            "Stage Complete",
            "DSP code generation completed!\n\n"
            "Proceed to Build stage to compile firmware."
        )

    def refresh(self):
        """Refresh panel with current project data."""
        project = self.project_manager.current_project
        if not project:
            return

        # Find all trained models
        model_dir = project.get_project_dir() / "models"
        if model_dir.exists():
            models = list(model_dir.glob("*_model.pkl"))
            if models:
                model_names = [m.stem.replace('_model', '') for m in models]

                # Update dropdown
                self.model_menu.configure(values=model_names, state="normal")
                self.model_var.set(model_names[0])  # Select first model

                # Trigger update
                self._on_model_change(model_names[0])

                # Update features
                self.features_status_label.configure(
                    text=f"{len(project.llm.selected_features)} features",
                    text_color="green"
                )

                # Check if DSP code already exists for the first model
                dsp_dir = project.get_project_dir() / "dsp" / model_names[0]
                if dsp_dir.exists():
                    header_file = dsp_dir / "anomaly_detector.h"
                    if header_file.exists():
                        # Enable export tab buttons
                        self.export_status_label.configure(
                            text=f"✓ Generated {model_names[0]} code",
                            text_color="green"
                        )
                        self.output_path_label.configure(text=str(dsp_dir))
                        self.open_folder_btn.configure(state="normal")
                        self.complete_btn.configure(state="normal")

                return

        # No models found
        self.model_menu.configure(values=["No models available"], state="disabled")
        self.model_var.set("No models available")
        self.model_status_label.configure(
            text="No model trained yet",
            text_color="red"
        )
        self.generate_btn.configure(state="disabled")

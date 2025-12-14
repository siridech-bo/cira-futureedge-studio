"""
CiRA FutureEdge Studio - Build Firmware Panel
UI for generating firmware build system and compilation
"""

import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
from typing import Optional
import threading
import subprocess
import shutil

from core.project import ProjectManager
from core.firmware_builder import FirmwareBuilder, BuildConfig
from loguru import logger


class BuildPanel(ctk.CTkFrame):
    """Panel for firmware build generation."""

    def __init__(self, parent, project_manager: ProjectManager):
        """Initialize the build panel."""
        super().__init__(parent)
        self.project_manager = project_manager
        self.builder = FirmwareBuilder()
        self.build_artifacts = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create notebook for tabs
        self.notebook = ctk.CTkTabview(self)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Add tabs
        self.notebook.add("Configuration")
        self.notebook.add("Generate")
        self.notebook.add("Files")
        self.notebook.add("Deploy")

        self._create_config_tab()
        self._create_generate_tab()
        self._create_files_tab()
        self._create_deploy_tab()

    def _create_config_tab(self):
        """Create build configuration tab."""
        tab = self.notebook.tab("Configuration")
        tab.grid_columnconfigure(0, weight=1)

        # Title
        title = ctk.CTkLabel(
            tab,
            text="Build Configuration",
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
            values=["cortex-m4", "cortex-m7", "esp32", "esp32-s3", "x86"]
        )
        platform_menu.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # Optimization
        ctk.CTkLabel(platform_frame, text="Optimization:").grid(
            row=1, column=0, padx=10, pady=10, sticky="w"
        )

        self.optimization_var = ctk.StringVar(value="Os")
        opt_menu = ctk.CTkOptionMenu(
            platform_frame,
            variable=self.optimization_var,
            values=["Os (Size)", "O2 (Balanced)", "O3 (Speed)"]
        )
        opt_menu.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # Options
        options_frame = ctk.CTkFrame(tab)
        options_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(
            options_frame,
            text="Build Options:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.use_float_var = ctk.BooleanVar(value=True)
        float_check = ctk.CTkCheckBox(
            options_frame,
            text="Use floating-point math",
            variable=self.use_float_var
        )
        float_check.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.use_rtos_var = ctk.BooleanVar(value=False)
        rtos_check = ctk.CTkCheckBox(
            options_frame,
            text="Include RTOS support",
            variable=self.use_rtos_var
        )
        rtos_check.grid(row=2, column=0, padx=10, pady=5, sticky="w")

        self.gen_docs_var = ctk.BooleanVar(value=True)
        docs_check = ctk.CTkCheckBox(
            options_frame,
            text="Generate documentation",
            variable=self.gen_docs_var
        )
        docs_check.grid(row=3, column=0, padx=10, pady=5, sticky="w")

    def _create_generate_tab(self):
        """Create build generation tab."""
        tab = self.notebook.tab("Generate")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(3, weight=1)  # Log frame expands, not button row

        # Title
        title = ctk.CTkLabel(
            tab,
            text="Generate Build System",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Status
        status_frame = ctk.CTkFrame(tab)
        status_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        status_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(status_frame, text="DSP Code:").grid(
            row=0, column=0, padx=10, pady=5, sticky="w"
        )
        self.dsp_status_label = ctk.CTkLabel(
            status_frame,
            text="No DSP code generated",
            text_color="gray"
        )
        self.dsp_status_label.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        # Model selector
        ctk.CTkLabel(status_frame, text="Select Model:").grid(
            row=1, column=0, padx=10, pady=5, sticky="w"
        )

        self.model_var = ctk.StringVar(value="No models available")
        self.model_menu = ctk.CTkOptionMenu(
            status_frame,
            variable=self.model_var,
            values=["No models available"]
        )
        self.model_menu.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        self.model_menu.configure(state="disabled")

        # Generate button and status in a frame
        button_frame = ctk.CTkFrame(tab, fg_color="transparent")
        button_frame.grid(row=2, column=0, padx=20, pady=10)

        self.generate_btn = ctk.CTkButton(
            button_frame,
            text="Generate Build Files",
            command=self._generate_build,
            fg_color="green",
            hover_color="darkgreen",
            height=40,
            state="disabled"
        )
        self.generate_btn.pack(pady=5)

        self.generate_status_label = ctk.CTkLabel(button_frame, text="")
        self.generate_status_label.pack(pady=5)

        # Log
        log_frame = ctk.CTkFrame(tab)
        log_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            log_frame,
            text="Generation Log:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.generation_log = ctk.CTkTextbox(log_frame, height=150)
        self.generation_log.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    def _create_files_tab(self):
        """Create generated files tab."""
        tab = self.notebook.tab("Files")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Title
        title = ctk.CTkLabel(
            tab,
            text="Generated Build Files",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Files list
        files_frame = ctk.CTkFrame(tab)
        files_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        files_frame.grid_columnconfigure(0, weight=1)
        files_frame.grid_rowconfigure(0, weight=1)

        self.files_text = ctk.CTkTextbox(files_frame)
        self.files_text.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.files_text.insert("1.0", "Generate build files to see contents...")
        self.files_text.configure(state="disabled")

    def _create_deploy_tab(self):
        """Create deployment tab."""
        tab = self.notebook.tab("Deploy")
        tab.grid_columnconfigure(0, weight=1)

        # Title
        title = ctk.CTkLabel(
            tab,
            text="Deploy Firmware",
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
        self.deploy_status_label = ctk.CTkLabel(
            status_frame,
            text="No build files generated",
            text_color="gray"
        )
        self.deploy_status_label.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(status_frame, text="Output:").grid(
            row=1, column=0, padx=10, pady=10, sticky="w"
        )
        self.output_path_label = ctk.CTkLabel(
            status_frame,
            text="",
            text_color="blue"
        )
        self.output_path_label.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # Instructions
        inst_frame = ctk.CTkFrame(tab)
        inst_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        inst_frame.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            inst_frame,
            text="Build Instructions:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.instructions_text = ctk.CTkTextbox(inst_frame, height=200)
        self.instructions_text.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        inst_frame.grid_rowconfigure(1, weight=1)

        # Buttons
        btn_frame = ctk.CTkFrame(tab)
        btn_frame.grid(row=3, column=0, padx=20, pady=20)

        self.open_folder_btn = ctk.CTkButton(
            btn_frame,
            text="Open Build Folder",
            command=self._open_build_folder,
            state="disabled"
        )
        self.open_folder_btn.pack(side="left", padx=10)

        self.complete_btn = ctk.CTkButton(
            btn_frame,
            text="✓ Project Complete!",
            command=self._mark_complete,
            fg_color="green",
            hover_color="darkgreen",
            state="disabled",
            height=40
        )
        self.complete_btn.pack(side="left", padx=10)

    def _generate_build(self):
        """Generate build system."""
        project = self.project_manager.current_project
        if not project:
            messagebox.showerror("Error", "No project loaded")
            return

        # Get selected model
        selected_model = self.model_var.get()
        if not selected_model or selected_model == "No models available":
            messagebox.showerror("Error", "No model selected")
            return

        # Get DSP code directory
        dsp_dir = project.get_project_dir() / "dsp" / selected_model
        if not dsp_dir.exists():
            messagebox.showerror(
                "Error",
                f"DSP code not found for {selected_model}\n"
                f"Generate DSP code first in the DSP Generation stage."
            )
            return

        # Build config
        opt_map = {"Os (Size)": "Os", "O2 (Balanced)": "O2", "O3 (Speed)": "O3"}
        config = BuildConfig(
            platform=self.platform_var.get(),
            optimization=opt_map.get(self.optimization_var.get(), "Os"),
            use_float=self.use_float_var.get(),
            use_rtos=self.use_rtos_var.get(),
            generate_docs=self.gen_docs_var.get()
        )

        # Disable button
        self.generate_btn.configure(state="disabled")
        self.generate_status_label.configure(text="Generating...", text_color="blue")
        self.generation_log.delete("1.0", "end")

        def generation_thread():
            try:
                self._log("Starting build system generation...")
                self._log(f"Platform: {config.platform}")
                self._log(f"Optimization: {config.optimization}")
                self._log(f"DSP Code: {dsp_dir}")

                # Output directory
                output_dir = project.get_project_dir() / "firmware" / selected_model

                # Copy DSP files
                output_dir.mkdir(parents=True, exist_ok=True)
                self._log("Copying DSP code files...")

                for file in dsp_dir.glob("*.h"):
                    shutil.copy(file, output_dir / file.name)
                for file in dsp_dir.glob("*.cpp"):
                    shutil.copy(file, output_dir / file.name)

                # Generate build files
                self._log("Generating build files...")
                self.build_artifacts = self.builder.generate_build_files(
                    dsp_dir,
                    config,
                    output_dir
                )

                self.after(0, lambda: self._generation_complete(self.build_artifacts, output_dir))

            except Exception as e:
                logger.error(f"Build generation failed: {e}")
                self.after(0, lambda: self._generation_failed(str(e)))

        thread = threading.Thread(target=generation_thread, daemon=True)
        thread.start()

    def _log(self, message: str):
        """Add message to generation log."""
        def update():
            self.generation_log.insert("end", f"{message}\n")
            self.generation_log.see("end")

        self.after(0, update)

    def _generation_complete(self, artifacts, output_dir):
        """Handle generation completion."""
        self.generate_btn.configure(state="normal")
        self.generate_status_label.configure(text="✓ Generation complete", text_color="green")

        self._log("\n" + "="*50)
        self._log("BUILD SYSTEM GENERATED")
        self._log("="*50)
        self._log(f"Platform: {artifacts.platform}")
        self._log(f"Output: {output_dir}")
        self._log("\nGenerated files:")
        self._log(f"  - CMakeLists.txt")
        self._log(f"  - main.cpp")
        self._log(f"  - README.md")
        self._log(f"  - build.sh/bat")

        # Update Files tab
        files_content = f"""Generated Build Files
{'='*50}

CMakeLists.txt - Build configuration
main.cpp - Application entry point
README.md - Build instructions
build.sh/bat - Build automation script

DSP Code Files:
anomaly_detector.h - Detection header
anomaly_detector.cpp - Detection implementation
features.cpp - Feature extraction
config.h - Platform configuration

Location: {output_dir}
"""
        self.files_text.configure(state="normal")
        self.files_text.delete("1.0", "end")
        self.files_text.insert("1.0", files_content)
        self.files_text.configure(state="disabled")

        # Update Deploy tab
        self.deploy_status_label.configure(
            text=f"✓ Build files ready for {artifacts.platform}",
            text_color="green"
        )
        self.output_path_label.configure(text=str(output_dir))

        # Load README
        readme_path = Path(artifacts.readme_file)
        if readme_path.exists():
            readme_content = readme_path.read_text()
            self.instructions_text.delete("1.0", "end")
            self.instructions_text.insert("1.0", readme_content)

        self.open_folder_btn.configure(state="normal")
        self.complete_btn.configure(state="normal")

        # Switch to Deploy tab
        self.notebook.set("Deploy")

        messagebox.showinfo(
            "Build System Generated",
            f"Build files generated successfully!\n\n"
            f"Platform: {artifacts.platform}\n"
            f"Location: {output_dir}\n\n"
            f"See README.md for build instructions."
        )

        # Save to project
        project = self.project_manager.current_project
        project.build.output_dir = str(output_dir)
        project.build.target_platform = artifacts.platform
        project.save()

    def _generation_failed(self, error: str):
        """Handle generation failure."""
        self.generate_btn.configure(state="normal")
        self.generate_status_label.configure(text="✗ Generation failed", text_color="red")
        self._log(f"\nERROR: {error}")

        messagebox.showerror("Generation Failed", f"Build generation failed:\n{error}")

    def _open_build_folder(self):
        """Open the build folder."""
        project = self.project_manager.current_project
        if project and project.build.output_dir:
            import subprocess
            subprocess.Popen(['explorer', project.build.output_dir])

    def _mark_complete(self):
        """Mark build stage as complete."""
        project = self.project_manager.current_project
        if not project:
            return

        project.mark_stage_completed("build")
        self.project_manager.save_project()

        messagebox.showinfo(
            "Project Complete!",
            "Congratulations! Your anomaly detection firmware is ready.\n\n"
            "✓ Data processed\n"
            "✓ Features extracted\n"
            "✓ Model trained\n"
            "✓ C++ code generated\n"
            "✓ Build system created\n\n"
            "Follow the build instructions to compile and deploy!"
        )

    def refresh(self):
        """Refresh panel with current project data."""
        project = self.project_manager.current_project
        if not project:
            return

        # Check for DSP code
        dsp_base = project.get_project_dir() / "dsp"
        if dsp_base.exists():
            models = [d.name for d in dsp_base.iterdir() if d.is_dir()]
            if models:
                self.dsp_status_label.configure(
                    text=f"✓ {len(models)} model(s) with DSP code",
                    text_color="green"
                )
                self.model_menu.configure(values=models, state="normal")
                self.model_var.set(models[0])
                self.generate_btn.configure(state="normal")
                return

        self.dsp_status_label.configure(
            text="No DSP code generated",
            text_color="red"
        )
        self.generate_btn.configure(state="disabled")

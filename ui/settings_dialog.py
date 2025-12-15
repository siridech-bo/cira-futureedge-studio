"""
CiRA FutureEdge Studio - Settings Dialog
Application-wide settings and preferences
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Optional
import os
import platform
import multiprocessing

from core.config import Config
from core.license_manager import get_license_manager
from core.license import LicenseStatus
from loguru import logger


class SettingsDialog(ctk.CTkToplevel):
    """Settings dialog window."""

    def __init__(self, parent, config: Config):
        """Initialize settings dialog."""
        super().__init__(parent)

        self.config = config
        self.modified = False

        # Window setup
        self.title("⚙️ Settings - CiRA FutureEdge Studio")
        self.geometry("900x700")

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"+{x}+{y}")

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create main container
        main_container = ctk.CTkFrame(self)
        main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(0, weight=1)

        # Create tabview
        self.tabview = ctk.CTkTabview(main_container)
        self.tabview.grid(row=0, column=0, sticky="nsew", pady=(0, 5))

        # Add tabs
        self.tabview.add("LLM")
        self.tabview.add("Build")
        self.tabview.add("Paths")
        self.tabview.add("Performance")
        self.tabview.add("Logging")
        self.tabview.add("License")

        # Create tab contents
        self._create_llm_tab()
        self._create_build_tab()
        self._create_paths_tab()
        self._create_performance_tab()
        self._create_logging_tab()
        self._create_license_tab()

        # Buttons at bottom
        button_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        button_frame.grid(row=1, column=0, pady=(5, 0), sticky="ew")
        button_frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(
            button_frame,
            text="Restore Defaults",
            command=self._restore_defaults,
            width=150
        ).grid(row=0, column=0, padx=5)

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._cancel,
            width=150
        ).grid(row=0, column=1, padx=5)

        ctk.CTkButton(
            button_frame,
            text="Save",
            command=self._save,
            fg_color="green",
            hover_color="darkgreen",
            width=150
        ).grid(row=0, column=2, padx=5)

        # Load current settings
        self._load_settings()

    def _create_llm_tab(self):
        """Create LLM settings tab."""
        tab = self.tabview.tab("LLM")
        tab.grid_columnconfigure(0, weight=1)

        # Title
        ctk.CTkLabel(
            tab,
            text="🤖 LLM Configuration",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(10, 5), sticky="w")

        # Settings frame
        settings_frame = ctk.CTkFrame(tab)
        settings_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        settings_frame.grid_columnconfigure(1, weight=1)

        row = 0

        # Model Path
        ctk.CTkLabel(settings_frame, text="Model Path:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        model_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        model_frame.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        model_frame.grid_columnconfigure(0, weight=1)

        self.llm_model_path = ctk.CTkEntry(model_frame)
        self.llm_model_path.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        ctk.CTkButton(
            model_frame,
            text="Browse...",
            command=self._browse_llm_model,
            width=100
        ).grid(row=0, column=1)
        row += 1

        # CPU Threads
        ctk.CTkLabel(settings_frame, text="CPU Threads:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        thread_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        thread_frame.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        thread_frame.grid_columnconfigure(0, weight=1)

        self.llm_threads = ctk.CTkSlider(
            thread_frame,
            from_=1,
            to=16,
            number_of_steps=15,
            command=self._update_thread_label
        )
        self.llm_threads.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.llm_threads_label = ctk.CTkLabel(thread_frame, text="4", width=30)
        self.llm_threads_label.grid(row=0, column=1)
        row += 1

        # Context Length
        ctk.CTkLabel(settings_frame, text="Context Length:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        self.llm_context = ctk.CTkOptionMenu(
            settings_frame,
            values=["2048", "4096", "8192"]
        )
        self.llm_context.grid(row=row, column=1, padx=10, pady=5, sticky="w")
        row += 1

        # Temperature
        ctk.CTkLabel(settings_frame, text="Temperature:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        temp_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        temp_frame.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        temp_frame.grid_columnconfigure(0, weight=1)

        self.llm_temperature = ctk.CTkSlider(
            temp_frame,
            from_=0.0,
            to=1.0,
            number_of_steps=100,
            command=self._update_temp_label
        )
        self.llm_temperature.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.llm_temp_label = ctk.CTkLabel(temp_frame, text="0.30", width=40)
        self.llm_temp_label.grid(row=0, column=1)
        row += 1

        # Max Tokens
        ctk.CTkLabel(settings_frame, text="Max Tokens:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        self.llm_max_tokens = ctk.CTkEntry(settings_frame, width=150)
        self.llm_max_tokens.grid(row=row, column=1, padx=10, pady=5, sticky="w")
        row += 1

        # Enable LLM
        self.llm_enabled = ctk.CTkCheckBox(
            settings_frame,
            text="Enable LLM Features"
        )
        self.llm_enabled.grid(row=row, column=0, columnspan=2, padx=10, pady=5, sticky="w")

    def _create_build_tab(self):
        """Create build configuration tab."""
        tab = self.tabview.tab("Build")
        tab.grid_columnconfigure(0, weight=1)

        # Title
        ctk.CTkLabel(
            tab,
            text="🛠️ Build Configuration",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(10, 5), sticky="w")

        # Settings frame
        settings_frame = ctk.CTkFrame(tab)
        settings_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        settings_frame.grid_columnconfigure(1, weight=1)

        row = 0

        # CMake Path
        ctk.CTkLabel(settings_frame, text="CMake Path:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        cmake_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        cmake_frame.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        cmake_frame.grid_columnconfigure(0, weight=1)

        self.cmake_path = ctk.CTkEntry(cmake_frame, placeholder_text="Auto-detect")
        self.cmake_path.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        ctk.CTkButton(
            cmake_frame,
            text="Browse...",
            command=lambda: self._browse_file(self.cmake_path, "Select CMake"),
            width=100
        ).grid(row=0, column=1)
        row += 1

        # CMake Generator
        ctk.CTkLabel(settings_frame, text="CMake Generator:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        self.cmake_generator = ctk.CTkOptionMenu(
            settings_frame,
            values=["MinGW Makefiles", "Ninja", "Unix Makefiles"]
        )
        self.cmake_generator.grid(row=row, column=1, padx=10, pady=5, sticky="w")
        row += 1

        # Build Type
        ctk.CTkLabel(settings_frame, text="Default Build Type:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        self.build_type = ctk.CTkOptionMenu(
            settings_frame,
            values=["Debug", "Release", "RelWithDebInfo"]
        )
        self.build_type.grid(row=row, column=1, padx=10, pady=5, sticky="w")
        row += 1

        # SDK Directory
        ctk.CTkLabel(settings_frame, text="SDK Directory:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        sdk_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        sdk_frame.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        sdk_frame.grid_columnconfigure(0, weight=1)

        self.sdk_dir = ctk.CTkEntry(sdk_frame)
        self.sdk_dir.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        ctk.CTkButton(
            sdk_frame,
            text="Browse...",
            command=lambda: self._browse_directory(self.sdk_dir, "Select SDK Directory"),
            width=100
        ).grid(row=0, column=1)
        row += 1

        # Toolchain Directory
        ctk.CTkLabel(settings_frame, text="Toolchain Directory:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        toolchain_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        toolchain_frame.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        toolchain_frame.grid_columnconfigure(0, weight=1)

        self.toolchain_dir = ctk.CTkEntry(toolchain_frame)
        self.toolchain_dir.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        ctk.CTkButton(
            toolchain_frame,
            text="Browse...",
            command=lambda: self._browse_directory(self.toolchain_dir, "Select Toolchain Directory"),
            width=100
        ).grid(row=0, column=1)
        row += 1

        # ARM GCC Path
        ctk.CTkLabel(settings_frame, text="ARM GCC Path:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        armgcc_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        armgcc_frame.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        armgcc_frame.grid_columnconfigure(0, weight=1)

        self.armgcc_path = ctk.CTkEntry(armgcc_frame, placeholder_text="Auto-detect")
        self.armgcc_path.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        ctk.CTkButton(
            armgcc_frame,
            text="Browse...",
            command=lambda: self._browse_file(self.armgcc_path, "Select ARM GCC"),
            width=100
        ).grid(row=0, column=1)

    def _create_paths_tab(self):
        """Create file locations tab."""
        tab = self.tabview.tab("Paths")
        tab.grid_columnconfigure(0, weight=1)

        # Title
        ctk.CTkLabel(
            tab,
            text="📂 File Locations",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(10, 5), sticky="w")

        # Settings frame
        settings_frame = ctk.CTkFrame(tab)
        settings_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        settings_frame.grid_columnconfigure(1, weight=1)

        row = 0

        # Default Project Location
        ctk.CTkLabel(settings_frame, text="Default Project Location:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        project_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        project_frame.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        project_frame.grid_columnconfigure(0, weight=1)

        self.output_dir = ctk.CTkEntry(project_frame)
        self.output_dir.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        ctk.CTkButton(
            project_frame,
            text="Browse...",
            command=lambda: self._browse_directory(self.output_dir, "Select Project Directory"),
            width=100
        ).grid(row=0, column=1)
        row += 1

        # Models Directory
        ctk.CTkLabel(settings_frame, text="Models Directory:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        models_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        models_frame.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        models_frame.grid_columnconfigure(0, weight=1)

        self.models_dir = ctk.CTkEntry(models_frame)
        self.models_dir.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        ctk.CTkButton(
            models_frame,
            text="Browse...",
            command=lambda: self._browse_directory(self.models_dir, "Select Models Directory"),
            width=100
        ).grid(row=0, column=1)
        row += 1

        # Export Directory
        ctk.CTkLabel(settings_frame, text="Export Directory:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        export_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        export_frame.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        export_frame.grid_columnconfigure(0, weight=1)

        self.export_dir = ctk.CTkEntry(export_frame, placeholder_text="Same as project")
        self.export_dir.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        ctk.CTkButton(
            export_frame,
            text="Browse...",
            command=lambda: self._browse_directory(self.export_dir, "Select Export Directory"),
            width=100
        ).grid(row=0, column=1)
        row += 1

        # Datasets Directory
        ctk.CTkLabel(settings_frame, text="Datasets Directory:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        datasets_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        datasets_frame.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        datasets_frame.grid_columnconfigure(0, weight=1)

        self.datasets_dir = ctk.CTkEntry(datasets_frame, placeholder_text="No default")
        self.datasets_dir.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        ctk.CTkButton(
            datasets_frame,
            text="Browse...",
            command=lambda: self._browse_directory(self.datasets_dir, "Select Datasets Directory"),
            width=100
        ).grid(row=0, column=1)
        row += 1

        # Temporary Files
        ctk.CTkLabel(settings_frame, text="Temporary Files:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        temp_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        temp_frame.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        temp_frame.grid_columnconfigure(0, weight=1)

        self.temp_dir = ctk.CTkEntry(temp_frame, placeholder_text="System temp")
        self.temp_dir.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        ctk.CTkButton(
            temp_frame,
            text="Browse...",
            command=lambda: self._browse_directory(self.temp_dir, "Select Temp Directory"),
            width=100
        ).grid(row=0, column=1)

    def _create_performance_tab(self):
        """Create performance settings tab."""
        tab = self.tabview.tab("Performance")
        tab.grid_columnconfigure(0, weight=1)

        # Title
        ctk.CTkLabel(
            tab,
            text="🚀 Performance Settings",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(10, 5), sticky="w")

        # Settings frame
        settings_frame = ctk.CTkFrame(tab)
        settings_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        settings_frame.grid_columnconfigure(1, weight=1)

        row = 0

        # GPU Acceleration
        ctk.CTkLabel(settings_frame, text="GPU Acceleration:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        self.gpu_accel = ctk.CTkOptionMenu(
            settings_frame,
            values=["Auto-detect", "CUDA", "DirectML", "CPU only"]
        )
        self.gpu_accel.grid(row=row, column=1, padx=10, pady=5, sticky="w")
        row += 1

        # Max CPU Threads
        ctk.CTkLabel(settings_frame, text="Max CPU Threads:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        thread_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        thread_frame.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        thread_frame.grid_columnconfigure(0, weight=1)

        max_cpus = multiprocessing.cpu_count()
        self.max_threads = ctk.CTkSlider(
            thread_frame,
            from_=1,
            to=max_cpus,
            number_of_steps=max_cpus - 1,
            command=self._update_max_thread_label
        )
        self.max_threads.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.max_threads_label = ctk.CTkLabel(thread_frame, text=f"{max_cpus-1}", width=40)
        self.max_threads_label.grid(row=0, column=1)
        row += 1

        # RAM Limit
        ctk.CTkLabel(settings_frame, text="RAM Limit for Training:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        self.ram_limit = ctk.CTkOptionMenu(
            settings_frame,
            values=["Auto", "4 GB", "8 GB", "16 GB", "32 GB"]
        )
        self.ram_limit.grid(row=row, column=1, padx=10, pady=5, sticky="w")
        row += 1

        # Enable Parallel Processing
        self.parallel_processing = ctk.CTkCheckBox(
            settings_frame,
            text="Enable Parallel Processing"
        )
        self.parallel_processing.grid(row=row, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        row += 1

        # Cache Directory
        ctk.CTkLabel(settings_frame, text="Cache Directory:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        cache_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        cache_frame.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        cache_frame.grid_columnconfigure(0, weight=1)

        self.cache_dir = ctk.CTkEntry(cache_frame, placeholder_text="Default")
        self.cache_dir.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        ctk.CTkButton(
            cache_frame,
            text="Browse...",
            command=lambda: self._browse_directory(self.cache_dir, "Select Cache Directory"),
            width=100
        ).grid(row=0, column=1)

    def _create_logging_tab(self):
        """Create logging settings tab."""
        tab = self.tabview.tab("Logging")
        tab.grid_columnconfigure(0, weight=1)

        # Title
        ctk.CTkLabel(
            tab,
            text="📊 Logging Settings",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(10, 5), sticky="w")

        # Settings frame
        settings_frame = ctk.CTkFrame(tab)
        settings_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        settings_frame.grid_columnconfigure(1, weight=1)

        row = 0

        # Log Level
        ctk.CTkLabel(settings_frame, text="Log Level:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        self.log_level = ctk.CTkOptionMenu(
            settings_frame,
            values=["DEBUG", "INFO", "WARNING", "ERROR"]
        )
        self.log_level.grid(row=row, column=1, padx=10, pady=5, sticky="w")
        row += 1

        # Log to File
        self.log_to_file = ctk.CTkCheckBox(
            settings_frame,
            text="Log to File"
        )
        self.log_to_file.grid(row=row, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        row += 1

        # Log File Location
        ctk.CTkLabel(settings_frame, text="Log File Location:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        log_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        log_frame.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        log_frame.grid_columnconfigure(0, weight=1)

        self.log_location = ctk.CTkEntry(log_frame, placeholder_text="logs/")
        self.log_location.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        ctk.CTkButton(
            log_frame,
            text="Browse...",
            command=lambda: self._browse_directory(self.log_location, "Select Log Directory"),
            width=100
        ).grid(row=0, column=1)
        row += 1

        # Max Log Size
        ctk.CTkLabel(settings_frame, text="Max Log Size (MB):").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        self.max_log_size = ctk.CTkEntry(settings_frame, width=150)
        self.max_log_size.grid(row=row, column=1, padx=10, pady=5, sticky="w")
        row += 1

        # Clear Logs on Startup
        self.clear_logs = ctk.CTkCheckBox(
            settings_frame,
            text="Clear Logs on Startup"
        )
        self.clear_logs.grid(row=row, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        row += 1

        # Show Console (Windows only)
        if platform.system() == "Windows":
            self.show_console = ctk.CTkCheckBox(
                settings_frame,
                text="Show Console Window"
            )
            self.show_console.grid(row=row, column=0, columnspan=2, padx=10, pady=5, sticky="w")

    def _create_license_tab(self):
        """Create license activation tab."""
        tab = self.tabview.tab("License")
        tab.grid_columnconfigure(0, weight=1)

        # Title
        ctk.CTkLabel(
            tab,
            text="🔑 License Activation",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(10, 5), sticky="w")

        # Get license manager
        self.license_mgr = get_license_manager()

        # License Status Frame
        status_frame = ctk.CTkFrame(tab)
        status_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        status_frame.grid_columnconfigure(1, weight=1)

        # Current Status
        ctk.CTkLabel(
            status_frame,
            text="License Status:",
            font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")

        current_license = self.license_mgr.get_current_license()
        if current_license and current_license.is_valid:
            status_text = f"{current_license.tier.display_name} - Active"
            status_color = "green"
        else:
            status_text = "Not Activated (FREE Tier)"
            status_color = "orange"

        self.license_status_label = ctk.CTkLabel(
            status_frame,
            text=status_text,
            text_color=status_color,
            font=ctk.CTkFont(weight="bold")
        )
        self.license_status_label.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        # License Details
        if current_license:
            row = 1

            # Licensed To
            if current_license.licensed_to:
                ctk.CTkLabel(status_frame, text="Licensed To:").grid(
                    row=row, column=0, padx=10, pady=5, sticky="w"
                )
                ctk.CTkLabel(status_frame, text=current_license.licensed_to).grid(
                    row=row, column=1, padx=10, pady=5, sticky="w"
                )
                row += 1

            # Organization
            if current_license.organization:
                ctk.CTkLabel(status_frame, text="Organization:").grid(
                    row=row, column=0, padx=10, pady=5, sticky="w"
                )
                ctk.CTkLabel(status_frame, text=current_license.organization).grid(
                    row=row, column=1, padx=10, pady=5, sticky="w"
                )
                row += 1

            # Expiry
            if current_license.expiry_date:
                ctk.CTkLabel(status_frame, text="Expires:").grid(
                    row=row, column=0, padx=10, pady=5, sticky="w"
                )
                expiry_text = current_license.expiry_date.strftime("%Y-%m-%d")
                ctk.CTkLabel(status_frame, text=expiry_text).grid(
                    row=row, column=1, padx=10, pady=5, sticky="w"
                )
                row += 1
            else:
                ctk.CTkLabel(status_frame, text="Expires:").grid(
                    row=row, column=0, padx=10, pady=5, sticky="w"
                )
                ctk.CTkLabel(status_frame, text="Lifetime").grid(
                    row=row, column=1, padx=10, pady=5, sticky="w"
                )
                row += 1

            # Hardware ID
            ctk.CTkLabel(status_frame, text="Hardware ID:").grid(
                row=row, column=0, padx=10, pady=5, sticky="w"
            )
            hw_id = current_license.hardware_id[:19] if current_license.hardware_id else "N/A"
            ctk.CTkLabel(status_frame, text=hw_id).grid(
                row=row, column=1, padx=10, pady=5, sticky="w"
            )

        # Activation Frame
        activation_frame = ctk.CTkFrame(tab)
        activation_frame.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        activation_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            activation_frame,
            text="Activate New License",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")

        # License Key
        ctk.CTkLabel(activation_frame, text="License Key:").grid(
            row=1, column=0, padx=10, pady=5, sticky="w"
        )
        self.license_key = ctk.CTkEntry(
            activation_frame,
            placeholder_text="XXXX-XXXX-XXXX-XXXX-XXXX"
        )
        self.license_key.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # Licensed To
        ctk.CTkLabel(activation_frame, text="Name:").grid(
            row=2, column=0, padx=10, pady=5, sticky="w"
        )
        self.license_name = ctk.CTkEntry(activation_frame, placeholder_text="Your Name")
        self.license_name.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        # Organization
        ctk.CTkLabel(activation_frame, text="Organization:").grid(
            row=3, column=0, padx=10, pady=5, sticky="w"
        )
        self.license_org = ctk.CTkEntry(
            activation_frame,
            placeholder_text="Company Name (optional)"
        )
        self.license_org.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        # Email
        ctk.CTkLabel(activation_frame, text="Email:").grid(
            row=4, column=0, padx=10, pady=5, sticky="w"
        )
        self.license_email = ctk.CTkEntry(
            activation_frame,
            placeholder_text="email@example.com (optional)"
        )
        self.license_email.grid(row=4, column=1, padx=10, pady=5, sticky="ew")

        # Activate Button
        self.activate_btn = ctk.CTkButton(
            activation_frame,
            text="Activate License",
            command=self._activate_license,
            fg_color="green",
            hover_color="darkgreen"
        )
        self.activate_btn.grid(row=5, column=0, columnspan=2, padx=10, pady=(10, 5))

        # Features Frame
        features_frame = ctk.CTkFrame(tab)
        features_frame.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        features_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            features_frame,
            text="Available Features",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        # Feature list
        license = self.license_mgr.get_current_license()
        if license:
            tier = license.tier
        else:
            from core.license import TIER_FREE
            tier = TIER_FREE

        features_text = f"""
ML Algorithms:        {'[YES]' if tier.ml_algorithms else '[NO]'}
Deep Learning:        {'[YES]' if tier.deep_learning else '[NO]'}
ONNX Export:          {'[YES]' if tier.onnx_export else '[NO]'}
LLM Features:         {'[YES]' if tier.llm_features else '[NO]'}
Multi-User:           {'[YES]' if tier.multi_user else '[NO]'}
API Access:           {'[YES]' if tier.api_access else '[NO]'}

Max Projects:         {'Unlimited' if tier.max_projects == -1 else tier.max_projects}
Max Samples:          {'Unlimited' if tier.max_samples == -1 else tier.max_samples}
        """

        ctk.CTkLabel(
            features_frame,
            text=features_text,
            justify="left",
            font=ctk.CTkFont(family="Consolas", size=11)
        ).grid(row=1, column=0, padx=10, pady=5, sticky="w")

        # Hardware ID Display
        hw_frame = ctk.CTkFrame(tab)
        hw_frame.grid(row=4, column=0, padx=20, pady=5, sticky="ew")
        hw_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            hw_frame,
            text="Your Hardware ID:",
            font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")

        hw_id = self.license_mgr.generate_hardware_id()
        self.hw_id_label = ctk.CTkLabel(
            hw_frame,
            text=hw_id,
            font=ctk.CTkFont(family="Consolas")
        )
        self.hw_id_label.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkButton(
            hw_frame,
            text="Copy",
            command=lambda: self._copy_to_clipboard(hw_id),
            width=80
        ).grid(row=0, column=2, padx=10, pady=5)

    def _activate_license(self):
        """Activate license with provided key."""
        key = self.license_key.get().strip()
        name = self.license_name.get().strip()
        org = self.license_org.get().strip()
        email = self.license_email.get().strip()

        if not key:
            messagebox.showerror("Error", "Please enter a license key.")
            return

        if not name:
            messagebox.showerror("Error", "Please enter your name.")
            return

        # Activate
        success, error = self.license_mgr.activate_license(
            key=key,
            licensed_to=name,
            organization=org,
            email=email
        )

        if success:
            messagebox.showinfo(
                "Success",
                "License activated successfully!\n\nPlease restart the application for changes to take effect."
            )
            logger.info(f"License activated: {key}")

            # Refresh the tab
            self.destroy()
        else:
            messagebox.showerror("Activation Failed", f"Failed to activate license:\n\n{error}")
            logger.error(f"License activation failed: {error}")

    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard."""
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Copied", "Hardware ID copied to clipboard!")

    def _load_settings(self):
        """Load current settings from config."""
        # LLM settings
        self.llm_model_path.insert(0, self.config.llm_model_name)
        self.llm_threads.set(self.config.llm_threads)
        self._update_thread_label(self.config.llm_threads)
        self.llm_context.set(str(self.config.llm_context_length))
        self.llm_temperature.set(self.config.llm_temperature)
        self._update_temp_label(self.config.llm_temperature)
        self.llm_max_tokens.insert(0, str(self.config.llm_max_tokens))
        self.llm_enabled.select()  # Default enabled

        # Build settings
        self.cmake_generator.set(self.config.cmake_generator)
        self.build_type.set(self.config.build_type)
        self.sdk_dir.insert(0, str(self.config.sdk_dir))
        self.toolchain_dir.insert(0, str(self.config.toolchain_dir))

        # Paths
        self.output_dir.insert(0, str(self.config.output_dir))
        self.models_dir.insert(0, str(self.config.models_dir))

        # Performance
        self.gpu_accel.set("Auto-detect")
        max_cpus = multiprocessing.cpu_count()
        self.max_threads.set(max_cpus - 1)
        self._update_max_thread_label(max_cpus - 1)
        self.ram_limit.set("Auto")
        self.parallel_processing.select()

        # Logging
        self.log_level.set(self.config.log_level)
        self.log_to_file.select()
        self.max_log_size.insert(0, "50")

    def _save(self):
        """Save settings."""
        try:
            # Update config
            self.config.llm_model_name = self.llm_model_path.get()
            self.config.llm_threads = int(self.llm_threads.get())
            self.config.llm_context_length = int(self.llm_context.get())
            self.config.llm_temperature = self.llm_temperature.get()
            self.config.llm_max_tokens = int(self.llm_max_tokens.get())

            self.config.cmake_generator = self.cmake_generator.get()
            self.config.build_type = self.build_type.get()
            self.config.sdk_dir = Path(self.sdk_dir.get())
            self.config.toolchain_dir = Path(self.toolchain_dir.get())

            self.config.output_dir = Path(self.output_dir.get())
            self.config.models_dir = Path(self.models_dir.get())

            self.config.log_level = self.log_level.get()

            # Save to file
            self.config.save()

            logger.info("Settings saved successfully")
            messagebox.showinfo("Settings Saved", "Settings have been saved successfully.")

            self.modified = True
            self.destroy()

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            messagebox.showerror("Error", f"Failed to save settings:\n{e}")

    def _cancel(self):
        """Cancel and close."""
        self.destroy()

    def _restore_defaults(self):
        """Restore default settings."""
        if messagebox.askyesno("Restore Defaults", "Are you sure you want to restore default settings?"):
            self.config = Config()  # Create new config with defaults
            self._load_settings()
            messagebox.showinfo("Defaults Restored", "Default settings have been restored.")

    def _browse_llm_model(self):
        """Browse for LLM model file."""
        filename = filedialog.askopenfilename(
            title="Select LLM Model",
            filetypes=[("GGUF files", "*.gguf"), ("All files", "*.*")]
        )
        if filename:
            self.llm_model_path.delete(0, "end")
            self.llm_model_path.insert(0, filename)

    def _browse_file(self, entry_widget, title):
        """Browse for a file."""
        filename = filedialog.askopenfilename(title=title)
        if filename:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, filename)

    def _browse_directory(self, entry_widget, title):
        """Browse for a directory."""
        dirname = filedialog.askdirectory(title=title)
        if dirname:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, dirname)

    def _update_thread_label(self, value):
        """Update thread count label."""
        self.llm_threads_label.configure(text=str(int(value)))

    def _update_temp_label(self, value):
        """Update temperature label."""
        self.llm_temp_label.configure(text=f"{float(value):.2f}")

    def _update_max_thread_label(self, value):
        """Update max thread count label."""
        self.max_threads_label.configure(text=str(int(value)))

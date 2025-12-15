"""
Main Application Window

The main CustomTkinter window that hosts all UI components.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Optional
from loguru import logger

from core.config import Config
from core.project import ProjectManager, Project
from core.license_manager import get_license_manager
from ui.theme import ThemeManager
from ui.navigation import NavigationSidebar
from ui.data_panel import DataSourcesPanel
from ui.features_panel import FeaturesPanel
from ui.filtering_panel import FilteringPanel
from ui.llm_panel import LLMPanel
from ui.model_panel import ModelPanel
from ui.dsp_panel import DSPPanel
from ui.build_panel import BuildPanel


class CiRAStudioApp:
    """Main application class."""

    def __init__(self, config: Config):
        """
        Initialize application.

        Args:
            config: Application configuration
        """
        self.config = config
        self.project_manager = ProjectManager()
        self.theme_manager = ThemeManager(config.theme, config.color_theme)

        # Initialize state first
        self.current_panel: Optional[ctk.CTkFrame] = None

        # Create main window
        self.root = ctk.CTk()
        self.root.title(config.app_name)
        self.root.geometry(f"{config.window_width}x{config.window_height}")

        # Center window on screen
        self._center_window()

        # Setup UI
        self._setup_ui()
        self._setup_menu()
        self._setup_keybindings()

        logger.info("Main window initialized")

    def _center_window(self) -> None:
        """Center window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _setup_ui(self) -> None:
        """Setup main UI layout."""
        # Configure grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # Navigation sidebar
        self.sidebar = NavigationSidebar(
            self.root,
            on_stage_change=self._on_stage_change,
            config=self.config
        )
        self.sidebar.grid(row=0, column=0, sticky="nsw")

        # Main content area
        self.content_frame = ctk.CTkFrame(self.root, corner_radius=0)
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.content_frame.grid_rowconfigure(1, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Top bar
        self._setup_top_bar()

        # Status bar
        self._setup_status_bar()

        # Show welcome screen initially
        self._show_welcome_screen()

    def _setup_top_bar(self) -> None:
        """Setup top bar with project info and controls."""
        self.top_bar = ctk.CTkFrame(self.content_frame, height=60, corner_radius=0)
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.top_bar.grid_columnconfigure(1, weight=1)

        # Project info
        self.project_label = ctk.CTkLabel(
            self.top_bar,
            text="No project open",
            font=("Segoe UI", 16, "bold"),
            anchor="w"
        )
        self.project_label.grid(row=0, column=0, padx=20, pady=15, sticky="w")

        # File menu buttons
        file_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        file_frame.grid(row=0, column=1, padx=10, pady=15, sticky="e")

        ctk.CTkButton(
            file_frame,
            text="📝 New",
            command=self._new_project,
            width=80,
            height=35
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            file_frame,
            text="📂 Open",
            command=self._open_project,
            width=80,
            height=35
        ).pack(side="left", padx=2)

        self.save_btn = ctk.CTkButton(
            file_frame,
            text="💾 Save",
            command=self._save_project,
            width=80,
            height=35,
            state="disabled"
        )
        self.save_btn.pack(side="left", padx=2)

        self.close_btn = ctk.CTkButton(
            file_frame,
            text="✖ Close",
            command=self._close_project,
            width=80,
            height=35,
            state="disabled"
        )
        self.close_btn.pack(side="left", padx=2)

        # Theme toggle button
        self.theme_btn = ctk.CTkButton(
            self.top_bar,
            text="🌙 Dark" if self.theme_manager.theme == "dark" else "☀️ Light",
            command=self._toggle_theme,
            width=100,
            height=35
        )
        self.theme_btn.grid(row=0, column=2, padx=10, pady=15)

        # Color theme selector
        self.color_theme_var = ctk.StringVar(value=self.theme_manager.color_theme.capitalize())
        self.color_theme_menu = ctk.CTkOptionMenu(
            self.top_bar,
            variable=self.color_theme_var,
            values=["Blue", "Green", "Dark-Blue", "Rime", "Sky", "Yellow", "Marsh"],
            command=self._change_color_theme,
            width=120,
            height=35
        )
        self.color_theme_menu.grid(row=0, column=3, padx=10, pady=15)

    def _setup_status_bar(self) -> None:
        """Setup status bar at bottom."""
        self.status_bar = ctk.CTkFrame(self.content_frame, height=30, corner_radius=0)
        self.status_bar.grid(row=2, column=0, sticky="ew")

        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Ready",
            font=("Segoe UI", 10),
            anchor="w"
        )
        self.status_label.pack(side="left", padx=10, pady=5)

        # License status
        license_mgr = get_license_manager()
        current_license = license_mgr.get_current_license()

        if current_license and current_license.is_valid:
            license_text = f"🔑 {current_license.tier.name}"
            license_color = "green"
        else:
            license_text = "🔑 FREE"
            license_color = "orange"

        self.license_label = ctk.CTkLabel(
            self.status_bar,
            text=license_text,
            font=("Segoe UI", 10, "bold"),
            text_color=license_color
        )
        self.license_label.pack(side="right", padx=10, pady=5)

    def _setup_menu(self) -> None:
        """Setup application menu."""
        # Note: CustomTkinter doesn't have native menu support
        # We'll use buttons in the top bar instead
        pass

    def _setup_keybindings(self) -> None:
        """Setup keyboard shortcuts."""
        self.root.bind("<Control-n>", lambda e: self._new_project())
        self.root.bind("<Control-o>", lambda e: self._open_project())
        self.root.bind("<Control-s>", lambda e: self._save_project())
        self.root.bind("<Control-w>", lambda e: self._close_project())
        self.root.bind("<Control-q>", lambda e: self._quit_app())
        self.root.bind("<F11>", lambda e: self.root.attributes("-fullscreen", True))
        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False))

    def _show_welcome_screen(self) -> None:
        """Show welcome screen when no project is open."""
        self._clear_content()

        welcome_frame = ctk.CTkFrame(self.content_frame)
        welcome_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        welcome_frame.grid_rowconfigure(0, weight=1)
        welcome_frame.grid_columnconfigure(0, weight=1)

        # Center content
        center_frame = ctk.CTkFrame(welcome_frame, fg_color="transparent")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Logo
        logo_label = ctk.CTkLabel(
            center_frame,
            text="⚡",
            font=("Segoe UI", 80)
        )
        logo_label.pack(pady=(0, 20))

        # Title
        title_label = ctk.CTkLabel(
            center_frame,
            text="CiRA FutureEdge Studio",
            font=("Segoe UI", 32, "bold")
        )
        title_label.pack(pady=(0, 10))

        # Subtitle
        subtitle_label = ctk.CTkLabel(
            center_frame,
            text="100% Offline Anomaly Detection for Embedded Devices",
            font=("Segoe UI", 14),
            text_color=("gray50", "gray")
        )
        subtitle_label.pack(pady=(0, 40))

        # Action buttons
        btn_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        btn_frame.pack()

        new_btn = ctk.CTkButton(
            btn_frame,
            text="📝 New Project",
            command=self._new_project,
            width=180,
            height=45,
            font=("Segoe UI", 14)
        )
        new_btn.pack(side="left", padx=10)

        open_btn = ctk.CTkButton(
            btn_frame,
            text="📂 Open Project",
            command=self._open_project,
            width=180,
            height=45,
            font=("Segoe UI", 14),
            fg_color="transparent",
            border_width=2,
            border_color=("gray40", "gray60"),
            text_color=("gray10", "gray90"),
            hover_color=("gray85", "gray25")
        )
        open_btn.pack(side="left", padx=10)

        self.current_panel = welcome_frame

    def _clear_content(self) -> None:
        """Clear current content panel."""
        if self.current_panel is not None:
            self.current_panel.destroy()
            self.current_panel = None

    def _on_stage_change(self, stage_id: str) -> None:
        """
        Handle stage change from navigation.

        Args:
            stage_id: New stage identifier
        """
        if not self.project_manager.has_project():
            messagebox.showwarning(
                "No Project",
                "Please create or open a project first."
            )
            return

        # Check if trying to access grayed-out stage in DL mode
        project = self.project_manager.current_project
        pipeline_mode = getattr(project.data, 'pipeline_mode', 'ml')
        if pipeline_mode == "dl" and stage_id in ["features", "filtering", "llm"]:
            messagebox.showinfo(
                "Deep Learning Mode",
                f"{self.sidebar.get_stage_name(stage_id)} is not needed for Deep Learning.\n\n"
                "TimesNet learns features automatically from raw time series data.\n\n"
                "Switch to Traditional ML mode to use feature extraction."
            )
            return

        logger.info(f"Switching to stage: {stage_id}")
        self.set_status(f"Loading {self.sidebar.get_stage_name(stage_id)}...")

        # Load appropriate panel for stage
        if stage_id == "data":
            self._show_data_panel()
        elif stage_id == "features":
            self._show_features_panel()
        elif stage_id == "filtering":
            self._show_filtering_panel()
        elif stage_id == "llm":
            self._show_llm_panel()
        elif stage_id == "model":
            self._show_model_panel()
        elif stage_id == "dsp":
            self._show_dsp_panel()
        elif stage_id == "build":
            self._show_build_panel()
        else:
            self._show_placeholder_panel(stage_id)

        self.set_status("Ready")

    def _show_placeholder_panel(self, stage_id: str) -> None:
        """Show placeholder panel for stage (temporary)."""
        self._clear_content()

        panel = ctk.CTkFrame(self.content_frame)
        panel.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)

        label = ctk.CTkLabel(
            panel,
            text=f"🚧 {self.sidebar.get_stage_name(stage_id)} Panel\n\nUnder Construction",
            font=("Segoe UI", 24),
            text_color="gray"
        )
        label.place(relx=0.5, rely=0.5, anchor="center")

        self.current_panel = panel

    def _show_data_panel(self) -> None:
        """Show data sources panel."""
        self._clear_content()

        panel = DataSourcesPanel(self.content_frame, self.project_manager)
        panel.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)

        self.current_panel = panel
        logger.info("Data sources panel loaded")

    def _show_features_panel(self) -> None:
        """Show feature extraction panel."""
        self._clear_content()

        panel = FeaturesPanel(self.content_frame, self.project_manager)
        panel.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        panel.refresh()  # Refresh with current project data

        self.current_panel = panel
        logger.info("Feature extraction panel loaded")

    def _show_filtering_panel(self) -> None:
        """Show feature filtering panel."""
        self._clear_content()

        panel = FilteringPanel(self.content_frame, self.project_manager)
        panel.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        panel.refresh()  # Refresh with current project data

        self.current_panel = panel
        logger.info("Feature filtering panel loaded")

    def _show_llm_panel(self) -> None:
        """Show LLM feature selection panel."""
        self._clear_content()

        panel = LLMPanel(self.content_frame, self.project_manager)
        panel.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        panel.refresh()  # Refresh with current project data

        self.current_panel = panel
        logger.info("LLM feature selection panel loaded")

    def _show_model_panel(self) -> None:
        """Show anomaly model training panel."""
        self._clear_content()

        panel = ModelPanel(self.content_frame, self.project_manager)
        panel.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        panel.refresh()  # Refresh with current project data

        self.current_panel = panel
        logger.info("Anomaly model training panel loaded")

    def _show_dsp_panel(self) -> None:
        """Show DSP code generation panel."""
        self._clear_content()

        panel = DSPPanel(self.content_frame, self.project_manager)
        panel.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        panel.refresh()  # Refresh with current project data

        self.current_panel = panel
        logger.info("DSP code generation panel loaded")

    def _show_build_panel(self) -> None:
        """Show firmware build panel."""
        self._clear_content()

        panel = BuildPanel(self.content_frame, self.project_manager)
        panel.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        panel.refresh()  # Refresh with current project data

        self.current_panel = panel
        logger.info("Firmware build panel loaded")

    def _new_project(self) -> None:
        """Create new project."""
        dialog = NewProjectDialog(self.root, self.config)
        self.root.wait_window(dialog)  # Wait for dialog to close
        if dialog.result:
            name, domain, workspace = dialog.result
            try:
                project = self.project_manager.new_project(name, domain, Path(workspace))
                project.save()
                self._update_project_ui()
                self.set_status(f"Created project: {name}")
                logger.info(f"New project created: {name}")

                # Update navigation for default pipeline mode (ml)
                pipeline_mode = getattr(project.data, 'pipeline_mode', 'ml')
                self.update_navigation_for_pipeline_mode(pipeline_mode)

                # Switch to data stage
                self.sidebar.set_active_stage("data")
                self._on_stage_change("data")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to create project:\n{e}")
                logger.error(f"Failed to create project: {e}")

    def _open_project(self) -> None:
        """Open existing project."""
        filename = filedialog.askopenfilename(
            title="Open Project",
            filetypes=[("CiRA Project", "*.ciraproject"), ("All Files", "*.*")]
        )

        if filename:
            try:
                project = self.project_manager.open_project(Path(filename))
                self._update_project_ui()
                self.set_status(f"Opened project: {project.name}")
                logger.info(f"Project opened: {filename}")

                # Update navigation for project's pipeline mode
                pipeline_mode = getattr(project.data, 'pipeline_mode', 'ml')
                self.update_navigation_for_pipeline_mode(pipeline_mode)

                # Switch to current stage
                self.sidebar.set_active_stage(project.current_stage)
                self._on_stage_change(project.current_stage)

            except Exception as e:
                messagebox.showerror("Error", f"Failed to open project:\n{e}")
                logger.error(f"Failed to open project: {e}")

    def _save_project(self) -> None:
        """Save current project."""
        if not self.project_manager.has_project():
            messagebox.showwarning("No Project", "No project is open.")
            return

        try:
            self.project_manager.save_project()
            self.set_status("Project saved")
            logger.info("Project saved")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save project:\n{e}")
            logger.error(f"Failed to save project: {e}")

    def _close_project(self) -> None:
        """Close current project."""
        if not self.project_manager.has_project():
            return

        # Ask to save if modified
        # TODO: Track project modifications

        self.project_manager.close_project()
        self._update_project_ui()
        self._show_welcome_screen()
        self.set_status("Project closed")
        logger.info("Project closed")

    def _quit_app(self) -> None:
        """Quit application."""
        if self.project_manager.has_project():
            if messagebox.askyesno("Quit", "Close project and quit?"):
                self.root.quit()
        else:
            self.root.quit()

    def _toggle_theme(self) -> None:
        """Toggle dark/light theme."""
        new_theme = self.theme_manager.toggle_theme()
        self.theme_btn.configure(
            text="🌙 Dark" if new_theme == "dark" else "☀️ Light"
        )
        logger.info(f"Theme toggled to: {new_theme}")

    def _change_color_theme(self, theme_name: str) -> None:
        """
        Change color theme.

        Args:
            theme_name: Selected theme name (capitalized)
        """
        # Convert to lowercase for theme manager
        theme_lower = theme_name.lower()

        # Notify user that app needs restart for theme changes
        from tkinter import messagebox
        if messagebox.askokcancel(
            "Theme Change",
            f"Changing to '{theme_name}' theme.\n\nThe app needs to restart for the new theme to fully apply.\n\nRestart now?"
        ):
            self.theme_manager.set_color_theme(theme_lower)

            # Save theme preference to config
            from core.config import Config
            config = Config.load()
            config.theme = self.theme_manager.theme
            config.color_theme = theme_lower
            config.save()

            # Restart app
            self.root.quit()
            import subprocess
            import sys
            subprocess.Popen([sys.executable, "main.py"], cwd=str(Path(__file__).parent.parent))
        else:
            # Reset dropdown to current theme
            self.color_theme_var.set(self.theme_manager.color_theme.capitalize())

    def _update_project_ui(self) -> None:
        """Update UI to reflect current project state."""
        project = self.project_manager.get_project()
        if project:
            self.project_label.configure(text=f"📁 {project.name}")

            # Enable Save and Close buttons
            self.save_btn.configure(state="normal")
            self.close_btn.configure(state="normal")

            # Mark completed stages
            for stage in project.completed_stages:
                self.sidebar.mark_stage_completed(stage)
        else:
            self.project_label.configure(text="No project open")

            # Disable Save and Close buttons
            self.save_btn.configure(state="disabled")
            self.close_btn.configure(state="disabled")

    def set_status(self, message: str) -> None:
        """
        Update status bar message.

        Args:
            message: Status message
        """
        self.status_label.configure(text=message)
        self.root.update_idletasks()

    def update_navigation_for_pipeline_mode(self, pipeline_mode: str) -> None:
        """
        Update navigation sidebar based on pipeline mode.

        Args:
            pipeline_mode: "ml" or "dl"
        """
        self.sidebar.update_for_pipeline_mode(pipeline_mode)
        logger.info(f"Navigation updated for pipeline mode: {pipeline_mode}")

    def run(self) -> None:
        """Start application main loop."""
        logger.info("Starting application main loop")
        self.root.mainloop()


class NewProjectDialog(ctk.CTkToplevel):
    """Dialog for creating new project."""

    def __init__(self, parent, config: Config):
        super().__init__(parent)

        self.config = config
        self.result = None

        self.title("New Project")
        self.geometry("500x400")
        self.resizable(False, False)

        # Make modal
        self.transient(parent)
        self.grab_set()

        self._setup_ui()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _setup_ui(self) -> None:
        """Setup dialog UI."""
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Create New Project",
            font=("Segoe UI", 20, "bold")
        )
        title_label.pack(pady=(0, 20))

        # Project name
        name_label = ctk.CTkLabel(main_frame, text="Project Name:", anchor="w")
        name_label.pack(fill="x", pady=(10, 5))

        self.name_entry = ctk.CTkEntry(main_frame, placeholder_text="My Anomaly Detector")
        self.name_entry.pack(fill="x", pady=(0, 10))

        # Domain selection
        domain_label = ctk.CTkLabel(main_frame, text="Domain:", anchor="w")
        domain_label.pack(fill="x", pady=(10, 5))

        self.domain_var = ctk.StringVar(value="rotating_machinery")
        domains = [
            "rotating_machinery",
            "thermal_systems",
            "electrical",
            "custom"
        ]

        self.domain_menu = ctk.CTkOptionMenu(
            main_frame,
            variable=self.domain_var,
            values=domains
        )
        self.domain_menu.pack(fill="x", pady=(0, 10))

        # Workspace directory
        workspace_label = ctk.CTkLabel(main_frame, text="Workspace Directory:", anchor="w")
        workspace_label.pack(fill="x", pady=(10, 5))

        workspace_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        workspace_frame.pack(fill="x", pady=(0, 10))

        self.workspace_entry = ctk.CTkEntry(
            workspace_frame,
            placeholder_text=str(self.config.output_dir)
        )
        self.workspace_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.workspace_entry.insert(0, str(self.config.output_dir))

        browse_btn = ctk.CTkButton(
            workspace_frame,
            text="Browse...",
            command=self._browse_workspace,
            width=100
        )
        browse_btn.pack(side="right")

        # Buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", pady=(20, 0))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self._cancel,
            fg_color="transparent",
            border_width=2,
            width=120
        )
        cancel_btn.pack(side="right", padx=(10, 0))

        create_btn = ctk.CTkButton(
            btn_frame,
            text="Create",
            command=self._create,
            width=120
        )
        create_btn.pack(side="right")

    def _browse_workspace(self) -> None:
        """Browse for workspace directory."""
        directory = filedialog.askdirectory(title="Select Workspace Directory")
        if directory:
            self.workspace_entry.delete(0, "end")
            self.workspace_entry.insert(0, directory)

    def _create(self) -> None:
        """Create project."""
        name = self.name_entry.get().strip()
        domain = self.domain_var.get()
        workspace = self.workspace_entry.get().strip()

        if not name:
            messagebox.showwarning("Invalid Input", "Please enter a project name.")
            return

        if not workspace or not Path(workspace).exists():
            messagebox.showwarning("Invalid Input", "Please select a valid workspace directory.")
            return

        self.result = (name, domain, workspace)
        self.destroy()

    def _cancel(self) -> None:
        """Cancel dialog."""
        self.result = None
        self.destroy()

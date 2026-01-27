"""
Navigation Sidebar

Provides left sidebar navigation for the application workflow.
"""

import customtkinter as ctk
from typing import Callable, List, Dict, Any, Optional
from loguru import logger

from core.config import Config


class NavigationButton(ctk.CTkButton):
    """Custom navigation button with active/inactive states."""

    def __init__(self, master, text: str, icon: str, command: Callable, **kwargs):
        """
        Initialize navigation button.

        Args:
            master: Parent widget
            text: Button text
            icon: Unicode icon/emoji
            command: Click callback
        """
        self.icon = icon
        self.button_text = text
        self.is_active = False

        super().__init__(
            master,
            text=f"{icon}  {text}",
            command=command,
            anchor="w",
            height=45,
            corner_radius=8,
            font=("Segoe UI", 13),
            text_color=("gray10", "gray90"),
            hover_color=("gray85", "gray30"),
            **kwargs
        )

    def set_active(self, active: bool) -> None:
        """Set button active state."""
        # CRITICAL: Don't change appearance if button is grayed out
        if hasattr(self, '_grayed_out') and self._grayed_out:
            logger.warning(f"⛔ Blocked set_active on grayed button: {self.button_text}")
            return

        self.is_active = active
        if active:
            # Light theme (first value) and dark theme (second value)
            self.configure(fg_color=("#2b76c2", "#1f538d"))
        else:
            self.configure(fg_color="transparent")

    def configure(self, **kwargs):
        """Override configure to protect grayed state."""
        # If grayed out, don't allow fg_color changes (except from gray_out_stage)
        if hasattr(self, '_grayed_out') and self._grayed_out:
            # Only allow graying/ungraying from gray_out_stage
            if 'fg_color' in kwargs:
                # Check if this is coming from gray_out_stage (dim red colors)
                fg = kwargs.get('fg_color', '')
                if fg not in [("#8B4545", "#5C3030"), "transparent"]:
                    logger.warning(f"⛔ BLOCKED fg_color change on grayed button: {self.button_text}, attempted color: {fg}")
                    kwargs.pop('fg_color')  # Remove the color change

        super().configure(**kwargs)


class NavigationSidebar(ctk.CTkFrame):
    """Navigation sidebar with stage buttons."""

    # Application stages
    STAGES = [
        {"id": "data", "name": "Data Sources", "icon": "📊"},
        {"id": "features", "name": "Feature Extraction", "icon": "🔬"},
        {"id": "filtering", "name": "Feature Filtering", "icon": "🔍"},
        {"id": "llm", "name": "LLM Selection", "icon": "🤖"},
        {"id": "model", "name": "Training", "icon": "🎯"},
        {"id": "dsp", "name": "Embedded Code Generation", "icon": "⚙️"},
        {"id": "build", "name": "Build Firmware", "icon": "🚀"},
    ]

    def __init__(self, master, on_stage_change: Callable[[str], None], config: Config, **kwargs):
        """
        Initialize navigation sidebar.

        Args:
            master: Parent widget
            on_stage_change: Callback when stage changes (receives stage_id)
            config: Application configuration
        """
        super().__init__(master, width=220, corner_radius=0, **kwargs)

        self.on_stage_change = on_stage_change
        self.config = config
        self.current_stage: Optional[str] = None
        self.buttons: Dict[str, NavigationButton] = {}

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup UI components."""
        # Logo/Title section
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(pady=20, padx=20, fill="x")

        logo_label = ctk.CTkLabel(
            title_frame,
            text="⚡",
            font=("Segoe UI", 32)
        )
        logo_label.pack()

        title_label = ctk.CTkLabel(
            title_frame,
            text="CiRA Studio",
            font=("Segoe UI", 18, "bold")
        )
        title_label.pack(pady=(5, 0))

        version_label = ctk.CTkLabel(
            title_frame,
            text="v1.0.0",
            font=("Segoe UI", 10),
            text_color=("gray50", "gray")
        )
        version_label.pack()

        # Separator (light theme color, dark theme color)
        separator = ctk.CTkFrame(self, height=2, fg_color=("gray70", "gray30"))
        separator.pack(fill="x", padx=20, pady=10)

        # Navigation buttons
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="both", expand=True, padx=15, pady=10)

        for stage in self.STAGES:
            btn = NavigationButton(
                nav_frame,
                text=stage["name"],
                icon=stage["icon"],
                command=lambda s=stage["id"]: self._on_button_click(s)
            )
            btn.pack(pady=5, fill="x")
            btn._grayed_out = False  # Initialize grayed state
            self.buttons[stage["id"]] = btn

        # Settings button at bottom
        settings_frame = ctk.CTkFrame(self, fg_color="transparent")
        settings_frame.pack(side="bottom", fill="x", padx=15, pady=15)

        settings_btn = ctk.CTkButton(
            settings_frame,
            text="⚙️  Settings",
            command=self._on_settings_click,
            anchor="w",
            height=40,
            corner_radius=8,
            font=("Segoe UI", 12),
            fg_color="transparent",
            hover_color=("gray80", "gray30"),
            text_color=("gray10", "gray90")
        )
        settings_btn.pack(fill="x")

    def _on_button_click(self, stage_id: str) -> None:
        """Handle navigation button click."""
        logger.info(f"Navigation: Switching to stage '{stage_id}'")
        self.set_active_stage(stage_id)
        self.on_stage_change(stage_id)

    def _on_settings_click(self) -> None:
        """Handle settings button click."""
        logger.info("Navigation: Opening settings")
        from ui.settings_dialog import SettingsDialog

        dialog = SettingsDialog(self.master, self.config)
        dialog.wait_window()  # Wait for dialog to close

        # Check if settings were modified
        if dialog.modified:
            logger.info("Settings were modified, config reloaded")
            # Config is already updated in the dialog

    def set_active_stage(self, stage_id: str) -> None:
        """
        Set active navigation stage.

        Args:
            stage_id: Stage identifier
        """
        # Don't activate grayed out stages
        if stage_id in self.buttons:
            if hasattr(self.buttons[stage_id], '_grayed_out') and self.buttons[stage_id]._grayed_out:
                # Stage is grayed out, don't activate
                return

        # Deactivate all buttons
        for btn in self.buttons.values():
            btn.set_active(False)

        # Activate selected button
        if stage_id in self.buttons:
            self.buttons[stage_id].set_active(True)
            self.current_stage = stage_id

    def enable_stage(self, stage_id: str, enabled: bool = True) -> None:
        """
        Enable or disable a stage button.

        Args:
            stage_id: Stage identifier
            enabled: Whether to enable the button
        """
        if stage_id in self.buttons:
            state = "normal" if enabled else "disabled"
            self.buttons[stage_id].configure(state=state)

    def gray_out_stage(self, stage_id: str, grayed: bool = True, reason: str = "") -> None:
        """
        Gray out a stage (for pipeline mode).

        Args:
            stage_id: Stage identifier
            grayed: Whether to gray out
            reason: Tooltip reason text
        """
        if stage_id in self.buttons:
            if grayed:
                # Force deactivate first (bypass the _grayed_out check)
                self.buttons[stage_id].is_active = False
                self.buttons[stage_id].configure(
                    state="disabled",
                    text_color=("gray90", "gray70"),
                    fg_color=("#8B4545", "#5C3030"),  # Dim red background (light theme, dark theme)
                    hover_color=("#8B4545", "#5C3030")  # Same color on hover (no change)
                )
                # Store grayed state
                self.buttons[stage_id]._grayed_out = True
            else:
                self.buttons[stage_id].configure(
                    state="normal",
                    text_color=("gray10", "gray90"),
                    fg_color="transparent",
                    hover_color=("gray85", "gray30")
                )
                # Clear grayed state
                self.buttons[stage_id]._grayed_out = False

    def update_for_pipeline_mode(self, pipeline_mode: str) -> None:
        """
        Update navigation for pipeline mode (ML vs DL).

        Args:
            pipeline_mode: "ml" or "dl"
        """
        logger.info(f"🔴 NAVIGATION UPDATE CALLED: pipeline_mode='{pipeline_mode}'")
        if pipeline_mode == "dl":
            # Gray out feature-related stages for deep learning
            logger.info("🔴 APPLYING RED BACKGROUNDS TO DISABLED TABS")
            self.gray_out_stage("features", grayed=True, reason="Not needed for Deep Learning")
            logger.info(f"🔴 features button fg_color: {self.buttons['features'].cget('fg_color')}")
            self.gray_out_stage("filtering", grayed=True, reason="Not needed for Deep Learning")
            logger.info(f"🔴 filtering button fg_color: {self.buttons['filtering'].cget('fg_color')}")
            self.gray_out_stage("llm", grayed=True, reason="Not needed for Deep Learning")
            logger.info(f"🔴 llm button fg_color: {self.buttons['llm'].cget('fg_color')}")
            self.gray_out_stage("dsp", grayed=True, reason="Use ONNX export for Deep Learning models")
            logger.info(f"🔴 dsp button fg_color: {self.buttons['dsp'].cget('fg_color')}")
            self.gray_out_stage("build", grayed=True, reason="Build firmware requires DSP C++ code (MCU only)")
            logger.info(f"🔴 build button fg_color: {self.buttons['build'].cget('fg_color')}")
            logger.info("Navigation: Grayed out feature stages for Deep Learning mode with RED backgrounds")
        else:
            # Enable all stages for traditional ML
            logger.info("🔴 REMOVING RED BACKGROUNDS")
            self.gray_out_stage("features", grayed=False)
            self.gray_out_stage("filtering", grayed=False)
            self.gray_out_stage("llm", grayed=False)
            self.gray_out_stage("dsp", grayed=False)
            self.gray_out_stage("build", grayed=False)
            logger.info("Navigation: Enabled all stages for Traditional ML mode")

    def mark_stage_completed(self, stage_id: str) -> None:
        """
        Mark a stage as completed (visual indicator).

        Args:
            stage_id: Stage identifier
        """
        if stage_id in self.buttons:
            # Add checkmark to button text
            stage = next((s for s in self.STAGES if s["id"] == stage_id), None)
            if stage:
                self.buttons[stage_id].configure(
                    text=f"{stage['icon']}  {stage['name']} ✓"
                )
                logger.info(f"Navigation: Stage '{stage_id}' marked as completed")

    def get_stage_name(self, stage_id: str) -> str:
        """
        Get human-readable stage name.

        Args:
            stage_id: Stage identifier

        Returns:
            Stage name
        """
        stage = next((s for s in self.STAGES if s["id"] == stage_id), None)
        return stage["name"] if stage else "Unknown"

"""
Navigation Sidebar

Provides left sidebar navigation for the application workflow.
"""

import customtkinter as ctk
from typing import Callable, List, Dict, Any, Optional
from loguru import logger


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
        self.is_active = active
        if active:
            # Light theme (first value) and dark theme (second value)
            self.configure(fg_color=("#2b76c2", "#1f538d"))
        else:
            self.configure(fg_color="transparent")


class NavigationSidebar(ctk.CTkFrame):
    """Navigation sidebar with stage buttons."""

    # Application stages
    STAGES = [
        {"id": "data", "name": "Data Sources", "icon": "📊"},
        {"id": "features", "name": "Feature Extraction", "icon": "🔬"},
        {"id": "filtering", "name": "Feature Filtering", "icon": "🔍"},
        {"id": "llm", "name": "LLM Selection", "icon": "🤖"},
        {"id": "model", "name": "Training", "icon": "🎯"},
        {"id": "dsp", "name": "DSP Generation", "icon": "⚙️"},
        {"id": "build", "name": "Build Firmware", "icon": "🚀"},
    ]

    def __init__(self, master, on_stage_change: Callable[[str], None], **kwargs):
        """
        Initialize navigation sidebar.

        Args:
            master: Parent widget
            on_stage_change: Callback when stage changes (receives stage_id)
        """
        super().__init__(master, width=220, corner_radius=0, **kwargs)

        self.on_stage_change = on_stage_change
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
        # TODO: Implement settings dialog

    def set_active_stage(self, stage_id: str) -> None:
        """
        Set active navigation stage.

        Args:
            stage_id: Stage identifier
        """
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

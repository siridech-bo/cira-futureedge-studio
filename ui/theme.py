"""
Theme Management

Handles application themes (dark/light mode) and color schemes.
"""

import customtkinter as ctk
from typing import Dict, Any
from loguru import logger
from pathlib import Path


class ThemeManager:
    """Manages application themes and appearance."""

    # Font sizes for consistent UI
    FONTS = {
        "title": 20,      # Main titles (increased from 16)
        "heading": 17,    # Section headings (increased from 14)
        "body": 14,       # Body text (increased from 12)
        "small": 12,      # Small text (increased from 10)
    }

    # Color schemes for different themes
    DARK_COLORS = {
        "primary": "#1f6aa5",
        "secondary": "#144870",
        "success": "#2fa572",
        "warning": "#ff9800",
        "error": "#f44336",
        "background": "#1a1a1a",
        "surface": "#2b2b2b",
        "text": "#ffffff",
        "text_secondary": "#b0b0b0",
        "border": "#404040",
        "hover": "#3a3a3a",
    }

    LIGHT_COLORS = {
        "primary": "#1f6aa5",
        "secondary": "#5fa3d0",
        "success": "#4caf50",
        "warning": "#ff9800",
        "error": "#f44336",
        "background": "#f5f5f5",
        "surface": "#ffffff",
        "text": "#000000",
        "text_secondary": "#666666",
        "border": "#e0e0e0",
        "hover": "#eeeeee",
    }

    # Available color themes
    COLOR_THEMES = ["blue", "green", "dark-blue", "rime", "sky", "yellow", "marsh"]

    def __init__(self, theme: str = "dark", color_theme: str = "blue"):
        """
        Initialize theme manager.

        Args:
            theme: "dark" or "light"
            color_theme: CustomTkinter color theme name
        """
        self.theme = theme
        self.color_theme = color_theme
        self._apply_theme()

    def _apply_theme(self) -> None:
        """Apply current theme settings."""
        ctk.set_appearance_mode(self.theme)

        # Check if it's a custom theme
        if self.color_theme in ["rime", "sky", "yellow", "marsh"]:
            theme_path = Path(__file__).parent.parent / "themes" / f"{self.color_theme}.json"
            if theme_path.exists():
                ctk.set_default_color_theme(str(theme_path))
                logger.info(f"Theme applied: {self.theme} mode, {self.color_theme} custom theme")
            else:
                logger.warning(f"Custom theme file not found: {theme_path}, using blue")
                ctk.set_default_color_theme("blue")
        else:
            ctk.set_default_color_theme(self.color_theme)
            logger.info(f"Theme applied: {self.theme} mode, {self.color_theme} color scheme")

    def set_theme(self, theme: str) -> None:
        """
        Set appearance theme.

        Args:
            theme: "dark" or "light"
        """
        if theme not in ["dark", "light"]:
            logger.warning(f"Invalid theme: {theme}, using 'dark'")
            theme = "dark"

        self.theme = theme
        ctk.set_appearance_mode(theme)
        logger.info(f"Theme changed to: {theme}")

    def set_color_theme(self, color_theme: str) -> None:
        """
        Set color theme.

        Args:
            color_theme: CustomTkinter color theme name
        """
        if color_theme not in self.COLOR_THEMES:
            logger.warning(f"Invalid color theme: {color_theme}, using 'blue'")
            color_theme = "blue"

        # Check if it's a custom theme
        if color_theme in ["rime", "sky", "yellow", "marsh"]:
            if self.load_custom_theme(color_theme):
                return
            else:
                # Fallback to blue if custom theme fails
                color_theme = "blue"

        self.color_theme = color_theme
        ctk.set_default_color_theme(color_theme)
        logger.info(f"Color theme changed to: {color_theme}")

    def toggle_theme(self) -> str:
        """
        Toggle between dark and light themes.

        Returns:
            New theme name
        """
        new_theme = "light" if self.theme == "dark" else "dark"
        self.set_theme(new_theme)
        return new_theme

    def get_colors(self) -> Dict[str, str]:
        """
        Get color palette for current theme.

        Returns:
            Dictionary of color names to hex values
        """
        return self.DARK_COLORS if self.theme == "dark" else self.LIGHT_COLORS

    def get_color(self, color_name: str) -> str:
        """
        Get specific color from current theme.

        Args:
            color_name: Color name (e.g., "primary", "background")

        Returns:
            Hex color code
        """
        colors = self.get_colors()
        return colors.get(color_name, colors["primary"])

    @staticmethod
    def configure_widget_colors(widget: ctk.CTkBaseClass, colors: Dict[str, Any]) -> None:
        """
        Configure widget colors.

        Args:
            widget: CustomTkinter widget
            colors: Dictionary of color properties
        """
        try:
            widget.configure(**colors)
        except Exception as e:
            logger.warning(f"Failed to configure widget colors: {e}")

    @classmethod
    def get_font(cls, font_type: str = "body", weight: str = "normal") -> ctk.CTkFont:
        """
        Get a CTkFont with specified type and weight.

        Args:
            font_type: Font type ("title", "heading", "body", "small")
            weight: Font weight ("normal" or "bold")

        Returns:
            CTkFont instance
        """
        size = cls.FONTS.get(font_type, cls.FONTS["body"])
        return ctk.CTkFont(size=size, weight=weight)

    def load_custom_theme(self, theme_name: str) -> bool:
        """
        Load a custom theme from themes directory.

        Args:
            theme_name: Name of the theme (e.g., "rime", "sky")

        Returns:
            True if theme loaded successfully
        """
        theme_path = Path(__file__).parent.parent / "themes" / f"{theme_name}.json"
        if theme_path.exists():
            try:
                ctk.set_default_color_theme(str(theme_path))
                self.color_theme = theme_name
                logger.info(f"Loaded custom theme: {theme_name}")
                return True
            except Exception as e:
                logger.error(f"Failed to load custom theme {theme_name}: {e}")
                return False
        else:
            logger.warning(f"Theme file not found: {theme_path}")
            return False

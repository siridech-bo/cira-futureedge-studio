"""
Configuration Management

Handles application settings, paths, and user preferences.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from loguru import logger


@dataclass
class Config:
    """Application configuration."""

    # Application info
    app_name: str = "CiRA FutureEdge Studio"
    version: str = "1.0.0"
    author: str = "CiRA Team"

    # Paths
    project_root: Path = Path(__file__).parent.parent
    models_dir: Path = project_root / "models"
    output_dir: Path = project_root / "output"
    sdk_dir: Path = project_root / "sdk"
    toolchain_dir: Path = project_root / "toolchain"

    # UI settings
    window_width: int = 1400
    window_height: int = 900
    theme: str = "dark"  # "dark" or "light"
    color_theme: str = "blue"  # CustomTkinter color themes

    # Feature extraction settings
    default_window_size: int = 100
    default_sampling_rate: float = 50.0  # Hz
    default_overlap: float = 0.0  # No overlap
    max_features: int = 5  # Maximum features for embedded deployment

    # LLM settings
    llm_model_name: str = "Llama-3.2-3B-Instruct-Q4_K_M.gguf"
    llm_threads: int = 4
    llm_context_length: int = 2048
    llm_temperature: float = 0.3  # Low temperature for deterministic output
    llm_max_tokens: int = 1024

    # Anomaly detection settings
    default_test_size: float = 0.2
    default_random_state: int = 42

    # Build settings
    cmake_generator: str = "MinGW Makefiles"
    build_type: str = "Release"
    target_platform: str = "x86"  # "x86", "cortex-m4", "esp32"

    # Logging
    log_level: str = "INFO"

    def __post_init__(self):
        """Initialize paths after dataclass creation."""
        # Convert strings to Path objects if needed
        if isinstance(self.project_root, str):
            self.project_root = Path(self.project_root)
        if isinstance(self.models_dir, str):
            self.models_dir = Path(self.models_dir)
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)
        if isinstance(self.sdk_dir, str):
            self.sdk_dir = Path(self.sdk_dir)
        if isinstance(self.toolchain_dir, str):
            self.toolchain_dir = Path(self.toolchain_dir)

        # Create directories if they don't exist
        self.models_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)

    def save(self, path: Optional[Path] = None) -> None:
        """Save configuration to JSON file."""
        if path is None:
            path = self.project_root / "config.json"

        config_dict = asdict(self)
        # Convert Path objects to strings for JSON serialization
        for key, value in config_dict.items():
            if isinstance(value, Path):
                config_dict[key] = str(value)

        with open(path, 'w') as f:
            json.dump(config_dict, f, indent=2)

        logger.info(f"Configuration saved to {path}")

    @classmethod
    def load(cls, path: Optional[Path] = None) -> 'Config':
        """Load configuration from JSON file."""
        if path is None:
            path = Path(__file__).parent.parent / "config.json"

        if not path.exists():
            logger.warning(f"Config file not found at {path}, using defaults")
            return cls()

        with open(path, 'r') as f:
            config_dict = json.load(f)

        # Convert string paths back to Path objects
        path_keys = ["project_root", "models_dir", "output_dir", "sdk_dir", "toolchain_dir"]
        for key in path_keys:
            if key in config_dict:
                config_dict[key] = Path(config_dict[key])

        logger.info(f"Configuration loaded from {path}")
        return cls(**config_dict)

    def get_llm_model_path(self) -> Path:
        """Get full path to LLM model file."""
        return self.models_dir / self.llm_model_name

    def get_feature_types(self) -> list:
        """Get allowed feature types for embedded deployment."""
        return [
            "rms",
            "mean_derivative",
            "spectral_power_bin",
            "zero_crossing_rate",
            "pysr_formula"
        ]


# Global config instance
_config_instance = None


def get_config() -> Config:
    """Get global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config.load()
    return _config_instance


def set_config(config: Config) -> None:
    """Set global configuration instance."""
    global _config_instance
    _config_instance = config

"""
Feature Extraction Configuration

Manages tsfresh feature extraction settings with support for:
- 3 complexity levels (Minimal, Efficient, Comprehensive)
- 3 configuration modes (Simple, Advanced, Per-Sensor)
- Custom feature definitions
- Rolling/forecasting configuration
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import json
from enum import Enum
from loguru import logger


class ComplexityLevel(str, Enum):
    """Feature extraction complexity levels."""
    MINIMAL = "minimal"
    EFFICIENT = "efficient"
    COMPREHENSIVE = "comprehensive"


class ConfigurationMode(str, Enum):
    """Feature configuration modes."""
    SIMPLE = "simple"          # Use preset defaults
    ADVANCED = "advanced"      # Global custom settings
    PER_SENSOR = "per_sensor"  # Different settings per sensor


class OperationMode(str, Enum):
    """Application operation modes."""
    ANOMALY_DETECTION = "anomaly_detection"
    FORECASTING = "forecasting"


@dataclass
class RollingConfig:
    """Configuration for rolling time series (forecasting mode)."""

    enabled: bool = False
    max_timeshift: int = 100        # Look back N samples
    min_timeshift: int = 10         # Minimum history needed
    rolling_direction: int = 1      # 1=forward, -1=backward
    target_column: Optional[str] = None  # Column to predict
    prediction_horizon: int = 1     # Steps ahead to predict

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'RollingConfig':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class CustomFeature:
    """Custom user-defined feature."""

    name: str
    code: str
    feature_type: str = "simple"  # "simple" or "combiner"
    parameters: Dict[str, List[Any]] = field(default_factory=dict)
    description: str = ""
    enabled: bool = True

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'CustomFeature':
        """Create from dictionary."""
        return cls(**data)

    def validate(self) -> tuple[bool, str]:
        """Validate custom feature code."""
        try:
            # Check if code is valid Python
            compile(self.code, '<string>', 'exec')

            # Check if function name matches
            if f"def {self.name}" not in self.code:
                return False, f"Function name must be '{self.name}'"

            # Check for required decorator
            if '@set_property' not in self.code:
                return False, "Missing @set_property decorator"

            return True, "Valid"

        except SyntaxError as e:
            return False, f"Syntax error: {str(e)}"


@dataclass
class FilteringConfig:
    """Feature filtering/selection configuration."""

    enabled: bool = True
    p_value_threshold: float = 0.05
    fdr_level: float = 0.05
    method: str = "benjamini_yekutieli"  # Multiple test procedure

    # Additional filtering options
    remove_low_variance: bool = True
    variance_threshold: float = 0.01
    remove_highly_correlated: bool = True
    correlation_threshold: float = 0.95

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'FilteringConfig':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class FeatureExtractionConfig:
    """Complete feature extraction configuration."""

    # Operation mode
    operation_mode: OperationMode = OperationMode.ANOMALY_DETECTION

    # Complexity and configuration
    complexity_level: ComplexityLevel = ComplexityLevel.EFFICIENT
    configuration_mode: ConfigurationMode = ConfigurationMode.SIMPLE

    # Global feature settings (for ADVANCED mode)
    global_fc_parameters: Optional[Dict[str, Any]] = None

    # Per-sensor settings (for PER_SENSOR mode)
    per_sensor_fc_parameters: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Rolling configuration
    rolling_config: RollingConfig = field(default_factory=RollingConfig)

    # Custom features
    custom_features: List[CustomFeature] = field(default_factory=list)

    # Filtering configuration
    filtering_config: FilteringConfig = field(default_factory=FilteringConfig)

    # Computation settings
    n_jobs: int = 4  # Parallel jobs
    chunksize: int = 10  # Chunk size for parallel processing
    show_warnings: bool = False

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = {
            'operation_mode': self.operation_mode.value,
            'complexity_level': self.complexity_level.value,
            'configuration_mode': self.configuration_mode.value,
            'global_fc_parameters': self.global_fc_parameters,
            'per_sensor_fc_parameters': self.per_sensor_fc_parameters,
            'rolling_config': self.rolling_config.to_dict(),
            'custom_features': [f.to_dict() for f in self.custom_features],
            'filtering_config': self.filtering_config.to_dict(),
            'n_jobs': self.n_jobs,
            'chunksize': self.chunksize,
            'show_warnings': self.show_warnings
        }
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'FeatureExtractionConfig':
        """Create from dictionary."""
        return cls(
            operation_mode=OperationMode(data.get('operation_mode', 'anomaly_detection')),
            complexity_level=ComplexityLevel(data.get('complexity_level', 'efficient')),
            configuration_mode=ConfigurationMode(data.get('configuration_mode', 'simple')),
            global_fc_parameters=data.get('global_fc_parameters'),
            per_sensor_fc_parameters=data.get('per_sensor_fc_parameters', {}),
            rolling_config=RollingConfig.from_dict(data.get('rolling_config', {})),
            custom_features=[CustomFeature.from_dict(f) for f in data.get('custom_features', [])],
            filtering_config=FilteringConfig.from_dict(data.get('filtering_config', {})),
            n_jobs=data.get('n_jobs', 4),
            chunksize=data.get('chunksize', 10),
            show_warnings=data.get('show_warnings', False)
        )

    def save(self, path: Path) -> None:
        """Save configuration to file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Feature config saved to {path}")

    @classmethod
    def load(cls, path: Path) -> 'FeatureExtractionConfig':
        """Load configuration from file."""
        with open(path, 'r') as f:
            data = json.load(f)
        config = cls.from_dict(data)
        logger.info(f"Feature config loaded from {path}")
        return config

    def get_enabled_custom_features(self) -> List[CustomFeature]:
        """Get list of enabled custom features."""
        return [f for f in self.custom_features if f.enabled]

    def add_custom_feature(self, feature: CustomFeature) -> None:
        """Add a custom feature."""
        # Check if feature name already exists
        existing = [f for f in self.custom_features if f.name == feature.name]
        if existing:
            logger.warning(f"Replacing existing custom feature: {feature.name}")
            self.custom_features = [f for f in self.custom_features if f.name != feature.name]

        self.custom_features.append(feature)
        logger.info(f"Added custom feature: {feature.name}")

    def remove_custom_feature(self, name: str) -> bool:
        """Remove a custom feature by name."""
        original_count = len(self.custom_features)
        self.custom_features = [f for f in self.custom_features if f.name != name]

        if len(self.custom_features) < original_count:
            logger.info(f"Removed custom feature: {name}")
            return True
        return False

    def get_tsfresh_settings(self) -> Dict[str, Any]:
        """
        Convert configuration to tsfresh-compatible settings.

        Returns settings dictionary suitable for extract_features() function.
        """
        from tsfresh.feature_extraction import (
            MinimalFCParameters,
            EfficientFCParameters,
            ComprehensiveFCParameters
        )

        # Get base settings from complexity level
        if self.complexity_level == ComplexityLevel.MINIMAL:
            settings = MinimalFCParameters()
        elif self.complexity_level == ComplexityLevel.EFFICIENT:
            settings = EfficientFCParameters()
        else:  # COMPREHENSIVE
            settings = ComprehensiveFCParameters()

        # Apply configuration mode
        if self.configuration_mode == ConfigurationMode.SIMPLE:
            # Use defaults
            return settings

        elif self.configuration_mode == ConfigurationMode.ADVANCED:
            # Apply global custom settings
            if self.global_fc_parameters:
                settings.update(self.global_fc_parameters)
            return settings

        elif self.configuration_mode == ConfigurationMode.PER_SENSOR:
            # Return per-sensor settings (will be handled differently)
            return self.per_sensor_fc_parameters

        return settings

    def is_forecasting_mode(self) -> bool:
        """Check if in forecasting mode."""
        return self.operation_mode == OperationMode.FORECASTING

    def is_rolling_enabled(self) -> bool:
        """Check if rolling is enabled."""
        return self.is_forecasting_mode() and self.rolling_config.enabled


# Default configurations for quick access
DEFAULT_ANOMALY_CONFIG = FeatureExtractionConfig(
    operation_mode=OperationMode.ANOMALY_DETECTION,
    complexity_level=ComplexityLevel.EFFICIENT,
    configuration_mode=ConfigurationMode.SIMPLE
)

DEFAULT_FORECASTING_CONFIG = FeatureExtractionConfig(
    operation_mode=OperationMode.FORECASTING,
    complexity_level=ComplexityLevel.EFFICIENT,
    configuration_mode=ConfigurationMode.SIMPLE,
    rolling_config=RollingConfig(
        enabled=True,
        max_timeshift=100,
        min_timeshift=10
    )
)

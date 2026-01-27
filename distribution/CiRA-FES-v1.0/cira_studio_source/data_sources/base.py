"""
Base classes for data sources.

Provides abstract interface for all data source implementations.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pathlib import Path
import pandas as pd
from dataclasses import dataclass
from loguru import logger


@dataclass
class DataSourceConfig:
    """Configuration for a data source."""
    source_type: str  # "csv", "database", "api", "stream"
    name: str
    description: str = ""
    parameters: Dict[str, Any] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


class DataSource(ABC):
    """Abstract base class for all data sources."""

    def __init__(self, config: DataSourceConfig):
        """
        Initialize data source.

        Args:
            config: Data source configuration
        """
        self.config = config
        self.is_connected = False
        self._data: Optional[pd.DataFrame] = None

    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to the data source.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the data source."""
        pass

    @abstractmethod
    def load_data(self, **kwargs) -> pd.DataFrame:
        """
        Load data from the source.

        Returns:
            DataFrame with loaded data

        Raises:
            Exception if loading fails
        """
        pass

    def validate_data(self, df: pd.DataFrame) -> tuple[bool, List[str]]:
        """
        Validate loaded data.

        Args:
            df: DataFrame to validate

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check if DataFrame is empty
        if df.empty:
            issues.append("DataFrame is empty")
            return False, issues

        # Check for required columns (time series should have timestamp-like column)
        if not any(col.lower() in ['time', 'timestamp', 'datetime'] for col in df.columns):
            issues.append("No time column found (expected 'time', 'timestamp', or 'datetime')")

        # Check for missing values
        missing = df.isnull().sum()
        if missing.any():
            for col, count in missing[missing > 0].items():
                issues.append(f"Column '{col}' has {count} missing values")

        # Check data types
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) == 0:
            issues.append("No numeric columns found (sensor data should be numeric)")

        is_valid = len(issues) == 0
        return is_valid, issues

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the data source.

        Returns:
            Dictionary with data source information
        """
        info = {
            "name": self.config.name,
            "type": self.config.source_type,
            "connected": self.is_connected,
            "description": self.config.description,
        }

        if self._data is not None:
            info.update({
                "rows": len(self._data),
                "columns": list(self._data.columns),
                "dtypes": {col: str(dtype) for col, dtype in self._data.dtypes.items()},
                "memory_usage": f"{self._data.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB"
            })

        return info

    def get_column_stats(self, column: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a specific column.

        Args:
            column: Column name

        Returns:
            Dictionary with column statistics or None if column doesn't exist
        """
        if self._data is None or column not in self._data.columns:
            return None

        col_data = self._data[column]
        stats = {
            "name": column,
            "dtype": str(col_data.dtype),
            "count": int(col_data.count()),
            "missing": int(col_data.isnull().sum()),
        }

        # Add numeric statistics if applicable
        if pd.api.types.is_numeric_dtype(col_data):
            stats.update({
                "min": float(col_data.min()),
                "max": float(col_data.max()),
                "mean": float(col_data.mean()),
                "median": float(col_data.median()),
                "std": float(col_data.std()),
            })

        return stats


class DataSourceFactory:
    """Factory for creating data source instances."""

    _registry: Dict[str, type] = {}

    @classmethod
    def register(cls, source_type: str, source_class: type):
        """
        Register a data source class.

        Args:
            source_type: Type identifier (e.g., "csv", "database")
            source_class: Data source class
        """
        cls._registry[source_type] = source_class
        logger.info(f"Registered data source: {source_type}")

    @classmethod
    def create(cls, config: DataSourceConfig) -> DataSource:
        """
        Create a data source instance.

        Args:
            config: Data source configuration

        Returns:
            Data source instance

        Raises:
            ValueError if source type not registered
        """
        source_class = cls._registry.get(config.source_type)
        if source_class is None:
            raise ValueError(f"Unknown data source type: {config.source_type}")

        return source_class(config)

    @classmethod
    def get_available_types(cls) -> List[str]:
        """
        Get list of available data source types.

        Returns:
            List of registered source types
        """
        return list(cls._registry.keys())

"""
CSV Data Loader

Loads time-series data from CSV files.
"""

from pathlib import Path
from typing import Optional, List
import pandas as pd
from loguru import logger

from data_sources.base import DataSource, DataSourceConfig, DataSourceFactory


class CSVDataSource(DataSource):
    """CSV file data source."""

    def __init__(self, config: DataSourceConfig):
        """
        Initialize CSV data source.

        Args:
            config: Data source configuration
                Expected parameters:
                - file_path: Path to CSV file
                - delimiter: Column delimiter (default: ',')
                - decimal: Decimal separator (default: '.')
                - encoding: File encoding (default: 'utf-8')
                - skiprows: Rows to skip (default: 0)
                - parse_dates: Columns to parse as dates (default: None)
        """
        super().__init__(config)
        self.file_path: Optional[Path] = None

    def connect(self) -> bool:
        """
        Validate CSV file exists.

        Returns:
            True if file exists, False otherwise
        """
        file_path = self.config.parameters.get("file_path")
        if not file_path:
            logger.error("No file_path specified in configuration")
            return False

        self.file_path = Path(file_path)

        if not self.file_path.exists():
            logger.error(f"CSV file not found: {self.file_path}")
            return False

        if not self.file_path.is_file():
            logger.error(f"Path is not a file: {self.file_path}")
            return False

        self.is_connected = True
        logger.info(f"Connected to CSV file: {self.file_path}")
        return True

    def disconnect(self) -> None:
        """Disconnect from CSV file."""
        self.is_connected = False
        self._data = None
        logger.info("Disconnected from CSV file")

    def load_data(self, **kwargs) -> pd.DataFrame:
        """
        Load data from CSV file.

        Args:
            **kwargs: Additional pandas read_csv parameters

        Returns:
            DataFrame with loaded data

        Raises:
            ValueError if not connected
            Exception if loading fails
        """
        if not self.is_connected:
            raise ValueError("Not connected to CSV file. Call connect() first.")

        # Get configuration parameters
        delimiter = self.config.parameters.get("delimiter", ",")
        decimal = self.config.parameters.get("decimal", ".")
        encoding = self.config.parameters.get("encoding", "utf-8")
        skiprows = self.config.parameters.get("skiprows", 0)
        parse_dates = self.config.parameters.get("parse_dates", None)

        # Merge kwargs with config parameters
        read_params = {
            "delimiter": delimiter,
            "decimal": decimal,
            "encoding": encoding,
            "skiprows": skiprows,
        }

        if parse_dates:
            read_params["parse_dates"] = parse_dates

        read_params.update(kwargs)

        try:
            logger.info(f"Loading CSV file: {self.file_path}")
            self._data = pd.read_csv(self.file_path, **read_params)

            logger.info(f"Loaded {len(self._data)} rows, {len(self._data.columns)} columns")
            logger.debug(f"Columns: {list(self._data.columns)}")

            # Validate data
            is_valid, issues = self.validate_data(self._data)
            if not is_valid:
                logger.warning(f"Data validation issues: {issues}")
            else:
                logger.info("Data validation passed")

            return self._data

        except Exception as e:
            logger.error(f"Failed to load CSV file: {e}")
            raise

    def preview_data(self, n_rows: int = 5) -> pd.DataFrame:
        """
        Preview first N rows of data.

        Args:
            n_rows: Number of rows to preview

        Returns:
            DataFrame with first N rows
        """
        if self._data is None:
            self.load_data()

        return self._data.head(n_rows)

    def get_sample_data(self, n_samples: int = 1000) -> pd.DataFrame:
        """
        Get random sample of data.

        Args:
            n_samples: Number of samples to return

        Returns:
            DataFrame with random sample
        """
        if self._data is None:
            self.load_data()

        if len(self._data) <= n_samples:
            return self._data.copy()

        return self._data.sample(n=n_samples, random_state=42)

    def detect_time_column(self) -> Optional[str]:
        """
        Detect the time/timestamp column.

        Returns:
            Name of time column or None if not found
        """
        if self._data is None:
            return None

        # Check for common time column names
        time_names = ['time', 'timestamp', 'datetime', 'date', 't']
        for col in self._data.columns:
            if col.lower() in time_names:
                return col

        # Check for datetime dtype
        for col in self._data.columns:
            if pd.api.types.is_datetime64_any_dtype(self._data[col]):
                return col

        return None

    def detect_sensor_columns(self) -> List[str]:
        """
        Detect sensor data columns (numeric columns excluding time).

        Returns:
            List of sensor column names
        """
        if self._data is None:
            return []

        time_col = self.detect_time_column()
        numeric_cols = self._data.select_dtypes(include=['number']).columns.tolist()

        # Exclude time column if it's numeric
        if time_col and time_col in numeric_cols:
            numeric_cols.remove(time_col)

        return numeric_cols

    def infer_sampling_rate(self) -> Optional[float]:
        """
        Infer sampling rate from time column.

        Returns:
            Sampling rate in Hz or None if cannot be determined
        """
        time_col = self.detect_time_column()
        if not time_col or self._data is None:
            return None

        try:
            # Convert to datetime if needed
            if not pd.api.types.is_datetime64_any_dtype(self._data[time_col]):
                time_data = pd.to_datetime(self._data[time_col])
            else:
                time_data = self._data[time_col]

            # Calculate time differences
            time_diffs = time_data.diff().dropna()

            # Get median time difference (more robust than mean)
            median_diff = time_diffs.median()

            # Convert to seconds
            median_diff_seconds = median_diff.total_seconds()

            if median_diff_seconds > 0:
                sampling_rate = 1.0 / median_diff_seconds
                logger.info(f"Inferred sampling rate: {sampling_rate:.2f} Hz")
                return sampling_rate

        except Exception as e:
            logger.warning(f"Failed to infer sampling rate: {e}")

        return None


# Register CSV data source
DataSourceFactory.register("csv", CSVDataSource)

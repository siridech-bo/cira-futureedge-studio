"""
Time-Series Windowing Engine

Segments time-series data into windows for feature extraction.
"""

from typing import List, Optional, Tuple, Dict, Any
import numpy as np
import pandas as pd
from dataclasses import dataclass
from loguru import logger


@dataclass
class WindowConfig:
    """Configuration for windowing."""
    window_size: int = 100  # Number of samples per window
    overlap: float = 0.0  # Overlap ratio (0.0 = no overlap, 0.5 = 50% overlap)
    sampling_rate: float = 50.0  # Hz
    min_window_samples: int = 10  # Minimum samples for a valid window


@dataclass
class Window:
    """A single window of time-series data."""
    window_id: int
    start_idx: int
    end_idx: int
    data: pd.DataFrame
    label: int = 0  # 0=nominal, 1=off, 2=anomaly (for anomaly detection)
    class_label: Optional[str] = None  # Class label for classification mode
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def size(self) -> int:
        """Number of samples in window."""
        return len(self.data)

    @property
    def duration(self) -> float:
        """Window duration in seconds (if sampling_rate in metadata)."""
        sampling_rate = self.metadata.get('sampling_rate', 1.0)
        return self.size / sampling_rate


class WindowingEngine:
    """Engine for segmenting time-series data into windows."""

    def __init__(self, config: WindowConfig):
        """
        Initialize windowing engine.

        Args:
            config: Windowing configuration
        """
        self.config = config
        self.windows: List[Window] = []

    def segment_data(
        self,
        data: pd.DataFrame,
        sensor_columns: List[str],
        time_column: Optional[str] = None,
        label_column: Optional[str] = None
    ) -> List[Window]:
        """
        Segment data into windows.

        Args:
            data: Input DataFrame
            sensor_columns: List of sensor column names to include
            time_column: Name of time column (optional)
            label_column: Name of label column (optional)

        Returns:
            List of Window objects
        """
        logger.info(f"Segmenting data into windows...")
        logger.info(f"Window size: {self.config.window_size}, Overlap: {self.config.overlap}")

        # Validate inputs
        for col in sensor_columns:
            if col not in data.columns:
                raise ValueError(f"Sensor column '{col}' not found in data")

        # Calculate step size
        step_size = int(self.config.window_size * (1 - self.config.overlap))
        if step_size < 1:
            step_size = 1

        windows = []
        window_id = 0

        # Extract relevant columns (include metadata columns like _source_file)
        if time_column and time_column in data.columns:
            columns_to_extract = [time_column] + sensor_columns
        else:
            columns_to_extract = sensor_columns

        # Add metadata columns if they exist (preserve source file tracking, etc.)
        metadata_columns = ['_source_file']
        for meta_col in metadata_columns:
            if meta_col in data.columns and meta_col not in columns_to_extract:
                columns_to_extract.append(meta_col)

        # Iterate through data and create windows
        for start_idx in range(0, len(data) - self.config.window_size + 1, step_size):
            end_idx = start_idx + self.config.window_size

            # Extract window data
            window_data = data.iloc[start_idx:end_idx][columns_to_extract].copy()

            # Skip if not enough samples
            if len(window_data) < self.config.min_window_samples:
                continue

            # Determine label for window using majority voting
            label = 0  # default: nominal (for anomaly detection)
            class_label = None  # default: None (for classification)

            if label_column and label_column in data.columns:
                # Use mode (most common label) in window - majority voting
                window_labels = data.iloc[start_idx:end_idx][label_column]
                if not window_labels.empty:
                    majority_label = window_labels.mode()[0]

                    # Check if label is string (classification) or numeric (anomaly)
                    if isinstance(majority_label, str):
                        class_label = majority_label
                        label = 0  # Keep numeric label at default for compatibility
                    else:
                        label = int(majority_label)
                        class_label = None

            # Create window metadata
            metadata = {
                'sampling_rate': self.config.sampling_rate,
                'n_sensors': len(sensor_columns),
                'sensor_names': sensor_columns,
            }

            if time_column and time_column in data.columns:
                metadata['start_time'] = str(data.iloc[start_idx][time_column])
                metadata['end_time'] = str(data.iloc[end_idx - 1][time_column])

            # Create window object
            window = Window(
                window_id=window_id,
                start_idx=start_idx,
                end_idx=end_idx,
                data=window_data,
                label=label,
                class_label=class_label,
                metadata=metadata
            )

            windows.append(window)
            window_id += 1

        self.windows = windows
        logger.info(f"Created {len(windows)} windows")

        return windows

    def get_window_stats(self) -> Dict[str, Any]:
        """
        Get statistics about windows.

        Returns:
            Dictionary with window statistics
        """
        if not self.windows:
            return {"total_windows": 0}

        label_counts = {}
        class_label_counts = {}

        for window in self.windows:
            # Count numeric labels (anomaly detection)
            label_counts[window.label] = label_counts.get(window.label, 0) + 1

            # Count class labels (classification)
            if window.class_label is not None:
                class_label_counts[window.class_label] = \
                    class_label_counts.get(window.class_label, 0) + 1

        stats = {
            "total_windows": len(self.windows),
            "window_size": self.config.window_size,
            "overlap": self.config.overlap,
            "sampling_rate": self.config.sampling_rate,
            "label_distribution": label_counts,
            "total_samples": sum(w.size for w in self.windows),
        }

        # Add class distribution if classification mode
        if class_label_counts:
            stats["class_distribution"] = class_label_counts

        return stats

    def get_windows_by_label(self, label: int) -> List[Window]:
        """
        Get windows with specific label (anomaly detection mode).

        Args:
            label: Label value (0=nominal, 1=off, 2=anomaly)

        Returns:
            List of windows with matching label
        """
        return [w for w in self.windows if w.label == label]

    def get_windows_by_class(self, class_label: str) -> List[Window]:
        """
        Get windows with specific class label (classification mode).

        Args:
            class_label: Class label (e.g., 'idle', 'snake', 'ingestion')

        Returns:
            List of windows with matching class label
        """
        return [w for w in self.windows if w.class_label == class_label]

    def get_class_labels(self) -> List[str]:
        """
        Get list of unique class labels from all windows.

        Returns:
            List of unique class labels (sorted)
        """
        class_labels = set()
        for window in self.windows:
            if window.class_label is not None:
                class_labels.add(window.class_label)
        return sorted(list(class_labels))

    def export_windows_to_numpy(
        self,
        sensor_columns: Optional[List[str]] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Export windows to numpy arrays for ML.

        Args:
            sensor_columns: Sensor columns to include (None = all sensors)

        Returns:
            Tuple of (X, y) where:
                X: shape (n_windows, window_size, n_sensors)
                y: shape (n_windows,) - labels
        """
        if not self.windows:
            return np.array([]), np.array([])

        # Determine which columns to use
        if sensor_columns is None:
            sensor_columns = self.windows[0].metadata['sensor_names']

        # Preallocate arrays
        n_windows = len(self.windows)
        window_size = self.config.window_size
        n_sensors = len(sensor_columns)

        X = np.zeros((n_windows, window_size, n_sensors))
        y = np.zeros(n_windows, dtype=int)

        # Fill arrays
        for i, window in enumerate(self.windows):
            # Extract sensor data (excluding time column if present)
            sensor_data = window.data[sensor_columns].values
            X[i] = sensor_data
            y[i] = window.label

        logger.info(f"Exported windows to numpy: X shape {X.shape}, y shape {y.shape}")

        return X, y

    def export_windows_to_hdf5(self, filepath: str) -> None:
        """
        Export windows to HDF5 file.

        Args:
            filepath: Path to output HDF5 file
        """
        import h5py

        if not self.windows:
            logger.warning("No windows to export")
            return

        with h5py.File(filepath, 'w') as f:
            # Store configuration
            config_group = f.create_group('config')
            config_group.attrs['window_size'] = self.config.window_size
            config_group.attrs['overlap'] = self.config.overlap
            config_group.attrs['sampling_rate'] = self.config.sampling_rate

            # Store windows
            for window in self.windows:
                window_group = f.create_group(f'window_{window.window_id}')
                window_group.create_dataset('data', data=window.data.values)
                window_group.attrs['label'] = window.label
                window_group.attrs['start_idx'] = window.start_idx
                window_group.attrs['end_idx'] = window.end_idx

                # Store metadata
                for key, value in window.metadata.items():
                    if isinstance(value, (int, float, str)):
                        window_group.attrs[key] = value
                    elif isinstance(value, list):
                        window_group.attrs[key] = str(value)

        logger.info(f"Exported {len(self.windows)} windows to {filepath}")

    def assign_labels(self, labels: Dict[int, int]) -> None:
        """
        Manually assign labels to windows.

        Args:
            labels: Dictionary mapping window_id to label
        """
        for window in self.windows:
            if window.window_id in labels:
                window.label = labels[window.window_id]

        logger.info(f"Updated labels for {len(labels)} windows")

    def filter_windows(
        self,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        labels: Optional[List[int]] = None
    ) -> List[Window]:
        """
        Filter windows by criteria.

        Args:
            min_size: Minimum window size
            max_size: Maximum window size
            labels: List of labels to include

        Returns:
            Filtered list of windows
        """
        filtered = self.windows

        if min_size is not None:
            filtered = [w for w in filtered if w.size >= min_size]

        if max_size is not None:
            filtered = [w for w in filtered if w.size <= max_size]

        if labels is not None:
            filtered = [w for w in filtered if w.label in labels]

        logger.info(f"Filtered {len(self.windows)} windows to {len(filtered)}")

        return filtered

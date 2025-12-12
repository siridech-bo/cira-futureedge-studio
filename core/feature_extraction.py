"""
Feature Extraction Engine

Handles feature extraction from time series data using tsfresh with support for:
- Multiple complexity levels
- Custom feature calculators
- Rolling mechanism for forecasting
- Feature filtering and selection
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from loguru import logger

from core.feature_config import (
    FeatureExtractionConfig,
    CustomFeature,
    ConfigurationMode,
    OperationMode
)
from core.windowing import Window


class FeatureExtractionEngine:
    """Engine for extracting features from time series data."""

    def __init__(self, config: FeatureExtractionConfig):
        """
        Initialize feature extraction engine.

        Args:
            config: Feature extraction configuration
        """
        self.config = config
        self.extracted_features: Optional[pd.DataFrame] = None
        self.filtered_features: Optional[pd.DataFrame] = None
        self.feature_names: List[str] = []
        self.relevance_table: Optional[pd.DataFrame] = None

        # Register custom features
        self._register_custom_features()

    def _register_custom_features(self) -> None:
        """Register custom user-defined features with tsfresh."""
        custom_features = self.config.get_enabled_custom_features()

        if not custom_features:
            return

        logger.info(f"Registering {len(custom_features)} custom features")

        for feature in custom_features:
            try:
                # Execute custom feature code in namespace
                namespace = {}
                exec(feature.code, namespace)

                # Get the function
                if feature.name in namespace:
                    func = namespace[feature.name]
                    logger.info(f"Registered custom feature: {feature.name}")
                else:
                    logger.error(f"Custom feature function not found: {feature.name}")

            except Exception as e:
                logger.error(f"Failed to register custom feature {feature.name}: {e}")

    def extract_from_windows(
        self,
        windows: List[Window],
        sensor_columns: List[str],
        target: Optional[pd.Series] = None
    ) -> pd.DataFrame:
        """
        Extract features from windowed data.

        Args:
            windows: List of Window objects
            sensor_columns: List of sensor column names
            target: Target variable for supervised filtering (optional)

        Returns:
            DataFrame with extracted features
        """
        from tsfresh import extract_features
        from tsfresh.utilities.dataframe_functions import impute

        logger.info(f"Extracting features from {len(windows)} windows")
        logger.info(f"Sensor columns: {sensor_columns}")
        logger.info(f"Configuration mode: {self.config.configuration_mode.value}")

        # Convert windows to tsfresh format
        df_tsfresh = self._windows_to_tsfresh_format(windows, sensor_columns)

        # Get tsfresh settings
        settings = self.config.get_tsfresh_settings()

        # Extract features
        if self.config.configuration_mode == ConfigurationMode.PER_SENSOR:
            # Per-sensor custom settings
            logger.info("Using per-sensor configuration")
            features = extract_features(
                df_tsfresh,
                column_id="window_id",
                column_sort="sample_id",
                default_fc_parameters=settings,
                n_jobs=self.config.n_jobs,
                chunksize=self.config.chunksize,
                disable_progressbar=False,
                show_warnings=self.config.show_warnings
            )
        else:
            # Global settings
            logger.info(f"Using {self.config.complexity_level.value} settings")
            features = extract_features(
                df_tsfresh,
                column_id="window_id",
                column_sort="sample_id",
                default_fc_parameters=settings,
                n_jobs=self.config.n_jobs,
                chunksize=self.config.chunksize,
                disable_progressbar=False,
                show_warnings=self.config.show_warnings
            )

        # Impute missing values
        impute(features)

        logger.info(f"Extracted {features.shape[1]} features")
        self.extracted_features = features
        self.feature_names = list(features.columns)

        # Apply filtering if enabled
        if self.config.filtering_config.enabled and target is not None:
            self.filtered_features = self.filter_features(features, target)
            return self.filtered_features

        return features

    def extract_from_rolling(
        self,
        data: pd.DataFrame,
        time_column: str,
        sensor_columns: List[str],
        target_column: str
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Extract features using rolling mechanism for forecasting.

        Args:
            data: Time series data
            time_column: Name of time column
            sensor_columns: List of sensor column names
            target_column: Column to predict

        Returns:
            Tuple of (features DataFrame, target Series)
        """
        from tsfresh.utilities.dataframe_functions import roll_time_series, make_forecasting_frame
        from tsfresh import extract_features
        from tsfresh.utilities.dataframe_functions import impute

        logger.info("Extracting features using rolling mechanism")
        logger.info(f"Max timeshift: {self.config.rolling_config.max_timeshift}")
        logger.info(f"Target column: {target_column}")

        # Prepare data for rolling
        df_prep = data[[time_column] + sensor_columns + [target_column]].copy()
        df_prep['id'] = 1  # Single time series ID

        # Roll time series
        df_rolled = roll_time_series(
            df_prep,
            column_id='id',
            column_sort=time_column,
            max_timeshift=self.config.rolling_config.max_timeshift,
            min_timeshift=self.config.rolling_config.min_timeshift,
            rolling_direction=self.config.rolling_config.rolling_direction
        )

        logger.info(f"Created {len(df_rolled['id'].unique())} rolled windows")

        # Extract features
        settings = self.config.get_tsfresh_settings()

        if self.config.configuration_mode == ConfigurationMode.PER_SENSOR:
            features = extract_features(
                df_rolled,
                column_id="id",
                column_sort=time_column,
                default_fc_parameters=settings,
                n_jobs=self.config.n_jobs,
                chunksize=self.config.chunksize,
                disable_progressbar=False,
                show_warnings=self.config.show_warnings
            )
        else:
            features = extract_features(
                df_rolled,
                column_id="id",
                column_sort=time_column,
                default_fc_parameters=settings,
                n_jobs=self.config.n_jobs,
                chunksize=self.config.chunksize,
                disable_progressbar=False,
                show_warnings=self.config.show_warnings
            )

        # Impute missing values
        impute(features)

        # Create forecasting frame to get target values
        X, y = make_forecasting_frame(
            df_prep,
            kind=target_column,
            max_timeshift=self.config.rolling_config.max_timeshift,
            column_id='id',
            column_sort=time_column
        )

        # Align features with target
        features_aligned = features.loc[y.index]

        logger.info(f"Extracted {features_aligned.shape[1]} features for {len(y)} samples")

        self.extracted_features = features_aligned
        self.feature_names = list(features_aligned.columns)

        # Apply filtering if enabled
        if self.config.filtering_config.enabled:
            self.filtered_features = self.filter_features(features_aligned, y)
            return self.filtered_features, y

        return features_aligned, y

    def filter_features(
        self,
        features: pd.DataFrame,
        target: pd.Series
    ) -> pd.DataFrame:
        """
        Filter features using statistical significance testing.

        Args:
            features: Extracted features DataFrame
            target: Target variable

        Returns:
            Filtered features DataFrame
        """
        from tsfresh.feature_selection.relevance import calculate_relevance_table
        from tsfresh.feature_selection.selection import select_features

        logger.info("Starting feature filtering")
        logger.info(f"Input features: {features.shape[1]}")

        # Phase 2: Calculate feature significance
        logger.info("Phase 2: Calculating feature significance...")
        self.relevance_table = calculate_relevance_table(
            features,
            target,
            ml_task='auto',
            n_jobs=self.config.n_jobs,
            chunksize=self.config.chunksize,
            show_warnings=self.config.show_warnings
        )

        # Phase 3: Multiple test procedure (Benjamini-Yekutieli)
        logger.info("Phase 3: Applying multiple test procedure...")
        filtered = select_features(
            features,
            target,
            ml_task='auto',
            fdr_level=self.config.filtering_config.fdr_level,
            n_jobs=self.config.n_jobs,
            chunksize=self.config.chunksize,
            show_warnings=self.config.show_warnings
        )

        # Additional filtering
        if self.config.filtering_config.remove_low_variance:
            logger.info("Removing low variance features...")
            from sklearn.feature_selection import VarianceThreshold
            selector = VarianceThreshold(
                threshold=self.config.filtering_config.variance_threshold
            )
            filtered_array = selector.fit_transform(filtered)
            filtered = pd.DataFrame(
                filtered_array,
                index=filtered.index,
                columns=filtered.columns[selector.get_support()]
            )

        if self.config.filtering_config.remove_highly_correlated:
            logger.info("Removing highly correlated features...")
            filtered = self._remove_correlated_features(
                filtered,
                threshold=self.config.filtering_config.correlation_threshold
            )

        logger.info(f"Filtered features: {filtered.shape[1]}")
        logger.info(f"Reduction: {features.shape[1]} → {filtered.shape[1]} "
                   f"({100 * (1 - filtered.shape[1]/features.shape[1]):.1f}% reduction)")

        return filtered

    def _remove_correlated_features(
        self,
        features: pd.DataFrame,
        threshold: float = 0.95
    ) -> pd.DataFrame:
        """Remove highly correlated features."""
        corr_matrix = features.corr().abs()

        # Select upper triangle of correlation matrix
        upper = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        )

        # Find features with correlation greater than threshold
        to_drop = [column for column in upper.columns if any(upper[column] > threshold)]

        logger.info(f"Removing {len(to_drop)} highly correlated features")

        return features.drop(columns=to_drop)

    def _windows_to_tsfresh_format(
        self,
        windows: List[Window],
        sensor_columns: List[str]
    ) -> pd.DataFrame:
        """
        Convert Window objects to tsfresh format.

        tsfresh expects:
        - column_id: Identifier for each time series (window_id)
        - column_sort: Time/order column (sample_id)
        - value columns: Sensor data

        Args:
            windows: List of Window objects
            sensor_columns: List of sensor column names

        Returns:
            DataFrame in tsfresh format
        """
        logger.info("Converting windows to tsfresh format")

        rows = []
        for window in windows:
            window_data = window.data[sensor_columns].copy()
            window_data['window_id'] = window.window_id
            window_data['sample_id'] = range(len(window_data))
            rows.append(window_data)

        df = pd.concat(rows, ignore_index=True)

        logger.info(f"Created tsfresh DataFrame: {df.shape}")
        return df

    def get_feature_importance(self) -> Optional[pd.DataFrame]:
        """
        Get feature importance from relevance table.

        Returns:
            DataFrame with feature names and importance scores
        """
        if self.relevance_table is None:
            logger.warning("No relevance table available. Run filtering first.")
            return None

        importance = self.relevance_table.copy()
        importance['abs_relevance'] = importance['relevance'].abs()
        importance = importance.sort_values('abs_relevance', ascending=False)

        return importance[['feature', 'relevance', 'p_value']]

    def export_features(self, path: Path, format: str = 'parquet') -> None:
        """
        Export extracted features to file.

        Args:
            path: Output file path
            format: File format ('parquet', 'csv', 'hdf5')
        """
        if self.extracted_features is None:
            raise ValueError("No features extracted yet")

        if format == 'parquet':
            self.extracted_features.to_parquet(path)
        elif format == 'csv':
            self.extracted_features.to_csv(path)
        elif format == 'hdf5':
            self.extracted_features.to_hdf(path, key='features', mode='w')
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Exported features to {path}")

    def get_feature_statistics(self) -> Dict[str, Any]:
        """Get statistics about extracted features."""
        if self.extracted_features is None:
            return {}

        stats = {
            'total_features': len(self.feature_names),
            'feature_names': self.feature_names,
            'num_samples': len(self.extracted_features),
            'memory_usage_mb': self.extracted_features.memory_usage(deep=True).sum() / 1024 / 1024
        }

        if self.filtered_features is not None:
            stats['filtered_features'] = self.filtered_features.shape[1]
            stats['reduction_percent'] = 100 * (1 - stats['filtered_features'] / stats['total_features'])

        return stats

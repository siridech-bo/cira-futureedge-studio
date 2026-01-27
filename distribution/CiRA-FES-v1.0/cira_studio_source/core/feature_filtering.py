"""
Feature Filtering

Provides multiple filtering strategies to remove irrelevant/redundant features:
1. Basic filtering (constant, low-variance)
2. tsfresh built-in filtering (hypothesis testing)
3. Mutual Information filtering
4. Correlation-based filtering
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from loguru import logger
from dataclasses import dataclass


@dataclass
class FilteringResult:
    """Result of feature filtering operation."""
    filtered_features: pd.DataFrame
    selected_feature_names: List[str]
    removed_feature_names: List[str]
    filtering_stats: Dict[str, Any]
    method: str


class FeatureFilter:
    """Feature filtering engine with multiple strategies."""

    def __init__(self):
        """Initialize feature filter."""
        pass

    def filter_basic(
        self,
        features_df: pd.DataFrame,
        variance_threshold: float = 0.01,
        remove_constant: bool = True,
        remove_nan: bool = True,
        remove_extreme: bool = True,
        extreme_threshold: float = 1e15
    ) -> FilteringResult:
        """
        Basic filtering: remove constant, low-variance, and NaN features.

        Args:
            features_df: Feature matrix
            variance_threshold: Minimum variance threshold
            remove_constant: Remove constant features
            remove_nan: Remove features with NaN values

        Returns:
            FilteringResult with filtered features
        """
        logger.info("Starting basic feature filtering")
        original_count = len(features_df.columns)
        removed_features = []
        stats = {}

        # Start with all features
        filtered_df = features_df.copy()

        # Remove constant features
        if remove_constant:
            constant_features = []
            for col in filtered_df.columns:
                if filtered_df[col].nunique() <= 1:
                    constant_features.append(col)

            if constant_features:
                logger.info(f"Removing {len(constant_features)} constant features")
                filtered_df = filtered_df.drop(columns=constant_features)
                removed_features.extend(constant_features)
                stats['constant_features'] = len(constant_features)

        # Remove low variance features
        if variance_threshold > 0:
            low_var_features = []
            for col in filtered_df.columns:
                if filtered_df[col].var() < variance_threshold:
                    low_var_features.append(col)

            if low_var_features:
                logger.info(f"Removing {len(low_var_features)} low-variance features (threshold={variance_threshold})")
                filtered_df = filtered_df.drop(columns=low_var_features)
                removed_features.extend(low_var_features)
                stats['low_variance_features'] = len(low_var_features)

        # Remove features with NaN values
        if remove_nan:
            nan_features = []
            for col in filtered_df.columns:
                if filtered_df[col].isna().any():
                    nan_features.append(col)

            if nan_features:
                logger.info(f"Removing {len(nan_features)} features with NaN values")
                filtered_df = filtered_df.drop(columns=nan_features)
                removed_features.extend(nan_features)
                stats['nan_features'] = len(nan_features)

        # Remove features with extreme values (numerical instability)
        if remove_extreme:
            extreme_features = []
            for col in filtered_df.columns:
                max_abs_val = filtered_df[col].abs().max()
                if max_abs_val > extreme_threshold:
                    extreme_features.append(col)
                    logger.debug(f"Feature {col} has extreme value: {max_abs_val:.2e}")

            if extreme_features:
                logger.info(f"Removing {len(extreme_features)} features with extreme values (>{extreme_threshold:.0e})")
                filtered_df = filtered_df.drop(columns=extreme_features)
                removed_features.extend(extreme_features)
                stats['extreme_features'] = len(extreme_features)

        stats['original_features'] = original_count
        stats['filtered_features'] = len(filtered_df.columns)
        stats['removed_features'] = len(removed_features)

        logger.info(f"Basic filtering: {original_count} → {len(filtered_df.columns)} features")

        return FilteringResult(
            filtered_features=filtered_df,
            selected_feature_names=list(filtered_df.columns),
            removed_feature_names=removed_features,
            filtering_stats=stats,
            method="basic"
        )

    def filter_tsfresh(
        self,
        features_df: pd.DataFrame,
        labels: List[str],
        fdr_level: float = 0.05,
        hypotheses_independent: bool = False
    ) -> FilteringResult:
        """
        Use tsfresh's built-in filtering based on hypothesis testing.

        Args:
            features_df: Feature matrix
            labels: Class labels for each sample
            fdr_level: False Discovery Rate level (default 0.05)
            hypotheses_independent: Whether to treat hypotheses as independent

        Returns:
            FilteringResult with filtered features
        """
        try:
            from tsfresh.feature_selection.relevance import calculate_relevance_table
            from tsfresh.feature_selection.selection import select_features
        except ImportError:
            raise ImportError("tsfresh not installed. Install with: pip install tsfresh")

        logger.info("Starting tsfresh hypothesis-based filtering")
        original_count = len(features_df.columns)

        # Convert labels to pandas Series
        y = pd.Series(labels, index=features_df.index)

        # Use tsfresh's select_features function
        logger.info(f"Running hypothesis tests with FDR level={fdr_level}")

        filtered_df = select_features(
            features_df,
            y,
            fdr_level=fdr_level,
            hypotheses_independent=hypotheses_independent
        )

        selected_features = list(filtered_df.columns)
        removed_features = [col for col in features_df.columns if col not in selected_features]

        stats = {
            'original_features': original_count,
            'filtered_features': len(selected_features),
            'removed_features': len(removed_features),
            'fdr_level': fdr_level,
            'hypotheses_independent': hypotheses_independent
        }

        logger.info(f"tsfresh filtering: {original_count} → {len(selected_features)} features")

        return FilteringResult(
            filtered_features=filtered_df,
            selected_feature_names=selected_features,
            removed_feature_names=removed_features,
            filtering_stats=stats,
            method="tsfresh"
        )

    def filter_mutual_information(
        self,
        features_df: pd.DataFrame,
        labels: List[str],
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
        min_mi_score: float = 0.01
    ) -> FilteringResult:
        """
        Filter features based on Mutual Information scores.

        Args:
            features_df: Feature matrix
            labels: Class labels for each sample
            top_k: Keep top K features (if specified)
            threshold: Keep features with MI > threshold (if specified)
            min_mi_score: Minimum MI score to keep (default 0.01)

        Returns:
            FilteringResult with filtered features
        """
        try:
            from sklearn.feature_selection import mutual_info_classif
            from sklearn.preprocessing import LabelEncoder
        except ImportError:
            raise ImportError("scikit-learn not installed. Install with: pip install scikit-learn")

        logger.info("Starting Mutual Information filtering")
        original_count = len(features_df.columns)

        # Encode labels
        le = LabelEncoder()
        y_encoded = le.fit_transform(labels)

        # Calculate MI scores
        logger.info("Calculating mutual information scores...")
        mi_scores = mutual_info_classif(
            features_df.values,
            y_encoded,
            random_state=42
        )

        # Create DataFrame with MI scores
        mi_df = pd.DataFrame({
            'feature': features_df.columns,
            'mi_score': mi_scores
        }).sort_values('mi_score', ascending=False)

        # Determine which features to keep
        if top_k is not None:
            # Keep top K features
            selected_features = mi_df.head(top_k)['feature'].tolist()
            logger.info(f"Keeping top {top_k} features by MI score")
        elif threshold is not None:
            # Keep features above threshold
            selected_features = mi_df[mi_df['mi_score'] > threshold]['feature'].tolist()
            logger.info(f"Keeping features with MI > {threshold}")
        else:
            # Keep features above minimum score
            selected_features = mi_df[mi_df['mi_score'] > min_mi_score]['feature'].tolist()
            logger.info(f"Keeping features with MI > {min_mi_score}")

        filtered_df = features_df[selected_features]
        removed_features = [col for col in features_df.columns if col not in selected_features]

        # Calculate statistics
        selected_mi = mi_df[mi_df['feature'].isin(selected_features)]
        stats = {
            'original_features': original_count,
            'filtered_features': len(selected_features),
            'removed_features': len(removed_features),
            'min_mi_score': float(selected_mi['mi_score'].min()) if len(selected_mi) > 0 else 0.0,
            'max_mi_score': float(selected_mi['mi_score'].max()) if len(selected_mi) > 0 else 0.0,
            'mean_mi_score': float(selected_mi['mi_score'].mean()) if len(selected_mi) > 0 else 0.0,
            'threshold_used': threshold if threshold is not None else min_mi_score,
            'top_k': top_k
        }

        logger.info(f"MI filtering: {original_count} → {len(selected_features)} features")
        logger.info(f"MI score range: {stats['min_mi_score']:.4f} - {stats['max_mi_score']:.4f}")

        return FilteringResult(
            filtered_features=filtered_df,
            selected_feature_names=selected_features,
            removed_feature_names=removed_features,
            filtering_stats=stats,
            method="mutual_information"
        )

    def analyze_feature_quality(
        self,
        features_df: pd.DataFrame,
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze feature quality and return statistics.

        Args:
            features_df: Feature matrix
            labels: Class labels (optional, for MI calculation)

        Returns:
            Dictionary with quality statistics
        """
        logger.info("Analyzing feature quality...")

        stats = {
            'total_features': len(features_df.columns),
            'total_samples': len(features_df),
        }

        # Check for constant features
        constant_features = []
        for col in features_df.columns:
            if features_df[col].nunique() <= 1:
                constant_features.append(col)
        stats['constant_features'] = len(constant_features)

        # Check for NaN features
        nan_features = [col for col in features_df.columns if features_df[col].isna().any()]
        stats['nan_features'] = len(nan_features)
        stats['nan_percentage'] = len(nan_features) / len(features_df.columns) * 100

        # Variance statistics
        variances = features_df.var()
        stats['variance_stats'] = {
            'min': float(variances.min()),
            'max': float(variances.max()),
            'mean': float(variances.mean()),
            'median': float(variances.median())
        }

        # Low variance count (< 0.01)
        low_var = (variances < 0.01).sum()
        stats['low_variance_features'] = int(low_var)

        # If labels provided, calculate MI scores
        if labels is not None:
            try:
                from sklearn.feature_selection import mutual_info_classif
                from sklearn.preprocessing import LabelEncoder

                le = LabelEncoder()
                y_encoded = le.fit_transform(labels)

                # Calculate MI for sample of features if too many
                sample_size = min(500, len(features_df.columns))
                sample_features = features_df.columns[:sample_size]

                mi_scores = mutual_info_classif(
                    features_df[sample_features].values,
                    y_encoded,
                    random_state=42
                )

                stats['mi_stats'] = {
                    'sampled_features': sample_size,
                    'min': float(mi_scores.min()),
                    'max': float(mi_scores.max()),
                    'mean': float(mi_scores.mean()),
                    'median': float(np.median(mi_scores)),
                    'features_with_mi_gt_0.01': int((mi_scores > 0.01).sum()),
                    'features_with_mi_gt_0.05': int((mi_scores > 0.05).sum()),
                    'features_with_mi_gt_0.10': int((mi_scores > 0.10).sum()),
                }
            except Exception as e:
                logger.warning(f"Could not calculate MI scores: {e}")
                stats['mi_stats'] = None

        logger.info(f"Quality analysis complete: {stats['total_features']} features analyzed")

        return stats

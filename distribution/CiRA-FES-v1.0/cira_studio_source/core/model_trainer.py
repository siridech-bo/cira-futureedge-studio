"""
CiRA FutureEdge Studio - Anomaly Detection Model Trainer
Integrates PyOD for anomaly detection with 45+ algorithms
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pickle
import json

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix
)

# PyOD imports
from pyod.models.iforest import IForest
from pyod.models.lof import LOF
from pyod.models.knn import KNN
from pyod.models.ocsvm import OCSVM
from pyod.models.pca import PCA
from pyod.models.abod import ABOD
from pyod.models.auto_encoder import AutoEncoder
from pyod.models.cblof import CBLOF
from pyod.models.hbos import HBOS
from pyod.models.mcd import MCD
from pyod.models.loda import LODA
from pyod.models.copod import COPOD
from pyod.models.ecod import ECOD

from loguru import logger


# Available algorithms with their default parameters
ALGORITHMS = {
    # Distance-based
    'knn': {
        'name': 'K-Nearest Neighbors',
        'class': KNN,
        'params': {'n_neighbors': 5, 'method': 'largest'},
        'description': 'Fast, works well with moderate dimensions',
        'recommended_for': 'General purpose, quick prototyping'
    },
    'lof': {
        'name': 'Local Outlier Factor',
        'class': LOF,
        'params': {'n_neighbors': 20},
        'description': 'Detects local density deviations',
        'recommended_for': 'Clustered normal data'
    },
    'abod': {
        'name': 'Angle-Based Outlier Detection',
        'class': ABOD,
        'params': {'n_neighbors': 5},
        'description': 'Robust in high dimensions',
        'recommended_for': 'High-dimensional data'
    },

    # Tree-based
    'iforest': {
        'name': 'Isolation Forest',
        'class': IForest,
        'params': {'n_estimators': 100, 'contamination': 0.1},
        'description': 'Fast, efficient for large datasets',
        'recommended_for': 'Default choice, works well generally'
    },

    # Linear models
    'pca': {
        'name': 'Principal Component Analysis',
        'class': PCA,
        'params': {'n_components': None, 'contamination': 0.1},
        'description': 'Linear dimensionality reduction',
        'recommended_for': 'Linear correlations in data'
    },
    'mcd': {
        'name': 'Minimum Covariance Determinant',
        'class': MCD,
        'params': {'contamination': 0.1},
        'description': 'Robust covariance estimation',
        'recommended_for': 'Gaussian-distributed features'
    },
    'ocsvm': {
        'name': 'One-Class SVM',
        'class': OCSVM,
        'params': {'nu': 0.5, 'kernel': 'rbf'},
        'description': 'Kernel-based boundary detection',
        'recommended_for': 'Complex decision boundaries'
    },

    # Clustering-based
    'cblof': {
        'name': 'Cluster-Based Local Outlier Factor',
        'class': CBLOF,
        'params': {'n_clusters': 8, 'contamination': 0.1},
        'description': 'Clusters data, detects outliers',
        'recommended_for': 'Data with natural clusters'
    },

    # Histogram-based
    'hbos': {
        'name': 'Histogram-Based Outlier Score',
        'class': HBOS,
        'params': {'n_bins': 10, 'contamination': 0.1},
        'description': 'Very fast, assumes feature independence',
        'recommended_for': 'Independent features, speed critical'
    },
    'loda': {
        'name': 'Lightweight On-line Detector of Anomalies',
        'class': LODA,
        'params': {'n_bins': 10, 'contamination': 0.1},
        'description': 'Fast, works with high dimensions',
        'recommended_for': 'Streaming data, online detection'
    },

    # Probabilistic
    'copod': {
        'name': 'COPOD (Copula-Based)',
        'class': COPOD,
        'params': {},
        'description': 'Parameter-free, empirical copula',
        'recommended_for': 'No hyperparameter tuning needed'
    },
    'ecod': {
        'name': 'ECOD (Empirical Cumulative)',
        'class': ECOD,
        'params': {},
        'description': 'Parameter-free, very fast',
        'recommended_for': 'Quick baseline, no tuning'
    },

    # Neural network (commented out - requires TensorFlow)
    # 'autoencoder': {
    #     'name': 'AutoEncoder',
    #     'class': AutoEncoder,
    #     'params': {'hidden_neurons': [64, 32, 32, 64], 'epochs': 100},
    #     'description': 'Deep learning reconstruction error',
    #     'recommended_for': 'Complex patterns, large datasets'
    # },
}


@dataclass
class TrainingConfig:
    """Configuration for model training."""
    algorithm: str = 'iforest'
    test_size: float = 0.3
    random_state: int = 42
    contamination: float = 0.1
    normalize: bool = True
    params: Dict[str, Any] = None

    def __post_init__(self):
        if self.params is None:
            self.params = {}


@dataclass
class TrainingResults:
    """Results from model training and evaluation."""
    algorithm: str
    model_path: str
    scaler_path: str

    # Training metrics
    train_samples: int
    test_samples: int
    n_features: int
    feature_names: List[str]

    # Evaluation metrics (if labels available)
    has_labels: bool = False
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    roc_auc: Optional[float] = None

    # Unsupervised metrics (always available)
    train_anomaly_rate: float = 0.0
    test_anomaly_rate: float = 0.0

    # Confusion matrix (if labels available)
    confusion_matrix: Optional[List[List[int]]] = None

    # Model parameters
    params: Dict[str, Any] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'algorithm': self.algorithm,
            'model_path': self.model_path,
            'scaler_path': self.scaler_path,
            'train_samples': self.train_samples,
            'test_samples': self.test_samples,
            'n_features': self.n_features,
            'feature_names': self.feature_names,
            'has_labels': self.has_labels,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'roc_auc': self.roc_auc,
            'train_anomaly_rate': self.train_anomaly_rate,
            'test_anomaly_rate': self.test_anomaly_rate,
            'confusion_matrix': self.confusion_matrix,
            'params': self.params
        }


class ModelTrainer:
    """Train and evaluate anomaly detection models using PyOD."""

    def __init__(self):
        """Initialize the model trainer."""
        self.model = None
        self.scaler = None
        self.feature_names = None

    @staticmethod
    def get_available_algorithms() -> Dict[str, dict]:
        """Get dictionary of available algorithms and their info."""
        return ALGORITHMS

    def train(
        self,
        features_df: pd.DataFrame,
        selected_features: List[str],
        config: TrainingConfig,
        output_dir: Path,
        labels: Optional[np.ndarray] = None
    ) -> TrainingResults:
        """
        Train an anomaly detection model.

        Args:
            features_df: DataFrame with all extracted features
            selected_features: List of feature names to use
            config: Training configuration
            output_dir: Directory to save model and scaler
            labels: Optional ground truth labels (0=normal, 1=anomaly)

        Returns:
            TrainingResults with metrics and paths
        """
        logger.info(f"Training {config.algorithm} with {len(selected_features)} features")

        # Select features
        X = features_df[selected_features].values
        self.feature_names = selected_features

        # Split data
        if labels is not None:
            X_train, X_test, y_train, y_test = train_test_split(
                X, labels, test_size=config.test_size,
                random_state=config.random_state, stratify=labels
            )
        else:
            X_train, X_test = train_test_split(
                X, test_size=config.test_size, random_state=config.random_state
            )
            y_train = y_test = None

        # Normalize if requested
        if config.normalize:
            self.scaler = StandardScaler()
            X_train = self.scaler.fit_transform(X_train)
            X_test = self.scaler.transform(X_test)
        else:
            self.scaler = None

        # Get algorithm configuration
        if config.algorithm not in ALGORITHMS:
            raise ValueError(f"Unknown algorithm: {config.algorithm}")

        algo_config = ALGORITHMS[config.algorithm]
        model_class = algo_config['class']

        # Merge default params with custom params
        model_params = algo_config['params'].copy()
        model_params.update(config.params)

        # Create and train model
        logger.info(f"Initializing {algo_config['name']} with params: {model_params}")
        self.model = model_class(**model_params)

        logger.info(f"Training on {X_train.shape[0]} samples...")
        self.model.fit(X_train)

        # Predict on both sets
        y_train_pred = self.model.predict(X_train)  # 0=normal, 1=anomaly
        y_test_pred = self.model.predict(X_test)

        # Calculate anomaly rates
        train_anomaly_rate = np.mean(y_train_pred)
        test_anomaly_rate = np.mean(y_test_pred)

        # Save model and scaler
        output_dir.mkdir(parents=True, exist_ok=True)
        model_path = output_dir / f"{config.algorithm}_model.pkl"
        scaler_path = output_dir / f"{config.algorithm}_scaler.pkl"

        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        logger.info(f"Model saved to {model_path}")

        if self.scaler is not None:
            with open(scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            logger.info(f"Scaler saved to {scaler_path}")

        # Create results object
        results = TrainingResults(
            algorithm=config.algorithm,
            model_path=str(model_path),
            scaler_path=str(scaler_path) if self.scaler else None,
            train_samples=len(X_train),
            test_samples=len(X_test),
            n_features=len(selected_features),
            feature_names=selected_features,
            train_anomaly_rate=float(train_anomaly_rate),
            test_anomaly_rate=float(test_anomaly_rate),
            params=model_params
        )

        # Calculate metrics if labels available
        if y_test is not None:
            results.has_labels = True
            results.precision = float(precision_score(y_test, y_test_pred))
            results.recall = float(recall_score(y_test, y_test_pred))
            results.f1_score = float(f1_score(y_test, y_test_pred))

            # Get decision scores for ROC AUC
            y_test_scores = self.model.decision_function(X_test)
            results.roc_auc = float(roc_auc_score(y_test, y_test_scores))

            # Confusion matrix
            cm = confusion_matrix(y_test, y_test_pred)
            results.confusion_matrix = cm.tolist()

            logger.info(f"Evaluation - Precision: {results.precision:.3f}, "
                       f"Recall: {results.recall:.3f}, F1: {results.f1_score:.3f}, "
                       f"ROC-AUC: {results.roc_auc:.3f}")
        else:
            logger.info(f"No labels provided - unsupervised mode")
            logger.info(f"Anomaly rates - Train: {train_anomaly_rate:.1%}, "
                       f"Test: {test_anomaly_rate:.1%}")

        # Save results metadata
        results_path = output_dir / f"{config.algorithm}_results.json"
        with open(results_path, 'w') as f:
            json.dump(results.to_dict(), f, indent=2)
        logger.info(f"Results saved to {results_path}")

        return results

    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict anomalies on new data.

        Args:
            X: Feature matrix (n_samples, n_features)

        Returns:
            Tuple of (predictions, scores)
            - predictions: Binary labels (0=normal, 1=anomaly)
            - scores: Anomaly scores (higher = more anomalous)
        """
        if self.model is None:
            raise ValueError("Model not trained yet")

        # Normalize if scaler exists
        if self.scaler is not None:
            X = self.scaler.transform(X)

        predictions = self.model.predict(X)
        scores = self.model.decision_function(X)

        return predictions, scores

    def load_model(self, model_path: Path, scaler_path: Optional[Path] = None):
        """Load a trained model and optional scaler."""
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        logger.info(f"Model loaded from {model_path}")

        if scaler_path and scaler_path.exists():
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            logger.info(f"Scaler loaded from {scaler_path}")

    @staticmethod
    def get_algorithm_info(algorithm: str) -> dict:
        """Get information about a specific algorithm."""
        if algorithm not in ALGORITHMS:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        return ALGORITHMS[algorithm]

    @staticmethod
    def recommend_algorithm(
        n_samples: int,
        n_features: int,
        has_labels: bool = False
    ) -> str:
        """
        Recommend an algorithm based on data characteristics.

        Args:
            n_samples: Number of samples
            n_features: Number of features
            has_labels: Whether ground truth labels are available

        Returns:
            Recommended algorithm name
        """
        # Small dataset (< 1000 samples)
        if n_samples < 1000:
            if n_features > 10:
                return 'lof'  # Local density works well
            else:
                return 'knn'  # Simple and effective

        # Medium dataset (1000-10000 samples)
        elif n_samples < 10000:
            if n_features > 20:
                return 'iforest'  # Scales well with dimensions
            else:
                return 'copod'  # Fast and parameter-free

        # Large dataset (> 10000 samples)
        else:
            if n_features > 50:
                return 'ecod'  # Very fast, high-dimensional
            else:
                return 'iforest'  # Efficient and robust

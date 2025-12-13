"""
CiRA FutureEdge Studio - Multi-Class Classification Trainer
Integrates sklearn classifiers for supervised multi-class classification
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pickle
import json

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)

# Sklearn classifier imports
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LogisticRegression

from loguru import logger


# Available classifiers with their default parameters
CLASSIFIERS = {
    # Ensemble methods
    'random_forest': {
        'name': 'Random Forest',
        'class': RandomForestClassifier,
        'params': {'n_estimators': 100, 'max_depth': 10, 'random_state': 42},
        'description': 'Ensemble of decision trees, robust and accurate',
        'recommended_for': 'General purpose, works well with many features'
    },
    'gradient_boosting': {
        'name': 'Gradient Boosting',
        'class': GradientBoostingClassifier,
        'params': {'n_estimators': 100, 'max_depth': 5, 'learning_rate': 0.1, 'random_state': 42},
        'description': 'Iterative ensemble, often highest accuracy',
        'recommended_for': 'Maximum accuracy, can handle complex patterns'
    },

    # Support Vector Machine
    'svm': {
        'name': 'Support Vector Machine',
        'class': SVC,
        'params': {'kernel': 'rbf', 'C': 1.0, 'gamma': 'scale', 'probability': True, 'random_state': 42},
        'description': 'Maximum-margin classifier with kernel tricks',
        'recommended_for': 'Non-linear decision boundaries, medium datasets'
    },

    # Neural Network
    'mlp': {
        'name': 'Multi-Layer Perceptron',
        'class': MLPClassifier,
        'params': {'hidden_layer_sizes': (100, 50), 'max_iter': 500, 'random_state': 42},
        'description': 'Neural network with backpropagation',
        'recommended_for': 'Complex patterns, large datasets'
    },

    # Instance-based
    'knn': {
        'name': 'K-Nearest Neighbors',
        'class': KNeighborsClassifier,
        'params': {'n_neighbors': 5, 'weights': 'distance'},
        'description': 'Simple distance-based classifier',
        'recommended_for': 'Small datasets, interpretable results'
    },

    # Tree-based
    'decision_tree': {
        'name': 'Decision Tree',
        'class': DecisionTreeClassifier,
        'params': {'max_depth': 10, 'min_samples_split': 5, 'random_state': 42},
        'description': 'Single decision tree, highly interpretable',
        'recommended_for': 'Interpretability, feature importance'
    },

    # Probabilistic
    'naive_bayes': {
        'name': 'Gaussian Naive Bayes',
        'class': GaussianNB,
        'params': {},
        'description': 'Fast probabilistic classifier',
        'recommended_for': 'Quick baseline, small datasets'
    },

    # Linear
    'logistic_regression': {
        'name': 'Logistic Regression',
        'class': LogisticRegression,
        'params': {'max_iter': 1000, 'random_state': 42},
        'description': 'Linear classifier with probability output',
        'recommended_for': 'Linearly separable data, baseline'
    },
}


@dataclass
class ClassificationConfig:
    """Configuration for classification training."""
    algorithm: str = 'random_forest'
    test_size: float = 0.3
    random_state: int = 42
    normalize: bool = True
    params: Dict[str, Any] = None

    # Manual train/test split (optional)
    train_features: Optional[Any] = None  # DataFrame with training features
    train_labels: Optional[List[str]] = None  # Training labels
    test_features: Optional[Any] = None  # DataFrame with test features
    test_labels: Optional[List[str]] = None  # Test labels

    def __post_init__(self):
        if self.params is None:
            self.params = {}


@dataclass
class ClassificationResults:
    """Results from classification training and evaluation."""
    algorithm: str
    model_path: str
    scaler_path: Optional[str]
    label_encoder_path: str

    # Dataset info
    train_samples: int
    test_samples: int
    n_features: int
    n_classes: int
    feature_names: List[str]
    class_names: List[str]

    # Overall metrics
    accuracy: float
    precision_macro: float
    recall_macro: float
    f1_macro: float

    # Per-class metrics
    per_class_precision: Dict[str, float]
    per_class_recall: Dict[str, float]
    per_class_f1: Dict[str, float]

    # Confusion matrix
    confusion_matrix: List[List[int]]

    # Model parameters
    params: Dict[str, Any]

    # Feature importance (if available)
    feature_importances: Optional[Dict[str, float]] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'algorithm': self.algorithm,
            'model_path': self.model_path,
            'scaler_path': self.scaler_path,
            'label_encoder_path': self.label_encoder_path,
            'train_samples': self.train_samples,
            'test_samples': self.test_samples,
            'n_features': self.n_features,
            'n_classes': self.n_classes,
            'feature_names': self.feature_names,
            'class_names': self.class_names,
            'accuracy': self.accuracy,
            'precision_macro': self.precision_macro,
            'recall_macro': self.recall_macro,
            'f1_macro': self.f1_macro,
            'per_class_precision': self.per_class_precision,
            'per_class_recall': self.per_class_recall,
            'per_class_f1': self.per_class_f1,
            'confusion_matrix': self.confusion_matrix,
            'params': self.params,
            'feature_importances': self.feature_importances
        }


class ClassificationTrainer:
    """Train and evaluate multi-class classification models using sklearn."""

    def __init__(self):
        """Initialize the classification trainer."""
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.feature_names = None
        self.class_names = None

    @staticmethod
    def get_available_classifiers() -> Dict[str, dict]:
        """Get dictionary of available classifiers and their info."""
        return CLASSIFIERS

    def train(
        self,
        features_df: pd.DataFrame,
        selected_features: List[str],
        labels: np.ndarray,
        config: ClassificationConfig,
        output_dir: Path
    ) -> ClassificationResults:
        """
        Train a multi-class classification model.

        Args:
            features_df: DataFrame with all extracted features
            selected_features: List of feature names to use
            labels: Class labels (strings or integers)
            config: Training configuration
            output_dir: Directory to save model, scaler, and encoder

        Returns:
            ClassificationResults with metrics and paths
        """
        logger.info(f"Training {config.algorithm} with {len(selected_features)} features")

        # Select features
        X = features_df[selected_features].values
        self.feature_names = selected_features

        # Encode labels
        self.label_encoder = LabelEncoder()
        y = self.label_encoder.fit_transform(labels)
        self.class_names = self.label_encoder.classes_.tolist()

        logger.info(f"Detected {len(self.class_names)} classes: {self.class_names}")

        # Check if we have pre-split train/test data
        if hasattr(config, 'train_features') and config.train_features is not None:
            # Use pre-split data (manual train/test split)
            logger.info("Using manual train/test split from separate datasets")

            X_train = config.train_features[selected_features].values
            y_train = self.label_encoder.transform(config.train_labels)

            if config.test_features is not None and config.test_labels is not None:
                X_test = config.test_features[selected_features].values
                y_test = self.label_encoder.transform(config.test_labels)
                logger.info(f"Train: {X_train.shape[0]} samples, Test: {X_test.shape[0]} samples")
            else:
                # No test data provided, use entire training data for evaluation
                X_test = X_train
                y_test = y_train
                logger.warning("No test data provided, using training data for evaluation")
        else:
            # Split data automatically (stratified to maintain class distribution)
            logger.info(f"Using automatic train/test split ({config.test_size*100:.0f}% test)")
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=config.test_size,
                random_state=config.random_state, stratify=y
            )

        # Normalize if requested
        if config.normalize:
            self.scaler = StandardScaler()
            X_train = self.scaler.fit_transform(X_train)
            X_test = self.scaler.transform(X_test)
        else:
            self.scaler = None

        # Get classifier configuration
        if config.algorithm not in CLASSIFIERS:
            raise ValueError(f"Unknown classifier: {config.algorithm}")

        clf_config = CLASSIFIERS[config.algorithm]
        model_class = clf_config['class']

        # Merge default params with custom params
        model_params = clf_config['params'].copy()
        model_params.update(config.params)

        # Create and train model
        logger.info(f"Initializing {clf_config['name']} with params: {model_params}")
        self.model = model_class(**model_params)

        logger.info(f"Training on {X_train.shape[0]} samples...")
        self.model.fit(X_train, y_train)

        # Predict on test set
        y_pred = self.model.predict(X_test)

        # Calculate overall metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision_macro = precision_score(y_test, y_pred, average='macro')
        recall_macro = recall_score(y_test, y_pred, average='macro')
        f1_macro = f1_score(y_test, y_pred, average='macro')

        # Calculate per-class metrics
        precision_per_class = precision_score(y_test, y_pred, average=None)
        recall_per_class = recall_score(y_test, y_pred, average=None)
        f1_per_class = f1_score(y_test, y_pred, average=None)

        per_class_precision = {self.class_names[i]: float(precision_per_class[i]) for i in range(len(self.class_names))}
        per_class_recall = {self.class_names[i]: float(recall_per_class[i]) for i in range(len(self.class_names))}
        per_class_f1 = {self.class_names[i]: float(f1_per_class[i]) for i in range(len(self.class_names))}

        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)

        # Feature importances (if available)
        feature_importances = None
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            feature_importances = {self.feature_names[i]: float(importances[i]) for i in range(len(self.feature_names))}
            logger.info(f"Top 5 features: {sorted(feature_importances.items(), key=lambda x: x[1], reverse=True)[:5]}")

        # Save model, scaler, and encoder
        output_dir.mkdir(parents=True, exist_ok=True)
        model_path = output_dir / f"{config.algorithm}_classifier.pkl"
        scaler_path = output_dir / f"{config.algorithm}_scaler.pkl"
        encoder_path = output_dir / f"{config.algorithm}_encoder.pkl"

        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        logger.info(f"Model saved to {model_path}")

        if self.scaler is not None:
            with open(scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            logger.info(f"Scaler saved to {scaler_path}")

        with open(encoder_path, 'wb') as f:
            pickle.dump(self.label_encoder, f)
        logger.info(f"Label encoder saved to {encoder_path}")

        # Create results object
        results = ClassificationResults(
            algorithm=config.algorithm,
            model_path=str(model_path),
            scaler_path=str(scaler_path) if self.scaler else None,
            label_encoder_path=str(encoder_path),
            train_samples=len(X_train),
            test_samples=len(X_test),
            n_features=len(selected_features),
            n_classes=len(self.class_names),
            feature_names=selected_features,
            class_names=self.class_names,
            accuracy=float(accuracy),
            precision_macro=float(precision_macro),
            recall_macro=float(recall_macro),
            f1_macro=float(f1_macro),
            per_class_precision=per_class_precision,
            per_class_recall=per_class_recall,
            per_class_f1=per_class_f1,
            confusion_matrix=cm.tolist(),
            params=model_params,
            feature_importances=feature_importances
        )

        logger.info(f"Classification Results - Accuracy: {accuracy:.3f}, "
                   f"Precision: {precision_macro:.3f}, "
                   f"Recall: {recall_macro:.3f}, "
                   f"F1: {f1_macro:.3f}")

        # Log per-class metrics
        logger.info("Per-class F1 scores:")
        for class_name, f1 in per_class_f1.items():
            logger.info(f"  {class_name}: {f1:.3f}")

        # Save results metadata
        results_path = output_dir / f"{config.algorithm}_results.json"
        with open(results_path, 'w') as f:
            json.dump(results.to_dict(), f, indent=2)
        logger.info(f"Results saved to {results_path}")

        return results

    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict classes on new data.

        Args:
            X: Feature matrix (n_samples, n_features)

        Returns:
            Tuple of (predictions, probabilities)
            - predictions: Class labels (decoded strings)
            - probabilities: Probability matrix (n_samples, n_classes)
        """
        if self.model is None:
            raise ValueError("Model not trained yet")

        # Normalize if scaler exists
        if self.scaler is not None:
            X = self.scaler.transform(X)

        # Predict
        y_pred_encoded = self.model.predict(X)
        predictions = self.label_encoder.inverse_transform(y_pred_encoded)

        # Get probabilities if available
        if hasattr(self.model, 'predict_proba'):
            probabilities = self.model.predict_proba(X)
        else:
            # For models without predict_proba (like SVM without probability=True)
            probabilities = None

        return predictions, probabilities

    def load_model(self, model_path: Path, scaler_path: Optional[Path] = None,
                   encoder_path: Optional[Path] = None):
        """Load a trained model, scaler, and label encoder."""
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        logger.info(f"Model loaded from {model_path}")

        if scaler_path and scaler_path.exists():
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            logger.info(f"Scaler loaded from {scaler_path}")

        if encoder_path and encoder_path.exists():
            with open(encoder_path, 'rb') as f:
                self.label_encoder = pickle.load(f)
            self.class_names = self.label_encoder.classes_.tolist()
            logger.info(f"Label encoder loaded from {encoder_path}")

    @staticmethod
    def get_classifier_info(algorithm: str) -> dict:
        """Get information about a specific classifier."""
        if algorithm not in CLASSIFIERS:
            raise ValueError(f"Unknown classifier: {algorithm}")
        return CLASSIFIERS[algorithm]

    @staticmethod
    def recommend_classifier(
        n_samples: int,
        n_features: int,
        n_classes: int
    ) -> str:
        """
        Recommend a classifier based on data characteristics.

        Args:
            n_samples: Number of samples
            n_features: Number of features
            n_classes: Number of classes

        Returns:
            Recommended classifier name
        """
        # Small dataset (< 500 samples)
        if n_samples < 500:
            if n_classes == 2:
                return 'logistic_regression'  # Fast baseline for binary
            else:
                return 'knn'  # Simple and effective for small datasets

        # Medium dataset (500-5000 samples)
        elif n_samples < 5000:
            if n_features > 50:
                return 'random_forest'  # Handles many features well
            else:
                return 'svm'  # Good for moderate datasets

        # Large dataset (> 5000 samples)
        else:
            if n_features > 100:
                return 'gradient_boosting'  # Best accuracy for large data
            else:
                return 'random_forest'  # Fast and reliable

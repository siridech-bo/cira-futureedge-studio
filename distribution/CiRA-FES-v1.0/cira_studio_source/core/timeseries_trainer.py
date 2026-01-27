"""
CiRA FutureEdge Studio - Time Series Deep Learning Trainer
Integrates TimesNet for temporal pattern classification
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pickle
import json

import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)
from tqdm import tqdm
from loguru import logger

from .deep_models.timesnet import TimesNet, TimesNetConfig, create_timesnet_for_classification


@dataclass
class TimeSeriesConfig:
    """Configuration for time series deep learning training."""
    algorithm: str = 'timesnet'
    test_size: float = 0.3
    random_state: int = 42
    device: str = 'auto'  # 'auto', 'cpu', or 'cuda'
    complexity: str = 'efficient'  # 'minimal', 'efficient', 'comprehensive'

    # Training hyperparameters
    batch_size: int = 32
    epochs: int = 50
    learning_rate: float = 0.001
    patience: int = 10  # Early stopping patience

    # Model-specific params
    params: Dict[str, Any] = None

    # Manual train/test split (optional)
    train_windows: Optional[Any] = None  # Training windows array
    train_labels: Optional[List[str]] = None  # Training labels
    test_windows: Optional[Any] = None  # Test windows array
    test_labels: Optional[List[str]] = None  # Test labels

    def __post_init__(self):
        if self.params is None:
            self.params = {}


@dataclass
class TimeSeriesResults:
    """Results from time series training and evaluation."""
    algorithm: str
    model_path: str
    label_encoder_path: str
    onnx_model_path: Optional[str]

    # Device info
    device_used: str

    # Dataset info
    train_samples: int
    test_samples: int
    window_size: int
    n_sensors: int
    n_classes: int
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

    # Training history
    training_history: Dict[str, List[float]]

    # Model info
    model_params: Dict[str, Any]
    total_parameters: int

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'algorithm': self.algorithm,
            'model_path': self.model_path,
            'label_encoder_path': self.label_encoder_path,
            'onnx_model_path': self.onnx_model_path,
            'device_used': self.device_used,
            'train_samples': self.train_samples,
            'test_samples': self.test_samples,
            'window_size': self.window_size,
            'n_sensors': self.n_sensors,
            'n_classes': self.n_classes,
            'class_names': self.class_names,
            'accuracy': self.accuracy,
            'precision_macro': self.precision_macro,
            'recall_macro': self.recall_macro,
            'f1_macro': self.f1_macro,
            'per_class_precision': self.per_class_precision,
            'per_class_recall': self.per_class_recall,
            'per_class_f1': self.per_class_f1,
            'confusion_matrix': self.confusion_matrix,
            'training_history': self.training_history,
            'model_params': self.model_params,
            'total_parameters': self.total_parameters
        }


class TimeSeriesTrainer:
    """Train and evaluate time series deep learning models using TimesNet."""

    def __init__(self):
        """Initialize the time series trainer."""
        self.model = None
        self.label_encoder = None
        self.class_names = None
        self.device = None
        self.device_desc = None

    def train(
        self,
        windows: np.ndarray,
        labels: np.ndarray,
        config: TimeSeriesConfig,
        output_dir: Path,
        progress_callback: Optional[callable] = None
    ) -> TimeSeriesResults:
        """
        Train a TimesNet model for classification.

        Args:
            windows: Windowed sensor data (n_windows, window_size, n_sensors)
            labels: Class labels (strings or integers)
            config: Training configuration
            output_dir: Directory to save model and encoder

        Returns:
            TimeSeriesResults with metrics and paths
        """
        logger.info(f"Training {config.algorithm} deep learning model")

        # Check if we have pre-split train/test data
        if hasattr(config, 'train_windows') and config.train_windows is not None:
            logger.info("Using manual train/test split from separate datasets")

            # Encode labels from manual split
            self.label_encoder = LabelEncoder()
            all_labels = list(config.train_labels)
            if config.test_labels is not None:
                all_labels.extend(config.test_labels)
            self.label_encoder.fit(all_labels)
            self.class_names = self.label_encoder.classes_.tolist()
            n_classes = len(self.class_names)

            X_train = config.train_windows
            y_train = self.label_encoder.transform(config.train_labels)

            if config.test_windows is not None and config.test_labels is not None:
                X_test = config.test_windows
                y_test = self.label_encoder.transform(config.test_labels)
                logger.info(f"Train: {X_train.shape[0]} samples, Test: {X_test.shape[0]} samples")
            else:
                X_test = X_train
                y_test = y_train
                logger.warning("No test data provided, using training data for evaluation")

            # Get dimensions from train data
            n_windows, window_size, n_sensors = X_train.shape
            logger.info(f"Train windows shape: {X_train.shape}")
        else:
            # Split data automatically (stratified)
            logger.info(f"Using automatic train/test split ({config.test_size*100:.0f}% test)")
            logger.info(f"Windows shape: {windows.shape}")

            # Get dimensions
            n_windows, window_size, n_sensors = windows.shape

            # Encode labels
            self.label_encoder = LabelEncoder()
            y = self.label_encoder.fit_transform(labels)
            self.class_names = self.label_encoder.classes_.tolist()
            n_classes = len(self.class_names)

            X_train, X_test, y_train, y_test = train_test_split(
                windows, y, test_size=config.test_size,
                random_state=config.random_state, stratify=y
            )

        logger.info(f"Detected {n_classes} classes: {self.class_names}")

        # Create model
        # Extract period configuration if provided
        fixed_periods = config.params.get('fixed_periods', None)
        if fixed_periods:
            logger.info(f"Using custom period configuration: {fixed_periods}")

        self.model, self.device, self.device_desc = create_timesnet_for_classification(
            seq_len=window_size,
            n_sensors=n_sensors,
            n_classes=n_classes,
            device=config.device,
            complexity=config.complexity,
            fixed_periods=fixed_periods
        )

        # Report to user
        logger.info(f"🖥️  Training Device: {self.device_desc}")
        logger.info(f"Model has {self.model.count_parameters():,} parameters")

        # Convert to PyTorch tensors
        X_train_tensor = torch.FloatTensor(X_train).to(self.device)
        y_train_tensor = torch.LongTensor(y_train).to(self.device)
        X_test_tensor = torch.FloatTensor(X_test).to(self.device)
        y_test_tensor = torch.LongTensor(y_test).to(self.device)

        # Create data loaders
        train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
        train_loader = DataLoader(
            train_dataset,
            batch_size=config.batch_size,
            shuffle=True
        )

        # Loss and optimizer
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(self.model.parameters(), lr=config.learning_rate)

        # Training loop
        logger.info(f"Starting training for {config.epochs} epochs...")

        history = {
            'train_loss': [],
            'train_acc': [],
            'val_loss': [],
            'val_acc': []
        }

        best_val_acc = 0.0
        patience_counter = 0

        for epoch in range(config.epochs):
            # Training phase
            self.model.train()
            train_loss = 0.0
            train_correct = 0
            train_total = 0

            pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{config.epochs}")
            for batch_x, batch_y in pbar:
                # Forward pass
                outputs = self.model(batch_x)
                loss = criterion(outputs, batch_y)

                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                # Metrics
                train_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                train_total += batch_y.size(0)
                train_correct += (predicted == batch_y).sum().item()

                pbar.set_postfix({
                    'loss': f'{loss.item():.4f}',
                    'acc': f'{100 * train_correct / train_total:.2f}%'
                })

            # Calculate epoch metrics
            epoch_train_loss = train_loss / len(train_loader)
            epoch_train_acc = train_correct / train_total

            # Validation phase
            self.model.eval()
            with torch.no_grad():
                val_outputs = self.model(X_test_tensor)
                val_loss = criterion(val_outputs, y_test_tensor).item()
                _, val_predicted = torch.max(val_outputs.data, 1)
                val_acc = (val_predicted == y_test_tensor).sum().item() / len(y_test_tensor)

            # Record history
            history['train_loss'].append(epoch_train_loss)
            history['train_acc'].append(epoch_train_acc)
            history['val_loss'].append(val_loss)
            history['val_acc'].append(val_acc)

            logger.info(
                f"Epoch {epoch+1}/{config.epochs} - "
                f"Train Loss: {epoch_train_loss:.4f}, Train Acc: {epoch_train_acc:.4f}, "
                f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}"
            )

            # Call progress callback if provided
            if progress_callback:
                progress_callback({
                    'epoch': epoch + 1,
                    'total_epochs': config.epochs,
                    'train_loss': epoch_train_loss,
                    'train_acc': epoch_train_acc,
                    'val_loss': val_loss,
                    'val_acc': val_acc
                })

            # Early stopping
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= config.patience:
                    logger.info(f"Early stopping triggered after {epoch+1} epochs")
                    break

        # Final evaluation
        self.model.eval()
        with torch.no_grad():
            test_outputs = self.model(X_test_tensor)
            _, y_pred = torch.max(test_outputs.data, 1)

        # Convert to numpy for sklearn metrics
        y_pred = y_pred.cpu().numpy()
        y_test = y_test_tensor.cpu().numpy()

        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision_macro = precision_score(y_test, y_pred, average='macro')
        recall_macro = recall_score(y_test, y_pred, average='macro')
        f1_macro = f1_score(y_test, y_pred, average='macro')

        # Per-class metrics
        precision_per_class = precision_score(y_test, y_pred, average=None)
        recall_per_class = recall_score(y_test, y_pred, average=None)
        f1_per_class = f1_score(y_test, y_pred, average=None)

        per_class_precision = {self.class_names[i]: float(precision_per_class[i]) for i in range(n_classes)}
        per_class_recall = {self.class_names[i]: float(recall_per_class[i]) for i in range(n_classes)}
        per_class_f1 = {self.class_names[i]: float(f1_per_class[i]) for i in range(n_classes)}

        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)

        # Save model and encoder
        output_dir.mkdir(parents=True, exist_ok=True)
        model_path = output_dir / f"{config.algorithm}_model.pth"
        encoder_path = output_dir / f"{config.algorithm}_encoder.pkl"
        onnx_path = output_dir / f"{config.algorithm}_model.onnx"

        # Save PyTorch model
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'model_config': self.model.config,
            'class_names': self.class_names
        }, model_path)
        logger.info(f"Model saved to {model_path}")

        # Save label encoder
        with open(encoder_path, 'wb') as f:
            pickle.dump(self.label_encoder, f)
        logger.info(f"Label encoder saved to {encoder_path}")

        # Export to ONNX
        onnx_exported = self._export_to_onnx(
            X_test_tensor[:1],  # Sample input
            onnx_path
        )

        # Create results object
        results = TimeSeriesResults(
            algorithm=config.algorithm,
            model_path=str(model_path),
            label_encoder_path=str(encoder_path),
            onnx_model_path=str(onnx_path) if onnx_exported else None,
            device_used=self.device_desc,
            train_samples=len(X_train),
            test_samples=len(X_test),
            window_size=window_size,
            n_sensors=n_sensors,
            n_classes=n_classes,
            class_names=self.class_names,
            accuracy=float(accuracy),
            precision_macro=float(precision_macro),
            recall_macro=float(recall_macro),
            f1_macro=float(f1_macro),
            per_class_precision=per_class_precision,
            per_class_recall=per_class_recall,
            per_class_f1=per_class_f1,
            confusion_matrix=cm.tolist(),
            training_history=history,
            model_params=self.model.get_model_info(),
            total_parameters=self.model.count_parameters()
        )

        logger.info(f"Training Results - Accuracy: {accuracy:.3f}, "
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

    def _export_to_onnx(self, sample_input: torch.Tensor, onnx_path: Path) -> bool:
        """
        Export model to ONNX format for TensorRT deployment.

        Args:
            sample_input: Sample input tensor
            onnx_path: Path to save ONNX model

        Returns:
            True if export successful, False otherwise
        """
        try:
            self.model.eval()
            torch.onnx.export(
                self.model,
                sample_input,
                onnx_path,
                export_params=True,
                opset_version=11,
                do_constant_folding=True,
                input_names=['input'],
                output_names=['output'],
                dynamic_axes={
                    'input': {0: 'batch_size'},
                    'output': {0: 'batch_size'}
                }
            )
            logger.info(f"ONNX model exported to {onnx_path}")
            return True
        except Exception as e:
            logger.warning(f"Failed to export ONNX model: {e}")
            return False

    def predict(self, windows: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict classes on new windowed data.

        Args:
            windows: Windowed sensor data (n_windows, window_size, n_sensors)

        Returns:
            Tuple of (predictions, probabilities)
            - predictions: Class labels (decoded strings)
            - probabilities: Probability matrix (n_samples, n_classes)
        """
        if self.model is None:
            raise ValueError("Model not trained yet")

        self.model.eval()

        # Convert to tensor
        X_tensor = torch.FloatTensor(windows).to(self.device)

        # Predict
        with torch.no_grad():
            outputs = self.model(X_tensor)
            probabilities = torch.softmax(outputs, dim=1)
            _, predicted_indices = torch.max(outputs, 1)

        # Convert to numpy
        predicted_indices = predicted_indices.cpu().numpy()
        probabilities = probabilities.cpu().numpy()

        # Decode labels
        predictions = self.label_encoder.inverse_transform(predicted_indices)

        return predictions, probabilities

    def load_model(self, model_path: Path, encoder_path: Optional[Path] = None):
        """Load a trained model and label encoder."""
        checkpoint = torch.load(model_path, map_location='cpu')

        # Recreate model from config
        config = checkpoint['model_config']
        self.model = TimesNet(config)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.class_names = checkpoint['class_names']

        # Get device
        self.device, self.device_desc = TimesNet.get_device(config.device)
        self.model = self.model.to(self.device)
        self.model.eval()

        logger.info(f"Model loaded from {model_path}")
        logger.info(f"Device: {self.device_desc}")

        if encoder_path and encoder_path.exists():
            with open(encoder_path, 'rb') as f:
                self.label_encoder = pickle.load(f)
            logger.info(f"Label encoder loaded from {encoder_path}")

    @staticmethod
    def get_available_models() -> Dict[str, dict]:
        """Get dictionary of available deep learning models."""
        return {
            'timesnet': {
                'name': 'TimesNet',
                'description': 'Temporal 2D-variation modeling for time series',
                'recommended_for': 'Complex temporal patterns, periodic sensor data',
                'complexity_levels': ['minimal', 'efficient', 'comprehensive']
            }
        }

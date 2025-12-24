"""
TimesNet Model Implementation

Temporal pattern recognition for time series classification.
Adapted from: https://github.com/thuml/Time-Series-Library/blob/main/models/TimesNet.py

Key features:
- FFT-based period detection
- Multi-scale feature extraction via Inception blocks
- GPU/CPU auto-detection with device reporting
"""

import torch
import torch.nn as nn
from dataclasses import dataclass
from typing import Optional, Literal, List
from loguru import logger

from .layers import DataEmbedding, TimesBlock


@dataclass
class TimesNetConfig:
    """Configuration for TimesNet model."""

    # Data dimensions
    seq_len: int = 100  # Window size
    c_in: int = 3  # Number of input channels (sensors)
    num_classes: int = 2  # Number of output classes

    # Model architecture
    d_model: int = 32  # Model dimension (reduced for CPU efficiency)
    d_ff: int = 64  # Feedforward dimension
    num_kernels: int = 4  # Number of Inception kernel sizes
    top_k: int = 3  # Top-k frequencies to keep
    e_layers: int = 2  # Number of TimesNet blocks

    # Training
    dropout: float = 0.1
    device: str = 'auto'  # 'auto', 'cpu', or 'cuda'

    # Task type
    task: Literal['classification', 'anomaly_detection'] = 'classification'

    # Period configuration (for ONNX compatibility)
    fixed_periods: Optional[List[int]] = None


class TimesNet(nn.Module):
    """
    TimesNet model for time series classification.

    Processes windowed sensor data using temporal 2D-variation modeling.
    """

    def __init__(self, config: TimesNetConfig):
        """
        Initialize TimesNet model.

        Args:
            config: Model configuration
        """
        super(TimesNet, self).__init__()

        self.config = config
        self.task = config.task
        self.seq_len = config.seq_len

        # Embedding layer
        self.enc_embedding = DataEmbedding(
            config.c_in,
            config.d_model,
            config.dropout
        )

        # Stack of TimesNet blocks
        self.layers = nn.ModuleList([
            TimesBlock(
                config.seq_len,
                config.d_model,
                config.d_ff,
                config.num_kernels,
                config.top_k,
                fixed_periods=config.fixed_periods
            )
            for _ in range(config.e_layers)
        ])

        self.layer_norm = nn.LayerNorm(config.d_model)

        # Classification head
        if config.task == 'classification':
            self.projection = nn.Linear(
                config.d_model * config.seq_len,
                config.num_classes
            )
        elif config.task == 'anomaly_detection':
            # Binary classification for anomaly detection
            self.projection = nn.Linear(
                config.d_model * config.seq_len,
                1
            )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input tensor (batch_size, seq_len, c_in)

        Returns:
            Class logits (batch_size, num_classes) for classification
            or anomaly scores (batch_size, 1) for anomaly detection
        """
        # Embedding
        enc_out = self.enc_embedding(x)

        # Pass through TimesNet blocks
        for layer in self.layers:
            enc_out = layer(enc_out)

        # Normalize
        enc_out = self.layer_norm(enc_out)

        # Flatten for classification
        enc_out = enc_out.reshape(enc_out.shape[0], -1)

        # Project to class logits
        output = self.projection(enc_out)

        return output

    @staticmethod
    def get_device(device_preference: str = 'auto') -> tuple[torch.device, str]:
        """
        Auto-detect and configure device (GPU/CPU).

        Args:
            device_preference: 'auto', 'cpu', or 'cuda'

        Returns:
            Tuple of (torch.device, description string)
        """
        if device_preference == 'cpu':
            device = torch.device('cpu')
            desc = "CPU (forced by user)"
            logger.info(f"Using {desc}")
            return device, desc

        if device_preference == 'cuda':
            if torch.cuda.is_available():
                device = torch.device('cuda')
                gpu_name = torch.cuda.get_device_name(0)
                desc = f"GPU: {gpu_name}"
                logger.info(f"Using {desc}")
                return device, desc
            else:
                logger.warning("CUDA requested but not available, falling back to CPU")
                device = torch.device('cpu')
                desc = "CPU (CUDA not available)"
                return device, desc

        # Auto-detection
        if torch.cuda.is_available():
            device = torch.device('cuda')
            gpu_name = torch.cuda.get_device_name(0)
            desc = f"GPU: {gpu_name}"
            logger.info(f"Auto-detected and using {desc}")

            # Report GPU memory
            gpu_mem_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
            logger.info(f"GPU memory: {gpu_mem_gb:.1f} GB")
        else:
            device = torch.device('cpu')
            cpu_count = torch.get_num_threads()
            desc = f"CPU ({cpu_count} threads)"
            logger.info(f"No GPU detected, using {desc}")

        return device, desc

    def count_parameters(self) -> int:
        """Count trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def get_model_info(self) -> dict:
        """Get model information for logging."""
        return {
            'architecture': 'TimesNet',
            'seq_len': self.config.seq_len,
            'input_channels': self.config.c_in,
            'num_classes': self.config.num_classes,
            'd_model': self.config.d_model,
            'd_ff': self.config.d_ff,
            'num_kernels': self.config.num_kernels,
            'top_k': self.config.top_k,
            'num_layers': self.config.e_layers,
            'total_parameters': self.count_parameters(),
            'task': self.task
        }


def create_timesnet_for_classification(
    seq_len: int,
    n_sensors: int,
    n_classes: int,
    device: str = 'auto',
    complexity: str = 'efficient',
    fixed_periods: Optional[List[int]] = None
) -> tuple[TimesNet, torch.device, str]:
    """
    Factory function to create TimesNet for classification.

    Args:
        seq_len: Window size
        n_sensors: Number of sensor channels
        n_classes: Number of classes
        device: 'auto', 'cpu', or 'cuda'
        complexity: 'minimal', 'efficient', or 'comprehensive'
        fixed_periods: Optional list of fixed periods for ONNX compatibility

    Returns:
        Tuple of (model, device, device_description)
    """
    # Configuration based on complexity
    configs = {
        'minimal': {
            'd_model': 16,
            'd_ff': 32,
            'num_kernels': 2,
            'top_k': 2,
            'e_layers': 1
        },
        'efficient': {
            'd_model': 32,
            'd_ff': 64,
            'num_kernels': 4,
            'top_k': 3,
            'e_layers': 2
        },
        'comprehensive': {
            'd_model': 64,
            'd_ff': 128,
            'num_kernels': 6,
            'top_k': 5,
            'e_layers': 3
        }
    }

    params = configs.get(complexity, configs['efficient'])

    config = TimesNetConfig(
        seq_len=seq_len,
        c_in=n_sensors,
        num_classes=n_classes,
        task='classification',
        device=device,
        fixed_periods=fixed_periods,
        **params
    )

    # Create model
    model = TimesNet(config)

    # Get device
    device_obj, device_desc = TimesNet.get_device(device)

    # Move model to device
    model = model.to(device_obj)

    logger.info(f"Created TimesNet model with {model.count_parameters():,} parameters")
    logger.info(f"Configuration: {complexity}")
    logger.info(f"Device: {device_desc}")

    return model, device_obj, device_desc

"""
Neural Network Layers for TimesNet

Implements embedding layers and Inception blocks adapted from:
https://github.com/thuml/Time-Series-Library/blob/main/models/TimesNet.py
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional


class DataEmbedding(nn.Module):
    """
    Time series data embedding with positional encoding.

    Combines value embedding with optional positional information.
    """

    def __init__(self, c_in: int, d_model: int, dropout: float = 0.1):
        """
        Args:
            c_in: Number of input channels (sensors)
            d_model: Dimension of model embeddings
            dropout: Dropout rate
        """
        super(DataEmbedding, self).__init__()

        self.value_embedding = nn.Linear(c_in, d_model)
        self.dropout = nn.Dropout(p=dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Input tensor (batch_size, seq_len, n_features)

        Returns:
            Embedded tensor (batch_size, seq_len, d_model)
        """
        x = self.value_embedding(x)
        return self.dropout(x)


class Inception_Block_V1(nn.Module):
    """
    Inception block for feature extraction.

    Uses multiple kernel sizes to capture patterns at different scales.
    Adapted from TimesNet architecture.
    """

    def __init__(self, in_channels: int, out_channels: int, num_kernels: int = 6):
        """
        Args:
            in_channels: Number of input channels
            out_channels: Number of output channels
            num_kernels: Number of different kernel sizes to use
        """
        super(Inception_Block_V1, self).__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.num_kernels = num_kernels

        # Create multiple convolutional layers with different kernel sizes
        kernels = []
        for i in range(num_kernels):
            # Kernel sizes: 1, 3, 5, 7, 9, 11, ...
            kernel_size = 2 * i + 1
            padding = kernel_size // 2

            kernels.append(
                nn.Conv2d(
                    in_channels,
                    out_channels,
                    kernel_size=kernel_size,
                    padding=padding
                )
            )

        self.kernels = nn.ModuleList(kernels)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Input tensor (batch_size, in_channels, height, width)

        Returns:
            Aggregated features (batch_size, out_channels, height, width)
        """
        # Apply all kernel sizes and average the results
        res_list = []
        for kernel in self.kernels:
            res_list.append(kernel(x))

        # Average across different kernel sizes
        res = torch.stack(res_list, dim=-1).mean(-1)

        return res


class TimesBlock(nn.Module):
    """
    Core TimesNet block for temporal pattern extraction.

    Uses FFT to identify periodic components and processes them
    with Inception blocks in 2D space.
    """

    def __init__(
        self,
        seq_len: int,
        d_model: int,
        d_ff: int,
        num_kernels: int = 6,
        top_k: int = 5
    ):
        """
        Args:
            seq_len: Length of input sequence
            d_model: Model dimension
            d_ff: Feedforward dimension
            num_kernels: Number of Inception kernel sizes
            top_k: Number of top frequencies to keep
        """
        super(TimesBlock, self).__init__()

        self.seq_len = seq_len
        self.d_model = d_model
        self.d_ff = d_ff
        self.top_k = top_k

        # Parameter for learning period weights
        self.conv = nn.Sequential(
            Inception_Block_V1(d_model, d_ff, num_kernels=num_kernels),
            nn.GELU(),
            Inception_Block_V1(d_ff, d_model, num_kernels=num_kernels)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Input tensor (batch_size, seq_len, d_model)

        Returns:
            Processed tensor with temporal patterns (batch_size, seq_len, d_model)
        """
        B, T, N = x.size()

        # Period detection using FFT
        # Apply FFT along sequence dimension
        x_freq = torch.fft.rfft(x, dim=1)

        # Get amplitude spectrum
        freq_amp = torch.abs(x_freq)
        freq_amp = freq_amp.mean(dim=-1)  # Average across features

        # Select top-k frequencies
        _, top_indices = torch.topk(freq_amp, self.top_k, dim=1)
        top_indices = top_indices.detach().cpu().numpy()

        # Initialize output
        res = torch.zeros_like(x)

        # Process each period component
        for i in range(B):
            for j in range(self.top_k):
                # Get period length
                freq_idx = top_indices[i, j]
                if freq_idx == 0:
                    period = self.seq_len
                else:
                    period = self.seq_len // freq_idx

                # Ensure valid period
                period = max(period, 2)

                # Reshape to 2D based on period
                length = (T // period) * period
                if length > 0:
                    padding = T - length

                    # Extract periodic component
                    x_period = x[i:i+1, :length, :]
                    x_period = x_period.reshape(1, T // period, period, N)
                    x_period = x_period.permute(0, 3, 1, 2).contiguous()

                    # Apply Inception block
                    x_period = self.conv(x_period)

                    # Reshape back
                    x_period = x_period.permute(0, 2, 3, 1).contiguous()
                    x_period = x_period.reshape(1, length, N)

                    # Pad if necessary
                    if padding > 0:
                        x_period = F.pad(x_period, (0, 0, 0, padding))

                    res[i:i+1] += x_period

        # Average across top-k periods
        res = res / self.top_k

        # Residual connection
        res = res + x

        return res

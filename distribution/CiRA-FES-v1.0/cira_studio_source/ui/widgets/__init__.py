"""
Visualization Widgets

Custom matplotlib-based widgets for data visualization in CiRA Studio.
"""

from .sensor_plot import SensorPlotWidget
from .class_distribution import ClassDistributionChart
from .windowing_viz import WindowingVisualization
from .confusion_matrix import ConfusionMatrixWidget
from .feature_importance import FeatureImportanceChart

__all__ = [
    'SensorPlotWidget',
    'ClassDistributionChart',
    'WindowingVisualization',
    'ConfusionMatrixWidget',
    'FeatureImportanceChart'
]

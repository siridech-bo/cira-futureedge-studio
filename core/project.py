"""
Project Management

Handles project creation, loading, saving, and state management.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from loguru import logger


@dataclass
class ProjectData:
    """Data ingestion stage configuration."""
    source_type: str = "csv"  # "csv", "database", "api", "stream"
    source_path: Optional[str] = None
    window_size: int = 100
    sampling_rate: float = 50.0
    overlap: float = 0.0
    labels: Dict[str, int] = field(default_factory=lambda: {"nominal": 0, "off": 1, "anomaly": 2})
    sensor_columns: List[str] = field(default_factory=list)
    data_file: Optional[str] = None  # Path to processed data
    windows_file: Optional[str] = None  # Path to saved windows
    num_windows: int = 0  # Number of windows created
    time_column: Optional[str] = None  # Detected time column

    # Classification mode fields (NEW)
    task_type: str = "anomaly_detection"  # "anomaly_detection" or "classification"
    class_mapping: Dict[str, int] = field(default_factory=dict)  # {"idle": 0, "snake": 1, "ingestion": 2}
    num_classes: int = 0  # Number of classes detected
    class_distribution: Dict[str, int] = field(default_factory=dict)  # {"idle": 450, "snake": 320}
    label_extraction_enabled: bool = False  # Whether to extract labels from filenames
    label_pattern: str = "prefix"  # "prefix", "suffix", "folder", "regex"
    window_labels: Optional[List[str]] = None  # Class label for each window


@dataclass
class ProjectFeatures:
    """Feature extraction stage configuration."""
    # Legacy fields (keep for compatibility)
    tsfresh_enabled: bool = True
    pysr_enabled: bool = False
    custom_dsp_enabled: bool = True
    feature_set: str = "comprehensive"  # "minimal", "efficient", "comprehensive"

    # New Phase 3 fields
    extracted: bool = False  # Whether features have been extracted
    feature_names: List[str] = field(default_factory=list)  # List of feature names
    operation_mode: str = "anomaly_detection"  # "anomaly_detection" or "forecasting"
    complexity_level: str = "efficient"  # "minimal", "efficient", "comprehensive"
    configuration_mode: str = "simple"  # "simple", "advanced", "per_sensor"

    # File paths
    extracted_features: Optional[str] = None  # Path to feature matrix
    filtered_features: Optional[str] = None  # Path to filtered features
    feature_config: Optional[str] = None  # Path to feature extraction config

    # Statistics
    num_features_extracted: int = 0
    num_features_selected: int = 0

    # Legacy
    candidate_features: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ProjectLLM:
    """LLM feature selection stage configuration."""
    model_name: str = "Llama-3.2-3B-Instruct-Q4_K_M.gguf"
    use_llm: bool = True
    selected_features: List[str] = field(default_factory=list)  # List of feature names
    num_selected: int = 0  # Number of features selected
    selection_reasoning: str = ""  # Reasoning for selection
    used_llm: bool = False  # Whether LLM was actually used
    fallback_used: bool = False  # Whether fallback was used

    # Legacy fields (keep for compatibility)
    llm_reasoning: str = ""


@dataclass
class ProjectModel:
    """Anomaly model training stage configuration."""
    algorithm: str = "iforest"  # PyOD algorithm name or classifier name
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    model_path: Optional[str] = None  # Path to trained model pickle
    scaler_path: Optional[str] = None  # Path to scaler pickle
    trained: bool = False
    model_params: Dict[str, Any] = field(default_factory=dict)

    # Legacy fields (keep for compatibility)
    model_file: Optional[str] = None

    # Classification mode fields (NEW)
    model_type: str = "anomaly"  # "anomaly" or "classifier"
    num_classes: int = 0  # Number of classes (for classification)
    class_names: List[str] = field(default_factory=list)  # ["idle", "snake", "ingestion"]
    label_encoder_path: Optional[str] = None  # Path to label encoder pickle
    confusion_matrix: Optional[List[List[int]]] = None  # Confusion matrix
    per_class_metrics: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # e.g., {"idle": {"precision": 0.95, "recall": 0.92, "f1": 0.93}}


@dataclass
class ProjectBuild:
    """Build stage configuration."""
    target_platform: str = "x86"  # "x86", "cortex-m4", "esp32"
    build_type: str = "Release"
    output_dir: Optional[str] = None
    firmware_file: Optional[str] = None


@dataclass
class Project:
    """Complete project state."""

    # Metadata
    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Untitled Project"
    domain: str = "rotating_machinery"  # "rotating_machinery", "thermal_systems", "custom"
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "1.0.0"

    # Project path
    project_path: Optional[str] = None

    # Stage configurations
    data: ProjectData = field(default_factory=ProjectData)
    features: ProjectFeatures = field(default_factory=ProjectFeatures)
    llm: ProjectLLM = field(default_factory=ProjectLLM)
    model: ProjectModel = field(default_factory=ProjectModel)
    build: ProjectBuild = field(default_factory=ProjectBuild)

    # Progress tracking
    current_stage: str = "data"  # "data", "features", "llm", "model", "dsp", "build"
    completed_stages: List[str] = field(default_factory=list)

    def save(self, path: Optional[Path] = None) -> None:
        """Save project to .ciraproject file."""
        if path is None:
            if self.project_path is None:
                raise ValueError("No project path specified")
            path = Path(self.project_path)

        # Update modified timestamp
        self.modified_at = datetime.now().isoformat()

        # Convert to dictionary
        project_dict = asdict(self)

        # Save to JSON
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(project_dict, f, indent=2)

        self.project_path = str(path)
        logger.info(f"Project saved to {path}")

    @classmethod
    def load(cls, path: Path) -> 'Project':
        """Load project from .ciraproject file."""
        if not path.exists():
            raise FileNotFoundError(f"Project file not found: {path}")

        with open(path, 'r') as f:
            project_dict = json.load(f)

        # Reconstruct nested dataclasses
        if 'data' in project_dict:
            project_dict['data'] = ProjectData(**project_dict['data'])
        if 'features' in project_dict:
            project_dict['features'] = ProjectFeatures(**project_dict['features'])
        if 'llm' in project_dict:
            project_dict['llm'] = ProjectLLM(**project_dict['llm'])
        if 'model' in project_dict:
            project_dict['model'] = ProjectModel(**project_dict['model'])
        if 'build' in project_dict:
            project_dict['build'] = ProjectBuild(**project_dict['build'])

        project = cls(**project_dict)
        logger.info(f"Project loaded from {path}")
        return project

    @classmethod
    def create_new(cls, name: str, domain: str, workspace_dir: Path) -> 'Project':
        """Create a new project."""
        project = cls(name=name, domain=domain)

        # Set default project path
        project_dir = workspace_dir / name.replace(" ", "_")
        project_dir.mkdir(parents=True, exist_ok=True)
        project.project_path = str(project_dir / f"{project.name}.ciraproject")

        logger.info(f"New project created: {name} in {project_dir}")
        return project

    def mark_stage_completed(self, stage: str) -> None:
        """Mark a stage as completed."""
        if stage not in self.completed_stages:
            self.completed_stages.append(stage)
            logger.info(f"Stage '{stage}' marked as completed")

    def get_project_dir(self) -> Path:
        """Get project directory path."""
        if self.project_path is None:
            raise ValueError("Project has no path")
        return Path(self.project_path).parent

    def get_data_dir(self) -> Path:
        """Get data directory for this project."""
        data_dir = self.get_project_dir() / "data"
        data_dir.mkdir(exist_ok=True)
        return data_dir

    def get_models_dir(self) -> Path:
        """Get models directory for this project."""
        models_dir = self.get_project_dir() / "models"
        models_dir.mkdir(exist_ok=True)
        return models_dir

    def get_output_dir(self) -> Path:
        """Get output directory for this project."""
        output_dir = self.get_project_dir() / "output"
        output_dir.mkdir(exist_ok=True)
        return output_dir

    def get_data_dir(self) -> Path:
        """Get data directory for this project."""
        data_dir = self.get_project_dir() / "data"
        data_dir.mkdir(exist_ok=True)
        return data_dir

    def get_features_dir(self) -> Path:
        """Get features directory for this project."""
        features_dir = self.get_project_dir() / "features"
        features_dir.mkdir(exist_ok=True)
        return features_dir

    def save_windows(self, windows: List, sensor_columns: List[str], time_column: Optional[str] = None) -> None:
        """
        Save windows to disk.

        Args:
            windows: List of Window objects
            sensor_columns: List of sensor column names
            time_column: Name of time column
        """
        import pickle

        data_dir = self.get_data_dir()
        windows_file = data_dir / "windows.pkl"

        # Save windows
        with open(windows_file, 'wb') as f:
            pickle.dump(windows, f)

        # Extract class labels if in classification mode
        class_labels = []
        class_distribution = {}

        for window in windows:
            if window.class_label is not None:
                class_labels.append(window.class_label)
                class_distribution[window.class_label] = \
                    class_distribution.get(window.class_label, 0) + 1

        # Update project data
        self.data.windows_file = str(windows_file)
        self.data.num_windows = len(windows)
        self.data.sensor_columns = sensor_columns
        self.data.time_column = time_column

        # Save classification mode data if available
        if class_labels:
            self.data.window_labels = class_labels
            self.data.class_distribution = class_distribution
            self.data.task_type = "classification"
            logger.info(f"Saved {len(windows)} windows with class labels: {class_distribution}")
        else:
            logger.info(f"Saved {len(windows)} windows to {windows_file}")

    def load_windows(self) -> Optional[List]:
        """
        Load windows from disk.

        Returns:
            List of Window objects or None if not found
        """
        import pickle

        if not self.data.windows_file:
            logger.warning("No windows file path in project")
            return None

        windows_path = Path(self.data.windows_file)
        if not windows_path.exists():
            logger.warning(f"Windows file not found: {windows_path}")
            return None

        try:
            with open(windows_path, 'rb') as f:
                windows = pickle.load(f)

            logger.info(f"Loaded {len(windows)} windows from {windows_path}")
            return windows

        except Exception as e:
            logger.error(f"Failed to load windows: {e}")
            return None

    def is_stage_completed(self, stage: str) -> bool:
        """Check if a stage is completed."""
        return stage in self.completed_stages

    def get_domain_description(self) -> str:
        """Get human-readable domain description."""
        domains = {
            "rotating_machinery": "Rotating Machinery (motors, pumps, bearings)",
            "thermal_systems": "Thermal Systems (heating, cooling, temperature monitoring)",
            "electrical": "Electrical Systems (power, current, voltage)",
            "custom": "Custom Domain"
        }
        return domains.get(self.domain, "Unknown Domain")


class ProjectManager:
    """Manages project lifecycle."""

    def __init__(self):
        self.current_project: Optional[Project] = None

    def new_project(self, name: str, domain: str, workspace_dir: Path) -> Project:
        """Create a new project."""
        self.current_project = Project.create_new(name, domain, workspace_dir)
        return self.current_project

    def open_project(self, path: Path) -> Project:
        """Open an existing project."""
        self.current_project = Project.load(path)
        return self.current_project

    def save_project(self, path: Optional[Path] = None) -> None:
        """Save current project."""
        if self.current_project is None:
            raise ValueError("No project is currently open")
        self.current_project.save(path)

    def close_project(self) -> None:
        """Close current project."""
        if self.current_project is not None:
            logger.info(f"Closing project: {self.current_project.name}")
            self.current_project = None

    def has_project(self) -> bool:
        """Check if a project is currently open."""
        return self.current_project is not None

    def get_project(self) -> Optional[Project]:
        """Get current project."""
        return self.current_project

"""
Data Sources Panel

UI for data ingestion, windowing, and visualization.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Optional, List
import pandas as pd
from loguru import logger

from core.project import ProjectManager
from core.windowing import WindowingEngine, WindowConfig
from data_sources.base import DataSourceConfig, DataSourceFactory
from data_sources.csv_loader import CSVDataSource
from data_sources.edgeimpulse_loader import EdgeImpulseDataSource
from data_sources.database_loader import DatabaseDataSource
from data_sources.restapi_loader import RestAPIDataSource
from data_sources.streaming_loader import StreamingDataSource
from ui.widgets.sensor_plot import SensorPlotWidget


class DataSourcesPanel(ctk.CTkFrame):
    """Panel for data source management and ingestion."""

    def __init__(self, parent, project_manager: ProjectManager, **kwargs):
        """
        Initialize data sources panel.

        Args:
            parent: Parent widget
            project_manager: Project manager instance
        """
        super().__init__(parent, **kwargs)

        self.project_manager = project_manager
        self.current_data_source: Optional[CSVDataSource] = None
        self.windowing_engine: Optional[WindowingEngine] = None
        self.loaded_data: Optional[pd.DataFrame] = None

        self._setup_ui()
        self._load_project_data()  # Load existing data if available

    def _setup_ui(self) -> None:
        """Setup UI components."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        title = ctk.CTkLabel(
            header,
            text="📊 Data Sources",
            font=("Segoe UI", 24, "bold")
        )
        title.pack(side="left")

        # Main content area with tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

        # Add tabs
        self.tabview.add("Load Data")
        self.tabview.add("Windowing")
        self.tabview.add("Preview")

        # Setup each tab
        self._setup_load_tab()
        self._setup_windowing_tab()
        self._setup_preview_tab()

    def _setup_load_tab(self) -> None:
        """Setup data loading tab."""
        tab = self.tabview.tab("Load Data")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        # Create scrollable frame for all content
        scrollable_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scrollable_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        scrollable_frame.grid_columnconfigure(0, weight=1)

        # Task Mode selection (NEW - Classification vs Anomaly Detection)
        task_mode_frame = ctk.CTkFrame(scrollable_frame, fg_color=("gray90", "gray20"))
        task_mode_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        task_mode_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            task_mode_frame,
            text="🎯 Task Mode:",
            font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.task_mode_var = ctk.StringVar(value="anomaly_detection")
        task_mode_selector = ctk.CTkSegmentedButton(
            task_mode_frame,
            variable=self.task_mode_var,
            values=["Anomaly Detection", "Classification"],
            command=self._on_task_mode_change
        )
        task_mode_selector.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # Info label for task mode
        self.task_mode_info = ctk.CTkLabel(
            task_mode_frame,
            text="ℹ️ Detects unusual patterns in unlabeled data",
            font=("Segoe UI", 10),
            text_color=("gray50", "gray60")
        )
        self.task_mode_info.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")

        # Pipeline Mode selection (ML vs DL) - Phase 3
        pipeline_mode_frame = ctk.CTkFrame(scrollable_frame, fg_color=("gray90", "gray20"))
        pipeline_mode_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        pipeline_mode_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            pipeline_mode_frame,
            text="🧮 Pipeline Mode:",
            font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.pipeline_mode_var = ctk.StringVar(value="ml")
        pipeline_mode_selector = ctk.CTkSegmentedButton(
            pipeline_mode_frame,
            variable=self.pipeline_mode_var,
            values=["Traditional ML", "Deep Learning"],
            command=self._on_pipeline_mode_change
        )
        pipeline_mode_selector.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # Info label for pipeline mode
        self.pipeline_mode_info = ctk.CTkLabel(
            pipeline_mode_frame,
            text="ℹ️ Feature extraction + sklearn/PyOD models",
            font=("Segoe UI", 10),
            text_color=("gray50", "gray60")
        )
        self.pipeline_mode_info.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")

        # Warning label (shown when mode is locked)
        self.pipeline_mode_warning = ctk.CTkLabel(
            pipeline_mode_frame,
            text="⚠️ Pipeline mode is locked after data processing starts",
            font=("Segoe UI", 10, "bold"),
            text_color="orange"
        )
        # Hidden by default, shown when locked

        # Data source type selection
        source_frame = ctk.CTkFrame(scrollable_frame)
        source_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        source_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            source_frame,
            text="Data Source Type:",
            font=("Segoe UI", 14)
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.source_type_var = ctk.StringVar(value="csv")
        source_menu = ctk.CTkOptionMenu(
            source_frame,
            variable=self.source_type_var,
            values=["CSV File", "Edge Impulse JSON", "Edge Impulse CBOR", "Database", "REST API", "Streaming"],
            command=self._on_source_type_change
        )
        source_menu.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # CSV-specific options
        self.csv_frame = ctk.CTkFrame(scrollable_frame)
        self.csv_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        self.csv_frame.grid_columnconfigure(1, weight=1)

        # File path
        ctk.CTkLabel(
            self.csv_frame,
            text="CSV File:",
            font=("Segoe UI", 12)
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.file_path_entry = ctk.CTkEntry(
            self.csv_frame,
            placeholder_text="Select CSV file..."
        )
        self.file_path_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        browse_btn = ctk.CTkButton(
            self.csv_frame,
            text="Browse...",
            command=self._browse_csv_file,
            width=100
        )
        browse_btn.grid(row=0, column=2, padx=10, pady=5)

        # Delimiter
        ctk.CTkLabel(
            self.csv_frame,
            text="Delimiter:",
            font=("Segoe UI", 12)
        ).grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.delimiter_var = ctk.StringVar(value=",")
        delimiter_menu = ctk.CTkOptionMenu(
            self.csv_frame,
            variable=self.delimiter_var,
            values=["Comma (,)", "Semicolon (;)", "Tab", "Space"]
        )
        delimiter_menu.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Encoding
        ctk.CTkLabel(
            self.csv_frame,
            text="Encoding:",
            font=("Segoe UI", 12)
        ).grid(row=2, column=0, padx=10, pady=5, sticky="w")

        self.encoding_var = ctk.StringVar(value="utf-8")
        encoding_menu = ctk.CTkOptionMenu(
            self.csv_frame,
            variable=self.encoding_var,
            values=["utf-8", "latin1", "ascii", "utf-16"]
        )
        encoding_menu.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Edge Impulse-specific options
        self.ei_frame = ctk.CTkFrame(scrollable_frame)
        self.ei_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        self.ei_frame.grid_columnconfigure(1, weight=1)
        self.ei_frame.grid_remove()  # Hidden by default

        # Training folder
        ctk.CTkLabel(
            self.ei_frame,
            text="Training Data:",
            font=("Segoe UI", 12, "bold")
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.ei_train_path_entry = ctk.CTkEntry(
            self.ei_frame,
            placeholder_text="Select folder with training files..."
        )
        self.ei_train_path_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        browse_train_btn = ctk.CTkButton(
            self.ei_frame,
            text="Browse Train...",
            command=self._browse_ei_train_folder,
            width=130,
            fg_color="green",
            hover_color="darkgreen"
        )
        browse_train_btn.grid(row=0, column=2, padx=10, pady=5)

        # Test folder
        ctk.CTkLabel(
            self.ei_frame,
            text="Test Data:",
            font=("Segoe UI", 12, "bold")
        ).grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.ei_test_path_entry = ctk.CTkEntry(
            self.ei_frame,
            placeholder_text="Select folder with test files (optional)..."
        )
        self.ei_test_path_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        browse_test_btn = ctk.CTkButton(
            self.ei_frame,
            text="Browse Test...",
            command=self._browse_ei_test_folder,
            width=130,
            fg_color="orange",
            hover_color="darkorange"
        )
        browse_test_btn.grid(row=1, column=2, padx=10, pady=5)

        # Single file option (legacy)
        ctk.CTkLabel(
            self.ei_frame,
            text="Or Single File:",
            font=("Segoe UI", 10),
            text_color="gray"
        ).grid(row=2, column=0, padx=10, pady=5, sticky="w")

        self.ei_file_path_entry = ctk.CTkEntry(
            self.ei_frame,
            placeholder_text="Select single JSON or CBOR file..."
        )
        self.ei_file_path_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        browse_ei_btn = ctk.CTkButton(
            self.ei_frame,
            text="Browse File...",
            command=self._browse_ei_file,
            width=130
        )
        browse_ei_btn.grid(row=2, column=2, padx=10, pady=5)

        # Device info (will be populated after loading)
        self.ei_info_label = ctk.CTkLabel(
            self.ei_frame,
            text="",
            font=("Segoe UI", 10),
            text_color="gray"
        )
        self.ei_info_label.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky="w")

        # Database-specific options
        self.db_frame = ctk.CTkFrame(scrollable_frame)
        self.db_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        self.db_frame.grid_columnconfigure(1, weight=1)
        self.db_frame.grid_remove()  # Hidden by default

        # Database type
        ctk.CTkLabel(
            self.db_frame,
            text="Database Type:",
            font=("Segoe UI", 12)
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.db_type_var = ctk.StringVar(value="postgresql")
        db_type_menu = ctk.CTkOptionMenu(
            self.db_frame,
            variable=self.db_type_var,
            values=["postgresql", "mysql", "sqlite", "sqlserver"],
            command=self._on_db_type_change
        )
        db_type_menu.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Host
        ctk.CTkLabel(
            self.db_frame,
            text="Host:",
            font=("Segoe UI", 12)
        ).grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.db_host_entry = ctk.CTkEntry(
            self.db_frame,
            placeholder_text="localhost"
        )
        self.db_host_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Port
        ctk.CTkLabel(
            self.db_frame,
            text="Port:",
            font=("Segoe UI", 12)
        ).grid(row=2, column=0, padx=10, pady=5, sticky="w")

        self.db_port_entry = ctk.CTkEntry(
            self.db_frame,
            placeholder_text="5432"
        )
        self.db_port_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w", columnspan=1)

        # Database name
        ctk.CTkLabel(
            self.db_frame,
            text="Database:",
            font=("Segoe UI", 12)
        ).grid(row=3, column=0, padx=10, pady=5, sticky="w")

        self.db_name_entry = ctk.CTkEntry(
            self.db_frame,
            placeholder_text="sensor_data"
        )
        self.db_name_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        # Username
        ctk.CTkLabel(
            self.db_frame,
            text="Username:",
            font=("Segoe UI", 12)
        ).grid(row=4, column=0, padx=10, pady=5, sticky="w")

        self.db_username_entry = ctk.CTkEntry(
            self.db_frame,
            placeholder_text="postgres"
        )
        self.db_username_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        # Password
        ctk.CTkLabel(
            self.db_frame,
            text="Password:",
            font=("Segoe UI", 12)
        ).grid(row=5, column=0, padx=10, pady=5, sticky="w")

        self.db_password_entry = ctk.CTkEntry(
            self.db_frame,
            placeholder_text="password",
            show="*"
        )
        self.db_password_entry.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

        # Table/Query
        ctk.CTkLabel(
            self.db_frame,
            text="Table:",
            font=("Segoe UI", 12)
        ).grid(row=6, column=0, padx=10, pady=5, sticky="w")

        self.db_table_entry = ctk.CTkEntry(
            self.db_frame,
            placeholder_text="sensor_readings"
        )
        self.db_table_entry.grid(row=6, column=1, padx=5, pady=5, sticky="ew")

        # Custom query option
        ctk.CTkLabel(
            self.db_frame,
            text="Custom Query (optional):",
            font=("Segoe UI", 12)
        ).grid(row=7, column=0, padx=10, pady=5, sticky="w")

        self.db_query_entry = ctk.CTkEntry(
            self.db_frame,
            placeholder_text="SELECT * FROM sensor_readings WHERE ..."
        )
        self.db_query_entry.grid(row=7, column=1, padx=5, pady=5, sticky="ew")

        # REST API-specific options
        self.api_frame = ctk.CTkFrame(scrollable_frame)
        self.api_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        self.api_frame.grid_columnconfigure(1, weight=1)
        self.api_frame.grid_remove()  # Hidden by default

        # API URL
        ctk.CTkLabel(
            self.api_frame,
            text="API URL:",
            font=("Segoe UI", 12)
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.api_url_entry = ctk.CTkEntry(
            self.api_frame,
            placeholder_text="https://api.example.com/sensors"
        )
        self.api_url_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # HTTP Method
        ctk.CTkLabel(
            self.api_frame,
            text="Method:",
            font=("Segoe UI", 12)
        ).grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.api_method_var = ctk.StringVar(value="GET")
        api_method_menu = ctk.CTkOptionMenu(
            self.api_frame,
            variable=self.api_method_var,
            values=["GET", "POST"]
        )
        api_method_menu.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Authentication type
        ctk.CTkLabel(
            self.api_frame,
            text="Authentication:",
            font=("Segoe UI", 12)
        ).grid(row=2, column=0, padx=10, pady=5, sticky="w")

        self.api_auth_var = ctk.StringVar(value="none")
        api_auth_menu = ctk.CTkOptionMenu(
            self.api_frame,
            variable=self.api_auth_var,
            values=["none", "basic", "bearer", "api_key"],
            command=self._on_api_auth_change
        )
        api_auth_menu.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Auth credentials (shown conditionally)
        self.api_auth_frame = ctk.CTkFrame(self.api_frame, fg_color="transparent")
        self.api_auth_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.api_auth_frame.grid_columnconfigure(1, weight=1)

        # Username (for basic auth)
        self.api_username_label = ctk.CTkLabel(
            self.api_auth_frame,
            text="Username:",
            font=("Segoe UI", 12)
        )
        self.api_username_entry = ctk.CTkEntry(
            self.api_auth_frame,
            placeholder_text="username"
        )

        # Password (for basic auth)
        self.api_password_label = ctk.CTkLabel(
            self.api_auth_frame,
            text="Password:",
            font=("Segoe UI", 12)
        )
        self.api_password_entry = ctk.CTkEntry(
            self.api_auth_frame,
            placeholder_text="password",
            show="*"
        )

        # Token (for bearer auth)
        self.api_token_label = ctk.CTkLabel(
            self.api_auth_frame,
            text="Token:",
            font=("Segoe UI", 12)
        )
        self.api_token_entry = ctk.CTkEntry(
            self.api_auth_frame,
            placeholder_text="your_bearer_token"
        )

        # API Key
        self.api_key_label = ctk.CTkLabel(
            self.api_auth_frame,
            text="API Key:",
            font=("Segoe UI", 12)
        )
        self.api_key_entry = ctk.CTkEntry(
            self.api_auth_frame,
            placeholder_text="your_api_key"
        )

        # JSON Path
        ctk.CTkLabel(
            self.api_frame,
            text="JSON Data Path:",
            font=("Segoe UI", 12)
        ).grid(row=4, column=0, padx=10, pady=5, sticky="w")

        self.api_json_path_entry = ctk.CTkEntry(
            self.api_frame,
            placeholder_text="$.data (optional)"
        )
        self.api_json_path_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        # Streaming-specific options
        self.stream_frame = ctk.CTkFrame(scrollable_frame)
        self.stream_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        self.stream_frame.grid_columnconfigure(1, weight=1)
        self.stream_frame.grid_remove()  # Hidden by default

        # Protocol
        ctk.CTkLabel(
            self.stream_frame,
            text="Protocol:",
            font=("Segoe UI", 12)
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.stream_protocol_var = ctk.StringVar(value="mqtt")
        stream_protocol_menu = ctk.CTkOptionMenu(
            self.stream_frame,
            variable=self.stream_protocol_var,
            values=["mqtt", "websocket", "serial"],
            command=self._on_stream_protocol_change
        )
        stream_protocol_menu.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Connection settings frame
        self.stream_config_frame = ctk.CTkFrame(self.stream_frame, fg_color="transparent")
        self.stream_config_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.stream_config_frame.grid_columnconfigure(1, weight=1)

        # MQTT Broker/WebSocket URL/Serial Port
        self.stream_addr_label = ctk.CTkLabel(
            self.stream_config_frame,
            text="Broker:",
            font=("Segoe UI", 12)
        )
        self.stream_addr_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.stream_addr_entry = ctk.CTkEntry(
            self.stream_config_frame,
            placeholder_text="mqtt.example.com"
        )
        self.stream_addr_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Port (for MQTT/WebSocket)
        self.stream_port_label = ctk.CTkLabel(
            self.stream_config_frame,
            text="Port:",
            font=("Segoe UI", 12)
        )
        self.stream_port_entry = ctk.CTkEntry(
            self.stream_config_frame,
            placeholder_text="1883"
        )

        # Topic (for MQTT)
        self.stream_topic_label = ctk.CTkLabel(
            self.stream_config_frame,
            text="Topic:",
            font=("Segoe UI", 12)
        )
        self.stream_topic_entry = ctk.CTkEntry(
            self.stream_config_frame,
            placeholder_text="sensors/data"
        )

        # Baud rate (for Serial)
        self.stream_baud_label = ctk.CTkLabel(
            self.stream_config_frame,
            text="Baud Rate:",
            font=("Segoe UI", 12)
        )
        self.stream_baud_entry = ctk.CTkEntry(
            self.stream_config_frame,
            placeholder_text="115200"
        )

        # Duration
        ctk.CTkLabel(
            self.stream_frame,
            text="Collection Duration (sec):",
            font=("Segoe UI", 12)
        ).grid(row=2, column=0, padx=10, pady=5, sticky="w")

        self.stream_duration_entry = ctk.CTkEntry(
            self.stream_frame,
            placeholder_text="10"
        )
        self.stream_duration_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Load button (in scrollable frame for visibility)
        load_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        load_frame.grid(row=4, column=0, pady=10)

        self.load_btn = ctk.CTkButton(
            load_frame,
            text="Load Data",
            command=self._load_data,
            width=200,
            height=40,
            font=("Segoe UI", 14),
            fg_color="green",
            hover_color="darkgreen"
        )
        self.load_btn.pack()

        # Status label
        self.load_status_label = ctk.CTkLabel(
            scrollable_frame,
            text="",
            font=("Segoe UI", 11),
            text_color="gray"
        )
        self.load_status_label.grid(row=5, column=0, pady=5)

    def _setup_windowing_tab(self) -> None:
        """Setup windowing configuration tab."""
        tab = self.tabview.tab("Windowing")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)  # Two columns: left for controls, right for info

        # Windowing parameters
        params_frame = ctk.CTkFrame(tab)
        params_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        params_frame.grid_columnconfigure(1, weight=1)

        # Window size
        ctk.CTkLabel(
            params_frame,
            text="Window Size (samples):",
            font=("Segoe UI", 12)
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.window_size_var = ctk.StringVar(value="100")
        window_size_entry = ctk.CTkEntry(
            params_frame,
            textvariable=self.window_size_var,
            width=150
        )
        window_size_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # Overlap
        ctk.CTkLabel(
            params_frame,
            text="Overlap (%):",
            font=("Segoe UI", 12)
        ).grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.overlap_var = ctk.StringVar(value="0")
        overlap_entry = ctk.CTkEntry(
            params_frame,
            textvariable=self.overlap_var,
            width=150
        )
        overlap_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # Sampling rate
        ctk.CTkLabel(
            params_frame,
            text="Sampling Rate (Hz):",
            font=("Segoe UI", 12)
        ).grid(row=2, column=0, padx=10, pady=10, sticky="w")

        self.sampling_rate_var = ctk.StringVar(value="50.0")
        sampling_rate_entry = ctk.CTkEntry(
            params_frame,
            textvariable=self.sampling_rate_var,
            width=150
        )
        sampling_rate_entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        # Create windows button
        create_btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        create_btn_frame.grid(row=1, column=0, pady=20)

        self.create_windows_btn = ctk.CTkButton(
            create_btn_frame,
            text="Create Windows",
            command=self._create_windows,
            width=200,
            height=40,
            font=("Segoe UI", 14),
            state="disabled"
        )
        self.create_windows_btn.pack()

        # Progress bar for loading and windowing operations
        self.progress_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self.progress_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=5)
        self.progress_frame.grid_columnconfigure(0, weight=1)
        self.progress_frame.grid_remove()  # Hidden by default

        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="Loading...",
            font=("Segoe UI", 10),
            text_color="blue"
        )
        self.progress_label.grid(row=0, column=0, sticky="w", padx=5, pady=(5, 2))

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            mode="determinate",
            height=15
        )
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        self.progress_bar.set(0)

        # Info panel on the right side
        info_frame = ctk.CTkFrame(tab, fg_color="#2b2b2b")
        info_frame.grid(row=0, column=1, rowspan=3, sticky="nsew", padx=10, pady=10)

        # Window stats label in the right panel
        self.window_stats_label = ctk.CTkLabel(
            info_frame,
            text="",
            font=("Segoe UI", 11),
            text_color="lightgray",
            justify="left",
            anchor="nw"
        )
        self.window_stats_label.pack(fill="both", expand=True, padx=15, pady=15)

    def _setup_preview_tab(self) -> None:
        """Setup data preview tab with visualization."""
        tab = self.tabview.tab("Preview")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)  # Plot gets flexible space

        # Navigation state
        self.current_batch_start = 0
        self.current_window_index = 0
        self.view_mode = "raw"  # "raw" or "windows"
        self.filtered_classes = []  # Empty = show all

        # Top row: Info and controls
        top_frame = ctk.CTkFrame(tab, fg_color="transparent")
        top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        top_frame.grid_columnconfigure(0, weight=1)

        # Info label
        self.info_label = ctk.CTkLabel(
            top_frame,
            text="No data loaded",
            font=("Segoe UI", 10),
            justify="left",
            anchor="w"
        )
        self.info_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)

        # Controls
        controls_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=1, sticky="e", padx=5)

        ctk.CTkLabel(
            controls_frame,
            text="Samples:",
            font=("Segoe UI", 10)
        ).pack(side="left", padx=5)

        self.max_samples_var = ctk.StringVar(value="1000")
        ctk.CTkEntry(
            controls_frame,
            textvariable=self.max_samples_var,
            width=70
        ).pack(side="left", padx=2)

        # Navigation row: Class filter, navigation buttons, mode selector
        nav_frame = ctk.CTkFrame(tab)
        nav_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        nav_frame.grid_columnconfigure(1, weight=1)

        # Class filter
        filter_frame = ctk.CTkFrame(nav_frame, fg_color="transparent")
        filter_frame.grid(row=0, column=0, sticky="w", padx=5)

        ctk.CTkLabel(
            filter_frame,
            text="Filter:",
            font=("Segoe UI", 10)
        ).pack(side="left", padx=5)

        self.class_filter_var = ctk.StringVar(value="All Classes")
        self.class_filter_menu = ctk.CTkOptionMenu(
            filter_frame,
            variable=self.class_filter_var,
            values=["All Classes"],
            command=self._on_class_filter_change,
            width=120
        )
        self.class_filter_menu.pack(side="left", padx=5)

        # Navigation buttons (center)
        nav_buttons_frame = ctk.CTkFrame(nav_frame, fg_color="transparent")
        nav_buttons_frame.grid(row=0, column=1)

        self.prev_btn = ctk.CTkButton(
            nav_buttons_frame,
            text="◀ Previous",
            command=self._navigate_previous,
            width=100,
            height=28
        )
        self.prev_btn.pack(side="left", padx=5)

        self.nav_label = ctk.CTkLabel(
            nav_buttons_frame,
            text="Batch 1",
            font=("Segoe UI", 11, "bold")
        )
        self.nav_label.pack(side="left", padx=10)

        self.next_btn = ctk.CTkButton(
            nav_buttons_frame,
            text="Next ▶",
            command=self._navigate_next,
            width=100,
            height=28
        )
        self.next_btn.pack(side="left", padx=5)

        # Mode selector (right)
        mode_frame = ctk.CTkFrame(nav_frame, fg_color="transparent")
        mode_frame.grid(row=0, column=2, sticky="e", padx=5)

        ctk.CTkLabel(
            mode_frame,
            text="View:",
            font=("Segoe UI", 10)
        ).pack(side="left", padx=5)

        self.view_mode_var = ctk.StringVar(value="Raw Data")
        self.view_mode_menu = ctk.CTkOptionMenu(
            mode_frame,
            variable=self.view_mode_var,
            values=["Raw Data", "Windows"],
            command=self._on_view_mode_change,
            width=100
        )
        self.view_mode_menu.pack(side="left", padx=5)

        # Sensor plot widget
        plot_frame = ctk.CTkFrame(tab)
        plot_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(5, 10))
        plot_frame.grid_columnconfigure(0, weight=1)
        plot_frame.grid_rowconfigure(0, weight=1)

        self.sensor_plot = SensorPlotWidget(
            plot_frame,
            width=1000,
            height=600
        )
        self.sensor_plot.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    def _on_task_mode_change(self, choice: str) -> None:
        """Handle task mode change between Anomaly Detection and Classification."""
        mode = "classification" if choice == "Classification" else "anomaly_detection"
        logger.info(f"Task mode changed to: {mode}")

        # Update project task type
        if self.project_manager.current_project:
            self.project_manager.current_project.data.task_type = mode
            self.project_manager.current_project.save()

        # Update info text
        if mode == "classification":
            self.task_mode_info.configure(
                text="ℹ️ Trains models to categorize data into predefined classes (requires labeled data)"
            )
        else:
            self.task_mode_info.configure(
                text="ℹ️ Detects unusual patterns in unlabeled data"
            )

    def _on_pipeline_mode_change(self, choice: str) -> None:
        """Handle pipeline mode change between ML and DL."""
        # Check if mode is locked
        if self.project_manager.current_project:
            if self.project_manager.current_project.data.pipeline_mode_locked:
                logger.warning("Pipeline mode is locked and cannot be changed")
                messagebox.showwarning(
                    "Mode Locked",
                    "Pipeline mode cannot be changed after data processing has started.\n\n"
                    "Create a new project to use a different pipeline mode."
                )
                # Revert to locked mode
                locked_mode = self.project_manager.current_project.data.pipeline_mode
                display_mode = "Traditional ML" if locked_mode == "ml" else "Deep Learning"
                self.pipeline_mode_var.set(display_mode)
                return

        mode = "dl" if choice == "Deep Learning" else "ml"
        logger.info(f"🔴 Pipeline mode changed to: {mode}")

        # Update project pipeline mode
        if self.project_manager.current_project:
            self.project_manager.current_project.data.pipeline_mode = mode
            self.project_manager.current_project.save()

        # Update info text
        if mode == "dl":
            self.pipeline_mode_info.configure(
                text="ℹ️ TimesNet deep learning on raw time series (GPU/CPU auto-detect)"
            )
        else:
            self.pipeline_mode_info.configure(
                text="ℹ️ Feature extraction + sklearn/PyOD models"
            )

        # 🔴 CRITICAL: Update navigation to show red backgrounds IMMEDIATELY
        logger.info(f"🔴 Updating navigation for mode: {mode}")
        # Try different ways to find the main window
        main_win = None
        if hasattr(self, 'winfo_toplevel'):
            top_level = self.winfo_toplevel()
            if hasattr(top_level, 'update_navigation_for_pipeline_mode'):
                main_win = top_level

        if not main_win and hasattr(self.master, 'master'):
            if hasattr(self.master.master, 'update_navigation_for_pipeline_mode'):
                main_win = self.master.master

        if main_win:
            logger.info(f"🔴 Found main window, calling update_navigation_for_pipeline_mode({mode})")
            main_win.update_navigation_for_pipeline_mode(mode)
        else:
            logger.error("🔴 FAILED to find main window for navigation update!")

    def _on_source_type_change(self, choice: str) -> None:
        """Handle data source type change."""
        logger.info(f"Data source type changed to: {choice}")

        # Hide all frames first
        self.csv_frame.grid_remove()
        self.ei_frame.grid_remove()
        self.db_frame.grid_remove()
        self.api_frame.grid_remove()
        self.stream_frame.grid_remove()

        # Show relevant frame
        if choice == "CSV File":
            self.csv_frame.grid()
        elif choice in ["Edge Impulse JSON", "Edge Impulse CBOR"]:
            self.ei_frame.grid()
        elif choice == "Database":
            self.db_frame.grid()
            self._on_db_type_change(self.db_type_var.get())
        elif choice == "REST API":
            self.api_frame.grid()
            self._on_api_auth_change(self.api_auth_var.get())
        elif choice == "Streaming":
            self.stream_frame.grid()
            self._on_stream_protocol_change(self.stream_protocol_var.get())

    def _browse_csv_file(self) -> None:
        """Browse for CSV file."""
        filename = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[
                ("CSV files", "*.csv"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )

        if filename:
            self.file_path_entry.delete(0, "end")
            self.file_path_entry.insert(0, filename)
            logger.info(f"Selected CSV file: {filename}")

    def _browse_ei_file(self) -> None:
        """Browse for Edge Impulse JSON/CBOR file."""
        filename = filedialog.askopenfilename(
            title="Select Edge Impulse File",
            filetypes=[
                ("Edge Impulse files", "*.json;*.cbor"),
                ("JSON files", "*.json"),
                ("CBOR files", "*.cbor"),
                ("All files", "*.*")
            ]
        )

        if filename:
            self.ei_file_path_entry.delete(0, "end")
            self.ei_file_path_entry.insert(0, filename)
            logger.info(f"Selected Edge Impulse file: {filename}")

    def _browse_ei_folder(self) -> None:
        """Browse for folder containing Edge Impulse JSON/CBOR files (batch loading)."""
        import os

        folder_path = filedialog.askdirectory(
            title="Select Folder with Edge Impulse Files"
        )

        if folder_path:
            # Update the entry field to show folder path
            self.ei_file_path_entry.delete(0, "end")
            self.ei_file_path_entry.insert(0, folder_path)

            # Count files for feedback
            file_count = 0
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.endswith(('.json', '.cbor')):
                        file_count += 1

            logger.info(f"Selected folder: {folder_path} ({file_count} Edge Impulse files found)")

    def _browse_ei_train_folder(self) -> None:
        """Browse for folder containing training Edge Impulse files."""
        import os

        folder_path = filedialog.askdirectory(
            title="Select Training Data Folder"
        )

        if folder_path:
            # Update the entry field to show folder path
            self.ei_train_path_entry.delete(0, "end")
            self.ei_train_path_entry.insert(0, folder_path)

            # Count files for feedback
            file_count = 0
            class_labels = set()
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.endswith(('.json', '.cbor')):
                        file_count += 1
                        # Extract class label from filename
                        label = file.split('.')[0]
                        class_labels.add(label)

            info_text = f"Training: {file_count} files, {len(class_labels)} classes: {', '.join(sorted(class_labels))}"
            self.ei_info_label.configure(text=info_text, text_color="green")
            logger.info(f"Selected training folder: {folder_path} ({file_count} files, {len(class_labels)} classes)")

    def _browse_ei_test_folder(self) -> None:
        """Browse for folder containing test Edge Impulse files."""
        import os

        folder_path = filedialog.askdirectory(
            title="Select Test Data Folder (Optional)"
        )

        if folder_path:
            # Update the entry field to show folder path
            self.ei_test_path_entry.delete(0, "end")
            self.ei_test_path_entry.insert(0, folder_path)

            # Count files for feedback
            file_count = 0
            class_labels = set()
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.endswith(('.json', '.cbor')):
                        file_count += 1
                        # Extract class label from filename
                        label = file.split('.')[0]
                        class_labels.add(label)

            # Update info label with both train and test info
            train_info = self.ei_info_label.cget("text")
            if train_info:
                info_text = f"{train_info} | Test: {file_count} files, {len(class_labels)} classes"
            else:
                info_text = f"Test: {file_count} files, {len(class_labels)} classes: {', '.join(sorted(class_labels))}"
            self.ei_info_label.configure(text=info_text, text_color="blue")
            logger.info(f"Selected test folder: {folder_path} ({file_count} files, {len(class_labels)} classes)")

    def _on_db_type_change(self, db_type: str) -> None:
        """Handle database type change."""
        # Update port placeholder based on database type
        port_defaults = {
            "postgresql": "5432",
            "mysql": "3306",
            "sqlite": "",
            "sqlserver": "1433"
        }

        placeholder = port_defaults.get(db_type, "5432")
        self.db_port_entry.configure(placeholder_text=placeholder)

        # Hide host/port for SQLite
        if db_type == "sqlite":
            self.db_host_entry.configure(state="disabled")
            self.db_port_entry.configure(state="disabled")
            self.db_username_entry.configure(state="disabled")
            self.db_password_entry.configure(state="disabled")
        else:
            self.db_host_entry.configure(state="normal")
            self.db_port_entry.configure(state="normal")
            self.db_username_entry.configure(state="normal")
            self.db_password_entry.configure(state="normal")

    def _on_api_auth_change(self, auth_type: str) -> None:
        """Handle API authentication type change."""
        # Hide all auth fields first
        self.api_username_label.grid_remove()
        self.api_username_entry.grid_remove()
        self.api_password_label.grid_remove()
        self.api_password_entry.grid_remove()
        self.api_token_label.grid_remove()
        self.api_token_entry.grid_remove()
        self.api_key_label.grid_remove()
        self.api_key_entry.grid_remove()

        # Show relevant fields based on auth type
        if auth_type == "basic":
            self.api_username_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
            self.api_username_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            self.api_password_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
            self.api_password_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        elif auth_type == "bearer":
            self.api_token_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
            self.api_token_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        elif auth_type == "api_key":
            self.api_key_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
            self.api_key_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    def _on_stream_protocol_change(self, protocol: str) -> None:
        """Handle streaming protocol change."""
        # Hide all protocol-specific fields first
        self.stream_port_label.grid_remove()
        self.stream_port_entry.grid_remove()
        self.stream_topic_label.grid_remove()
        self.stream_topic_entry.grid_remove()
        self.stream_baud_label.grid_remove()
        self.stream_baud_entry.grid_remove()

        # Update labels and show relevant fields
        if protocol == "mqtt":
            self.stream_addr_label.configure(text="Broker:")
            self.stream_addr_entry.configure(placeholder_text="mqtt.example.com")

            self.stream_port_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
            self.stream_port_entry.configure(placeholder_text="1883")
            self.stream_port_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

            self.stream_topic_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
            self.stream_topic_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        elif protocol == "websocket":
            self.stream_addr_label.configure(text="WebSocket URL:")
            self.stream_addr_entry.configure(placeholder_text="ws://example.com:8080/stream")

        elif protocol == "serial":
            self.stream_addr_label.configure(text="Port:")
            self.stream_addr_entry.configure(placeholder_text="COM3 or /dev/ttyUSB0")

            self.stream_baud_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
            self.stream_baud_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    def _load_data(self) -> None:
        """Load data from selected source."""
        source_type = self.source_type_var.get()

        try:
            self.load_status_label.configure(text="Loading data...")
            self.load_btn.configure(state="disabled")

            # Load based on source type
            if source_type == "CSV File":
                file_path = self.file_path_entry.get().strip()
                if not file_path:
                    messagebox.showwarning("No File", "Please select a CSV file first.")
                    return
                self._load_csv_data(file_path)

            elif source_type in ["Edge Impulse JSON", "Edge Impulse CBOR"]:
                # Check for train/test split folders first
                train_path = self.ei_train_path_entry.get().strip()
                test_path = self.ei_test_path_entry.get().strip()
                file_path = self.ei_file_path_entry.get().strip()

                if train_path:
                    # Load train/test split separately
                    self._load_edgeimpulse_train_test(train_path, test_path, source_type)
                elif file_path:
                    # Load single file or batch folder (legacy)
                    self._load_edgeimpulse_data(file_path, source_type)
                else:
                    messagebox.showwarning("No Data", "Please select training data folder or a single file.")
                    return

            elif source_type == "Database":
                self._load_database_data()

            elif source_type == "REST API":
                self._load_restapi_data()

            elif source_type == "Streaming":
                self._load_streaming_data()

            else:
                messagebox.showinfo("Not Implemented", "This data source type is not yet supported.")
                return

            # Update UI
            self.load_status_label.configure(
                text=f"✓ Loaded {len(self.loaded_data)} rows, {len(self.loaded_data.columns)} columns",
                text_color="green"
            )

            # Enable windowing
            self.create_windows_btn.configure(state="normal")

            # Update preview
            self._update_preview()

            # Try to infer sampling rate
            inferred_rate = self.current_data_source.infer_sampling_rate()
            if inferred_rate:
                self.sampling_rate_var.set(f"{inferred_rate:.2f}")

            logger.info(f"Data loaded successfully: {len(self.loaded_data)} rows")

        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            self.load_status_label.configure(
                text=f"✗ Error: {str(e)}",
                text_color="red"
            )
            messagebox.showerror("Load Error", f"Failed to load data:\n{e}")

        finally:
            self.load_btn.configure(state="normal")

    def _load_csv_data(self, file_path: str) -> None:
        """Load CSV data."""
        # Get delimiter
        delimiter_map = {
            "Comma (,)": ",",
            "Semicolon (;)": ";",
            "Tab": "\t",
            "Space": " "
        }
        delimiter = delimiter_map.get(self.delimiter_var.get(), ",")

        # Create data source config
        config = DataSourceConfig(
            source_type="csv",
            name=Path(file_path).name,
            parameters={
                "file_path": file_path,
                "delimiter": delimiter,
                "encoding": self.encoding_var.get()
            }
        )

        # Create and connect data source
        self.current_data_source = CSVDataSource(config)

        if not self.current_data_source.connect():
            raise Exception("Failed to connect to CSV file")

        # Load data
        self.loaded_data = self.current_data_source.load_data()

    def _load_edgeimpulse_data(self, file_path: str, source_type: str) -> None:
        """Load Edge Impulse JSON/CBOR data (single file or batch folder)."""
        import os

        # Determine format type
        format_type = "json" if source_type == "Edge Impulse JSON" else "cbor"

        # Check if path is a folder (batch loading)
        if os.path.isdir(file_path):
            self._load_edgeimpulse_batch(file_path, format_type)
        else:
            # Single file loading
            self._load_edgeimpulse_single_file(file_path, format_type)

    def _load_edgeimpulse_single_file(self, file_path: str, format_type: str) -> None:
        """Load single Edge Impulse file."""
        # Create data source
        self.current_data_source = EdgeImpulseDataSource()
        self.current_data_source.file_path = Path(file_path)
        self.current_data_source.format_type = format_type

        if not self.current_data_source.connect():
            raise Exception(f"Failed to connect: {self.current_data_source.last_error}")

        # Load data
        self.loaded_data = self.current_data_source.load_data()

        # Update device info label
        device_info = self.current_data_source.get_device_info()
        sensor_info = self.current_data_source.get_sensor_info()
        sampling_rate = self.current_data_source.get_sampling_rate()

        info_text = f"Device: {device_info['type']}"
        if device_info['name']:
            info_text += f" ({device_info['name']})"
        if sampling_rate is not None:
            info_text += f" | Sampling: {sampling_rate:.2f} Hz"
        info_text += f" | Sensors: {len(sensor_info)}"

        self.ei_info_label.configure(text=info_text)

    def _load_edgeimpulse_batch(self, folder_path: str, format_type: str) -> None:
        """Load all Edge Impulse files from a folder recursively."""
        import os

        # Find all matching files recursively
        all_files = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.cbor') or file.endswith('.json'):
                    all_files.append(os.path.join(root, file))

        if not all_files:
            raise Exception(f"No .cbor or .json files found in {folder_path}")

        logger.info(f"Found {len(all_files)} Edge Impulse files in folder")

        # Load all files and concatenate
        all_dataframes = []
        class_labels = set()

        for file_path in all_files:
            try:
                # Create data source for this file
                data_source = EdgeImpulseDataSource()
                data_source.file_path = Path(file_path)
                data_source.format_type = format_type

                if not data_source.connect():
                    logger.warning(f"Skipping {file_path}: {data_source.last_error}")
                    continue

                # Load data
                df = data_source.load_data()

                # Extract class label from filename (e.g., "idle.1.cbor" -> "idle")
                filename = os.path.basename(file_path)
                label = filename.split('.')[0]  # Get first part before first dot

                # Add label column if in classification mode
                task_type = "classification"  # Always add labels for batch loading - user can filter later
                if label:
                    df['label'] = label
                    class_labels.add(label)
                    logger.info(f"Loaded {file_path}: {len(df)} rows, label='{label}'")
                else:
                    logger.info(f"Loaded {file_path}: {len(df)} rows")

                all_dataframes.append(df)

            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")
                continue

        if not all_dataframes:
            raise Exception("No files could be loaded successfully")

        # Concatenate all DataFrames
        self.loaded_data = pd.concat(all_dataframes, ignore_index=True)

        # Fix time column to be continuous (remove jumps between files)
        if 'time' in self.loaded_data.columns:
            # Create continuous time index based on row index
            # Assuming constant sampling rate within each file
            self.loaded_data['time'] = range(len(self.loaded_data))
            logger.info("Reset time column to continuous index for batch loading")

        # Store a simple data source reference (we'll use the first file's metadata)
        self.current_data_source = EdgeImpulseDataSource()
        self.current_data_source.file_path = Path(all_files[0])
        self.current_data_source.format_type = format_type
        self.current_data_source.connect()
        # Load first file to initialize sensor detection (but we use self.loaded_data for actual data)
        self.current_data_source.load_data()

        # Update info label
        info_text = f"Batch Load: {len(all_files)} files, {len(self.loaded_data)} total rows"
        if class_labels:
            info_text += f" | Classes: {sorted(class_labels)}"

        self.ei_info_label.configure(text=info_text)
        logger.info(f"Batch loading complete: {len(all_dataframes)} files concatenated")

    def _load_edgeimpulse_train_test(self, train_folder: str, test_folder: str, format_type: str) -> None:
        """Load training and test data separately from different folders."""
        import os
        import pickle

        # Convert UI format type to internal format
        format_map = {
            "Edge Impulse JSON": "json",
            "Edge Impulse CBOR": "cbor"
        }
        internal_format = format_map.get(format_type, "auto")

        # Helper function to load folder
        def load_folder(folder_path, dataset_name):
            all_files = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.endswith(('.json', '.cbor')):
                        all_files.append(os.path.join(root, file))

            if not all_files:
                raise Exception(f"No .cbor or .json files found in {folder_path}")

            logger.info(f"Loading {dataset_name}: Found {len(all_files)} files")

            all_dataframes = []
            class_labels = set()

            for file_path in all_files:
                try:
                    data_source = EdgeImpulseDataSource()
                    data_source.file_path = Path(file_path)
                    data_source.format_type = internal_format

                    if not data_source.connect():
                        logger.warning(f"Skipping {file_path}: {data_source.last_error}")
                        continue

                    df = data_source.load_data()

                    # Extract class label from filename
                    filename = os.path.basename(file_path)
                    label = filename.split('.')[0]

                    if label:
                        df['label'] = label
                        class_labels.add(label)
                        logger.info(f"Loaded {filename}: {len(df)} rows, label='{label}'")

                    # Store source file information
                    df['_source_file'] = filename

                    all_dataframes.append(df)

                except Exception as e:
                    logger.error(f"Failed to load {file_path}: {e}")
                    continue

            if not all_dataframes:
                raise Exception(f"No files could be loaded from {dataset_name} folder")

            # Concatenate all DataFrames
            combined_df = pd.concat(all_dataframes, ignore_index=True)

            # Fix time column
            if 'time' in combined_df.columns:
                combined_df['time'] = range(len(combined_df))

            return combined_df, class_labels, all_files

        # Load training data
        train_df, train_classes, train_files = load_folder(train_folder, "training")

        # Load test data if provided
        test_df = None
        test_classes = set()
        test_files = []
        if test_folder:
            test_df, test_classes, test_files = load_folder(test_folder, "test")

        # Save train and test data separately
        project = self.project_manager.current_project
        if project:
            data_dir = project.get_data_dir()

            # Save training data
            train_data_path = data_dir / "train_data.pkl"
            with open(train_data_path, 'wb') as f:
                pickle.dump(train_df, f)
            project.data.train_data_file = str(train_data_path)
            logger.info(f"Saved training data: {len(train_df)} rows to {train_data_path}")

            # Save test data if available
            if test_df is not None:
                test_data_path = data_dir / "test_data.pkl"
                with open(test_data_path, 'wb') as f:
                    pickle.dump(test_df, f)
                project.data.test_data_file = str(test_data_path)
                logger.info(f"Saved test data: {len(test_df)} rows to {test_data_path}")

            # Mark as manual split
            project.data.train_test_split_type = "manual"
            project.data.task_type = "classification"

            # Store original folder paths for display and re-loading
            project.data.train_folder_path = train_folder
            project.data.test_folder_path = test_folder if test_folder else None
            project.data.source_type = format_type  # Store source type for re-loading

            # Store class info
            all_classes = train_classes | test_classes
            project.data.num_classes = len(all_classes)
            project.data.class_mapping = {cls: idx for idx, cls in enumerate(sorted(all_classes))}

            project.save()

        # For UI display, show combined data (but keep them separate internally)
        if test_df is not None:
            self.loaded_data = pd.concat([train_df, test_df], ignore_index=True)
            info_text = f"Train: {len(train_df)} rows, {len(train_files)} files | Test: {len(test_df)} rows, {len(test_files)} files"
            info_text += f" | Classes: {sorted(train_classes | test_classes)}"
        else:
            self.loaded_data = train_df
            info_text = f"Train: {len(train_df)} rows, {len(train_files)} files | Classes: {sorted(train_classes)}"

        # Store data source reference
        self.current_data_source = EdgeImpulseDataSource()
        self.current_data_source.file_path = Path(train_files[0])
        self.current_data_source.format_type = internal_format  # Use internal format
        self.current_data_source.connect()
        self.current_data_source.load_data()

        self.ei_info_label.configure(text=info_text, text_color="blue")
        logger.info(f"Train/Test split loading complete")

    def _load_database_data(self) -> None:
        """Load data from database."""
        # Get database parameters
        db_type = self.db_type_var.get()
        host = self.db_host_entry.get().strip() or "localhost"
        port = self.db_port_entry.get().strip()
        database = self.db_name_entry.get().strip()
        username = self.db_username_entry.get().strip()
        password = self.db_password_entry.get().strip()
        table = self.db_table_entry.get().strip()
        query = self.db_query_entry.get().strip()

        if not database:
            messagebox.showwarning("Missing Info", "Please enter database name.")
            return

        # Create data source config
        config = DataSourceConfig(
            source_type="database",
            name=f"{db_type}://{database}",
            parameters={
                "db_type": db_type,
                "host": host,
                "port": port,
                "database": database,
                "username": username,
                "password": password,
                "table": table,
                "query": query
            }
        )

        # Create and connect data source
        self.current_data_source = DatabaseDataSource(config)

        if not self.current_data_source.connect():
            raise Exception("Failed to connect to database")

        # Load data
        self.loaded_data = self.current_data_source.load_data()

    def _load_restapi_data(self) -> None:
        """Load data from REST API."""
        # Get API parameters
        url = self.api_url_entry.get().strip()
        method = self.api_method_var.get()
        auth_type = self.api_auth_var.get()

        if not url:
            messagebox.showwarning("Missing Info", "Please enter API URL.")
            return

        # Get auth credentials
        auth_params = {}
        if auth_type == "basic":
            auth_params["username"] = self.api_username_entry.get().strip()
            auth_params["password"] = self.api_password_entry.get().strip()
        elif auth_type == "bearer":
            auth_params["token"] = self.api_token_entry.get().strip()
        elif auth_type == "api_key":
            auth_params["api_key"] = self.api_key_entry.get().strip()

        json_path = self.api_json_path_entry.get().strip()

        # Create data source config
        config = DataSourceConfig(
            source_type="restapi",
            name=url,
            parameters={
                "url": url,
                "method": method,
                "auth_type": auth_type,
                "json_path": json_path,
                **auth_params
            }
        )

        # Create and connect data source
        self.current_data_source = RestAPIDataSource(config)

        if not self.current_data_source.connect():
            raise Exception("Failed to connect to API")

        # Load data
        self.loaded_data = self.current_data_source.load_data()

    def _load_streaming_data(self) -> None:
        """Load data from streaming source."""
        # Get streaming parameters
        protocol = self.stream_protocol_var.get()
        addr = self.stream_addr_entry.get().strip()
        duration = self.stream_duration_entry.get().strip()

        if not addr:
            messagebox.showwarning("Missing Info", f"Please enter {protocol} address.")
            return

        if not duration:
            messagebox.showwarning("Missing Info", "Please enter collection duration.")
            return

        try:
            duration = int(duration)
        except ValueError:
            messagebox.showwarning("Invalid Input", "Duration must be a number.")
            return

        # Get protocol-specific parameters
        params = {
            "protocol": protocol,
            "duration": duration
        }

        if protocol == "mqtt":
            params["broker"] = addr
            params["port"] = int(self.stream_port_entry.get().strip() or "1883")
            params["topic"] = self.stream_topic_entry.get().strip() or "sensors/data"
        elif protocol == "websocket":
            params["url"] = addr
        elif protocol == "serial":
            params["port"] = addr
            params["baud_rate"] = int(self.stream_baud_entry.get().strip() or "115200")

        # Create data source config
        config = DataSourceConfig(
            source_type="streaming",
            name=f"{protocol}://{addr}",
            parameters=params
        )

        # Create and connect data source
        self.current_data_source = StreamingDataSource(config)

        if not self.current_data_source.connect():
            raise Exception(f"Failed to connect to {protocol} stream")

        # Show progress dialog
        messagebox.showinfo(
            "Collecting Data",
            f"Collecting data for {duration} seconds...\nPlease wait."
        )

        # Load data
        self.loaded_data = self.current_data_source.load_data()

    def _create_windows(self) -> None:
        """Create windows from loaded data."""
        if self.loaded_data is None:
            messagebox.showwarning("No Data", "Please load data first.")
            return

        # Show progress bar
        self.progress_frame.grid()
        self.progress_label.configure(text="Creating windows...")
        self.progress_bar.set(0.1)
        self.update_idletasks()

        try:
            # Get parameters
            window_size = int(self.window_size_var.get())
            overlap = float(self.overlap_var.get()) / 100.0  # Convert to ratio
            sampling_rate = float(self.sampling_rate_var.get())

            self.progress_bar.set(0.2)
            self.update_idletasks()

            # Create windowing config
            config = WindowConfig(
                window_size=window_size,
                overlap=overlap,
                sampling_rate=sampling_rate
            )

            # Initialize windowing engine
            self.windowing_engine = WindowingEngine(config)

            self.progress_bar.set(0.3)
            self.update_idletasks()

            # Detect sensor columns
            sensor_columns = self.current_data_source.detect_sensor_columns()
            time_column = self.current_data_source.detect_time_column()

            if not sensor_columns:
                raise ValueError("No numeric sensor columns found in data")

            # Check if label column exists (from batch loading)
            label_column = None
            if 'label' in self.loaded_data.columns:
                label_column = 'label'
                logger.info("Found 'label' column in data - will use for window labeling")

            # Check if we have separate train/test data
            project = self.project_manager.current_project
            if project and project.data.train_test_split_type == "manual":
                # Load and window train/test data separately
                import pickle

                self.progress_label.configure(text="Windowing training data...")
                self.progress_bar.set(0.4)
                self.update_idletasks()

                # Window training data
                with open(project.data.train_data_file, 'rb') as f:
                    train_data = pickle.load(f)

                train_windows = self.windowing_engine.segment_data(
                    train_data,
                    sensor_columns=sensor_columns,
                    time_column=time_column,
                    label_column=label_column
                )

                self.progress_label.configure(text="Windowing test data...")
                self.progress_bar.set(0.6)
                self.update_idletasks()

                # Window test data if available
                test_windows = []
                if project.data.test_data_file:
                    with open(project.data.test_data_file, 'rb') as f:
                        test_data = pickle.load(f)

                    test_windows = self.windowing_engine.segment_data(
                        test_data,
                        sensor_columns=sensor_columns,
                        time_column=time_column,
                        label_column=label_column
                    )

                # Save train and test windows separately
                data_dir = project.get_data_dir()

                train_windows_path = data_dir / "train_windows.pkl"
                with open(train_windows_path, 'wb') as f:
                    pickle.dump(train_windows, f)
                project.data.train_windows_file = str(train_windows_path)
                project.data.num_train_windows = len(train_windows)

                if test_windows:
                    test_windows_path = data_dir / "test_windows.pkl"
                    with open(test_windows_path, 'wb') as f:
                        pickle.dump(test_windows, f)
                    project.data.test_windows_file = str(test_windows_path)
                    project.data.num_test_windows = len(test_windows)

                # Combined windows for display/stats
                windows = train_windows + test_windows
                # Update windowing engine with combined windows for preview
                self.windowing_engine.windows = windows
                logger.info(f"Created {len(train_windows)} train windows, {len(test_windows)} test windows")

            else:
                # Standard windowing (single dataset or auto-split)
                windows = self.windowing_engine.segment_data(
                    self.loaded_data,
                    sensor_columns=sensor_columns,
                    time_column=time_column,
                    label_column=label_column
                )

            # Update stats
            stats = self.windowing_engine.get_window_stats()
            stats_text = f"""Windows created successfully!

Total windows: {stats['total_windows']}
Window size: {stats['window_size']} samples
Overlap: {stats['overlap']*100:.1f}%
Sampling rate: {stats['sampling_rate']} Hz
Sensor columns: {len(sensor_columns)}
"""

            # Add train/test split info if using manual split
            if project and project.data.train_test_split_type == "manual":
                stats_text += f"\nTrain/Test Split (Manual):\n"
                stats_text += f"  Training: {project.data.num_train_windows} windows\n"
                stats_text += f"  Test: {project.data.num_test_windows} windows\n"

            # Add class distribution if classification mode
            if 'class_distribution' in stats:
                stats_text += "\nClass Distribution:\n"
                for class_name, count in stats['class_distribution'].items():
                    stats_text += f"  - {class_name}: {count} windows\n"

            self.window_stats_label.configure(text=stats_text)

            self.progress_label.configure(text="Saving windows...")
            self.progress_bar.set(0.8)
            self.update_idletasks()

            # Save to project
            if self.project_manager.has_project():
                project = self.project_manager.get_project()
                project.data.window_size = window_size
                project.data.sampling_rate = sampling_rate
                project.data.overlap = overlap
                project.data.sensor_columns = sensor_columns

                # Save windows to disk
                project.save_windows(windows, sensor_columns, time_column)

                # Lock pipeline mode after windowing is complete
                project.data.pipeline_mode_locked = True
                logger.info(f"Pipeline mode locked to: {project.data.pipeline_mode}")

                # Show warning in UI
                self.pipeline_mode_warning.grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")

                project.mark_stage_completed("data")
                self.project_manager.save_project()

            self.progress_bar.set(1.0)
            self.progress_label.configure(text="✓ Windows created successfully!")
            self.update_idletasks()

            logger.info(f"Created {len(windows)} windows")

            # Hide progress bar after 1 second
            self.after(1000, self.progress_frame.grid_remove)

            messagebox.showinfo("Success", f"Created {len(windows)} windows successfully!")

        except Exception as e:
            logger.error(f"Failed to create windows: {e}")
            messagebox.showerror("Windowing Error", f"Failed to create windows:\n{e}")

            # Hide progress bar on error
            self.progress_frame.grid_remove()

    def _update_preview(self) -> None:
        """Update data preview with visualization."""
        if self.loaded_data is None:
            return

        # Detect sensor and time columns
        sensor_columns = self.current_data_source.detect_sensor_columns()
        time_column = self.current_data_source.detect_time_column()

        # Compact single-line info
        info_text = f"📊 {len(self.loaded_data)} rows × {len(self.loaded_data.columns)} cols | "
        info_text += f"Sensors: {', '.join(sensor_columns[:3])}"
        if len(sensor_columns) > 3:
            info_text += f" +{len(sensor_columns)-3} more"

        # Update class filter options if label column exists
        if 'label' in self.loaded_data.columns:
            class_counts = self.loaded_data['label'].value_counts()
            class_list = [f"{label}:{count}" for label, count in class_counts.items()]
            info_text += f" | Classes: {', '.join(class_list)}"

            # Update filter dropdown
            class_names = ["All Classes"] + sorted(class_counts.index.tolist())
            self.class_filter_menu.configure(values=class_names)
            self.class_filter_var.set("All Classes")
        else:
            # No classes, reset filter
            self.class_filter_menu.configure(values=["All Classes"])
            self.class_filter_var.set("All Classes")

        self.info_label.configure(text=info_text)

        # Reset navigation
        self.current_batch_start = 0
        self.current_window_index = 0
        self._update_navigation_ui()

        # Plot sensor data
        self._refresh_plot()

    def _refresh_plot(self) -> None:
        """Refresh the sensor plot with current data."""
        # Allow plotting in windows mode even without loaded_data
        if self.loaded_data is None and self.view_mode != "windows":
            return

        try:
            max_samples = int(self.max_samples_var.get())
        except ValueError:
            max_samples = 1000

        # Get data to plot based on mode
        if self.view_mode == "windows":
            plot_data = self._get_window_data()
            if plot_data is None:
                return

            # Get sensor columns from project data or plot_data columns
            project = self.project_manager.current_project
            if project and hasattr(project.data, 'sensor_columns') and project.data.sensor_columns:
                sensor_columns = project.data.sensor_columns
            else:
                # Use all numeric columns except time/label/metadata
                sensor_columns = [col for col in plot_data.columns if col not in ['time', 'label', 'timestamp', '_source_file']]

            time_column = 'time' if 'time' in plot_data.columns else None

            # Get window info for title (use filtered windows)
            filtered_windows = self._get_filtered_windows()
            window = filtered_windows[self.current_window_index]
            class_label = f" - {window.class_label}" if hasattr(window, 'class_label') and window.class_label else ""

            # Get source file from window data if available
            source_file = ""
            source_file_name = ""
            logger.info(f"Window data columns: {list(plot_data.columns)}")
            if '_source_file' in plot_data.columns:
                # Get the most common source file in this window
                source_files = plot_data['_source_file'].unique()
                if len(source_files) > 0:
                    source_file_name = source_files[0]
                    source_file = f" | File: {source_file_name}"
                    logger.info(f"Found source file: {source_file_name}")
            else:
                logger.warning("_source_file column not found in window data")

            # Update info label with source file
            if source_file_name:
                self.info_label.configure(text=f"📊 Window {self.current_window_index + 1}/{len(filtered_windows)}{class_label} | 📄 Source: {source_file_name}")
            else:
                self.info_label.configure(text=f"📊 Window {self.current_window_index + 1}/{len(filtered_windows)}{class_label}")

            title = f"Window {self.current_window_index + 1}/{len(filtered_windows)}{class_label} ({len(plot_data)} samples){source_file}"
        else:
            # Raw data mode with class filter
            sensor_columns = self.current_data_source.detect_sensor_columns()
            time_column = self.current_data_source.detect_time_column()

            if not sensor_columns:
                logger.warning("No sensor columns detected for plotting")
                return

            data_to_plot = self._apply_class_filter(self.loaded_data)
            start = self.current_batch_start
            end = start + max_samples
            plot_data = data_to_plot.iloc[start:end]

            total_batches = (len(data_to_plot) + max_samples - 1) // max_samples
            current_batch = (start // max_samples) + 1
            title = f"Sensor Data (Batch {current_batch}/{total_batches}, {len(plot_data)} samples)"

        # Plot
        self.sensor_plot.plot_sensors(
            data=plot_data,
            sensor_columns=sensor_columns,
            time_column=time_column,
            title=title,
            xlabel="Time" if time_column else "Sample Index",
            ylabel="Sensor Values"
        )

        logger.info(f"Plotted {len(sensor_columns)} sensors with {len(plot_data)} samples")

    def _apply_class_filter(self, data):
        """Apply class filter to data."""
        if 'label' not in data.columns:
            return data

        selected_class = self.class_filter_var.get()
        if selected_class == "All Classes":
            return data

        return data[data['label'] == selected_class].reset_index(drop=True)

    def _get_filtered_windows(self):
        """Get list of windows filtered by selected class."""
        if not hasattr(self, 'windowing_engine') or self.windowing_engine is None:
            return []

        windows = self.windowing_engine.windows
        if not windows:
            return []

        # Apply class filter
        selected_class = self.class_filter_var.get()
        if selected_class == "All Classes":
            return windows

        # Filter windows by class label
        filtered = [w for w in windows if hasattr(w, 'class_label') and w.class_label == selected_class]
        return filtered

    def _get_window_data(self):
        """Get data for current window index."""
        filtered_windows = self._get_filtered_windows()
        if not filtered_windows or self.current_window_index >= len(filtered_windows):
            return None

        # Return the DataFrame from the window object
        window = filtered_windows[self.current_window_index]
        return window.data

    def _navigate_previous(self):
        """Navigate to previous batch or window."""
        # Allow navigation if we have windows even without loaded_data
        if self.loaded_data is None and self.view_mode != "windows":
            return

        if self.view_mode == "windows":
            if self.current_window_index > 0:
                self.current_window_index -= 1
                self._update_navigation_ui()
                self._refresh_plot()
        else:
            try:
                max_samples = int(self.max_samples_var.get())
            except ValueError:
                max_samples = 1000

            if self.current_batch_start >= max_samples:
                self.current_batch_start -= max_samples
                self._update_navigation_ui()
                self._refresh_plot()

    def _navigate_next(self):
        """Navigate to next batch or window."""
        # Allow navigation if we have windows even without loaded_data
        if self.loaded_data is None and self.view_mode != "windows":
            return

        if self.view_mode == "windows":
            filtered_windows = self._get_filtered_windows()
            if filtered_windows and self.current_window_index < len(filtered_windows) - 1:
                self.current_window_index += 1
                self._update_navigation_ui()
                self._refresh_plot()
        else:
            try:
                max_samples = int(self.max_samples_var.get())
            except ValueError:
                max_samples = 1000

            data_to_plot = self._apply_class_filter(self.loaded_data)
            if self.current_batch_start + max_samples < len(data_to_plot):
                self.current_batch_start += max_samples
                self._update_navigation_ui()
                self._refresh_plot()

    def _update_navigation_ui(self):
        """Update navigation label and button states."""
        if self.view_mode == "windows":
            # Windows mode - use filtered windows
            filtered_windows = self._get_filtered_windows()
            if filtered_windows:
                total = len(filtered_windows)
                current = self.current_window_index + 1
                self.nav_label.configure(text=f"Window {current}/{total}")
                self.prev_btn.configure(state="normal" if self.current_window_index > 0 else "disabled")
                self.next_btn.configure(state="normal" if self.current_window_index < total - 1 else "disabled")
            else:
                self.nav_label.configure(text="No Windows")
                self.prev_btn.configure(state="disabled")
                self.next_btn.configure(state="disabled")
            return

        # Batch mode - requires loaded_data
        if self.loaded_data is None:
            self.nav_label.configure(text="No Data")
            self.prev_btn.configure(state="disabled")
            self.next_btn.configure(state="disabled")
            return
        else:
            try:
                max_samples = int(self.max_samples_var.get())
            except ValueError:
                max_samples = 1000

            data_to_plot = self._apply_class_filter(self.loaded_data)
            total_batches = (len(data_to_plot) + max_samples - 1) // max_samples
            current_batch = (self.current_batch_start // max_samples) + 1

            self.nav_label.configure(text=f"Batch {current_batch}/{total_batches}")
            self.prev_btn.configure(state="normal" if self.current_batch_start > 0 else "disabled")
            self.next_btn.configure(state="normal" if self.current_batch_start + max_samples < len(data_to_plot) else "disabled")

    def _on_view_mode_change(self, mode):
        """Handle view mode change."""
        self.view_mode = "windows" if mode == "Windows" else "raw"
        self.current_batch_start = 0
        self.current_window_index = 0
        self._update_navigation_ui()
        self._refresh_plot()

    def _on_class_filter_change(self, selected_class):
        """Handle class filter change."""
        self.current_batch_start = 0
        self.current_window_index = 0  # Reset window index when filter changes
        self._update_navigation_ui()
        self._refresh_plot()

    def _load_project_data(self) -> None:
        """Load and display existing project data if available."""
        if not self.project_manager.has_project():
            return

        project = self.project_manager.current_project

        # Load pipeline mode
        pipeline_mode = getattr(project.data, 'pipeline_mode', 'ml')
        display_mode = "Traditional ML" if pipeline_mode == "ml" else "Deep Learning"
        self.pipeline_mode_var.set(display_mode)

        # Update pipeline mode info text
        if pipeline_mode == "dl":
            self.pipeline_mode_info.configure(
                text="ℹ️ TimesNet deep learning on raw time series (GPU/CPU auto-detect)"
            )
        else:
            self.pipeline_mode_info.configure(
                text="ℹ️ Feature extraction + sklearn/PyOD models"
            )

        # Show warning if mode is locked
        if getattr(project.data, 'pipeline_mode_locked', False):
            self.pipeline_mode_warning.grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")

        # Load task mode
        task_type = getattr(project.data, 'task_type', 'anomaly_detection')
        display_task = "Classification" if task_type == "classification" else "Anomaly Detection"
        self.task_mode_var.set(display_task)

        # Check if project has windows
        if project.data.num_windows > 0:
            # Check if using manual train/test split
            if project.data.train_test_split_type == "manual":
                # Get source type for display
                source_type = getattr(project.data, 'source_type', 'Unknown')
                source_type_display = {
                    'json': 'Edge Impulse JSON',
                    'cbor': 'Edge Impulse CBOR',
                    'csv': 'CSV'
                }.get(source_type, source_type.upper())

                # Check if source files still exist
                import os
                train_exists = os.path.exists(project.data.train_folder_path) if project.data.train_folder_path else False
                test_exists = os.path.exists(project.data.test_folder_path) if project.data.test_folder_path else False

                source_status = "✓ Source files found" if train_exists else "⚠ Source files not found"

                # Truncate long folder paths for display
                def truncate_path(path, max_length=60):
                    if not path or len(path) <= max_length:
                        return path
                    # Show start and end of path
                    return path[:25] + "..." + path[-(max_length-28):]

                train_path_display = truncate_path(project.data.train_folder_path)
                test_path_display = truncate_path(project.data.test_folder_path)

                # Show train/test split info with source information
                info_text = f"""✓ Project data loaded with manual train/test split!

📁 DATA SOURCE
Format: {source_type_display}
Status: {source_status}
Training folder: {train_path_display or 'N/A'}
Test folder: {test_path_display or 'N/A'}

📊 WINDOWS
Training windows: {project.data.num_train_windows}
Test windows: {project.data.num_test_windows}
Total windows: {project.data.num_windows}
Window size: {project.data.window_size} samples
Overlap: {project.data.overlap * 100:.1f}%
Sampling rate: {project.data.sampling_rate} Hz

🔬 SENSORS
Sensor columns: {len(project.data.sensor_columns)}
Sensors: {', '.join(project.data.sensor_columns) if project.data.sensor_columns else 'N/A'}

💡 Use the 'Raw Data' / 'Windows' toggle in Preview tab to switch views.
To reload or modify data, load a new data source.
                """

                # Populate train/test folder paths in UI
                if project.data.train_folder_path:
                    self.ei_train_path_entry.delete(0, 'end')
                    self.ei_train_path_entry.insert(0, project.data.train_folder_path)
                if project.data.test_folder_path:
                    self.ei_test_path_entry.delete(0, 'end')
                    self.ei_test_path_entry.insert(0, project.data.test_folder_path)
            else:
                # Display standard window information
                info_text = f"""✓ Project data loaded!

Source: {project.data.source_path or 'N/A'}
Windows: {project.data.num_windows}
Window size: {project.data.window_size} samples
Overlap: {project.data.overlap * 100:.1f}%
Sampling rate: {project.data.sampling_rate} Hz
Sensor columns: {len(project.data.sensor_columns)}
Sensors: {', '.join(project.data.sensor_columns) if project.data.sensor_columns else 'N/A'}

To reload or modify data, load a new data source.
To proceed to feature extraction, go to the Feature Extraction stage.
                """

            self.window_stats_label.configure(text=info_text)

            # Set window config values
            self.window_size_var.set(str(project.data.window_size))
            self.overlap_var.set(str(project.data.overlap * 100))
            self.sampling_rate_var.set(str(project.data.sampling_rate))

            # Re-load raw source data if available (for Raw Data view)
            self._reload_source_data_if_available(project)

            # Load windows for preview
            try:
                import pickle
                from pathlib import Path

                # Load windows based on split type
                if project.data.train_test_split_type == "manual":
                    # Load train and test windows
                    if project.data.train_windows_file and project.data.test_windows_file:
                        with open(project.data.train_windows_file, 'rb') as f:
                            train_windows = pickle.load(f)
                        with open(project.data.test_windows_file, 'rb') as f:
                            test_windows = pickle.load(f)
                        # Combine for preview
                        self.windows = train_windows + test_windows
                        logger.info(f"Loaded {len(train_windows)} train + {len(test_windows)} test windows for preview")
                        logger.info(f"Total combined windows: {len(self.windows)}")
                else:
                    # Load single windows file
                    if project.data.windows_file:
                        with open(project.data.windows_file, 'rb') as f:
                            self.windows = pickle.load(f)
                        logger.info(f"Loaded {len(self.windows)} windows for preview")

                # Initialize windowing engine with loaded windows
                if self.windows:
                    from core.windowing import WindowingEngine, WindowConfig
                    config = WindowConfig(
                        window_size=project.data.window_size,
                        overlap=project.data.overlap,
                        sampling_rate=project.data.sampling_rate
                    )
                    self.windowing_engine = WindowingEngine(config)
                    self.windowing_engine.windows = self.windows  # Set windows directly

                    # Update class filter options if in classification mode
                    if hasattr(project.data, 'class_mapping') and project.data.class_mapping:
                        class_names = list(project.data.class_mapping.keys())
                        self.class_filter_menu.configure(values=["All Classes"] + class_names)

                    # Set view mode to windows and update preview
                    self.view_mode = "windows"
                    self.current_window_index = 0

                    # Update info label with data source information
                    num_windows = len(self.windows)

                    # Show which views are available
                    has_raw_data = self.loaded_data is not None
                    view_status = "Raw Data & Windows views available" if has_raw_data else "Windows view only"

                    self.info_label.configure(text=f"📊 {num_windows} windows loaded | {view_status}")

                    # Refresh plot to show first window
                    self._refresh_plot()

            except Exception as e:
                logger.error(f"Error loading windows for preview: {e}")
                import traceback
                traceback.print_exc()

            logger.info(f"Loaded project data: {project.data.num_windows} windows")

    def _reload_source_data_if_available(self, project) -> None:
        """
        Re-load raw source data when opening a saved project.
        This enables Raw Data view mode alongside Windows view.
        """
        import os

        # Check if source paths are stored
        if not hasattr(project.data, 'train_folder_path') or not project.data.train_folder_path:
            logger.info("No source paths stored - Raw Data view will be unavailable")
            return

        # Check if source files still exist
        train_exists = os.path.exists(project.data.train_folder_path)
        test_exists = project.data.test_folder_path and os.path.exists(project.data.test_folder_path)

        if not train_exists:
            logger.warning(f"Source training folder not found: {project.data.train_folder_path}")
            logger.warning("Raw Data view will be unavailable - only Windows view supported")
            return

        # Show progress bar
        self.progress_frame.grid()
        self.progress_label.configure(text="Re-loading source data...")
        self.progress_bar.set(0.1)
        self.update_idletasks()

        try:
            # Always detect format from actual file extensions (don't trust stored metadata)
            import glob
            sample_files = glob.glob(os.path.join(project.data.train_folder_path, '*.*'))
            if sample_files:
                # Check first file extension
                first_file = sample_files[0]
                if first_file.endswith('.cbor'):
                    source_type = 'cbor'
                elif first_file.endswith('.json'):
                    source_type = 'json'
                else:
                    source_type = 'json'  # default
                logger.info(f"Detected source format from file extension: {source_type}")
            else:
                # Fallback to stored value or default
                source_type = getattr(project.data, 'source_type', 'json')
                logger.warning(f"No files found, using stored/default format: {source_type}")

            # Map internal format to UI format string
            format_map = {
                "json": "Edge Impulse JSON",
                "cbor": "Edge Impulse CBOR"
            }
            ui_format = format_map.get(source_type, "Edge Impulse JSON")

            logger.info(f"Re-loading source data from: {project.data.train_folder_path}")
            logger.info(f"Format: {ui_format}")

            self.progress_bar.set(0.3)
            self.update_idletasks()

            # Re-load the data using existing load function
            self._load_edgeimpulse_train_test(
                project.data.train_folder_path,
                project.data.test_folder_path,
                ui_format
            )

            self.progress_bar.set(1.0)
            self.progress_label.configure(text="✓ Source data loaded successfully!")
            self.update_idletasks()

            logger.info("✓ Raw source data re-loaded successfully - both Raw and Windows views available")

            # Hide progress bar after 1 second
            self.after(1000, self.progress_frame.grid_remove)

        except Exception as e:
            logger.error(f"Failed to re-load source data: {e}")
            logger.warning("Raw Data view will be unavailable - only Windows view supported")
            import traceback
            traceback.print_exc()

            # Hide progress bar on error
            self.progress_frame.grid_remove()

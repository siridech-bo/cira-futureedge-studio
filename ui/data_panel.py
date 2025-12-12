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

        # Task Mode selection (NEW - Classification vs Anomaly Detection)
        task_mode_frame = ctk.CTkFrame(tab, fg_color=("gray90", "gray20"))
        task_mode_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
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

        # Data source type selection
        source_frame = ctk.CTkFrame(tab)
        source_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
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
        self.csv_frame = ctk.CTkFrame(tab)
        self.csv_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
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
        self.ei_frame = ctk.CTkFrame(tab)
        self.ei_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        self.ei_frame.grid_columnconfigure(1, weight=1)
        self.ei_frame.grid_remove()  # Hidden by default

        # File path
        ctk.CTkLabel(
            self.ei_frame,
            text="Edge Impulse File:",
            font=("Segoe UI", 12)
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.ei_file_path_entry = ctk.CTkEntry(
            self.ei_frame,
            placeholder_text="Select JSON or CBOR file..."
        )
        self.ei_file_path_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        browse_ei_btn = ctk.CTkButton(
            self.ei_frame,
            text="Browse...",
            command=self._browse_ei_file,
            width=100
        )
        browse_ei_btn.grid(row=0, column=2, padx=10, pady=5)

        # Device info (will be populated after loading)
        self.ei_info_label = ctk.CTkLabel(
            self.ei_frame,
            text="",
            font=("Segoe UI", 10),
            text_color="gray"
        )
        self.ei_info_label.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="w")

        # Database-specific options
        self.db_frame = ctk.CTkFrame(tab)
        self.db_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
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
        self.api_frame = ctk.CTkFrame(tab)
        self.api_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
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
        self.stream_frame = ctk.CTkFrame(tab)
        self.stream_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
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

        # Load button
        load_frame = ctk.CTkFrame(tab, fg_color="transparent")
        load_frame.grid(row=2, column=0, pady=20)

        self.load_btn = ctk.CTkButton(
            load_frame,
            text="Load Data",
            command=self._load_data,
            width=200,
            height=40,
            font=("Segoe UI", 14)
        )
        self.load_btn.pack()

        # Status label
        self.load_status_label = ctk.CTkLabel(
            tab,
            text="",
            font=("Segoe UI", 11),
            text_color="gray"
        )
        self.load_status_label.grid(row=3, column=0, pady=5)

    def _setup_windowing_tab(self) -> None:
        """Setup windowing configuration tab."""
        tab = self.tabview.tab("Windowing")
        tab.grid_columnconfigure(0, weight=1)

        # Windowing parameters
        params_frame = ctk.CTkFrame(tab)
        params_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
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

        # Window stats
        self.window_stats_label = ctk.CTkLabel(
            tab,
            text="",
            font=("Segoe UI", 11),
            text_color="gray",
            justify="left"
        )
        self.window_stats_label.grid(row=2, column=0, pady=10)

    def _setup_preview_tab(self) -> None:
        """Setup data preview tab."""
        tab = self.tabview.tab("Preview")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Info frame
        info_frame = ctk.CTkFrame(tab)
        info_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.info_label = ctk.CTkLabel(
            info_frame,
            text="No data loaded",
            font=("Segoe UI", 12),
            justify="left"
        )
        self.info_label.pack(padx=10, pady=10, anchor="w")

        # Preview text
        preview_frame = ctk.CTkFrame(tab)
        preview_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(0, weight=1)

        self.preview_text = ctk.CTkTextbox(
            preview_frame,
            font=("Courier New", 10)
        )
        self.preview_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    def _on_task_mode_change(self, choice: str) -> None:
        """Handle task mode change between Anomaly Detection and Classification."""
        mode = "classification" if choice == "Classification" else "anomaly_detection"
        logger.info(f"Task mode changed to: {mode}")

        # Update project task type
        if self.project_manager.current_project:
            self.project_manager.current_project.data.task_type = mode
            self.project_manager.save_current_project()

        # Update info text
        if mode == "classification":
            self.task_mode_info.configure(
                text="ℹ️ Trains models to categorize data into predefined classes (requires labeled data)"
            )
        else:
            self.task_mode_info.configure(
                text="ℹ️ Detects unusual patterns in unlabeled data"
            )

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
                file_path = self.ei_file_path_entry.get().strip()
                if not file_path:
                    messagebox.showwarning("No File", "Please select an Edge Impulse file first.")
                    return
                self._load_edgeimpulse_data(file_path, source_type)

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
        """Load Edge Impulse JSON/CBOR data."""
        # Determine format type
        format_type = "json" if source_type == "Edge Impulse JSON" else "cbor"

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
        info_text += f" | Sampling: {sampling_rate:.2f} Hz | Sensors: {len(sensor_info)}"

        self.ei_info_label.configure(text=info_text)

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

        try:
            # Get parameters
            window_size = int(self.window_size_var.get())
            overlap = float(self.overlap_var.get()) / 100.0  # Convert to ratio
            sampling_rate = float(self.sampling_rate_var.get())

            # Create windowing config
            config = WindowConfig(
                window_size=window_size,
                overlap=overlap,
                sampling_rate=sampling_rate
            )

            # Initialize windowing engine
            self.windowing_engine = WindowingEngine(config)

            # Detect sensor columns
            sensor_columns = self.current_data_source.detect_sensor_columns()
            time_column = self.current_data_source.detect_time_column()

            if not sensor_columns:
                raise ValueError("No numeric sensor columns found in data")

            # Segment data
            windows = self.windowing_engine.segment_data(
                self.loaded_data,
                sensor_columns=sensor_columns,
                time_column=time_column
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

            self.window_stats_label.configure(text=stats_text)

            # Save to project
            if self.project_manager.has_project():
                project = self.project_manager.get_project()
                project.data.window_size = window_size
                project.data.sampling_rate = sampling_rate
                project.data.overlap = overlap
                project.data.sensor_columns = sensor_columns

                # Save windows to disk
                project.save_windows(windows, sensor_columns, time_column)

                project.mark_stage_completed("data")
                self.project_manager.save_project()

            logger.info(f"Created {len(windows)} windows")
            messagebox.showinfo("Success", f"Created {len(windows)} windows successfully!")

        except Exception as e:
            logger.error(f"Failed to create windows: {e}")
            messagebox.showerror("Windowing Error", f"Failed to create windows:\n{e}")

    def _update_preview(self) -> None:
        """Update data preview."""
        if self.loaded_data is None:
            return

        # Update info
        info_text = f"""Data Info:
Rows: {len(self.loaded_data)}
Columns: {len(self.loaded_data.columns)}
Memory: {self.loaded_data.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB

Columns: {', '.join(self.loaded_data.columns)}

Detected:
- Time column: {self.current_data_source.detect_time_column() or 'None'}
- Sensor columns: {', '.join(self.current_data_source.detect_sensor_columns())}
        """

        self.info_label.configure(text=info_text)

        # Update preview text
        self.preview_text.delete("1.0", "end")
        preview_df = self.loaded_data.head(20)
        self.preview_text.insert("1.0", preview_df.to_string())

    def _load_project_data(self) -> None:
        """Load and display existing project data if available."""
        if not self.project_manager.has_project():
            return

        project = self.project_manager.current_project

        # Check if project has windows
        if project.data.num_windows > 0:
            # Display window information
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

            logger.info(f"Loaded project data: {project.data.num_windows} windows")

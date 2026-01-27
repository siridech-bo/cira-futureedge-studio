"""
Streaming Data Source

Captures real-time data from streaming protocols (MQTT, WebSocket, Serial).
"""

from typing import Optional, Dict, Any, List, Callable
import pandas as pd
from loguru import logger
import time
import threading
from queue import Queue
from .base import DataSource, DataSourceConfig, DataSourceFactory


class StreamingDataSource(DataSource):
    """Data source for real-time streaming data."""

    def __init__(self, config: DataSourceConfig):
        """
        Initialize streaming data source.

        Args:
            config: Data source configuration with parameters:
                - protocol: Streaming protocol ("mqtt", "websocket", "serial")

                For MQTT:
                - broker: MQTT broker address
                - port: MQTT broker port (default 1883)
                - topic: MQTT topic to subscribe to
                - username: MQTT username (optional)
                - password: MQTT password (optional)
                - qos: Quality of Service (0, 1, or 2)

                For WebSocket:
                - url: WebSocket URL
                - headers: Additional headers (dict)

                For Serial:
                - port: Serial port (e.g., "COM3" or "/dev/ttyUSB0")
                - baudrate: Baud rate (default 9600)
                - timeout: Read timeout in seconds

                Common:
                - duration: Recording duration in seconds
                - max_samples: Maximum number of samples to collect
                - parse_json: Parse messages as JSON
                - time_column: Timestamp column name (or auto-generate)
        """
        super().__init__(config)
        self.client = None
        self.is_streaming = False
        self.data_queue = Queue()
        self.stream_thread = None

    def connect(self) -> bool:
        """Connect to the streaming source."""
        params = self.config.parameters
        protocol = params.get("protocol", "mqtt")

        try:
            if protocol == "mqtt":
                return self._connect_mqtt()
            elif protocol == "websocket":
                return self._connect_websocket()
            elif protocol == "serial":
                return self._connect_serial()
            else:
                logger.error(f"Unsupported streaming protocol: {protocol}")
                return False

        except Exception as e:
            logger.error(f"Failed to connect to {protocol} stream: {e}")
            return False

    def _connect_mqtt(self) -> bool:
        """Connect to MQTT broker."""
        try:
            import paho.mqtt.client as mqtt

            params = self.config.parameters
            broker = params.get("broker", "localhost")
            port = params.get("port", 1883)
            topic = params.get("topic")

            if not topic:
                raise ValueError("MQTT topic is required")

            # Create MQTT client
            self.client = mqtt.Client()

            # Setup callbacks
            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    logger.info(f"Connected to MQTT broker: {broker}:{port}")
                    client.subscribe(topic)
                else:
                    logger.error(f"MQTT connection failed with code: {rc}")

            def on_message(client, userdata, msg):
                self.data_queue.put({
                    "timestamp": time.time(),
                    "topic": msg.topic,
                    "payload": msg.payload.decode()
                })

            self.client.on_connect = on_connect
            self.client.on_message = on_message

            # Setup authentication if provided
            username = params.get("username")
            password = params.get("password")
            if username and password:
                self.client.username_pw_set(username, password)

            # Connect
            self.client.connect(broker, port, 60)
            self.client.loop_start()

            self.is_connected = True
            return True

        except ImportError:
            logger.error("paho-mqtt not installed. Install with: pip install paho-mqtt")
            return False

    def _connect_websocket(self) -> bool:
        """Connect to WebSocket."""
        try:
            import websocket

            params = self.config.parameters
            url = params.get("url")

            if not url:
                raise ValueError("WebSocket URL is required")

            def on_message(ws, message):
                self.data_queue.put({
                    "timestamp": time.time(),
                    "message": message
                })

            def on_error(ws, error):
                logger.error(f"WebSocket error: {error}")

            def on_close(ws, close_status_code, close_msg):
                logger.info("WebSocket connection closed")

            def on_open(ws):
                logger.info(f"Connected to WebSocket: {url}")

            # Create WebSocket connection
            headers = params.get("headers", {})
            self.client = websocket.WebSocketApp(
                url,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open,
                header=headers
            )

            self.is_connected = True
            return True

        except ImportError:
            logger.error("websocket-client not installed. Install with: pip install websocket-client")
            return False

    def _connect_serial(self) -> bool:
        """Connect to serial port."""
        try:
            import serial

            params = self.config.parameters
            port = params.get("port")
            baudrate = params.get("baudrate", 9600)
            timeout = params.get("timeout", 1)

            if not port:
                raise ValueError("Serial port is required")

            self.client = serial.Serial(port, baudrate, timeout=timeout)
            logger.info(f"Connected to serial port: {port} at {baudrate} baud")

            self.is_connected = True
            return True

        except ImportError:
            logger.error("pyserial not installed. Install with: pip install pyserial")
            return False

    def disconnect(self) -> None:
        """Disconnect from streaming source."""
        self.is_streaming = False

        params = self.config.parameters
        protocol = params.get("protocol", "mqtt")

        if self.client:
            if protocol == "mqtt":
                self.client.loop_stop()
                self.client.disconnect()
            elif protocol == "websocket":
                self.client.close()
            elif protocol == "serial":
                self.client.close()

            self.client = None

        self.is_connected = False
        logger.info(f"{protocol.upper()} connection closed")

    def load_data(self, **kwargs) -> pd.DataFrame:
        """
        Start streaming and collect data.

        Returns:
            DataFrame with collected streaming data

        Raises:
            Exception if not connected
        """
        if not self.is_connected:
            raise Exception("Not connected. Call connect() first.")

        params = self.config.parameters
        protocol = params.get("protocol", "mqtt")
        duration = params.get("duration", 10)  # Default 10 seconds
        max_samples = params.get("max_samples", None)
        parse_json = params.get("parse_json", False)

        # Clear queue
        while not self.data_queue.empty():
            self.data_queue.get()

        self.is_streaming = True

        # Start streaming thread for WebSocket
        if protocol == "websocket":
            self.stream_thread = threading.Thread(target=self.client.run_forever)
            self.stream_thread.daemon = True
            self.stream_thread.start()

        # Start serial reading thread
        elif protocol == "serial":
            def read_serial():
                while self.is_streaming:
                    try:
                        if self.client.in_waiting > 0:
                            line = self.client.readline().decode().strip()
                            if line:
                                self.data_queue.put({
                                    "timestamp": time.time(),
                                    "data": line
                                })
                    except Exception as e:
                        logger.error(f"Serial read error: {e}")
                        time.sleep(0.1)

            self.stream_thread = threading.Thread(target=read_serial)
            self.stream_thread.daemon = True
            self.stream_thread.start()

        # Collect data for specified duration
        logger.info(f"Collecting streaming data for {duration} seconds...")
        start_time = time.time()
        samples_collected = 0

        while self.is_streaming:
            # Check duration
            if time.time() - start_time >= duration:
                break

            # Check max samples
            if max_samples and samples_collected >= max_samples:
                break

            time.sleep(0.1)
            samples_collected = self.data_queue.qsize()

        self.is_streaming = False

        # Convert queue to list
        data_list = []
        while not self.data_queue.empty():
            data_list.append(self.data_queue.get())

        if not data_list:
            logger.warning("No data collected from stream")
            return pd.DataFrame()

        # Parse JSON if enabled
        if parse_json:
            import json
            parsed_data = []
            for item in data_list:
                try:
                    if protocol == "mqtt":
                        payload = json.loads(item["payload"])
                        payload["timestamp"] = item["timestamp"]
                        payload["topic"] = item["topic"]
                        parsed_data.append(payload)
                    elif protocol == "websocket":
                        message = json.loads(item["message"])
                        message["timestamp"] = item["timestamp"]
                        parsed_data.append(message)
                    elif protocol == "serial":
                        data = json.loads(item["data"])
                        data["timestamp"] = item["timestamp"]
                        parsed_data.append(data)
                except json.JSONDecodeError:
                    parsed_data.append(item)
            data_list = parsed_data

        # Convert to DataFrame
        df = pd.DataFrame(data_list)

        # Ensure timestamp column
        time_column = params.get("time_column", "timestamp")
        if time_column in df.columns:
            df[time_column] = pd.to_datetime(df[time_column], unit='s')
        else:
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit='s')

        logger.info(f"Collected {len(df)} samples from {protocol.upper()} stream")
        self._data = df
        return df


# Register the data source
DataSourceFactory.register("streaming", StreamingDataSource)

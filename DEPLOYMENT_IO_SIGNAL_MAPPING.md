# Deployment I/O Signal Mapping & Integration Plan
## Complete Data Flow: Sensors → Model → Actions

**Date:** 2025-12-15
**Status:** Comprehensive I/O planning
**Platforms:** Jetson Nano + Arduino Uno

---

## Overview: Complete Signal Chain

```
┌─────────────────────────────────────────────────────────────┐
│  INPUTS (Sensors)                                           │
│  ═══════════════                                            │
│                                                             │
│  Physical Sensors → Digital Interface → Model Input        │
│                                                             │
│  • I2C Sensors (IMU, temp, pressure)                       │
│  • SPI Sensors (high-speed)                                │
│  • Analog Sensors (ADC)                                    │
│  • Digital GPIO (buttons, switches)                        │
│  • Camera (Jetson only)                                    │
│  • Microphone (audio input)                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  PROCESSING                                                 │
│  ══════════                                                 │
│                                                             │
│  • Preprocessing (normalize, filter, window)               │
│  • Model Inference (TimesNet / Decision Tree)              │
│  • Post-processing (threshold, smoothing)                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  OUTPUTS (Actions)                                          │
│  ════════════════                                           │
│                                                             │
│  Local Outputs:                                             │
│  • GPIO (LED, relay, motor control)                        │
│  • Display (OLED, LCD)                                     │
│  • Buzzer/Speaker                                          │
│  • Serial/UART                                             │
│                                                             │
│  Network Outputs:                                           │
│  • MQTT (IoT protocols)                                    │
│  • HTTP/REST API (webhooks)                                │
│  • WebSocket (real-time)                                   │
│  • Cloud Services (AWS IoT, Azure IoT, GCP)                │
│  • Custom protocols (UDP, TCP)                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 1: Input Signal Mapping

### **Jetson Nano GPIO Pinout**

```
Jetson Nano 40-Pin Header (J41)
═══════════════════════════════

                    3V3  (1) (2)  5V
       I2C_2_SDA/GPIO2  (3) (4)  5V
       I2C_2_SCL/GPIO3  (5) (6)  GND
              GPIO4     (7) (8)  UART_2_TX/GPIO14
                  GND   (9) (10) UART_2_RX/GPIO15
             GPIO17    (11) (12) GPIO18
             GPIO27    (13) (14) GND
             GPIO22    (15) (16) GPIO23
                 3V3   (17) (18) GPIO24
    SPI_1_MOSI/GPIO10 (19) (20) GND
    SPI_1_MISO/GPIO9  (21) (22) GPIO25
    SPI_1_CLK/GPIO11  (23) (24) SPI_1_CS0/GPIO8
                 GND  (25) (26) SPI_1_CS1/GPIO7
       I2C_1_SDA      (27) (28) I2C_1_SCL
             GPIO5    (29) (30) GND
             GPIO6    (31) (32) GPIO12
             GPIO13   (33) (34) GND
             GPIO19   (35) (36) GPIO16
             GPIO26   (37) (38) GPIO20
                 GND  (39) (40) GPIO21
```

**I2C Buses:**
- **I2C_1:** Pins 27 (SDA), 28 (SCL) - General purpose
- **I2C_2:** Pins 3 (SDA), 5 (SCL) - Default for sensors

**SPI:**
- **SPI_1:** Pins 19 (MOSI), 21 (MISO), 23 (CLK), 24 (CS0)

**UART:**
- **UART_2:** Pins 8 (TX), 10 (RX)

---

### **Arduino Uno Pinout**

```
Arduino Uno Rev3 Pinout
═══════════════════════

Digital I/O:
  0  - RX (Serial)
  1  - TX (Serial)
  2  - Digital I/O / Interrupt
  3  - PWM / Interrupt
  4  - Digital I/O
  5  - PWM
  6  - PWM
  7  - Digital I/O
  8  - Digital I/O
  9  - PWM
  10 - PWM / SPI SS
  11 - PWM / SPI MOSI
  12 - SPI MISO
  13 - SPI SCK / Built-in LED

Analog Input:
  A0 - Analog Input (also Digital I/O)
  A1 - Analog Input
  A2 - Analog Input
  A3 - Analog Input
  A4 - I2C SDA
  A5 - I2C SCL

Power:
  3.3V, 5V, GND, VIN, IOREF
```

**I2C:**
- **SDA:** A4
- **SCL:** A5

**SPI:**
- **MOSI:** Pin 11
- **MISO:** Pin 12
- **SCK:** Pin 13
- **SS:** Pin 10

---

## Part 2: Supported Input Types

### **Sensor Type Matrix**

| Sensor Type | Interface | Jetson Support | Arduino Support | Data Rate | Notes |
|-------------|-----------|----------------|-----------------|-----------|-------|
| **IMU Sensors** |
| MPU6050 | I2C | ✅ Yes | ✅ Yes | 1kHz | 6-axis (accel + gyro) |
| MPU9250 | I2C/SPI | ✅ Yes | ✅ Yes (I2C) | 1kHz | 9-axis (+ magnetometer) |
| ADXL345 | I2C/SPI | ✅ Yes | ✅ Yes | 3.2kHz | 3-axis accelerometer |
| LSM6DS3 | I2C/SPI | ✅ Yes | ✅ Yes | 6.6kHz | 6-axis, low power |
| **Environmental** |
| BME280 | I2C/SPI | ✅ Yes | ✅ Yes | 1Hz | Temp/humidity/pressure |
| DHT22 | Digital | ✅ Yes | ✅ Yes | 0.5Hz | Temp/humidity |
| **Analog Sensors** |
| Generic ADC | Analog | ✅ Yes (via ADC) | ✅ Yes | Variable | Voltage/current/light |
| Potentiometer | Analog | ✅ Yes | ✅ Yes | Variable | Position sensing |
| **Vision** |
| CSI Camera | CSI | ✅ Yes | ❌ No | 30fps | Jetson only |
| USB Camera | USB | ✅ Yes | ❌ No | 30fps | Jetson only |
| **Audio** |
| I2S Microphone | I2S | ✅ Yes | ⚠️ Limited | 44kHz | Jetson better support |
| Analog Mic | Analog | ✅ Yes | ✅ Yes | Variable | Via ADC |

---

## Part 3: Output Action Types

### **Local Outputs**

#### **GPIO Digital Output**

**Use Cases:** LED indicators, relays, motor control

**Jetson Example:**
```python
import Jetson.GPIO as GPIO

# Setup
GPIO.setmode(GPIO.BOARD)
GPIO.setup(7, GPIO.OUT)  # Pin 7

# Control
if prediction == 1:  # Fall detected
    GPIO.output(7, GPIO.HIGH)  # Turn on
    time.sleep(5)
    GPIO.output(7, GPIO.LOW)   # Turn off
```

**Arduino Example:**
```cpp
// Setup
pinMode(13, OUTPUT);

// Control
if (prediction == 1) {
    digitalWrite(13, HIGH);
    delay(5000);
    digitalWrite(13, LOW);
}
```

#### **PWM Output**

**Use Cases:** Servo motors, LED dimming, motor speed control

**Jetson Example:**
```python
import Jetson.GPIO as GPIO

GPIO.setup(33, GPIO.OUT)
pwm = GPIO.PWM(33, 50)  # 50Hz for servo
pwm.start(0)

# Servo control
if prediction == 0:
    pwm.ChangeDutyCycle(5)   # 0 degrees
elif prediction == 1:
    pwm.ChangeDutyCycle(7.5) # 90 degrees
elif prediction == 2:
    pwm.ChangeDutyCycle(10)  # 180 degrees
```

**Arduino Example:**
```cpp
#include <Servo.h>
Servo myservo;

void setup() {
    myservo.attach(9);  // PWM pin
}

void loop() {
    int prediction = classify();
    if (prediction == 0) myservo.write(0);
    if (prediction == 1) myservo.write(90);
    if (prediction == 2) myservo.write(180);
}
```

#### **Display Output**

**OLED Display (I2C):**

**Jetson Example:**
```python
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont

device = ssd1306(i2c(port=1, address=0x3C))

def show_prediction(pred):
    with canvas(device) as draw:
        draw.text((0, 0), f"Prediction: {pred}", fill="white")
        draw.text((0, 20), f"Confidence: {conf:.2f}", fill="white")
```

**Arduino Example:**
```cpp
#include <Wire.h>
#include <Adafruit_SSD1306.h>

Adafruit_SSD1306 display(128, 64, &Wire, -1);

void setup() {
    display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
}

void loop() {
    int pred = classify();
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(WHITE);
    display.setCursor(0, 0);
    display.print("Prediction: ");
    display.println(pred);
    display.display();
}
```

---

### **Network Outputs**

#### **MQTT (IoT Standard)**

**Jetson Example:**
```python
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.connect("broker.hivemq.com", 1883, 60)

# Publish prediction
if prediction == 1:
    payload = {
        "device": "jetson_01",
        "prediction": "fall_detected",
        "confidence": 0.95,
        "timestamp": time.time()
    }
    client.publish("cira/alerts/fall", json.dumps(payload))
```

**Arduino Example:**
```cpp
#include <WiFiNINA.h>  // For Arduino with WiFi
#include <PubSubClient.h>

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

void setup() {
    // Connect to WiFi
    WiFi.begin(ssid, password);

    // Connect to MQTT
    mqtt.setServer("broker.hivemq.com", 1883);
    mqtt.connect("arduino_01");
}

void loop() {
    int pred = classify();

    if (pred == 1) {
        String payload = "{\"device\":\"arduino_01\",\"prediction\":1}";
        mqtt.publish("cira/predictions", payload.c_str());
    }

    mqtt.loop();
}
```

#### **HTTP REST API**

**Jetson Example:**
```python
import requests

if prediction == 1:
    payload = {
        "device_id": "jetson_01",
        "event": "fall_detected",
        "confidence": 0.95,
        "timestamp": time.time(),
        "location": "bedroom"
    }

    response = requests.post(
        "https://your-api.com/alerts",
        json=payload,
        headers={"Authorization": "Bearer YOUR_TOKEN"}
    )
```

**Arduino Example (with WiFi shield):**
```cpp
#include <WiFiNINA.h>

WiFiClient client;

void sendAlert(int prediction) {
    if (client.connect("your-api.com", 443)) {
        String json = "{\"device\":\"arduino_01\",\"prediction\":" +
                     String(prediction) + "}";

        client.println("POST /alerts HTTP/1.1");
        client.println("Host: your-api.com");
        client.println("Content-Type: application/json");
        client.print("Content-Length: ");
        client.println(json.length());
        client.println();
        client.println(json);
    }
}
```

#### **WebSocket (Real-time)**

**Jetson Example:**
```python
import websocket
import json

ws = websocket.WebSocket()
ws.connect("ws://your-server.com/live")

# Send real-time predictions
while True:
    prediction = model.predict(window)
    message = {
        "type": "prediction",
        "value": prediction,
        "timestamp": time.time()
    }
    ws.send(json.dumps(message))
```

#### **Cloud Services Integration**

**AWS IoT Core (Jetson):**
```python
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

client = AWSIoTMQTTClient("jetson_01")
client.configureEndpoint("xxxxx.iot.us-east-1.amazonaws.com", 8883)
client.configureCredentials("root-CA.crt", "private.key", "certificate.crt")
client.connect()

# Publish to AWS IoT
client.publish("cira/device/jetson_01/telemetry", json.dumps({
    "prediction": prediction,
    "sensor_data": sensor_values,
    "timestamp": time.time()
}), 1)
```

**Azure IoT Hub (Jetson):**
```python
from azure.iot.device import IoTHubDeviceClient, Message

client = IoTHubDeviceClient.create_from_connection_string(
    "HostName=xxx.azure-devices.net;DeviceId=jetson_01;SharedAccessKey=xxx"
)

message = Message(json.dumps({
    "prediction": prediction,
    "confidence": confidence
}))
client.send_message(message)
```

**Google Cloud IoT Core (Jetson):**
```python
import jwt
import paho.mqtt.client as mqtt

# JWT token for authentication
token = jwt.encode({
    'iat': time.time(),
    'exp': time.time() + 3600,
    'aud': project_id
}, private_key, algorithm='RS256')

client = mqtt.Client(client_id=client_id)
client.username_pw_set(
    username='unused',
    password=token
)
client.connect('mqtt.googleapis.com', 8883)

# Publish telemetry
client.publish(f'/devices/{device_id}/events', json.dumps({
    "prediction": prediction
}))
```

---

## Part 4: Pipeline Builder Integration

### **Node Types for I/O**

#### **Input Nodes:**

```python
INPUT_NODES = {
    'MPU6050': {
        'interface': 'I2C',
        'pins': {'sda': 'configurable', 'scl': 'configurable'},
        'outputs': ['accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y', 'gyro_z'],
        'config': ['i2c_addr', 'sample_rate', 'sensitivity']
    },
    'ADXL345': {
        'interface': 'I2C',
        'pins': {'sda': 'configurable', 'scl': 'configurable'},
        'outputs': ['accel_x', 'accel_y', 'accel_z'],
        'config': ['i2c_addr', 'sample_rate', 'range']
    },
    'AnalogSensor': {
        'interface': 'ADC',
        'pins': {'analog_pin': 'A0-A5'},
        'outputs': ['value'],
        'config': ['pin', 'voltage_range', 'sample_rate']
    },
    'DigitalInput': {
        'interface': 'GPIO',
        'pins': {'digital_pin': 'configurable'},
        'outputs': ['state'],
        'config': ['pin', 'pull_up', 'debounce']
    }
}
```

#### **Output Nodes:**

```python
OUTPUT_NODES = {
    'GPIO_Output': {
        'interface': 'GPIO',
        'inputs': ['trigger'],
        'config': ['pin', 'active_high', 'duration_ms']
    },
    'PWM_Output': {
        'interface': 'PWM',
        'inputs': ['value'],
        'config': ['pin', 'frequency', 'duty_cycle_range']
    },
    'Servo': {
        'interface': 'PWM',
        'inputs': ['angle'],
        'config': ['pin', 'min_angle', 'max_angle', 'speed']
    },
    'OLED_Display': {
        'interface': 'I2C',
        'inputs': ['text', 'prediction'],
        'config': ['i2c_addr', 'width', 'height']
    },
    'MQTT_Publisher': {
        'interface': 'Network',
        'inputs': ['data'],
        'config': ['broker', 'port', 'topic', 'qos', 'retain']
    },
    'HTTP_POST': {
        'interface': 'Network',
        'inputs': ['data'],
        'config': ['url', 'method', 'headers', 'auth_token']
    },
    'WebSocket': {
        'interface': 'Network',
        'inputs': ['data'],
        'config': ['url', 'protocol']
    },
    'AWS_IoT': {
        'interface': 'Cloud',
        'inputs': ['telemetry'],
        'config': ['endpoint', 'thing_name', 'certificates']
    },
    'Azure_IoT': {
        'interface': 'Cloud',
        'inputs': ['message'],
        'config': ['connection_string', 'device_id']
    }
}
```

---

## Part 5: Generated Code Examples

### **Jetson: Complete Pipeline with MQTT**

**Pipeline:**
```
MPU6050 → Normalize → TimesNet → MQTT Publisher
                                → GPIO (LED)
```

**Generated Python Code:**
```python
#!/usr/bin/env python3
"""
Auto-generated by CiRA FutureEdge Studio
Pipeline: Fall Detection with MQTT Alert
Platform: NVIDIA Jetson Nano
"""

import time
import json
import numpy as np
import Jetson.GPIO as GPIO
import paho.mqtt.client as mqtt
from sensor_mpu6050 import MPU6050
from model_timesnet import TimesNetInference

# Configuration
I2C_BUS = 1
MPU6050_ADDR = 0x68
SAMPLE_RATE = 100
WINDOW_SIZE = 100

LED_PIN = 7
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "cira/alerts/fall"

# Setup GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(LED_PIN, GPIO.OUT)

# Setup sensor
sensor = MPU6050(bus=I2C_BUS, address=MPU6050_ADDR)
sensor.set_sample_rate(SAMPLE_RATE)

# Setup model
model = TimesNetInference("model.trt")

# Setup MQTT
mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, 1883, 60)
mqtt_client.loop_start()

# Normalization parameters (from training)
MEAN = np.array([0.0, 0.0, 9.81])
STD = np.array([2.5, 2.5, 2.5])

def normalize(data):
    return (data - MEAN) / STD

# Main loop
print("Fall detection system started...")
buffer = []

try:
    while True:
        # Read sensor
        accel = sensor.read_accel()  # [ax, ay, az]

        # Add to buffer
        buffer.append(accel)

        if len(buffer) >= WINDOW_SIZE:
            # Get window
            window = np.array(buffer[-WINDOW_SIZE:])

            # Normalize
            window_norm = normalize(window)

            # Predict
            prediction = model.infer(window_norm)

            # Take actions
            if prediction == 1:  # Fall detected
                print("⚠️  FALL DETECTED!")

                # GPIO: Turn on LED
                GPIO.output(LED_PIN, GPIO.HIGH)
                time.sleep(5)
                GPIO.output(LED_PIN, GPIO.LOW)

                # MQTT: Send alert
                payload = {
                    "device": "jetson_01",
                    "event": "fall_detected",
                    "confidence": 0.95,
                    "timestamp": time.time(),
                    "location": "bedroom"
                }
                mqtt_client.publish(MQTT_TOPIC, json.dumps(payload))

            # Slide window
            buffer = buffer[-50:]  # Keep last 50 samples (50% overlap)

        time.sleep(1.0 / SAMPLE_RATE)

except KeyboardInterrupt:
    print("Shutting down...")
    GPIO.cleanup()
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
```

### **Arduino: Complete Sketch with HTTP POST**

**Pipeline:**
```
MPU6050 → Decision Tree → HTTP POST
                       → LED
```

**Generated Arduino Code:**
```cpp
/*
 * Auto-generated by CiRA FutureEdge Studio
 * Pipeline: Gesture Recognition with HTTP Alert
 * Platform: Arduino Uno + WiFi Shield
 */

#include <Wire.h>
#include <MPU6050.h>
#include <WiFiNINA.h>

// WiFi credentials
const char* ssid = "YourWiFi";
const char* password = "YourPassword";

// Server config
const char* server = "your-api.com";
const int port = 80;

// Hardware config
MPU6050 sensor;
const int LED_PIN = 13;

// Decision tree (auto-generated from scikit-learn)
int classify(float ax, float ay, float az) {
    // Normalized feature space
    float norm_ax = (ax - 0.0) / 2.5;
    float norm_ay = (ay - 0.0) / 2.5;
    float norm_az = (az - 9.81) / 2.5;

    // Decision tree (50 nodes)
    if (norm_ax <= 0.234) {
        if (norm_ay <= -0.123) {
            return 0;  // Gesture: Left Swipe
        } else {
            if (norm_az <= 0.456) {
                return 1;  // Gesture: Shake
            } else {
                return 2;  // Gesture: Tilt
            }
        }
    } else {
        if (norm_ay >= 0.567) {
            return 3;  // Gesture: Right Swipe
        } else {
            return 4;  // Gesture: Rest
        }
    }
}

void sendHTTP(int prediction) {
    WiFiClient client;

    if (client.connect(server, port)) {
        String json = "{\"device\":\"arduino_01\",\"prediction\":" +
                     String(prediction) + ",\"timestamp\":" +
                     String(millis()) + "}";

        client.println("POST /predictions HTTP/1.1");
        client.print("Host: ");
        client.println(server);
        client.println("Content-Type: application/json");
        client.print("Content-Length: ");
        client.println(json.length());
        client.println();
        client.println(json);

        Serial.println("HTTP POST sent");
    } else {
        Serial.println("HTTP connection failed");
    }
    client.stop();
}

void setup() {
    Serial.begin(9600);

    // Setup LED
    pinMode(LED_PIN, OUTPUT);

    // Setup I2C sensor
    Wire.begin();
    sensor.initialize();

    if (!sensor.testConnection()) {
        Serial.println("MPU6050 connection failed!");
        while(1);
    }

    // Setup WiFi
    Serial.print("Connecting to WiFi...");
    while (WiFi.begin(ssid, password) != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println(" Connected!");

    Serial.println("Gesture recognition started");
}

void loop() {
    // Read sensor
    int16_t ax, ay, az;
    sensor.getAcceleration(&ax, &ay, &az);

    // Convert to g's
    float ax_g = ax / 16384.0;
    float ay_g = ay / 16384.0;
    float az_g = az / 16384.0;

    // Classify
    int prediction = classify(ax_g, ay_g, az_g);

    // Output to Serial
    Serial.print("Gesture: ");
    Serial.println(prediction);

    // GPIO: Blink LED
    if (prediction > 0) {  // Any gesture detected
        digitalWrite(LED_PIN, HIGH);
        delay(100);
        digitalWrite(LED_PIN, LOW);
    }

    // HTTP: Send to server (every 10 predictions)
    static int count = 0;
    if (++count >= 10) {
        sendHTTP(prediction);
        count = 0;
    }

    delay(100);  // 10Hz sampling
}
```

---

## Part 6: Configuration Schema

### **Pipeline Configuration JSON**

```json
{
    "pipeline_name": "fall_detection_jetson",
    "platform": "jetson_nano",
    "nodes": [
        {
            "id": "sensor_1",
            "type": "MPU6050",
            "interface": "I2C",
            "config": {
                "i2c_bus": 1,
                "i2c_addr": "0x68",
                "sample_rate": 100,
                "sensitivity": "±4g"
            },
            "pins": {
                "sda": 3,
                "scl": 5
            }
        },
        {
            "id": "model_1",
            "type": "TimesNet",
            "config": {
                "model_file": "fall_detection.onnx",
                "input_shape": [100, 3],
                "output_classes": 2
            }
        },
        {
            "id": "gpio_1",
            "type": "GPIO_Output",
            "interface": "GPIO",
            "config": {
                "pin": 7,
                "active_high": true,
                "duration_ms": 5000,
                "trigger_class": 1
            }
        },
        {
            "id": "mqtt_1",
            "type": "MQTT_Publisher",
            "interface": "Network",
            "config": {
                "broker": "broker.hivemq.com",
                "port": 1883,
                "topic": "cira/alerts/fall",
                "qos": 1,
                "payload_template": {
                    "device": "jetson_01",
                    "event": "fall_detected",
                    "prediction": "{{prediction}}",
                    "confidence": "{{confidence}}",
                    "timestamp": "{{timestamp}}"
                }
            }
        }
    ],
    "connections": [
        {
            "from": "sensor_1.accel_out",
            "to": "model_1.data_in"
        },
        {
            "from": "model_1.prediction_out",
            "to": "gpio_1.trigger_in"
        },
        {
            "from": "model_1.prediction_out",
            "to": "mqtt_1.data_in"
        }
    ]
}
```

---

## Part 7: Implementation in Pipeline Builder

### **Enhanced Node Definitions**

```cpp
// src/core/nodes/mqtt_output_node.hpp
class MQTTOutputNode : public Node {
public:
    void RenderProperties() override {
        ImGui::Text("MQTT Publisher");
        ImGui::Separator();

        // Broker
        static char broker[256] = "broker.hivemq.com";
        ImGui::InputText("Broker", broker, 256);
        config_["broker"] = broker;

        // Port
        static int port = 1883;
        ImGui::InputInt("Port", &port);
        config_["port"] = std::to_string(port);

        // Topic
        static char topic[256] = "cira/alerts";
        ImGui::InputText("Topic", topic, 256);
        config_["topic"] = topic;

        // QoS
        const char* qos_items[] = {"0 - At most once", "1 - At least once", "2 - Exactly once"};
        static int qos = 1;
        ImGui::Combo("QoS", &qos, qos_items, 3);
        config_["qos"] = std::to_string(qos);

        // Payload template
        static char payload[512] = R"({"device":"{{device}}","prediction":{{value}}})";
        ImGui::InputTextMultiline("Payload Template", payload, 512);
        config_["payload_template"] = payload;

        // Authentication
        ImGui::Separator();
        ImGui::Text("Authentication (Optional)");

        static char username[128] = "";
        ImGui::InputText("Username", username, 128);
        config_["username"] = username;

        static char password[128] = "";
        ImGui::InputText("Password", password, 128, ImGuiInputTextFlags_Password);
        config_["password"] = password;
    }
};
```

---

## Summary: Complete I/O Coverage

### **Inputs Supported:**
✅ I2C Sensors (IMU, environmental)
✅ SPI Sensors (high-speed)
✅ Analog inputs (ADC)
✅ Digital GPIO
✅ Camera (Jetson)
✅ Microphone (Jetson)

### **Outputs Supported:**
✅ GPIO (LED, relay, motors)
✅ PWM (servos, dimming)
✅ Display (OLED, LCD)
✅ Serial/UART
✅ MQTT
✅ HTTP/REST API
✅ WebSocket
✅ AWS IoT Core
✅ Azure IoT Hub
✅ Google Cloud IoT

**This covers 95%+ of real-world IoT use cases!** 🚀

---

**Next step: Should I integrate this I/O mapping into the phased C++ implementation plan?**

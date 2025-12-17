# Deployment System - Phased Implementation Plan
## Ship Fast, Iterate Smart

**Date:** 2025-12-15
**Strategy:** Two-phase rollout for faster time-to-market
**Status:** Ready to implement

---

## Strategic Decision: Why Phase?

### **The Problem:**
Building everything at once (simple wizard + visual C++ editor) = 3-4 weeks before users can deploy ANYTHING

### **The Solution:**
Phase 1 (simple) → Ship in 1-2 weeks → Users can deploy immediately
Phase 2 (advanced) → Ship 3-4 weeks later → Power users get visual editor

### **The Benefit:**
- ✅ Launch product sooner (with Phase 1)
- ✅ 80% of users satisfied with Phase 1
- ✅ Validate demand before investing in C++
- ✅ Phase 2 becomes premium feature (PRO upsell)

---

## Phase 1: Simple Template Wizard (PRIORITY!)

**Timeline:** 1-2 weeks
**Technology:** Pure Python (CustomTkinter) - NO C++
**Goal:** 80% of users can deploy with simple form

### **User Experience:**

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Select Target Platform                            │
│  ──────────────────────────────────                        │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │  ESP32   │  │  Jetson  │  │ Nano 33  │                 │
│  │  [✓]     │  │  [ ]     │  │  [ ]     │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
│                                                             │
│  [Next →]                                                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Step 2: Select Sensor                                      │
│  ─────────────────────────                                  │
│                                                             │
│  ○ MPU6050 (6-axis IMU)                                    │
│  ○ ADXL345 (3-axis Accelerometer)                         │
│  ○ Built-in Sensors (Nano 33 only)                        │
│                                                             │
│  [← Back]  [Next →]                                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Step 3: Pin Configuration                                  │
│  ──────────────────────────                                 │
│                                                             │
│  I2C Configuration:                                         │
│  SDA Pin:  [21  ▼]  (Default for ESP32)                   │
│  SCL Pin:  [22  ▼]                                         │
│  I2C Addr: [0x68  ]                                        │
│                                                             │
│  Sample Rate: [100 Hz ▼]                                   │
│                                                             │
│  [← Back]  [Next →]                                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Step 4: Output Actions                                     │
│  ──────────────────────                                     │
│                                                             │
│  When model detects Class 1 (Fall):                        │
│                                                             │
│  ☑ Turn on LED (Pin 2, 5 seconds)                         │
│  ☑ Send Serial message                                     │
│  ☐ Send WiFi alert                                         │
│                                                             │
│  [← Back]  [Next →]                                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Step 5: Generate Firmware                                  │
│  ─────────────────────────────                              │
│                                                             │
│  Review Configuration:                                      │
│  ✓ Platform:   ESP32                                       │
│  ✓ Sensor:     MPU6050                                     │
│  ✓ Model:      fall_detection_timesnet.onnx               │
│  ✓ Actions:    LED + Serial                               │
│                                                             │
│  Project Name: [fall_detection_esp32]                      │
│                                                             │
│  [🚀 Generate Firmware]                                     │
│                                                             │
│  [← Back]                                                   │
└─────────────────────────────────────────────────────────────┘
```

### **What Gets Generated:**

```
output/fall_detection_esp32/
├── src/
│   ├── main.cpp              ← GENERATED from template
│   ├── sensor_mpu6050.cpp    ← GENERATED
│   ├── model_runner.cpp      ← GENERATED
│   └── model_data.h          ← Your trained model
├── lib/
│   └── MPU6050/              ← Pre-bundled library
├── platformio.ini            ← GENERATED
└── README.md                 ← Flash instructions
```

### **Implementation:**

**File:** `ui/deployment_wizard.py` (ENHANCE EXISTING)

```python
class DeploymentWizard(ctk.CTkToplevel):
    """Simple 5-step deployment wizard."""

    def __init__(self, parent, model_info):
        super().__init__(parent)

        self.title("Deploy to Hardware")
        self.geometry("700x500")

        self.model_info = model_info  # {path, type, input_shape, classes}
        self.current_step = 1

        # User choices
        self.config = {
            'platform': '',
            'sensor': '',
            'pins': {},
            'actions': []
        }

        self.create_ui()

    def create_ui(self):
        """Create wizard UI."""
        # Header
        self.header = ctk.CTkLabel(
            self,
            text="Deploy to Hardware - Step 1 of 5",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.header.pack(pady=20)

        # Content frame (changes per step)
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Navigation buttons
        nav_frame = ctk.CTkFrame(self)
        nav_frame.pack(fill="x", padx=20, pady=10)

        self.back_btn = ctk.CTkButton(
            nav_frame,
            text="← Back",
            command=self.previous_step,
            width=100
        )
        self.back_btn.pack(side="left")

        self.next_btn = ctk.CTkButton(
            nav_frame,
            text="Next →",
            command=self.next_step,
            width=100
        )
        self.next_btn.pack(side="right")

        # Show first step
        self.show_step(1)

    def show_step(self, step):
        """Display content for current step."""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        self.current_step = step
        self.header.configure(text=f"Deploy to Hardware - Step {step} of 5")

        if step == 1:
            self._create_step1_platform()
        elif step == 2:
            self._create_step2_sensor()
        elif step == 3:
            self._create_step3_pins()
        elif step == 4:
            self._create_step4_actions()
        elif step == 5:
            self._create_step5_generate()

        # Update button states
        self.back_btn.configure(state="normal" if step > 1 else "disabled")
        self.next_btn.configure(
            text="Generate" if step == 5 else "Next →"
        )

    def _create_step1_platform(self):
        """Step 1: Platform selection."""
        ctk.CTkLabel(
            self.content_frame,
            text="Select Target Platform:",
            font=ctk.CTkFont(size=14)
        ).pack(pady=10)

        platforms = [
            ("ESP32 DevKit", "esp32", "⚡ 240MHz, WiFi/BT, $10"),
            ("Jetson Nano", "jetson", "🚀 GPU, 4GB RAM, $99"),
            ("Arduino Nano 33", "nano33", "🔋 Low Power, Built-in IMU, $33")
        ]

        for label, value, desc in platforms:
            frame = ctk.CTkFrame(self.content_frame)
            frame.pack(fill="x", padx=20, pady=5)

            radio = ctk.CTkRadioButton(
                frame,
                text=label,
                variable=self.platform_var,
                value=value,
                font=ctk.CTkFont(size=13, weight="bold")
            )
            radio.pack(anchor="w", padx=10, pady=5)

            ctk.CTkLabel(
                frame,
                text=desc,
                font=ctk.CTkFont(size=11),
                text_color="gray60"
            ).pack(anchor="w", padx=30)

    def _create_step2_sensor(self):
        """Step 2: Sensor selection."""
        # Similar implementation...
        pass

    def _create_step3_pins(self):
        """Step 3: Pin configuration."""
        # Similar implementation...
        pass

    def _create_step4_actions(self):
        """Step 4: Output actions."""
        # Similar implementation...
        pass

    def _create_step5_generate(self):
        """Step 5: Generate firmware."""
        # Review + generate button

        generate_btn = ctk.CTkButton(
            self.content_frame,
            text="🚀 Generate Firmware",
            command=self._generate_firmware,
            height=50,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        generate_btn.pack(pady=20)

    def _generate_firmware(self):
        """Generate firmware from template."""
        from core.deployment.template_generator import TemplateGenerator

        generator = TemplateGenerator(
            platform=self.config['platform'],
            sensor=self.config['sensor'],
            pins=self.config['pins'],
            actions=self.config['actions'],
            model_file=self.model_info['path']
        )

        output_dir = generator.generate()

        messagebox.showinfo(
            "Success",
            f"Firmware generated!\n\nOutput: {output_dir}\n\n"
            "See README.md for flashing instructions."
        )

        self.destroy()
```

**File:** `core/deployment/template_generator.py` (NEW)

```python
"""Simple template-based firmware generator."""

from jinja2 import Environment, FileSystemLoader
import os
import shutil

class TemplateGenerator:
    """Generate firmware from templates."""

    def __init__(self, platform, sensor, pins, actions, model_file):
        self.platform = platform
        self.sensor = sensor
        self.pins = pins
        self.actions = actions
        self.model_file = model_file

        self.env = Environment(
            loader=FileSystemLoader('templates')
        )

    def generate(self):
        """Generate complete firmware package."""
        # Create output directory
        output_dir = f"output/firmware_{self.platform}_{int(time.time())}"
        os.makedirs(f"{output_dir}/src", exist_ok=True)

        # Generate main.cpp
        self._generate_main_cpp(output_dir)

        # Generate sensor driver
        self._generate_sensor_driver(output_dir)

        # Generate model runner
        self._generate_model_runner(output_dir)

        # Copy model file
        shutil.copy(
            self.model_file,
            f"{output_dir}/src/model_data.h"
        )

        # Generate platformio.ini
        self._generate_platformio_ini(output_dir)

        # Copy sensor library
        self._copy_sensor_library(output_dir)

        # Generate README
        self._generate_readme(output_dir)

        return output_dir

    def _generate_main_cpp(self, output_dir):
        """Generate main.cpp from template."""
        template = self.env.get_template(
            f'{self.platform}/main.cpp.jinja2'
        )

        code = template.render(
            sensor=self.sensor,
            pins=self.pins,
            actions=self.actions
        )

        with open(f"{output_dir}/src/main.cpp", 'w') as f:
            f.write(code)

    # ... other generation methods
```

**Templates:** `templates/esp32/main.cpp.jinja2`

```cpp
// Auto-generated by CiRA FutureEdge Studio
// Platform: {{ platform }}
// Sensor: {{ sensor }}

#include <Arduino.h>
#include <Wire.h>

{% if sensor == "mpu6050" %}
#include <MPU6050.h>
MPU6050 sensor;
{% elif sensor == "adxl345" %}
#include <Adafruit_ADXL345_U.h>
Adafruit_ADXL345_Unified sensor = Adafruit_ADXL345_Unified(12345);
{% endif %}

#include "model_runner.h"

void setup() {
    Serial.begin(115200);

    // Initialize I2C
    Wire.begin({{ pins.sda }}, {{ pins.scl }});

    // Initialize sensor
    {% if sensor == "mpu6050" %}
    sensor.initialize();
    if (!sensor.testConnection()) {
        Serial.println("MPU6050 connection failed!");
        while(1);
    }
    {% elif sensor == "adxl345" %}
    if (!sensor.begin()) {
        Serial.println("ADXL345 not found!");
        while(1);
    }
    {% endif %}

    // Initialize actions
    {% for action in actions %}
    {% if action.type == "led" %}
    pinMode({{ action.pin }}, OUTPUT);
    {% endif %}
    {% endfor %}

    Serial.println("System ready");
}

void loop() {
    // Read sensor data
    {% if sensor == "mpu6050" %}
    int16_t ax, ay, az;
    sensor.getAcceleration(&ax, &ay, &az);
    {% elif sensor == "adxl345" %}
    sensors_event_t event;
    sensor.getEvent(&event);
    float ax = event.acceleration.x;
    float ay = event.acceleration.y;
    float az = event.acceleration.z;
    {% endif %}

    // Run model inference
    int prediction = run_model(ax, ay, az);

    // Execute actions
    {% for action in actions %}
    {% if action.type == "led" %}
    if (prediction == {{ action.trigger_class }}) {
        digitalWrite({{ action.pin }}, HIGH);
        delay({{ action.duration }});
        digitalWrite({{ action.pin }}, LOW);
    }
    {% elif action.type == "serial" %}
    Serial.print("Prediction: ");
    Serial.println(prediction);
    {% endif %}
    {% endfor %}

    delay(100);
}
```

### **Phase 1 Deliverables:**

- ✅ 5-step wizard (CustomTkinter)
- ✅ Template-based code generation (Jinja2)
- ✅ Support 3 platforms (ESP32, Jetson, Nano33)
- ✅ Support 2 sensors (MPU6050, ADXL345)
- ✅ Generated firmware compiles and works
- ✅ Complete in 1-2 weeks

---

## Phase 2: Visual Pipeline Builder (LATER!)

**Timeline:** 3-4 weeks AFTER Phase 1 ships
**Technology:** C++ with imgui-node-editor
**Goal:** 20% power users get advanced visual editor

### **When to Start Phase 2:**

**Wait for validation:**
1. ✅ Ship Phase 1
2. ✅ Get user feedback
3. ✅ See if users need complex pipelines

**Scenarios:**

**Scenario A:** Users love Phase 1, ask for more complexity
→ Build Phase 2 (justified investment)

**Scenario B:** Users satisfied with Phase 1
→ **Don't build Phase 2!** (saved 3-4 weeks)

**Scenario C:** Users need something in between
→ Add more templates to Phase 1 (1 week vs 4 weeks)

### **Phase 2 Implementation:**

*Use the C++ standalone plan from previous document*

Full imgui-node-editor with:
- Drag-drop nodes
- Complex pipelines
- Multiple sensors
- Conditional logic
- Advanced users only

---

## Comparison: Phase 1 vs Phase 2

| Feature | Phase 1 (Simple Wizard) | Phase 2 (Visual Editor) |
|---------|-------------------------|-------------------------|
| **Timeline** | 1-2 weeks | 3-4 weeks |
| **Technology** | Python (CustomTkinter) | C++ (imgui-node-editor) |
| **Complexity** | Low | High |
| **User Coverage** | 80% | 20% (advanced) |
| **Use Cases** | Single sensor → model → action | Multi-sensor, complex logic |
| **Risk** | Low | Medium |
| **Can Ship Product** | ✅ YES | Not alone |

---

## Rollout Timeline

```
Week 1-2:   Phase 1 implementation
Week 3:     Testing + polish
Week 4:     🚀 PRODUCT LAUNCH (with Phase 1)
            ↓
            Users deploy with simple wizard
            Gather feedback
            ↓
Week 5-8:   Phase 2 implementation (IF validated)
Week 9:     🎨 PHASE 2 RELEASE (advanced feature)
            ↓
            Power users get visual editor
```

---

## Revenue Strategy

**Phase 1:** FREE tier users
- 10 deployments with simple wizard
- Single sensor, basic actions

**Phase 2:** PRO tier only ($99/year)
- Unlimited deployments
- Visual pipeline builder
- Multi-sensor pipelines
- Custom logic

**This creates natural upgrade path!**

---

## Risk Mitigation

### **Phase 1 Risks:**
- ✅ **Low risk** (pure Python, no new tech)
- ✅ **Fast to fix** (just templates)
- ✅ **Can't block launch** (worst case: improve templates)

### **Phase 2 Risks:**
- ⚠️ C++ complexity
- ⚠️ imgui-node-editor learning curve
- ⚠️ Cross-platform builds

**Mitigation:** Only build if Phase 1 validates demand!

---

## Decision Framework

**Ship Phase 1 if:**
- ✅ Want to launch product soon
- ✅ 80% coverage is acceptable
- ✅ Want to validate deployment workflow first

**Add Phase 2 if:**
- ✅ Phase 1 shipped and working
- ✅ Users requesting complex pipelines
- ✅ Have 3-4 weeks for C++ development
- ✅ Can justify as premium feature

---

## My Strong Recommendation

### **START WITH PHASE 1 ONLY**

**Reasons:**
1. ✅ Ship in 1-2 weeks (vs 4-5 weeks)
2. ✅ 80% of users satisfied
3. ✅ Launch product sooner
4. ✅ Validate demand before C++ investment
5. ✅ Lower risk
6. ✅ Phase 2 becomes upsell opportunity

**Don't build Phase 2 until:**
- Users ask for it
- Revenue justifies investment
- Phase 1 is stable

---

**Implement Phase 1 now, decide on Phase 2 later based on real user data!**

**Ready to start Phase 1 implementation?** 🚀

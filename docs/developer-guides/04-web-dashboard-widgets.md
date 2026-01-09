# Web Dashboard Widget Development

This guide explains how to create custom widgets for the CiRA Runtime web dashboard.

## Overview

The web dashboard displays real-time data from the block runtime using widgets. Widgets subscribe to block outputs via WebSocket and display data in various formats (gauges, graphs, text, etc.).

**Architecture:**
```
Block Runtime (Jetson)
    ↓ WebSocket
Web Dashboard (Browser)
    ↓ JavaScript
Widgets (widgets.js)
```

---

## Widget System Architecture

### File Locations

```
cira-block-runtime/web/
├── index.html           # Main dashboard page
├── css/
│   └── dashboard.css    # Widget styling
└── js/
    ├── dashboard.js     # Dashboard initialization
    ├── widgets.js       # Widget base classes
    ├── recorder-widget.js  # Dataset recorder widget
    └── ws-manager.js    # WebSocket management
```

### Widget Base Class

All widgets extend the `Widget` base class:

```javascript
class Widget {
    constructor(id, type, config) {
        this.id = id;
        this.type = type;
        this.config = { ...this.getDefaultConfig(), ...(config || {}) };
        this.element = null;
    }

    getDefaultConfig() {
        return { title: 'Widget' };
    }

    render(container) { /* ... */ }
    renderBody() { /* Override this */ }
    afterRender() { /* Subscribe to data */ }
    update(data) { /* Handle data updates */ }
    destroy() { /* Cleanup */ }
    serialize() { /* Save state */ }
}
```

---

## Part 1: Creating a Simple Widget

### Example: Creating a Text Display Widget

**File:** `cira-block-runtime/web/js/widgets.js`

```javascript
// Text Display Widget - Shows a single value
class TextWidget extends Widget {
    getDefaultConfig() {
        return {
            title: 'Text Display',
            nodeId: 1,           // Which block to read from
            pin: 'value_out',    // Which pin to read
            fontSize: 48         // Display font size
        };
    }

    renderBody() {
        return `
            <div class="text-widget">
                <div class="text-widget-value"
                     id="text-value-${this.id}"
                     style="font-size:${this.config.fontSize}px;">
                    --
                </div>
                <div class="text-widget-label">${this.config.title}</div>
            </div>
        `;
    }

    afterRender() {
        // Subscribe to WebSocket for real-time updates
        const nodeId = this.config.nodeId;
        const pinName = this.config.pin;

        if (nodeId && pinName && typeof wsManager !== 'undefined') {
            wsManager.subscribe(this.id, nodeId, pinName, (value, timestamp) => {
                this.updateTextValue(value);
            });
        }
    }

    updateTextValue(value) {
        const valueElement = document.getElementById(`text-value-${this.id}`);
        if (!valueElement) return;

        // Format numbers to 2 decimal places
        let displayValue = value;
        if (typeof value === 'number') {
            displayValue = value.toFixed(2);
        }

        valueElement.textContent = displayValue;
    }

    destroy() {
        // Unsubscribe from WebSocket when widget is removed
        if (typeof wsManager !== 'undefined') {
            wsManager.unsubscribe(this.id);
        }
    }
}
```

### Register Widget Type

In `dashboard.js`, add to widget registry:

```javascript
function createWidget(type, id, config) {
    switch (type) {
        case 'status':
            return new StatusWidget(id, type, config);
        case 'gauge':
            return new GaugeWidget(id, type, config);
        case 'text':
            return new TextWidget(id, type, config);  // ← Add this
        // ... other widgets ...
        default:
            console.error('Unknown widget type:', type);
            return null;
    }
}
```

### Add to Widget Menu

In `index.html`, add button to widget menu:

```html
<div class="widget-menu">
    <button onclick="addWidget('status')">📊 Status</button>
    <button onclick="addWidget('gauge')">⏱️ Gauge</button>
    <button onclick="addWidget('text')">📝 Text Display</button>  <!-- Add this -->
    <!-- ... other widgets ... -->
</div>
```

---

## Part 2: Advanced Widget with Configuration

### Example: Gauge Widget with Multiple Data Sources

```javascript
class GaugeWidget extends Widget {
    getDefaultConfig() {
        return {
            title: 'Gauge',
            nodeId: null,
            pin: null,
            min: 0,
            max: 100,
            unit: '%',
            thresholds: {
                warning: 70,
                critical: 90
            }
        };
    }

    renderBody() {
        return `
            <div class="gauge-widget">
                <canvas id="gauge-canvas-${this.id}" width="200" height="200"></canvas>
                <div class="gauge-value" id="gauge-value-${this.id}">--</div>
            </div>
        `;
    }

    afterRender() {
        const canvas = document.getElementById(`gauge-canvas-${this.id}`);
        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        // Create Chart.js gauge
        this.chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [0, 100],
                    backgroundColor: ['#3498db', '#2c3e50'],
                    borderWidth: 0
                }]
            },
            options: {
                circumference: 180,
                rotation: -90,
                cutout: '75%',
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                }
            }
        });

        // Subscribe to data
        if (this.config.nodeId && this.config.pin && typeof wsManager !== 'undefined') {
            wsManager.subscribe(this.id, this.config.nodeId, this.config.pin, (value, timestamp) => {
                this.updateGauge(value);
            });
        }
    }

    updateGauge(value) {
        if (!this.chart) return;

        const { min, max, unit, thresholds } = this.config;

        // Clamp value to range
        value = Math.max(min, Math.min(max, value));
        const percentage = ((value - min) / (max - min)) * 100;

        // Update chart
        this.chart.data.datasets[0].data = [percentage, 100 - percentage];

        // Color based on thresholds
        if (value >= thresholds.critical) {
            this.chart.data.datasets[0].backgroundColor[0] = '#e74c3c'; // Red
        } else if (value >= thresholds.warning) {
            this.chart.data.datasets[0].backgroundColor[0] = '#f39c12'; // Orange
        } else {
            this.chart.data.datasets[0].backgroundColor[0] = '#3498db'; // Blue
        }

        this.chart.update('none'); // Update without animation

        // Update text value
        const valueElement = document.getElementById(`gauge-value-${this.id}`);
        if (valueElement) {
            valueElement.textContent = `${value.toFixed(1)}${unit}`;
        }
    }

    destroy() {
        if (this.chart) {
            this.chart.destroy();
        }
        if (typeof wsManager !== 'undefined') {
            wsManager.unsubscribe(this.id);
        }
    }
}
```

---

## Part 3: Interactive Widget with Commands

### Example: LED Control Widget

```javascript
class LEDWidget extends Widget {
    getDefaultConfig() {
        return {
            title: 'LED Control',
            nodeId: null,        // Node to control
            statePin: 'state',   // Pin to read state
            commandTopic: 'led_command'  // Command topic
        };
    }

    renderBody() {
        return `
            <div class="led-widget">
                <div class="led-indicator" id="led-indicator-${this.id}">
                    <div class="led-light" id="led-light-${this.id}"></div>
                </div>
                <div class="led-controls">
                    <button class="btn-on" onclick="ledWidget_${this.id}.turnOn()">ON</button>
                    <button class="btn-off" onclick="ledWidget_${this.id}.turnOff()">OFF</button>
                    <button class="btn-toggle" onclick="ledWidget_${this.id}.toggle()">Toggle</button>
                </div>
                <div class="led-status" id="led-status-${this.id}">Unknown</div>
            </div>
        `;
    }

    afterRender() {
        // Make widget accessible globally for button onclick
        window[`ledWidget_${this.id}`] = this;

        // Subscribe to state updates
        if (this.config.nodeId && this.config.statePin && typeof wsManager !== 'undefined') {
            wsManager.subscribe(this.id, this.config.nodeId, this.config.statePin, (value, timestamp) => {
                this.updateState(value);
            });
        }
    }

    updateState(state) {
        const light = document.getElementById(`led-light-${this.id}`);
        const status = document.getElementById(`led-status-${this.id}`);

        if (state) {
            light.classList.add('on');
            light.classList.remove('off');
            status.textContent = 'ON';
        } else {
            light.classList.add('off');
            light.classList.remove('on');
            status.textContent = 'OFF';
        }
    }

    turnOn() {
        this.sendCommand(true);
    }

    turnOff() {
        this.sendCommand(false);
    }

    toggle() {
        // Read current state and invert
        const light = document.getElementById(`led-light-${this.id}`);
        const isOn = light.classList.contains('on');
        this.sendCommand(!isOn);
    }

    sendCommand(state) {
        if (typeof wsManager !== 'undefined' && wsManager.isConnected()) {
            const command = {
                command: 'set_output',
                node_id: this.config.nodeId,
                pin_name: 'state',
                value: state
            };
            wsManager.ws.send(JSON.stringify(command));
            console.log('[LED Widget] Sent command:', command);
        }
    }

    destroy() {
        // Clean up global reference
        delete window[`ledWidget_${this.id}`];

        if (typeof wsManager !== 'undefined') {
            wsManager.unsubscribe(this.id);
        }
    }
}
```

**Add CSS for LED indicator:**

```css
/* In dashboard.css */
.led-widget {
    text-align: center;
    padding: 20px;
}

.led-indicator {
    margin: 20px auto;
}

.led-light {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    border: 3px solid #555;
    box-shadow: 0 0 10px rgba(0,0,0,0.3);
    transition: all 0.3s ease;
}

.led-light.on {
    background: radial-gradient(circle, #00ff00 0%, #00cc00 100%);
    box-shadow: 0 0 30px #00ff00;
}

.led-light.off {
    background: radial-gradient(circle, #333 0%, #111 100%);
    box-shadow: 0 0 10px rgba(0,0,0,0.5);
}

.led-controls {
    margin: 20px 0;
}

.led-controls button {
    margin: 5px;
    padding: 10px 20px;
    font-size: 14px;
    cursor: pointer;
    border: none;
    border-radius: 5px;
    transition: all 0.2s;
}

.btn-on {
    background: #27ae60;
    color: white;
}

.btn-on:hover {
    background: #229954;
}

.btn-off {
    background: #e74c3c;
    color: white;
}

.btn-off:hover {
    background: #c0392b;
}

.btn-toggle {
    background: #3498db;
    color: white;
}

.btn-toggle:hover {
    background: #2980b9;
}
```

---

## Part 4: Widget Configuration Dialog

### Adding Configuration Dialog

**In dashboard.js:**

```javascript
function configureWidget(widgetId) {
    const widget = widgets.get(widgetId);
    if (!widget) return;

    // Show modal with configuration form
    const modal = document.getElementById('config-modal');
    const form = document.getElementById('config-form');

    // Build form based on widget config
    let formHTML = `<h3>Configure ${widget.config.title}</h3>`;

    for (const [key, value] of Object.entries(widget.config)) {
        formHTML += `
            <div class="form-group">
                <label for="config-${key}">${key}:</label>
                <input type="text"
                       id="config-${key}"
                       value="${value}"
                       class="form-control">
            </div>
        `;
    }

    formHTML += `
        <div class="form-actions">
            <button onclick="applyWidgetConfig('${widgetId}')">Apply</button>
            <button onclick="closeConfigModal()">Cancel</button>
        </div>
    `;

    form.innerHTML = formHTML;
    modal.style.display = 'block';
}

function applyWidgetConfig(widgetId) {
    const widget = widgets.get(widgetId);
    if (!widget) return;

    // Read form values
    for (const key of Object.keys(widget.config)) {
        const input = document.getElementById(`config-${key}`);
        if (input) {
            widget.config[key] = input.value;
        }
    }

    // Re-render widget
    const container = widget.element;
    widget.destroy();
    widget.render(container);

    // Save dashboard state
    saveDashboard();

    closeConfigModal();
}
```

---

## Part 5: WebSocket Communication

### Subscribing to Block Outputs

```javascript
// Subscribe to a specific block output
wsManager.subscribe(widgetId, nodeId, pinName, (value, timestamp) => {
    console.log(`Received: ${value} at ${timestamp}`);
    updateWidget(value);
});

// Unsubscribe when done
wsManager.unsubscribe(widgetId);
```

### Sending Commands to Blocks

```javascript
// Send command to set block input
const command = {
    command: 'set_output',
    node_id: 12,
    pin_name: 'record_trigger',
    value: true
};
wsManager.ws.send(JSON.stringify(command));

// Start recording
const startRecording = {
    command: 'start_recording',
    node_id: 12
};
wsManager.ws.send(JSON.stringify(startRecording));

// Stop recording
const stopRecording = {
    command: 'stop_recording',
    node_id: 12
};
wsManager.ws.send(JSON.stringify(stopRecording));
```

### Handling Different Data Types

```javascript
updateValue(value) {
    // Handle different data types
    if (typeof value === 'number') {
        this.displayNumber(value);
    }
    else if (typeof value === 'string') {
        this.displayString(value);
    }
    else if (typeof value === 'boolean') {
        this.displayBoolean(value);
    }
    else if (Array.isArray(value)) {
        this.displayArray(value);
    }
    else if (typeof value === 'object') {
        this.displayObject(value);
    }
}
```

---

## Part 6: Dashboard Persistence

### Saving Dashboard Layout

```javascript
function saveDashboard() {
    const config = {
        widgets: []
    };

    for (const [id, widget] of widgets) {
        config.widgets.push(widget.serialize());
    }

    // Save to localStorage
    localStorage.setItem('dashboard_config', JSON.stringify(config));

    // Or save to server
    fetch('/api/dashboard/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
    });
}

function loadDashboard() {
    // Load from localStorage
    const config = localStorage.getItem('dashboard_config');
    if (config) {
        const data = JSON.parse(config);
        data.widgets.forEach(widgetConfig => {
            addWidget(widgetConfig.type, widgetConfig.id, widgetConfig.config);
        });
    }
}
```

---

## Testing Widgets

### 1. Local Testing (Without Jetson)

Create mock WebSocket manager:

```javascript
// In dashboard.js (for testing)
class MockWSManager {
    subscribe(id, nodeId, pin, callback) {
        // Generate fake data every second
        this.intervals = this.intervals || {};
        this.intervals[id] = setInterval(() => {
            const mockValue = Math.random() * 100;
            callback(mockValue, Date.now());
        }, 1000);
    }

    unsubscribe(id) {
        if (this.intervals && this.intervals[id]) {
            clearInterval(this.intervals[id]);
            delete this.intervals[id];
        }
    }

    isConnected() {
        return true;
    }
}

// Use mock in development
if (window.location.hostname === 'localhost') {
    window.wsManager = new MockWSManager();
}
```

### 2. Testing with Jetson

1. Deploy your pipeline to Jetson
2. Open dashboard: `http://192.168.1.200:8083`
3. Add your widget
4. Configure node ID and pin name
5. Verify data updates in real-time

---

## Common Widget Patterns

### Pattern 1: Time Series Graph

```javascript
class GraphWidget extends Widget {
    constructor(id, type, config) {
        super(id, type, config);
        this.dataPoints = [];
        this.maxPoints = 100;
    }

    afterRender() {
        const canvas = document.getElementById(`graph-canvas-${this.id}`);
        const ctx = canvas.getContext('2d');

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: this.config.title,
                    data: [],
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                animation: false,
                scales: {
                    x: { display: false },
                    y: { beginAtZero: true }
                }
            }
        });

        // Subscribe to data
        wsManager.subscribe(this.id, this.config.nodeId, this.config.pin, (value) => {
            this.addDataPoint(value);
        });
    }

    addDataPoint(value) {
        const timestamp = new Date().toLocaleTimeString();

        this.chart.data.labels.push(timestamp);
        this.chart.data.datasets[0].data.push(value);

        // Keep only last N points
        if (this.chart.data.labels.length > this.maxPoints) {
            this.chart.data.labels.shift();
            this.chart.data.datasets[0].data.shift();
        }

        this.chart.update('none');
    }
}
```

### Pattern 2: Status Indicator

```javascript
class StatusIndicatorWidget extends Widget {
    renderBody() {
        return `
            <div class="status-indicator">
                <div class="status-icon" id="status-icon-${this.id}">🔴</div>
                <div class="status-text" id="status-text-${this.id}">Offline</div>
            </div>
        `;
    }

    afterRender() {
        wsManager.subscribe(this.id, this.config.nodeId, 'ready', (isReady) => {
            this.updateStatus(isReady);
        });
    }

    updateStatus(isReady) {
        const icon = document.getElementById(`status-icon-${this.id}`);
        const text = document.getElementById(`status-text-${this.id}`);

        if (isReady) {
            icon.textContent = '🟢';
            text.textContent = 'Ready';
        } else {
            icon.textContent = '🔴';
            text.textContent = 'Not Ready';
        }
    }
}
```

---

## Checklist for Creating Widgets

- [ ] Create widget class extending `Widget`
- [ ] Implement `getDefaultConfig()` with configuration options
- [ ] Implement `renderBody()` with HTML structure
- [ ] Implement `afterRender()` to subscribe to WebSocket
- [ ] Implement `update()` or custom update methods
- [ ] Implement `destroy()` to clean up subscriptions
- [ ] Add widget to `createWidget()` factory function
- [ ] Add widget button to dashboard menu
- [ ] Add CSS styling in `dashboard.css`
- [ ] Test with mock data
- [ ] Test with real Jetson runtime
- [ ] Save dashboard layout persistence

---

## Troubleshooting

### Problem: Widget doesn't update

**Check:**
- WebSocket connection: Check browser console for connection errors
- Node ID and pin name are correct
- Block is running and outputting data
- Subscription is set up in `afterRender()`

### Problem: Widget disappears after refresh

**Solution:** Implement dashboard persistence (saveDashboard/loadDashboard)

### Problem: Multiple widgets interfere with each other

**Solution:** Use unique IDs for all DOM elements: `id="element-${this.id}"`

---

## Example: Complete Widget Implementation

See **recorder-widget.js** in the codebase for a complete example of a complex widget with:
- Configuration dialog
- WebSocket commands
- File listing and management
- Auto-refresh
- Error handling

This is a production-ready example you can use as a reference!

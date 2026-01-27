// Widget Base Class
class Widget {
    constructor(id, type, config) {
        this.id = id;
        this.type = type;
        this.config = { ...this.getDefaultConfig(), ...(config || {}) };
        this.element = null;
    }

    getDefaultConfig() {
        return {
            title: 'Widget'
        };
    }

    render(container) {
        const html = `
            <div class="widget-header">
                <span class="widget-title">${this.config.title}</span>
                <div class="widget-actions">
                    <button class="widget-action" onclick="configureWidget('${this.id}')">⚙️</button>
                    <button class="widget-action" onclick="removeWidget('${this.id}')">🗑️</button>
                </div>
            </div>
            <div class="widget-body" id="widget-body-${this.id}">
                ${this.renderBody()}
            </div>
        `;

        container.innerHTML = html;
        this.element = container;
        this.afterRender();
    }

    renderBody() {
        return '<p>Widget content</p>';
    }

    afterRender() {
        // Override in subclasses
    }

    update(data) {
        // Override in subclasses
    }

    serialize() {
        return {
            id: this.id,
            type: this.type,
            config: this.config
        };
    }
}

// Status Indicator Widget
class StatusWidget extends Widget {
    getDefaultConfig() {
        return {
            title: 'Runtime Status',
            showUptime: true
        };
    }

    renderBody() {
        return `
            <div class="status-widget">
                <div class="status-widget-icon" id="status-icon-${this.id}">🟢</div>
                <div class="status-widget-text" id="status-text-${this.id}">Running</div>
                <div class="status-widget-subtext" id="status-uptime-${this.id}">Uptime: --</div>
            </div>
        `;
    }

    update(data) {
        const icon = document.getElementById(`status-icon-${this.id}`);
        const text = document.getElementById(`status-text-${this.id}`);
        const uptime = document.getElementById(`status-uptime-${this.id}`);

        if (data.system) {
            const uptimeSeconds = data.system.uptime_seconds || 0;
            const hours = Math.floor(uptimeSeconds / 3600);
            const minutes = Math.floor((uptimeSeconds % 3600) / 60);

            if (uptime && this.config.showUptime) {
                uptime.textContent = `Uptime: ${hours}h ${minutes}m`;
            }
        }

        // Status always running for now
        if (icon) icon.textContent = '🟢';
        if (text) text.textContent = 'Running';
    }
}

// Gauge Widget
class GaugeWidget extends Widget {
    getDefaultConfig() {
        return {
            title: 'Gauge',
            dataSource: 'system.cpu_usage',
            min: 0,
            max: 100,
            unit: '%'
        };
    }

    renderBody() {
        return `<div class="gauge-widget">
            <canvas id="gauge-canvas-${this.id}" width="200" height="200"></canvas>
        </div>`;
    }

    afterRender() {
        const canvas = document.getElementById(`gauge-canvas-${this.id}`);
        if (!canvas) return;

        const ctx = canvas.getContext('2d');

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

        // Subscribe to WebSocket for real-time updates
        if (this.config.node_id && this.config.pin_name && typeof wsManager !== 'undefined') {
            wsManager.subscribe(this.id, this.config.node_id, this.config.pin_name, (value, timestamp) => {
                this.updateGauge(value);
            });
        }
    }

    updateGauge(value) {
        if (!this.chart) return;

        const percentage = ((value - this.config.min) / (this.config.max - this.config.min)) * 100;
        this.chart.data.datasets[0].data = [percentage, 100 - percentage];

        // Change color based on value
        if (percentage > 80) {
            this.chart.data.datasets[0].backgroundColor[0] = '#e74c3c';
        } else if (percentage > 50) {
            this.chart.data.datasets[0].backgroundColor[0] = '#f39c12';
        } else {
            this.chart.data.datasets[0].backgroundColor[0] = '#2ecc71';
        }

        this.chart.update('none');
    }

    destroy() {
        if (typeof wsManager !== 'undefined') {
            wsManager.unsubscribe(this.id);
        }
        if (this.chart) {
            this.chart.destroy();
        }
    }

    update(data) {
        if (!this.chart) return;

        let value = 0;

        // Get value from configured block/pin
        if (this.config.nodeId && this.config.pin && data.blockData) {
            const nodeData = data.blockData[this.config.nodeId];
            if (nodeData && nodeData[this.config.pin]) {
                value = nodeData[this.config.pin].value;
            }
        }
        // Fallback to system metrics for backward compatibility
        else if (this.config.dataSource && this.config.dataSource.startsWith('system.')) {
            const metric = this.config.dataSource.split('.')[1];
            if (data.system && data.system[metric] !== undefined) {
                value = data.system[metric];
            }
        }

        // Update chart
        const percentage = ((value - this.config.min) / (this.config.max - this.config.min)) * 100;
        this.chart.data.datasets[0].data = [percentage, 100 - percentage];

        // Change color based on value
        if (percentage > 80) {
            this.chart.data.datasets[0].backgroundColor[0] = '#e74c3c';
        } else if (percentage > 50) {
            this.chart.data.datasets[0].backgroundColor[0] = '#f39c12';
        } else {
            this.chart.data.datasets[0].backgroundColor[0] = '#2ecc71';
        }

        this.chart.update('none');
    }
}

// Line Chart Widget
class ChartWidget extends Widget {
    constructor(id, type, config) {
        super(id, type, config);
        this.dataHistory = [];
        this.maxDataPoints = 50;
    }

    getDefaultConfig() {
        return {
            title: 'Line Chart',
            dataSource: 'system.cpu_usage',
            maxPoints: 50
        };
    }

    renderBody() {
        return `<div style="height:100%;">
            <canvas id="chart-canvas-${this.id}"></canvas>
        </div>`;
    }

    afterRender() {
        const canvas = document.getElementById(`chart-canvas-${this.id}`);
        if (!canvas) return;

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
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#aaa' }
                    },
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#aaa', maxTicksLimit: 10 }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });

        // Subscribe to WebSocket for real-time updates
        if (this.config.node_id && this.config.pin_name && typeof wsManager !== 'undefined') {
            wsManager.subscribe(this.id, this.config.node_id, this.config.pin_name, (value, timestamp) => {
                this.addDataPoint(value);
            });
        }
    }

    addDataPoint(value) {
        if (!this.chart) return;

        const time = new Date().toLocaleTimeString();

        this.chart.data.labels.push(time);
        this.chart.data.datasets[0].data.push(value);

        // Limit data points
        if (this.chart.data.labels.length > (this.config.maxPoints || 50)) {
            this.chart.data.labels.shift();
            this.chart.data.datasets[0].data.shift();
        }

        this.chart.update('none');
    }

    destroy() {
        if (typeof wsManager !== 'undefined') {
            wsManager.unsubscribe(this.id);
        }
        if (this.chart) {
            this.chart.destroy();
        }
    }

    update(data) {
        if (!this.chart) return;

        let value = 0;

        // Get value from configured block/pin
        if (this.config.nodeId && this.config.pin && data.blockData) {
            const nodeData = data.blockData[this.config.nodeId];
            if (nodeData && nodeData[this.config.pin]) {
                value = nodeData[this.config.pin].value;
            }
        }
        // Fallback to system metrics for backward compatibility
        else if (this.config.dataSource && this.config.dataSource.startsWith('system.')) {
            const metric = this.config.dataSource.split('.')[1];
            if (data.system && data.system[metric] !== undefined) {
                value = data.system[metric];
            }
        }

        // Add to history
        const now = new Date();
        const timeLabel = now.toLocaleTimeString();

        this.dataHistory.push({ time: timeLabel, value: value });

        // Keep only last N points
        if (this.dataHistory.length > this.config.maxPoints) {
            this.dataHistory.shift();
        }

        // Update chart
        this.chart.data.labels = this.dataHistory.map(d => d.time);
        this.chart.data.datasets[0].data = this.dataHistory.map(d => d.value);
        this.chart.update('none');
    }
}

// Text Display Widget
class TextWidget extends Widget {
    getDefaultConfig() {
        return {
            title: 'Text Display',
            dataSource: 'custom.value',
            format: '{value}',
            fontSize: 48
        };
    }

    renderBody() {
        return `
            <div class="text-widget">
                <div class="text-widget-value" id="text-value-${this.id}" style="font-size:${this.config.fontSize}px;">
                    --
                </div>
                <div class="text-widget-label">${this.config.title}</div>
            </div>
        `;
    }

    afterRender() {
        // Subscribe to WebSocket for real-time updates
        // Support both property name formats: nodeId/pin (from config dialog) and node_id/pin_name (legacy)
        const nodeId = this.config.nodeId || this.config.node_id;
        const pinName = this.config.pin || this.config.pin_name;

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
        if (typeof wsManager !== 'undefined') {
            wsManager.unsubscribe(this.id);
        }
    }

    update(data) {
        const valueElement = document.getElementById(`text-value-${this.id}`);
        if (!valueElement) return;

        let value = '--';

        // Get value from configured block/pin
        if (this.config.nodeId && this.config.pin && data.blockData) {
            const nodeData = data.blockData[this.config.nodeId];
            if (nodeData && nodeData[this.config.pin]) {
                value = nodeData[this.config.pin].value;

                // Format numbers to 2 decimal places
                if (typeof value === 'number') {
                    value = value.toFixed(2);
                }
            }
        }
        // Fallback to system metrics for backward compatibility
        else if (this.config.dataSource && this.config.dataSource.startsWith('system.')) {
            const metric = this.config.dataSource.split('.')[1];
            if (data.system && data.system[metric] !== undefined) {
                value = data.system[metric];
            }
        }

        // Format value
        const formatted = this.config.format.replace('{value}', value);
        valueElement.textContent = formatted;
    }
}

// Log Viewer Widget
class LogsWidget extends Widget {
    constructor(id, type, config) {
        super(id, type, config);
        this.logs = [];
    }

    getDefaultConfig() {
        return {
            title: 'Log Viewer',
            filterLevel: 'ALL',
            maxLines: 100,
            autoScroll: true
        };
    }

    renderBody() {
        return `<div class="log-viewer" id="log-viewer-${this.id}"></div>`;
    }

    async afterRender() {
        // Fetch initial logs
        await this.fetchLogs();

        // Poll for new logs every 2 seconds
        this.pollInterval = setInterval(() => this.fetchLogs(), 2000);
    }

    async fetchLogs() {
        try {
            const limit = this.config.maxLines || 100;
            const response = await fetch('/api/logs?limit=' + limit, {
                headers: authManager.getHeaders()
            });

            if (response.ok) {
                const logs = await response.json();
                this.updateLogs(logs);
            }
        } catch (error) {
            console.error('Failed to fetch logs:', error);
        }
    }

    updateLogs(logs) {
        const viewer = document.getElementById(`log-viewer-${this.id}`);
        if (!viewer) return;

        // Filter logs
        const filtered = this.config.filterLevel === 'ALL'
            ? logs
            : logs.filter(log => log.level === this.config.filterLevel);

        // Render logs
        viewer.innerHTML = filtered.map(log => {
            const time = new Date(log.timestamp).toLocaleTimeString();
            return `
                <div class="log-entry">
                    <span class="log-timestamp">${time}</span>
                    <span class="log-level ${log.level}">${log.level}</span>
                    <span class="log-message">${log.message}</span>
                </div>
            `;
        }).join('');

        // Auto-scroll to bottom
        if (this.config.autoScroll) {
            viewer.scrollTop = viewer.scrollHeight;
        }
    }

    destroy() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
        }
    }
}

// Button Widget (Virtual GPIO Input)
class ButtonWidget extends Widget {
    constructor(id, type, config) {
        super(id, type, config);
        this.state = false;
        this.eventHandlers = [];
    }

    getDefaultConfig() {
        return {
            title: 'Button',
            buttonId: 'button_1',
            label: 'Press Me',
            momentary: true  // true = momentary, false = toggle
        };
    }

    renderBody() {
        return `
            <div class="button-widget">
                <button class="widget-button" id="widget-button-${this.id}">
                    ${this.config.label}
                </button>
                <div class="button-state" id="button-state-${this.id}">Released</div>
            </div>
        `;
    }

    afterRender() {
        // Clean up old event listeners first
        this.destroy();

        const button = document.getElementById(`widget-button-${this.id}`);
        if (!button) return;

        if (this.config.momentary) {
            // Momentary mode - press and release
            const handlers = {
                mousedown: () => this.setButtonState(true),
                mouseup: () => this.setButtonState(false),
                mouseleave: () => this.setButtonState(false),
                touchstart: (e) => { e.preventDefault(); this.setButtonState(true); },
                touchend: (e) => { e.preventDefault(); this.setButtonState(false); }
            };

            for (const [event, handler] of Object.entries(handlers)) {
                button.addEventListener(event, handler);
                this.eventHandlers.push({ element: button, event, handler });
            }
        } else {
            // Toggle mode - click to toggle
            const handler = () => this.setButtonState(!this.state);
            button.addEventListener('click', handler);
            this.eventHandlers.push({ element: button, event: 'click', handler });
        }
    }

    destroy() {
        // Remove all event listeners
        for (const { element, event, handler } of this.eventHandlers) {
            element.removeEventListener(event, handler);
        }
        this.eventHandlers = [];
    }

    setButtonState(pressed) {
        this.state = pressed;

        // Update UI immediately for fast response
        const button = document.getElementById(`widget-button-${this.id}`);
        const stateText = document.getElementById(`button-state-${this.id}`);

        if (button) {
            if (pressed) {
                button.classList.add('pressed');
            } else {
                button.classList.remove('pressed');
            }
        }

        if (stateText) {
            if (this.config.momentary) {
                stateText.textContent = pressed ? 'Pressed' : 'Released';
            } else {
                stateText.textContent = pressed ? 'ON' : 'OFF';
            }
        }

        // Send to backend via WebSocket (fast!)
        if (this.config.buttonId && typeof wsManager !== 'undefined') {
            // Send command via WebSocket using button_id
            const command = {
                command: 'button_press',
                button_id: this.config.buttonId,
                state: pressed ? 1 : 0
            };

            if (wsManager.ws && wsManager.ws.readyState === WebSocket.OPEN) {
                wsManager.ws.send(JSON.stringify(command));
                console.log(`[ButtonWidget] Sent via WebSocket: button_id=${this.config.buttonId}, state=${pressed}`);
            } else {
                console.warn('[ButtonWidget] WebSocket not connected');
            }
        } else {
            console.warn('[ButtonWidget] Button not configured with button_id');
        }
    }

    update(data) {
        // Button state is controlled by user, not by data updates
    }
}

// LED Widget (Virtual GPIO Output)
class LEDWidget extends Widget {
    constructor(id, type, config) {
        super(id, type, config);
        this.state = false;
    }

    getDefaultConfig() {
        return {
            title: 'LED',
            ledId: 'led_1',
            label: 'Status',
            color: 'green'  // red, green, blue, yellow, white
        };
    }

    renderBody() {
        return `
            <div class="led-widget">
                <div class="led-indicator ${this.config.color}" id="led-indicator-${this.id}">
                </div>
                <div class="led-label">${this.config.label}</div>
                <div class="led-state" id="led-state-${this.id}">OFF</div>
            </div>
        `;
    }

    afterRender() {
        // Use WebSocket for real-time LED state updates (Node-RED architecture)
        if (this.config.node_id && this.config.pin_name) {
            this.connectWebSocket();
        } else {
            console.warn('[LEDWidget] LED widget not configured - please configure block and pin');
        }
    }

    connectWebSocket() {
        const nodeId = this.config.node_id;
        const pinName = this.config.pin_name;

        if (!nodeId || !pinName) return;

        console.log(`[LEDWidget] Subscribing to WebSocket: ${nodeId}:${pinName}`);

        // Subscribe via global WebSocket manager (replaces SSE entirely)
        wsManager.subscribe(this.id, nodeId, pinName, (value, timestamp) => {
            // LED state is a boolean value
            const state = value === true || value === 1 || value === "true" || value === "1";
            this.updateLEDState(state);
        });
    }

    destroy() {
        // Unsubscribe from WebSocket when widget is removed
        if (typeof wsManager !== 'undefined') {
            wsManager.unsubscribe(this.id);
        }
    }

    async fetchLEDState() {
        try {
            const response = await fetch('/api/widget/led', {
                headers: authManager.getHeaders()
            });

            if (response.ok) {
                const data = await response.json();

                // Find our LED in the response
                const ledData = data.leds.find(led => led.led_id === this.config.ledId);
                if (ledData) {
                    this.updateLEDState(ledData.state);
                }
            }
        } catch (error) {
            console.error('Error fetching LED state:', error);
        }
    }

    updateLEDState(state) {
        if (this.state === state) return;  // No change

        this.state = state;

        const indicator = document.getElementById(`led-indicator-${this.id}`);
        const stateText = document.getElementById(`led-state-${this.id}`);

        if (indicator) {
            if (state) {
                indicator.classList.add('on');
            } else {
                indicator.classList.remove('on');
            }
        }

        if (stateText) {
            stateText.textContent = state ? 'ON' : 'OFF';
        }
    }

    update(data) {
        // LED state is fetched separately via polling or SSE
    }

    destroy() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
        }
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }
}

// Widget Factory
class WidgetFactory {
    static create(type, id, config) {
        switch (type) {
            case 'status':
                return new StatusWidget(id, type, config);
            case 'gauge':
                return new GaugeWidget(id, type, config);
            case 'chart':
                return new ChartWidget(id, type, config);
            case 'text':
                return new TextWidget(id, type, config);
            case 'logs':
                return new LogsWidget(id, type, config);
            case 'button':
                return new ButtonWidget(id, type, config);
            case 'led':
                return new LEDWidget(id, type, config);
            case 'signalplot':
                return new SignalPlotWidget(id, type, config);
            case 'oscilloscope':
                return new OscilloscopeWidget(id, type, config);
            case 'recorder':
                return new DataRecorderWidget(id, type, config);
            default:
                return new Widget(id, type, config);
        }
    }
}

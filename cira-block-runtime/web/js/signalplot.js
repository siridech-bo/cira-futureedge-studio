/**
 * SignalPlotWidget - Real-time signal visualization widget
 * Uses Server-Sent Events (SSE) for streaming data from backend
 * Uses uPlot for high-performance real-time plotting
 */

class SignalPlotWidget extends Widget {
    constructor(id, type, config) {
        super(id, type, config);
        this.eventSource = null;
        this.plot = null;
        this.dataX = [];
        this.dataY = [];
        this.maxPoints = (config && config.maxPoints) || 100;
        this.updateInterval = null;
        this.startTimestamp = null;
    }

    render(container) {
        const label = this.config.label || 'Signal Plot';
        const nodeId = this.config.node_id || 'N/A';
        const pinName = this.config.pin_name || 'N/A';

        const html = `
            <div class="widget-header">
                <span class="widget-title">${label}</span>
                <span class="widget-subtitle">${nodeId}:${pinName}</span>
                <button class="widget-config-btn" onclick="configureWidget('${this.id}')">⚙</button>
            </div>
            <div class="widget-body signal-plot-body">
                <div id="plot-${this.id}" class="signal-plot-container"></div>
                <div class="signal-plot-status" id="status-${this.id}">
                    <span class="status-indicator" id="indicator-${this.id}">⚫</span>
                    <span id="rate-${this.id}">0 Hz</span>
                </div>
            </div>
        `;

        container.innerHTML = html;
        this.element = container;
        this.afterRender();
    }

    afterRender() {
        // Clean up existing resources before re-initializing
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }

        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }

        if (this.plot) {
            this.plot.destroy();
            this.plot = null;
        }

        // Reset data buffers
        this.dataX = [];
        this.dataY = [];
        this.startTimestamp = null;

        // Initialize uPlot
        const plotContainer = document.getElementById(`plot-${this.id}`);
        if (!plotContainer) {
            console.error('[SignalPlot] Plot container not found:', `plot-${this.id}`);
            return;
        }

        console.log('[SignalPlot] Initializing uPlot for widget', this.id);

        // Determine Y-axis range (default to -1.5 to 1.5 for sine wave)
        let yMin = this.config.y_min !== undefined ? this.config.y_min : -1.5;
        let yMax = this.config.y_max !== undefined ? this.config.y_max : 1.5;

        // Calculate proper dimensions - get parent widget body height
        const widgetBody = plotContainer.parentElement;
        console.log('[SignalPlot] Widget body offsetWidth:', widgetBody.offsetWidth, 'offsetHeight:', widgetBody.offsetHeight);

        const plotWidth = widgetBody.offsetWidth - 20; // Account for padding
        let plotHeight = widgetBody.offsetHeight - 60; // Account for padding + status bar

        // Fallback: if height is too small, use a minimum height
        if (plotHeight < 100) {
            console.warn('[SignalPlot] Calculated height too small:', plotHeight, '- using fallback 300px');
            plotHeight = 300;
        }

        console.log('[SignalPlot] Final plot dimensions:', plotWidth, 'x', plotHeight);

        const opts = {
            width: plotWidth,
            height: plotHeight,
            legend: {
                show: false,  // Disable legend overlay
            },
            cursor: {
                show: true,
                drag: {
                    x: false,
                    y: false,
                }
            },
            scales: {
                x: {
                    time: false,
                },
                y: {
                    range: [yMin, yMax],
                }
            },
            axes: [
                {
                    label: 'Time (s)',
                    labelSize: 20,
                    labelFont: '12px Arial',
                    stroke: '#aaa',
                    grid: {
                        stroke: 'rgba(255, 255, 255, 0.1)',
                        width: 1,
                    },
                    ticks: {
                        stroke: 'rgba(255, 255, 255, 0.1)',
                    },
                    size: 50,
                },
                {
                    label: 'Value',
                    labelSize: 30,
                    labelFont: '12px Arial',
                    stroke: '#aaa',
                    grid: {
                        stroke: 'rgba(255, 255, 255, 0.1)',
                        width: 1,
                    },
                    ticks: {
                        stroke: 'rgba(255, 255, 255, 0.1)',
                    },
                    size: 60,
                }
            ],
            series: [
                {
                    label: 'Time'
                },
                {
                    label: this.config.pin_name || 'Signal',
                    stroke: this.config.color || '#3498db',
                    width: 2,
                }
            ],
        };

        // Initialize with empty data
        const data = [
            [], // x values (time)
            []  // y values (signal)
        ];

        this.plot = new uPlot(opts, data, plotContainer);

        // Connect to SSE stream
        this.connectStream();

        // Update plot periodically for smooth rendering
        this.updateInterval = setInterval(() => {
            if (this.dataX.length > 0) {
                this.updatePlot();
            }
        }, 100);  // Update every 100ms
    }

    connectStream() {
        const token = sessionStorage.getItem('auth_token') || '';
        const nodeId = this.config.node_id;
        const pinName = this.config.pin_name;
        const sampleRate = this.config.sample_rate || 0;

        if (!nodeId || !pinName) {
            console.error('[SignalPlot] Missing node_id or pin_name configuration');
            this.updateStatus('error', 'Config Error');
            return;
        }

        // Close existing connection
        if (this.eventSource) {
            this.eventSource.close();
        }

        // Build URL with query parameters
        const url = `/api/signals/stream?token=${token}&node_id=${encodeURIComponent(nodeId)}&pin_name=${encodeURIComponent(pinName)}&sample_rate=${sampleRate}`;

        console.log(`[SignalPlot] Connecting to ${url}`);
        this.eventSource = new EventSource(url);

        this.eventSource.onopen = () => {
            console.log('[SignalPlot] Stream connected');
            this.updateStatus('connected', 'Connected');
            this.lastDataTime = Date.now();
            this.sampleCount = 0;
        };

        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('[SignalPlot] Received data:', data);

                // Calculate relative time in seconds from first sample
                if (!this.startTimestamp) {
                    this.startTimestamp = data.timestamp;
                    console.log('[SignalPlot] First data point received, timestamp:', data.timestamp);
                }
                const timeInSeconds = (data.timestamp - this.startTimestamp) / 1000.0;

                // Handle both scalar and array values
                let value;
                if (Array.isArray(data.value)) {
                    // For vector outputs (like Channel Merge), use first element by default
                    // TODO: Add configuration to select which array element to plot
                    value = data.value[0];
                    console.log('[SignalPlot] Array value received, using first element:', value, 'full array:', data.value);
                } else {
                    value = data.value;
                }

                // Add to buffers
                this.dataX.push(timeInSeconds);
                this.dataY.push(value);

                // Limit buffer size
                if (this.dataX.length > this.maxPoints) {
                    this.dataX.shift();
                    this.dataY.shift();
                }

                // Update data rate
                this.sampleCount++;
                const now = Date.now();
                if (now - this.lastDataTime >= 1000) {
                    const rate = this.sampleCount / ((now - this.lastDataTime) / 1000);
                    this.updateStatus('connected', `${rate.toFixed(1)} Hz`);
                    console.log('[SignalPlot] Data rate:', rate.toFixed(1), 'Hz, buffer size:', this.dataX.length);
                    this.lastDataTime = now;
                    this.sampleCount = 0;
                }

            } catch (error) {
                console.error('[SignalPlot] Failed to parse data:', error);
            }
        };

        this.eventSource.onerror = (error) => {
            console.error('[SignalPlot] Stream error:', error);
            this.updateStatus('error', 'Disconnected');

            // Attempt to reconnect after 2 seconds
            setTimeout(() => this.connectStream(), 2000);
        };
    }

    updatePlot() {
        if (!this.plot) {
            console.warn('[SignalPlot] updatePlot called but plot is null');
            return;
        }

        // Update plot with current data
        this.plot.setData([
            this.dataX,
            this.dataY
        ]);

        // Debug: Log update every 2 seconds
        const now = Date.now();
        if (!this.lastUpdateLog || now - this.lastUpdateLog > 2000) {
            console.log('[SignalPlot] Updating plot with', this.dataX.length, 'points');
            this.lastUpdateLog = now;
        }
    }

    updateStatus(status, text) {
        const indicator = document.getElementById(`indicator-${this.id}`);
        const rateText = document.getElementById(`rate-${this.id}`);

        if (indicator) {
            if (status === 'connected') {
                indicator.textContent = '🟢';
            } else if (status === 'error') {
                indicator.textContent = '🔴';
            } else {
                indicator.textContent = '⚫';
            }
        }

        if (rateText) {
            rateText.textContent = text;
        }
    }

    destroy() {
        console.log(`[SignalPlot] Destroying widget ${this.id}`);

        // Stop update interval
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }

        // Close SSE connection
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }

        // Destroy plot
        if (this.plot) {
            this.plot.destroy();
            this.plot = null;
        }

        console.log(`[SignalPlot] Widget ${this.id} destroyed`);
    }
}

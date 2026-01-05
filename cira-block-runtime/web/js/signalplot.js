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
                <span class="widget-config-badge" id="config-badge-${this.id}" style="font-size: 10px; padding: 2px 6px; background: #555; border-radius: 3px; margin-left: 8px; display: none;">Checking...</span>
                <div class="widget-actions">
                    <button class="widget-action" onclick="configureWidget('${this.id}')">⚙️</button>
                    <button class="widget-action" onclick="removeWidget('${this.id}')">🗑️</button>
                </div>
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

        // Check if source block is Signal Generator and fetch its config
        this.checkSignalGeneratorConfig();

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
        // Use WebSocket instead of SSE
        console.log(`[SignalPlot] Subscribing to WebSocket: ${nodeId}:${pinName}`);

        wsManager.subscribe(this.id, nodeId, pinName, (value, timestamp) => {
            try {
                console.log('[SignalPlot] Received WebSocket data:', value, timestamp);

                // Calculate relative time in seconds from first sample
                if (!this.startTimestamp) {
                    this.startTimestamp = timestamp;
                    console.log('[SignalPlot] First data point received, timestamp:', timestamp);
                    this.updateStatus('connected', 'Connected');
                    this.lastDataTime = Date.now();
                    this.sampleCount = 0;
                }
                const timeInSeconds = (timestamp - this.startTimestamp) / 1000.0;

                // Handle both scalar and array values
                let plotValue;
                if (Array.isArray(value)) {
                    // For vector outputs (like Channel Merge), use first element by default
                    plotValue = value[0];
                    console.log('[SignalPlot] Array value received, using first element:', plotValue, 'full array:', value);
                } else {
                    plotValue = value;
                }

                // Add to buffers
                this.dataX.push(timeInSeconds);
                this.dataY.push(plotValue);

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
                console.error('[SignalPlot] Failed to parse WebSocket data:', error);
            }
        });
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

    checkSignalGeneratorConfig() {
        // Fetch block config to check if it's a Signal Generator
        const nodeId = this.config.node_id;
        if (!nodeId) return;

        fetch(`/api/blocks`)
            .then(response => response.json())
            .then(data => {
                const block = data.blocks.find(b => b.node_id == nodeId);
                if (block && block.type.includes('signal_generator')) {
                    // Check signal_type configuration
                    const signalType = block.config?.signal_type || 'dataset';
                    const datasetInline = block.config?.dataset_inline || '';
                    const datasetPath = block.config?.dataset_path || '';

                    // Show warning if using dataset mode with no dataset
                    if (signalType === 'dataset' && !datasetInline && !datasetPath) {
                        this.showConfigWarning('⚠️ Signal Generator: No Dataset Loaded!');
                    } else if (signalType === 'dataset') {
                        this.showConfigWarning(`📊 Mode: Dataset`);
                    } else {
                        this.showConfigWarning(`📈 Mode: ${signalType}`);
                    }
                }
            })
            .catch(err => console.error('[SignalPlot] Failed to fetch block config:', err));
    }

    showConfigWarning(message) {
        const badge = document.getElementById(`config-badge-${this.id}`);
        if (badge) {
            badge.style.display = 'inline-block';
            badge.textContent = message;
            if (message.includes('⚠️')) {
                badge.style.background = '#e74c3c';
                badge.style.fontWeight = 'bold';
            } else if (message.includes('📊')) {
                badge.style.background = '#3498db';
            } else {
                badge.style.background = '#2ecc71';
            }
        }
    }

    destroy() {
        console.log(`[SignalPlot] Destroying widget ${this.id}`);

        // Stop update interval
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }

        // Unsubscribe from WebSocket
        if (typeof wsManager !== 'undefined') {
            wsManager.unsubscribe(this.id);
        }

        // Destroy plot
        if (this.plot) {
            this.plot.destroy();
            this.plot = null;
        }

        console.log(`[SignalPlot] Widget ${this.id} destroyed`);
    }
}

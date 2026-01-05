/**
 * Industrial-Grade Oscilloscope Widget
 * High-speed signal visualization for vibration/impact detection
 * Supports compact (dashboard) and fullscreen (dedicated tab) modes
 */

class OscilloscopeWidget extends Widget {
    constructor(id, type, config) {
        super(id, type, config);

        // Operating mode
        this.mode = (config && config.mode) || 'compact';  // 'compact' or 'fullscreen'

        // Canvas and rendering
        this.canvas = null;
        this.ctx = null;
        this.animationFrameId = null;
        this.eventSources = [];  // Store all SSE connections for proper cleanup
        this.websocket = null;  // WebSocket connection for binary streaming

        // Data buffers (ring buffers for each channel)
        this.bufferSize = 2048;  // Maximum buffer size
        this.buffers = {
            ch1: { data: [], enabled: true, color: '#ff3b3b', label: 'CH1' },
            ch2: { data: [], enabled: true, color: '#00ff88', label: 'CH2' },
            ch3: { data: [], enabled: true, color: '#ffaa00', label: 'CH3' }
        };

        // Timebase settings
        this.timebase = {
            timePerDiv: 0.05,  // 50ms per division (default)
            divisions: 10,     // Horizontal divisions
            position: 0,       // Horizontal position offset
            options: [0.001, 0.002, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]  // seconds
        };

        // Vertical settings (per channel)
        this.vertical = {
            ch1: { voltsPerDiv: 1.0, position: 0, enabled: true },  // g per division
            ch2: { voltsPerDiv: 1.0, position: 0, enabled: true },
            ch3: { voltsPerDiv: 1.0, position: 0, enabled: true },
            divisions: 8,  // Vertical divisions
            options: [0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0]  // g
        };

        // Trigger settings
        this.trigger = {
            source: 'ch1',
            level: 1.5,
            slope: 'rising',  // 'rising' or 'falling'
            mode: 'auto',     // 'auto', 'normal', 'single'
            holdoff: 0,       // ms
            armed: false,
            triggered: false,
            position: 0.25    // Trigger position in buffer (25% = pre-trigger)
        };

        // Acquisition settings
        this.acquisition = {
            running: true,
            sampleRate: 800,  // Hz (configurable for different sensors)
            mode: 'normal',   // 'normal' or 'peak-detect'
        };

        // Measurements
        this.measurements = {
            ch1: { vpp: 0, rms: 0, freq: 0, max: 0, min: 0 },
            ch2: { vpp: 0, rms: 0, freq: 0, max: 0, min: 0 },
            ch3: { vpp: 0, rms: 0, freq: 0, max: 0, min: 0 }
        };

        // SSE connection
        this.eventSource = null;

        // Grid style
        this.grid = {
            majorColor: '#2a5a7a',
            minorColor: '#1a3a52',
            subdivisions: 5
        };

        console.log('[Oscilloscope] Created:', this.mode, 'mode');
    }

    getDefaultConfig() {
        return {
            title: 'Oscilloscope',
            node_id: '',
            mode: 'compact'
        };
    }

    render(container) {
        const html = this.mode === 'compact' ?
            this.renderCompact() : this.renderFullscreen();

        container.innerHTML = html;
        this.element = container;
        this.afterRender();
    }

    renderCompact() {
        const nodeId = this.config.node_id || 'N/A';

        return `
            <div class="oscilloscope-widget compact">
                <div class="oscilloscope-header">
                    <span class="oscilloscope-title">OSCILLOSCOPE</span>
                    <span class="oscilloscope-node">[${nodeId}]</span>
                    <div class="oscilloscope-channel-indicators">
                        <span class="channel-indicator ch1">●</span>
                        <span class="channel-indicator ch2">●</span>
                        <span class="channel-indicator ch3">●</span>
                    </div>
                    <div class="widget-actions">
                        <button class="btn-expand" onclick="expandOscilloscope('${this.id}')">⤢</button>
                        <button class="widget-action" onclick="configureWidget('${this.id}')">⚙️</button>
                        <button class="widget-action" onclick="removeWidget('${this.id}')">🗑️</button>
                    </div>
                </div>

                <div class="oscilloscope-display">
                    <canvas id="oscilloscope-canvas-${this.id}"></canvas>
                </div>

                <div class="oscilloscope-controls-compact">
                    <div class="control-group">
                        <label>Time/Div</label>
                        <select id="timebase-${this.id}" onchange="updateTimebase('${this.id}', this.value)">
                            ${this.timebase.options.map(t =>
                                `<option value="${t}" ${t === this.timebase.timePerDiv ? 'selected' : ''}>${this.formatTime(t)}</option>`
                            ).join('')}
                        </select>
                    </div>

                    <div class="control-group">
                        <label>Trigger</label>
                        <select id="trigger-mode-${this.id}" onchange="updateTriggerMode('${this.id}', this.value)">
                            <option value="auto" selected>Auto</option>
                            <option value="normal">Normal</option>
                            <option value="single">Single</option>
                        </select>
                    </div>

                    <div class="control-group">
                        <button class="btn-control ${this.acquisition.running ? 'active' : ''}"
                                id="btn-run-${this.id}"
                                onclick="toggleRun('${this.id}')">
                            ${this.acquisition.running ? '⏸ STOP' : '▶ RUN'}
                        </button>
                    </div>
                </div>

                <div class="oscilloscope-measurements-compact">
                    <span id="measure-ch1-${this.id}">CH1: --</span>
                    <span id="measure-ch2-${this.id}">CH2: --</span>
                    <span id="measure-ch3-${this.id}">CH3: --</span>
                </div>
            </div>
        `;
    }

    renderFullscreen() {
        const nodeId = this.config.node_id || 'N/A';

        return `
            <div class="oscilloscope-widget fullscreen">
                <div class="oscilloscope-header">
                    <span class="oscilloscope-title">OSCILLOSCOPE</span>
                    <span class="oscilloscope-node">[${nodeId}]</span>
                    <div class="oscilloscope-channel-indicators">
                        <span class="channel-indicator ch1">●</span>
                        <span class="channel-indicator ch2">●</span>
                        <span class="channel-indicator ch3">●</span>
                    </div>
                    <button class="widget-config-btn" onclick="configureWidget('${this.id}')">⚙</button>
                </div>

                <div class="oscilloscope-main">
                    <div class="oscilloscope-display-full">
                        <div class="voltage-scale" id="voltage-scale-${this.id}">
                            <div>5g</div><div>2.5g</div><div>0g</div><div>-2.5g</div><div>-5g</div>
                        </div>
                        <canvas id="oscilloscope-canvas-${this.id}"></canvas>
                        <div class="time-scale" id="time-scale-${this.id}">
                            <div>0ms</div><div>100ms</div><div>200ms</div><div>300ms</div><div>400ms</div><div>500ms</div>
                        </div>
                    </div>

                    <div class="oscilloscope-controls-full">
                        <div class="control-panel">
                            <div class="panel-header">HORIZONTAL</div>
                            <div class="control-row">
                                <label>Time/Div</label>
                                <select id="timebase-${this.id}" onchange="updateTimebase('${this.id}', this.value)">
                                    ${this.timebase.options.map(t =>
                                        `<option value="${t}" ${t === this.timebase.timePerDiv ? 'selected' : ''}>${this.formatTime(t)}</option>`
                                    ).join('')}
                                </select>
                            </div>
                            <div class="control-row">
                                <label>Position</label>
                                <input type="range" min="-50" max="50" value="0"
                                       id="time-pos-${this.id}"
                                       onchange="updateTimePosition('${this.id}', this.value)">
                            </div>
                        </div>

                        <div class="control-panel">
                            <div class="panel-header">VERTICAL</div>
                            ${['ch1', 'ch2', 'ch3'].map((ch, idx) => `
                                <div class="channel-control">
                                    <label>
                                        <input type="checkbox" checked
                                               onchange="toggleChannel('${this.id}', '${ch}', this.checked)">
                                        <span class="channel-label ${ch}">${ch.toUpperCase()}</span>
                                    </label>
                                    <select onchange="updateVoltsPerDiv('${this.id}', '${ch}', this.value)">
                                        ${this.vertical.options.map(v =>
                                            `<option value="${v}" ${v === 1.0 ? 'selected' : ''}>${v}g</option>`
                                        ).join('')}
                                    </select>
                                </div>
                            `).join('')}
                        </div>

                        <div class="control-panel">
                            <div class="panel-header">TRIGGER</div>
                            <div class="control-row">
                                <label>Source</label>
                                <select id="trigger-source-${this.id}" onchange="updateTriggerSource('${this.id}', this.value)">
                                    <option value="ch1" selected>CH1</option>
                                    <option value="ch2">CH2</option>
                                    <option value="ch3">CH3</option>
                                </select>
                            </div>
                            <div class="control-row">
                                <label>Level</label>
                                <input type="number" step="0.1" value="1.5"
                                       id="trigger-level-${this.id}"
                                       onchange="updateTriggerLevel('${this.id}', this.value)">
                                <span>g</span>
                            </div>
                            <div class="control-row">
                                <label>Slope</label>
                                <select id="trigger-slope-${this.id}" onchange="updateTriggerSlope('${this.id}', this.value)">
                                    <option value="rising" selected>↑ Rising</option>
                                    <option value="falling">↓ Falling</option>
                                </select>
                            </div>
                            <div class="control-row">
                                <label>Mode</label>
                                <select id="trigger-mode-${this.id}" onchange="updateTriggerMode('${this.id}', this.value)">
                                    <option value="auto" selected>Auto</option>
                                    <option value="normal">Normal</option>
                                    <option value="single">Single</option>
                                </select>
                            </div>
                        </div>

                        <div class="control-panel">
                            <div class="panel-header">ACQUIRE</div>
                            <div class="control-row">
                                <button class="btn-control ${this.acquisition.running ? 'active' : ''}"
                                        id="btn-run-${this.id}"
                                        onclick="toggleRun('${this.id}')">
                                    ${this.acquisition.running ? '⏸ STOP' : '▶ RUN'}
                                </button>
                                <button class="btn-control" onclick="singleCapture('${this.id}')">
                                    ⏺ SINGLE
                                </button>
                            </div>
                            <div class="control-row status-row">
                                <span>Status:</span>
                                <span class="status-indicator ${this.acquisition.running ? 'running' : 'stopped'}"
                                      id="status-${this.id}">●</span>
                            </div>
                            <div class="control-row">
                                <span>Rate: ${this.acquisition.sampleRate} Hz</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="oscilloscope-measurements-full">
                    <div class="measurement-row" id="measure-ch1-${this.id}">
                        <span class="ch-label ch1">CH1:</span>
                        <span>Vpp=--</span>
                        <span>RMS=--</span>
                        <span>Freq=--</span>
                        <span>Max=--</span>
                    </div>
                    <div class="measurement-row" id="measure-ch2-${this.id}">
                        <span class="ch-label ch2">CH2:</span>
                        <span>Vpp=--</span>
                        <span>RMS=--</span>
                        <span>Freq=--</span>
                        <span>Max=--</span>
                    </div>
                    <div class="measurement-row" id="measure-ch3-${this.id}">
                        <span class="ch-label ch3">CH3:</span>
                        <span>Vpp=--</span>
                        <span>RMS=--</span>
                        <span>Freq=--</span>
                        <span>Max=--</span>
                    </div>
                    <div class="measurement-row info-row">
                        <span>Sample Rate: <span id="sample-rate-${this.id}">${this.acquisition.sampleRate}</span> Hz</span>
                        <span>Buffer: <span id="buffer-status-${this.id}">0/${this.bufferSize}</span></span>
                        <span>⏱ <span id="timestamp-${this.id}">--:--:--.---</span></span>
                    </div>
                </div>
            </div>
        `;
    }

    afterRender() {
        // Get canvas
        this.canvas = document.getElementById(`oscilloscope-canvas-${this.id}`);
        if (!this.canvas) {
            console.error('[Oscilloscope] Canvas not found');
            return;
        }

        this.ctx = this.canvas.getContext('2d');

        // Set canvas size based on mode
        this.resizeCanvas();

        // Add mouse interaction for trigger level dragging
        this.setupTriggerDragging();

        // Start rendering loop
        this.startRendering();

        // Connect to SSE stream
        this.connectStream();

        console.log('[Oscilloscope] Initialized:', this.canvas.width, 'x', this.canvas.height);
    }

    setupTriggerDragging() {
        let isDragging = false;
        const hitRadius = 10; // pixels from trigger line to detect hover/click

        // Mouse cursor handling
        this.canvas.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const y = e.clientY - rect.top;

            // Check if near trigger line
            if (this.triggerLineY && Math.abs(y - this.triggerLineY) < hitRadius) {
                this.canvas.style.cursor = 'ns-resize';

                // If dragging, update trigger level
                if (isDragging) {
                    this.updateTriggerFromMouse(y);
                }
            } else {
                if (!isDragging) {
                    this.canvas.style.cursor = 'default';
                }
            }

            // Update while dragging
            if (isDragging) {
                this.updateTriggerFromMouse(y);
            }
        });

        // Start dragging
        this.canvas.addEventListener('mousedown', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const y = e.clientY - rect.top;

            if (this.triggerLineY && Math.abs(y - this.triggerLineY) < hitRadius) {
                isDragging = true;
                this.canvas.style.cursor = 'ns-resize';
            }
        });

        // Stop dragging
        this.canvas.addEventListener('mouseup', () => {
            isDragging = false;
        });

        this.canvas.addEventListener('mouseleave', () => {
            isDragging = false;
            this.canvas.style.cursor = 'default';
        });
    }

    updateTriggerFromMouse(mouseY) {
        const h = this.canvas.height;
        const centerY = h / 2;
        const voltsPerDiv = this.vertical[this.trigger.source].voltsPerDiv;
        const pixelsPerVolt = (h / this.vertical.divisions) / voltsPerDiv;

        // Convert mouse Y to trigger level value
        const newLevel = -(mouseY - centerY) / pixelsPerVolt;

        // Clamp to reasonable range
        const maxLevel = this.vertical.divisions * voltsPerDiv;
        this.trigger.level = Math.max(-maxLevel, Math.min(maxLevel, newLevel));

        // Update any UI controls
        const levelInput = document.getElementById(`trigger-level-${this.id}`);
        if (levelInput) {
            levelInput.value = this.trigger.level.toFixed(2);
        }
    }

    resizeCanvas() {
        const parent = this.canvas.parentElement;
        if (!parent) {
            console.warn('[Oscilloscope] No parent element for canvas');
            return;
        }

        const rect = parent.getBoundingClientRect();

        if (this.mode === 'compact') {
            this.canvas.width = rect.width - 20;
            // Cap height at 350px for compact mode to avoid covering other widgets
            this.canvas.height = Math.min(350, Math.max(300, rect.height - 20));
            console.log('[Oscilloscope] Resized to compact:', this.canvas.width, 'x', this.canvas.height);
        } else {
            this.canvas.width = rect.width - 100;  // Leave space for voltage scale
            this.canvas.height = 600;
            console.log('[Oscilloscope] Resized to fullscreen:', this.canvas.width, 'x', this.canvas.height);
        }

        // Enable anti-aliasing
        if (this.ctx) {
            this.ctx.imageSmoothingEnabled = true;
            this.ctx.imageSmoothingQuality = 'high';
        }
    }

    startRendering() {
        const render = () => {
            this.drawOscilloscope();
            this.animationFrameId = requestAnimationFrame(render);
        };
        render();
    }

    drawOscilloscope() {
        if (!this.ctx) return;

        const w = this.canvas.width;
        const h = this.canvas.height;

        // Clear canvas
        this.ctx.fillStyle = '#0a0e27';
        this.ctx.fillRect(0, 0, w, h);

        // Draw grid
        this.drawGrid(w, h);

        // Draw trigger level indicator
        this.drawTriggerLevel(w, h);

        // Draw waveforms
        this.drawWaveforms(w, h);

        // Draw center crosshair
        this.drawCrosshair(w, h);
    }

    drawGrid(w, h) {
        this.ctx.lineWidth = 1;

        const hDivs = this.timebase.divisions;
        const vDivs = this.vertical.divisions;
        const subdivs = this.grid.subdivisions;

        // Vertical lines
        for (let i = 0; i <= hDivs; i++) {
            const x = (i / hDivs) * w;

            // Major division
            this.ctx.strokeStyle = this.grid.majorColor;
            this.ctx.beginPath();
            this.ctx.moveTo(x, 0);
            this.ctx.lineTo(x, h);
            this.ctx.stroke();

            // Subdivisions
            if (i < hDivs) {
                this.ctx.strokeStyle = this.grid.minorColor;
                for (let j = 1; j < subdivs; j++) {
                    const subX = x + (j / subdivs) * (w / hDivs);
                    this.ctx.setLineDash([2, 3]);
                    this.ctx.beginPath();
                    this.ctx.moveTo(subX, 0);
                    this.ctx.lineTo(subX, h);
                    this.ctx.stroke();
                    this.ctx.setLineDash([]);
                }
            }
        }

        // Horizontal lines
        for (let i = 0; i <= vDivs; i++) {
            const y = (i / vDivs) * h;

            // Major division
            this.ctx.strokeStyle = this.grid.majorColor;
            this.ctx.beginPath();
            this.ctx.moveTo(0, y);
            this.ctx.lineTo(w, y);
            this.ctx.stroke();

            // Subdivisions
            if (i < vDivs) {
                this.ctx.strokeStyle = this.grid.minorColor;
                for (let j = 1; j < subdivs; j++) {
                    const subY = y + (j / subdivs) * (h / vDivs);
                    this.ctx.setLineDash([2, 3]);
                    this.ctx.beginPath();
                    this.ctx.moveTo(0, subY);
                    this.ctx.lineTo(w, subY);
                    this.ctx.stroke();
                    this.ctx.setLineDash([]);
                }
            }
        }
    }

    drawCrosshair(w, h) {
        const centerX = w / 2;
        const centerY = h / 2;
        const size = 10;

        this.ctx.strokeStyle = '#3a5a7a';
        this.ctx.lineWidth = 1.5;

        // Horizontal
        this.ctx.beginPath();
        this.ctx.moveTo(centerX - size, centerY);
        this.ctx.lineTo(centerX + size, centerY);
        this.ctx.stroke();

        // Vertical
        this.ctx.beginPath();
        this.ctx.moveTo(centerX, centerY - size);
        this.ctx.lineTo(centerX, centerY + size);
        this.ctx.stroke();
    }

    drawTriggerLevel(w, h) {
        if (this.trigger.mode === 'off') return;

        const channel = this.buffers[this.trigger.source];
        if (!channel || !channel.enabled) return;

        const voltsPerDiv = this.vertical[this.trigger.source].voltsPerDiv;
        const level = this.trigger.level;

        // Convert trigger level to Y position
        const centerY = h / 2;
        const pixelsPerVolt = (h / this.vertical.divisions) / voltsPerDiv;
        const y = centerY - (level * pixelsPerVolt);

        if (y < 0 || y > h) return;

        // Store trigger Y position for mouse interaction
        this.triggerLineY = y;

        // Draw trigger line
        this.ctx.strokeStyle = '#ff00ff';
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([8, 4]);
        this.ctx.beginPath();
        this.ctx.moveTo(0, y);
        this.ctx.lineTo(w, y);
        this.ctx.stroke();
        this.ctx.setLineDash([]);

        // Draw trigger level label (left side)
        this.ctx.fillStyle = '#ff00ff';
        this.ctx.font = 'bold 12px monospace';
        this.ctx.textAlign = 'left';
        this.ctx.textBaseline = 'middle';
        const label = `T: ${level.toFixed(2)}g`;
        const labelWidth = this.ctx.measureText(label).width;

        // Background for label
        this.ctx.fillStyle = 'rgba(255, 0, 255, 0.2)';
        this.ctx.fillRect(5, y - 10, labelWidth + 10, 20);

        // Label text
        this.ctx.fillStyle = '#ff00ff';
        this.ctx.fillText(label, 10, y);

        // Draw trigger arrow (right side)
        this.ctx.fillStyle = '#ff00ff';
        this.ctx.beginPath();
        if (this.trigger.slope === 'rising') {
            this.ctx.moveTo(w - 20, y);
            this.ctx.lineTo(w - 10, y - 5);
            this.ctx.lineTo(w - 10, y + 5);
        } else {
            this.ctx.moveTo(w - 20, y);
            this.ctx.lineTo(w - 10, y + 5);
            this.ctx.lineTo(w - 10, y - 5);
        }
        this.ctx.fill();
    }

    drawWaveforms(w, h) {
        const channels = ['ch1', 'ch2', 'ch3'];

        for (const chName of channels) {
            const channel = this.buffers[chName];
            if (!channel.enabled || channel.data.length === 0) continue;

            const vertSettings = this.vertical[chName];
            if (!vertSettings.enabled) continue;

            this.drawWaveform(w, h, channel, vertSettings);
        }
    }

    drawWaveform(w, h, channel, vertSettings) {
        const data = channel.data;
        if (data.length < 2) return;

        const centerY = h / 2;
        const voltsPerDiv = vertSettings.voltsPerDiv;
        const pixelsPerVolt = (h / this.vertical.divisions) / voltsPerDiv;

        // Calculate points to display based on timebase
        const totalTime = this.timebase.timePerDiv * this.timebase.divisions;
        const pointsToShow = Math.min(data.length, Math.floor(totalTime * this.acquisition.sampleRate));

        if (pointsToShow < 2) return;

        // Draw waveform
        this.ctx.strokeStyle = channel.color;
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();

        for (let i = 0; i < pointsToShow; i++) {
            const value = data[data.length - pointsToShow + i];
            const x = (i / pointsToShow) * w;
            const y = centerY - (value * pixelsPerVolt) + vertSettings.position;

            if (i === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }
        }

        this.ctx.stroke();
    }

    connectStream() {
        const token = sessionStorage.getItem('auth_token') || '';
        const nodeId = this.config.node_id;

        if (!nodeId) {
            console.warn('[Oscilloscope] No node_id configured');
            return;
        }

        // Build channel map from configuration (support any pin names)
        const channelConfig = [
            { pin: this.config.ch1_pin, ch: 'ch1' },
            { pin: this.config.ch2_pin, ch: 'ch2' },
            { pin: this.config.ch3_pin, ch: 'ch3' }
        ];

        // Filter out unconfigured channels
        const activeChannels = channelConfig.filter(cfg => cfg.pin && cfg.pin !== '');

        if (activeChannels.length === 0) {
            console.warn('[Oscilloscope] No pins configured for any channel');
            return;
        }

        console.log('[Oscilloscope] Connecting to channels:', activeChannels);

        // Close any existing connections first
        this.eventSources.forEach(es => es.close());
        this.eventSources = [];
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }

        // Use WebSocket only (SSE disabled) - subscribe via global manager
        console.log('[Oscilloscope] Using WebSocket streaming mode (global manager)');

        // Subscribe to each channel via global WebSocket manager
        activeChannels.forEach(cfg => {
            const widgetChannelId = `${this.id}_${cfg.ch}`;
            wsManager.subscribe(widgetChannelId, nodeId, cfg.pin, (value, timestamp) => {
                if (!this.acquisition.running) return;

                try {
                    const plotValue = Array.isArray(value) ? value[0] : value;
                    const chName = cfg.ch;

                    // Debug logging
                    if (this.buffers[chName].data.length % 50 === 0) {
                        console.log(`[Oscilloscope] ${chName} received value:`, plotValue, 'buffer size:', this.buffers[chName].data.length);
                    }

                    // Add to buffer
                    this.buffers[chName].data.push(plotValue);

                    // Limit buffer size
                    if (this.buffers[chName].data.length > this.bufferSize) {
                        this.buffers[chName].data.shift();
                    }

                    // Update measurements periodically
                    if (this.buffers[chName].data.length % 100 === 0) {
                        this.updateMeasurements(chName);
                    }

                } catch (error) {
                    console.error('[Oscilloscope] WebSocket data error:', error);
                }
            });
        });

        console.log(`[Oscilloscope] Subscribed to ${activeChannels.length} channel(s) via WebSocket`);
    }

    parseBinaryMessage(arrayBuffer) {
        try {
            const view = new DataView(arrayBuffer);
            let offset = 0;

            // Read message type (1 byte)
            const messageType = view.getUint8(offset);
            offset += 1;

            if (messageType !== 1) {  // SignalData = 1
                return null;
            }

            // Read signal_id length (4 bytes)
            const signalIdLen = view.getUint32(offset, true);
            offset += 4;

            // Read signal_id string
            const signalIdBytes = new Uint8Array(arrayBuffer, offset, signalIdLen);
            const signalId = new TextDecoder().decode(signalIdBytes);
            offset += signalIdLen;

            // Read timestamp (8 bytes)
            const timestampLow = view.getUint32(offset, true);
            offset += 4;
            const timestampHigh = view.getUint32(offset, true);
            offset += 4;
            const timestamp = timestampLow + (timestampHigh * 0x100000000);

            // Read sample count (4 bytes)
            const sampleCount = view.getUint32(offset, true);
            offset += 4;

            // Read samples (4 bytes per float)
            const samples = [];
            for (let i = 0; i < sampleCount; i++) {
                samples.push(view.getFloat32(offset, true));
                offset += 4;
            }

            // Read statistics (skip for now, but they're there)
            // original_sample_count (4 bytes)
            // min_value (4 bytes)
            // max_value (4 bytes)
            // avg_value (4 bytes)

            return {
                signal_id: signalId,
                timestamp: timestamp,
                samples: samples
            };

        } catch (error) {
            console.error('[Oscilloscope] Binary parse error:', error);
            return null;
        }
    }

    updateMeasurements(chName) {
        const data = this.buffers[chName].data;
        if (data.length < 2) return;

        // Calculate measurements
        const max = Math.max(...data);
        const min = Math.min(...data);
        const vpp = max - min;

        // RMS calculation
        const sumSquares = data.reduce((sum, val) => sum + val * val, 0);
        const rms = Math.sqrt(sumSquares / data.length);

        // Simple frequency estimation (zero crossing)
        let crossings = 0;
        for (let i = 1; i < data.length; i++) {
            if ((data[i-1] < 0 && data[i] >= 0) || (data[i-1] >= 0 && data[i] < 0)) {
                crossings++;
            }
        }
        const duration = data.length / this.acquisition.sampleRate;
        const freq = crossings / (2 * duration);

        this.measurements[chName] = {
            vpp: vpp,
            rms: rms,
            freq: freq > 1 ? freq : 0,
            max: max,
            min: min
        };

        // Update UI
        this.updateMeasurementDisplay(chName);
    }

    updateMeasurementDisplay(chName) {
        const m = this.measurements[chName];
        const chNum = chName.replace('ch', '');

        if (this.mode === 'compact') {
            const el = document.getElementById(`measure-${chName}-${this.id}`);
            if (el) {
                el.textContent = `CH${chNum}: Vpp=${m.vpp.toFixed(2)}g RMS=${m.rms.toFixed(2)}g`;
            }
        } else {
            const el = document.getElementById(`measure-${chName}-${this.id}`);
            if (el) {
                el.innerHTML = `
                    <span class="ch-label ${chName}">CH${chNum}:</span>
                    <span>Vpp=${m.vpp.toFixed(2)}g</span>
                    <span>RMS=${m.rms.toFixed(2)}g</span>
                    <span>Freq=${m.freq > 1 ? m.freq.toFixed(1) : 'N/A'}Hz</span>
                    <span>Max=${m.max.toFixed(2)}g</span>
                `;
            }
        }
    }

    formatTime(seconds) {
        if (seconds >= 1) return `${seconds}s`;
        if (seconds >= 0.001) return `${(seconds * 1000).toFixed(0)}ms`;
        return `${(seconds * 1000000).toFixed(0)}µs`;
    }

    destroy() {
        console.log('[Oscilloscope] Destroying widget', this.id);

        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
        }

        // Unsubscribe from all WebSocket channels
        if (typeof wsManager !== 'undefined' && this.config && this.config.channels) {
            console.log('[Oscilloscope] Unsubscribing from WebSocket channels');
            this.config.channels.forEach((cfg, index) => {
                if (cfg.enabled) {
                    const widgetChannelId = `${this.id}_CH${index + 1}`;
                    wsManager.unsubscribe(widgetChannelId);
                }
            });
        }

        // CRITICAL: Remove any fullscreen overlay that might still exist
        const fullscreenOverlay = document.getElementById(`oscilloscope-fullscreen-${this.id}`);
        if (fullscreenOverlay) {
            console.log('[Oscilloscope] Removing fullscreen overlay during destroy');
            fullscreenOverlay.remove();
        }
    }
}

// Helper to get widget from dashboard
function getOscWidget(widgetId) {
    if (typeof dashboard !== 'undefined' && dashboard && dashboard.widgets) {
        const item = dashboard.widgets.get(widgetId);
        return item ? item.widget : null;
    }
    return null;
}

// Global control functions (called from HTML onclick handlers)
function updateTimebase(widgetId, value) {
    const widget = getOscWidget(widgetId);
    if (widget) {
        widget.timebase.timePerDiv = parseFloat(value);
    }
}

function updateTriggerMode(widgetId, mode) {
    const widget = getOscWidget(widgetId);
    if (widget) {
        widget.trigger.mode = mode;
    }
}

function toggleRun(widgetId) {
    const widget = getOscWidget(widgetId);
    if (widget) {
        widget.acquisition.running = !widget.acquisition.running;
        const btn = document.getElementById(`btn-run-${widgetId}`);
        if (btn) {
            btn.textContent = widget.acquisition.running ? '⏸ STOP' : '▶ RUN';
            btn.classList.toggle('active', widget.acquisition.running);
        }
    }
}

function expandOscilloscope(widgetId) {
    const widget = getOscWidget(widgetId);
    if (!widget) return;

    console.log('[Oscilloscope] Expanding to fullscreen:', widgetId);

    // Create fullscreen overlay
    const overlay = document.createElement('div');
    overlay.id = `oscilloscope-fullscreen-${widgetId}`;
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: #0a0e27;
        z-index: 10000;
        display: flex;
        flex-direction: column;
        padding: 20px;
    `;

    // Store original parent to restore later
    const originalParent = widget.canvas.parentElement;
    const originalNextSibling = widget.canvas.nextSibling;

    // Declare escHandler first (will be defined later)
    let escHandler = null;

    // Close function
    const closeFullscreen = () => {
        console.log('[Oscilloscope] ===== CLOSE BUTTON CLICKED =====');

        // Remove ESC key handler
        if (escHandler) {
            document.removeEventListener('keydown', escHandler);
            console.log('[Oscilloscope] ESC handler removed');
        }

        // Move canvas back to original parent (in correct position)
        try {
            if (originalNextSibling) {
                originalParent.insertBefore(widget.canvas, originalNextSibling);
            } else {
                originalParent.appendChild(widget.canvas);
            }
            console.log('[Oscilloscope] Canvas moved back to original parent');
        } catch (e) {
            console.error('[Oscilloscope] Error moving canvas:', e);
        }

        // Reset ALL canvas styles
        widget.canvas.style.cssText = '';
        widget.canvas.style.cursor = '';
        console.log('[Oscilloscope] Canvas styles reset');

        // Remove overlay completely
        try {
            if (overlay && overlay.parentElement) {
                overlay.parentElement.removeChild(overlay);
                console.log('[Oscilloscope] Overlay removed from DOM');
            }
        } catch (e) {
            console.error('[Oscilloscope] Error removing overlay:', e);
        }

        // Double-check overlay is really gone
        setTimeout(() => {
            const checkOverlay = document.getElementById(`oscilloscope-fullscreen-${widgetId}`);
            if (checkOverlay) {
                console.warn('[Oscilloscope] Overlay still exists! Force removing...');
                try {
                    checkOverlay.remove();
                } catch (e) {
                    console.error('[Oscilloscope] Error force-removing overlay:', e);
                }
            } else {
                console.log('[Oscilloscope] Overlay confirmed removed');
            }
        }, 100);

        // Reset document body overflow
        document.body.style.overflow = '';

        // Restore original size
        setTimeout(() => {
            widget.resizeCanvas();
            console.log('[Oscilloscope] Canvas resized to:', widget.canvas.width, 'x', widget.canvas.height);
        }, 150);

        console.log('[Oscilloscope] ===== CLOSE COMPLETE =====');
    };

    // Close button
    const closeBtn = document.createElement('button');
    closeBtn.textContent = '✕ Close';
    closeBtn.style.cssText = `
        position: absolute;
        top: 20px;
        right: 20px;
        padding: 10px 20px;
        background: #ff3b3b;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 16px;
        font-weight: bold;
        z-index: 10001;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    `;

    // Use addEventListener instead of onclick
    closeBtn.addEventListener('click', closeFullscreen);
    console.log('[Oscilloscope] Close button event listener attached');

    // Create fullscreen control panel
    const controlPanel = document.createElement('div');
    controlPanel.style.cssText = `
        position: absolute;
        right: 20px;
        top: 80px;
        width: 280px;
        background: #16213e;
        border: 1px solid #2a5a7a;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        max-height: calc(100vh - 160px);
        overflow-y: auto;
    `;

    controlPanel.innerHTML = `
        <div style="color: #00a8ff; font-weight: bold; margin-bottom: 15px; font-size: 14px;">⚙️ CONTROLS</div>

        <div style="margin-bottom: 20px;">
            <div style="color: #8a9ab0; font-size: 12px; margin-bottom: 8px; font-weight: bold;">HORIZONTAL</div>
            <div style="margin-bottom: 10px;">
                <label style="color: #e0e6ed; font-size: 12px; display: block; margin-bottom: 4px;">Time/Div</label>
                <select id="fs-timebase-${widgetId}" onchange="updateTimebase('${widgetId}', this.value)"
                        style="width: 100%; padding: 6px; background: #0a0e27; color: #e0e6ed; border: 1px solid #2a5a7a; border-radius: 4px;">
                    ${widget.timebase.options.map(t =>
                        `<option value="${t}" ${t === widget.timebase.timePerDiv ? 'selected' : ''}>${widget.formatTime(t)}</option>`
                    ).join('')}
                </select>
            </div>
        </div>

        <div style="margin-bottom: 20px;">
            <div style="color: #8a9ab0; font-size: 12px; margin-bottom: 8px; font-weight: bold;">CHANNELS</div>
            ${['ch1', 'ch2', 'ch3'].map((ch, idx) => {
                const colors = { ch1: '#ff3b3b', ch2: '#00ff88', ch3: '#ffaa00' };
                return `
                    <div style="margin-bottom: 12px; padding: 8px; background: #0a0e27; border-radius: 4px;">
                        <label style="display: flex; align-items: center; margin-bottom: 6px;">
                            <input type="checkbox" checked onchange="toggleChannel('${widgetId}', '${ch}', this.checked)"
                                   style="margin-right: 8px;">
                            <span style="color: ${colors[ch]}; font-weight: bold; font-size: 12px;">${ch.toUpperCase()}</span>
                        </label>
                        <select onchange="updateVoltsPerDiv('${widgetId}', '${ch}', this.value)"
                                style="width: 100%; padding: 4px; background: #16213e; color: #e0e6ed; border: 1px solid #2a5a7a; border-radius: 3px; font-size: 11px;">
                            ${widget.vertical.options.map(v =>
                                `<option value="${v}" ${v === 1.0 ? 'selected' : ''}>${v}g/div</option>`
                            ).join('')}
                        </select>
                    </div>
                `;
            }).join('')}
        </div>

        <div style="margin-bottom: 20px;">
            <div style="color: #8a9ab0; font-size: 12px; margin-bottom: 8px; font-weight: bold;">TRIGGER</div>
            <div style="margin-bottom: 10px;">
                <label style="color: #e0e6ed; font-size: 12px; display: block; margin-bottom: 4px;">Mode</label>
                <select id="fs-trigger-mode-${widgetId}" onchange="updateTriggerMode('${widgetId}', this.value)"
                        style="width: 100%; padding: 6px; background: #0a0e27; color: #e0e6ed; border: 1px solid #2a5a7a; border-radius: 4px;">
                    <option value="auto" selected>Auto</option>
                    <option value="normal">Normal</option>
                    <option value="single">Single</option>
                </select>
            </div>
        </div>

        <div>
            <button class="btn-control active" id="fs-btn-run-${widgetId}" onclick="toggleRun('${widgetId}')"
                    style="width: 100%; padding: 10px; background: #00ff88; color: #0a0e27; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; font-size: 13px;">
                ${widget.acquisition.running ? '⏸ STOP' : '▶ RUN'}
            </button>
        </div>
    `;

    // Canvas container (left side, taking most space)
    const canvasContainer = document.createElement('div');
    canvasContainer.style.cssText = `
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 300px;
        margin-top: 20px;
    `;

    // Move widget's canvas to fullscreen
    canvasContainer.appendChild(widget.canvas);

    overlay.appendChild(closeBtn);
    overlay.appendChild(controlPanel);
    overlay.appendChild(canvasContainer);
    document.body.appendChild(overlay);

    // Resize canvas to fullscreen (account for control panel on right)
    widget.canvas.width = window.innerWidth - 400;
    widget.canvas.height = window.innerHeight - 100;

    // Add ESC key handler to close
    escHandler = (e) => {
        if (e.key === 'Escape') {
            e.preventDefault();
            console.log('[Oscilloscope] ESC key pressed, closing fullscreen');
            closeFullscreen();
        }
    };
    document.addEventListener('keydown', escHandler);
    console.log('[Oscilloscope] ESC handler registered');

    console.log('[Oscilloscope] Fullscreen mode activated:', widget.canvas.width, 'x', widget.canvas.height);
}

function toggleChannel(widgetId, channel, enabled) {
    const widget = getOscWidget(widgetId);
    if (widget) {
        widget.vertical[channel].enabled = enabled;
        widget.buffers[channel].enabled = enabled;
    }
}

function updateVoltsPerDiv(widgetId, channel, value) {
    const widget = getOscWidget(widgetId);
    if (widget) {
        widget.vertical[channel].voltsPerDiv = parseFloat(value);
    }
}

function updateTriggerSource(widgetId, source) {
    const widget = getOscWidget(widgetId);
    if (widget) {
        widget.trigger.source = source;
    }
}

function updateTriggerLevel(widgetId, level) {
    const widget = getOscWidget(widgetId);
    if (widget) {
        widget.trigger.level = parseFloat(level);
    }
}

function updateTriggerSlope(widgetId, slope) {
    const widget = getOscWidget(widgetId);
    if (widget) {
        widget.trigger.slope = slope;
    }
}

function updateTimePosition(widgetId, position) {
    const widget = getOscWidget(widgetId);
    if (widget) {
        widget.timebase.position = parseInt(position);
    }
}

function singleCapture(widgetId) {
    const widget = getOscWidget(widgetId);
    if (widget) {
        widget.trigger.mode = 'single';
        widget.trigger.armed = true;
        widget.acquisition.running = true;
    }
}

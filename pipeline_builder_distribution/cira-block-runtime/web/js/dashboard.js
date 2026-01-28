// Dashboard Manager
class DashboardManager {
    constructor() {
        this.grid = null;
        this.widgets = new Map();
        this.isEditMode = false;
        this.metricsInterval = null;
        this.widgetIdCounter = 0;

        // Cache for block list (invalidated on deployment)
        this.blocksCache = null;
        this.blocksCacheTimestamp = 0;
        this.blocksCacheVersion = 0; // Incremented on deployment

        // Request guards to prevent piling up
        this.isFetchingBlocks = false;
        this.isFetchingBlockData = false;
    }

    async initialize() {
        // CRITICAL: Preload blocks.json BEFORE widgets start SSE connections
        // This prevents connection pool saturation from blocking the blocks fetch
        console.log('[Dashboard] Preloading blocks.json before widget initialization...');
        await this.fetchBlocks(false);
        console.log('[Dashboard] Blocks preloaded, proceeding with dashboard initialization');

        // Initialize GridStack
        this.grid = GridStack.init({
            float: true,
            cellHeight: '80px',
            minRow: 1,
            margin: 10,
            animate: true
        });

        // Load saved dashboard or use default
        this.loadDashboard();

        // Setup event listeners
        this.setupEventListeners();

        // Start metrics polling
        // TEMPORARILY DISABLED: Jetson too slow to handle both polling and configuration
        // this.startMetricsPolling();

        // Update connection status
        this.updateConnectionStatus(true);
    }

    setupEventListeners() {
        // Edit mode toggle
        document.getElementById('btn-edit-mode').addEventListener('click', () => {
            this.enterEditMode();
        });

        // Save dashboard
        document.getElementById('btn-save-dashboard').addEventListener('click', () => {
            this.saveDashboard();
        });

        // Cancel edit
        document.getElementById('btn-cancel-edit').addEventListener('click', () => {
            this.exitEditMode(false);
        });

        // Widget palette drag
        this.setupWidgetPalette();
    }

    setupWidgetPalette() {
        const paletteItems = document.querySelectorAll('.palette-item');

        paletteItems.forEach(item => {
            item.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('widgetType', item.dataset.widget);
            });
        });

        // Allow dropping on grid
        const gridElement = document.querySelector('.grid-stack');
        gridElement.addEventListener('dragover', (e) => {
            e.preventDefault();
        });

        gridElement.addEventListener('drop', (e) => {
            e.preventDefault();
            if (!this.isEditMode) return;

            const widgetType = e.dataTransfer.getData('widgetType');
            if (widgetType) {
                this.addWidget(widgetType);
            }
        });
    }

    enterEditMode() {
        this.isEditMode = true;

        // Show palette and save button
        document.getElementById('widget-palette').style.display = 'block';
        document.getElementById('btn-save-dashboard').style.display = 'inline-block';
        document.getElementById('btn-cancel-edit').style.display = 'inline-block';
        document.getElementById('btn-edit-mode').style.display = 'none';

        // Add editing class to content
        document.querySelector('.dashboard-content').classList.add('editing');

        // Enable grid editing
        this.grid.enableMove(true);
        this.grid.enableResize(true);

        // Hide empty state
        document.getElementById('empty-state').style.display = 'none';
    }

    exitEditMode(save = false) {
        this.isEditMode = false;

        // Hide palette and save button
        document.getElementById('widget-palette').style.display = 'none';
        document.getElementById('btn-save-dashboard').style.display = 'none';
        document.getElementById('btn-cancel-edit').style.display = 'none';
        document.getElementById('btn-edit-mode').style.display = 'inline-block';

        // Remove editing class
        document.querySelector('.dashboard-content').classList.remove('editing');

        // Disable grid editing
        this.grid.enableMove(false);
        this.grid.enableResize(false);

        if (save) {
            // Save handled separately
        } else {
            // Reload dashboard to revert changes
            this.loadDashboard();
        }
    }

    addWidget(type, config = null, gridOptions = null) {
        const widgetId = `widget-${Date.now()}-${this.widgetIdCounter++}`;
        const widget = WidgetFactory.create(type, widgetId, config);

        // Default grid options
        const defaultGridOptions = {
            w: 3,
            h: 3,
            x: 0,
            y: 0,
            autoPosition: true
        };

        const options = { ...defaultGridOptions, ...(gridOptions || {}) };

        // Add to grid
        const gridItem = this.grid.addWidget({
            ...options,
            content: `<div id="widget-container-${widgetId}"></div>`
        });

        // Render widget
        const container = gridItem.querySelector(`#widget-container-${widgetId}`);
        widget.render(container);

        // Store widget
        this.widgets.set(widgetId, { widget, gridItem });

        return widgetId;
    }

    removeWidget(widgetId) {
        const item = this.widgets.get(widgetId);
        if (!item) return;

        // Destroy widget
        if (item.widget.destroy) {
            item.widget.destroy();
        }

        // Remove from grid
        this.grid.removeWidget(item.gridItem);

        // Remove from map
        this.widgets.delete(widgetId);
    }

    async loadDashboard() {
        try {
            // Try loading from server
            const response = await fetch('/api/dashboard/config', {
                headers: authManager.getHeaders()
            });

            let config = null;

            if (response.ok) {
                config = await response.json();
            }

            // Fallback to localStorage
            if (!config || Object.keys(config).length === 0) {
                const localConfig = localStorage.getItem('dashboard_config');
                if (localConfig) {
                    config = JSON.parse(localConfig);
                }
            }

            // Load config or use default
            if (config && config.widgets && config.widgets.length > 0) {
                this.applyDashboardConfig(config);
                document.getElementById('empty-state').style.display = 'none';
            } else {
                this.loadDefaultDashboard();
            }
        } catch (error) {
            console.error('Failed to load dashboard:', error);
            this.loadDefaultDashboard();
        }
    }

    applyDashboardConfig(config) {
        // Clear existing widgets
        this.widgets.forEach((item, id) => {
            this.removeWidget(id);
        });

        // Add widgets from config
        config.widgets.forEach(widgetConfig => {
            this.addWidget(
                widgetConfig.type,
                widgetConfig.config,
                widgetConfig.gridOptions
            );
        });
    }

    loadDefaultDashboard() {
        // Default dashboard layout
        this.addWidget('status', { title: 'Runtime Status' }, { x: 0, y: 0, w: 4, h: 3 });
        this.addWidget('gauge', { title: 'CPU Usage', dataSource: 'system.cpu_usage' }, { x: 4, y: 0, w: 4, h: 3 });
        this.addWidget('chart', { title: 'CPU History', dataSource: 'system.cpu_usage' }, { x: 8, y: 0, w: 4, h: 4 });
        this.addWidget('logs', { title: 'Runtime Logs' }, { x: 0, y: 3, w: 8, h: 5 });

        document.getElementById('empty-state').style.display = 'none';
    }

    async saveDashboard() {
        const config = this.serializeDashboard();

        try {
            // Save to server
            await fetch('/api/dashboard/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...authManager.getHeaders()
                },
                body: JSON.stringify(config)
            });

            // Save to localStorage as backup
            localStorage.setItem('dashboard_config', JSON.stringify(config));

            alert('Dashboard saved successfully!');
            this.exitEditMode(true);
        } catch (error) {
            console.error('Failed to save dashboard:', error);
            alert('Failed to save dashboard: ' + error.message);
        }
    }

    serializeDashboard() {
        const widgets = [];

        this.widgets.forEach((item, id) => {
            const gridNode = item.gridItem.gridstackNode;

            widgets.push({
                type: item.widget.type,
                config: item.widget.config,
                gridOptions: {
                    x: gridNode.x,
                    y: gridNode.y,
                    w: gridNode.w,
                    h: gridNode.h
                }
            });
        });

        return {
            version: 1,
            widgets: widgets
        };
    }

    startMetricsPolling() {
        this.fetchMetrics();

        // Poll every 10 seconds (reduced from 1s to prevent connection overload)
        this.metricsInterval = setInterval(() => {
            this.fetchMetrics();
        }, 2000);
    }

    async fetchBlocks(forceRefresh = false) {
        console.log('[Dashboard] fetchBlocks called (forceRefresh:', forceRefresh, ')');

        // Prevent concurrent requests
        if (this.isFetchingBlocks) {
            console.log('[Dashboard] Already fetching blocks, skipping...');
            return this.blocksCache || [];
        }

        this.isFetchingBlocks = true;

        try {
            // Fetch static blocks.json file (no auth needed, no timeout issues)
            console.log('[Dashboard] Fetching /blocks.json...');

            // Add timeout to prevent hanging if connection pool is saturated
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

            const response = await fetch('/blocks.json', { signal: controller.signal });
            clearTimeout(timeoutId);

            console.log('[Dashboard] Response received, status:', response.status);

            if (response.ok) {
                const data = await response.json();
                console.log('[Dashboard] Raw response data:', data);

                // Handle response format with version
                const blocks = data.blocks || data; // Support both old array format and new object format
                const serverVersion = data.version || 0;
                console.log('[Dashboard] Extracted blocks:', blocks, 'version:', serverVersion);

                // Check if pipeline changed (version mismatch)
                if (!forceRefresh && this.blocksCache !== null && this.blocksCacheVersion === serverVersion) {
                    console.log('[Dashboard] Pipeline unchanged (version:', serverVersion, ') - using cache');
                    return this.blocksCache;
                }

                // Version changed or no cache - update cache
                if (this.blocksCacheVersion !== serverVersion && this.blocksCacheVersion !== 0) {
                    console.log('[Dashboard] Pipeline changed! Old version:', this.blocksCacheVersion, '→ New version:', serverVersion);
                } else {
                    console.log('[Dashboard] Caching blocks (version:', serverVersion, ')');
                }

                this.blocksCache = blocks;
                this.blocksCacheVersion = serverVersion;
                this.blocksCacheTimestamp = Date.now();

                return blocks;
            } else {
                console.error('[Dashboard] Failed to fetch blocks.json, status:', response.status);
            }
        } catch (error) {
            console.error('[Dashboard] Error fetching blocks.json:', error);
        } finally {
            this.isFetchingBlocks = false;
        }

        // Return cached blocks on error, or empty array
        if (this.blocksCache !== null) {
            console.log('[Dashboard] Returning cached blocks due to error');
            return this.blocksCache;
        }
        return [];
    }

    async fetchBlockData() {
        // Prevent concurrent requests
        if (this.isFetchingBlockData) {
            return {};
        }

        this.isFetchingBlockData = true;

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout (increased for slow Jetson)

            const response = await fetch('/api/blocks/data', {
                headers: authManager.getHeaders(),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                console.error('Fetch block data timeout - continuing with empty data');
            } else {
                console.error('Failed to fetch block data:', error);
            }
        } finally {
            this.isFetchingBlockData = false;
        }
        return {};
    }

    async fetchMetrics() {
        try {
            // Fetch real block data
            const blockData = await this.fetchBlockData();

            // Fetch system metrics
            const response = await fetch('/api/metrics', {
                headers: authManager.getHeaders()
            });

            if (response.ok) {
                const metrics = await response.json();
                metrics.blockData = blockData; // Add block data to metrics
                this.updateWidgets(metrics);
                this.updateConnectionStatus(true);
            } else {
                this.updateConnectionStatus(false);
            }
        } catch (error) {
            console.error('Failed to fetch metrics:', error);
            this.updateConnectionStatus(false);
        }
    }

    updateWidgets(metrics) {
        this.widgets.forEach((item) => {
            if (item.widget.update) {
                item.widget.update(metrics);
            }
        });
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');

        if (connected) {
            statusElement.classList.remove('disconnected');
            statusElement.classList.add('connected');
            statusElement.querySelector('.status-text').textContent = 'Connected';
        } else {
            statusElement.classList.remove('connected');
            statusElement.classList.add('disconnected');
            statusElement.querySelector('.status-text').textContent = 'Disconnected';
        }
    }
}

// Global functions for widget actions
let isConfigModalOpen = false;  // Prevent multiple simultaneous modal opens

async function configureWidget(widgetId) {
    console.log('[Dashboard] configureWidget called for:', widgetId, 'isConfigModalOpen:', isConfigModalOpen);

    // Prevent opening modal if already open
    if (isConfigModalOpen) {
        console.warn('[Dashboard] Modal already open, ignoring click');
        return;
    }

    isConfigModalOpen = true;

    const item = dashboard.widgets.get(widgetId);
    if (!item || !item.widget) {
        console.error('[Dashboard] Widget not found:', widgetId);
        isConfigModalOpen = false;
        return;
    }

    const widget = item.widget;
    console.log('[Dashboard] Configuring widget type:', widget.type);

    // Show modal immediately with loading state
    const modal = document.getElementById('widget-config-modal');
    const modalBody = document.getElementById('widget-config-body');
    modalBody.innerHTML = '<div style="text-align: center; padding: 40px; color: #00a8ff;">Loading configuration...</div>';
    modal.style.display = 'flex';
    modal.style.pointerEvents = 'auto';
    console.log('[Dashboard] Modal shown with loading state');

    // Fetch available blocks
    console.log('[Dashboard] Fetching blocks...');
    let blocks = [];
    try {
        blocks = await dashboard.fetchBlocks();
        console.log('[Dashboard] Fetched', blocks.length, 'blocks');
    } catch (error) {
        console.error('[Dashboard] ERROR fetching blocks:', error);
        blocks = [];
    }

    // Build configuration form
    console.log('[Dashboard] Building configuration form...');

    let html = `
        <div class="config-form">
            <div class="form-group">
                <label>Widget Title</label>
                <input type="text" id="config-title" value="${widget.config.title}" />
            </div>
    `;

    // Add type-specific configuration
    if (widget.type === 'button') {
        html += `
            <div class="form-group">
                <label>Button ID</label>
                <input type="text" id="config-button-id" value="${widget.config.buttonId || 'button_1'}" placeholder="button_1" />
                <small>Must match the button_id in your Web Button block configuration</small>
            </div>
            <div class="form-group">
                <label>Button Label</label>
                <input type="text" id="config-button-label" value="${widget.config.label || 'Press Me'}" />
            </div>
            <div class="form-group">
                <label>Mode</label>
                <select id="config-button-mode">
                    <option value="true" ${widget.config.momentary !== false ? 'selected' : ''}>Momentary (Press & Release)</option>
                    <option value="false" ${widget.config.momentary === false ? 'selected' : ''}>Toggle (Click to toggle)</option>
                </select>
            </div>
        `;
    } else if (widget.type === 'led') {
        html += `
            <div class="form-group">
                <label>LED ID</label>
                <input type="text" id="config-led-id" value="${widget.config.ledId || 'led_1'}" placeholder="led_1" />
                <small>Must match the led_id in your pipeline node configuration</small>
            </div>
            <div class="form-group">
                <label>LED Label</label>
                <input type="text" id="config-led-label" value="${widget.config.label || 'Status'}" />
            </div>
            <div class="form-group">
                <label>LED Color</label>
                <select id="config-led-color">
                    <option value="red" ${widget.config.color === 'red' ? 'selected' : ''}>Red</option>
                    <option value="green" ${widget.config.color === 'green' || !widget.config.color ? 'selected' : ''}>Green</option>
                    <option value="blue" ${widget.config.color === 'blue' ? 'selected' : ''}>Blue</option>
                    <option value="yellow" ${widget.config.color === 'yellow' ? 'selected' : ''}>Yellow</option>
                    <option value="white" ${widget.config.color === 'white' ? 'selected' : ''}>White</option>
                </select>
            </div>
            <div class="form-group">
                <label>Real-time Updates (SSE)</label>
                <small>Configure data source for instant updates instead of 500ms polling</small>
            </div>
            <div class="form-group">
                <label>Data Source Block</label>
                <select id="config-led-node" onchange="updateLEDPinOptions()">
                    <option value="">-- Polling Mode (500ms delay) --</option>
                    ${blocks.map(b => `<option value="${b.node_id}" ${widget.config.node_id == b.node_id ? 'selected' : ''}>${b.type} (ID: ${b.node_id})</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label>Output Pin</label>
                <select id="config-led-pin">
                    <option value="">-- Select Pin --</option>
                </select>
                <small>Select the block output pin that controls this LED</small>
            </div>
        `;
    } else if (widget.type === 'signalplot') {
        html += `
            <div class="form-group">
                <label>Data Source</label>
                <select id="config-signal-node" onchange="updateSignalPinOptions()">
                    <option value="">-- Select Block --</option>
                    ${blocks.map(b => `<option value="${b.node_id}" ${widget.config.node_id == b.node_id ? 'selected' : ''}>${b.type} (ID: ${b.node_id})</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label>Output Pin</label>
                <select id="config-signal-pin">
                    <option value="">-- Select Pin --</option>
                </select>
            </div>
            <div class="form-group">
                <label>Plot Label</label>
                <input type="text" id="config-plot-label" value="${widget.config.label || 'Signal'}" />
            </div>
            <div class="form-group">
                <label>Max Points</label>
                <input type="number" id="config-max-points" value="${widget.config.maxPoints || 100}" min="10" max="1000" />
                <small>Number of data points to display</small>
            </div>
            <div class="form-group">
                <label>Sample Rate (Downsampling)</label>
                <input type="number" id="config-sample-rate" value="${widget.config.sample_rate || 0}" min="0" />
                <small>0 = no downsampling, N = show every Nth sample</small>
            </div>
            <div class="form-group">
                <label>Line Color</label>
                <input type="color" id="config-plot-color" value="${widget.config.color || '#4BC0C0'}" />
            </div>
            <div class="form-group">
                <label>Y-Axis Min</label>
                <input type="number" step="0.1" id="config-y-min" value="${widget.config.y_min !== undefined ? widget.config.y_min : -1.5}" />
                <small>Minimum Y-axis value</small>
            </div>
            <div class="form-group">
                <label>Y-Axis Max</label>
                <input type="number" step="0.1" id="config-y-max" value="${widget.config.y_max !== undefined ? widget.config.y_max : 1.5}" />
                <small>Maximum Y-axis value</small>
            </div>
        `;
    } else if (widget.type === 'oscilloscope') {
        html += `
            <div class="form-group">
                <label>Data Source Block</label>
                <select id="config-scope-node" onchange="updateScopePinOptions()">
                    <option value="">-- Select Block --</option>
                    ${blocks.map(b => `<option value="${b.node_id}" ${widget.config.node_id == b.node_id ? 'selected' : ''}>${b.type} (ID: ${b.node_id})</option>`).join('')}
                </select>
                <small>Select any block with output signals</small>
            </div>
            <div class="form-group">
                <label>Channel 1 Pin (Red)</label>
                <select id="config-scope-ch1-pin">
                    <option value="">-- Select Pin --</option>
                </select>
            </div>
            <div class="form-group">
                <label>Channel 2 Pin (Green)</label>
                <select id="config-scope-ch2-pin">
                    <option value="">-- Select Pin --</option>
                </select>
            </div>
            <div class="form-group">
                <label>Channel 3 Pin (Orange)</label>
                <select id="config-scope-ch3-pin">
                    <option value="">-- Select Pin --</option>
                </select>
            </div>
            <div class="form-group">
                <label>Mode</label>
                <select id="config-scope-mode">
                    <option value="compact" ${widget.config.mode === 'compact' ? 'selected' : ''}>Compact (Dashboard)</option>
                    <option value="fullscreen" ${widget.config.mode === 'fullscreen' ? 'selected' : ''}>Fullscreen</option>
                </select>
                <small>Compact mode for dashboard, fullscreen for dedicated analysis</small>
            </div>
        `;
    } else if (widget.type === 'recorder') {
        html += `
            <div class="form-group">
                <label>Data Recorder Node</label>
                <select id="config-recorder-node">
                    <option value="">-- Select Data Recorder Block --</option>
                    ${blocks.map(b => `<option value="${b.node_id}" ${widget.config.recorderNodeId == b.node_id ? 'selected' : ''}>${b.type} (ID: ${b.node_id})</option>`).join('')}
                </select>
                <small>Select the Data Recorder block node from your pipeline</small>
            </div>
            <div class="form-group">
                <label>Recording Format</label>
                <select id="config-recorder-format">
                    <option value="cbor" ${widget.config.format === 'cbor' ? 'selected' : ''}>CBOR (Binary, Compact)</option>
                    <option value="csv" ${widget.config.format === 'csv' ? 'selected' : ''}>CSV (Human-readable)</option>
                    <option value="json" ${widget.config.format === 'json' ? 'selected' : ''}>JSON (Structured)</option>
                </select>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="config-recorder-auto-refresh" ${widget.config.autoRefresh !== false ? 'checked' : ''} />
                    Auto-refresh dataset list
                </label>
                <small>Automatically refresh the dataset list after stopping recording</small>
            </div>
        `;
    } else if (widget.type === 'gauge' || widget.type === 'text' || widget.type === 'chart') {
        html += `
            <div class="form-group">
                <label>Data Source</label>
                <select id="config-node" onchange="updatePinOptions()">
                    <option value="">-- Select Block --</option>
                    ${blocks.map(b => `<option value="${b.node_id}" ${widget.config.nodeId == b.node_id ? 'selected' : ''}>${b.type} (ID: ${b.node_id})</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label>Output Pin</label>
                <select id="config-pin">
                    <option value="">-- Select Pin --</option>
                </select>
            </div>
        `;

        if (widget.type === 'gauge') {
            html += `
                <div class="form-group">
                    <label>Min Value</label>
                    <input type="number" id="config-min" value="${widget.config.min || 0}" />
                </div>
                <div class="form-group">
                    <label>Max Value</label>
                    <input type="number" id="config-max" value="${widget.config.max || 100}" />
                </div>
                <div class="form-group">
                    <label>Unit</label>
                    <input type="text" id="config-unit" value="${widget.config.unit || ''}" />
                </div>
            `;
        }
    }

    html += '</div>';
    modalBody.innerHTML = html;

    // Store blocks data and current widget for later use
    modal.dataset.widgetId = widgetId;
    modal.dataset.blocks = JSON.stringify(blocks);

    // Update pin options if node already selected
    if (widget.config.nodeId) {
        updatePinOptions();
        if (widget.config.pin) {
            document.getElementById('config-pin').value = widget.config.pin;
        }
    }

    // Update signal plot pin options if node already selected
    if (widget.type === 'signalplot' && widget.config.node_id) {
        updateSignalPinOptions();
        if (widget.config.pin_name) {
            document.getElementById('config-signal-pin').value = widget.config.pin_name;
        }
    }

    // Update oscilloscope pin options if node already selected
    if (widget.type === 'oscilloscope' && widget.config.node_id) {
        updateScopePinOptions();
        if (widget.config.ch1_pin) {
            document.getElementById('config-scope-ch1-pin').value = widget.config.ch1_pin;
        }
        if (widget.config.ch2_pin) {
            document.getElementById('config-scope-ch2-pin').value = widget.config.ch2_pin;
        }
        if (widget.config.ch3_pin) {
            document.getElementById('config-scope-ch3-pin').value = widget.config.ch3_pin;
        }
    }

    // Update LED pin options if node already selected
    if (widget.type === 'led' && widget.config.node_id) {
        updateLEDPinOptions();
        if (widget.config.pin_name) {
            document.getElementById('config-led-pin').value = widget.config.pin_name;
        }
    }

    console.log('[Dashboard] About to show modal...');
    modal.style.display = 'flex';
    modal.style.pointerEvents = 'auto';  // Enable clicks on modal
    console.log('[Dashboard] Modal opened, display:', modal.style.display, 'pointer-events:', modal.style.pointerEvents);
    console.log('[Dashboard] Modal visibility check - offsetWidth:', modal.offsetWidth, 'offsetHeight:', modal.offsetHeight);
}

function updatePinOptions() {
    const modal = document.getElementById('widget-config-modal');
    const blocks = JSON.parse(modal.dataset.blocks || '[]');
    const nodeId = parseInt(document.getElementById('config-node').value);
    const pinSelect = document.getElementById('config-pin');

    pinSelect.innerHTML = '<option value="">-- Select Pin --</option>';

    if (nodeId) {
        const block = blocks.find(b => b.node_id === nodeId);
        if (block && block.output_pins) {
            block.output_pins.forEach(pin => {
                pinSelect.innerHTML += `<option value="${pin}">${pin}</option>`;
            });
        }
    }
}

function updateSignalPinOptions() {
    const modal = document.getElementById('widget-config-modal');
    const blocks = JSON.parse(modal.dataset.blocks || '[]');
    const nodeId = parseInt(document.getElementById('config-signal-node').value);
    const pinSelect = document.getElementById('config-signal-pin');

    pinSelect.innerHTML = '<option value="">-- Select Pin --</option>';

    if (nodeId) {
        const block = blocks.find(b => b.node_id === nodeId);
        if (block && block.output_pins) {
            block.output_pins.forEach(pin => {
                pinSelect.innerHTML += `<option value="${pin}">${pin}</option>`;
            });
        }
    }
}

function updateScopePinOptions() {
    const modal = document.getElementById('widget-config-modal');
    const blocks = JSON.parse(modal.dataset.blocks || '[]');
    const nodeId = parseInt(document.getElementById('config-scope-node').value);
    const ch1Select = document.getElementById('config-scope-ch1-pin');
    const ch2Select = document.getElementById('config-scope-ch2-pin');
    const ch3Select = document.getElementById('config-scope-ch3-pin');

    // Clear all dropdowns
    ch1Select.innerHTML = '<option value="">-- Select Pin --</option>';
    ch2Select.innerHTML = '<option value="">-- Select Pin --</option>';
    ch3Select.innerHTML = '<option value="">-- Select Pin --</option>';

    if (nodeId) {
        const block = blocks.find(b => b.node_id === nodeId);
        if (block && block.output_pins) {
            block.output_pins.forEach(pin => {
                ch1Select.innerHTML += `<option value="${pin}">${pin}</option>`;
                ch2Select.innerHTML += `<option value="${pin}">${pin}</option>`;
                ch3Select.innerHTML += `<option value="${pin}">${pin}</option>`;
            });
        }
    }
}

function updateLEDPinOptions() {
    const modal = document.getElementById('widget-config-modal');
    const blocks = JSON.parse(modal.dataset.blocks || '[]');
    const nodeId = parseInt(document.getElementById('config-led-node').value);
    const pinSelect = document.getElementById('config-led-pin');

    pinSelect.innerHTML = '<option value="">-- Select Pin --</option>';

    if (nodeId) {
        const block = blocks.find(b => b.node_id === nodeId);
        if (block && block.output_pins) {
            block.output_pins.forEach(pin => {
                pinSelect.innerHTML += `<option value="${pin}">${pin}</option>`;
            });
        }
    }
}

function closeConfigModal() {
    console.log('[Dashboard] Closing config modal');
    const modal = document.getElementById('widget-config-modal');
    modal.style.display = 'none';
    modal.style.pointerEvents = 'none';  // Ensure it doesn't block clicks

    // CRITICAL: Also check for any stray fullscreen overlays that might be blocking
    const overlays = document.querySelectorAll('[id^="oscilloscope-fullscreen-"]');
    if (overlays.length > 0) {
        console.warn('[Dashboard] Found', overlays.length, 'fullscreen overlays, removing...');
        overlays.forEach(overlay => overlay.remove());
    }

    // Reset the modal open flag
    isConfigModalOpen = false;

    console.log('[Dashboard] Modal closed, display:', modal.style.display, 'pointer-events:', modal.style.pointerEvents);
}

function saveWidgetConfig() {
    const modal = document.getElementById('widget-config-modal');
    const widgetId = modal.dataset.widgetId;
    const item = dashboard.widgets.get(widgetId);

    if (!item || !item.widget) {
        closeConfigModal();
        return;
    }

    const widget = item.widget;

    // Update basic config
    widget.config.title = document.getElementById('config-title').value;

    // Update data source config
    const nodeSelect = document.getElementById('config-node');
    const pinSelect = document.getElementById('config-pin');

    if (nodeSelect) {
        widget.config.nodeId = parseInt(nodeSelect.value) || null;
        widget.config.pin = pinSelect.value || null;
    }

    // Update type-specific config
    if (widget.type === 'button') {
        widget.config.buttonId = document.getElementById('config-button-id').value;
        widget.config.label = document.getElementById('config-button-label').value;
        widget.config.momentary = document.getElementById('config-button-mode').value === 'true';
    } else if (widget.type === 'led') {
        widget.config.ledId = document.getElementById('config-led-id').value;
        widget.config.label = document.getElementById('config-led-label').value;
        widget.config.color = document.getElementById('config-led-color').value;

        // SSE configuration for real-time updates
        const ledNodeSelect = document.getElementById('config-led-node');
        const ledPinSelect = document.getElementById('config-led-pin');
        widget.config.node_id = ledNodeSelect.value || null;
        widget.config.pin_name = ledPinSelect.value || null;
    } else if (widget.type === 'signalplot') {
        const signalNodeSelect = document.getElementById('config-signal-node');
        const signalPinSelect = document.getElementById('config-signal-pin');

        widget.config.node_id = signalNodeSelect.value || null;
        widget.config.pin_name = signalPinSelect.value || null;
        widget.config.label = document.getElementById('config-plot-label').value;
        widget.config.maxPoints = parseInt(document.getElementById('config-max-points').value) || 100;
        widget.config.sample_rate = parseInt(document.getElementById('config-sample-rate').value) || 0;
        widget.config.color = document.getElementById('config-plot-color').value;
        widget.config.y_min = parseFloat(document.getElementById('config-y-min').value);
        widget.config.y_max = parseFloat(document.getElementById('config-y-max').value);
    } else if (widget.type === 'oscilloscope') {
        widget.config.node_id = document.getElementById('config-scope-node').value || null;
        widget.config.ch1_pin = document.getElementById('config-scope-ch1-pin').value || '';
        widget.config.ch2_pin = document.getElementById('config-scope-ch2-pin').value || '';
        widget.config.ch3_pin = document.getElementById('config-scope-ch3-pin').value || '';
        widget.config.mode = document.getElementById('config-scope-mode').value || 'compact';
    } else if (widget.type === 'recorder') {
        const recorderNodeSelect = document.getElementById('config-recorder-node');
        widget.config.recorderNodeId = parseInt(recorderNodeSelect.value) || 1;
        widget.config.format = document.getElementById('config-recorder-format').value || 'cbor';
        widget.config.autoRefresh = document.getElementById('config-recorder-auto-refresh').checked;
    } else if (widget.type === 'gauge') {
        widget.config.min = parseFloat(document.getElementById('config-min').value) || 0;
        widget.config.max = parseFloat(document.getElementById('config-max').value) || 100;
        widget.config.unit = document.getElementById('config-unit').value || '';
    }

    // Re-render widget with new config
    if (widget.element) {
        // For widgets with WebSocket connections, destroy old connection before re-rendering
        if ((widget.type === 'signalplot' || widget.type === 'led' || widget.type === 'oscilloscope' || widget.type === 'button' || widget.type === 'recorder') && typeof widget.destroy === 'function') {
            widget.destroy();
        }

        widget.render(widget.element);

        // Reinitialize after rendering
        if ((widget.type === 'signalplot' || widget.type === 'led' || widget.type === 'oscilloscope' || widget.type === 'button' || widget.type === 'recorder') && typeof widget.afterRender === 'function') {
            widget.afterRender();
        }
    }

    closeConfigModal();
}

function removeWidget(widgetId) {
    if (confirm('Remove this widget?')) {
        dashboard.removeWidget(widgetId);
    }
}

// Close modal when clicking outside
document.addEventListener('click', (e) => {
    const modal = document.getElementById('widget-config-modal');
    if (e.target === modal) {
        closeConfigModal();
    }
});

document.querySelector('.close-modal')?.addEventListener('click', closeConfigModal);

// Initialize dashboard
let dashboard = null;

function initializeDashboard() {
    dashboard = new DashboardManager();
    dashboard.initialize();
}

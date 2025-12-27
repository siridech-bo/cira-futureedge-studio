// Dashboard Manager
class DashboardManager {
    constructor() {
        this.grid = null;
        this.widgets = new Map();
        this.isEditMode = false;
        this.metricsInterval = null;
        this.widgetIdCounter = 0;
    }

    initialize() {
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
        this.startMetricsPolling();

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

        // Poll every 1 second
        this.metricsInterval = setInterval(() => {
            this.fetchMetrics();
        }, 1000);
    }

    async fetchBlocks() {
        try {
            const response = await fetch('/api/blocks', {
                headers: authManager.getHeaders()
            });

            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Failed to fetch blocks:', error);
        }
        return [];
    }

    async fetchBlockData() {
        try {
            const response = await fetch('/api/blocks/data', {
                headers: authManager.getHeaders()
            });

            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Failed to fetch block data:', error);
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
async function configureWidget(widgetId) {
    const item = dashboard.widgets.get(widgetId);
    if (!item || !item.widget) return;

    const widget = item.widget;

    // Fetch available blocks
    const blocks = await dashboard.fetchBlocks();

    // Build configuration form
    const modal = document.getElementById('widget-config-modal');
    const modalBody = document.getElementById('widget-config-body');

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
                <small>Must match the button_id in your pipeline node configuration</small>
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

    modal.style.display = 'flex';
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
    document.getElementById('widget-config-modal').style.display = 'none';
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
    } else if (widget.type === 'gauge') {
        widget.config.min = parseFloat(document.getElementById('config-min').value) || 0;
        widget.config.max = parseFloat(document.getElementById('config-max').value) || 100;
        widget.config.unit = document.getElementById('config-unit').value || '';
    }

    // Re-render widget with new config
    if (widget.element) {
        // For widgets with SSE connections, destroy old connection before re-rendering
        if ((widget.type === 'signalplot' || widget.type === 'led') && typeof widget.destroy === 'function') {
            widget.destroy();
        }

        widget.render(widget.element);

        // Reinitialize after rendering
        if ((widget.type === 'signalplot' || widget.type === 'led') && typeof widget.afterRender === 'function') {
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

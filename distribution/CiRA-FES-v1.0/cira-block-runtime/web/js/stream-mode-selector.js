/**
 * Stream Mode Selector UI
 * Allows user to switch between SSE and WebSocket modes
 */

class StreamModeSelector {
    constructor() {
        this.createUI();
    }

    createUI() {
        // Create floating mode selector
        const selector = document.createElement('div');
        selector.id = 'stream-mode-selector';
        selector.innerHTML = `
            <div class="mode-selector-header">
                <span>📡 Stream Mode</span>
                <button id="mode-selector-toggle" class="toggle-btn">▼</button>
            </div>
            <div class="mode-selector-body" id="mode-selector-body" style="display: none;">
                <div class="mode-option">
                    <input type="radio" id="mode-auto" name="stream-mode" value="auto" checked>
                    <label for="mode-auto">
                        <strong>Auto</strong>
                        <small>Use WebSocket if available, fallback to SSE</small>
                    </label>
                </div>
                <div class="mode-option">
                    <input type="radio" id="mode-websocket" name="stream-mode" value="websocket">
                    <label for="mode-websocket">
                        <strong>WebSocket</strong>
                        <small>High performance binary streaming (NEW)</small>
                    </label>
                </div>
                <div class="mode-option">
                    <input type="radio" id="mode-sse" name="stream-mode" value="sse">
                    <label for="mode-sse">
                        <strong>SSE</strong>
                        <small>Server-Sent Events (Legacy, stable)</small>
                    </label>
                </div>
                <button id="mode-apply" class="apply-btn">Apply & Reload</button>
                <div class="mode-status" id="mode-status"></div>
            </div>
        `;

        // Add CSS
        const style = document.createElement('style');
        style.textContent = `
            #stream-mode-selector {
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: rgba(10, 14, 39, 0.95);
                border: 2px solid #2a5a7a;
                border-radius: 8px;
                padding: 10px;
                min-width: 300px;
                z-index: 10000;
                font-family: 'Roboto', sans-serif;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
            }

            .mode-selector-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                color: #00a8ff;
                font-weight: bold;
                cursor: pointer;
                padding: 5px;
            }

            .toggle-btn {
                background: none;
                border: none;
                color: #00a8ff;
                font-size: 14px;
                cursor: pointer;
                padding: 0;
                width: 24px;
            }

            .mode-selector-body {
                margin-top: 10px;
                padding-top: 10px;
                border-top: 1px solid #2a5a7a;
            }

            .mode-option {
                margin: 10px 0;
                display: flex;
                align-items: flex-start;
            }

            .mode-option input[type="radio"] {
                margin: 5px 10px 0 0;
            }

            .mode-option label {
                color: #e0e6ed;
                cursor: pointer;
                flex: 1;
            }

            .mode-option label strong {
                display: block;
                color: #00a8ff;
                margin-bottom: 2px;
            }

            .mode-option label small {
                display: block;
                color: #8a9ab0;
                font-size: 11px;
            }

            .apply-btn {
                background: #00a8ff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                cursor: pointer;
                width: 100%;
                margin-top: 10px;
                font-weight: bold;
            }

            .apply-btn:hover {
                background: #0088cc;
            }

            .mode-status {
                margin-top: 10px;
                padding: 8px;
                border-radius: 4px;
                font-size: 12px;
                text-align: center;
            }

            .mode-status.info {
                background: rgba(0, 168, 255, 0.2);
                color: #00a8ff;
            }

            .mode-status.success {
                background: rgba(0, 255, 136, 0.2);
                color: #00ff88;
            }
        `;

        document.head.appendChild(style);
        document.body.appendChild(selector);

        // Add event listeners
        this.attachEventListeners();

        // Load saved preference
        this.loadSavedMode();

        // Show current status
        this.updateStatus();
    }

    attachEventListeners() {
        // Toggle expand/collapse
        document.getElementById('mode-selector-toggle').addEventListener('click', () => {
            const body = document.getElementById('mode-selector-body');
            const toggle = document.getElementById('mode-selector-toggle');
            if (body.style.display === 'none') {
                body.style.display = 'block';
                toggle.textContent = '▲';
            } else {
                body.style.display = 'none';
                toggle.textContent = '▼';
            }
        });

        // Apply button
        document.getElementById('mode-apply').addEventListener('click', () => {
            const selected = document.querySelector('input[name="stream-mode"]:checked').value;
            this.applyMode(selected);
        });
    }

    loadSavedMode() {
        const saved = localStorage.getItem('oscilloscope_stream_mode') || 'auto';
        document.querySelector(`input[value="${saved}"]`).checked = true;
        OscilloscopeStreamConfig.mode = saved;
    }

    applyMode(mode) {
        // Save to localStorage
        localStorage.setItem('oscilloscope_stream_mode', mode);

        // Update config
        OscilloscopeStreamConfig.mode = mode;

        // Show confirmation
        const status = document.getElementById('mode-status');
        status.className = 'mode-status success';
        status.textContent = `✓ Mode changed to: ${mode.toUpperCase()}. Reloading...`;

        // Reload page after 1 second
        setTimeout(() => {
            window.location.reload();
        }, 1000);
    }

    updateStatus() {
        const status = document.getElementById('mode-status');
        const currentMode = OscilloscopeStreamConfig.selectMode();

        status.className = 'mode-status info';
        status.innerHTML = `
            <strong>Active Mode:</strong> ${currentMode.toUpperCase()}<br>
            <small>WebSocket: ${OscilloscopeStreamConfig.detectWebSocketSupport() ? '✓ Available' : '✗ Not Available'}</small>
        `;
    }
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new StreamModeSelector();
    });
} else {
    new StreamModeSelector();
}

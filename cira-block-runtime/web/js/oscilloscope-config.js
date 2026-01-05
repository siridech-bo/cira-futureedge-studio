/**
 * Oscilloscope Streaming Configuration
 *
 * Choose between SSE (existing) and WebSocket (new)
 */

const OscilloscopeStreamConfig = {
    // Streaming mode: 'sse', 'websocket', or 'auto'
    // Use WebSocket only (Node-RED architecture)
    mode: 'websocket',  // Force WebSocket mode - SSE is deprecated

    // Ports
    http_port: 8083,      // HTTP server port
    websocket_port: 8084, // WebSocket server port

    // Performance settings
    targetFPS: 30,              // Target frame rate for rendering
    downsampleTarget: 1000,     // Number of samples to request from server

    // Feature detection
    detectWebSocketSupport() {
        return 'WebSocket' in window && typeof WebSocket === 'function';
    },

    // Check if MessagePack is available (optional, for binary protocol)
    detectMessagePackSupport() {
        return typeof msgpack !== 'undefined';
    },

    // Auto-select best mode
    selectMode() {
        if (this.mode === 'sse') {
            return 'sse';
        }

        if (this.mode === 'websocket') {
            if (this.detectWebSocketSupport()) {
                return 'websocket';
            } else {
                console.warn('[Oscilloscope] WebSocket not supported, falling back to SSE');
                return 'sse';
            }
        }

        // Auto mode: prefer WebSocket if available
        if (this.mode === 'auto') {
            if (this.detectWebSocketSupport()) {
                console.log('[Oscilloscope] Auto-selected WebSocket mode (high performance)');
                return 'websocket';
            } else {
                console.log('[Oscilloscope] Auto-selected SSE mode (fallback)');
                return 'sse';
            }
        }

        return 'sse';  // Default fallback
    },

    // Get WebSocket URL
    getWebSocketURL() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.hostname;
        return `${protocol}//${host}:${this.websocket_port}`;
    },

    // Get HTTP URL base
    getHTTPURL() {
        const protocol = window.location.protocol;
        const host = window.location.hostname;
        return `${protocol}//${host}:${this.http_port}`;
    },

    // Display current configuration
    printConfig() {
        console.log('=== Oscilloscope Stream Configuration ===');
        console.log('Mode:', this.selectMode());
        console.log('WebSocket Support:', this.detectWebSocketSupport());
        console.log('MessagePack Support:', this.detectMessagePackSupport());
        console.log('HTTP URL:', this.getHTTPURL());
        console.log('WebSocket URL:', this.getWebSocketURL());
        console.log('==========================================');
    }
};

// Print configuration on load
OscilloscopeStreamConfig.printConfig();

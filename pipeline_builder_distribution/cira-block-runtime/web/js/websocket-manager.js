/**
 * Centralized WebSocket Manager (Node-RED Architecture)
 *
 * Manages a single WebSocket connection for all widgets
 * - Subscribe/unsubscribe to signals
 * - Multiplex data to widgets
 * - Auto-reconnect with exponential backoff
 * - Replace SSE entirely
 */

class WebSocketManager {
    constructor() {
        this.ws = null;
        this.subscriptions = new Map(); // widget_id → {nodeId, pinName, callback}
        this.reconnectDelay = 1000;
        this.maxReconnectDelay = 30000;
        this.reconnectTimer = null;
        this.isConnecting = false;
        this.messagePackSupported = typeof msgpack !== 'undefined';

        console.log('[WebSocketManager] MessagePack support:', this.messagePackSupported);
    }

    /**
     * Initialize WebSocket connection
     */
    connect() {
        if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
            return;
        }

        this.isConnecting = true;

        // WebSocket server runs on HTTP port + 1
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const httpPort = parseInt(window.location.port) || 8080;
        const wsPort = httpPort + 1;
        const wsUrl = `${protocol}//${window.location.hostname}:${wsPort}`;

        console.log('[WebSocketManager] Connecting to:', wsUrl);

        try {
            this.ws = new WebSocket(wsUrl);
            this.ws.binaryType = 'arraybuffer';

            this.ws.onopen = () => {
                console.log('[WebSocketManager] Connected successfully');
                this.isConnecting = false;
                this.reconnectDelay = 1000; // Reset backoff
                this.resubscribeAll();
            };

            this.ws.onmessage = (event) => {
                this.handleMessage(event);
            };

            this.ws.onerror = (error) => {
                console.error('[WebSocketManager] Error:', error);
                this.isConnecting = false;
            };

            this.ws.onclose = () => {
                console.log('[WebSocketManager] Disconnected');
                this.isConnecting = false;
                this.scheduleReconnect();
            };

        } catch (error) {
            console.error('[WebSocketManager] Failed to create WebSocket:', error);
            this.isConnecting = false;
            this.scheduleReconnect();
        }
    }

    /**
     * Schedule reconnection with exponential backoff
     */
    scheduleReconnect() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
        }

        console.log(`[WebSocketManager] Reconnecting in ${this.reconnectDelay}ms...`);

        this.reconnectTimer = setTimeout(() => {
            this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxReconnectDelay);
            this.connect();
        }, this.reconnectDelay);
    }

    /**
     * Subscribe widget to a signal (nodeId:pinName)
     *
     * @param {string} widgetId - Unique widget identifier
     * @param {number} nodeId - Block node ID
     * @param {string} pinName - Output pin name
     * @param {function} callback - Callback(value, timestamp)
     */
    subscribe(widgetId, nodeId, pinName, callback) {
        console.log(`[WebSocketManager] Subscribe: widget=${widgetId}, signal=${nodeId}:${pinName}`);

        // Store subscription
        this.subscriptions.set(widgetId, { nodeId, pinName, callback });

        // Send subscribe command if connected
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            const signalId = `${nodeId}:${pinName}`;
            const subscribeMsg = JSON.stringify({
                command: 'subscribe',
                signal_id: signalId
            });

            this.ws.send(subscribeMsg);
            console.log(`[WebSocketManager] Sent subscribe command for ${signalId}`);
        } else {
            console.warn('[WebSocketManager] Not connected yet, subscription will be sent on connect');
        }
    }

    /**
     * Unsubscribe widget from signal
     */
    unsubscribe(widgetId) {
        const sub = this.subscriptions.get(widgetId);
        if (!sub) return;

        console.log(`[WebSocketManager] Unsubscribe: widget=${widgetId}, signal=${sub.nodeId}:${sub.pinName}`);

        // Send unsubscribe command if connected
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            const signalId = `${sub.nodeId}:${sub.pinName}`;
            const unsubscribeMsg = JSON.stringify({
                command: 'unsubscribe',
                signal_id: signalId
            });
            this.ws.send(unsubscribeMsg);
        }

        // Remove subscription
        this.subscriptions.delete(widgetId);
    }

    /**
     * Resubscribe all widgets after reconnection
     */
    resubscribeAll() {
        console.log(`[WebSocketManager] Resubscribing ${this.subscriptions.size} widgets`);

        for (const [widgetId, sub] of this.subscriptions.entries()) {
            const signalId = `${sub.nodeId}:${sub.pinName}`;
            const subscribeMsg = JSON.stringify({
                command: 'subscribe',
                signal_id: signalId
            });
            this.ws.send(subscribeMsg);
        }
    }

    /**
     * Handle incoming WebSocket message
     */
    handleMessage(event) {
        try {
            if (event.data instanceof ArrayBuffer) {
                // Binary MessagePack data
                this.handleBinaryMessage(event.data);
            } else {
                // JSON text data (for commands/status)
                const data = JSON.parse(event.data);
                this.handleJSONMessage(data);
            }
        } catch (error) {
            console.error('[WebSocketManager] Failed to parse message:', error);
        }
    }

    /**
     * Handle MessagePack binary message
     */
    handleBinaryMessage(buffer) {
        if (!this.messagePackSupported) {
            console.warn('[WebSocketManager] MessagePack not available, cannot decode binary message');
            return;
        }

        try {
            const data = msgpack.decode(new Uint8Array(buffer));

            // MessagePack format: {type: 1, signal_id: "2:channel_0", samples: [...], ...}
            if (data.type === 1) { // SignalData
                const signalId = data.signal_id;
                const [nodeIdStr, pinName] = signalId.split(':');
                const nodeId = parseInt(nodeIdStr);

                // Find subscribed widgets
                for (const [widgetId, sub] of this.subscriptions.entries()) {
                    if (sub.nodeId === nodeId && sub.pinName === pinName) {
                        // For oscilloscope: pass array of samples
                        if (data.samples && Array.isArray(data.samples)) {
                            sub.callback(data.samples, data.timestamp);
                        } else {
                            // For single value (LED, gauge, etc)
                            const value = data.avg !== undefined ? data.avg :
                                         (data.samples && data.samples.length > 0 ? data.samples[0] : 0);
                            sub.callback(value, data.timestamp);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('[WebSocketManager] Failed to decode MessagePack:', error);
        }
    }

    /**
     * Handle JSON message
     */
    handleJSONMessage(data) {
        console.log('[WebSocketManager] Received JSON message:', data);

        // Handle signal data (type: 1 for numbers, type: 2 for strings)
        if ((data.type === 1 || data.type === 2) && data.signal_id) {
            // Deliver to all widgets subscribed to this signal
            for (const [widgetId, subscription] of this.subscriptions.entries()) {
                const subscriptionSignalId = `${subscription.nodeId}:${subscription.pinName}`;
                if (subscriptionSignalId === data.signal_id) {
                    console.log(`[WebSocketManager] Delivering to widget ${widgetId}: value=${data.value} (type=${data.type})`);
                    subscription.callback(data.value, data.timestamp);
                }
            }
        } else if (data.type === 'status') {
            console.log('[WebSocketManager] Status:', data.message);
        } else if (data.type === 'error') {
            console.error('[WebSocketManager] Server error:', data.message);
        }
    }

    /**
     * Disconnect WebSocket
     */
    disconnect() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        this.subscriptions.clear();
    }

    /**
     * Check if connected
     */
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }

    /**
     * Get connection status
     */
    getStatus() {
        if (!this.ws) return 'disconnected';

        switch (this.ws.readyState) {
            case WebSocket.CONNECTING: return 'connecting';
            case WebSocket.OPEN: return 'connected';
            case WebSocket.CLOSING: return 'closing';
            case WebSocket.CLOSED: return 'disconnected';
            default: return 'unknown';
        }
    }
}

// Global WebSocket manager instance (like Node-RED)
const wsManager = new WebSocketManager();

// Auto-connect on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('[WebSocketManager] Auto-connecting on page load');
    wsManager.connect();
});

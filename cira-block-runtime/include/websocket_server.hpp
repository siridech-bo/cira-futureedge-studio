#pragma once

#include <string>
#include <functional>
#include <memory>
#include <vector>
#include <unordered_map>
#include <mutex>
#include "signal_aggregator.hpp"

namespace CiraBlockRuntime {

/**
 * WebSocket message types (MessagePack encoded)
 */
enum class WSMessageType : uint8_t {
    SignalData = 1,      // Oscilloscope waveform data
    ImageFrame = 2,      // JPEG/PNG image
    VideoFrame = 3,      // H.264 video frame
    Command = 4,         // Client command
    StatusUpdate = 5     // System status
};

/**
 * WebSocket connection handle
 */
using WSConnectionId = uint64_t;

/**
 * WebSocket message callback
 */
using WSMessageCallback = std::function<void(WSConnectionId conn_id, const std::vector<uint8_t>& data)>;

/**
 * WebSocket server interface
 *
 * This is a lightweight wrapper that can use:
 * - uWebSockets (when available, for max performance)
 * - Fallback implementation using existing http library
 */
class WebSocketServer {
public:
    WebSocketServer(int port, SignalAggregator* aggregator);
    ~WebSocketServer();

    /**
     * Start WebSocket server
     */
    bool Start();

    /**
     * Stop WebSocket server
     */
    void Stop();

    /**
     * Check if server is running
     */
    bool IsRunning() const { return running_; }

    /**
     * Broadcast waveform chunk to all subscribers
     */
    void BroadcastWaveform(const WaveformChunk& chunk);

    /**
     * Broadcast image frame (for future camera support)
     */
    void BroadcastImage(const std::string& node_id,
                       const std::vector<uint8_t>& jpeg_data);

    /**
     * Send message to specific connection
     */
    void SendToConnection(WSConnectionId conn_id,
                         const std::vector<uint8_t>& data);

    /**
     * Register message callback
     */
    void SetMessageCallback(WSMessageCallback callback);

    /**
     * Get number of active connections
     */
    size_t GetConnectionCount() const;

private:
    struct Connection {
        WSConnectionId id;
        std::vector<std::string> subscribed_signals;  // Format: "node_id:pin_name"
        bool active;
    };

    int port_;
    bool running_;
    SignalAggregator* aggregator_;
    WSMessageCallback message_callback_;

    mutable std::mutex connections_mutex_;
    std::unordered_map<WSConnectionId, Connection> connections_;

    // Internal implementation (will use uWebSockets when available)
    class Impl;
    std::unique_ptr<Impl> impl_;

    void OnClientConnected(WSConnectionId conn_id);
    void OnClientDisconnected(WSConnectionId conn_id);
    void OnClientMessage(WSConnectionId conn_id, const std::vector<uint8_t>& data);

    std::vector<uint8_t> EncodeWaveformMessage(const WaveformChunk& chunk);
    std::vector<uint8_t> EncodeImageMessage(const std::string& node_id,
                                           const std::vector<uint8_t>& jpeg_data);
};

/**
 * MessagePack encoding/decoding utilities
 */
class MessagePackUtil {
public:
    /**
     * Encode waveform chunk to MessagePack binary
     *
     * Format:
     * {
     *   "type": 1,                    // WSMessageType::SignalData
     *   "signal_id": "node_2:channel_0",
     *   "timestamp": 1234567890,
     *   "samples": [1.2, 3.4, ...],
     *   "count": 500,
     *   "min": -1.5,
     *   "max": 1.5,
     *   "avg": 0.2
     * }
     */
    static std::vector<uint8_t> EncodeWaveform(const WaveformChunk& chunk);

    /**
     * Encode image frame to MessagePack binary
     *
     * Format:
     * {
     *   "type": 2,                    // WSMessageType::ImageFrame
     *   "node_id": "camera_1",
     *   "timestamp": 1234567890,
     *   "format": "jpeg",
     *   "data": <binary>
     * }
     */
    static std::vector<uint8_t> EncodeImage(
        const std::string& node_id,
        const std::vector<uint8_t>& jpeg_data
    );

    /**
     * Decode client command message
     *
     * Format:
     * {
     *   "type": 4,                    // WSMessageType::Command
     *   "command": "subscribe",
     *   "signal_id": "node_2:channel_0"
     * }
     */
    struct Command {
        std::string command;          // "subscribe", "unsubscribe", "get_waveform"
        std::string signal_id;
        int target_samples = 1000;
    };

    static Command DecodeCommand(const std::vector<uint8_t>& data);
};

} // namespace CiraBlockRuntime

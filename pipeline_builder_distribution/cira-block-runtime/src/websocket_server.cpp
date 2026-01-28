#include "websocket_server.hpp"
#include <iostream>
#include <sstream>
#include <cstring>
#include <algorithm>

#ifdef HAS_IXWEBSOCKET
#include <ixwebsocket/IXWebSocketServer.h>
#endif

// Check if msgpack is available
#ifdef __has_include
#  if __has_include(<msgpack.hpp>)
#    include <msgpack.hpp>
#    define HAS_MSGPACK 1
#  endif
#endif

namespace CiraBlockRuntime {

//
// MessagePack Utilities
//

std::vector<uint8_t> MessagePackUtil::EncodeWaveform(const WaveformChunk& chunk) {
#ifdef HAS_MSGPACK
    // Use MessagePack library if available
    msgpack::sbuffer buffer;
    msgpack::packer<msgpack::sbuffer> pk(&buffer);

    pk.pack_map(8);  // 8 key-value pairs

    pk.pack(std::string("type"));
    pk.pack(static_cast<uint8_t>(WSMessageType::SignalData));

    pk.pack(std::string("signal_id"));
    pk.pack(chunk.signal_id);

    pk.pack(std::string("timestamp"));
    pk.pack(chunk.timestamp);

    pk.pack(std::string("samples"));
    pk.pack(chunk.samples);

    pk.pack(std::string("count"));
    pk.pack(chunk.original_sample_count);

    pk.pack(std::string("min"));
    pk.pack(chunk.min_value);

    pk.pack(std::string("max"));
    pk.pack(chunk.max_value);

    pk.pack(std::string("avg"));
    pk.pack(chunk.avg_value);

    return std::vector<uint8_t>(buffer.data(), buffer.data() + buffer.size());
#else
    // Fallback: Use simple binary format
    // Format: [type:1][signal_id_len:2][signal_id][timestamp:8][num_samples:4][samples...]
    std::vector<uint8_t> data;

    // Type
    data.push_back(static_cast<uint8_t>(WSMessageType::SignalData));

    // Signal ID length and string
    uint16_t id_len = chunk.signal_id.length();
    data.push_back((id_len >> 8) & 0xFF);
    data.push_back(id_len & 0xFF);
    data.insert(data.end(), chunk.signal_id.begin(), chunk.signal_id.end());

    // Timestamp (8 bytes, little-endian)
    for (int i = 0; i < 8; ++i) {
        data.push_back((chunk.timestamp >> (i * 8)) & 0xFF);
    }

    // Number of samples (4 bytes)
    uint32_t num_samples = chunk.samples.size();
    for (int i = 0; i < 4; ++i) {
        data.push_back((num_samples >> (i * 8)) & 0xFF);
    }

    // Samples (4 bytes each, float as bytes)
    for (float sample : chunk.samples) {
        uint32_t sample_bits;
        std::memcpy(&sample_bits, &sample, sizeof(float));
        for (int i = 0; i < 4; ++i) {
            data.push_back((sample_bits >> (i * 8)) & 0xFF);
        }
    }

    return data;
#endif
}

std::vector<uint8_t> MessagePackUtil::EncodeImage(
    const std::string& node_id,
    const std::vector<uint8_t>& jpeg_data
) {
#ifdef HAS_MSGPACK
    msgpack::sbuffer buffer;
    msgpack::packer<msgpack::sbuffer> pk(&buffer);

    pk.pack_map(4);

    pk.pack(std::string("type"));
    pk.pack(static_cast<uint8_t>(WSMessageType::ImageFrame));

    pk.pack(std::string("node_id"));
    pk.pack(node_id);

    pk.pack(std::string("format"));
    pk.pack(std::string("jpeg"));

    pk.pack(std::string("data"));
    pk.pack(jpeg_data);

    return std::vector<uint8_t>(buffer.data(), buffer.data() + buffer.size());
#else
    // Simple binary format for images
    std::vector<uint8_t> data;
    data.push_back(static_cast<uint8_t>(WSMessageType::ImageFrame));

    // Node ID
    uint16_t id_len = node_id.length();
    data.push_back((id_len >> 8) & 0xFF);
    data.push_back(id_len & 0xFF);
    data.insert(data.end(), node_id.begin(), node_id.end());

    // Image data length
    uint32_t img_len = jpeg_data.size();
    for (int i = 0; i < 4; ++i) {
        data.push_back((img_len >> (i * 8)) & 0xFF);
    }

    // Image data
    data.insert(data.end(), jpeg_data.begin(), jpeg_data.end());

    return data;
#endif
}

MessagePackUtil::Command MessagePackUtil::DecodeCommand(const std::vector<uint8_t>& data) {
    Command cmd;

#ifdef HAS_MSGPACK
    try {
        msgpack::object_handle oh = msgpack::unpack(
            reinterpret_cast<const char*>(data.data()),
            data.size()
        );
        msgpack::object obj = oh.get();

        if (obj.type == msgpack::type::MAP) {
            for (size_t i = 0; i < obj.via.map.size; ++i) {
                std::string key = obj.via.map.ptr[i].key.as<std::string>();
                if (key == "command") {
                    cmd.command = obj.via.map.ptr[i].val.as<std::string>();
                } else if (key == "signal_id") {
                    cmd.signal_id = obj.via.map.ptr[i].val.as<std::string>();
                } else if (key == "target_samples") {
                    cmd.target_samples = obj.via.map.ptr[i].val.as<int>();
                }
            }
        }
    } catch (const std::exception& e) {
        std::cerr << "[MessagePack] Decode error: " << e.what() << std::endl;
    }
#else
    // Simple fallback parsing (JSON-like text)
    std::string text(data.begin(), data.end());
    // Very simple parser - production code should use JSON library
    size_t cmd_pos = text.find("\"command\":");
    if (cmd_pos != std::string::npos) {
        size_t start = text.find("\"", cmd_pos + 10);
        size_t end = text.find("\"", start + 1);
        if (start != std::string::npos && end != std::string::npos) {
            cmd.command = text.substr(start + 1, end - start - 1);
        }
    }

    size_t sig_pos = text.find("\"signal_id\":");
    if (sig_pos != std::string::npos) {
        size_t start = text.find("\"", sig_pos + 12);
        size_t end = text.find("\"", start + 1);
        if (start != std::string::npos && end != std::string::npos) {
            cmd.signal_id = text.substr(start + 1, end - start - 1);
        }
    }
#endif

    return cmd;
}

//
// WebSocketServer Implementation using IXWebSocket
//

#ifdef HAS_IXWEBSOCKET

class WebSocketServer::Impl {
public:
    Impl(int port, WebSocketServer* parent)
        : port_(port)
        , running_(false)
        , parent_(parent)
        , next_conn_id_(1)
        , server_(port, "0.0.0.0") // Listen on all interfaces
    {
        // Set up connection callback
        server_.setOnConnectionCallback(
            [this](std::weak_ptr<ix::WebSocket> webSocket, std::shared_ptr<ix::ConnectionState> connectionState) {
                OnConnection(webSocket, connectionState);
            });
    }

    bool Start() {
        auto result = server_.listen();
        if (!result.first) {
            std::cerr << "[WebSocketServer] Failed to start: " << result.second << std::endl;
            return false;
        }

        server_.start();
        running_ = true;

        std::cout << "[WebSocketServer] Started successfully on 0.0.0.0:" << port_ << std::endl;
        std::cout << "[WebSocketServer] Production-ready IXWebSocket implementation" << std::endl;
        return true;
    }

    void Stop() {
        if (!running_) return;

        running_ = false;
        server_.stop();

        std::cout << "[WebSocketServer] Server stopped" << std::endl;
    }

    bool IsRunning() const {
        return running_;
    }

    void Send(WSConnectionId conn_id, const std::vector<uint8_t>& data) {
        std::lock_guard<std::mutex> lock(connections_mutex_);

        auto it = connections_.find(conn_id);
        if (it == connections_.end()) {
            return;
        }

        auto ws = it->second.websocket.lock();
        if (ws) {
            // Send as text (JSON) instead of binary (MessagePack)
            ws->sendText(std::string(data.begin(), data.end()));
        }
    }

    void Broadcast(const std::vector<uint8_t>& data) {
        std::lock_guard<std::mutex> lock(connections_mutex_);

        std::string binary_data(data.begin(), data.end());
        for (const auto& [conn_id, info] : connections_) {
            auto ws = info.websocket.lock();
            if (ws) {
                ws->sendBinary(binary_data);
            }
        }
    }

    std::set<WSConnectionId> GetSubscribedConnections(const std::string& signal_id) {
        std::lock_guard<std::mutex> lock(connections_mutex_);
        std::set<WSConnectionId> result;

        for (const auto& [conn_id, info] : connections_) {
            if (info.subscribed_signals.count(signal_id) > 0) {
                result.insert(conn_id);
            }
        }

        return result;
    }

private:
    struct ConnectionInfo {
        std::weak_ptr<ix::WebSocket> websocket;
        std::set<std::string> subscribed_signals; // Format: "node_id:pin_name"
    };

    void OnConnection(std::weak_ptr<ix::WebSocket> webSocketWeak,
                     std::shared_ptr<ix::ConnectionState> connectionState) {
        auto webSocket = webSocketWeak.lock();
        if (!webSocket) return;

        // Set up message callback for this connection
        webSocket->setOnMessageCallback(
            [this, webSocketWeak](const ix::WebSocketMessagePtr& msg) {
                if (msg->type == ix::WebSocketMessageType::Open) {
                    OnOpen(webSocketWeak);
                }
                else if (msg->type == ix::WebSocketMessageType::Close) {
                    OnClose(webSocketWeak);
                }
                else if (msg->type == ix::WebSocketMessageType::Message) {
                    OnMessage(webSocketWeak, msg->str);
                }
            });
    }

    void OnOpen(std::weak_ptr<ix::WebSocket> webSocketWeak) {
        std::lock_guard<std::mutex> lock(connections_mutex_);

        WSConnectionId conn_id = next_conn_id_++;
        connections_[conn_id] = ConnectionInfo{webSocketWeak, {}};

        std::cout << "[WebSocketServer] Client connected (ID: " << conn_id << ")" << std::endl;

        if (parent_) {
            parent_->OnClientConnected(conn_id);
        }
    }

    void OnClose(std::weak_ptr<ix::WebSocket> webSocketWeak) {
        std::lock_guard<std::mutex> lock(connections_mutex_);

        // Find connection by weak_ptr
        for (auto it = connections_.begin(); it != connections_.end(); ++it) {
            auto ws1 = it->second.websocket.lock();
            auto ws2 = webSocketWeak.lock();
            if (ws1 && ws2 && ws1.get() == ws2.get()) {
                WSConnectionId conn_id = it->first;
                std::cout << "[WebSocketServer] Client disconnected (ID: " << conn_id << ")" << std::endl;

                if (parent_) {
                    parent_->OnClientDisconnected(conn_id);
                }

                connections_.erase(it);
                break;
            }
        }
    }

    void OnMessage(std::weak_ptr<ix::WebSocket> webSocketWeak, const std::string& payload) {
        std::lock_guard<std::mutex> lock(connections_mutex_);

        // Find connection ID
        WSConnectionId conn_id = 0;
        for (const auto& [id, info] : connections_) {
            auto ws1 = info.websocket.lock();
            auto ws2 = webSocketWeak.lock();
            if (ws1 && ws2 && ws1.get() == ws2.get()) {
                conn_id = id;
                break;
            }
        }

        if (conn_id == 0) return;

        try {
            // Simple JSON parsing for commands
            if (payload.find("\"command\":\"subscribe\"") != std::string::npos) {
                size_t start = payload.find("\"signal_id\":\"");
                if (start != std::string::npos) {
                    start += 13;
                    size_t end = payload.find("\"", start);
                    if (end != std::string::npos) {
                        std::string signal_id = payload.substr(start, end - start);
                        connections_[conn_id].subscribed_signals.insert(signal_id);
                        std::cout << "[WebSocketServer] Client " << conn_id << " subscribed to: " << signal_id << std::endl;
                    }
                }
            }
            else if (payload.find("\"command\":\"unsubscribe\"") != std::string::npos) {
                size_t start = payload.find("\"signal_id\":\"");
                if (start != std::string::npos) {
                    start += 13;
                    size_t end = payload.find("\"", start);
                    if (end != std::string::npos) {
                        std::string signal_id = payload.substr(start, end - start);
                        connections_[conn_id].subscribed_signals.erase(signal_id);
                        std::cout << "[WebSocketServer] Client " << conn_id << " unsubscribed from: " << signal_id << std::endl;
                    }
                }
            }

            if (parent_) {
                std::vector<uint8_t> data(payload.begin(), payload.end());
                parent_->OnClientMessage(conn_id, data);
            }

        } catch (const std::exception& e) {
            std::cerr << "[WebSocketServer] Message parse error: " << e.what() << std::endl;
        }
    }

    int port_;
    bool running_;
    WebSocketServer* parent_;
    ix::WebSocketServer server_;

    WSConnectionId next_conn_id_;
    std::mutex connections_mutex_;
    std::map<WSConnectionId, ConnectionInfo> connections_;
};

#endif // HAS_IXWEBSOCKET

WebSocketServer::WebSocketServer(int port, SignalAggregator* aggregator)
    : port_(port)
    , running_(false)
    , aggregator_(aggregator)
    , impl_(std::make_unique<Impl>(port, this))
{
}

WebSocketServer::~WebSocketServer() {
    Stop();
}

bool WebSocketServer::Start() {
    if (running_) {
        return true;
    }

    running_ = impl_->Start();
    return running_;
}

void WebSocketServer::Stop() {
    if (!running_) {
        return;
    }

    impl_->Stop();
    running_ = false;
}

void WebSocketServer::BroadcastWaveform(const WaveformChunk& chunk) {
    if (!running_) {
        return;
    }

    // Send JSON text instead of MessagePack binary for browser compatibility
    std::ostringstream json;

    // Handle string values (type 2) vs numeric values (type 1)
    if (chunk.is_string) {
        json << "{\"type\":2,\"signal_id\":\"" << chunk.signal_id << "\",\"timestamp\":"
             << chunk.timestamp << ",\"value\":\"" << chunk.string_value << "\"}";
    } else {
        json << "{\"type\":1,\"signal_id\":\"" << chunk.signal_id << "\",\"timestamp\":"
             << chunk.timestamp << ",\"value\":";

        // Send first sample value for real-time display
        if (!chunk.samples.empty()) {
            json << chunk.samples[0];
        } else {
            json << "null";
        }

        json << "}";
    }

    std::string json_str = json.str();
    std::vector<uint8_t> data(json_str.begin(), json_str.end());

    // Get connections subscribed to this signal (uses Impl's subscription tracking)
    std::set<WSConnectionId> subscribers = impl_->GetSubscribedConnections(chunk.signal_id);

    // Send only to subscribed clients (Node-RED architecture)
    for (WSConnectionId conn_id : subscribers) {
        impl_->Send(conn_id, data);
    }
}

void WebSocketServer::BroadcastImage(const std::string& node_id,
                                    const std::vector<uint8_t>& jpeg_data) {
    if (!running_) {
        return;
    }

    std::vector<uint8_t> data = MessagePackUtil::EncodeImage(node_id, jpeg_data);

    std::lock_guard<std::mutex> lock(connections_mutex_);

    // Broadcast to all connections
    for (const auto& [conn_id, conn] : connections_) {
        if (conn.active) {
            impl_->Send(conn_id, data);
        }
    }
}

void WebSocketServer::SendToConnection(WSConnectionId conn_id,
                                      const std::vector<uint8_t>& data) {
    if (!running_) {
        return;
    }

    impl_->Send(conn_id, data);
}

void WebSocketServer::SetMessageCallback(WSMessageCallback callback) {
    message_callback_ = callback;
}

size_t WebSocketServer::GetConnectionCount() const {
    std::lock_guard<std::mutex> lock(connections_mutex_);
    size_t count = 0;
    for (const auto& [id, conn] : connections_) {
        if (conn.active) {
            count++;
        }
    }
    return count;
}

void WebSocketServer::OnClientConnected(WSConnectionId conn_id) {
    std::lock_guard<std::mutex> lock(connections_mutex_);

    Connection conn;
    conn.id = conn_id;
    conn.active = true;
    connections_[conn_id] = conn;

    std::cout << "[WebSocketServer] Client connected: " << conn_id << std::endl;
}

void WebSocketServer::OnClientDisconnected(WSConnectionId conn_id) {
    std::lock_guard<std::mutex> lock(connections_mutex_);
    connections_.erase(conn_id);

    std::cout << "[WebSocketServer] Client disconnected: " << conn_id << std::endl;
}

void WebSocketServer::OnClientMessage(WSConnectionId conn_id,
                                     const std::vector<uint8_t>& data) {
    auto cmd = MessagePackUtil::DecodeCommand(data);

    std::lock_guard<std::mutex> lock(connections_mutex_);

    auto it = connections_.find(conn_id);
    if (it == connections_.end()) {
        return;
    }

    if (cmd.command == "subscribe") {
        // Add signal to subscription list
        it->second.subscribed_signals.push_back(cmd.signal_id);
        std::cout << "[WebSocketServer] Client " << conn_id
                  << " subscribed to: " << cmd.signal_id << std::endl;

    } else if (cmd.command == "unsubscribe") {
        // Remove signal from subscription list
        auto& subs = it->second.subscribed_signals;
        subs.erase(std::remove(subs.begin(), subs.end(), cmd.signal_id), subs.end());
        std::cout << "[WebSocketServer] Client " << conn_id
                  << " unsubscribed from: " << cmd.signal_id << std::endl;

    } else if (cmd.command == "get_waveform") {
        // Send current waveform chunk
        if (aggregator_) {
            WaveformChunk chunk = aggregator_->GetWaveformChunk(
                cmd.signal_id,
                cmd.target_samples
            );
            std::vector<uint8_t> msg = MessagePackUtil::EncodeWaveform(chunk);
            impl_->Send(conn_id, msg);
        }
    }

    // Call user callback if set
    if (message_callback_) {
        message_callback_(conn_id, data);
    }
}

} // namespace CiraBlockRuntime

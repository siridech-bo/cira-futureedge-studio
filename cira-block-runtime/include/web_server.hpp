#pragma once

#include <string>
#include <memory>
#include <thread>
#include <atomic>
#include <vector>
#include <queue>
#include <mutex>
#include "httplib.h"
#include "nlohmann/json.hpp"
#include "metrics_collector.hpp"
#include "auth_manager.hpp"

namespace CiraBlockRuntime {

// Forward declarations
class BlockRuntime;
class BlockExecutor;

struct LogMessage {
    std::string level;     // INFO, WARNING, ERROR
    std::string message;
    uint64_t timestamp;

    nlohmann::json ToJson() const {
        return {
            {"level", level},
            {"message", message},
            {"timestamp", timestamp}
        };
    }
};

class WebServer {
public:
    WebServer(int port, BlockRuntime* runtime, BlockExecutor* executor = nullptr);
    ~WebServer();

    // Start/stop server
    void Start();
    void Stop();
    bool IsRunning() const;

    // Set authentication credentials
    void SetAuth(const std::string& username, const std::string& password);

    // Add log message to buffer
    void AddLog(const std::string& level, const std::string& message);

    // Broadcast metrics to all connected WebSocket clients
    void BroadcastMetrics(const nlohmann::json& metrics);

private:
    int port_;
    BlockRuntime* runtime_;
    BlockExecutor* executor_;
    std::unique_ptr<httplib::Server> server_;
    std::thread server_thread_;
    std::atomic<bool> running_;

    // Authentication
    AuthManager auth_manager_;

    // Log buffer
    std::queue<LogMessage> log_buffer_;
    std::mutex log_mutex_;
    static constexpr size_t MAX_LOG_BUFFER_SIZE = 1000;

    // Setup routes
    void SetupRoutes();

    // Route handlers
    void HandleRoot(const httplib::Request& req, httplib::Response& res);
    void HandleLogin(const httplib::Request& req, httplib::Response& res);
    void HandleDashboardConfig(const httplib::Request& req, httplib::Response& res);
    void HandleSaveDashboardConfig(const httplib::Request& req, httplib::Response& res);
    void HandleBlocks(const httplib::Request& req, httplib::Response& res);
    void HandleBlockData(const httplib::Request& req, httplib::Response& res);
    void HandleMetrics(const httplib::Request& req, httplib::Response& res);
    void HandleLogs(const httplib::Request& req, httplib::Response& res);
    void HandleRuntimeControl(const httplib::Request& req, httplib::Response& res);
    void HandleWidgetButton(const httplib::Request& req, httplib::Response& res);
    void HandleWidgetLED(const httplib::Request& req, httplib::Response& res);

    // Utility
    bool ValidateAuth(const httplib::Request& req);
    std::string GetAuthToken(const httplib::Request& req);
    void ServeStaticFile(const std::string& filepath, httplib::Response& res, const std::string& content_type);
    std::string LoadDashboardHTML();
    std::string LoadDashboardConfig();
    void SaveDashboardConfig(const std::string& config);
    std::vector<LogMessage> GetRecentLogs(size_t limit);
};

} // namespace CiraBlockRuntime

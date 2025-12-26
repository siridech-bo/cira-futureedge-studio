#include "web_server.hpp"
#include "block_executor.hpp"
#include <fstream>
#include <sstream>
#include <iostream>
#include <chrono>

// GCC 7.x compatibility: use experimental/filesystem
#if __has_include(<filesystem>)
#include <filesystem>
namespace fs = std::filesystem;
#elif __has_include(<experimental/filesystem>)
#include <experimental/filesystem>
namespace fs = std::experimental::filesystem;
#else
#error "No filesystem support found"
#endif

namespace CiraBlockRuntime {

WebServer::WebServer(int port, BlockRuntime* runtime, BlockExecutor* executor)
    : port_(port)
    , runtime_(runtime)
    , executor_(executor)
    , running_(false) {
}

WebServer::~WebServer() {
    Stop();
}

void WebServer::Start() {
    if (running_) {
        return;
    }

    running_ = true;
    server_ = std::make_unique<httplib::Server>();

    SetupRoutes();

    // Start server in separate thread
    server_thread_ = std::thread([this]() {
        std::cout << "Web server starting on port " << port_ << std::endl;
        if (!server_->listen("0.0.0.0", port_)) {
            std::cerr << "Failed to start web server on port " << port_ << std::endl;
            running_ = false;
        }
    });

    AddLog("INFO", "Web server started on port " + std::to_string(port_));
}

void WebServer::Stop() {
    if (!running_) {
        return;
    }

    running_ = false;

    if (server_) {
        server_->stop();
    }

    if (server_thread_.joinable()) {
        server_thread_.join();
    }

    AddLog("INFO", "Web server stopped");
}

bool WebServer::IsRunning() const {
    return running_;
}

void WebServer::SetAuth(const std::string& username, const std::string& password) {
    auth_manager_.SetCredentials(username, password);

    if (username.empty()) {
        AddLog("WARNING", "Web authentication disabled - not secure!");
    } else {
        AddLog("INFO", "Web authentication enabled for user: " + username);
    }
}

void WebServer::AddLog(const std::string& level, const std::string& message) {
    std::lock_guard<std::mutex> lock(log_mutex_);

    LogMessage log;
    log.level = level;
    log.message = message;
    log.timestamp = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::system_clock::now().time_since_epoch()
    ).count();

    log_buffer_.push(log);

    // Keep buffer size manageable
    while (log_buffer_.size() > MAX_LOG_BUFFER_SIZE) {
        log_buffer_.pop();
    }
}

void WebServer::BroadcastMetrics(const nlohmann::json& metrics) {
    // TODO: Implement WebSocket broadcasting when clients are connected
    // For now, metrics are polled via REST API
}

void WebServer::SetupRoutes() {
    // Serve dashboard HTML
    server_->Get("/", [this](const httplib::Request& req, httplib::Response& res) {
        HandleRoot(req, res);
    });

    // Serve static files (CSS, JS)
    server_->Get(R"(/css/(.+))", [this](const httplib::Request& req, httplib::Response& res) {
        std::string filename = req.matches[1];
        std::string filepath = "web/css/" + filename;
        ServeStaticFile(filepath, res, "text/css");
    });

    server_->Get(R"(/js/(.+))", [this](const httplib::Request& req, httplib::Response& res) {
        std::string filename = req.matches[1];
        std::string filepath = "web/js/" + filename;
        ServeStaticFile(filepath, res, "application/javascript");
    });

    // Authentication
    server_->Post("/api/auth/login", [this](const httplib::Request& req, httplib::Response& res) {
        HandleLogin(req, res);
    });

    // Dashboard configuration
    server_->Get("/api/dashboard/config", [this](const httplib::Request& req, httplib::Response& res) {
        if (!ValidateAuth(req)) {
            res.status = 401;
            res.set_content("{\"error\":\"Unauthorized\"}", "application/json");
            return;
        }
        HandleDashboardConfig(req, res);
    });

    server_->Post("/api/dashboard/config", [this](const httplib::Request& req, httplib::Response& res) {
        if (!ValidateAuth(req)) {
            res.status = 401;
            res.set_content("{\"error\":\"Unauthorized\"}", "application/json");
            return;
        }
        HandleSaveDashboardConfig(req, res);
    });

    // Block information
    server_->Get("/api/blocks", [this](const httplib::Request& req, httplib::Response& res) {
        if (!ValidateAuth(req)) {
            res.status = 401;
            res.set_content("{\"error\":\"Unauthorized\"}", "application/json");
            return;
        }
        HandleBlocks(req, res);
    });

    // Block real-time data
    server_->Get("/api/blocks/data", [this](const httplib::Request& req, httplib::Response& res) {
        if (!ValidateAuth(req)) {
            res.status = 401;
            res.set_content("{\"error\":\"Unauthorized\"}", "application/json");
            return;
        }
        HandleBlockData(req, res);
    });

    // Metrics
    server_->Get("/api/metrics", [this](const httplib::Request& req, httplib::Response& res) {
        if (!ValidateAuth(req)) {
            res.status = 401;
            res.set_content("{\"error\":\"Unauthorized\"}", "application/json");
            return;
        }
        HandleMetrics(req, res);
    });

    // Logs
    server_->Get("/api/logs", [this](const httplib::Request& req, httplib::Response& res) {
        if (!ValidateAuth(req)) {
            res.status = 401;
            res.set_content("{\"error\":\"Unauthorized\"}", "application/json");
            return;
        }
        HandleLogs(req, res);
    });

    // Runtime control
    server_->Post("/api/runtime/:action", [this](const httplib::Request& req, httplib::Response& res) {
        if (!ValidateAuth(req)) {
            res.status = 401;
            res.set_content("{\"error\":\"Unauthorized\"}", "application/json");
            return;
        }
        HandleRuntimeControl(req, res);
    });

    // Widget endpoints
    server_->Post("/api/widget/button", [this](const httplib::Request& req, httplib::Response& res) {
        if (!ValidateAuth(req)) {
            res.status = 401;
            res.set_content("{\"error\":\"Unauthorized\"}", "application/json");
            return;
        }
        HandleWidgetButton(req, res);
    });

    server_->Get("/api/widget/led", [this](const httplib::Request& req, httplib::Response& res) {
        if (!ValidateAuth(req)) {
            res.status = 401;
            res.set_content("{\"error\":\"Unauthorized\"}", "application/json");
            return;
        }
        HandleWidgetLED(req, res);
    });
}

void WebServer::HandleRoot(const httplib::Request& req, httplib::Response& res) {
    std::string html = LoadDashboardHTML();
    res.set_content(html, "text/html");
}

void WebServer::HandleLogin(const httplib::Request& req, httplib::Response& res) {
    try {
        auto json = nlohmann::json::parse(req.body);
        std::string username = json["username"];
        std::string password = json["password"];

        std::string token = auth_manager_.Login(username, password);

        if (token.empty()) {
            res.status = 401;
            res.set_content("{\"error\":\"Invalid credentials\"}", "application/json");
            AddLog("WARNING", "Failed login attempt for user: " + username);
        } else {
            nlohmann::json response;
            response["token"] = token;
            response["auth_enabled"] = auth_manager_.IsAuthEnabled();
            res.set_content(response.dump(), "application/json");
            AddLog("INFO", "User logged in: " + username);
        }
    } catch (const std::exception& e) {
        res.status = 400;
        res.set_content("{\"error\":\"Invalid request\"}", "application/json");
    }
}

void WebServer::HandleDashboardConfig(const httplib::Request& req, httplib::Response& res) {
    std::string config = LoadDashboardConfig();
    if (config.empty()) {
        config = "{}";  // Return empty object if no config exists
    }
    res.set_content(config, "application/json");
}

void WebServer::HandleSaveDashboardConfig(const httplib::Request& req, httplib::Response& res) {
    SaveDashboardConfig(req.body);
    res.set_content("{\"success\":true}", "application/json");
    AddLog("INFO", "Dashboard configuration saved");
}

void WebServer::HandleBlocks(const httplib::Request& req, httplib::Response& res) {
    nlohmann::json response = nlohmann::json::array();

    if (executor_) {
        const auto& nodes = executor_->GetNodes();

        for (const auto& [node_id, node] : nodes) {
            nlohmann::json block_info;
            block_info["node_id"] = node_id;
            block_info["type"] = node.node_type;
            block_info["status"] = "running";

            // List all output pins
            nlohmann::json pins = nlohmann::json::array();
            for (const auto& [pin_name, value] : node.output_values) {
                pins.push_back(pin_name);
            }
            block_info["output_pins"] = pins;

            response.push_back(block_info);
        }
    }

    res.set_content(response.dump(), "application/json");
}

void WebServer::HandleBlockData(const httplib::Request& req, httplib::Response& res) {
    nlohmann::json response = nlohmann::json::object();

    if (executor_) {
        const auto& nodes = executor_->GetNodes();

        for (const auto& [node_id, node] : nodes) {
            nlohmann::json node_data;

            // Add all output pin values
            for (const auto& [pin_name, value] : node.output_values) {
                nlohmann::json pin_data;

                // Convert BlockValue (std::variant) to JSON
                std::visit([&pin_data](auto&& arg) {
                    using T = std::decay_t<decltype(arg)>;
                    if constexpr (std::is_same_v<T, float>) {
                        pin_data["value"] = arg;
                        pin_data["type"] = "float";
                    } else if constexpr (std::is_same_v<T, int>) {
                        pin_data["value"] = arg;
                        pin_data["type"] = "int";
                    } else if constexpr (std::is_same_v<T, bool>) {
                        pin_data["value"] = arg;
                        pin_data["type"] = "bool";
                    } else if constexpr (std::is_same_v<T, std::string>) {
                        pin_data["value"] = arg;
                        pin_data["type"] = "string";
                    } else if constexpr (std::is_same_v<T, std::vector<float>>) {
                        pin_data["value"] = arg;
                        pin_data["type"] = "array_float";
                    }
                }, value);

                node_data[pin_name] = pin_data;
            }

            response[std::to_string(node_id)] = node_data;
        }
    }

    res.set_content(response.dump(), "application/json");
}

void WebServer::HandleMetrics(const httplib::Request& req, httplib::Response& res) {
    // TODO: Get actual metrics from runtime's MetricsCollector
    nlohmann::json metrics = {
        {"blocks", nlohmann::json::array()},
        {"system", {
            {"cpu_usage", 25.5},
            {"memory_used_mb", 512},
            {"memory_total_mb", 4096},
            {"uptime_seconds", 3600}
        }},
        {"timestamp", std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::system_clock::now().time_since_epoch()
        ).count()}
    };

    res.set_content(metrics.dump(), "application/json");
}

void WebServer::HandleLogs(const httplib::Request& req, httplib::Response& res) {
    // Parse query parameters
    size_t limit = 100;
    if (req.has_param("limit")) {
        limit = std::stoi(req.get_param_value("limit"));
    }

    auto logs = GetRecentLogs(limit);

    nlohmann::json response = nlohmann::json::array();
    for (const auto& log : logs) {
        response.push_back(log.ToJson());
    }

    res.set_content(response.dump(), "application/json");
}

void WebServer::HandleRuntimeControl(const httplib::Request& req, httplib::Response& res) {
    std::string action = req.matches[1];

    // TODO: Implement actual runtime control
    nlohmann::json response;

    if (action == "start") {
        response["success"] = true;
        response["message"] = "Runtime start requested";
        AddLog("INFO", "Runtime start requested via web interface");
    } else if (action == "stop") {
        response["success"] = true;
        response["message"] = "Runtime stop requested";
        AddLog("INFO", "Runtime stop requested via web interface");
    } else if (action == "restart") {
        response["success"] = true;
        response["message"] = "Runtime restart requested";
        AddLog("INFO", "Runtime restart requested via web interface");
    } else {
        res.status = 400;
        response["error"] = "Unknown action: " + action;
    }

    res.set_content(response.dump(), "application/json");
}

bool WebServer::ValidateAuth(const httplib::Request& req) {
    std::string token = GetAuthToken(req);
    return auth_manager_.ValidateToken(token);
}

std::string WebServer::GetAuthToken(const httplib::Request& req) {
    // Check Authorization header
    if (req.has_header("Authorization")) {
        std::string auth = req.get_header_value("Authorization");
        if (auth.find("Bearer ") == 0) {
            return auth.substr(7);  // Remove "Bearer " prefix
        }
    }

    // Check query parameter (for WebSocket)
    if (req.has_param("token")) {
        return req.get_param_value("token");
    }

    return "";
}

void WebServer::ServeStaticFile(const std::string& filepath, httplib::Response& res, const std::string& content_type) {
    std::ifstream file(filepath);
    if (file.is_open()) {
        std::stringstream buffer;
        buffer << file.rdbuf();
        res.set_content(buffer.str(), content_type.c_str());
    } else {
        res.status = 404;
        res.set_content("File not found", "text/plain");
    }
}

std::string WebServer::LoadDashboardHTML() {
    // Try to load from file
    std::string html_path = "web/index.html";

    std::ifstream file(html_path);
    if (file.is_open()) {
        std::stringstream buffer;
        buffer << file.rdbuf();
        return buffer.str();
    }

    // Return minimal placeholder if file not found
    return R"(
<!DOCTYPE html>
<html>
<head>
    <title>CiRA Dashboard</title>
</head>
<body>
    <h1>CiRA Runtime Dashboard</h1>
    <p>Dashboard files not found. Please deploy web assets.</p>
</body>
</html>
)";
}

std::string WebServer::LoadDashboardConfig() {
    std::string config_path = "dashboard_config.json";

    std::ifstream file(config_path);
    if (file.is_open()) {
        std::stringstream buffer;
        buffer << file.rdbuf();
        return buffer.str();
    }

    return "";
}

void WebServer::SaveDashboardConfig(const std::string& config) {
    std::string config_path = "dashboard_config.json";

    std::ofstream file(config_path);
    if (file.is_open()) {
        file << config;
        file.close();
    }
}

std::vector<LogMessage> WebServer::GetRecentLogs(size_t limit) {
    std::lock_guard<std::mutex> lock(log_mutex_);

    std::vector<LogMessage> result;
    std::queue<LogMessage> temp = log_buffer_;  // Copy queue

    while (!temp.empty() && result.size() < limit) {
        result.push_back(temp.front());
        temp.pop();
    }

    return result;
}

void WebServer::HandleWidgetButton(const httplib::Request& req, httplib::Response& res) {
    try {
        nlohmann::json request_body = nlohmann::json::parse(req.body);

        if (!request_body.contains("button_id") || !request_body.contains("state")) {
            res.status = 400;
            res.set_content("{\"error\":\"Missing button_id or state\"}", "application/json");
            return;
        }

        std::string button_id = request_body["button_id"];
        bool state = request_body["state"];

        if (!executor_) {
            res.status = 500;
            res.set_content("{\"error\":\"Block executor not available\"}", "application/json");
            return;
        }

        // Find the WebButtonBlock by matching button_id in node config
        const auto& nodes = executor_->GetNodes();
        bool button_found = false;

        for (const auto& [node_id, node] : nodes) {
            // Check if this is a web-button node
            if (node.node_type.find("web") != std::string::npos &&
                node.node_type.find("button") != std::string::npos) {

                // Check if button_id matches
                auto it = node.config.find("button_id");
                if (it != node.config.end() && it->second == button_id) {
                    // Found the button! Update its state via the block's SetButtonState method
                    // Note: We need to access the actual block instance through the executor
                    auto block = executor_->GetBlock(node_id);
                    if (block) {
                        // Call SetInput to update button state
                        block->SetInput("state", state);
                        button_found = true;

                        AddLog("INFO", "Web button '" + button_id + "' state changed to " +
                               (state ? "pressed" : "released"));
                        break;
                    }
                }
            }
        }

        if (button_found) {
            nlohmann::json response;
            response["success"] = true;
            response["button_id"] = button_id;
            response["state"] = state;
            res.set_content(response.dump(), "application/json");
        } else {
            res.status = 404;
            res.set_content("{\"error\":\"Button not found\"}", "application/json");
        }

    } catch (const std::exception& e) {
        res.status = 400;
        res.set_content("{\"error\":\"Invalid request\"}", "application/json");
        AddLog("ERROR", "Widget button request failed: " + std::string(e.what()));
    }
}

void WebServer::HandleWidgetLED(const httplib::Request& req, httplib::Response& res) {
    nlohmann::json response;
    response["leds"] = nlohmann::json::array();

    if (!executor_) {
        res.status = 500;
        res.set_content("{\"error\":\"Block executor not available\"}", "application/json");
        return;
    }

    // Find all WebLEDBlocks and get their states
    const auto& nodes = executor_->GetNodes();

    for (const auto& [node_id, node] : nodes) {
        // Check if this is a web-led node
        if (node.node_type.find("web") != std::string::npos &&
            node.node_type.find("led") != std::string::npos) {

            // Get LED configuration
            std::string led_id = "led_" + std::to_string(node_id);
            std::string label = "LED";
            std::string color = "green";

            auto it_id = node.config.find("led_id");
            if (it_id != node.config.end()) {
                led_id = it_id->second;
            }

            auto it_label = node.config.find("label");
            if (it_label != node.config.end()) {
                label = it_label->second;
            }

            auto it_color = node.config.find("color");
            if (it_color != node.config.end()) {
                color = it_color->second;
            }

            // Get LED state from output values
            bool state = false;
            auto output_it = node.output_values.find("state");
            if (output_it != node.output_values.end()) {
                // Extract bool from BlockValue (std::variant)
                if (std::holds_alternative<bool>(output_it->second)) {
                    state = std::get<bool>(output_it->second);
                }
            }

            // Add LED info to response
            nlohmann::json led_info;
            led_info["led_id"] = led_id;
            led_info["label"] = label;
            led_info["state"] = state;
            led_info["color"] = color;

            response["leds"].push_back(led_info);
        }
    }

    res.set_content(response.dump(), "application/json");
}

} // namespace CiraBlockRuntime

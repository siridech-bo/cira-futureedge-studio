#include "manifest_parser.hpp"
#include "block_loader.hpp"
#include "block_executor.hpp"
#include <iostream>
#include <signal.h>
#include <thread>
#include <chrono>

#ifdef WITH_WEB_SERVER
#include "web_server.hpp"
#include "metrics_collector.hpp"
#endif

using namespace CiraBlockRuntime;

// Global flag for graceful shutdown
volatile bool g_running = true;

void signal_handler(int signal) {
    std::cout << "\nReceived signal " << signal << ", shutting down..." << std::endl;
    g_running = false;
}

void print_usage(const char* program_name) {
    std::cout << "CiRA Block Runtime v1.0.0" << std::endl;
    std::cout << "Usage: " << program_name << " <manifest.json> [options]" << std::endl;
    std::cout << std::endl;
    std::cout << "Options:" << std::endl;
    std::cout << "  --block-path <path>    Set custom block library path" << std::endl;
    std::cout << "                         (default: /usr/local/lib/cira/blocks/)" << std::endl;
    std::cout << "  --iterations <n>       Run for N iterations then exit (default: infinite)" << std::endl;
    std::cout << "  --rate <hz>            Execution rate in Hz (default: 10)" << std::endl;
#ifdef WITH_WEB_SERVER
    std::cout << "  --web-port <port>      Enable web dashboard on port (default: disabled)" << std::endl;
    std::cout << "  --web-user <username>  Web dashboard username (default: none - no auth)" << std::endl;
    std::cout << "  --web-pass <password>  Web dashboard password (default: none - no auth)" << std::endl;
    std::cout << "  --no-auth              Disable web authentication (not recommended)" << std::endl;
#endif
    std::cout << "  --help                 Show this help message" << std::endl;
}

int main(int argc, char* argv[]) {
    std::cout << "========================================" << std::endl;
    std::cout << "   CiRA Block Runtime v1.0.0" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << std::endl;

    // Parse command line arguments
    if (argc < 2) {
        print_usage(argv[0]);
        return 1;
    }

    // Check for --help first
    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "--help") {
            print_usage(argv[0]);
            return 0;
        }
    }

    std::string manifest_path = argv[1];
    std::string block_path = "/usr/local/lib/cira/blocks/";
    int max_iterations = -1;  // -1 = infinite
    int rate_hz = 10;

#ifdef WITH_WEB_SERVER
    int web_port = 0;  // 0 = disabled
    std::string web_user;
    std::string web_pass;
    bool web_no_auth = false;
#endif

    for (int i = 2; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "--block-path" && i + 1 < argc) {
            block_path = argv[++i];
        } else if (arg == "--iterations" && i + 1 < argc) {
            max_iterations = std::atoi(argv[++i]);
        } else if (arg == "--rate" && i + 1 < argc) {
            rate_hz = std::atoi(argv[++i]);
        }
#ifdef WITH_WEB_SERVER
        else if (arg == "--web-port" && i + 1 < argc) {
            web_port = std::atoi(argv[++i]);
        } else if (arg == "--web-user" && i + 1 < argc) {
            web_user = argv[++i];
        } else if (arg == "--web-pass" && i + 1 < argc) {
            web_pass = argv[++i];
        } else if (arg == "--no-auth") {
            web_no_auth = true;
        }
#endif
    }

    // Install signal handlers
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    // Parse manifest
    std::cout << "Loading manifest: " << manifest_path << std::endl;
    ManifestParser parser;
    if (!parser.LoadFromFile(manifest_path)) {
        std::cerr << "ERROR: " << parser.GetError() << std::endl;
        return 1;
    }

    const BlockManifest& manifest = parser.GetManifest();

    // Create block loader
    BlockLoader loader;
    loader.SetBlockLibraryPath(block_path);
    std::cout << "Block library path: " << block_path << std::endl;

    // Verify all required blocks are available
    // Create executor (even if blocks are missing, for web server)
    BlockExecutor executor;

    std::cout << "\n=== Checking Required Blocks ===" << std::endl;
    bool all_blocks_available = true;
    for (const auto& block : manifest.blocks) {
        bool available = loader.IsBlockAvailable(block.id, block.version);
        std::cout << "  " << block.id << " v" << block.version << ": "
                 << (available ? "✓ Available" : "✗ Missing") << std::endl;
        if (!available) {
            all_blocks_available = false;
        }
    }

    bool executor_initialized = false;

    if (!all_blocks_available) {
        std::cerr << "\nWARNING: Some required blocks are missing" << std::endl;
        std::cerr << "Please install missing blocks to: " << block_path << std::endl;

        // If web dashboard is disabled, exit with error
        // If web dashboard is enabled, continue to allow dashboard access
        if (web_port == 0) {
            std::cerr << "ERROR: Cannot run without blocks when web dashboard is disabled" << std::endl;
            return 1;
        }

        std::cout << "\nContinuing with web dashboard only (no block execution)..." << std::endl;

        // Skip executor initialization - just run web server
        goto start_web_server;
    }

    // Build execution graph
    if (!executor.BuildFromManifest(manifest, loader)) {
        std::cerr << "ERROR: Failed to build execution graph: "
                 << executor.GetError() << std::endl;
        return 1;
    }

    // Initialize all blocks (continue even if some fail)
    if (!executor.Initialize()) {
        std::cerr << "WARNING: Some blocks failed to initialize: "
                 << executor.GetError() << std::endl;

        if (web_port == 0) {
            // Without web dashboard, we can't continue with failed blocks
            std::cerr << "ERROR: Cannot run without web dashboard when blocks fail" << std::endl;
            executor.Shutdown();
            return 1;
        }

        std::cout << "Continuing with web dashboard (some blocks may not function)..." << std::endl;
    }

    executor_initialized = true;

#ifdef WITH_WEB_SERVER
start_web_server:
    // Start web server if enabled
    std::unique_ptr<CiraBlockRuntime::WebServer> web_server;
    std::unique_ptr<CiraBlockRuntime::MetricsCollector> metrics_collector;

    if (web_port > 0) {
        std::cout << "\n=== Starting Web Dashboard ===" << std::endl;
        std::cout << "  Port: " << web_port << std::endl;

        metrics_collector = std::make_unique<CiraBlockRuntime::MetricsCollector>();
        web_server = std::make_unique<CiraBlockRuntime::WebServer>(web_port, nullptr, &executor);

        // Setup authentication
        if (!web_no_auth && !web_user.empty() && !web_pass.empty()) {
            web_server->SetAuth(web_user, web_pass);
            std::cout << "  Authentication: Enabled" << std::endl;
            std::cout << "  Username: " << web_user << std::endl;
        } else {
            web_server->SetAuth("", "");  // Disable auth
            std::cout << "  Authentication: Disabled (WARNING: Not secure!)" << std::endl;
        }

        web_server->Start();

        std::cout << "\n  Dashboard URL: http://localhost:" << web_port << std::endl;
        std::cout << "  (Replace 'localhost' with device IP for remote access)" << std::endl;
        std::cout << "========================================" << std::endl;
    }
#endif

    // Main execution loop (only if executor was initialized successfully)
    if (executor_initialized) {
        std::cout << "\n========================================" << std::endl;
        std::cout << "   Starting Pipeline Execution" << std::endl;
        std::cout << "   Rate: " << rate_hz << " Hz" << std::endl;
        if (max_iterations > 0) {
            std::cout << "   Iterations: " << max_iterations << std::endl;
        } else {
            std::cout << "   Iterations: Infinite (Ctrl+C to stop)" << std::endl;
        }
        std::cout << "========================================" << std::endl;
        std::cout << std::endl;

        int iteration = 0;
        auto loop_duration = std::chrono::milliseconds(1000 / rate_hz);

        while (g_running && (max_iterations < 0 || iteration < max_iterations)) {
        auto loop_start = std::chrono::high_resolution_clock::now();

        // Execute pipeline (continue even if execution fails)
        if (!executor.Execute()) {
            std::cerr << "WARNING: Execution failed: " << executor.GetError() << std::endl;
            // Don't break - continue running for web dashboard access
            // User can see errors in the dashboard
        }

        iteration++;

        // Print statistics every 10 iterations
        if (iteration % 10 == 0) {
            auto stats = executor.GetStats();
            std::cout << "Iteration " << iteration
                     << " | Avg execution time: " << stats.avg_execution_time_ms << " ms"
                     << " | Errors: " << stats.total_errors << std::endl;
        }

        // Sleep to maintain target rate
        auto loop_end = std::chrono::high_resolution_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(loop_end - loop_start);
        if (elapsed < loop_duration) {
            std::this_thread::sleep_for(loop_duration - elapsed);
        } else {
            std::cerr << "Warning: Execution time (" << elapsed.count()
                     << " ms) exceeds target period (" << loop_duration.count() << " ms)" << std::endl;
        }
        }

        // Shutdown
        std::cout << "\n=== Final Statistics ===" << std::endl;
        auto stats = executor.GetStats();
        std::cout << "  Total executions: " << stats.total_executions << std::endl;
        std::cout << "  Total errors: " << stats.total_errors << std::endl;
        std::cout << "  Avg execution time: " << stats.avg_execution_time_ms << " ms" << std::endl;

        executor.Shutdown();
    } else {
        // No executor - web dashboard only mode
        std::cout << "\n========================================" << std::endl;
        std::cout << "   Web Dashboard Only Mode" << std::endl;
        std::cout << "   Press Ctrl+C to stop" << std::endl;
        std::cout << "========================================" << std::endl;

        // Just wait for signal
        while (g_running) {
            std::this_thread::sleep_for(std::chrono::seconds(1));
        }
    }

    loader.UnloadAll();

#ifdef WITH_WEB_SERVER
    // Stop web server
    if (web_server) {
        std::cout << "\nStopping web server..." << std::endl;
        web_server->Stop();
    }
#endif

    std::cout << "\nShutdown complete. Goodbye!" << std::endl;
    return 0;
}

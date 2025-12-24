#include "manifest_parser.hpp"
#include "block_loader.hpp"
#include "block_executor.hpp"
#include <iostream>
#include <signal.h>
#include <thread>
#include <chrono>

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

    for (int i = 2; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "--block-path" && i + 1 < argc) {
            block_path = argv[++i];
        } else if (arg == "--iterations" && i + 1 < argc) {
            max_iterations = std::atoi(argv[++i]);
        } else if (arg == "--rate" && i + 1 < argc) {
            rate_hz = std::atoi(argv[++i]);
        }
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

    if (!all_blocks_available) {
        std::cerr << "\nERROR: Some required blocks are missing" << std::endl;
        std::cerr << "Please install missing blocks to: " << block_path << std::endl;
        return 1;
    }

    // Create executor
    BlockExecutor executor;

    // Build execution graph
    if (!executor.BuildFromManifest(manifest, loader)) {
        std::cerr << "ERROR: Failed to build execution graph: "
                 << executor.GetError() << std::endl;
        return 1;
    }

    // Initialize all blocks
    if (!executor.Initialize()) {
        std::cerr << "ERROR: Failed to initialize blocks: "
                 << executor.GetError() << std::endl;
        executor.Shutdown();
        return 1;
    }

    // Main execution loop
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

        // Execute pipeline
        if (!executor.Execute()) {
            std::cerr << "ERROR: Execution failed: " << executor.GetError() << std::endl;
            break;
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
    loader.UnloadAll();

    std::cout << "\nShutdown complete. Goodbye!" << std::endl;
    return 0;
}

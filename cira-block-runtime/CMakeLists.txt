cmake_minimum_required(VERSION 3.10)
project(cira-block-runtime VERSION 1.0.0)

# C++17 required
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Build type
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Include directories
include_directories(
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/third_party
)

# Optional: Enable web server
option(WITH_WEB_SERVER "Build with embedded web server" ON)

# Runtime executable
set(RUNTIME_SOURCES
    src/main.cpp
    src/manifest_parser.cpp
    src/block_loader.cpp
    src/block_executor.cpp
)

# Add web server sources if enabled
if(WITH_WEB_SERVER)
    list(APPEND RUNTIME_SOURCES
        src/web_server.cpp
        src/metrics_collector.cpp
        src/auth_manager.cpp
        src/signal_aggregator.cpp
        src/websocket_server.cpp
    )
    add_definitions(-DWITH_WEB_SERVER)

    # Check for msgpack-c (header-only)
    if(EXISTS "${CMAKE_SOURCE_DIR}/third_party/msgpack-c/include")
        include_directories(${CMAKE_SOURCE_DIR}/third_party/msgpack-c/include)
        message(STATUS "Found msgpack-c: Using MessagePack binary protocol")
    else()
        message(STATUS "msgpack-c not found: Using fallback binary protocol")
        message(STATUS "To enable MessagePack: git clone https://github.com/msgpack/msgpack-c.git third_party/msgpack-c")
    endif()

    # Check for IXWebSocket (lightweight C++ WebSocket library)
    if(EXISTS "${CMAKE_SOURCE_DIR}/third_party/IXWebSocket")
        include_directories(${CMAKE_SOURCE_DIR}/third_party/IXWebSocket)
        message(STATUS "Found IXWebSocket: Production WebSocket support enabled")
        add_definitions(-DHAS_IXWEBSOCKET)

        # Add IXWebSocket source files (only the ones we need for server)
        set(IXWEBSOCKET_SOURCES
            ${CMAKE_SOURCE_DIR}/third_party/IXWebSocket/ixwebsocket/IXWebSocketServer.cpp
            ${CMAKE_SOURCE_DIR}/third_party/IXWebSocket/ixwebsocket/IXWebSocket.cpp
            ${CMAKE_SOURCE_DIR}/third_party/IXWebSocket/ixwebsocket/IXWebSocketTransport.cpp
            ${CMAKE_SOURCE_DIR}/third_party/IXWebSocket/ixwebsocket/IXWebSocketHandshake.cpp
            ${CMAKE_SOURCE_DIR}/third_party/IXWebSocket/ixwebsocket/IXWebSocketHttpHeaders.cpp
            ${CMAKE_SOURCE_DIR}/third_party/IXWebSocket/ixwebsocket/IXWebSocketCloseConstants.cpp
            ${CMAKE_SOURCE_DIR}/third_party/IXWebSocket/ixwebsocket/IXWebSocketPerMessageDeflate.cpp
            ${CMAKE_SOURCE_DIR}/third_party/IXWebSocket/ixwebsocket/IXWebSocketPerMessageDeflateCodec.cpp
            ${CMAKE_SOURCE_DIR}/third_party/IXWebSocket/ixwebsocket/IXWebSocketPerMessageDeflateOptions.cpp
            ${CMAKE_SOURCE_DIR}/third_party/IXWebSocket/ixwebsocket/IXSocketServer.cpp
            ${CMAKE_SOURCE_DIR}/third_party/IXWebSocket/ixwebsocket/IXSocket.cpp
            ${CMAKE_SOURCE_DIR}/third_party/IXWebSocket/ixwebsocket/IXSocketConnect.cpp
            ${CMAKE_SOURCE_DIR}/third_party/IXWebSocket/ixwebsocket/IXSocketFactory.cpp
            ${CMAKE_SOURCE_DIR}/third_party/IXWebSocket/ixwebsocket/IXDNSLookup.cpp
            ${CMAKE_SOURCE_DIR}/third_party/IXWebSocket/ixwebsocket/IXCancellationRequest.cpp
            ${CMAKE_SOURCE_DIR}/third_party/IXWebSocket/ixwebsocket/IXConnectionState.cpp
            ${CMAKE_SOURCE_DIR}/third_party/IXWebSocket/ixwebsocket/IXNetSystem.cpp
            ${CMAKE_SOURCE_DIR}/third_party/IXWebSocket/ixwebsocket/IXSetThreadName.cpp
            ${CMAKE_SOURCE_DIR}/third_party/IXWebSocket/ixwebsocket/IXSelectInterruptFactory.cpp
            ${CMAKE_SOURCE_DIR}/third_party/IXWebSocket/ixwebsocket/IXSelectInterrupt.cpp
            ${CMAKE_SOURCE_DIR}/third_party/IXWebSocket/ixwebsocket/IXSelectInterruptPipe.cpp
            ${CMAKE_SOURCE_DIR}/third_party/IXWebSocket/ixwebsocket/IXSelectInterruptEvent.cpp
            ${CMAKE_SOURCE_DIR}/third_party/IXWebSocket/ixwebsocket/IXStrCaseCompare.cpp
            ${CMAKE_SOURCE_DIR}/third_party/IXWebSocket/ixwebsocket/IXUserAgent.cpp
            ${CMAKE_SOURCE_DIR}/third_party/IXWebSocket/ixwebsocket/IXHttp.cpp
            ${CMAKE_SOURCE_DIR}/third_party/IXWebSocket/ixwebsocket/IXExponentialBackoff.cpp
            ${CMAKE_SOURCE_DIR}/third_party/IXWebSocket/ixwebsocket/IXUrlParser.cpp
        )
        list(APPEND RUNTIME_SOURCES ${IXWEBSOCKET_SOURCES})
    else()
        message(STATUS "IXWebSocket not found: WebSocket server will not function")
        message(STATUS "To enable IXWebSocket: git clone https://github.com/machinezone/IXWebSocket.git third_party/IXWebSocket")
    endif()
endif()

add_executable(cira-block-runtime ${RUNTIME_SOURCES})

# Link libraries
if(UNIX)
    target_link_libraries(cira-block-runtime dl pthread)

    # Link stdc++fs for GCC < 9 (experimental/filesystem)
    if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU" AND CMAKE_CXX_COMPILER_VERSION VERSION_LESS 9.0)
        target_link_libraries(cira-block-runtime stdc++fs)
    endif()

    # OpenSSL for SHA256 hashing in AuthManager
    if(WITH_WEB_SERVER)
        find_package(OpenSSL)
        if(OpenSSL_FOUND)
            target_link_libraries(cira-block-runtime OpenSSL::Crypto)
        endif()
    endif()
elseif(WIN32)
    target_link_libraries(cira-block-runtime ws2_32)

    # Windows Crypto API for SHA256 hashing
    if(WITH_WEB_SERVER)
        target_link_libraries(cira-block-runtime crypt32)
    endif()
endif()

# Compiler flags
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(cira-block-runtime PRIVATE
        -Wall -Wextra -Wpedantic
    )
endif()

# Install runtime
install(TARGETS cira-block-runtime
    RUNTIME DESTINATION bin
)

# Install headers (for block development)
install(DIRECTORY include/
    DESTINATION include/cira-block-runtime
    FILES_MATCHING PATTERN "*.hpp"
)

# Install web assets (if web server enabled)
if(WITH_WEB_SERVER)
    install(DIRECTORY web/
        DESTINATION share/cira-block-runtime/web
        FILES_MATCHING
        PATTERN "*.html"
        PATTERN "*.css"
        PATTERN "*.js"
    )
    message(STATUS "Web server enabled - dashboard will be available on port 8080")
endif()

# Optional: Build example blocks
option(BUILD_BLOCKS "Build example blocks" ON)
if(BUILD_BLOCKS)
    # Sensors
    add_subdirectory(blocks/sensors/adxl345)
    add_subdirectory(blocks/sensors/bme280)
    add_subdirectory(blocks/sensors/analog_input)
    add_subdirectory(blocks/sensors/gpio_input)
    add_subdirectory(blocks/sensors/synthetic_signal)

    # Processing
    add_subdirectory(blocks/processing/sliding_window)
    add_subdirectory(blocks/processing/channel_merge)
    add_subdirectory(blocks/processing/low_pass_filter)
    add_subdirectory(blocks/processing/normalize)

    # AI Models
    add_subdirectory(blocks/ai/timesnet_onnx)
    add_subdirectory(blocks/ai/decision_tree)

    # Outputs
    add_subdirectory(blocks/outputs/gpio_output)
    add_subdirectory(blocks/outputs/oled_display)
    add_subdirectory(blocks/outputs/pwm_output)
    add_subdirectory(blocks/outputs/mqtt_publisher)
    add_subdirectory(blocks/outputs/http_post)
    add_subdirectory(blocks/outputs/websocket)

    # Network/Web widgets
    add_subdirectory(blocks/network/web_button)
    add_subdirectory(blocks/network/web_led)
endif()

# Optional: Build tests
option(BUILD_TESTS "Build test programs" ON)
if(BUILD_TESTS AND NOT WIN32)
    # Skip tests on Windows (uses Linux-specific dlfcn.h)
    add_subdirectory(tests)
endif()

# Print build info
message(STATUS "========================================")
message(STATUS "  CiRA Block Runtime v${PROJECT_VERSION}")
message(STATUS "========================================")
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ compiler: ${CMAKE_CXX_COMPILER_ID}")
message(STATUS "Build blocks: ${BUILD_BLOCKS}")
message(STATUS "========================================")

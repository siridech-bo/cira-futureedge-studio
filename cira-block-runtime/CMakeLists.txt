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

# Runtime executable
add_executable(cira-block-runtime
    src/main.cpp
    src/manifest_parser.cpp
    src/block_loader.cpp
    src/block_executor.cpp
)

# Link libraries
if(UNIX)
    target_link_libraries(cira-block-runtime dl pthread)
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

# Optional: Build example blocks
option(BUILD_BLOCKS "Build example blocks" ON)
if(BUILD_BLOCKS)
    # Sensors
    add_subdirectory(blocks/sensors/adxl345)
    # TODO: add_subdirectory(blocks/sensors/bme280)

    # Processing
    add_subdirectory(blocks/processing/sliding_window)
    add_subdirectory(blocks/processing/channel_merge)
    # TODO: add_subdirectory(blocks/processing/low_pass_filter)

    # Models
    # TODO: add_subdirectory(blocks/models/timesnet)

    # Outputs
    add_subdirectory(blocks/outputs/gpio_output)
    # TODO: add_subdirectory(blocks/outputs/oled_display)
    # TODO: add_subdirectory(blocks/outputs/mqtt_publisher)
endif()

# Print build info
message(STATUS "========================================")
message(STATUS "  CiRA Block Runtime v${PROJECT_VERSION}")
message(STATUS "========================================")
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ compiler: ${CMAKE_CXX_COMPILER_ID}")
message(STATUS "Build blocks: ${BUILD_BLOCKS}")
message(STATUS "========================================")

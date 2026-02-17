cmake_minimum_required(VERSION 3.10)

# ADXL345 sensor block using libdriver
# Supports both I2C and SPI interfaces

# Source files
set(ADXL345_SOURCES
    adxl345_block.cpp
)

# Add libdriver sources (only on Linux)
if(UNIX AND NOT APPLE)
    list(APPEND ADXL345_SOURCES
        libdriver/src/driver_adxl345.c
        driver_adxl345_interface_linux.c
    )
endif()

# Build ADXL345 sensor block as shared library
add_library(adxl345-sensor-v2.0.0 SHARED
    ${ADXL345_SOURCES}
)

# Include directories
target_include_directories(adxl345-sensor-v2.0.0 PRIVATE
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/libdriver/src
    ${CMAKE_CURRENT_SOURCE_DIR}/libdriver/interface
)

# Compiler definitions
if(UNIX AND NOT APPLE)
    target_compile_definitions(adxl345-sensor-v2.0.0 PRIVATE
        __linux__
    )
endif()

# C++ standard
set_target_properties(adxl345-sensor-v2.0.0 PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
    C_STANDARD 99
    C_STANDARD_REQUIRED ON
)

# Remove 'lib' prefix from output filename
set_target_properties(adxl345-sensor-v2.0.0 PROPERTIES PREFIX "")

# Install to block library directory
install(TARGETS adxl345-sensor-v2.0.0
    LIBRARY DESTINATION /usr/local/lib/cira/blocks/
)

# Also keep v1.0.0 symlink for backwards compatibility
install(CODE "
    execute_process(
        COMMAND ${CMAKE_COMMAND} -E create_symlink
            adxl345-sensor-v2.0.0.so
            \$ENV{DESTDIR}/usr/local/lib/cira/blocks/adxl345-sensor-v1.0.0.so
    )
")

message(STATUS "Building ADXL345 sensor block v2.0.0 with libdriver")
message(STATUS "  - I2C support: enabled")
message(STATUS "  - SPI support: enabled")
message(STATUS "  - Features: tap detection, freefall, activity sensing")

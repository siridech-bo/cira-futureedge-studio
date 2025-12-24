cmake_minimum_required(VERSION 3.10)

# Build ADXL345 sensor block as shared library
add_library(adxl345-sensor-v1.0.0 SHARED
    adxl345_block.cpp
)

# Include runtime headers
target_include_directories(adxl345-sensor-v1.0.0 PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)

# Remove 'lib' prefix from output filename
set_target_properties(adxl345-sensor-v1.0.0 PROPERTIES PREFIX "")

# Install to block library directory
install(TARGETS adxl345-sensor-v1.0.0
    LIBRARY DESTINATION /usr/local/lib/cira/blocks/
)

message(STATUS "Building ADXL345 sensor block")

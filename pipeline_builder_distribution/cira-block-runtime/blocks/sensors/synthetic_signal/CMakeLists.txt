cmake_minimum_required(VERSION 3.10)

# Build SyntheticSignal sensor block as shared library
add_library(synthetic-signal-generator-v1.0.0 SHARED
    synthetic_signal_block.cpp
)

# Include runtime headers
target_include_directories(synthetic-signal-generator-v1.0.0 PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)

# Link against nlohmann_json (header-only library)
# Assuming nlohmann/json.hpp is available in system includes or vendor directory
find_package(nlohmann_json 3.2.0 QUIET)
if(nlohmann_json_FOUND)
    target_link_libraries(synthetic-signal-generator-v1.0.0 PRIVATE nlohmann_json::nlohmann_json)
else()
    # Fallback: include from common system paths or vendor
    target_include_directories(synthetic-signal-generator-v1.0.0 PRIVATE
        ${CMAKE_SOURCE_DIR}/vendor/nlohmann
        /usr/include
        /usr/local/include
    )
endif()

# Remove 'lib' prefix from output filename
set_target_properties(synthetic-signal-generator-v1.0.0 PROPERTIES PREFIX "")

# Install to block library directory
install(TARGETS synthetic-signal-generator-v1.0.0
    LIBRARY DESTINATION /usr/local/lib/cira/blocks/
)

message(STATUS "Building SyntheticSignal sensor block")

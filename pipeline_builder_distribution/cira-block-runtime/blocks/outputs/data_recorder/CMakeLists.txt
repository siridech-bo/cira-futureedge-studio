# Data Recorder Block
add_library(data-recorder-v1.0.0 SHARED
    data_recorder_block.cpp
)

target_include_directories(data-recorder-v1.0.0 PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)

target_compile_features(data-recorder-v1.0.0 PRIVATE cxx_std_17)

# Link experimental filesystem library for GCC < 9
target_link_libraries(data-recorder-v1.0.0 PRIVATE stdc++fs)

# Set output name to match block naming convention
set_target_properties(data-recorder-v1.0.0 PROPERTIES
    OUTPUT_NAME "data-recorder-v1.0.0"
    PREFIX ""
)

# Install to blocks directory at root level
install(TARGETS data-recorder-v1.0.0
    LIBRARY DESTINATION ${CMAKE_INSTALL_PREFIX}/blocks
)

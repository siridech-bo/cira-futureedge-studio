# Data Recorder Block
add_library(data_recorder SHARED
    data_recorder_block.cpp
)

target_include_directories(data_recorder PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)

target_compile_features(data_recorder PRIVATE cxx_std_17)

# Link experimental filesystem library for GCC < 9
target_link_libraries(data_recorder PRIVATE stdc++fs)

# Install to blocks directory
install(TARGETS data_recorder
    LIBRARY DESTINATION ${CMAKE_INSTALL_PREFIX}/blocks/outputs/data_recorder
)

cmake_minimum_required(VERSION 3.10)

add_library(sliding-window-v1.0.0 SHARED
    sliding_window_block.cpp
)

target_include_directories(sliding-window-v1.0.0 PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)

set_target_properties(sliding-window-v1.0.0 PROPERTIES PREFIX "")

install(TARGETS sliding-window-v1.0.0
    LIBRARY DESTINATION /usr/local/lib/cira/blocks/
)

message(STATUS "Building Sliding Window block")

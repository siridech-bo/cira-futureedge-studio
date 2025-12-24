cmake_minimum_required(VERSION 3.15)

add_library(websocket-v1.0.0 SHARED
    websocket_block.cpp
    websocket_block.hpp
)

target_include_directories(websocket-v1.0.0 PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)

target_link_libraries(websocket-v1.0.0 PRIVATE
)

set_target_properties(websocket-v1.0.0 PROPERTIES
    OUTPUT_NAME "websocket-v1.0.0"
    PREFIX ""
)

cmake_minimum_required(VERSION 3.10)

add_library(websocket-client-v1.0.0 SHARED
    websocket_block.cpp
    websocket_block.hpp
)

target_include_directories(websocket-client-v1.0.0 PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)

target_link_libraries(websocket-client-v1.0.0 PRIVATE
)

set_target_properties(websocket-client-v1.0.0 PROPERTIES
    OUTPUT_NAME "websocket-client-v1.0.0"
    PREFIX ""
)

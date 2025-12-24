cmake_minimum_required(VERSION 3.15)

add_library(http-post-v1.0.0 SHARED
    http_post_block.cpp
    http_post_block.hpp
)

target_include_directories(http-post-v1.0.0 PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)

target_link_libraries(http-post-v1.0.0 PRIVATE
)

set_target_properties(http-post-v1.0.0 PROPERTIES
    OUTPUT_NAME "http-post-v1.0.0"
    PREFIX ""
)

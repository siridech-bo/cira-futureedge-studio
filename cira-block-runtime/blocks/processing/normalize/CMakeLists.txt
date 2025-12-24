cmake_minimum_required(VERSION 3.15)

add_library(normalize-v1.0.0 SHARED
    normalize_block.cpp
    normalize_block.hpp
)

target_include_directories(normalize-v1.0.0 PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)

target_link_libraries(normalize-v1.0.0 PRIVATE
)

set_target_properties(normalize-v1.0.0 PROPERTIES
    OUTPUT_NAME "normalize-v1.0.0"
    PREFIX ""
)

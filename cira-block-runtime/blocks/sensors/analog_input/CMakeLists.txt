cmake_minimum_required(VERSION 3.15)

add_library(analog-input-v1.0.0 SHARED
    analog_input_block.cpp
    analog_input_block.hpp
)

target_include_directories(analog-input-v1.0.0 PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)

target_link_libraries(analog-input-v1.0.0 PRIVATE
)

set_target_properties(analog-input-v1.0.0 PROPERTIES
    OUTPUT_NAME "analog-input-v1.0.0"
    PREFIX ""
)

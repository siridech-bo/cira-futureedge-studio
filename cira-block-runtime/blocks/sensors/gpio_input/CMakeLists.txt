cmake_minimum_required(VERSION 3.15)

add_library(gpio-input-v1.0.0 SHARED
    gpio_input_block.cpp
    gpio_input_block.hpp
)

target_include_directories(gpio-input-v1.0.0 PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)

target_link_libraries(gpio-input-v1.0.0 PRIVATE
)

set_target_properties(gpio-input-v1.0.0 PROPERTIES
    OUTPUT_NAME "gpio-input-v1.0.0"
    PREFIX ""
)

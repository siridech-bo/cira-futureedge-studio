cmake_minimum_required(VERSION 3.15)

add_library(pwm-output-v1.0.0 SHARED
    pwm_output_block.cpp
    pwm_output_block.hpp
)

target_include_directories(pwm-output-v1.0.0 PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)

target_link_libraries(pwm-output-v1.0.0 PRIVATE
)

set_target_properties(pwm-output-v1.0.0 PROPERTIES
    OUTPUT_NAME "pwm-output-v1.0.0"
    PREFIX ""
)

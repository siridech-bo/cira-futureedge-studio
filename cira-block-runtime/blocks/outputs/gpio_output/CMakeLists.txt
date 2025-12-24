cmake_minimum_required(VERSION 3.10)

add_library(gpio-output-v1.0.0 SHARED
    gpio_output_block.cpp
)

target_include_directories(gpio-output-v1.0.0 PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)

set_target_properties(gpio-output-v1.0.0 PROPERTIES PREFIX "")

install(TARGETS gpio-output-v1.0.0
    LIBRARY DESTINATION /usr/local/lib/cira/blocks/
)

message(STATUS "Building GPIO Output block")

cmake_minimum_required(VERSION 3.15)

add_library(mqtt-publisher-v1.0.0 SHARED
    mqtt_publisher_block.cpp
    mqtt_publisher_block.hpp
)

target_include_directories(mqtt-publisher-v1.0.0 PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)

target_link_libraries(mqtt-publisher-v1.0.0 PRIVATE
)

set_target_properties(mqtt-publisher-v1.0.0 PROPERTIES
    OUTPUT_NAME "mqtt-publisher-v1.0.0"
    PREFIX ""
)

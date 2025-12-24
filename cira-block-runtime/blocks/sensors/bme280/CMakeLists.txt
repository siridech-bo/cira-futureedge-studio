add_library(bme280-sensor-v1.0.0 SHARED
    bme280_block.cpp
)

target_include_directories(bme280-sensor-v1.0.0 PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)


set_target_properties(bme280-sensor-v1.0.0 PROPERTIES
    OUTPUT_NAME "bme280-sensor-v1.0.0"
    PREFIX ""
)

add_library(oled-display-v1.1.0 SHARED
    oled_display_block.cpp
)

target_include_directories(oled-display-v1.1.0 PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)


# Set output name
set_target_properties(oled-display-v1.1.0 PROPERTIES
    OUTPUT_NAME "oled-display-v1.1.0"
    PREFIX ""
)

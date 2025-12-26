# Web LED Block - Virtual LED output on web dashboard

add_library(web-led-v1.0.0 SHARED
    web_led_block.cpp
)

target_include_directories(web-led-v1.0.0 PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)

set_target_properties(web-led-v1.0.0 PROPERTIES
    PREFIX ""
    SUFFIX ".so"
)

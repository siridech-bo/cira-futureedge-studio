# Web Button Block - Virtual GPIO input from web dashboard

add_library(web-button-v1.0.0 SHARED
    web_button_block.cpp
)

target_include_directories(web-button-v1.0.0 PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)

set_target_properties(web-button-v1.0.0 PROPERTIES
    PREFIX ""
    SUFFIX ".so"
)

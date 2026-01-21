add_library(timesnet-v1.2.0 SHARED
    timesnet_onnx_block.cpp
)

target_include_directories(timesnet-v1.2.0 PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)


# ONNX Runtime support (required for TimesNet inference on Linux/Jetson)
if(UNIX)
    target_compile_definitions(timesnet-v1.2.0 PRIVATE USE_ONNXRUNTIME)
    target_link_libraries(timesnet-v1.2.0 PRIVATE onnxruntime)
endif()

# Set output name
set_target_properties(timesnet-v1.2.0 PROPERTIES
    OUTPUT_NAME "timesnet-v1.2.0"
    PREFIX ""
)

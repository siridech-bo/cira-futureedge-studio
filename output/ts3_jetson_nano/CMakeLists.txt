cmake_minimum_required(VERSION 3.10)
project(ts3_jetson_nano VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ONNX Runtime - Manual configuration
# You can set ONNXRUNTIME_ROOT to your ONNX Runtime installation path
if(NOT DEFINED ONNXRUNTIME_ROOT)
    set(ONNXRUNTIME_ROOT "/usr/local" CACHE PATH "ONNX Runtime installation directory")
endif()

# Find ONNX Runtime headers and libraries
find_path(ONNXRUNTIME_INCLUDE_DIR
    NAMES onnxruntime_cxx_api.h
    PATHS ${ONNXRUNTIME_ROOT}/include ${ONNXRUNTIME_ROOT}/include/onnxruntime
    NO_DEFAULT_PATH
)

find_library(ONNXRUNTIME_LIBRARY
    NAMES onnxruntime
    PATHS ${ONNXRUNTIME_ROOT}/lib ${ONNXRUNTIME_ROOT}/lib64
    NO_DEFAULT_PATH
)

if(ONNXRUNTIME_INCLUDE_DIR AND ONNXRUNTIME_LIBRARY)
    message(STATUS "Found ONNX Runtime: ${ONNXRUNTIME_LIBRARY}")
    message(STATUS "ONNX Runtime include: ${ONNXRUNTIME_INCLUDE_DIR}")
else()
    message(FATAL_ERROR "ONNX Runtime not found. Please install ONNX Runtime or set ONNXRUNTIME_ROOT")
endif()

add_executable(inference src/main.cpp)
target_include_directories(inference PRIVATE ${ONNXRUNTIME_INCLUDE_DIR})
target_link_libraries(inference PRIVATE ${ONNXRUNTIME_LIBRARY})

# Install
install(TARGETS inference DESTINATION bin)

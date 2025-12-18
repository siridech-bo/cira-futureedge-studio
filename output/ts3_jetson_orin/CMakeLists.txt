cmake_minimum_required(VERSION 3.15)
project(ts3_jetson_orin VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find ONNX Runtime
find_package(onnxruntime REQUIRED)

add_executable(inference src/main.cpp)
target_link_libraries(inference PRIVATE onnxruntime)

# Install
install(TARGETS inference DESTINATION bin)

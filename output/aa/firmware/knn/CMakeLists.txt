cmake_minimum_required(VERSION 3.15)

# Project
project(CiRAFirmware C CXX)

# Platform: cortex-m4
set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR cortex-m4)

# Toolchain
set(CMAKE_C_COMPILER arm-none-eabi-gcc)
set(CMAKE_CXX_COMPILER arm-none-eabi-g++)
set(CMAKE_SIZE arm-none-eabi-size)
set(CMAKE_OBJCOPY arm-none-eabi-objcopy)

# Compiler flags
set(CMAKE_C_FLAGS "-Os -Wall -Wextra")
set(CMAKE_CXX_FLAGS "-Os -Wall -Wextra -std=c++11")

# Platform-specific flags
if("cortex-m4" MATCHES "cortex-m")
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -mcpu=cortex-m4 -mthumb -mfloat-abi=soft")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -mcpu=cortex-m4 -mthumb -mfloat-abi=soft")
endif()

# Include directories
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
)

# Source files
set(SOURCES
    main.cpp
    anomaly_detector.cpp
    features.cpp
)

# Executable
add_executable(firmware.elf ${SOURCES})

# Link options
target_link_libraries(firmware.elf m)

# Generate binary and hex files
add_custom_command(TARGET firmware.elf POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} -O binary firmware.elf firmware.bin
    COMMAND ${CMAKE_OBJCOPY} -O ihex firmware.elf firmware.hex
    COMMAND ${CMAKE_SIZE} firmware.elf
    COMMENT "Generating binary and hex files..."
)

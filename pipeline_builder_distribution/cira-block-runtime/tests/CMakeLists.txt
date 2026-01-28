cmake_minimum_required(VERSION 3.15)

# Test executable
add_executable(test_all_blocks test_all_blocks.cpp)

target_include_directories(test_all_blocks PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)

target_link_libraries(test_all_blocks PRIVATE
    ${CMAKE_DL_LIBS}
)

# On Windows, use .dll extension
if(WIN32)
    target_compile_definitions(test_all_blocks PRIVATE WINDOWS_BUILD)
endif()

# Copy test executable to build directory for easy access
install(TARGETS test_all_blocks
    RUNTIME DESTINATION bin
)

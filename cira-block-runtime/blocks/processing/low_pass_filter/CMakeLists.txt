add_library(low-pass-filter-v1.0.0 SHARED low_pass_filter_block.cpp)
target_include_directories(low-pass-filter-v1.0.0 PRIVATE ${CMAKE_SOURCE_DIR}/include)
set_target_properties(low-pass-filter-v1.0.0 PROPERTIES OUTPUT_NAME "low-pass-filter-v1.0.0" PREFIX "")

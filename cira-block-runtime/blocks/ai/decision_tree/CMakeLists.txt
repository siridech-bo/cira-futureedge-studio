cmake_minimum_required(VERSION 3.15)

add_library(decision-tree-v1.0.0 SHARED
    decision_tree_block.cpp
    decision_tree_block.hpp
)

target_include_directories(decision-tree-v1.0.0 PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)

target_link_libraries(decision-tree-v1.0.0 PRIVATE
)

set_target_properties(decision-tree-v1.0.0 PROPERTIES
    OUTPUT_NAME "decision-tree-v1.0.0"
    PREFIX ""
)

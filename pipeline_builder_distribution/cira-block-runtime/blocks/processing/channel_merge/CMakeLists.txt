cmake_minimum_required(VERSION 3.10)

add_library(channel-merge-v1.0.0 SHARED
    channel_merge_block.cpp
)

target_include_directories(channel-merge-v1.0.0 PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)

set_target_properties(channel-merge-v1.0.0 PROPERTIES PREFIX "")

install(TARGETS channel-merge-v1.0.0
    LIBRARY DESTINATION /usr/local/lib/cira/blocks/
)

message(STATUS "Building Channel Merge block")

cmake_minimum_required(VERSION 3.13)
# Toolchain smoke test (F-000 CA4): the on-board LED blinks. Built with tools/build blink.
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)
project(blink C CXX ASM)
set(CMAKE_C_STANDARD 11)
pico_sdk_init()
add_executable(blink blink.c)
target_link_libraries(blink pico_stdlib)
pico_add_extra_outputs(blink)

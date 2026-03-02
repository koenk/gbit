cmake_minimum_required(VERSION 3.16)

project(gbit C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS ON)

add_library(gbitlib SHARED
    lib/tester.c
    lib/inputstate.c
    lib/ref_cpu.c
    lib/disassembler.c
)

target_include_directories(gbitlib
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}
)

set_target_properties(gbitlib PROPERTIES
    OUTPUT_NAME gbit
)

if(MSVC)
    target_compile_options(gbitlib PRIVATE /W4)
    set_target_properties(gbitlib PROPERTIES
        WINDOWS_EXPORT_ALL_SYMBOLS ON
    )
else()
    target_compile_options(gbitlib PRIVATE -Wall -Wextra)
endif()

add_executable(gbit
    main.c
    test_cpu.c
)

target_include_directories(gbit
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
)

if(MSVC)
    target_compile_definitions(gbit PRIVATE GBIT_NO_GETOPT=1)
    target_compile_options(gbit PRIVATE /W4)
else()
    target_compile_options(gbit PRIVATE -Wall -Wextra)
endif()

target_link_libraries(gbit PRIVATE gbitlib)

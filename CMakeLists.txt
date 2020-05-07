cmake_minimum_required(VERSION 3.16)
project(plox)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_C_FLAGS_RELEASE -Os)

include_directories(clox)

add_executable(clox
        clox/main.c
        clox/chunk.c
        clox/memory.c
        clox/debug.c
        clox/value.c
        clox/vm.c
        clox/compiler.c
        clox/scanner.c
        clox/object.c
        clox/table.c
        )

add_executable(fib tool/fib.c)

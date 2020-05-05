#ifndef clox_common_h
#define clox_common_h

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

//#define DEBUG_PRINT_CODE

//#define DEBUG_TRACE_EXECUTION

#define UINT8_COUNT (UINT8_MAX + 1)

static void startErrorRed() {
    fprintf(stderr, "\x1b[38;5;1m");
}

static void endErrorRed() {
    fprintf(stderr, "\x1b[0m");
}

#endif
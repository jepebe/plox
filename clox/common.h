#ifndef clox_common_h
#define clox_common_h

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

//#define DEBUG_PRINT_CODE

#define DEBUG_TRACE_EXECUTION

static void startErrorRed() {
    fprintf(stderr, "\x1b[31m");
}

static void endErrorRed() {
    fprintf(stderr, "\x1b[0m");
}

#endif
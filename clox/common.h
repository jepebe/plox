#ifndef clox_common_h
#define clox_common_h

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

//#define DEBUG_PRINT_CODE
//#define DEBUG_TRACE_EXECUTION
//#define DEBUG_STRESS_GC
//#define DEBUG_LOG_GC
//#define DEBUG_SUMMARY_GC

#define UINT8_COUNT (UINT8_MAX + 1)

static void startErrorRed() {
    fprintf(stderr, "\x1b[38;5;1m");
}

static void startWarningYellow() {
    fprintf(stderr, "\x1b[38;5;226m");
}

static void endColor() {
    fprintf(stderr, "\x1b[0m");
}

#endif
#include <stdio.h>

#include "debug.h"
#include "value.h"

void disassembleChunk(Chunk *chunk, const char *name) {
    printf("== %s ==\n", name);

    for (int offset = 0; offset < chunk->count;) {
        offset = disassembleInstruction(chunk, offset);
    }
}

static int constantInstruction(const char *name, Chunk *chunk, int offset,
                               bool long_const) {
    int index;
    int offset_skip;

    if (long_const == true) {
        uint32_t b = chunk->code[offset + 1];
        b = (b << 8u) | chunk->code[offset + 2];
        b = (b << 8u) | chunk->code[offset + 3];
        index = b;
        offset_skip = 4;
    } else {
        index = chunk->code[offset + 1];
        offset_skip = 2;
    }

    printf("%-16s %4d '", name, index);
    printValue(chunk->constants.values[index]);
    printf("'\n");
    return offset + offset_skip;
}

static int simpleInstruction(const char *name, int offset) {
    printf("%s\n", name);
    return offset + 1;
}

int disassembleInstruction(Chunk *chunk, int offset) {
    printf("%04d ", offset);
    if (offset > 0 && getLine(chunk, offset) == getLine(chunk, offset - 1)) {
        printf("   | ");
    } else {
        printf("%4d ", getLine(chunk, offset));
    }

    uint8_t instruction = chunk->code[offset];
    switch (instruction) {
        case OP_CONSTANT:
            return constantInstruction("OP_CONSTANT", chunk, offset, false);
        case OP_CONSTANT_LONG:
            return constantInstruction("OP_CONSTANT_LONG", chunk, offset, true);
        case OP_ADD:
            return simpleInstruction("OP_ADD", offset);
        case OP_SUBTRACT:
            return simpleInstruction("OP_SUBTRACT", offset);
        case OP_MULTIPLY:
            return simpleInstruction("OP_MULTIPLY", offset);
        case OP_DIVIDE:
            return simpleInstruction("OP_DIVIDE", offset);
        case OP_NEGATE:
            return simpleInstruction("OP_NEGATE", offset);
        case OP_RETURN:
            return simpleInstruction("OP_RETURN", offset);
        default:
            printf("Unknown opcode %d\n", instruction);
            return offset + 1;
    }
}

#include <stdlib.h>

#include "chunk.h"
#include "memory.h"

void initChunk(Chunk *chunk) {
    chunk->count = 0;
    chunk->capacity = 0;
    chunk->code = NULL;
    chunk->line_count = 0;
    chunk->line_count_capacity = 0;
    chunk->lines = NULL;
    initValueArray(&chunk->constants);
}

void freeChunk(Chunk *chunk) {
    FREE_ARRAY(uint8_t, chunk->code, chunk->capacity);
    FREE_ARRAY(int, chunk->lines, chunk->capacity);
    freeValueArray(&chunk->constants);
    initChunk(chunk);
}

void encodeLine(Chunk *chunk, int line) {
    if (chunk->line_count == 0 || chunk->lines[(chunk->line_count - 1) * 2] != line) {
        if (chunk->line_count_capacity < chunk->line_count + 1) {
            int oldCapacity = chunk->line_count_capacity;
            chunk->line_count_capacity = GROW_CAPACITY(oldCapacity);
            chunk->lines = GROW_ARRAY(chunk->lines, int,
                                      oldCapacity, chunk->line_count_capacity);
        }

        chunk->line_count++;

        int line_index = chunk->line_count - 1;
        chunk->lines[line_index * 2] = line;
        chunk->lines[line_index * 2 + 1] = 1;

    } else {
        int line_index = chunk->line_count - 1;
        chunk->lines[line_index * 2 + 1]++;
    }
}

void writeChunk(Chunk *chunk, uint8_t byte, int line) {
    if (chunk->capacity < chunk->count + 1) {
        int oldCapacity = chunk->capacity;
        chunk->capacity = GROW_CAPACITY(oldCapacity);
        chunk->code = GROW_ARRAY(chunk->code, uint8_t, oldCapacity,
                                 chunk->capacity);
    }

    chunk->code[chunk->count] = byte;
    encodeLine(chunk, line);
    chunk->count++;
}

int addConstant(Chunk* chunk, Value value) {
    writeValueArray(&chunk->constants, value);
    return chunk->constants.count - 1;
}

int getLine(Chunk *chunk, int offset) {
    int index = 0;
    int line = chunk->lines[index];
    int rle_pointer = chunk->lines[index + 1];
    while(rle_pointer <= offset) {
        index += 2;
        line = chunk->lines[index];
        rle_pointer += chunk->lines[index + 1];
    }
    return line;
}

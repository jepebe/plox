#include "common.h"
#include "chunk.h"
#include "debug.h"

int main(int argc, const char* argv[]) {
    Chunk chunk;
    initChunk(&chunk);

    for(int i = 0; i < 512; i++) {
        writeConstant(&chunk, 1.2 * i, i);
        writeConstant(&chunk, 99 * i, i);
        writeChunk(&chunk, OP_RETURN, i);
    }

    disassembleChunk(&chunk, "test chunk");
    freeChunk(&chunk);
    return 0;
}
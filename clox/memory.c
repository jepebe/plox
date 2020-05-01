#include <stdlib.h>

#include "common.h"
#include "memory.h"
#include "vm.h"

void* reallocate(void* previous, size_t oldSize, size_t newSize) {
    if (newSize == 0) {
        free(previous);
        return NULL;
    }

    return realloc(previous, newSize);
}

static void freeObject(Obj* object) {
    switch (object->type) {
        case OBJ_STRING: {
            FREE(ObjString, object);
            break;
        }
    }
}

void freeObjects() {
    Obj* object = vm.objects;
    while (object != NULL) {
        Obj* next = object->next;
        freeObject(object);
        object = next;
    }
}

#include <stdio.h>
#include <string.h>

#include "memory.h"
#include "object.h"
#include "value.h"
#include "vm.h"

#define ALLOCATE_OBJ(type, objectType, data_type, size) \
    (type*)allocateObject(sizeof(type) + size * sizeof(data_type), objectType)

static Obj* allocateObject(size_t size, ObjType type) {
    Obj* object = (Obj*)reallocate(NULL, 0, size);
    object->type = type;
    object->next = vm.objects;
    vm.objects = object;
    return object;
}

ObjString *createString(int length) {
    ObjString* string = ALLOCATE_OBJ(ObjString, OBJ_STRING, char, length + 1);
    string->length = length;
    string->chars[length] = '\0';
    return string;
}

ObjString* copyString(const char* chars, int length) {
    ObjString* copy = createString(length);
    memcpy(copy->chars, chars, length);
    return copy;
}

void printObject(Value value) {
    switch (OBJ_TYPE(value)) {
        case OBJ_STRING:
            printf("%s", AS_CSTRING(value));
            break;
    }
}

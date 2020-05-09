#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

#include "common.h"
#include "vm.h"
#include "debug.h"
#include "compiler.h"
#include "memory.h"
#include "object.h"

VM vm;

static Value clockNative(int argCount, Value* args) {
    return NUMBER_VAL((double) clock() / CLOCKS_PER_SEC);
}

static Value printGlobals(int argc, Value* args) {
    for (int i = 0; i < vm.globals.capacity; i++) {
        Entry entry = vm.globals.entries[i];
        if (entry.key == NULL) continue;
        Value obj = (OBJ_VAL(&entry.value));
        printf("[%s %s] ", entry.key->chars, nameType(OBJ_TYPE(obj)));
    }
    printf("\n");
    return NIL_VAL;
}

static Value utf8Length(int argc, Value* args) {
    if(argc == 1 && IS_STRING(args[0])) {
        ObjString *string = AS_STRING(args[0]);
        size_t len = 0;
        char* s = string->chars;
        for (; *s; ++s) if ((*s & 0xC0) != 0x80) ++len;
        return NUMBER_VAL(len);
    }
    return NUMBER_VAL(-1);
}

static Value bytesLength(int argc, Value* args) {
    if(argc == 1 && IS_STRING(args[0])) {
        ObjString *string = AS_STRING(args[0]);
        return NUMBER_VAL(string->length);
        //return NUMBER_VAL(strlen(string->chars));
    }
    return NUMBER_VAL(-1);
}

static void resetStack() {
    vm.stackTop = vm.stack;
    vm.frameCount = 0;
    vm.openUpvalues = NULL;
}

static void runtimeError(const char *format, ...) {
    startErrorRed();

    CallFrame* frame = &vm.frames[vm.frameCount - 1];
    size_t instruction = frame->ip - frame->closure->function->chunk.code - 1;
    int line = frame->closure->function->chunk.lines[instruction];
    fprintf(stderr, "[RuntimeError at line %d] ", line);

    va_list args;
    va_start(args, format);
    vfprintf(stderr, format, args);
    va_end(args);

    endColor();

    fputs("\n", stderr);

    for (int i = vm.frameCount - 1; i >= 0; i--) {
        frame = &vm.frames[i];
        ObjFunction* function = frame->closure->function;
        // -1 because the IP is sitting on the next instruction to be
        // executed.
        instruction = frame->ip - function->chunk.code - 1;
        line = function->chunk.lines[instruction];
        fprintf(stderr, "[line %d] in ", line);
        if (function->name == NULL) {
            fprintf(stderr, "script\n");
        } else {
            fprintf(stderr, "%s()\n", function->name->chars);
        }
    }

    resetStack();
}

static void defineNative(const char* name, NativeFn function) {
    push(OBJ_VAL(copyString(name, (int)strlen(name))));
    push(OBJ_VAL(newNative(function)));
    tableSet(&vm.globals, AS_STRING(vm.stack[0]), vm.stack[1]);
    pop();
    pop();
}

void initVM() {
    resetStack();
    vm.objects = NULL;
    vm.bytesAllocated = 0;
    vm.nextGC = 1024 * 1024;

    vm.grayCount = 0;
    vm.grayCapacity = 0;
    vm.grayStack = NULL;

    initTable(&vm.globals);
    initTable(&vm.strings);

    vm.initString = NULL;
    vm.initString = copyString("init", 4);

    defineNative("clock", clockNative);
    defineNative("printGlobals", printGlobals);
    defineNative("len", utf8Length);
    defineNative("blen", bytesLength);
}

void freeVM() {
    freeTable(&vm.globals);
    freeTable(&vm.strings);
    vm.initString = NULL;
    freeObjects();
}

void push(Value value) {
    *vm.stackTop = value;
    vm.stackTop++;
}

Value pop() {
    vm.stackTop--;
    return *vm.stackTop;
}

static Value peek(int distance) {
    return vm.stackTop[-1 - distance];
}

static bool call(ObjClosure* closure, int argCount) {
    if (argCount != closure->function->arity) {
        runtimeError("Expected %d arguments but got %d.",
                     closure->function->arity, argCount);
        return false;
    }

    if (vm.frameCount == FRAMES_MAX) {
        runtimeError("Stack overflow.");
        return false;
    }

    CallFrame* frame = &vm.frames[vm.frameCount++];
    frame->closure = closure;
    frame->ip = closure->function->chunk.code;

    frame->slots = vm.stackTop - argCount - 1;
    return true;
}

static bool callValue(Value callee, int argCount) {
    if (IS_OBJ(callee)) {
        switch (OBJ_TYPE(callee)) {
            case OBJ_BOUND_METHOD: {
                ObjBoundMethod* bound = AS_BOUND_METHOD(callee);
                vm.stackTop[-argCount - 1] = bound->receiver;
                return call(bound->method, argCount);
            }
            case OBJ_CLOSURE:
                return call(AS_CLOSURE(callee), argCount);
            case OBJ_CLASS: {
                ObjClass* klass = AS_CLASS(callee);
                vm.stackTop[-argCount - 1] = OBJ_VAL(newInstance(klass));
                Value initializer;
                if (tableGet(&klass->methods, vm.initString, &initializer)) {
                    return call(AS_CLOSURE(initializer), argCount);
                } else if (argCount != 0) {
                    runtimeError("Expected 0 arguments but got %d.", argCount);
                    return false;
                }
                return true;
            }
            case OBJ_NATIVE: {
                NativeFn native = AS_NATIVE(callee);
                Value result = native(argCount, vm.stackTop - argCount);
                vm.stackTop -= argCount + 1;
                push(result);
                return true;
            }
            default:
                // Non-callable object type.
                break;
        }
    }
    runtimeError("Can only call functions and classes.");
    return false;
}

static bool invokeFromClass(ObjClass* klass, ObjString* name, int argCount) {
    Value method;
    if (!tableGet(&klass->methods, name, &method)) {
        runtimeError("Undefined property '%s'.", name->chars);
        return false;
    }

    return call(AS_CLOSURE(method), argCount);
}

static bool invoke(ObjString* name, int argCount) {
    Value receiver = peek(argCount);

    if (!IS_INSTANCE(receiver)) {
        runtimeError("Only instances have methods.");
        return false;
    }

    ObjInstance* instance = AS_INSTANCE(receiver);

    Value value;
    if (tableGet(&instance->fields, name, &value)) {
        vm.stackTop[-argCount - 1] = value;
        return callValue(value, argCount);
    }

    return invokeFromClass(instance->klass, name, argCount);
}

static bool bindMethod(ObjClass* klass, ObjString* name) {
    Value method;
    if (!tableGet(&klass->methods, name, &method)) {
        runtimeError("Undefined property '%s'.", name->chars);
        return false;
    }

    ObjBoundMethod* bound = newBoundMethod(peek(0), AS_CLOSURE(method));
    pop();
    push(OBJ_VAL(bound));
    return true;
}

static ObjUpvalue* captureUpvalue(Value* local) {
    ObjUpvalue* prevUpvalue = NULL;
    ObjUpvalue* upvalue = vm.openUpvalues;

    while (upvalue != NULL && upvalue->location > local) {
        prevUpvalue = upvalue;
        upvalue = upvalue->next;
    }

    if (upvalue != NULL && upvalue->location == local) return upvalue;

    ObjUpvalue* createdUpvalue = newUpvalue(local);
    createdUpvalue->next = upvalue;

    if (prevUpvalue == NULL) {
        vm.openUpvalues = createdUpvalue;
    } else {
        prevUpvalue->next = createdUpvalue;
    }

    return createdUpvalue;
}

static void closeUpvalues(Value* last) {
    while (vm.openUpvalues != NULL && vm.openUpvalues->location >= last) {
        ObjUpvalue* upvalue = vm.openUpvalues;
        upvalue->closed = *upvalue->location;
        upvalue->location = &upvalue->closed;
        vm.openUpvalues = upvalue->next;
    }
}

static void defineMethod(ObjString* name) {
    Value method = peek(0);
    ObjClass* klass = AS_CLASS(peek(1));
    tableSet(&klass->methods, name, method);
    pop();
}

static bool isFalsey(Value value) {
    return IS_NIL(value) || (IS_BOOL(value) && !AS_BOOL(value));
}

static inline void print_trace_execution(CallFrame* frame) {
    printf("          ");
    for (Value *slot = vm.stack; slot < vm.stackTop; slot++) {
        printf("[ ");
        printValue(*slot);
        printf(" ]");
    }
    printf("\n");
    disassembleInstruction(&frame->closure->function->chunk,
                           (int)(frame->ip - frame->closure->function->chunk.code));
}

static inline uint8_t read_byte(CallFrame* frame) {
    return *frame->ip++;
}

static inline uint16_t read_short(CallFrame* frame) {
    frame->ip += 2;
    return (uint16_t)(((unsigned) frame->ip[-2] << 8u) | frame->ip[-1]);
}

static inline Value read_constant(CallFrame* frame) {
    return frame->closure->function->chunk.constants.values[read_byte(frame)];
}

static inline ObjString* read_string(CallFrame* frame) {
    return AS_STRING(read_constant(frame));
}

static ObjString* concatenate(ObjString *a, ObjString * b) {
    int length = a->length + b->length;
    char* chars = ALLOCATE(char, length + 1);
    memcpy(chars, a->chars, a->length);
    memcpy(chars + a->length, b->chars, b->length);
    chars[length] = '\0';

    ObjString* result = takeString(chars, length);
    return result;
}

static inline InterpretResult coerce_and_concatenate_string() {
    char buffer[50];
    ObjString *a;
    ObjString *b;

    if (IS_STRING(peek(0))) {
        b = AS_STRING(pop());
    } else if(IS_NUMBER(peek(0))) {
        double val = AS_NUMBER(pop());
        int length = sprintf(buffer, "%g", val);
        b = copyString(buffer, length);
    } else {
        runtimeError("Operands must be numbers or strings.");
        return INTERPRET_RUNTIME_ERROR;
    }

    if (IS_STRING(peek(0))) {
        a = AS_STRING(pop());
    } else if(IS_NUMBER(peek(0))) {
        double val = AS_NUMBER(pop());
        int length = sprintf(buffer, "%g", val);
        a = copyString(buffer, length);
    } else {
        runtimeError("Operands must be numbers or strings.");
        return INTERPRET_RUNTIME_ERROR;
    }
    push(OBJ_VAL(a));
    push(OBJ_VAL(b));
    ObjString * result = concatenate(a, b);
    pop();
    pop();
    push(OBJ_VAL(result));
    return INTERPRET_OK;
}

static inline InterpretResult binary_op(char op) {
    if (!IS_NUMBER(peek(0)) || !IS_NUMBER(peek(1))) {
        runtimeError("Operands must be numbers.");
        return INTERPRET_RUNTIME_ERROR;
    }

    double b = AS_NUMBER(pop());
    double a = AS_NUMBER(pop());
    Value value;
    switch(op) {
        case '+':
            value = NUMBER_VAL(a + b);
            break;
        case '-':
            value = NUMBER_VAL(a - b);
            break;
        case '*':
            value = NUMBER_VAL(a * b);
            break;
        case '/':
            value = NUMBER_VAL(a / b);
            break;
        case '<':
            value = BOOL_VAL(a < b);
            break;
        case '>':
            value = BOOL_VAL(a > b);
            break;
        default:
            runtimeError("Unknown operator '%s'", op);
            return INTERPRET_RUNTIME_ERROR;
    }
    push(value);
    return INTERPRET_OK;
}

static InterpretResult run() {
    CallFrame* frame = &vm.frames[vm.frameCount - 1];


    for (;;) {
#ifdef DEBUG_TRACE_EXECUTION
        print_trace_execution(frame);
#endif
        InterpretResult op_result = INTERPRET_OK;
        uint8_t instruction;
        switch (instruction = read_byte(frame)) {
            case OP_CONSTANT: {
                Value constant = read_constant(frame);
                push(constant);
                break;
            }
            case OP_NIL: push(NIL_VAL); break;
            case OP_TRUE: push(BOOL_VAL(true)); break;
            case OP_FALSE: push(BOOL_VAL(false)); break;
            case OP_POP: pop(); break;
            case OP_GET_LOCAL: {
                uint8_t slot = read_byte(frame);
                push(frame->slots[slot]);
                break;
            }
            case OP_GET_GLOBAL: {
                ObjString* name = read_string(frame);
                Value value;
                if (!tableGet(&vm.globals, name, &value)) {
                    runtimeError("Undefined variable '%s'.", name->chars);
                    op_result = INTERPRET_RUNTIME_ERROR;
                } else {
                    push(value);
                }
                break;
            }
            case OP_DEFINE_GLOBAL: {
                ObjString* name = read_string(frame);
                tableSet(&vm.globals, name, peek(0));
                pop();
                break;
            }
            case OP_SET_GLOBAL: {
                ObjString* name = read_string(frame);
                if (tableSet(&vm.globals, name, peek(0))) {
                    tableDelete(&vm.globals, name);
                    runtimeError("Undefined variable '%s'.", name->chars);
                    op_result = INTERPRET_RUNTIME_ERROR;
                }
                break;
            }
            case OP_SET_LOCAL: {
                uint8_t slot = read_byte(frame);
                frame->slots[slot] = peek(0);
                break;
            }
            case OP_GET_UPVALUE: {
                uint8_t slot = read_byte(frame);
                push(*frame->closure->upvalues[slot]->location);
                break;
            }
            case OP_SET_UPVALUE: {
                uint8_t slot = read_byte(frame);
                *frame->closure->upvalues[slot]->location = peek(0);
                break;
            }
            case OP_GET_PROPERTY: {
                if (!IS_INSTANCE(peek(0))) {
                    runtimeError("Only instances have properties.");
                    op_result = INTERPRET_RUNTIME_ERROR;
                    break;
                }
                ObjInstance* instance = AS_INSTANCE(peek(0));
                ObjString* name = read_string(frame);

                Value value;
                if (tableGet(&instance->fields, name, &value)) {
                    pop(); // Instance.
                    push(value);
                    break;
                }
                if (!bindMethod(instance->klass, name)) {
                    op_result = INTERPRET_RUNTIME_ERROR;
                }
                break;
            }
            case OP_SET_PROPERTY: {
                if (!IS_INSTANCE(peek(1))) {
                    runtimeError("Only instances have fields.");
                    op_result = INTERPRET_RUNTIME_ERROR;
                    break;
                }
                ObjInstance* instance = AS_INSTANCE(peek(1));
                tableSet(&instance->fields, read_string(frame), peek(0));

                Value value = pop();
                pop();
                push(value);
                break;
            }
            case OP_EQUAL: {
                Value b = pop();
                Value a = pop();
                push(BOOL_VAL(valuesEqual(a, b)));
                break;
            }
            case OP_GREATER: {
                op_result = binary_op('>');
                break;
            }
            case OP_LESS: {
                op_result = binary_op('<');
                break;
            }
            case OP_ADD: {
                if (IS_STRING(peek(0)) || IS_STRING(peek(1))) {
                    op_result = coerce_and_concatenate_string();
                } else if (IS_NUMBER(peek(0)) && IS_NUMBER(peek(1))) {
                    op_result = binary_op('+');
                } else {
                    runtimeError("Operands must be two numbers or two strings.");
                    op_result = INTERPRET_RUNTIME_ERROR;
                }
                break;
            }
            case OP_SUBTRACT: {
                op_result = binary_op('-');
                break;
            }
            case OP_MULTIPLY: {
                op_result = binary_op('*');
                break;
            }
            case OP_DIVIDE: {
                op_result = binary_op('/');
                break;
            }
            case OP_NOT: {
                push(BOOL_VAL(isFalsey(pop())));
                break;
            }
            case OP_NEGATE: {
                if (!IS_NUMBER(peek(0))) {
                    runtimeError("Operand must be a number.");
                    op_result = INTERPRET_RUNTIME_ERROR;
                } else {
                    push(NUMBER_VAL(-AS_NUMBER(pop())));
                }
                break;
            }
            case OP_PRINT: {
                printValue(pop());
                printf("\n");
                break;
            }
            case OP_JUMP: {
                uint16_t offset = read_short(frame);
                frame->ip += offset;
                break;
            }
            case OP_JUMP_IF_FALSE: {
                uint16_t offset = read_short(frame);
                if (isFalsey(peek(0))) frame->ip += offset;
                break;
            }
            case OP_LOOP: {
                uint16_t offset = read_short(frame);
                frame->ip -= offset;
                break;
            }
            case OP_CALL: {
                int argCount = read_byte(frame);
                if (!callValue(peek(argCount), argCount)) {
                    op_result = INTERPRET_RUNTIME_ERROR;
                } else {
                    frame = &vm.frames[vm.frameCount - 1];
                }
                break;
            }
            case OP_INVOKE: {
                ObjString* method = read_string(frame);
                int argCount = read_byte(frame);
                if (!invoke(method, argCount)) {
                    op_result = INTERPRET_RUNTIME_ERROR;
                } else {
                    frame = &vm.frames[vm.frameCount - 1];
                }
                break;
            }
            case OP_CLOSURE: {
                ObjFunction* function = AS_FUNCTION(read_constant(frame));
                ObjClosure* closure = newClosure(function);
                push(OBJ_VAL(closure));
                for (int i = 0; i < closure->upvalueCount; i++) {
                    uint8_t isLocal = read_byte(frame);
                    uint8_t index = read_byte(frame);
                    if (isLocal) {
                        closure->upvalues[i] = captureUpvalue(frame->slots + index);
                    } else {
                        closure->upvalues[i] = frame->closure->upvalues[index];
                    }
                }
                break;
            }
            case OP_CLOSE_UPVALUE:
                closeUpvalues(vm.stackTop - 1);
                pop();
                break;
            case OP_RETURN: {
                Value result = pop();

                closeUpvalues(frame->slots);

                vm.frameCount--;
                if (vm.frameCount == 0) {
                    pop();
                    return INTERPRET_OK;
                }

                vm.stackTop = frame->slots;
                push(result);

                frame = &vm.frames[vm.frameCount - 1];
                break;
            }
            case OP_CLASS:
                push(OBJ_VAL(newClass(read_string(frame))));
                break;
            case OP_METHOD:
                defineMethod(read_string(frame));
                break;
        }

        if(op_result != INTERPRET_OK) {
            return op_result;
        }
    }
}

InterpretResult interpret(const char *source) {
    ObjFunction* function = compile(source);
    if (function == NULL) return INTERPRET_COMPILE_ERROR;

    push(OBJ_VAL(function));
    ObjClosure* closure = newClosure(function);
    pop();
    push(OBJ_VAL(closure));
    callValue(OBJ_VAL(closure), 0);

    return run();
}
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
    initTable(&vm.globals);
    initTable(&vm.strings);

    defineNative("clock", clockNative);
}

void freeVM() {
    freeTable(&vm.globals);
    freeTable(&vm.strings);
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
            case OBJ_CLOSURE:
                return call(AS_CLOSURE(callee), argCount);
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

static bool isFalsey(Value value) {
    return IS_NIL(value) || (IS_BOOL(value) && !AS_BOOL(value));
}

static void concatenate(ObjString *a, ObjString * b) {
    int length = a->length + b->length;
    char* chars = ALLOCATE(char, length + 1);
    memcpy(chars, a->chars, a->length);
    memcpy(chars + a->length, b->chars, b->length);
    chars[length] = '\0';

    ObjString* result = takeString(chars, length);

    push(OBJ_VAL(result));
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

static inline InterpretResult binary_op(char op, CallFrame* __unused frame) {
    if (!IS_NUMBER(peek(0)) || !IS_NUMBER(peek(1))) {
        runtimeError("Operands must be numbers.");
        return INTERPRET_RUNTIME_ERROR;
    }

    double b = AS_NUMBER(pop());
    double a = AS_NUMBER(pop());
    Value value;
    switch(op) {
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

    char buffer[50];
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
            case OP_EQUAL: {
                Value b = pop();
                Value a = pop();
                push(BOOL_VAL(valuesEqual(a, b)));
                break;
            }
            case OP_GREATER: {
                op_result = binary_op('>', frame);
                break;
            }
            case OP_LESS: {
                op_result = binary_op('<', frame);
                break;
            }
            case OP_ADD: {
                if (IS_STRING(peek(0)) && IS_STRING(peek(1))) {
                    ObjString* b = AS_STRING(pop());
                    ObjString* a = AS_STRING(pop());
                    concatenate(a, b);
                } else if (IS_STRING(peek(0)) && IS_NUMBER(peek(1))) {
                    ObjString* b = AS_STRING(pop());
                    double a_double = AS_NUMBER(pop());
                    int length = sprintf(buffer, "%g", a_double);
                    ObjString *a = copyString(buffer, length);
                    concatenate(a, b);

                } else if (IS_NUMBER(peek(0)) && IS_STRING(peek(1))) {
                    double b_double = AS_NUMBER(pop());
                    ObjString* a = AS_STRING(pop());
                    int length = sprintf(buffer, "%g", b_double);
                    ObjString *b = copyString(buffer, length);
                    concatenate(a, b);

                } else if (IS_NUMBER(peek(0)) && IS_NUMBER(peek(1))) {
                    double b = AS_NUMBER(pop());
                    double a = AS_NUMBER(pop());
                    push(NUMBER_VAL(a + b));
                } else {
                    runtimeError("Operands must be two numbers or two strings.");
                    op_result = INTERPRET_RUNTIME_ERROR;
                }
                break;
            }
            case OP_SUBTRACT: {
                op_result = binary_op('-', frame);
                break;
            }
            case OP_MULTIPLY: {
                op_result = binary_op('*', frame);
                break;
            }
            case OP_DIVIDE: {
                op_result = binary_op('/', frame);
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
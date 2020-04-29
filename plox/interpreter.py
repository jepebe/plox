from typing import List

from plox.environment import Environment
import plox.expr as Expr
import plox.stmt as Stmt
from plox.lox_bool import lox_false, lox_true, LoxBool
from plox.lox_callable import LoxCallable
from plox.lox_class import LoxClass
from plox.lox_function import LoxFunction
from plox.lox_instance import LoxInstance
from plox.plox_errors import PloxRuntimeError, PloxTypeError, PloxReturnException
from plox.stmt import Class
from plox.token import Token
from plox.token_type import TokenType, EQUALITY_TOKENS, COMPARISON_TOKENS


class _PloxBreakException(Exception):
    pass


def is_plox_truthy(value):
    if value is None:
        return lox_false
    if isinstance(value, LoxBool):
        return value
    if value is False:
        return lox_false
    elif value is True:
        return lox_true
    return lox_true


def is_plox_number(operand):
    return isinstance(operand, (int, float)) and not isinstance(operand, bool)


def is_plox_string(operand):
    return isinstance(operand, str)


def stringify(value):
    if value is None:
        return 'nil'
    return str(value)


def check_number_operand(operator, operand):
    if is_plox_number(operand):
        return
    raise PloxTypeError(operator, operand)


def check_number_operands(operator, left, right):
    if is_plox_number(left) and is_plox_number(right):
        return
    raise PloxTypeError(operator, left, right)


BINARY_OPS = {
    TokenType.MINUS: lambda left, right: left - right,
    TokenType.SLASH: lambda left, right: left / right,
    TokenType.STAR: lambda left, right: left * right,
    TokenType.PLUS: lambda left, right: left + right,
    TokenType.GREATER: lambda left, right: is_plox_truthy(left > right),
    TokenType.GREATER_EQUAL: lambda left, right: is_plox_truthy(left >= right),
    TokenType.LESS: lambda left, right: is_plox_truthy(left < right),
    TokenType.LESS_EQUAL: lambda left, right: is_plox_truthy(left <= right),
    TokenType.BANG_EQUAL: lambda left, right: is_plox_truthy(left != right),
    TokenType.EQUAL_EQUAL: lambda left, right: is_plox_truthy(left == right),
}


class _Clock(LoxCallable):

    def call(self, interpreter, arguments):
        import time
        return time.time_ns() // 1000000

    def arity(self):
        return 0

    def __str__(self) -> str:
        return "<native fn>"


class Interpreter(Expr.ExprVisitor, Stmt.StmtVisitor):
    def __init__(self, error):
        self.error = error
        self.env = Environment()
        self.globals = self.env
        self.globals.define('clock', _Clock())
        self._locals = {}

    def evaluate(self, expr: Expr.Expr):
        return expr.accept(self)

    def visit_block_stmt(self, stmt: Stmt.Block) -> object:
        self._execute_block(stmt.statements, Environment(self.env))
        return None

    def visit_break_stmt(self, stmt: Stmt.Break) -> object:
        raise _PloxBreakException()

    def visit_class_stmt(self, stmt: Class) -> object:
        environment = self.env
        superclass = None
        if stmt.superclass:
            superclass = self.evaluate(stmt.superclass)

            if not isinstance(superclass, LoxClass):
                raise PloxRuntimeError(stmt.superclass.name, "Superclass must be a class.")

        environment.define(stmt.name.lexeme, None)

        if stmt.superclass:
            environment = Environment(environment)
            environment.define('super', superclass)

        methods = {}
        for method in stmt.methods:
            is_initializer = method.name.lexeme == 'init'
            is_getter = method.getter
            function = LoxFunction(method, environment, is_initializer, is_getter)
            methods[method.name.lexeme] = function

        klass = LoxClass(stmt.name.lexeme, superclass, methods)

        if superclass:
            environment = environment.enclosing

        environment.assign(stmt.name, klass)
        return None

    def visit_expression_stmt(self, stmt: Stmt.Expression) -> object:
        self.evaluate(stmt.expression)
        return None

    def visit_function_stmt(self, stmt: Stmt.Function) -> object:
        if not stmt.anonymous:
            function = LoxFunction(stmt, self.env, False)
            self.env.define(stmt.name.lexeme, function)
            return None

        # anonymous function from expression
        return LoxFunction(stmt, self.env, False)

    def visit_if_stmt(self, stmt: Stmt.If) -> object:
        if is_plox_truthy(self.evaluate(stmt.condition)):
            self._execute(stmt.then_branch)
        elif stmt.else_branch is not None:
            self._execute(stmt.else_branch)

        return None

    def visit_print_stmt(self, stmt: Stmt.Print) -> object:
        value = self.evaluate(stmt.expression)
        print(stringify(value))
        return None

    def visit_return_stmt(self, stmt: Stmt.Return) -> object:
        value = None
        if stmt.value is not None:
            value = self.evaluate(stmt.value)
        raise PloxReturnException(value)

    def visit_var_stmt(self, stmt: Stmt.Var) -> object:
        self.env.define(stmt.name.lexeme, None)

        if stmt.initializer is not None:
            value = self.evaluate(stmt.initializer)
            self.env.assign(stmt.name, value)

        return None

    def visit_while_stmt(self, stmt: Stmt.While) -> object:
        while is_plox_truthy(self.evaluate(stmt.condition)):
            try:
                self._execute(stmt.body)
            except _PloxBreakException:
                break
        return None

    def visit_assign_expr(self, expr: Expr.Assign) -> object:
        value = self.evaluate(expr.value)

        if expr in self._locals:
            distance = self._locals[expr]
            self.env.assign_at(distance, expr.name, value)
        else:
            self.globals.assign(expr.name, value)

        return value

    def visit_ternary_expr(self, expr: Expr.Ternary) -> object:
        condition = self.evaluate(expr.condition)
        if is_plox_truthy(condition):
            return self.evaluate(expr.then_branch)
        else:
            return self.evaluate(expr.else_branch)

    def visit_logical_expr(self, expr: Expr.Logical) -> object:
        left = self.evaluate(expr.left)
        if expr.operator.type == TokenType.OR:
            if is_plox_truthy(left):
                return left
        else:
            if not is_plox_truthy(left):
                return left

        return self.evaluate(expr.right)

    def visit_variable_expr(self, expr: Expr.Variable) -> object:
        return self._look_up_variable(expr.name, expr)

    def visit_literal_expr(self, expr: Expr.Literal) -> object:
        return expr.value

    def visit_get_expr(self, expr: Expr.Get) -> object:
        obj = self.evaluate(expr.objct)
        if isinstance(obj, LoxInstance):
            result = obj.get(expr.name)
            if isinstance(result, LoxFunction) and result.is_getter:
                result = result.call(self, [])
            return result

        raise PloxRuntimeError(expr.name, "Only instances have properties.")

    def visit_grouping_expr(self, expr: Expr.Grouping) -> object:
        return self.evaluate(expr.expression)

    def visit_set_expr(self, expr: Expr.Set) -> object:
        objct = self.evaluate(expr.objct)

        if not isinstance(objct, LoxInstance):
            raise PloxRuntimeError(expr.name, "Only instances have fields.")
        value = self.evaluate(expr.value)
        objct.set(expr.name, value)
        return value

    def visit_super_expr(self, expr: Super) -> object:
        distance = self._locals.get(expr)
        superclass = self.env.get_at(distance, "super")

        # "this" is always one level nearer than "super"'s environment.
        objct = self.env.get_at(distance - 1, "this")
        method = superclass.find_method(expr.method.lexeme)

        if not method:
            raise PloxRuntimeError(expr.method, f"Undefined property '{expr.method.lexeme}'.")

        return method.bind(objct)

    def visit_this_expr(self, expr: Expr.This) -> object:
        return self._look_up_variable(expr.keyword, expr)

    def visit_unary_expr(self, expr: Expr.Unary) -> object:
        right = self.evaluate(expr.right)
        opt = expr.operator.type
        if opt == TokenType.MINUS:
            check_number_operand(expr.operator, right)
            return -right
        elif opt == TokenType.BANG:
            return is_plox_truthy(right).notify()

        return None

    def visit_binary_expr(self, expr: Expr.Binary) -> object:
        left = self.evaluate(expr.left)
        right = self.evaluate(expr.right)
        opt = expr.operator.type

        if opt == TokenType.PLUS:
            if is_plox_number(left) and is_plox_number(right):
                return BINARY_OPS[opt](left, right)
            if is_plox_string(left) and is_plox_string(right):
                return BINARY_OPS[opt](left, right)
            if is_plox_string(left) or is_plox_string(right):
                return BINARY_OPS[opt](str(left), str(right))
            raise PloxTypeError(expr.operator, left, right)

        elif opt in EQUALITY_TOKENS:
            return BINARY_OPS[opt](left, right)

        elif opt in COMPARISON_TOKENS:
            if is_plox_number(left) and is_plox_number(right):
                return BINARY_OPS[opt](left, right)
            if is_plox_string(left) and is_plox_string(right):
                return BINARY_OPS[opt](left, right)
            raise PloxTypeError(expr.operator, left, right)

        elif opt in BINARY_OPS:
            check_number_operands(expr.operator, left, right)
            if opt == TokenType.SLASH and right == 0:
                raise PloxRuntimeError(expr.operator, 'Division by zero.')

            return BINARY_OPS[opt](left, right)

        return None

    def visit_call_expr(self, expr: Expr.Call) -> object:
        func = self.evaluate(expr.callee)
        arguments = []
        for arg in expr.arguments:
            arguments.append(self.evaluate(arg))

        if not isinstance(func, LoxCallable):
            raise PloxRuntimeError(expr.paren, "Can only call functions and classes.")

        if len(arguments) != func.arity():
            msg = f"Expected {func.arity()} arguments but got {len(arguments)}."
            raise PloxRuntimeError(expr.paren, msg)

        return func.call(self, arguments)

    def _execute(self, stmt):
        stmt.accept(self)

    def resolve(self, expr: Expr.Expr, depth: int):
        self._locals[expr] = depth

    def _look_up_variable(self, name: Token, expr: Expr.Expr):
        if expr in self._locals:
            distance = self._locals[expr]
            return self.env.get_at(distance, name.lexeme)
        else:
            return self.globals.get(name)

    def _execute_block(self, statements, environment):
        previous = self.env
        try:
            self.env = environment

            for stmt in statements:
                self._execute(stmt)
        finally:
            self.env = previous

    def interpret(self, statements):
        try:
            for statement in statements:
                self._execute(statement)
        except PloxRuntimeError as e:
            self.error(e)

from collections import deque
from enum import Enum, auto
from typing import List

import plox.expr as Expr
import plox.stmt as Stmt
from plox.expr import Get, Set, This
from plox.stmt import Class
from plox.token import Token


class FunctionType(Enum):
    NONE = auto(),
    FUNCTION = auto(),
    GETTER = auto(),
    INITIALIZER = auto(),
    METHOD = auto()


class LoopType(Enum):
    NONE = auto(),
    FOR = auto(),
    WHILE = auto()


class ClassType(Enum):
    NONE = auto(),
    CLASS = auto()


class Scope(object):
    def __init__(self):
        self.stack = deque()

    def push(self, state):
        self.stack.append(state)

    def pop(self):
        self.stack.pop()

    def current(self):
        return self.stack[-1]

    def update(self, value):
        self.stack[-1] = value

    def __bool__(self):
        return len(self.stack) > 0

    def __iter__(self):
        return iter(self.stack)

    def __len__(self):
        return len(self.stack)

    def __getitem__(self, item):
        return self.stack[item]


class Resolver(Expr.ExprVisitor, Stmt.StmtVisitor):
    def __init__(self, error, interpreter):
        self.interpreter = interpreter
        self.error = error

        self.scopes = Scope()
        self.loop_scopes = Scope()
        self.loop_scopes.push(LoopType.NONE)
        self.function_scopes = Scope()
        self.function_scopes.push(FunctionType.NONE)
        self.class_scopes = Scope()
        self.class_scopes.push(ClassType.NONE)
        self.return_scopes = Scope()
        self.return_scopes.push(None)

    def visit_block_stmt(self, stmt: Stmt.Block) -> object:
        self._begin_scope()
        self._resolve_statements(stmt.statements)
        self._end_scope()
        return None

    def visit_break_stmt(self, expr: Stmt.Break) -> object:
        if self.loop_scopes.current() == LoopType.NONE:
            self.error(expr.name, "'break' outside loop.")
        return None

    def visit_class_stmt(self, stmt: Class) -> object:
        self.class_scopes.push(ClassType.CLASS)
        self._declare(stmt.name)
        self._define(stmt.name)

        self._begin_scope()
        self.scopes.current()['this'] = {'defined': True, 'accessed': True, 'token': stmt.name}

        for method in stmt.methods:
            declaration = FunctionType.METHOD
            if method.name.lexeme == 'init':
                declaration = FunctionType.INITIALIZER
            if method.getter:
                declaration = FunctionType.GETTER
            self._resolve_function(method, declaration)

        self._end_scope()
        self.class_scopes.pop()
        return None

    def visit_expression_stmt(self, expr: Stmt.Expression) -> object:
        self._resolve_expression(expr.expression)
        return None

    def visit_var_stmt(self, stmt: Stmt.Var) -> object:
        self._declare(stmt.name)
        if stmt.initializer is None:
            self.error(stmt.name, "variable definition without assignment.")
        else:
            self._resolve_expression(stmt.initializer)
        self._define(stmt.name)
        return None

    def visit_function_stmt(self, stmt: Stmt.Function) -> object:
        if not stmt.anonymous:
            self._declare(stmt.name)
            self._define(stmt.name)
        self._resolve_function(stmt, FunctionType.FUNCTION)
        return None

    def visit_if_stmt(self, stmt: Stmt.If) -> object:
        self._resolve_expression(stmt.condition)
        self.return_scopes.push(None)
        self._resolve_statement(stmt.then_branch)
        self.return_scopes.pop()
        if stmt.else_branch:
            self.return_scopes.push(None)
            self._resolve_statement(stmt.else_branch)
            self.return_scopes.pop()
        return None

    def visit_print_stmt(self, expr: Stmt.Print) -> object:
        self._resolve_expression(expr.expression)
        return None

    def visit_return_stmt(self, stmt: Stmt.Return) -> object:
        if self.function_scopes.current() == FunctionType.NONE:
            self.error(stmt.keyword, "Cannot return from top-level code.")

        if stmt.value:
            if self.function_scopes.current() == FunctionType.INITIALIZER:
                self.error(stmt.keyword, "Cannot return a value from an initializer.")
            self._resolve_expression(stmt.value)

        self.return_scopes.update(stmt)
        return None

    def visit_while_stmt(self, stmt: Stmt.While) -> object:
        self.loop_scopes.push(LoopType.WHILE)
        self._resolve_expression(stmt.condition)

        self.return_scopes.push(None)
        self._resolve_statement(stmt.body)
        self.return_scopes.pop()

        self.loop_scopes.pop()
        return None

    def visit_variable_expr(self, expr: Expr.Variable) -> object:
        if self.scopes:
            scope = self.scopes.current()
            if expr.name.lexeme in scope and not scope[expr.name.lexeme]['defined']:
                self.error(expr.name, "Cannot read local variable in its own initializer.")

        self._resolve_local(expr, expr.name)
        return None

    def visit_assign_expr(self, expr: Expr.Assign) -> object:
        self._resolve_expression(expr.value)
        self._resolve_local(expr, expr.name)
        return None

    def visit_binary_expr(self, expr: Expr.Binary) -> object:
        self._resolve_expression(expr.left)
        self._resolve_expression(expr.right)
        return None

    def visit_call_expr(self, expr: Expr.Call) -> object:
        self._resolve_expression(expr.callee)
        for arg in expr.arguments:
            self._resolve_expression(arg)
        return None

    def visit_get_expr(self, expr: Get) -> object:
        self._resolve_expression(expr.objct)
        return None

    def visit_grouping_expr(self, expr: Expr.Grouping) -> object:
        self._resolve_expression(expr.expression)
        return None

    def visit_literal_expr(self, expr: Expr.Literal) -> object:
        return None

    def visit_logical_expr(self, expr: Expr.Logical) -> object:
        self._resolve_expression(expr.left)
        self._resolve_expression(expr.right)
        return None

    def visit_set_expr(self, expr: Set) -> object:
        self._resolve_expression(expr.value)
        self._resolve_expression(expr.objct)
        return None

    def visit_ternary_expr(self, expr: Expr.Ternary) -> object:
        self._resolve_expression(expr.condition)
        self._resolve_expression(expr.then_branch)
        self._resolve_expression(expr.else_branch)
        return None

    def visit_this_expr(self, expr: This) -> object:
        if self.class_scopes.current() == ClassType.NONE:
            self.error(expr.keyword, "Cannot use 'this' outside of a class.")
            return None

        self._resolve_local(expr, expr.keyword)
        return None

    def visit_unary_expr(self, expr: Expr.Unary) -> object:
        self._resolve_expression(expr.right)
        return None

    def _resolve_statements(self, statements: List[Stmt.Stmt]):
        unreachable_warning = False
        for stmt in statements:
            ret_scp = self.return_scopes[-1]
            if ret_scp and not unreachable_warning:
                self.error(ret_scp.keyword, 'Unreachable code.', warning=True, after=True)
                unreachable_warning = True
            self._resolve_statement(stmt)

    def _resolve_statement(self, statement: Stmt.Stmt):
        statement.accept(self)

    def _resolve_expression(self, expression: Expr.Expr):
        expression.accept(self)

    def _resolve_local(self, expr: Expr.Expr, name: Token):
        for index, scope in enumerate(reversed(self.scopes)):
            if name.lexeme in scope:
                self.interpreter.resolve(expr, index)
                self._mark_as_accessed(name, scope)
                return

    def _resolve_function(self, function: Stmt.Function, func_type: FunctionType):
        self.function_scopes.push(func_type)
        self._begin_scope()
        for param in function.params:
            self._declare(param)
            self._define(param)
            #  self._mark_as_accessed(param, self.scopes[-1])  # function parameters can be ignored?
        self._resolve_statements(function.body)
        self._end_scope()
        self.function_scopes.pop()

    def _begin_scope(self):
        self.return_scopes.push(None)
        self.scopes.push({})

    def _end_scope(self):
        for name, state in self.scopes.current().items():
            if not state['accessed']:
                self.error(state['token'], 'Local variable declared but never used.', warning=True)
        self.scopes.pop()
        self.return_scopes.pop()

    def _declare(self, name: Token):
        if self.scopes:
            scope = self.scopes.current()

            if name.lexeme in scope:
                self.error(name, "Variable with this name already declared in this scope.")

            scope[name.lexeme] = {'defined': False, 'accessed': False, 'token': name}

    def _define(self, name: Token):
        if self.scopes:
            self.scopes.current()[name.lexeme]['defined'] = True

    def _mark_as_accessed(self, name: Token, scope):
        scope[name.lexeme]['accessed'] = True

    def resolve(self, statements):
        self._resolve_statements(statements)

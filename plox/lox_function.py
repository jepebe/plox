from plox.environment import Environment
from plox.lox_callable import LoxCallable
from plox.plox_errors import PloxReturnException
from plox.stmt import Function


class LoxFunction(LoxCallable):
    def __init__(self, declaration: Function,
                 closure: Environment,
                 is_initializer: bool = False,
                 is_getter: bool = False):
        self.declaration = declaration
        self.closure = closure
        self.anonymous = declaration.anonymous
        self.is_initializer = is_initializer
        self.is_getter = is_getter

    def bind(self, instance):
        environment = Environment(self.closure)
        environment.define("this", instance)
        return LoxFunction(self.declaration, environment, self.is_initializer, self.is_getter)

    def call(self, interpreter, arguments):
        environment = Environment(self.closure)

        for param, arg in zip(self.declaration.params, arguments):
            environment.define(param.lexeme, None)
            environment.assign(param, arg)

        try:
            interpreter._execute_block(self.declaration.body, environment)
        except PloxReturnException as return_value:
            if self.is_initializer:
                return self.closure.get_at(0, 'this')
            return return_value.value

        if self.is_initializer:
            return self.closure.get_at(0, "this")
        return None

    def arity(self):
        return len(self.declaration.params)

    def is_anonymous(self):
        return self.anonymous

    def __str__(self) -> str:
        if self.anonymous:
            name = 'anonymous function'
        else:
            name = self.declaration.name.lexeme

        return f'<fn {name}>'

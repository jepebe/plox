from plox.lox_function import LoxFunction
from plox.plox_errors import PloxRuntimeError
from plox.token import Token


class LoxInstance(object):
    def __init__(self, klass):
        self.fields = {}
        self.klass = klass

    def __str__(self) -> str:
        return self.klass.name + " instance"

    def get(self, name: Token or str):
        if name.lexeme in self.fields:
            return self.fields[name.lexeme]

        method = self.klass.find_method(name.lexeme)
        if method:
            return method.bind(self)

        raise PloxRuntimeError(name, f"Undefined property '{name.lexeme}'.")

    def find_method(self, name) -> LoxFunction:
        method = self.klass.find_method(name)
        if method:
            return method.bind(self)
        return None

    def set(self, name: Token, value: object):
        self.fields[name.lexeme] = value

from plox.plox_errors import PloxRuntimeError
from plox.token import Token


class Environment(object):
    def __init__(self, enclosing=None):
        self.enclosing = enclosing
        self.values = {}

    def get(self, name: Token):
        vname = name.lexeme
        if vname in self.values:
            return self.values[vname]

        if self.enclosing is not None:
            return self.enclosing.get(name)

        raise PloxRuntimeError(name, f'Undefined variable \'{vname}\'.')

    def get_at(self, distance: int, name: str):
        return self.ancestor(distance).values[name]

    def ancestor(self, distance):
        env = self
        for i in range(distance):
            env = env.enclosing
        return env

    def define(self, name: str, value: object):
        self.values[name] = value

    def assign(self, name: Token, value: object):
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
            return

        if self.enclosing is not None:
            self.enclosing.assign(name, value)
            return

        raise PloxRuntimeError(name, f'Undefined variable \'{name.lexeme}\'.')

    def assign_at(self, distance: int, name: Token, value: object):
        self.ancestor(distance).values[name.lexeme] = value

    def __str__(self):
        result = ''

        for key, val in self.values.items():
            result += f'{key}: {val}\n'
        if self.enclosing:
            result += '---\n'
            result += str(self.enclosing)

        return result
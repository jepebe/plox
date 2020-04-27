from typing import Dict

from plox.lox_callable import LoxCallable
from plox.lox_function import LoxFunction
from plox.lox_instance import LoxInstance


class LoxClass(LoxCallable):
    def __init__(self, name: str, superclass: 'LoxClass', methods: Dict[str, LoxFunction]):
        self.name = name
        self.superclass = superclass
        self.methods = methods

    def __str__(self):
        return self.name

    def call(self, interpreter, arguments):
        instance = LoxInstance(self)
        initializer = self.find_method("init")
        if initializer:
            initializer.bind(instance).call(interpreter, arguments)
        return instance

    def arity(self):
        init = self.find_method('init')
        if init:
            return init.arity()
        return 0

    def find_method(self, name) -> LoxFunction:
        if name in self.methods:
            return self.methods[name]

        if self.superclass:
            return self.superclass.find_method(name)

        return None



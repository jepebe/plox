from typing import Dict

from plox.lox_callable import LoxCallable
from plox.lox_function import LoxFunction
from plox.lox_instance import LoxInstance


class LoxClass(LoxCallable):
    def __init__(self, name: str, methods: Dict[str, LoxFunction]):
        self.name = name
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
        return self.methods.get(name, None)



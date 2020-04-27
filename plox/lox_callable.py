class LoxCallable(object):
    def call(self, interpreter, arguments):
        print(f'call(...) in {self.__class__.__name__} not implemented.')
        return None

    def arity(self):
        print(f'arity() in {self.__class__.__name__} not implemented.')
        return -1

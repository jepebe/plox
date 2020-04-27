class PloxParserError(Exception):
    def __init__(self, token, message):
        super(PloxParserError, self).__init__(message)
        self.token = token
        self.message = message


class PloxRuntimeError(Exception):
    def __init__(self, token, message):
        super(PloxRuntimeError, self).__init__(message)
        self.token = token
        self.message = message


class PloxTypeError(PloxRuntimeError):
    def __init__(self, token, *operands):
        operator = token.lexeme
        ops = ' and '.join(["'%s'" % o.__class__.__name__ for o in operands])
        msg = f'Unsupported operand type(s) for {operator}: {ops}'
        super().__init__(token, msg)


class PloxReturnException(Exception):
    def __init__(self, value):
        self.value = value
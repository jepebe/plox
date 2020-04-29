class LoxBool(object):
    def __init__(self, boolean):
        self.boolean = boolean

    def __bool__(self):
        return self.boolean

    def notify(self):
        return LoxBool(not self.boolean)

    def __str__(self):
        if self.boolean:
            return 'true'
        else:
            return 'false'

    def __eq__(self, other):
        if other is None:
            return False
        if isinstance(other, LoxBool):
            return self.boolean == other.boolean
        if isinstance(other, int) and other == 0:
            return self.boolean
        return False


lox_true = LoxBool(True)
lox_false = LoxBool(False)

from plox.expr import ExprVisitor, Binary, Unary, Literal, Grouping
from plox.token import Token
from plox.token_type import TokenType


class AstPrinter(ExprVisitor):
    def print(self, expr):
        return expr.accept(self)

    def visit_binary_expr(self, expr):
        return self.parenthesize(expr.operator.lexeme, expr.left, expr.right)

    def visit_grouping_expr(self, expr):
        return self.parenthesize("group", expr.expression)

    def visit_literal_expr(self, expr):
        if expr.value is None:
            return "nil"
        return str(expr.value)

    def visit_unary_expr(self, expr):
        return self.parenthesize(expr.operator.lexeme, expr.right)

    def parenthesize(self, name, *exprs):
        result = ['(', name]

        for expr in exprs:
            result.append(' ')
            result.append(expr.accept(self))
        result.append(')')
        return ''.join(result)


if __name__ == '__main__':
    expression = Binary(
        Unary(
            Token(TokenType.MINUS, '-', None, 1),
            Literal(123)
        ),
        Token(TokenType.STAR, '*', None, 1),
        Grouping(
            Literal(45.67)
        )
    )
    print(AstPrinter().print(expression))

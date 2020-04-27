import plox.expr as Expr
import plox.stmt as Stmt
from plox.plox_errors import PloxParserError
from plox.token import Token
from plox.token_type import TokenType as TT, EQUALITY_TOKENS, COMPARISON_TOKENS
from plox.token_type import ADDITION_TOKENS, MULTIPLICATION_TOKENS, KEYWORD_TOKENS


class Parser(object):

    def __init__(self, tokens, error):
        self.tokens = tokens
        self.error = error
        self.current = 0

    def parse(self):
        statements = []
        while not self._is_at_end():
            statements.append(self._declaration())
        return statements

    def _declaration(self):
        try:
            if self._match(TT.CLASS):
                return self._class_declaration()
            if self._match(TT.FUN):
                return self._function("function")
            if self._match(TT.VAR):
                return self._var_declaration()

            return self._statement()
        except PloxParserError as e:
            self._synchronize()

        return None

    def _class_declaration(self):
        name = self._consume(TT.IDENTIFIER, "Expect class name.")
        self._consume(TT.LEFT_BRACE, "Expect '{' before class body.")

        methods = []
        while not self._check(TT.RIGHT_BRACE) and not self._is_at_end():
            methods.append(self._function("method"))

        self._consume(TT.RIGHT_BRACE, "Expect '}' after class body.")

        return Stmt.Class(name, methods)

    def _statement(self):
        if self._match(TT.BREAK):
            return self._break_statement()
        if self._match(TT.FOR):
            return self._for_statement()
        if self._match(TT.IF):
            return self._if_statement()
        if self._match(TT.PRINT):
            return self._print_statement()
        if self._match(TT.RETURN):
            return self._return_statement()
        if self._match(TT.WHILE):
            return self._while_statement()
        if self._match(TT.LEFT_BRACE):
            return Stmt.Block(self._block())
        return self._expression_statement()

    def _break_statement(self):
        break_token = self._previous()
        self._consume(TT.SEMICOLON, "Expect ';' after break.")

        return Stmt.Break(break_token)

    def _for_statement(self):
        self._consume(TT.LEFT_PAREN, "Expect '(' after 'for'.")
        if self._match(TT.SEMICOLON):
            initializer = None
        elif self._match(TT.VAR):
            initializer = self._var_declaration()
        else:
            initializer = self._expression_statement()

        condition = None
        if not self._check(TT.SEMICOLON):
            condition = self._expression()

        self._consume(TT.SEMICOLON, "Expect ';' after loop condition.")

        increment = None
        if not self._check(TT.RIGHT_PAREN):
            increment = self._expression()

        self._consume(TT.RIGHT_PAREN, "Expect ')' after for clauses.")

        body = self._statement()

        if increment is not None:
            body = Stmt.Block([body, Stmt.Expression(increment)])

        if condition is None:
            condition = Expr.Literal(True)
        body = Stmt.While(condition, body)

        if initializer is not None:
            body = Stmt.Block([initializer, body])

        return body

    def _if_statement(self):
        self._consume(TT.LEFT_PAREN, "Expect '(' after 'if'.")
        condition = self._expression()
        self._consume(TT.RIGHT_PAREN, "Expect ')' after if condition.")

        then_branch = self._statement()
        else_branch = None
        if self._match(TT.ELSE):
            else_branch = self._statement()

        return Stmt.If(condition, then_branch, else_branch)

    def _while_statement(self):
        self._consume(TT.LEFT_PAREN, "Expect '(' after 'while'.")
        condition = self._expression()
        self._consume(TT.RIGHT_PAREN, "Expect ')' after condition.")
        body = self._statement()

        return Stmt.While(condition, body)

    def _print_statement(self):
        value = self._expression()
        self._consume(TT.SEMICOLON, "Expect ';' after value.")
        return Stmt.Print(value)

    def _return_statement(self):
        keyword = self._previous()
        value = None
        if not self._check(TT.SEMICOLON):
            value = self._expression()
        self._consume(TT.SEMICOLON, "Expect ';' after return value.")
        return Stmt.Return(keyword, value)

    def _block(self):
        statements = []
        while not self._check(TT.RIGHT_BRACE) and not self._is_at_end():
            statements.append(self._declaration())

        self._consume(TT.RIGHT_BRACE, "Expect '}' after block.")
        return statements

    def _var_declaration(self):
        name = self._consume(TT.IDENTIFIER, "Expect variable name.")

        initializer = None
        if self._match(TT.EQUAL):
            initializer = self._expression()

        self._consume(TT.SEMICOLON, "Expect ';' after variable declaration.")
        return Stmt.Var(name, initializer)

    def _expression_statement(self):
        value = self._expression()
        self._consume(TT.SEMICOLON, "Expect ';' after expression.")
        return Stmt.Expression(value)

    def _function(self, kind, anonymous=False):
        getter = False
        if anonymous:
            token = self._previous()
            fname = f"anonymous_function_at_line_{token.line}"
            name = Token(TT.IDENTIFIER, fname, None, token.line)
            self._consume(TT.LEFT_PAREN, f"Expect '(' after 'fun' keyword.")
        else:
            name = self._consume(TT.IDENTIFIER, f'Expect {kind} name.')
            if self._check(TT.LEFT_BRACE):
                getter = True
            else:
                self._consume(TT.LEFT_PAREN, f"Expect '(' after {kind} name.")

        parameters = []
        if not getter:
            if not self._check(TT.RIGHT_PAREN):
                parameters.append(self._consume(TT.IDENTIFIER, "Expect parameter name."))
                while self._match(TT.COMMA):
                    if len(parameters) >= 255:
                        self._error(self._peek(), "Cannot have more than 255 parameters.")
                    parameters.append(self._consume(TT.IDENTIFIER, "Expect parameter name."))

            self._consume(TT.RIGHT_PAREN, "Expect ')' after parameters.")

        self._consume(TT.LEFT_BRACE, f"Expect '{{' before {kind} body.")
        body = self._block()
        return Stmt.Function(name, parameters, body, anonymous, getter)

    def _binary_rule(self, next_rule, tokens):
        expr = next_rule()

        while self._match(*tokens):
            operator = self._previous()
            right = next_rule()
            expr = Expr.Binary(expr, operator, right)
        return expr

    def _expression(self):
        return self._assignment()

    def _assignment(self):
        expr = self._ternary()

        if self._match(TT.EQUAL):
            equals = self._previous()
            value = self._assignment()

            if isinstance(expr, Expr.Variable):
                return Expr.Assign(expr.name, value)
            elif isinstance(expr, Expr.Get):
                return Expr.Set(expr.objct, expr.name, value)
            self._error(equals, 'Invalid assignment target.')
        return expr

    def _ternary(self):
        expr = self._or()

        if self._match(TT.QUESTION_MARK):
            then_branch = self._expression()
            self._consume(TT.COLON, "Expect ':' after expression in ternary.")
            else_branch = self._expression()
            expr = Expr.Ternary(expr, then_branch, else_branch)
        return expr

    def _or(self):
        expr = self._and()
        while self._match(TT.OR):
            operator = self._previous()
            right = self._and()
            expr = Expr.Logical(expr, operator, right)
        return expr

    def _and(self):
        expr = self._equality()
        while self._match(TT.AND):
            operator = self._previous()
            right = self._equality()
            expr = Expr.Logical(expr, operator, right)
        return expr

    def _equality(self):
        return self._binary_rule(self._comparison, EQUALITY_TOKENS)

    def _comparison(self):
        return self._binary_rule(self._addition, COMPARISON_TOKENS)

    def _addition(self):
        return self._binary_rule(self._multiplication, ADDITION_TOKENS)

    def _multiplication(self):
        return self._binary_rule(self._unary, MULTIPLICATION_TOKENS)

    def _unary(self):
        if self._match(TT.BANG, TT.MINUS):
            operator = self._previous()
            right = self._unary()
            return Expr.Unary(operator, right)

        return self._call()

    def _call(self):
        expr = self._primary()

        while True:
            if self._match(TT.LEFT_PAREN):
                expr = self._finish_call(expr)
            elif self._match(TT.DOT):
                name = self._consume(TT.IDENTIFIER, "Expect property name after '.'.")
                expr = Expr.Get(expr, name)
            else:
                break

        return expr

    def _finish_call(self, callee):
        arguments = []
        if not self._check(TT.RIGHT_PAREN):
            arguments.append(self._expression())

            while self._match(TT.COMMA):
                if len(arguments) >= 255:
                    self._error(self._peek(), "Cannot have more than 255 arguments.")
                arguments.append(self._expression())
        paren = self._consume(TT.RIGHT_PAREN, "Expect ')' after arguments.")
        return Expr.Call(callee, paren, arguments)

    def _primary(self):
        if self._match(TT.FALSE):
            return Expr.Literal(False)
        if self._match(TT.TRUE):
            return Expr.Literal(True)
        if self._match(TT.NIL):
            return Expr.Literal(None)

        if self._match(TT.FUN):
            return self._function('anonymous function', anonymous=True)

        if self._match(TT.NUMBER, TT.STRING):
            return Expr.Literal(self._previous().literal)

        if self._match(TT.THIS):
            return Expr.This(self._previous())

        if self._match(TT.IDENTIFIER):
            return Expr.Variable(self._previous())

        if self._match(TT.LEFT_PAREN):
            expr = self._expression()
            self._consume(TT.RIGHT_PAREN, "Expect ')' after expression.")
            return Expr.Grouping(expr)

        raise self._error(self._peek(), "Expect expression.")

    def _match(self, *types):
        for t in types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _check(self, token_type):
        if self._is_at_end():
            return False
        return self._peek().type == token_type

    def _advance(self):
        if not self._is_at_end():
            self.current += 1

        return self._previous()

    def _is_at_end(self):
        return self._peek().type == TT.EOF

    def _peek(self):
        return self.tokens[self.current]

    def _previous(self):
        return self.tokens[self.current - 1]

    def _consume(self, token_type, message):
        if self._check(token_type):
            return self._advance()
        raise self._error(self._peek(), message)

    def _error(self, token, message):
        self.error(token, message)
        return PloxParserError(token, message)

    def _synchronize(self):
        self._advance()
        while not self._is_at_end():
            if self._previous().type == TT.SEMICOLON:
                return

            if self._peek().type in KEYWORD_TOKENS:
                return

            self._advance()

from plox.token import Token
from plox.token_type import TokenType

TOKEN_TYPES = {
    '(': TokenType.LEFT_PAREN,
    ')': TokenType.RIGHT_PAREN,
    '{': TokenType.LEFT_BRACE,
    '}': TokenType.RIGHT_BRACE,
    ',': TokenType.COMMA,
    '.': TokenType.DOT,
    '-': TokenType.MINUS,
    '+': TokenType.PLUS,
    ';': TokenType.SEMICOLON,
    '*': TokenType.STAR,
    '?': TokenType.QUESTION_MARK,
    ':': TokenType.COLON,
    '!': TokenType.BANG,
    '!=': TokenType.BANG_EQUAL,
    '=': TokenType.EQUAL,
    '==': TokenType.EQUAL_EQUAL,
    '<': TokenType.LESS,
    '<=': TokenType.LESS_EQUAL,
    '>': TokenType.GREATER,
    '>=': TokenType.GREATER_EQUAL,
    'and': TokenType.AND,
    'break': TokenType.BREAK,
    'class': TokenType.CLASS,
    'else': TokenType.ELSE,
    'false': TokenType.FALSE,
    'for': TokenType.FOR,
    'fun': TokenType.FUN,
    'if': TokenType.IF,
    'nil': TokenType.NIL,
    'or': TokenType.OR,
    'print': TokenType.PRINT,
    'return': TokenType.RETURN,
    'super': TokenType.SUPER,
    'this': TokenType.THIS,
    'true': TokenType.TRUE,
    'var': TokenType.VAR,
    'while': TokenType.WHILE,
}


class Scanner(object):
    def __init__(self, source, error):
        self.tokens = []
        self.source = source
        self.error = error
        self.start = 0
        self.current = 0
        self.line = 1

    def scan_tokens(self):
        while not self._is_at_end():
            self.start = self.current
            self._scan_token()

        self.tokens.append(Token(TokenType.EOF, '', None, self.line))
        return self.tokens

    def _is_at_end(self):
        return self.current >= len(self.source)

    def _advance(self):
        self.current += 1
        return self.source[self.current - 1]

    def _match(self, expected):
        if self._is_at_end():
            return False
        if self.source[self.current] != expected:
            return False

        self.current += 1
        return True

    def _peek(self):
        if self._is_at_end():
            return '\0'
        return self.source[self.current]

    def _peek_next(self):
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current + 1]

    def _is_digit(self, c):
        return ord('0') <= ord(c) <= ord('9')

    def _is_alpha(self, c):
        c = ord(c)
        return ord('a') <= c <= ord('z') or ord('A') <= c <= ord('Z') or c == ord('_')

    def _is_alpha_numeric(self, c):
        return self._is_digit(c) or self._is_alpha(c)

    def _identifier(self):
        while self._is_alpha_numeric(self._peek()):
            self._advance()

        text = self.source[self.start:self.current]
        token_type = TOKEN_TYPES.get(text, TokenType.IDENTIFIER)
        self._add_token(token_type)

    def _number(self):
        formatter = int
        while self._is_digit(self._peek()):
            self._advance()

        if self._peek() == '.' and self._is_digit(self._peek_next()):
            formatter = float
            self._advance()

            while self._is_digit(self._peek()):
                self._advance()

        value = self.source[self.start:self.current]
        self._add_token(TokenType.NUMBER, formatter(value))

    def _string(self, quote):
        while self._peek() != quote and not self._is_at_end():
            if self._peek() == '\n':
                self.line += 1
            self._advance()

        if self._is_at_end():
            self.error(self.line, "Unterminated string.")
            return

        self._advance()  # the ending quote

        value = self.source[self.start + 1: self.current - 1]
        self._add_token(TokenType.STRING, value)

    def _add_token(self, token_type, literal=None):
        text = self.source[self.start:self.current]
        self.tokens.append(Token(token_type, text, literal, self.line))

    def _consume_line(self):
        while self._peek() != '\n' and not self._is_at_end():
            self._advance()

    def _scan_token(self):
        c = self._advance()

        if c in ('(', ')', '{', '}', ',', '.', '-', '+', ';', '*', '?', ':'):
            self._add_token(TOKEN_TYPES[c])
        elif c in ('!', '=', '<', '>'):
            if self._match('='):
                c = f'{c}='
            self._add_token(TOKEN_TYPES[c])
        elif c == '/':
            if self._match('/'):  # // style comment
                self._consume_line()
            else:
                self._add_token(TokenType.SLASH)
        elif c == '#':  # Python style comment
            self._consume_line()
        elif c in (' ', '\r', '\t'):
            pass
        elif c == '\n':
            self.line += 1
        elif c in ('"', '\''):
            self._string(c)
        elif self._is_digit(c):
            self._number()
        elif self._is_alpha(c):
            self._identifier()
        else:
            self.error(self.line, f'Unexpected character: \'{c}\'')

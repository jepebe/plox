from enum import Enum, auto


class TokenType(Enum):
    # Single-character tokens.
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()

    COMMA = auto()
    DOT = auto()
    MINUS = auto()
    PLUS = auto()
    SEMICOLON = auto()
    SLASH = auto()
    STAR = auto()
    QUESTION_MARK = auto()
    COLON = auto()

    # One or two character tokens.
    BANG = auto()
    BANG_EQUAL = auto()

    EQUAL = auto()
    EQUAL_EQUAL = auto()

    GREATER = auto()
    GREATER_EQUAL = auto()

    LESS = auto()
    LESS_EQUAL = auto()

    # Literals.
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()

    # Keywords.
    AND = auto()
    BREAK = auto()
    CLASS = auto()
    ELSE = auto()
    FALSE = auto()
    FUN = auto()
    FOR = auto()
    IF = auto()
    NIL = auto()
    OR = auto()

    PRINT = auto()
    RETURN = auto()
    SUPER = auto()
    THIS = auto()
    TRUE = auto()
    VAR = auto()
    WHILE = auto()

    EOF = auto()


EQUALITY_TOKENS = (
    TokenType.BANG_EQUAL,
    TokenType.EQUAL_EQUAL
)

COMPARISON_TOKENS = (
    TokenType.GREATER,
    TokenType.GREATER_EQUAL,
    TokenType.LESS,
    TokenType.LESS_EQUAL
)

ADDITION_TOKENS = (
    TokenType.MINUS,
    TokenType.PLUS
)

MULTIPLICATION_TOKENS = (
    TokenType.SLASH,
    TokenType.STAR
)

KEYWORD_TOKENS = (
    TokenType.BREAK,
    TokenType.CLASS,
    TokenType.FUN,
    TokenType.VAR,
    TokenType.FOR,
    TokenType.IF,
    TokenType.WHILE,
    TokenType.PRINT,
    TokenType.RETURN
)

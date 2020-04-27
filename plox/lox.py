import sys

from plox.ast_printer import AstPrinter
from plox.interpreter import Interpreter
from plox.parser import Parser
from plox.plox_errors import PloxRuntimeError, PloxParserError
from plox.resolver import Resolver
from plox.scanner import Scanner
from plox.token_type import TokenType


def red(text):
    return color(text, 1)


def color(text, value=0):
    return '\u001b[38;5;%im%s\u001b[0m' % (value, text)


def green(text):
    return color(text, 3)


def blue(text):
    return color(text, 69)


def yellow(text):
    return color(text, 226)


class Lox(object):
    def __init__(self):
        self.had_error = False
        self.had_runtime_error = False
        self.interpreter = Interpreter(self.runtime_error)
        self.warning_count = 0
        self.error_count = 0

    def token_error(self, token, message, warning=False, after=False):
        if token.type == TokenType.EOF:
            self._report(token.line, " at end", message, warning)
        elif after:
            self._report(token.line, f' after \'{token.lexeme}\'', message, warning)
        else:
            self._report(token.line, f' at \'{token.lexeme}\'', message, warning)

    def error(self, token, message, warning=False):
        self._report(token.line, "", message, warning)

    def prompt_error(self, token, message):
        self.had_error = True

    def runtime_error(self, error):
        print(red(f'[RuntimeError at line {error.token.line}] {error.message}'))
        self.had_runtime_error = True

    def _report(self, line, where, message, warning):
        level = 'Error'
        color = red
        if warning:
            level = 'Warning'
            color = yellow
        print(color(f'[line {line}] {level}{where}: {message}'))
        if not warning:
            self.had_error = True
            self.error_count += 1
        else:
            self.warning_count += 1

    def run(self, source, error_handler):
        scanner = Scanner(source, self.token_error)
        parser = Parser(scanner.scan_tokens(), self.token_error)
        statements = parser.parse()

        if self.warning_count > 0 or self.error_count > 0:
            print(f'{self.error_count} error(s) and {self.warning_count} warning(s) occurred')

        if self.had_error:
            return

        resolver = Resolver(self.token_error, self.interpreter)
        resolver.resolve(statements)

        if self.warning_count > 0 or self.error_count > 0:
            print(f'{self.error_count} error(s) and {self.warning_count} warning(s) occurred')

        if self.had_error:
            return

        self.interpreter.interpret(statements)


def run_file(path):
    with open(path, 'r') as lf:
        data = lf.read()

    lox = Lox()
    lox.run(data, lox.error)

    if lox.had_error:
        sys.exit(65)

    if lox.had_runtime_error:
        sys.exit(70)


def run_prompt():
    lox = Lox()

    while True:
        print('> ', end='')
        data = input()
        lox.run(data, lox.prompt_error)

        if lox.had_error:
            lox.had_error = False
            scanner = Scanner(data, lox.token_error)
            parser = Parser(scanner.scan_tokens(), lox.error)

            try:
                expr = parser._expression()
                print(lox.interpreter.evaluate(expr))
            except (PloxParserError, PloxRuntimeError) as e:
                lox.runtime_error(e)

        lox.had_error = False
        lox.had_runtime_error = False


if __name__ == '__main__':
    if len(sys.argv) > 2:
        print('Usage: plox [script]')
        sys.exit(64)
    elif len(sys.argv) == 2:
        run_file(sys.argv[1])
    else:
        run_prompt()

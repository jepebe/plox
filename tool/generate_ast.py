import sys


def _writeln(f):
    def w(line):
        f.write(f'{line}\n')

    return w


def define_type(writer, base_name, class_name, fields):
    writer(f'class {class_name}({base_name}):')
    writer(f'\tdef __init__(self, {", ".join(fields)}):')
    for field in fields:
        field = field.split(':')[0]
        writer(f'\t\tself.{field} = {field}')
    writer(f'')
    writer(f'\tdef accept(self, visitor):')
    func_name = f'visit_{class_name.lower()}_{base_name.lower()}'
    writer(f'\t\treturn visitor.{func_name}(self)')
    writer(f'')
    writer(f'')


def define_visitor(writer, base_name, types):
    writer(f'class {base_name}Visitor(object):')
    for t in types:
        class_name = t.split(':')[0].strip()
        func_name = f'visit_{class_name.lower()}_{base_name.lower()}'
        writer(f'\tdef {func_name}(self, {base_name.lower()}: {class_name}) -> object:')
        writer(f'\t\tprint("[{func_name}] Not implemented!")')
        writer(f'\t\treturn None')
        writer(f'')
    writer(f'')


def define_ast(output_dir, base_name, imports, types):
    with open(f'{output_dir}/{base_name.lower()}.py', 'w') as ast:
        writer = _writeln(ast)
        for imp in imports:
            writer(imp)
        writer('')
        writer('')
        writer(f'class {base_name}(object):')
        writer(f'\tdef accept(self, visitor):')
        writer(f'\t\tprint("[{base_name}.accept()] Not implemented!")')
        writer(f'')
        writer(f'')

        for t in types:
            class_name, fields = t.split(':')
            fields = [field.strip() for field in fields.split(',')]
            fields = ['%s: %s' % (f.split(' ')[1], f.split(' ')[0]) for f in fields]
            define_type(writer, base_name, class_name.strip(), fields)

        define_visitor(writer, base_name, types)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: generate_ast [output_directory]')
        sys.exit(1)

    output_dir = sys.argv[1]

    imports = [
        'from plox.token import Token',
        'from typing import List'
    ]
    define_ast(output_dir, 'Expr', imports, [
        "Assign   : Token name, Expr value",
        "Binary   : Expr left, Token operator, Expr right",
        "Call     : Expr callee, Token paren, List[Expr] arguments",
        "Get      : Expr objct, Token name",
        "Grouping : Expr expression",
        "Literal  : object value",
        "Logical  : Expr left, Token operator, Expr right",
        "Set      : Expr objct, Token name, Expr value",
        "Ternary  : Expr condition, Expr then_branch, Expr else_branch",
        "This     : Token keyword",
        "Unary    : Token operator, Expr right",
        "Variable : Token name"
    ])

    imports = [
        'from plox.expr import Expr',
        'from plox.token import Token',
        'from typing import List'
    ]
    define_ast(output_dir, 'Stmt', imports, [
        "Block      : List[Stmt] statements",
        "Break      : Token name",
        "Function   : Token name, List[Token] params, List[Stmt] body, bool anonymous, bool getter",
        "Class      : Token name, List[Function] methods",
        "Expression : Expr expression",
        "If         : Expr condition, Stmt then_branch, Stmt else_branch",
        "Print      : Expr expression",
        "Return     : Token keyword, Expr value",
        "Var        : Token name, Expr initializer",
        "While      : Expr condition, Stmt body"
    ])

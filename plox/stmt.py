from plox.expr import Expr, Variable
from plox.token import Token
from typing import List


class Stmt(object):
	def accept(self, visitor):
		print("[Stmt.accept()] Not implemented!")


class Block(Stmt):
	def __init__(self, statements: List[Stmt]):
		self.statements = statements

	def accept(self, visitor):
		return visitor.visit_block_stmt(self)


class Break(Stmt):
	def __init__(self, name: Token):
		self.name = name

	def accept(self, visitor):
		return visitor.visit_break_stmt(self)


class Function(Stmt):
	def __init__(self, name: Token, params: List[Token], body: List[Stmt], anonymous: bool, getter: bool):
		self.name = name
		self.params = params
		self.body = body
		self.anonymous = anonymous
		self.getter = getter

	def accept(self, visitor):
		return visitor.visit_function_stmt(self)


class Class(Stmt):
	def __init__(self, name: Token, superclass: Variable, methods: List[Function]):
		self.name = name
		self.superclass = superclass
		self.methods = methods

	def accept(self, visitor):
		return visitor.visit_class_stmt(self)


class Expression(Stmt):
	def __init__(self, expression: Expr):
		self.expression = expression

	def accept(self, visitor):
		return visitor.visit_expression_stmt(self)


class If(Stmt):
	def __init__(self, condition: Expr, then_branch: Stmt, else_branch: Stmt):
		self.condition = condition
		self.then_branch = then_branch
		self.else_branch = else_branch

	def accept(self, visitor):
		return visitor.visit_if_stmt(self)


class Print(Stmt):
	def __init__(self, expression: Expr):
		self.expression = expression

	def accept(self, visitor):
		return visitor.visit_print_stmt(self)


class Return(Stmt):
	def __init__(self, keyword: Token, value: Expr):
		self.keyword = keyword
		self.value = value

	def accept(self, visitor):
		return visitor.visit_return_stmt(self)


class Var(Stmt):
	def __init__(self, name: Token, initializer: Expr):
		self.name = name
		self.initializer = initializer

	def accept(self, visitor):
		return visitor.visit_var_stmt(self)


class While(Stmt):
	def __init__(self, condition: Expr, body: Stmt):
		self.condition = condition
		self.body = body

	def accept(self, visitor):
		return visitor.visit_while_stmt(self)


class StmtVisitor(object):
	def visit_block_stmt(self, stmt: Block) -> object:
		print("[visit_block_stmt] Not implemented!")
		return None

	def visit_break_stmt(self, stmt: Break) -> object:
		print("[visit_break_stmt] Not implemented!")
		return None

	def visit_function_stmt(self, stmt: Function) -> object:
		print("[visit_function_stmt] Not implemented!")
		return None

	def visit_class_stmt(self, stmt: Class) -> object:
		print("[visit_class_stmt] Not implemented!")
		return None

	def visit_expression_stmt(self, stmt: Expression) -> object:
		print("[visit_expression_stmt] Not implemented!")
		return None

	def visit_if_stmt(self, stmt: If) -> object:
		print("[visit_if_stmt] Not implemented!")
		return None

	def visit_print_stmt(self, stmt: Print) -> object:
		print("[visit_print_stmt] Not implemented!")
		return None

	def visit_return_stmt(self, stmt: Return) -> object:
		print("[visit_return_stmt] Not implemented!")
		return None

	def visit_var_stmt(self, stmt: Var) -> object:
		print("[visit_var_stmt] Not implemented!")
		return None

	def visit_while_stmt(self, stmt: While) -> object:
		print("[visit_while_stmt] Not implemented!")
		return None



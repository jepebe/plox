from plox.token import Token
from typing import List


class Expr(object):
	def accept(self, visitor):
		print("[Expr.accept()] Not implemented!")


class Assign(Expr):
	def __init__(self, name: Token, value: Expr):
		self.name = name
		self.value = value

	def accept(self, visitor):
		return visitor.visit_assign_expr(self)


class Binary(Expr):
	def __init__(self, left: Expr, operator: Token, right: Expr):
		self.left = left
		self.operator = operator
		self.right = right

	def accept(self, visitor):
		return visitor.visit_binary_expr(self)


class Call(Expr):
	def __init__(self, callee: Expr, paren: Token, arguments: List[Expr]):
		self.callee = callee
		self.paren = paren
		self.arguments = arguments

	def accept(self, visitor):
		return visitor.visit_call_expr(self)


class Get(Expr):
	def __init__(self, objct: Expr, name: Token):
		self.objct = objct
		self.name = name

	def accept(self, visitor):
		return visitor.visit_get_expr(self)


class Grouping(Expr):
	def __init__(self, expression: Expr):
		self.expression = expression

	def accept(self, visitor):
		return visitor.visit_grouping_expr(self)


class Literal(Expr):
	def __init__(self, value: object):
		self.value = value

	def accept(self, visitor):
		return visitor.visit_literal_expr(self)


class Logical(Expr):
	def __init__(self, left: Expr, operator: Token, right: Expr):
		self.left = left
		self.operator = operator
		self.right = right

	def accept(self, visitor):
		return visitor.visit_logical_expr(self)


class Set(Expr):
	def __init__(self, objct: Expr, name: Token, value: Expr):
		self.objct = objct
		self.name = name
		self.value = value

	def accept(self, visitor):
		return visitor.visit_set_expr(self)


class Subscript(Expr):
	def __init__(self, objct: Expr, bracket: Token, index: Expr):
		self.objct = objct
		self.bracket = bracket
		self.index = index

	def accept(self, visitor):
		return visitor.visit_subscript_expr(self)


class Super(Expr):
	def __init__(self, keyword: Token, method: Token):
		self.keyword = keyword
		self.method = method

	def accept(self, visitor):
		return visitor.visit_super_expr(self)


class Ternary(Expr):
	def __init__(self, condition: Expr, then_branch: Expr, else_branch: Expr):
		self.condition = condition
		self.then_branch = then_branch
		self.else_branch = else_branch

	def accept(self, visitor):
		return visitor.visit_ternary_expr(self)


class This(Expr):
	def __init__(self, keyword: Token):
		self.keyword = keyword

	def accept(self, visitor):
		return visitor.visit_this_expr(self)


class Unary(Expr):
	def __init__(self, operator: Token, right: Expr):
		self.operator = operator
		self.right = right

	def accept(self, visitor):
		return visitor.visit_unary_expr(self)


class Variable(Expr):
	def __init__(self, name: Token):
		self.name = name

	def accept(self, visitor):
		return visitor.visit_variable_expr(self)


class ExprVisitor(object):
	def visit_assign_expr(self, expr: Assign) -> object:
		print("[visit_assign_expr] Not implemented!")
		return None

	def visit_binary_expr(self, expr: Binary) -> object:
		print("[visit_binary_expr] Not implemented!")
		return None

	def visit_call_expr(self, expr: Call) -> object:
		print("[visit_call_expr] Not implemented!")
		return None

	def visit_get_expr(self, expr: Get) -> object:
		print("[visit_get_expr] Not implemented!")
		return None

	def visit_grouping_expr(self, expr: Grouping) -> object:
		print("[visit_grouping_expr] Not implemented!")
		return None

	def visit_literal_expr(self, expr: Literal) -> object:
		print("[visit_literal_expr] Not implemented!")
		return None

	def visit_logical_expr(self, expr: Logical) -> object:
		print("[visit_logical_expr] Not implemented!")
		return None

	def visit_set_expr(self, expr: Set) -> object:
		print("[visit_set_expr] Not implemented!")
		return None

	def visit_subscript_expr(self, expr: Subscript) -> object:
		print("[visit_subscript_expr] Not implemented!")
		return None

	def visit_super_expr(self, expr: Super) -> object:
		print("[visit_super_expr] Not implemented!")
		return None

	def visit_ternary_expr(self, expr: Ternary) -> object:
		print("[visit_ternary_expr] Not implemented!")
		return None

	def visit_this_expr(self, expr: This) -> object:
		print("[visit_this_expr] Not implemented!")
		return None

	def visit_unary_expr(self, expr: Unary) -> object:
		print("[visit_unary_expr] Not implemented!")
		return None

	def visit_variable_expr(self, expr: Variable) -> object:
		print("[visit_variable_expr] Not implemented!")
		return None



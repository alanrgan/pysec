from parsec import *
from collections import namedtuple

class Statement(object):
	def __init__(self, val):
		self.val = val

class MatchStatement(object):
	def __init__(self, stmts):
		self.stmts = stmts

class IfStatement(object):
	def __init__(self, cond, conseq, alt):
		self.cond = cond
		self.conseq = conseq
		self.alt = alt

class ForStatement(object):
	def __init__(self, var, fexpr, body):
		self.var = var
		self.expr = fexpr
		self.body = body

class BinOpExpr(object):
	def __init__(self, op, left, right):
		self.op = op
		self.left = left
		self.right = right

	def eval(self):
		left = self.left if not isinstance(self.left, BinOpExpr) else self.left.eval()
		right = self.right if not isinstance(self.right, BinOpExpr) else self.right.eval()
		return opfuncs[self.op](left, right)

	def __repr__(self):
		left = "(%s)" % repr(self.left) if isinstance(self.left, BinOpExpr) else repr(self.left)
		right = "(%s)" % repr(self.right) if isinstance(self.right, BinOpExpr) else repr(self.right)
		return "%s %c %s" % (left, self.op, right)

ks = ["let", "if", "else", "return", "break",
	  "def", "match", "true", "false", "for", "in"]
binops = "+-*/^"
OpInfo = namedtuple("OpInfo", "prec, assoc")

precedence_map = {
	'+': OpInfo(4, 'LEFT'),
	'-': OpInfo(4, 'LEFT'),
	'*': OpInfo(5, 'LEFT'),
	'/': OpInfo(5, 'LEFT'),
	'^': OpInfo(6, 'RIGHT')
}
opfuncs = {
	'+': lambda x,y: x+y,
	'-': lambda x,y: x-y,
	'*': lambda x,y: x*y,
	'/': lambda x,y: x/y,
	'^': lambda x,y: x**y
}

for i,k in enumerate(ks):
	keyword = String(k) if i == 0 else keyword|String(k)

kwords = keyword
@Parser
def keyword():
	x, _ = yield kwords >> NotFollowedBy(alpha())
	produce(x)
#keyword = generate(keyword >> NotFollowedBy(alpha()))

comma = Char(',')
integer = parsec_map(int, concat(Many1(digit())))
lbrace = Char('{')
rbrace = Char('}')
lbrack = Char('[')
rbrack = Char(']')
whitespace = generate(concat(Many(OneOf(" \n\t\r"))))
wslbrace = Surround(Char('{'), whitespace)
wsrbrace = Surround(Char('}'), whitespace)
identChars= alpha() >> concat(Many(alpha()|digit()|Char('_')))

ident = identChars ^ keyword
identws = Surround(ident, whitespace)
boolean = String("true").result(True) | String("false").result(False)
string = Char('"') << concat(ManyUntil(AnyChar(), Char('"')))

def spaced(parser):
	return Surround(parser, whitespace)

@Parser
def statement():
	x, _ = yield spaced(
					   exprStatement
				 	 | compound
				 	 | if_statement
				 	 | for_statement
				 )
	produce(x)

@Parser
def compound():
	x = (yield Between(Char('{'), spaced(statementList), Char('}')))[0]
	produce(x)

@Parser
def statementList():
	x, _ = yield Many(spaced(statement))
	produce(x)

@Parser
def if_statement():
	yield String("if")
	cond = (yield expr)[0]
	yield wslbrace
	stmts = (yield statementList)[0]
	yield wsrbrace
	el = (yield Try(String("else") << statement))[0]
	produce(IfStatement(cond, stmts, el))

@Parser
def for_statement():
	yield String("for")
	var = (yield identws)[0]
	yield String("in")
	exp = (yield expr)[0]
	body = (yield spaced(compound))[0]
	produce(ForStatement(var,exp,body))

@Parser
def match_statement():
	yield spaced(String("match"))
	stmts, _ = yield Between(Char('{'), statementList, Char('}'))
	produce(MatchStatement(stmts))

"""
The following is an example of extending the Parser class for more than simple
'feed-back' parsing.
"""
class expr(Parser):
	def __init__(self, precedence=0):
		self.precedence = precedence

	def parse_body(self, _string, acc=""):
		x, _ = yield atom
		while True:
			op = (yield Try(PeekChar()))[0]
			if op and op in binops:
				next_precedence, assoc = precedence_map[op]
				if self.precedence >= next_precedence:
					break
				x, _ = yield infix_expr((op, assoc), x, next_precedence)
			else:
				break
		produce(x)

class infix_expr(Parser):
	def __init__(self, opinfo, exp, precedence):
		self.precedence = precedence-1 if opinfo[1] == 'RIGHT' else precedence
		self.expr = exp
		self.op = opinfo[0]

	def parse_body(self, _string, acc=""):
		if self.op in binops:
			yield OneOf(binops)
			right, _ = yield expr(self.precedence)
			produce(BinOpExpr(self.op, self.expr, right))
		else:
			yield ParseError("unexpected token " + repr(self.op))

atom = spaced(
	  ident
	| integer
	| boolean
	| string
	| Between(Char('('),expr(),Char(')'))
)
array = generate(Between(lbrack, SepBy(expr(), comma), rbrack))

exprStatement = expr().discard(Char(';'))
print generate(expr())("3+4*5^2")
print generate(string)('"hello world"')
"""
ms = match_statement('''
	match {
		hello;
		false;
		true;
		3;
	}
''')
ifs = if_statement('''if true {
		3;
	} else if true {
		4;
	}
''')
fexpr = statement('''
	for x in 342 {
		for z in twenty {
			5;
		}
		if true {
			7;
		}
	}''')"""
from parsec import *

class Statement():
	def __init__(self, val):
		self.val = val

class MatchStatement():
	def __init__(self, stmts):
		self.stmts = stmts

class IfStatement():
	def __init__(self, cond, conseq, alt):
		self.cond = cond
		self.conseq = conseq
		self.alt = alt

class ForStatement():
	def __init__(self, var, fexpr, body):
		self.var = var
		self.expr = fexpr
		self.body = body

ks = ["let", "if", "else", "return", "break",
	  "def", "match", "true", "false", "for", "in"]

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

expr = spaced(ident | integer | boolean)
exprStatement = expr.discard(Char(';'))

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
	}''')
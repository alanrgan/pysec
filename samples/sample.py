from parsec import *

class Statement():
	def __init__(self, val):
		self.val = val

class MatchStatement():
	def __init__(self, stmts):
		self.stmts = stmts

ks = ["let", "if", "else", "return", "break",
	  "def", "match", "true", "false"]

for i,k in enumerate(ks):
	keyword = String(k) if i == 0 else keyword|String(k)
keyword = generate(keyword >> NotFollowedBy(alpha()))

comma = Char(',')
integer = parsec_map(int, concat(Many1(digit())))
lbrace = Char('{')
rbrace = Char('}')
lbrack = Char('[')
rbrack = Char(']')
identChars= alpha() >> concat(Many(alpha()|digit()|Char('_')))
whitespace = generate(concat(Many(OneOf(" \n\t\r"))))

ident = identChars ^ keyword
boolean = String("true").result(True) | String("false").result(False)
expr = ident | integer | boolean

exprStatement = expr.discard(Char(';'))

statement = parsec_map(Statement, exprStatement)

@Parser
def match_statement():
	yield Surround(String("match"), whitespace)
	stmts, _ = yield Between(Char('{'), Many(Surround(statement, whitespace)), Char('}'))
	produce(MatchStatement(stmts))

ms = match_statement('''
	match {
		hello;
		false;
		true;
		3;
	}
''')
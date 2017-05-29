from parsec import *

def ident():
	return alpha() >> Many(alpha()|digit()|Char('_'))

whitespace = generate(Many1(OneOf(" \r\n\t")))
maybeSpace = generate(Many(OneOf(" \r\n\t")))
"""
whitespace = Many(OneOf(" \r\t\n"))
w = whitespace > String("hello")
print w("    hello")
"""
#b = Char('x') >> Between(Char("{"), alpha(), Char("}"))
#print b("x{x}")
#print SepBy(ident(),whitespace())("hello world")
#parser = Char('x') >> Char('y') << Char('k') << Char('z') >> Char('d')
#print parser("xykzd")

"""
class Statement:
	def __init__(self):
		self.
"""

integer = parsec_map(int, Many1(digit()))
wss = parsec_map(len, whitespace)

@Parser
def spacedInt():
	ws = yield maybeSpace
	x, _ = yield integer
	yield maybeSpace
	produce(x)

@Parser
def foo():
	i, _ = yield spacedInt
	produce(i)

@Parser
def mytest():
	yield Many(Char('x'))
	x, _ = yield Char('y') >> Char ('z')
	produce(x)

@Parser
def bar():
	i, _ = yield foo
	produce(i)

@Parser
def baz():
	i, _ = yield spacedInt | Char('w')
	yield Many(Char('x'))
	produce(i)

x = generate(Many1(Char('x')))
print baz("wxxxx")
"""
print integer("1234")
m = many(Char('x'))
b = between(Many1(Char('x')),Char('y'),Char('x'))
print b("xxxxxyx")
parser = generate(Char('x') >> Between(Char('{'),Char('x'),Char('}')))
print parser("x{x}")
parser = generate(Char('x') >> Char('y') << Char('k') << Char('z') >> Char('d'))
print parser("xykzd")
parser = generate(SepBy(Char('x'), Char(',')))
print parser("x,x,x,x,x")
"""
#m = many(Char('x'))
"""
print mytest('xxxxxyz')
#m = generate(Many(Char('x')))
#print foo('xxxxxx')
print spacedInt("  5   ")
parser = generate(SepBy(integer, Char(",")))
print parser("1,2,3,4")
parser = generate(SepBy(Char('x'), Char(',')))
print parser("x,x,x,x,x,x")"""
#print type(bar("   3 "))
#print wss("     ")
#print many('1234xy')
#print integer.parse("12345")
#a = integer.run("1234")
#print a
from parsec import *

def ident():
	return alpha() >> Many(alpha()|digit()|Char('_'))

def whitespace():
	return Many1(OneOf(" \n\r\t"))

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

@Parser
def integer():
	x, _ = yield Many1(digit())
	produce(int(x))

@Parser
def x():
	x, _ = yield Many1(Char('x'))
	produce(x)

def many(parser):
	@Parser
	def inner():
		x, _  = yield Many(parser)#Many(digit()) >> Char('x') >> Char('y')
		produce(x)
	return inner

def between(start, body, end):
	@Parser
	def inner():
		x, _ = yield Between(start, body, end)
		produce(x)
	return inner

#m = Many(Char('x'))
m = many(Char('x'))
b = between(Many1(Char('x')),Char('y'),Char('x'))
print b("xxxxxyx")
parser = generate(Char('x') >> Between(Char('{'),Char('x'),Char('}')))
print parser("x{x}")
parser = generate(Char('x') >> Char('y') << Char('k') << Char('z') >> Char('d'))
print parser("xykzd")
#print many('1234xy')
#print integer.parse("12345")
#a = integer.run("1234")
#print a
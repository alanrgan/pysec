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

def no_rest(fn):
	def wrapper():
		yield fn().next()
		yield ""
	return wrapper

class MyParser(Parser):
	def __init__(self, fn):
		Parser.__init__(self)
		self.fn = fn

	def parse_body(self, string, acc=""):
		return self.fn()

@MyParser
def integer():
	x, _ = yield Char('x')
	y, _ = yield Char('y')
	produce({x:y})

print integer.parse("xy")
#a = integer.run("1234")
#print a
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

class MyParser(Parser):
	def __init__(self, fn):
		Parser.__init__(self)
		self.fn = fn

	def run(self, string):
		return self.parse(string, no_send =)

	def parse_body(self, string, acc=""):
		return self.fn(string)

#class Integer(MyParser):
#	def __init__(self):
#		Parser.__init__(self)

#	def parse_body(self, string, acc=""):
@MyParser
def integer(string):
	number = Many1(digit())
	num, rest, error = number.parse(string)
	yield int(num)

a = integer.run("1234")
print a
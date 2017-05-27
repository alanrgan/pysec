from parsec import *
import unittest

"""
xyz = Many(Char('x')) >> Many(Char('y')) >> Char('z')
print xyz('yyyyz')
print xyz('xxxxxyz')
xs = Many1(Char('x')) | Many(Char('y'))
print xs('yyy')
hello_world = String("Hello") >> Char(" ") >> String("World")
print hello_world("Hello World")

ds = Char('x') >> Many(digit) >> Char("x")
print (digit|ds)("x1234x")

whitespace = Many(OneOf(" \n\r\t"))
print (whitespace << String("hello"))("      hello")
ps = Char("\\") >> Char('y') | Char('z')
print ps("\\y")
print ps("z")
"""
#print ps("\\z")

def ident():
	return alpha() >> Many(alpha()|digit()|Char('_'))

def integer():
	return Many1(digit())

def parse_int(string):
	return int(integer()(string)[0])

def whitespace():
	return Many1(OneOf(" \n\r\t"))

def block():
	word = Between(whitespace(), ident(), whitespace())
	return Between(Char('{'),word,Char('}'))

class BasicTest(unittest.TestCase):
	def test_chain(self):
		parser = Char('x') >> Between(Char('{'),Char('x'),Char('}'))
		self.assertEquals(parser("x{x}")[0], "xx")
		parser = Char('x') >> Char('y') << Char('k') << Char('z') >> Char('d')
		self.assertEquals(parser("xykzd")[0], "xzd")

	def test_chain_and_alternative(self):
		parser = Char("\\") >> Char('y') >> Char('x') | Char('z')
		self.assertEquals(parser("\\yx")[0], "\\yx")
		self.assertEquals(parser("z")[0], "z")
		self.assertRaises(ParseError, parser, "yxz")
		self.assertRaises(ParseError, parser, "\\z")
		self.assertRaises(ParseError, parser, "\\yz")

	def test_alternatives(self):
		parser = String("hello") | String("what") | Char("x")
		self.assertEquals(parser("helloworld!")[0], "hello")
		self.assertEquals(parser("what")[0], "what")
		self.assertEquals(parser("xyz")[0], "x")
		self.assertRaises(ParseError, parser, "world")

class CombinatorTest(unittest.TestCase):
	def test_block(self):
		parser = block()
		self.assertEquals(parser("{    hello_world  }")[0], "hello_world")
		self.assertRaises(ParseError, parser, "hello_world }")

	def test_sep_by(self):
		parser = SepBy(Many1(alpha()), Char(','))
		self.assertEquals(parser("one,two,three,four")[0], ["one", "two", "three", "four"])
		self.assertEquals(parser("onetwothreefour")[0], ["onetwothreefour"])
		self.assertRaises(ParseError, parser, "one,")

		parser = SepBy(ident(), whitespace())
		self.assertEquals(parser("hello   world foo bar baz")[0], ["hello", "world", "foo", "bar", "baz"])

if __name__ == '__main__':
	unittest.main()

#print block()("{   hello_world   }")


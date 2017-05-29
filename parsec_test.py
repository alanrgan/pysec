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

integer = parsec_map(int,Many1(digit()))
whitespace = generate(Many1(OneOf(" \r\n\t")))
maybeSpace = generate(Many(OneOf(" \r\n\t")))

def block():
	word = Between(whitespace(), ident(), whitespace())
	return generate(Between(Char('{'),word,Char('}')))

class BasicTest(unittest.TestCase):
	def test_chain(self):
		parser = generate(Char('x') >> Between(Char('{'),Char('x'),Char('}')))
		self.assertEquals(parser("x{x}"), "xx")
		parser = generate(Char('x') >> Char('y') << Char('k') << Char('z') >> Char('d'))
		self.assertEquals(parser("xykzd"), "xzd")

	def test_chain_and_alternative(self):
		parser = generate(Char("\\") >> Char('y') >> Char('x') | Char('z'))
		self.assertEquals(parser("\\yx"), "\\yx")
		self.assertEquals(parser("z"), "z")
		self.assertRaises(ParseError, parser, "yxz")
		self.assertRaises(ParseError, parser, "\\z")
		self.assertRaises(ParseError, parser, "\\yz")

	def test_alternatives(self):
		parser = generate(String("hello") | String("what") | Char("x"))
		self.assertEquals(parser("helloworld!"), "hello")
		self.assertEquals(parser("what"), "what")
		self.assertEquals(parser("xyz"), "x")
		self.assertRaises(ParseError, parser, "world")

class StringCombinatorTest(unittest.TestCase):
	def test_between(self):
		parser = between(Many1(Char('x')),Char('y'),Char('x'))
		self.assertEquals(parser("xxxxxxyx"), "y")
		self.assertRaises(ParseError, parser, "yx")
		self.assertEquals(parser("xxxyxx"), "y")

	def test_sep_by(self):
		parser = generate(SepBy(Char('x'), Char(',')))
		self.assertEquals(parser('x,x,x,x,x,x'), ["x","x","x","x","x","x"])
		self.assertRaises(ParseError, parser, 'x,x,x,')
		parser = generate(SepBy(integer, Char(',')))
		self.assertEquals(parser('1,2,3,4,5'), range(1,6))
		parser = generate(SepBy(integer, whitespace))
		self.assertEquals(parser('1 2 3  4 5 6'), range(1,7))

	"""
	def test_block(self):
		parser = generate(block())
		self.assertEquals(parser("{    hello_world  }"), "hello_world")
		self.assertRaises(ParseError, parser, "hello_world }")
	"""

	"""
	def test_sep_by(self):
		parser = generate(SepBy(Many1(alpha()), Char(',')))
		self.assertEquals(parser("one,two,three,four"), ["one", "two", "three", "four"])
		self.assertEquals(parser("onetwothreefour"), ["onetwothreefour"])
		self.assertRaises(ParseError, parser, "one,")

		parser = generate(SepBy(ident(), whitespace()))
		self.assertEquals(parser("hello   world foo bar baz"), ["hello", "world", "foo", "bar", "baz"])
	"""

class TypedCombinatorTest(unittest.TestCase):
	def __init__(self, *args, **kwargs):
		super(TypedCombinatorTest, self).__init__(*args, **kwargs)
		self.init_parsers()

	def init_parsers(self):
		self.maybeSpace = generate(Many1(OneOf(" \r\n\t")))
		@Parser
		def spacedInt():
			ws = yield maybeSpace
			x, _ = yield integer
			yield maybeSpace
			produce(x)
		self.spaced_int = spacedInt

		@Parser
		def yield_generated():
			i, _ = yield spacedInt
			produce(i)
		self.yield_generated = yield_generated

	def test_basic_int(self):
		parser = integer
		self.assertEquals(parser("1234"), 1234)
		self.assertRaises(ParseError, parser, "xyz")

	def test_spaced_int(self):
		@Parser
		def parser():
			yield self.maybeSpace
			x, _ = yield integer
			yield self.maybeSpace
			produce(x)
		self.assertEquals(parser("    12345 "), 12345)

	def test_yield_generated(self):
		parser = self.yield_generated
		self.assertEquals(parser("    124141    "), 124141)
		self.assertRaises(ParseError, parser, "     xyz  ")

if __name__ == '__main__':
	unittest.main()

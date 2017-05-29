from parsec import *
import unittest

def ident():
	return alpha() >> Many(alpha()|digit()|Char('_'))

integer = parsec_map(int,concat(Many1(digit())))
whitespace = generate(concat(Many1(OneOf(" \r\n\t"))))
maybeSpace = generate(concat(Many(OneOf(" \r\n\t"))))

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

	def test_xor(self):
		forbidden = ["let", "return", "one"]
		fn = lambda x: String(x).discard(NotFollowedBy(alpha()))
		parser = concat(Many1(alpha())) ^ map(fn, forbidden)
		self.assertEquals(parser("hello"), "hello")
		self.assertRaises(ParseError, parser, "let")

class StringCombinatorTest(unittest.TestCase):
	def test_between(self):
		parser = between(concat(Many1(Char('x'))),Char('y'),Char('x'))
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
		parser = generate(SepBy(integer, Between(whitespace, Char('z'), whitespace)))
		self.assertEquals(parser("123   z  1234 z     6"), [123,1234,6])

	def test_end_by(self):
		mystring = parsec_map(lambda x: ''.join(x), Many1(alpha()))
		parser = generate(EndBy(mystring, Char(';')))
		self.assertEquals(parser("one;two;three;"), ["one","two", "three"])
		self.assertRaises(ParseError, parser, "two;four")

class TypedCombinatorTest(unittest.TestCase):
	def __init__(self, *args, **kwargs):
		super(TypedCombinatorTest, self).__init__(*args, **kwargs)
		self.init_parsers()

	def init_parsers(self):
		self.maybeSpace = generate(concat(Many1(OneOf(" \r\n\t"))))
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

	def test_not_followed_by(self):
		@Parser
		def parser():
			yield String("let")
			yield NotFollowedBy(alpha())
			produce(True)
		self.assertEquals(parser("let "), True)
		self.assertRaises(ParseError, parser, "lets")

if __name__ == '__main__':
	unittest.main()

from enum import Enum
import copy
import inspect
import re

def isgenstarted(gen):
	return gen.gi_frame.f_lasti != -1

class NextType(Enum):
	Chain, Alternative, Discard = range(3)

class Discard(Enum):
	NONE, RIGHT, LEFT = range(3)

class ReturnVal:
	def __init__(self, val):
		self.value = val

class Parsec:
	def __init__(self):
		self.error = None
		self.next_parser = None
		self.type = None
		self.mapfn = lambda x: x

	def __call__(self, *args):
		return self.parse(args[0])

	def __rshift__(self, other):
		return Chain(self, other, discard=False)

	def __or__(self, other):
		return generate(Alternative(self, other))

	def __lshift__(self, other):
		"""Discard"""
		return generate(Chain(self, other, discard=True))

	def __xor__(self, other):
		return generate(Only(self, other))

	def discard(self, other):
		@Parser
		def parser():
			x, _ = yield self
			_, rest = yield other
			produce(x)
		return parser

	def add(self, other, ty, head=True):
		nself = copy.deepcopy(self) if head else self
		othercpy = copy.deepcopy(other)
		nself.type = ty
		if nself.next_parser:
			nself.next_parser.add(othercpy, ty, False)
		else:
			nself.next_parser = othercpy
		return nself

	def parse_help(self, rest, acc, mres, res, gens=None, parser=None):
		if parser is None:
			parser = gens.send(mres)
		ps = parser.parse_body(rest, acc)

		if isinstance(parser, Parser):
			try:
				while True:
					if isgenstarted(ps):
						a = ps.send(mres)
					else:
						a = ps.next()
					ms = self.parse_help(rest, acc, mres, res, parser=a)
					if len(ms) == 1:
						raise ms[0]
					res, rest = ms
					mres = ms
			except ReturnVal as stopped:
				mres = [stopped.value, ms[1]]
		else:
			mres = list(ps)
		return mres

	def parse(self, string, acc="", suppress=False, no_send=False):
		res, rest = acc, string
		try:
			gens = self.parse_body(string, acc)
			mres, parser = None, None
			while True:
				mres = self.parse_help(rest, acc, mres, res, gens)
				if mres and isinstance(mres[0], ParseError):
					raise mres[0]
				elif mres:
					_, rest = mres
		except ReturnVal as stop:
			return stop.value

	def result(self, value):
		return parsec_map(lambda _: value, self)

	def parse_body(self, string, acc=""):
		pass

	def send_rest(self, result, rest, error, suppress):
		if self.next_parser:
			if self.type == NextType.Alternative:
				if error:
					return self.next_parser.parse(rest, result, suppress)
			elif error and not suppress:
				raise error
			else:
				return self.next_parser.parse(rest, result, suppress)
		elif error and not suppress:
			raise error
		return result, rest, error

	def parsec_map(self, fn):
		self.mapfn = fn
		return self

class Parser(Parsec):
	def __init__(self, fn):
		Parsec.__init__(self)
		self.fn = fn

	def parse_body(self, string, acc=""):
		return self.fn()

class Only(Parsec):
	"""
	Succeeds if the first parser succeeds and the other parsers fail
	on the same input.
	Ex:
		Only(alpha(), Char('x')) will parse any character except 'x'
	"""
	def __init__(self, first, others):
		Parsec.__init__(self)
		self.first = first
		if type(others) is not list:
			others = [others]
		self.others = others

	def parse_body(self, string, acc=None):
		inner = generate_rest(self.first)
		x, rest = inner(string)
		for i, parser in enumerate(self.others):
			try:
				x = generate(parser)(string)
				yield ParseError("Found unexpected %s" % repr(x))
				return
			except ParseError:
				continue
		yield x
		yield rest

class Chain(Parsec):
	def __init__(self, first, other, discard=False):
		Parsec.__init__(self)
		self.others = [first, other]
		self.discard = {0: discard}

	def __rshift__(self, other):
		nself = copy.deepcopy(self)
		nself.discard[len(nself.others)-1] = False
		nself.others.append(other)
		return nself

	def __lshift__(self, other):
		nself = copy.deepcopy(self)
		nself.discard[len(nself.others)-1] = True
		nself.others.append(other)
		return nself

	def parse_body(self, string, acc=None):
		result, prevacc, rest = "", acc, string
		res = ""
		for i, parser in enumerate(self.others):
			inner = generate_rest(parser)
			x = inner(rest)
			if isinstance(x, tuple):
				res, rest = x
			else:
				res = x
			if i < len(self.discard) and self.discard[i]  == True:
				res = prevacc
			else:
				prevacc = res
				if not acc:
					acc = res
				else:
					acc += res
		yield acc
		yield rest

class Alternative(Parsec):
	def __init__(self, first, other):
		Parsec.__init__(self)
		self.others = [first, other]

	def __or__(self, other):
		nself = copy.deepcopy(self)
		nself.others.append(other)
		return nself

	def parse_body(self, string, acc=None):
		result, rest = acc, string
		for i,parser in enumerate(self.others):
			inner = generate_rest(parser)
			if i != len(self.others) - 1:
				try:
					res, rest = inner(string)
					acc = res if not acc else acc+res
					yield acc
					yield rest
					return
				except ParseError:
					continue
			else:
				res, rest = inner(string)
				acc = res if not acc else acc+res
				yield acc
				yield rest
				return
		yield ParserError("Failed alternatives")

class ParseError:
	def __init__(self, message):
		self.message = message

	def __str__(self):
		return self.message

class Many(Parsec):
	def __init__(self, parser):
		Parsec.__init__(self)
		self.parser = parser

	def parse_body(self, string, acc=""):
		inner = generate_rest(self.parser)

		val = None
		result, rest = [], string
		while True:
			try:
				val, rest = inner(rest)
				result.append(val)
			except ParseError:
				break
		yield result
		yield rest

class Many1(Parsec):
	def __init__(self, parser):
		Parsec.__init__(self)
		self.parser = parser

	def parse_body(self, string, acc=""):
		inner = generate_rest(self.parser)

		result = []
		val, rest = inner(string)
		result.append(val)
		while True:
			try:
				val, rest = inner(rest)
				result.append(val)
			except ParseError:
				break
 		yield result
		yield rest

class Char(Parsec):
	def __init__(self, char):
		Parsec.__init__(self)
		self.char = char

	def parse_body(self, string, acc=""):
		if string.startswith(self.char):
			yield acc+self.char
			yield string[1:]
		else:
			error = "expected %s, got %s" % (str(self.char), repr(string[0]) if len(string) > 0 else repr(""))
			yield ParseError(error)

class String(Parsec):
	def __init__(self, string):
		Parsec.__init__(self)
		self.string = string

	def parse_body(self, string, acc=""):
		if string.startswith(self.string):
			yield acc+self.string
			yield string[len(self.string):]
		else:
			yield ParseError("Could not parse " + self.string)

class Regex(Parsec):
	def __init__(self, pattern):
		Parsec.__init__(self)
		self.pattern = pattern
		self.re = re.compile(pattern)

	def parse_body(self, string, acc=""):
		m = self.re.match(string)
		if m:
			res = m.group(0)
			rest = string[len(res):]
			yield res
			yield rest
		else:
			yield ParseError("Could not match pattern %r" % self.pattern)

class OneOf(Parsec):
	def __init__(self, chars):
		Parsec.__init__(self)
		self.chars = chars

	def parse_body(self, string, acc=""):
		if string.startswith(tuple(self.chars)):
			yield acc+string[0]
			yield string[1:]
		else:
			chrs = "".join(self.chars)
			error = "expected one of %s, got %s" \
					% (chrs, repr(string[0]) if len(string) > 0 else repr(""))
			yield ParseError(error)

class NoneOf(Parsec):
	def __init__(self, chars):
		Parsec.__init__(self)
		self.chars = chars

	def parse_body(self, string, acc=""):
		if not string.startswith(tuple(self.chars)):
			yield acc+string[0]
			yield string[1:]
		else:
			chrs = "".join(self.chars)
			error = "expected none of %s, got %s" % (chrs, string[0] if len(string) > 0 else "")
			yield ParseError(error)

class Between(Parsec):
	def __init__(self, start_parser, body_parser, end_parser):
		Parsec.__init__(self)
		self.start = start_parser
		self.body = body_parser
		self.end = end_parser

	def parse_body(self, string, acc=""):
		@Parser
		def inner():
			yield self.start
			x, _ = yield self.body
			_, rest = yield self.end
			produce((x,rest))
		result, rest = inner(string)
		yield result
		yield rest

class SepBy(Parsec):
	def __init__(self, body_parser, sep_parser):
		Parsec.__init__(self)
		self.body = body_parser
		self.sep = sep_parser

	def parse_body(self, string, acc=""):
		inner_body = generate_rest(self.body)
		inner_sep = generate_rest(self.sep)

		result, rest = [], string
		ct = 0
		while True:
			if ct > 0:
				try:
					sep, rest = inner_sep(rest)
				except ParseError:
					break
			res, rest = inner_body(rest)
			result.append(res)
			ct += 1
			
		yield result
		yield rest

class EndBy(Parsec):
	def __init__(self, body, sep):
		Parsec.__init__(self)
		self.body = body
		self.sep = sep

	def parse_body(self, string, acc=""):
		inner_body = generate_rest(self.body)
		inner_sep = generate_rest(self.sep)

		result, rest = [], string
		while True:
			try:
				res, rest = inner_body(rest)
			except ParseError:
				break
			_, rest = inner_sep(rest)
			result.append(res)
		yield result
		yield rest

class NotFollowedBy(Parsec):
	def __init__(self, parser):
		self.parser = parser

	def parse_body(self, string, acc=""):
		inner = generate(self.parser)
		try:
			x = inner(string)
			yield ParseError("NotFollowedBy " + repr(self.parser) + " failed")
		except ParseError:
			yield ""
			yield string

def produce(val):
	raise ReturnVal(val)

def digit():
	ns = [chr(i) for i in range(ord("0"), ord("9")+1)]
	return generate(OneOf(ns))

def upper():
	chars = [chr(i) for i in range(ord('A'), ord('Z')+1)]
	return generate(OneOf(chars))

def lower():
	chars = [chr(i) for i in range(ord('a'), ord('z')+1)]
	return generate(OneOf(chars))

def alpha():
	return upper()|lower()

def concat(parser):
	return parsec_map(lambda x: ''.join(x), parser)

def parsec_map(f, parser):
	@Parser
	def inner():
		x = yield parser
		produce(f(x[0]))
	return inner

def generate_rest(parser):
	@Parser
	def inner():
		x, rest = yield parser
		produce((x,rest))
	return inner

def generate(parser):
	@Parser
	def inner():
		x = yield parser
		produce(x[0])
	return inner

def wrap(parser):
	@Parser
	def inner():
		produce(parser)
	return inner

def Surround(parser, surr):
	return Between(surr, parser, surr)

def many(parser):
	return wrap(Many(parser))

def between(start, body, end):
	return generate(Between(start, body, end))

from enum import Enum
import copy
import inspect

class NextType(Enum):
	Chain, Alternative, Discard = range(3)

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
		return self.add(other, NextType.Alternative)

	def __lshift__(self, other):
		"""Discard"""
		return Chain(self, other, discard=True)

	def add(self, other, ty, head=True):
		nself = copy.deepcopy(self) if head else self
		othercpy = copy.deepcopy(other)
		nself.type = ty
		if nself.next_parser:
			nself.next_parser.add(othercpy, ty, False)
		else:
			nself.next_parser = othercpy
		return nself

	def parse(self, string, acc="", suppress=False, no_send=False):
		res, rest = acc, string
		try:
			gens = self.parse_body(string, acc)
			mres, subparser, parser = None, None, None
			while True:
				#print "sending " + repr(mres)
				parser = gens.send(mres)
				#print "Parser: " + repr(parser)
				#print "mres is " + repr(mres)
				ps = parser.parse_body(rest, acc)
				if isinstance(parser, Parser):
					try:
						while True:
							#print "I AM A PARSER!\n"
							a = ps.next()
							#print "a is " + repr(a)
							ms = list(a.parse_body(rest, acc))
							#print "ms is " + repr(ms)
							res = ps.send(ms)
							#print "OUTTA HERE\n"
					except ReturnVal as stopped:
						mres = [stopped.value, ms[1]]
				else:
					mres = list(ps)
					#print "MRES!!! is " + repr(mres)
					#if len(mres) == 2:
					#	_, rest = mres
				if mres and isinstance(mres[0], ParseError):
					#print "raising"
					raise mres[0]
				elif mres:
					_, rest = mres
				#l = [0]
				#l = list(ps)
				#print l
				"""if len(l) == 1 and isinstance(l[0], ParseError):
					raise l[0]
				elif len(l) == 2:
					mres = l
					res, rest = mres
				else:
					subparser = l[0]"""
		except ReturnVal as stop:
			#print "stopvalue is " + repr(stop.value)
			#print "rest is " + repr(rest)
			#print "mres is " + repr(mres)
			#print "done with " + repr(self)
			return stop.value

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

	def parse_body(self, string, acc=""):
		result, prevacc, rest = "", acc, string
		res = ""
		for i, parser in enumerate(self.others):
			inner = generate_rest(parser)
			res, rest = inner(rest)
			if i < len(self.discard) and self.discard[i]:
				res = prevacc
			else:
				prevacc = res
				acc += res
		yield acc
		yield rest

	"""
	res, prevacc, rest, error = "", acc, string, None
		for i,parser in enumerate(self.others):
			if i > 0 and self.discard[i-1]:
				res = prevacc
			res, rest, error = parser.parse(rest, acc=res, suppress=True)
			if i < len(self.discard) and not self.discard[i]:
				prevacc = res
			if error:
				return "", string, error
		return res, rest, error
	"""

class Alternative(Parsec):
	def __init__(self, first, other):
		Parsec.__init__(self)
		self.pair = (first, other)

	def parse_body(self):
		pass

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
		result, rest = acc, string
		while True:
			try:
				val, rest = inner(rest)
				result += val
			except ParseError:
				break
		#print "in many, rest is " + repr(rest)
		yield result
		yield rest

class Many1(Parsec):
	def __init__(self, parser):
		Parsec.__init__(self)
		self.parser = parser

	def parse_body(self, string, acc=""):
		inner = generate_rest(self.parser)

		result = acc
		val, rest = inner(string)
		result += val
		while True:
			try:
				val, rest = inner(rest)
				result += val
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
			error = "expected %s, got %s" % (str(self.char), string[0] if len(string) > 0 else "")
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
			x, rest = yield self.start << self.body
			yield self.end
			produce((x,rest))
		inner.show_rest = True
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

		result, rest, error = [], string, None
		while True:
			try:
				res, rest = inner_body(rest)
				_, rest = inner_sep(rest)
				result.append(res)
			except ParseError:
				break
		yield result
		yield rest

def produce(val):
	raise ReturnVal(val)

def digit():
	ns = [chr(i) for i in range(ord("0"), ord("9")+1)]
	return OneOf(ns)

def upper():
	chars = [chr(i) for i in range(ord('A'), ord('Z')+1)]
	return OneOf(chars)

def lower():
	chars = [chr(i) for i in range(ord('a'), ord('z')+1)]
	return OneOf(chars)

def alpha():
	return upper()|lower()

def parsec_map(f, parser):
	@Parser
	def inner():
		#print "in parsec map!!"
		x, _ = yield parser
		#print "second part of psec map"
		#print "x is " + repr(x)
		produce(f(x))
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
		x, _ = yield parser
			#print "x[0] is " + repr(x[0])
			#print "parser was " + repr(parser)
		produce(x)
	return inner

def many(parser):
	@Parser
	def inner():
		produce(Many(parser))
	return inner

def between(start, body, end):
	return generate(Between(start, body, end))

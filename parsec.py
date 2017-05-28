from enum import Enum
import copy

class NextType(Enum):
	Chain, Alternative, Discard = range(3)

class ReturnVal:
	def __init__(self, val):
		self.value = val

class Parser:
	def __init__(self):
		self.error = None
		self.next_parser = None
		self.type = None
		self.value = None

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
		gens = self.parse_body(string, acc)
		try:
			mres = None
			while True:
				parser = gens.send(mres)
				ps = parser.parse_body(rest, res)
				l = list(ps)
				if len(l) == 1:
					raise l[0]
				else:
					mres = l
					res, rest = mres
		except ReturnVal as stop:
			return stop.value
		"""
			l = list(parser.parse_body(rest, res))
			if len(l) == 1:
				raise l[0]
			else:
				res, rest = l
		return res"""
		"""g = self.parse_body(string, acc)
		try:
			res = g.next()
			if isinstance(res, ParseError):
				raise res
			g.close()
			return res
		except StopIteration as stop:
			return stop.value"""
		#result, rest, error = self.parse_body(string, acc)
		#if not no_send:
		#	return self.send_rest(result, rest, error, suppress)

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

class Chain(Parser):
	def __init__(self, first, other, discard=False):
		Parser.__init__(self)
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
		result, rest = acc, string
		for i, parser in enumerate(self.others):
			if self.discard[i-1]:
			acc += yield parser
		produce(acc)

class Alternative(Parser):
	def __init__(self, first, other):
		Parser.__init__(self)
		self.pair = (first, other)

	def parse_body(self):
		pass

class ParseError:
	def __init__(self, message):
		self.message = message

	def __str__(self):
		return self.message

class Many(Parser):
	def __init__(self, parser):
		Parser.__init__(self)
		self.parser = parser

	def parse_body(self, string, acc=""):
		error = None
		result, rest = acc, string
		while error is None:
			val, rest, error = self.parser.parse(rest, suppress=True)
			if not error:
				result += val
		return result, rest, None

class Many1(Parser):
	def __init__(self, parser):
		Parser.__init__(self)
		self.parser = parser

	def parse_body(self, string, acc=""):
		result = acc
		val, rest, error = self.parser.parse(string, acc=acc, suppress=True)
		if error:
			return acc, rest, error
		else:
			result += val
			while error is None:
				val, rest, error = self.parser.parse(rest, suppress=True)
				if not error:
					result += val
			return result, rest, None

class Char(Parser):
	def __init__(self, char):
		Parser.__init__(self)
		self.char = char

	def parse_body(self, string, acc=""):
		if string.startswith(self.char):
			yield acc+self.char
			yield string[1:]
			#return acc+self.char, string[1:], None
		else:
			error = "expected %s, got %s" % (str(self.char), string[0] if len(string) > 0 else "")
			yield ParseError(error)
			#return acc, string, ParseError(error)

class String(Parser):
	def __init__(self, string):
		Parser.__init__(self)
		self.string = string

	def parse_body(self, string, acc=""):
		if string.startswith(self.string):
			yield acc+self.string
			yield string[len(self.string):]
			#return acc+self.string, string[len(self.string):], None
		else:
			yield ParseError("Could not parse " + self.string)
			#return acc, string, ParseError("Cannot parse empty string")

class OneOf(Parser):
	def __init__(self, chars):
		Parser.__init__(self)
		self.chars = chars

	def parse_body(self, string, acc=""):
		if string.startswith(tuple(self.chars)):
			yield acc+string[0]
			yield string[1:]
			#return acc+string[0], string[1:], None
		else:
			chrs = "".join(self.chars)
			error = "expected one of %s, got %s" \
					% (chrs, string[0] if len(string) > 0 else "")
			yield ParseError(error)
			#return acc, string, ParseError(error)

class NoneOf(Parser):
	def __init__(self, chars):
		Parser.__init__(self)
		self.chars = chars

	def parse_body(self, string, acc=""):
		if not string.startswith(tuple(self.chars)):
			yield acc+string[0]
			yield string[1:]
			#return acc+string[0], string[1:], None
		else:
			chrs = "".join(self.chars)
			error = "expected none of %s, got %s" % (chrs, string[0] if len(string) > 0 else "")
			yield ParseError(error)
			#return acc, string, ParseError(error)

class Between(Parser):
	def __init__(self, start_parser, body_parser, end_parser):
		Parser.__init__(self)
		self.start = start_parser
		self.body = body_parser
		self.end = end_parser

	def parse_body(self, string, acc=""):
		prefix = self.start << self.body
		#result, rest, error = prefix.parse(string, acc=acc)
		if error:
			yield error
			#return acc, string, error
		yield self.end
		#_, rest, error = self.end(rest)
		yield result
		yield rest
		#return result, rest, error

class SepBy(Parser):
	def __init__(self, body_parser, sep_parser):
		Parser.__init__(self)
		self.body = body_parser
		self.sep = sep_parser

	def parse_body(self, string, acc=""):
		result, rest, error = [], string, None
		while not error:
			#res, rest, berror = self.body.parse(rest, suppress=True)
			_, rest, error = self.sep.parse(rest, suppress=True)
			result.append(res)
		yield result
		yield rest
		#return result, rest, berror

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

from parsec import *
import re

whitespace = generate(Many(OneOf(" \r\n\t")))
comma = Char(',')
lbrace = Char('{')
rbrace = Char('}')
lbrack = Char('[')
rbrack = Char(']')
colon = Char(':')
true = Wrap(parsec_map(lambda x: True, String("true")))
false = Wrap(parsec_map(lambda x: False, String("false")))
null = Wrap(parsec_map(lambda x: None, String("null")))
number = Many1(digit())

def normalize(string):
	return re.sub(r'([\n\r\t\f\b])', r"\\\1", string)

def charseq():
	def strpart():
		return Regex(r'[^"\\]+')
	def stresc():
		return Char('\\') >> (
			Char('\\')
			| Char('/')
			| parsec_map(lambda x: '\b', Char('b'))
			| parsec_map(lambda x: '\f', Char('f'))
			| parsec_map(lambda x: '\n', Char('n'))
			| parsec_map(lambda x: '\r', Char('r'))
		)

	return strpart() | stresc()

@Parser
def quoted():
	yield Char('"')
	body, _ = yield Many(charseq())
	yield Char('"')
	produce(body)

@Parser
def array():
	yield lbrack
	elements = yield SepBy(value, comma)
	yield rbrack
	produce(elements)

@Parser
def object_pair():
	key = yield quoted
	yield colon
	val = yield value
	produce((key, val))

@Parser
def json_object():
	yield lbrace
	pairs = yield SepBy(object_pair, comma)
	yield rbrace
	produce(dict(pairs))

value = Wrap(quoted) | number | Wrap(json_object) | Wrap(array) | true | false | null

jsonp = whitespace >> Wrap(json_object)
#print jsonp('{"a": "true", "b": false, "C": ["a", "b", "C"]}')
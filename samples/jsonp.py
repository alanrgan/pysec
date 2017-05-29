from parsec import *
import re

whitespace = generate(concat(Many(OneOf(" \r\n\t"))))
comma = Char(',')
lbrace = Char('{')
rbrace = Char('}')
lbrack = Char('[')
rbrack = Char(']')
colon = Char(':')
true = String("true").result(True)
false = String("false").result(False)
null = String("null").result(None)
number = parsec_map(int, concat(Many1(digit())))

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
	produce(''.join(body))

@Parser
def array():
	yield lbrack
	elements, _ = yield SepBy(value, comma)
	yield rbrack
	produce(elements)

@Parser
def object_pair():
	key, rest = yield quoted
	yield colon
	val, _ = yield value
	produce((key, val))

@Parser
def json_object():
	yield lbrace
	pairs, _ = yield whitespace << SepBy(object_pair, Surround(comma, whitespace))
	yield whitespace
	yield rbrace
	produce(dict(pairs))

atom = quoted | number | json_object | array | true | false | null
value = Between(whitespace, atom, whitespace)

jsonp = whitespace << json_object

first = jsonp('{ "a": "true",     "b": 4 , "C": ["a","b","C"] }')
second = jsonp('''
            {
                "a": {
                    "a": "x",
                    "b": "t",
                    "c": {
                        "a": true,
                        "c": [true, false, true]
                    }
                }
            }
        ''')
#print object_pair('"a":"true"')
#b = generate(SepBy(quoted,comma))
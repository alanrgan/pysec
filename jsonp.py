from parsec import *
import re

whitespace = generate(Many(OneOf(" \r\n\t")))
comma = Char(',')
lbrace = Char('{')
rbrace = Char('}')
lbrack = Char('[')
rbrack = Char(']')
colon = Char(':')
true = parsec_map(lambda x: True, String("true"))
false = parsec_map(lambda x: False, String("false"))
null = parsec_map(lambda x: None, String("null"))
number = parsec_map(int, Many1(digit()))

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
	pairs, _ = yield whitespace << (
					SepBy(object_pair, (whitespace >> comma >> whitespace))
				)
	yield whitespace
	yield rbrace
	produce(dict(pairs))

atom = quoted | number | json_object | array | true | false | null
value = Between(whitespace, atom, whitespace)

jsonp = whitespace << json_object
print jsonp('{ "a": "true", "b": 4 , "C": ["a","b","C"] }')
print jsonp('''
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
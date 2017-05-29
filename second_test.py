from parsec import *
"""
alt = generate(Char('x')|Char('y')|Char('z')|Char('d'))
num = parsec_map(int, Many1(digit()))
def foo():
	return alt | num

print foo()("1234")"""
whitespace = generate(Many1(OneOf(" \t\r\n")))
my_integer = parsec_map(int, Many1(digit()))
print type(my_integer("12345"))

#spacedInt = generate(Between(whitespace, my_integer, whitespace))
@Parser
def spacedInt():
	yield whitespace
	i, _ = yield my_integer
	yield whitespace
	produce({"number": i})

result = spacedInt("          123483274834        ")
print result
print type(result)

"""ps = generate(whitespace << my_integer)
print ps("   5")"""

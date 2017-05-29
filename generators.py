"""def coroutine(func):
	def start(*args, **kwargs):
		cr = func(*args, **kwargs)
		cr.next()
		return cr
	return start

@coroutine
def grep(pattern):
	print "Looking for %s" % pattern
	while True:
		line = (yield)
		if pattern in line:
			print line,

if __name__ == '__main__':
	g = grep("python")
	g.send("Whooooo")
	g.send("A series of tubes")
	g.send("python is great")
	g.send("i love python")"""

def countdown(n):
	counter = n
	while n >= 0:
		v = yield n
		print "got " + v
		n -= 1

g = countdown(30)
r = g.send(None)
print r
r = g.send("hello")
print r
import re
import math
from functools import reduce
from abc import ABC, abstractmethod

variables = {}

class VectorError(Exception):
	pass

def sqrt(radicand, mul=1):
	isqrt = math.isqrt(radicand)
	if isqrt**2 == radicand:
		# no need for sqrt symbol to stay
		return isqrt*mul
	else:
		return Sqrt(radicand, mul)

def div(a, b):
	if not isinstance(a, float) and not isinstance(b, float) and not isinstance(a, Special) and not isinstance(b, Special):
		# check if frac needed
		if a//b * b == a:
			return a//b
		else:
			return Fraction(a,b)
	else:
		return a/b

# note that this INCLUDES FRACTIONS tho
def is_plain_num(item):
	return isinstance(item, int) or isinstance(item, float) or isinstance(item, Fraction)

def can_add(a, b):
	if is_plain_num(a) or is_plain_num(b):
		return is_plain_num(a) and is_plain_num(b)
	if isinstance(a, Vector) or isinstance(b, Vector):
		return isinstance(a, Vector) and isinstance(b, Vector)
	if isinstance(a, Sqrt) or isinstance(b, Sqrt):
		return a.radicand == b.radicand

class Special(ABC):
	@abstractmethod
	def as_num(self):
		pass

	@abstractmethod
	def __add__(self, other):
		pass

	@abstractmethod
	def __sub__(self, other):
		pass

	@abstractmethod
	def __mul__(self, other):
		pass

	@abstractmethod
	def __truediv__(self, other):
		pass

	def __radd__(self, other):
		return self + other

	def __rsub__(self, other):
		return (self * -1) + other

	def __rmul__(self, other):
		return self * other

	@abstractmethod
	def __rtruediv__(self, other):
		pass

	def compare(self, other, op):
		v = self.as_num()
		if isinstance(other, Special):
			return op(v, other.as_num())
		else:
			return op(v, other)

	def __lt__(self, other):
		return self.compare(other, lambda a,b: a < b)
	
	def __le__(self, other):
		return self.compare(other, lambda a,b: a <= b)

	def __gt__(self, other):
		return self.compare(other, lambda a,b: a > b)
	
	def __ge__(self, other):
		return self.compare(other, lambda a,b: a >= b)

class Expr(Special):
	def __init__(self, items):
		self.items = []
		self.c = 0
		
		for item in items:
			if is_plain_num(item):
				self.c += item
			else:
				i = 0
				found = False
				for item2 in self.items:
					if can_add(item, item2):
						self.items[i] += item
						found = True
					i += 1
				if not found:
					self.items.append(item)

	def as_num(self):
		return c + reduce(lambda a,b: a + (as_num(b) if isinstance(b, Special) else b), self.items, 0)

	def __str__(self):
		res = ""
		if self.c != 0:
			res = str(self.c)
			if len(self.items) > 0:
				if self.items[0] >= 0:
					res += " + "
				else:
					res += " "
		if len(self.items) > 0:
			if self.items[0] < 0:
				res += "- "
			res += str(self.items[0])

		for item in self.items[1:]:
			if item >= 0:
				res += " + "
			else:
				res += " - "
			res += str(item)
		return res

	def __add__(self, other):
		if isinstance(other, Expr):
			return Expr([self.c, other.c, *self.items, *other.items])
		else:
			return Expr([self.c, *self.items, other])

	def __sub__(self, other):
		if isinstance(other, Expr):
			return Expr([self.c, other.c * -1, *self.items, *map(lambda a : a * -1, other.items)])
		else:
			return Expr([self.c, *self.items, other * -1])

	def __mul__(self, other):
		print("todo")
		return -1

	def __truediv__(self, other):
		print("todo")
		return -1

	def __rtruediv__(self, other):
		print("todo")
		return -1

class Fraction(Special):
	def __init__(self, numer, denom):
		if not isinstance(numer, Special) and not isinstance(denom, Special):
			# denominator should always be positive by convention
			if denom < 0:
				denom *= -1
				numer *= -1

			common = math.gcd(numer, denom)
			numer //= common
			denom //= common
		self.numer = numer
		self.denom = denom

	def as_num(self):
		n = self.numer
		d = self.denom
		if is_special(n):
			n = n.as_num()
		if is_special(d):
			d = d.as_num()
		return n / d

	def __str__(self):
		return "("+str(self.numer)+"/"+str(self.denom)+")"

	def _add_sub(self, other, op):
		if isinstance(other, float):
			return op(self.as_num(), other())
		if isinstance(other, int):
			return Fraction(op(self.numer, other * self.denom), self.denom)

	def __add__(self, other):
		return self.check(self._add_sub(other, lambda a,b : a + b))

	def check(self, other):
		if isinstance(other, Fraction):
			if other.denom == 1:
				return other.numer
		return other

	def __sub__(self, other):
		return self.check(self._add_sub(other, lambda a,b : a - b))

	def _mul_div(self, other, op, is_div=False):
		if isinstance(other, Fraction):
			if is_div:
				return Fraction(self.numer * other.denom, self.denom * other.numer)
			else:
				return Fraction(self.numer * other.numer, self.denom * other.denom)
		if isinstance(other, float):
			return op(self.as_num(), other)
		if isinstance(other, int):
			if is_div:
				return Fraction(self.numer, self.denom * other)
			else:
				return Fraction(self.numer * other, self.denom)
		

	def __mul__(self, other):
		return self.check(self._mul_div(other, lambda a,b : a * b))

	def __truediv__(self, other):
		return self.check(self._mul_div(other, lambda a,b : a / b, True))

	def __rtruediv__(self, other):
		if isinstance(other, Fraction):
			return Fraction(other.numer * self.denom, other.denom * self.numer)
		else:
			return Fraction(other * self.denom, self.numer)

class Sqrt(Special):
	def __init__(self, radicand, mul=1):
		# remove perfect squares
		d = 2
		while d*d <= radicand:
			if radicand % (d*d) == 0:
				mul *= d
				radicand //= d*d
			else:
				d += 1

		self.radicand = radicand
		self.mul = mul

	def __str__(self):
		s = ""
		if self.mul != 1:
			s += str(self.mul)
		return s + "√(" + str(self.radicand) + ")"

	def as_num(self):
		return self.mul * math.sqrt(self.radicand)

	def _mul_div(self, other, op):
		if isinstance(other, Sqrt):
			# √5 * √3
			newr = op(self.radicand, other.radicand)
			newm = op(self.mul, other.mul)
			return sqrt(newr, newm)
		c = other
		newm = op(self.mul, c)
		return sqrt(self.radicand, newm)

	def __mul__(self, other):
		return self._mul_div(other, lambda a, b: a*b)

	def __truediv__(self, other):
		return self._mul_div(other, lambda a, b: div(a,b))

	def __add__(self, other):
		return Expr([self, other])

	def __sub__(self, other):
		return Expr([self, other * -1])

	def __rtruediv__(self, other):
		return Fraction(other, self)

class Vector:
	def __init__(self, value):
		self.value = value

	def __str__(self):
		return "["+", ".join(map(lambda a : str(a), self.value))+"]"

	# printing inside list / tuple
	def __repr__(self):
		return str(self)

	def _add_sub(self, other, lmd):
		if not isVector(other):
			raise VectorError("Can't add/subtract scalar and vector")
		v1, v2 = self.value, other.value
		if len(v1) != len(v2):
			raise VectorError("Can't add/subtract vectors of different dimensions. Result is undefined.")
			return None
		new_v = list(map(lmd, v1, v2))
		return Vector(new_v)

	def __add__(self, other):
		return self._add_sub(other, lambda a,b : a+b)

	def __sub__(self, other):	
		return self._add_sub(other, lambda a,b : a-b)

	# two vectors multiplied, or multiply by a constant
	# or -1 for undefined
	def __mul__(self, other):
		if isVector(other):
			# multiply two vectors
			v1, v2 = self.value, other.value
			if len(v1) != len(v2):
				raise VectorError("Can't multiply vectors of different dimensions. Result is undefined.")
				return None
			return reduce(lambda a, b : a+b, list(map(lambda a,b : a*b, v1, v2)))
		else:
			# multiply by scalar
			c = other
			new_v = list(map(lambda a : a*c, self.value))
			return Vector(new_v)

	def __truediv__(self, other):
		if isVector(other):
			raise VectorError("Cannot divide a vector by another vector.")
			return None
		else:
			# divide by scalar
			c = other
			new_v = list(map(lambda a : div(a,c), self.value))
			return Vector(new_v)

	def __rmul__(self, other):
		return self.__mul__(other)

	def __rtruediv__(self, other):
		raise VectorError("Cannot divide a scalar by a vector")
		return None

	def __radd__(self, other):
		raise VectorError("Can't add scalar and vector")
		return None		

	def __rsub__(self, other):
		raise VectorError("Can't subtract vector from scalar")
		return None

	# get norm (aka length) of vector
	def norm(self):
		return sqrt(sum(x**2 for x in self.value))

	def __abs__(self):
		return self.norm()

	def unit_vector(self):
		return self.__truediv__(self.norm())
			

def isVector(item):
	return isinstance(item, Vector)

def main():
	print("h for help")
	cmd = 0; #command
	while cmd != "":
		cmd = input(">> ")
		if cmd != "":
			parse_command(re.sub(r"\s", "", cmd))

def parse_command(cmd):
	cmd = re.sub(r"sqrt", "√", cmd)
	cmds = cmd.split(";")

	for c in cmds:
		if c == "h":
			print_help()
			continue
		if len(c) > 0 and c[0] == "~":
			#arbitrary symbol i decided means you can type functions
			print(parse_func(c[1:]))
			continue
		if set_var(c):
			continue
		print(solve_all(c))

def angle_between(a, b):
	if not isinstance(a, Vector) or not isinstance(b, Vector):
		print("Both arguments to angle() must be vectors.")
		return None
	return "arccos("+str((a*b)/(abs(a)*abs(b)))+")"

def proj(a, b):
	print("Projection of "+str(a)+" onto "+str(b))
	if not isinstance(a, Vector) or not isinstance(b, Vector):
		print("Both arguments to proj() must be vectors.")
		return None
	return b*(div((a*b),(abs(b)*abs(b))))

# idk I just decided that you would write for example angle(a~b) to get angle between a and b. tilde instead of comma bc idk i picked a character that was unused. comma is used in separators for vectors sooo
def parse_func(f):
	match = re.search(r"^([a-z]+)\((.*)\)$", f)
	if not match:
		print("Malformed function")
		return None
	args = match.groups()[1].split("~")
	solved_args = []
	for arg in args:
		parsed = parse_exp(arg)["match"]
		if parsed == None:
			return None
		solved = solve(parsed)
		if solved == None:
			return None
		solved_args.append(solved)

	f_name = match.groups()[0]

	match f_name:
		case "angle":
			if len(solved_args) != 2:
				print(len(solved_args) + " args given when 2 expected.")
			return angle_between(*solved_args)
		case "proj":
			if len(solved_args) != 2:
				print(len(solved_args) + " args given when 2 expected.")
			return proj(*solved_args)

	print("Unknown function name: "+f_name)
	return None

def solve_all(cmd):
	im = implicit_mult(cmd)
	parsed = parse_exp(im)
	if parsed == None:
		return None
	try:
		return solve(parsed["match"])
	except VectorError as e:
		print(f"Error: {e}")

def implicit_mult(cmd):
	# num/var before bracket/paren/other var. e.g. 2(5+1) or a[9,2] or abc
	cmd = re.sub(r"([\da-zA-Z])(?=[\[\(a-zA-Z])", r"\1*", cmd)

	# num/var/bracket/paren after closing bracket/paren. e.g. (1+2)a or (1+2)(3+4)
	cmd = re.sub(r"([\]\)])([\da-zA-Z\(\[])", r"\1*\2", cmd)

	return cmd

def solve(ast):
	if not isinstance(ast, tuple):
		return ast
	if len(ast) == 2:
		# single operator
		arg1 = solve(ast[1])
		if arg1 == None:
			return None
		match ast[0]:
			case '|':
				return abs(arg1)
			case '^':
				if isinstance(arg1, Vector):
					return arg1.unit_vector()
				else:
					print("This only supports ^ for vectors (to get unit vector). If you're trying to do powers, that's too damn bad.")
					return None
			case '√':
				return sqrt(arg1)
		print("Unknown symbol: "+ast[0])
		return None
	arg1 = solve(ast[0])
	if arg1 == None:
		return None
	symbol = ast[1]
	arg2 = solve(ast[2])
	if arg2 == None:
		return None
	
	match symbol:
		case '*':
			return arg1*arg2
		case '/':
			return div(arg1,arg2)
		case '+':
			return arg1+arg2
		case '-':
			return arg1-arg2
	print("Unknown symbol: "+symbol)
	return None

# used if the command has an equals sign in it
def set_var(cmd):
	match = re.search(r"^(.)=(.*)$", cmd)
	if not match:
		return 0
	letter = match.groups()[0]
	exp = match.groups()[1]
	if not re.search(r"[a-zA-Z]", letter):
		print("Invalid. Only letters can be used as variable names, not "+letter)
		return 1

	val = solve(parse_exp(exp))
	if val != None:
		variables[letter] = val["match"]

	return 1

# give just what's in the brackets
# e.g. for [3,2], give it "3,2"
# returns vector as a list, OR -1 if invalid format
def parse_vector(vector):
	if not re.search(r"^(-?\d+,)*-?\d+,?$", vector):
		print("Invalid vector.\nUse this format:\n[-4, -2, -4]")
		return None
	v = list(map(lambda a : int(a), vector.split(",")))
	return Vector(v)

def parse_exp(cmd):
	parsed = parse_arg(cmd)
	if parsed == None:
		return None
	i = parsed["index"]
	ast = parsed["match"]

	while (i < len(cmd) and cmd[i] in ['+', '-']):
		parsed = parse_arg(cmd[i+1:])
		if parsed == None:
			return None
	
		ast = (ast, cmd[i], parsed["match"])
		i += 1 + parsed["index"]

	return {
		"match": ast,
		"index": i
	}

def parse_arg(cmd):
	parsed = parse_factor(cmd)
	if parsed == None:
		return None
	i = parsed["index"]
	ast = parsed["match"]

	while (i < len(cmd) and cmd[i] in ['*', '/']):
		parsed = parse_factor(cmd[i+1:])
		if parsed == None:
			return None
	
		ast = (ast, cmd[i], parsed["match"])
		i += 1 + parsed["index"]

	return {
		"match": ast,
		"index": i
	}

# give it all text after first paren
# e.g. for "3*(5+(2-1))", give it "5+(2-1))"
def get_in_paren(txt):
	i = 0
	open_paren = 0
	for c in txt:
		if c == "(":
			open_paren += 1
		elif c == ")":
			if open_paren > 0:
				open_paren -= 1
			else:
				return txt[:i]
		i += 1
	return None

# returns { match, index }
def parse_factor(arg):
	if len(arg) == 0:
		print("Trailing symbol.")
		return None
	if arg[0] == '(':
		match = get_in_paren(arg[1:])
		if match == None:
			print("Invalid. Needs closing parentheses.")
			return None
		parsed = parse_exp(match);
		if parsed == None:
			return None
		return {
			"match": parsed["match"],
			"index": len(match)+2 # +2 for paren
		}
	if arg[0] == '[':
		match = re.search(r"^\[(.*?)\]", arg)
		if not match:
			print("Invalid. Needs closing bracket.")
			return None
		return {
			"match": parse_vector(match.groups()[0]),
			"index": len(match.group())
		}
	if arg[0] == '|':
		match = re.search(r"^\|(.*?)\|", arg)
		if not match:
			print("Invalid. Needs closing |.")
		parsed = parse_exp(match.groups()[0])
		if parsed == None:
			return None
		return {
			"match": ('|', parsed["match"]),
			"index": len(match.group())
		}
	if arg[0] in ['^', '√']:
		if arg[1] == '(':
			match = get_in_paren(arg[2:])
			if match == None:
				print("Invalid. Needs closing parentheses.")
				return None
			parsed = parse_exp(match);
			if parsed == None:
				return None
			return {
				"match": (arg[0], parsed["match"]),
				"index": len(match)+3 # +2 for paren, +1 for symbol (e.g. ^)
			}
		
		else:
			parsed = parse_arg(arg[1:])
			if parsed == None:
				return None
			return {
				"match": (arg[0], parsed["match"]),
				"index": parsed["index"]+1 # no paren, +1 for symbol (e.g. ^)
			}
	match = re.search(r"^[a-zA-Z]", arg)
	if match:
		v = match.group();
		if v not in variables:
			print(v+" was not initialized")
			return None
		return {
			"match": variables[v],
			"index": 1
		}
	match = re.search(r"^-?\d+", arg)
	if not match:
		print(arg[0]+" where digit or variable name expected ")
		return None
	g = match.group()
	return {
		"match": int(g),
		"index": len(g)
	}
	
def print_help():
	print("Here is an example of what you could do:")
	print(">> a = [1,2,3]")
	print(">> b = [4,5,6]")
	print(">> a + b")
	print("[5, 7, 9]")
	print(">> 2a")
	print("[2, 4, 6]")
	print(">> 2a * b")
	print("64")
	print("---- END EXAMPLE ----")
	print("use |a| to get norm of vector a")
	print("use ^a to get unit vector of vector a")
	print("note: absolute value in absolute value is broken. e.g. no |1-(a+|-9|)|")
	print("Special functions:")
	print(">> ~angle(a~b)")
	print("angle between vectors a and b")
	print(">> ~proj(a~b)")
	print("projection of vector a onto vector b")

main()

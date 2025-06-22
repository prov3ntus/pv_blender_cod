import inspect, os, sys

def get_parent_func_name( *_, parent_level: int = 0 ):
	"""Crawls down the function call stack to get the name of 
	the function's parent that called `get_parent_func_name()`

	Args:
		`parent_level` (int, optional):
			Number of function parents to crawl up.
			For example, consider the following: `foo1()` calls `foo2()`, which calls `foo3()`.
			If you call `get_parent_func_name()` in `foo3()`, it will return the string literal `"foo2"`. 
			If you call `get_parent_func_name( 1 )` in `foo3()`, it'll return the string literal `"foo1"`.
			Defaults to 0.

	Returns:
		String Literal: The name of the parent function
	"""

	if parent_level < 0:
		return None

	try:
		for idx, line in enumerate( inspect.stack() ):
			print( f"{idx}:\n{line}" )
			print()

		return inspect.stack()[ parent_level + 1 ].function
	except IndexError:
		return None



def get_line_number( back: int = 0 ):
	try:
		return sys._getframe( back + 1 ).f_lineno
	except ValueError:
		return None



def get_file_name( back: int = 0 ):
	try:
		return sys._getframe( back + 1 ).f_code.co_filename
	except ValueError:
		return None



def get_function_name( back: int = 0 ):
	"""Gets the current function name

	Args:
		`back` (int, optional): How many times to crawl down the function call stack. Defaults to 0.

	Returns:
		string: The function name
		None: If `back` is greater than the function call stack
	"""
	try:
		return sys._getframe( back + 1 ).f_code.co_name
	except ValueError:
		return None



def WHERE( back: int = 0 ):
	try:
		frame = sys._getframe( back + 1 )
		return f"{ os.path.basename( frame.f_code.co_filename ) }:{frame.f_lineno} {frame.f_code.co_name}()"
	except ValueError:
		return None
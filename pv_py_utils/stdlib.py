import os, sys, subprocess
from time import sleep as wait, perf_counter as get_time, monotonic as timer
from typing import Iterable, Union

DEBUG_STR		= "[   DEBUG   ]\t"
ERROR_STR		= "[   ERROR   ]\t"
WARNING_STR		= "[  WARNING  ]\t"
CONSOLE_STR		= "[  CONSOLE  ]\t"
true: bool		= True
false: bool		= False
undefined		= None



class GVar():
	__name__ = 'struct'
	__info__ = 'Global variable utilisation to transcend variable scopes (even consistent across scripts)'
	is_updating: bool = false

gvar = GVar()


#############################
### Function declarations ###
#############################

def is_even( _number: Union[ int, float ] ) -> bool:
	return ( _number % 2 ) == 0

def is_odd( _number: Union[ int, float ] ) -> bool:
	return ( _number % 2 ) == 1

def clear_console():
	os.system( "cls || clear" ) 

def binary_search( key: object, _array: Iterable ) -> Union[ int, None ]:
	"""Traditional implementation of a binary search. Searches for `key` in `_array`.
	Useful for efficiently searching large data sets.\n
	Usually ~16x faster than doing `key in _array` or `_array.__contains__( key )`.\n
	Use of the algorithm requires the list to be `sorted()`.

	Args:
		key (object): The key to search for. 
		_array (Iterable): The array to search in.

	Returns:
		int | None: Returns the index of `key` in `_array`. Otherwise, returns `None`.
	"""

	low = 0
	high = _array.__len__() - 1
	mid = 0

	while low <= high:
		mid = ( high + low ) // 2

		if _array[ mid ] < key: low = mid + 1 		# If key is greater, ignore left half
		elif _array[ mid ] > key: high = mid - 1 	# If key is smaller, ignore right half
		else: return mid							# So key must be present at mid

	# key is not present
	return undefined

def clamp( value: object, _min: object, _max: object ) -> object:
	"""Restricts `value` within the given range `_min` -> `_max`."""
	return sorted( ( _min, value, _max ) )[ 1 ] # type: ignore

def get_py_version() -> str:
	"""Returns current python version.
	E.g. will return 3.11
	"""
	
	return '.'.join( map( str, sys.version_info[ :2 ] ) )

#######################
# String manipulation #
#######################

def concatenate( *__params: Union[ str, int, float ], sep: str = '' ):
	"""
	Concatenates all params, with an optional separator defined by changing the kwarg 'sep'
	"""
	"""
	concatenation = ''
	for string in __params:
		concatenation += str( string ) + sep
	"""
	
	concatenation = f'{ sep }'.join( str( _item ) for _item in __params )
	return concatenation

def concat( *__params: Union[ str, int, float ], sep: str = '' ):
	"""
	Concatenates all params, with an optional separator defined by changing the kwarg 'sep'
	"""
	return concatenate( *__params, sep=sep )

def strip_all( _str : str, *strip_args: Iterable[ str ] ) -> str:
	"""Replaces all instances of `strip_args` found in `_str` with `''`. 

	Args:
		_str (str): The string to modify.

	Returns:
		str: The modified string. Will return a copy of the original string if no items in `strip_args` are found.
	"""
	for arg in strip_args: _str = _str.replace( arg, '' )
	return _str

def exit( input_str: str = 'Press [ENTER] to exit...', exit_code = undefined ) -> None:
	input( input_str )
	sys.exit( exit_code )

def pip_install( package ):
	"""Opens a new subprocess and calls pip from current python installation to install the given package

 	Usage:
  	```py
	 try:
	    import pandas as pd
	except ImportError:
	    result = pip_install( "pandas" ) 
	finally:
	    import pandas as pd
	```
 	"""
	return subprocess.check_call( [ sys.executable, "-m", "pip", "install", package ] )

__all__ = (
	# String constants
	'DEBUG_STR', 'ERROR_STR', 'WARNING_STR', 'CONSOLE_STR',

	# GSC-inspired stuff
	'true', 'false', 'undefined',
	'gvar', 'is_even', 'is_odd',
	'wait', 'get_time', 'timer',

	# stdlib stuff
	'concatenate', 'concat', 'clear_console',
	'clamp', #'binary_search', 'replace_all',
)

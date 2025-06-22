from datetime import datetime
from ..pv_py_utils import console
from ..pv_py_utils.stdlib import strip_all

# ENUM
class Levels:
	"""
	## Levels
	OFF: `-1`\n
	INFO: `0`\n
	WARNING: `1`\n
	ERROR: `2`
	"""
	OFF: int = -1
	INFO: int = 0
	WARNING: int = 1
	ERROR: int = 2

level_to_name = {
	Levels.OFF: "OFF",
	Levels.INFO: "INFO",
	Levels.WARNING: "WARNING",
	Levels.ERROR: "ERROR",
}

name_to_level = {
	"OFF": Levels.OFF,
	"INFO": Levels.INFO,
	"WARNING": Levels.WARNING,
	"ERROR": Levels.ERROR,
}

"""Levels
OFF: -1
INFO: 0
WARNING: 1
ERROR: 2
"""
level = -1
file_path = 'console.log'
file_mode = 'w'



def info( *values: object, sep: str = ' ', end: str = '\n' ):
	"""Write information to this log file @ the INFO level

	Args:
		sep (str, optional): String inserted between values. Defaults to a space `' '`.
		end (str, optional): String appended after the last value. Defaults to a new line `'\\n'`.
	"""
	if( Levels.INFO > level ): return

	_write( f"{ datetime.now().strftime( '%x | %H:%M:%S:%f' ) } [ INFO ]\t{ sep.join( map( str, values ) ) + end }" )
	
def warning( *values: object, sep: str = ' ', end: str = '\n' ):
	"""Write a warning message to this log file @ the WARNING level

	Args:
		sep (str, optional): String inserted between values. Defaults to a space `' '`.
		end (str, optional): String appended after the last value. Defaults to a new line `'\\n'`.
	"""
	if( Levels.WARNING > level ): return

	_write( f"{ datetime.now().strftime( '%x | %H:%M:%S:%f' ) } [ WARNING ]\t{ sep.join( map( str, values ) ) + end }" )

def error( *values: object, sep: str = ' ', end: str = '\n' ):
	"""Write an error message to this log file @ the ERROR level

	Args:
		sep (str, optional): String inserted between values. Defaults to a space `' '`.
		end (str, optional): String appended after the last value. Defaults to a new line `'\\n'`.
	"""
	if( Levels.WARNING > level ): return

	_write( f"{ datetime.now().strftime( '%x | %H:%M:%S:%f' ) } [ ERROR ]\t{ sep.join( map( str, values ) ) + end }" )

def _write( message: str ) -> None:
	with open( file_path, file_mode, encoding='utf-8' ) as _log:
		_log.write( strip_all( message, *console.bcolors().__list__ ) )

def set_level( new_level: int, quiet: bool = False ):
	"""
	## Levels
	OFF: `-1`\n
	INFO: `0`\n
	WARNING: `1`\n
	ERROR: `2`
	"""
	level = new_level

	if( not quiet ):
		info( "Log level set to", level_to_name[ level ] )

def get_level( numerical: bool = False ):
	"""Gets current level of log file

	Args:
		numerical (bool, optional): Whether to return the actual numerical level, or the readable level, (e.g. returns "OFF" when true). Defaults to `false`.
	"""
	return level if numerical else level_to_name[ level ]


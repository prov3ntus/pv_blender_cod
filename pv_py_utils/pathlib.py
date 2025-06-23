import os
from typing import Union
from ..pv_py_utils import console

def is_empty( __file__: Union[ str, os.PathLike ] ) -> bool:
	with open( __file__ ) as f: return f.read().strip().__len__() == 0

def get_parent_dir( __file__: Union[ str, os.PathLike ], dirs_to_move_up: int = 1 ) -> Union[ str, os.PathLike, None ]:
	_path = __file__
	for i in range( dirs_to_move_up ):
		_path = os.path.abspath( os.path.join( _path, os.pardir ) )
	
	return _path

	# My code:
	#indexes = [i for i in range(len(__file__)) if __file__.startswith(( '\\', '/' ), i)]
	#return __file__[ :indexes[ -1 ] ]

def get_file_name( __file__: Union[ str, os.PathLike ], extention: bool = False ) -> str:
	"""Retuns the file name from a full file path ( w/ an extention if 'extention' param is true )"""
	if not extention:
		return os.path.splitext( os.path.basename( __file__ ) )[0]
	return os.path.basename( __file__ )

def get_base_name( __file__: Union[ str, os.PathLike ], extention: bool = False ) -> str:
	"""Retuns the file name from a full file path ( w/ an extention if 'extention' param is true )"""
	return get_file_name( __file__, extention )

def get_file_type( __file__: Union[ str, os.PathLike ] ) -> str:
	"""Returns the extention of a file

	E.g. '.png'
	"""
	return os.path.splitext( __file__ )[1]

def get_file_extension( __file__: Union[ str, os.PathLike ] ) -> str:
	"""Retuns the extention of a file

	E.g. '.png'
	"""
	return get_file_type( __file__ )

def get_file_ext( __file__: Union[ str, os.PathLike ] ) -> str:
	"""Retuns the extention of a file

	E.g. '.png'
	"""
	return get_file_type( __file__ )

def get_files_in_dir( dir: Union[ str, os.PathLike ], full_path=False, extention: str = None, include_dirs: bool = True ) -> list[ str ]:
	"""Returns all the files in the directory.

	Can optionally disclude counting directory names as well.

	Args:
		dir (Union[ str, os.PathLike ]): The path to the directory.
		full_path (bool, optional): True returns the full path to the file, false only the file. Defaults to False.
		extention (str, optional): Can filter by file type. Defaults to None.
		include_dirs (bool, optional): Can choose whether to return directory names or skip them. Defaults to True.

	Returns:
		List of files in given directory, filtered based on args
	"""

	files = [] 
	if not full_path:
		if extention is not None:
			for f in os.scandir( dir ):
				if os.path.isdir( f ) and not include_dirs:
					continue
				if f.name.lower().endswith( extention.lower() ):
					files.append(f.name) 
		else:
			for f in os.scandir( dir ):
				if os.path.isdir( f ) and not include_dirs:
					continue
				files.append(f.name)
		
		return files
	
	# Code below runs if full_path = true
	if not extention is None:
		for f in os.scandir( dir ):
			if os.path.isdir( f ) and not include_dirs:
				continue
			if f.name.endswith( extention ):
				files.append( os.path.join( dir, f.name ) ) 
	else:
		for f in os.scandir( dir ):
			if os.path.isdir( f ) and not include_dirs:
				continue
			files.append( os.path.join( dir, f.name ) ) 
	
	return files



def search_file_for_keyword( file_path: Union[ str, os.PathLike ], kword: str, return_idx=False, return_all=True ) -> Union[ Union[ str, int ], list[ Union[ str, int ] ] ]:
	"""
	Searches a file and returns a list of all lines in that file that have the keyword in.

	If nothing is found it returns an empty list.

	### @params:

	if return_all is False, it will return the first occurence.

	If return_idx is True, then it will return the line numbers.
	"""

	with open( file_path, 'r' ) as f:
		lines = f.readlines() 
	matches = [] 
	matches_idx = [] 
	for line in lines:
		idx = lines.index( line ) 
		if( line.find( kword ) != -1 ):
			matches.append( line ) 
			matches_idx.append( idx ) 
			if not return_all:
				break

	if matches == []:
		return []

	if not return_idx:

		if not return_all:
			return matches[0] # Return 1st match
		
		return matches # Return all matches
	
	if not return_all:
		return matches_idx[0] # Return line number of 1st match
	
	return matches_idx # Return line number of all matches

def get_folder_size( _dir: str, formatted: bool = True, granularity: int = 3 ) -> Union[ str, int ]:
	"""Returns the folder size\n
	If `formatted` is `true`, it will return a formatted console.bytesf str of the size with granularity applied.\n
	If it's false, it will return the size of the folder in bytes.
	"""
	n_size = 0
	for path, _, files in os.walk( _dir ):
		for f in files: n_size += os.path.getsize( os.path.join( path, f ) )
	if formatted: n_size = console.bytesf( n_size, granularity )
	return n_size

def get_file_size( _filedir, formatted: bool = True, granularity: int = 3 ) -> Union[ str, int ]:
	"""Returns the respective file size"""
	__size = os.path.getsize( _filedir )
	if formatted: __size = console.bytesf( __size, granularity )
	return __size

def get_file_array_size( _filedirarray, formatted: bool = True, granularity: int = 3 ) -> Union[ str, int ]:
	"""Returns the total file size of all the file paths in an array"""
	n_size = 0
	for _dir in _filedirarray: n_size += os.path.getsize( _dir )
	if formatted: n_size = console.bytesf( n_size, granularity )
	return n_size

def delete_file( _path: Union[ str, os.PathLike ] ) -> None:
	"""PERMANENTLY deletes a file from the path given
	"""
	os.remove( _path )



__all__ = (
	# Get names / types
	'get_parent_dir', 'get_file_name',
	'get_base_name', 'get_file_type',
	'get_file_extension', 'get_files_in_dir',

	# Get sizes
	'get_folder_size', 'get_file_size',
	'get_file_array_size',
	
	# ye
	'delete_file',

	# Searchers
	"search_file_for_keyword",
)

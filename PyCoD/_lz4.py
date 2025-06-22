import os, sys

# sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), "lz4" ) )

# try:
# 	from lz4 import block
# except ModuleNotFoundError:
# 	pip_install( 'lz4' )
# finally:
from .lz4 import block

def compress( data ):
	return block.compress( data, store_size=False )

uncompress = block.decompress

support_info = f'LZ4: Using python-lz4'

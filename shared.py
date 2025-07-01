# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

import subprocess, sys, bpy, datetime
from .pv_py_utils import console
from .pv_py_utils.stdlib import *

plugin_preferences = None
warning_messages: list[ str ] = []

def get_metadata_string( filepath ):
	msg = f"Exported with pv_blender_cod using Blender {bpy.app.version_string}\n"
	msg += concat( f"// Export filename: ", filepath.replace( '\\', '/' ), "\n" )
	msg += f"// Exported on {datetime.datetime.now().strftime( '%B %d, %Y at %H:%M:%S' )}\n"

	if bpy.data.filepath not in ( None, '' ):
		msg += concat( f"// Source filename: ", bpy.data.filepath.replace( '\\', '/' ), "\n" )


	return msg


def calculate_unit_scale_factor( scene ):
	scale = plugin_preferences.scale_length
	
	if scene.unit_settings.system != 'NONE':
		scale *= scene.unit_settings.scale_length
	
	return scale


def raise_error( msg ):
	class ErrorOperator( bpy.types.Operator ):
		bl_idname = "wm.error_operator"
		bl_label = "pv_blender_cod Error"

		message: bpy.props.StringProperty(
			name="Error Message"
		) # type: ignore

		def execute( self, context ):
			self.report( {'ERROR'}, self.message )
			return { 'FINISHED' }

	# Register the operator if not already registered
	if "wm.error_operator" not in bpy.types.Operator.__dict__:
		bpy.utils.register_class( ErrorOperator )

	bpy.ops.wm.error_operator( 'INVOKE_DEFAULT', message = msg )


class PV_OT_message_list_popup( bpy.types.Operator ):
	
	bl_idname = "wm.pv_message_list_popup"
	bl_label = "Warnings occured during export!"

	messages: bpy.props.StringProperty() # type: ignore

	def execute(self, context):
		return {'FINISHED'}

	def invoke(self, context, event):
		return context.window_manager.invoke_props_dialog( self, width=600 )

	def draw(self, context):
		layout = self.layout
		col = layout.column()

		lines = self.messages.split('\n')
		display_lines = lines[:5]
		for line in display_lines:
			col.label(text=line)

		remaining = len(lines) - len(display_lines)
		if remaining > 0:
			col.label( text = f"... + {remaining} more." )

		col.separator()

		col.label(
			text = "Go to Window --> Toggle System Console for more info.",
			icon = 'INFO'
		)


def show_warnings():
	global warning_messages

	# Only show dialog if there are messages to show
	if not warning_messages.__len__(): return

	msg_str = "\n".join( warning_messages )
	warning_messages = []
	# print( "[ DEBUG ] Showing warnings dialog..." )
	print()
	bpy.ops.wm.pv_message_list_popup( 'INVOKE_DEFAULT', messages = msg_str )
	print()

def add_warning( _msg: str ):
	console.warning( _msg )
	
	global warning_messages
	warning_messages.append( '--> ' + _msg )


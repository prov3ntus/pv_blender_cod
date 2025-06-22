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
	msg = "// Exported using pv_blender_cod in Blender %s\n" % bpy.app.version_string
	msg += f"// Exported on {datetime.datetime.now().strftime( '%B %d, %Y at %H:%M:%S' )}\n"

	msg += "// Export filename: '%s'\n" % filepath.replace( "\\", "/" )

	if bpy.data.filepath in ( None, '' ):
		source_file = "<none>"
	else:
		source_file = "'%s'" % bpy.data.filepath.replace( '\\', '/' )

	return msg + f"// Source filename: {source_file}\n"


def calculate_unit_scale_factor( scene, apply_unit_scale = false ):
	'''
	Calcualte the conversion factor to convert from
	Blender units (Usually 1 meter) to inches (CoD units).
	
	If no explicit unit system is set in the scene settings, we fallback to the
	global Blender-CoD scale units. If that option is disabled we use a 1:1
	scale factor to convert from Blender Units to Inches
	(Assuming 1 BU is 1 inch)
	'''
	if not apply_unit_scale:
		return 1.0

	if scene.unit_settings.system != 'NONE':
		return plugin_preferences.scale_length / 0.0254
	else:
		return scene.unit_settings.scale_length / 0.0254


def join_objects_temporarily(objects):
	"""Creates a temporary joined copy of objects without modifying the originals."""

	if not objects:
		return None

	og_selection = set(objects)

	bpy.ops.object.select_all(action='DESELECT')

	copies = []
	for obj in objects:
		obj_copy = obj.copy()
		obj_copy.data = obj.data.copy()
		# object.data doesn't contain transforms
		# so apply them here:
		obj_copy.matrix_world = obj.matrix_world

		bpy.context.collection.objects.link(obj_copy)
		copies.append(obj_copy)

	for obj in copies:
		obj.select_set( true )
	bpy.context.view_layer.objects.active = copies[0]

	bpy.ops.object.join()
	joined = bpy.context.object
	
	# Reselect what we prev. had selected
	bpy.ops.object.select_all(action='DESELECT')
	for obj in og_selection:
		obj.select_set( true )

	return joined


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


class PV_OT_message_list_popup(bpy.types.Operator):
	
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


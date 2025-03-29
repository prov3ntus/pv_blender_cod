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

plugin_preferences = None

def get_metadata_string(filepath):
	import bpy
	msg = "// Exported using pv_blender_cod in Blender %s\n" % bpy.app.version_string
	msg += "// Export filename: '%s'\n" % filepath.replace("\\", "/")
	if bpy.data.filepath is None:
		source_file = "<none>"
	else:
		source_file = bpy.data.filepath.replace('\\', '/')
	msg += "// Source filename: '%s'\n" % source_file
	return msg


def calculate_unit_scale_factor(scene, apply_unit_scale=False):
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


units_of_time = (
	( 'weeks',	604_800	),
	( 'days',	86400	),
	( 'hours',	3600	),
	( 'mins',	60		),
	( 'secs',	1		),
	( 'ms',		10**-3	),
	( 'μs',		10**-6	),
	( 'ns',		10**-9	)
)

def timef( seconds: float, granularity=2 ):
	"""Formats the given time from seconds into a readable string.

	E.g.:
	- 180 (w/ a granularity of 2) would return "3 mins"
	- 192.152 (w/ a granularity of 2) would return "3 mins, 12 secs"
	- 192.152 (w/ a granularity of 3) would return "3 mins, 12 secs, 151 ms"
	- 4825 (w/ a granularity of 2) would return "1 hour, 20 mins"
	- 4825 (w/ a granularity of 3) would return "1 hour, 20 mins, 25 secs"
	"""
	result = []

	for name, count in units_of_time:
		value = seconds // count
		if value:
			seconds -= value * count
			if value == 1:
				name = name.rstrip( 's' )
			result.append( "%i %s" % ( int( value ), name ) )
	
	if not result:
		result = [ "0 secs" ]

	return ', '.join( result[ :granularity ] )



def join_objects_temporarily(objects):
	"""Creates a temporary joined copy of objects without modifying the originals."""

	import bpy
	
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
		obj.select_set(True)
	bpy.context.view_layer.objects.active = copies[0]

	bpy.ops.object.join()
	joined = bpy.context.object
	
	# Reselect what we prev. had selected
	bpy.ops.object.select_all(action='DESELECT')
	for obj in og_selection:
		obj.select_set(True)

	return joined
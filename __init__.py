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


import bpy
from bpy.types import Operator, AddonPreferences
from bpy.props import (BoolProperty, IntProperty, FloatProperty,
					   StringProperty, EnumProperty, CollectionProperty)
from bpy_extras.io_utils import ExportHelper, ImportHelper

from bpy.utils import register_class, unregister_class

import os, time

from . import PyCoD, export_xmodel, export_xanim, import_xmodel, import_xanim, shared, updater
from .PyCoD import sanim, xmodel, xanim, xbin

bl_info = {
	"name": "pv_blender_cod",
	"author": "prov3ntus, shiversoftdev, Ma_rv, CoDEmanX, Flybynyt, SE2Dev",
	"version": (0, 8, 5), # IF EDITING THIS MAKE SURE TO CHANGE updater.LOCAL_VERSION IN updater.py SO UPDATING WORKS CORRECTLY
	"blender": (3, 0, 0),
	"location": "File > Import  |  File > Export",
	"description": "Import/Export XModels and XAnims",
	"wiki_url": "https://github.com/w4133d/pv_blender_cod/",
	"tracker_url": "https://github.com/w4133d/pv_blender_cod/issues/",
	"support": "COMMUNITY",
	"category": "Import-Export"
}

print()
print( "=" * 20, "BlenderCoD Init - pv", "=" * 20 )


def register():
	for cls in classes:
		bpy.utils.register_class(cls)

	# __name__ is the same as the package name (pv_blender_cod)
	preferences = bpy.context.preferences.addons[__name__].preferences

	# Each of these appended functions is executed every time the
	# corresponding menu list is shown
	if not preferences.use_submenu:
		bpy.types.TOPBAR_MT_file_import.append(menu_func_xmodel_import)
		bpy.types.TOPBAR_MT_file_import.append(menu_func_xanim_import)
		bpy.types.TOPBAR_MT_file_export.append(menu_func_xmodel_export)
		bpy.types.TOPBAR_MT_file_export.append(menu_func_xanim_export)
	else:
		bpy.types.TOPBAR_MT_file_import.append(menu_func_import_submenu)
		bpy.types.TOPBAR_MT_file_export.append(menu_func_export_submenu)

	# bpy.types.USERPREF_PT_addons.append(updater.draw_update_button)

	# Set the global 'plugin_preferences' variable for each module
	shared.plugin_preferences = preferences

	# Check for update if auto-update is enabled
	if preferences.auto_update_enabled:
		updated = updater.check_for_update()

		if updated == updater.UPDATE_FAILED:
			print( "[ pv_blender_cod ]\tpv_blender_cod update failed." )
		elif updated == updater.UPDATE_AVAILABLE:
			bpy.app.timers.register( updater.delayed_update_prompt, first_interval = 1.0 )
		elif updated == updater.UPDATE_UPTODATE:
			print( f"[ pv_blender_cod ]\tpv_blender_cod is up-to-date. (v{updater.LOCAL_VERSION})" )
	

def unregister():

	# You have to try to unregister both types of the menus here because
	# the preferences will have already been changed by the time this func runs
	bpy.types.TOPBAR_MT_file_import.remove(menu_func_xmodel_import)
	bpy.types.TOPBAR_MT_file_import.remove(menu_func_xanim_import)
	bpy.types.TOPBAR_MT_file_export.remove(menu_func_xmodel_export)
	bpy.types.TOPBAR_MT_file_export.remove(menu_func_xanim_export)

	bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_submenu)
	bpy.types.TOPBAR_MT_file_export.remove(menu_func_export_submenu)

	# bpy.types.USERPREF_PT_addons.remove(updater.draw_update_button)

	for cls in classes:
		bpy.utils.unregister_class(cls)


def update_submenu_mode(self, context):
	try: unregister()
	except: pass
	register()


def update_scale_length(self, context):
	unit_map = {
		'CENTI':    .01,
		'MILLI':    .001,
		'METER':    1.,
		'KILO':     1000.0,
		'INCH':     .0254,
		'FOOT':     .3048,
		'YARD':     .9144,
		'MILE':     1609.343994,
	}

	if self.unit_enum in unit_map:
		self.scale_length = unit_map[self.unit_enum]


class BlenderCoD_Preferences(AddonPreferences):
	bl_idname = __name__

	use_submenu: BoolProperty(
		name="Group Import/Export Buttons",
		default=False,
		update=update_submenu_mode
	) # type: ignore

	unit_enum: EnumProperty(
		items=(('CENTI', "Centimeters", ""),
			   ('MILLI', "Millimeters", ""),
			   ('METER', "Meters", ""),
			   ('KILO', "Kilometers", ""),
			   ('INCH', "Inches", ""),
			   ('FOOT', "Feet", ""),
			   ('YARD', "Yards", ""),
			   ('MILE', "Miles", ""),
			   ('CUSTOM', "Custom", ""),
			   ),
		name="Default Unit",
		description="The default unit to interpret one Blender Unit as when "
					"no units are specified in the scene presets",
		default='INCH',
		update=update_scale_length
	) # type: ignore

	scale_length: FloatProperty(
		name="Unit Scale",
		description="Scale factor to use, follows the same conventions as "
					"Blender's unit scale in the scene properties\n"
					"(Is the conversion factor to convert one Blender unit to "
					"one meter)",
		soft_min=0.001,
		soft_max=100.0,
		min=0.00001,
		max=100000.0,
		precision=6,
		step=1,
		default=1.0
	) # type: ignore

	auto_update_enabled: BoolProperty(
		name = "Auto-update When Blender Starts",
		description = "Automatically check for pv_blender_cod updates when Blender starts",
		default = True
	) # type: ignore

	def draw(self, context):
		layout = self.layout

		row = layout.row()
		row.prop(self, "use_submenu")

		col1 = layout.row( align = True )
		# Auto-update toggle
		col1.prop( self, "auto_update_enabled" )

		# Update button
		col1.operator(
			"wm.update_addon",
			text="Check for Updates",
			icon='FILE_REFRESH'
		)

		# Scale options
		col2 = row.column(align=True)
		col2.label(text="Units:")
		sub = col2.split(align=True)
		sub.prop(self, "unit_enum", text="")
		sub = col2.split(align=True)
		sub.enabled = self.unit_enum == 'CUSTOM'
		sub.prop(self, "scale_length")


# To support reload properly, try to access a package var, if it's there,
# reload everything
if "bpy" in locals():
	print( "Reloading pv_blender_cod...")
	import imp
	if "import_xmodel" in locals():
		imp.reload(import_xmodel)
	if "export_xmodel" in locals():
		print( "-> Reloading export_xmodel lib" )
		imp.reload(export_xmodel)
	if "import_xanim" in locals():
		imp.reload(import_xanim)
	if "export_xanim" in locals():
		imp.reload(export_xanim)
	if "shared" in locals():
		imp.reload(shared)
	if "PyCoD" in locals():
		imp.reload(PyCoD)
	if "sanim" in locals():
		imp.reload(sanim)
	if "xanim" in locals():
		imp.reload(xanim)
	if "xbin" in locals():
		imp.reload(xbin)
	if "xmodel" in locals():
		print( "-> Reloading xmodel PyCoD lib" )
		imp.reload(xmodel)
	if "updater" in locals():
		imp.reload( updater )
else:
	from . import import_xmodel, export_xmodel, import_xanim, export_xanim
	from . import shared
	from . import PyCoD
	from .PyCoD import sanim, xanim, xbin, xmodel


class COD_MT_import_xmodel(bpy.types.Operator, ImportHelper):
	bl_idname = "import_scene.xmodel"
	bl_label = "Import XModel"
	bl_description = "Import a CoD xmodel_export / xmodel_bin File"
	bl_options = {'PRESET'}

	filename_ext = ".xmodel_export;.xmodel_bin"
	filter_glob: StringProperty(
		default="*.xmodel_export;*.xmodel_bin",
		options={'HIDDEN'}
	)

	ui_tab: EnumProperty(
		items=(('MAIN', "Main", "Main basic settings"),
			   ('ARMATURE', "Armature", "Armature-related settings"),
			   ),
		name="ui_tab",
		description="Import options categories",
		default='MAIN'
	)

	global_scale: FloatProperty(
		name="Scale",
		min=0.001, max=1000.0,
		default=1.0,
	)

	apply_unit_scale: BoolProperty(
		name="Apply Unit",
		description="Scale all data according to current Blender size,"
					" to match CoD units",
		default=True,
	)

	use_single_mesh: BoolProperty(
		name="Combine Meshes",
		description="Combine all meshes in the file into a single object",  # nopep8
		default=True
	)

	use_dup_tris: BoolProperty(
		name="Import Duplicate Tris",
		description=("Import tris that reuse the same vertices as another tri "
					 "(otherwise they are discarded)"),
		default=True
	)

	use_custom_normals: BoolProperty(
		name="Import Normals",
		description=("Import custom normals, if available "
					 "(otherwise Blender will recompute them)"),
		default=True
	)

	use_vertex_colors: BoolProperty(
		name="Import Vertex Colors",
		default=True
	)

	use_armature: BoolProperty(
		name="Import Armature",
		description="Import the skeleton",
		default=True
	)

	use_parents: BoolProperty(
		name="Import Relationships",
		description="Import the parent / child bone relationships",
		default=True
	)

	"""
	force_connect_children : BoolProperty(
		name="Force Connect Children",
		description=("Force connection of children bones to their parent, "
					 "even if their computed head/tail "
					 "positions do not match"),
		default=False,
	)
	"""  # nopep8

	attach_model: BoolProperty(
		name="Attach Model",
		description="Attach head to body, gun to hands, etc.",
		default=False
	)

	merge_skeleton: BoolProperty(
		name="Merge Skeletons",
		description="Merge imported skeleton with the selected skeleton",
		default=False
	)

	use_image_search: BoolProperty(
		name="Image Search",
		description=("Search subdirs for any associated images "
					 "(Warning, may be slow)"),
		default=True
	)

	def execute(self, context):
		from . import import_xmodel
		start_time = time.perf_counter()

		keywords = self.as_keywords(ignore=("filter_glob",
											"check_existing",
											"ui_tab"))

		result = import_xmodel.load(self, context, **keywords)

		if not result:
			_time = shared.timef( time.perf_counter() - start_time )
			self.report( {'INFO'}, "Import finished in %s." % _time )
			print( "Import finished in %s." % _time )
			return {'FINISHED'}
		else:
			self.report( {'ERROR'}, result )
			return {'CANCELLED'}

	@classmethod
	def poll(self, context):
		return (context.scene is not None)

	def draw(self, context):
		layout = self.layout

		layout.prop(self, 'ui_tab', expand=True)
		if self.ui_tab == 'MAIN':
			# Orientation (Possibly)
			# Axis Options (Possibly)

			row = layout.row(align=True)
			row.prop(self, "global_scale")
			sub = row.row(align=True)
			sub.prop(self, "apply_unit_scale", text="")

			layout.prop(self, 'use_single_mesh')

			layout.prop(self, 'use_custom_normals')
			layout.prop(self, 'use_vertex_colors')
			layout.prop(self, 'use_dup_tris')
			layout.prop(self, 'use_image_search')
		elif self.ui_tab == 'ARMATURE':
			layout.prop(self, 'use_armature')
			col = layout.column()
			col.enabled = self.use_armature
			col.prop(self, 'use_parents')

			# Possibly support force_connect_children?
			# sub = col.split()
			# sub.enabled = self.use_parents
			# sub.prop(self, 'force_connect_children')
			col.prop(self, 'attach_model')
			sub = col.split()
			sub.enabled = self.attach_model
			sub.prop(self, 'merge_skeleton')


class COD_MT_import_xanim(bpy.types.Operator, ImportHelper):
	bl_idname = "import_scene.xanim"
	bl_label = "Import XAnim"
	bl_description = "Import a CoD XANIM_EXPORT / XANIM_BIN File"
	bl_options = {'PRESET'}

	filename_ext = ".XANIM_EXPORT;.NT_EXPORT;.XANIM_BIN"
	filter_glob: StringProperty(
		default="*.XANIM_EXPORT;*.NT_EXPORT;*.XANIM_BIN",
		options={'HIDDEN'}
	)

	files: CollectionProperty(type=bpy.types.PropertyGroup)

	global_scale: FloatProperty(
		name="Scale",
		min=0.001, max=1000.0,
		default=1.0,
	)

	apply_unit_scale: BoolProperty(
		name="Apply Unit",
		description="Scale all data according to current Blender size,"
					" to match CoD units",
		default=True,
	)

	use_actions: BoolProperty(
		name="Import as Action(s)",
		description=("Import each animation as a separate action "
					 "instead of appending to the current action"),
		default=True
	)

	use_actions_skip_existing: BoolProperty(
		name="Skip Existing Actions",
		description="Skip animations that already have existing actions",
		default=False
	)

	use_notetracks: BoolProperty(
		name="Import Notetracks",
		description=("Import notes to scene timeline markers "
					 "(or action pose markers if 'Import as Action' is enabled)"),  # nopep8
		default=True
	)

	use_notetrack_file: BoolProperty(
		name="Import NT_EXPORT File",
		description=("Automatically import the matching NT_EXPORT file "
					 "(if present) for each XANIM_EXPORT"),
		default=True
	)

	fps_scale_type: EnumProperty(
		name="Scale FPS",
		description="Automatically convert all imported animation(s) to the specified framerate",   # nopep8
		items=(('DISABLED', "Disabled", "No framerate adjustments are applied"),   # nopep8
			   ('SCENE', "Scene", "Use the scene's framerate"),
			   ('CUSTOM', "Custom", "Use custom framerate")
			   ),
		default='DISABLED',
	)

	fps_scale_target_fps: FloatProperty(
		name="Target FPS",
		description=("Custom framerate that all imported anims "
					 "will be adjusted to use"),
		default=30,
		min=1,
		max=120
	)

	update_scene_fps: BoolProperty(
		name="Update Scene FPS",
		description=("Set the scene framerate to match the framerate "
					 "found in the first imported animation"),
		default=False
	)

	anim_offset: FloatProperty(
		name="Animation Offset",
		description="Offset to apply to animation during import, in frames",
		default=1.0,
	)

	def execute(self, context):
		from . import import_xanim
		start_time = time.perf_counter()

		ignored_properties = ("filter_glob", "files", "apply_unit_scale")
		result = import_xanim.load(
			self,
			context,
			self.apply_unit_scale,
			**self.as_keywords(ignore=ignored_properties))

		if not result:
			_time = shared.timef( time.perf_counter() - start_time )
			self.report( {'INFO'}, "Import finished in %s." % _time )
			print( "Import finished in %s." % _time )
			return {'FINISHED'}
		else:
			self.report( {'ERROR'}, result )
			return {'CANCELLED'}

	@classmethod
	def poll(self, context):
		return (context.scene is not None)

	def draw(self, context):
		layout = self.layout

		row = layout.row(align=True)
		row.prop(self, "global_scale")
		sub = row.row(align=True)
		sub.prop(self, "apply_unit_scale", text="")

		layout.prop(self, 'use_actions')
		sub = layout.split()
		sub.enabled = self.use_actions
		sub.prop(self, 'use_actions_skip_existing')
		layout.prop(self, 'use_notetracks')
		sub = layout.split()
		sub.enabled = self.use_notetracks
		sub.prop(self, 'use_notetrack_file')

		sub = layout.box()
		split = sub.split(factor=0.55)
		split.label(text="Scale FPS:")
		split.prop(self, 'fps_scale_type', text="")
		if self.fps_scale_type == 'DISABLED':
			sub.prop(self, "update_scene_fps")
		elif self.fps_scale_type == 'SCENE':
			sub.label(text="Target Framerate: %.2f" % context.scene.render.fps)
		elif self.fps_scale_type == 'CUSTOM':
			sub.prop(self, 'fps_scale_target_fps')
		layout.prop(self, 'anim_offset')


class COD_MT_export_xmodel(bpy.types.Operator, ExportHelper):
	bl_idname = "export_scene.xmodel"
	bl_label = 'Export XModel'
	bl_description = "Export a CoD xmodel_export / xmodel_bin File"
	bl_options = {'PRESET'}

	filename_ext = ".xmodel_export"
	filter_glob: StringProperty(
		default="*.xmodel_export;*.xmodel_bin", options={'HIDDEN'})

	# List of operator properties, the attributes will be assigned
	# to the class instance from the operator settings before calling.

	# Used to map target_format values to actual file extensions
	format_ext_map = {
		'xmodel_export': '.xmodel_export',
		'xmodel_bin': '.xmodel_bin'
	}

	target_format: EnumProperty(
		name="Format",
		description="The target format to export to",
		items=(('xmodel_export', "ASCII (Export)",
				"Raw text format used from CoD1 to Black Ops I"),
			   ('xmodel_bin', "Binary (Bin)",
				"Binary model format used by Black Ops III")),
		default='xmodel_bin'
	) # type: ignore

	version: EnumProperty(
		name="Version",
		description="xmodel_export format version for export",
		items=(('5', "Version 5", "vCoD, CoD:UO"),
			   ('6', "Version 6", "CoD2, CoD4, World at War, Black Ops I"),
			   ('7', "Version 7", "Black Ops III")),
		default='7'
	) # type: ignore

	use_selection: BoolProperty(
		name="Selection only",
		description=("Export selected meshes only "
					 "(object or weight paint mode)"),
		default=False
	)

	global_scale: FloatProperty(
		name="Scale",
		min=0.001, max=1000.0,
		default=1.0,
	)

	apply_unit_scale: BoolProperty(
		name="Apply Unit",
		description="Scale all data according to current Blender size,"
					" to match CoD units",
		default=True,
	)

	use_vertex_colors: BoolProperty(
		name="Vertex Colors",
		description=("Export vertex colors "
					 "(if disabled, white color will be used)"),
		default=True
	)

	#  White is 1 (opaque), black 0 (invisible)
	use_vertex_colors_alpha: BoolProperty(
		name="Calculate Alpha",
		description=("Automatically calculate alpha channel for vertex colors "
					 "by averaging the RGB color values together "
					 "(if disabled, 1.0 is used)"),
		default=False
	)

	use_vertex_colors_alpha_mode: EnumProperty(
		name="Vertex Alpha Source Layer",
		description="The target vertex color layer to use for calculating the alpha values",  # nopep8
		items=(('PRIMARY', "Active Layer",
				"Use the active vertex color layer to calculate alpha"),
			   ('SECONDARY', "Secondary Layer",
				("Use the secondary (first inactive) vertex color layer to calculate alpha "  # nopep8
				 "(If only one layer is present, the active layer is used)")),
			   ),
		default='PRIMARY'
	)

	use_vertex_cleanup: BoolProperty(
		name="Clean Up Vertices",
		description=("Try this if you have problems converting to xmodel. "
					 "Skips vertices which aren't used by any face "
					 "and updates references."),
		default=False
	)

	apply_modifiers: BoolProperty(
		name="Apply Modifiers",
		description="Apply all mesh modifiers (except Armature)",
		default=False
	)

	modifier_quality: EnumProperty(
		name="Modifier Quality",
		description="The quality at which to apply mesh modifiers",
		items=(('PREVIEW', "Preview", ""),
			   ('RENDER', "Render", ""),
			   ),
		default='PREVIEW'
	)

	use_armature: BoolProperty(
		name="Armature",
		description=("Export bones "
					 "(if disabled, only a 'tag_origin' bone will be written)"),  # nopep8
		default=True
	)

	"""
	use_armature_pose : BoolProperty(
		name="Pose animation to models",
		description=("Export meshes with Armature modifier applied "
					 "as a series of xmodel_export files"),
		default=False
	)

	frame_start : IntProperty(
		name="Start",
		description="First frame to export",
		default=1,
		min=0
	)

	frame_end : IntProperty(
		name="End",
		description="Last frame to export",
		default=250,
		min=0
	)
	"""

	use_weight_min: BoolProperty(
		name="Minimum Bone Weight",
		description=("Try this if you get 'too small weight' "
					 "errors when converting"),
		default=False,
	)

	use_weight_min_threshold: FloatProperty(
		name="Threshold",
		description="Smallest allowed weight (minimum value)",
		default=0.010097,
		min=0.0,
		max=1.0,
		precision=6
	)

	def execute(self, context):
		print()
		print( '=' * 10 + " EXPORT XMODEL " + '=' * 10 )
		from . import export_xmodel
		start_time = time.perf_counter()

		ignore = ("filter_glob", "check_existing")
		result = export_xmodel.save(self, context,
									**self.as_keywords(ignore=ignore))

		if not result:
			_time = shared.timef( time.perf_counter() - start_time )
			self.report( {'INFO'}, "Export finished in %s." % _time )
			print( "Export finished in %s." % _time )
			return {'FINISHED'}
		else:
			self.report({'ERROR'}, result)
			return {'CANCELLED'}

	@classmethod
	def poll(self, context):
		return (context.scene is not None)

	def check(self, context):
		'''
		This is a modified version of the ExportHelper check() method
		This one provides automatic checking for the file extension
		 based on what 'target_format' is (through 'format_ext_map')
		'''
		import os
		from bpy_extras.io_utils import _check_axis_conversion
		change_ext = False
		change_axis = _check_axis_conversion(self)

		check_extension = self.check_extension

		if check_extension is not None:
			filepath = self.filepath
			if os.path.basename(filepath):
				# If the current extension is one of the valid extensions
				#  (as defined by this class), strip the extension, and ensure
				#  that it has the correct one
				# (needed when switching extensions)
				base, ext = os.path.splitext(filepath)
				if ext[1:] in self.format_ext_map:
					filepath = base
				target_ext = self.format_ext_map[self.target_format]
				filepath = bpy.path.ensure_ext(filepath,
											   target_ext
											   if check_extension
											   else "")

				if filepath != self.filepath:
					self.filepath = filepath
					change_ext = True

		return (change_ext or change_axis)

	# Extend ExportHelper invoke function to support dynamic default values
	def invoke(self, context, event):

		# self.use_frame_start = context.scene.frame_start
		self.use_frame_start = context.scene.frame_current

		# self.use_frame_end = context.scene.frame_end
		self.use_frame_end = context.scene.frame_current

		return super().invoke(context, event)

	def draw(self, context):
		layout = self.layout

		layout.prop(self, 'target_format', expand=True)
		layout.prop(self, 'version')

		# Calculate number of selected mesh objects
		if context.mode in ('OBJECT', 'PAINT_WEIGHT'):
			objects = bpy.data.objects
			meshes_selected = len(
				[m for m in objects if m.type == 'MESH' and m.select_get()])
		else:
			meshes_selected = 0

		layout.prop(self, 'use_selection',
					text="Selected Only (%d meshes)" % meshes_selected)

		row = layout.row(align=True)
		row.prop(self, "global_scale")
		sub = row.row(align=True)
		sub.prop(self, "apply_unit_scale", text="")

		# Axis?

		sub = layout.split(factor=0.5)
		sub.prop(self, 'apply_modifiers')
		sub = sub.row()
		sub.enabled = self.apply_modifiers
		sub.prop(self, 'modifier_quality', expand=True)

		# layout.prop(self, 'custom_normals')

		if int(self.version) >= 6:
			row = layout.row()
			row.prop(self, 'use_vertex_colors')
			sub = row.split()
			sub.enabled = self.use_vertex_colors
			sub.prop(self, 'use_vertex_colors_alpha')
			sub = layout.split()
			sub.enabled = (self.use_vertex_colors and
						   self.use_vertex_colors_alpha)
			sub = sub.split(factor=0.5)
			sub.label(text="Vertex Alpha Layer")
			sub.prop(self, 'use_vertex_colors_alpha_mode', text="")

		layout.prop(self, 'use_vertex_cleanup')

		layout.prop(self, 'use_armature')
		box = layout.box()
		box.enabled = self.use_armature
		sub = box.column(align=True)
		sub.prop(self, 'use_weight_min')
		sub = box.split(align=True)
		sub.active = self.use_weight_min
		sub.prop(self, 'use_weight_min_threshold')


class COD_MT_export_xanim(bpy.types.Operator, ExportHelper):
	bl_idname = "export_scene.xanim"
	bl_label = 'Export XAnim'
	bl_description = "Export a CoD XANIM_EXPORT / XANIM_BIN File"
	bl_options = {'PRESET'}

	filename_ext = ".XANIM_EXPORT"
	filter_glob: StringProperty(
		default="*.XANIM_EXPORT;*.XANIM_BIN", options={'HIDDEN'})

	# Used to map target_format values to actual file extensions
	format_ext_map = {
		'XANIM_EXPORT': '.XANIM_EXPORT',
		'XANIM_BIN': '.XANIM_BIN'
	}

	target_format: EnumProperty(
		name="Format",
		description="The target format to export to",
		items=(('XANIM_EXPORT', "XANIM_EXPORT",
				"Raw text format used from CoD1-CoD:BO"),
			   ('XANIM_BIN', "XANIM_BIN",
				"Binary animation format used by CoD:BO3")),
		default='XANIM_EXPORT'
	)

	use_selection: BoolProperty(
		name="Selection Only",
		description="Export selected bones only (pose mode)",
		default=False
	)

	global_scale: FloatProperty(
		name="Scale",
		min=0.001, max=1000.0,
		default=1.0,
	)

	apply_unit_scale: BoolProperty(
		name="Apply Unit",
		description="Scale all data according to current Blender size,"
					" to match CoD units",
		default=True,
	)

	use_all_actions: BoolProperty(
		name="Export All Actions",
		description="Export *all* actions rather than just the active one",
		default=False
	)

	filename_format: StringProperty(
		name="Format",
		description=("The format string for the filenames when exporting multiple actions\n"  # nopep8
					 "%action, %s - The action name\n"
					 "%number, %d - The action number\n"
					 "%base,   %b - The base filename (at the top of the export window)\n"  # nopep8
					 ""),
		default="%action"
	)

	use_notetracks: BoolProperty(
		name="Notetracks",
		description="Export notetracks",
		default=True
	)

	use_notetrack_mode: EnumProperty(
		name="Notetrack Mode",
		description="Notetrack format to use. Always set 'CoD 7' for Black Ops, even if not using notetrack!",   # nopep8
		items=(('SCENE', "Scene",
				"Separate NT_EXPORT notetrack file for 'World at War'"),
			   ('ACTION', "Action",
				"Separate NT_EXPORT notetrack file for 'Black Ops'")),
		default='ACTION'
	)

	use_notetrack_format: EnumProperty(
		name="Notetrack format",
		description=("Notetrack format to use. "
					 "Always set 'CoD 7' for Black Ops, "
					 "even if not using notetrack!"),
		items=(('5', "CoD 5",
				"Separate NT_EXPORT notetrack file for 'World at War'"),
			   ('7', "CoD 7",
				"Separate NT_EXPORT notetrack file for 'Black Ops'"),
			   ('1', "all other",
				"Inline notetrack data for all CoD versions except WaW and BO")
			   ),
		default='1'
	)

	use_notetrack_file: BoolProperty(
		name="Write NT_EXPORT",
		description=("Create an NT_EXPORT file for "
					 "the exported XANIM_EXPORT file(s)"),
		default=False
	)

	use_frame_range_mode: EnumProperty(
		name="Frame Range Mode",
		description="Decides what to use for the frame range",
		items=(('SCENE', "Scene", "Use the scene's frame range"),
			   ('ACTION', "Action", "Use the frame range from each action"),
			   ('CUSTOM', "Custom", "Use a user-defined frame range")),
		default='ACTION'
	)

	frame_start: IntProperty(
		name="Start",
		description="First frame to export",
		min=0,
		default=1
	)

	frame_end: IntProperty(
		name="End",
		description="Last frame to export",
		min=0,
		default=250
	)

	use_custom_framerate: BoolProperty(
		name="Custom Framerate",
		description=("Force all written files to use a user defined "
					 "custom framerate rather than the scene's framerate"),
		default=False
	)

	use_framerate: IntProperty(
		name="Framerate",
		description=("Set frames per second for export, "
					 "30 fps is commonly used."),
		default=30,
		min=1,
		max=1000
	)

	def execute(self, context):
		from . import export_xanim
		start_time = time.perf_counter()
		result = export_xanim.save(
			self,
			context,
			**self.as_keywords(ignore=("filter_glob", "check_existing")))

		if not result:
			msg = "Export finished in %s." % shared.timef( time.perf_counter() - start_time )
			self.report({'INFO'}, msg)
			return {'FINISHED'}
		else:
			self.report({'ERROR'}, result)
			return {'CANCELLED'}

	@classmethod
	def poll(self, context):
		return (context.scene is not None)

	def check(self, context):
		'''
		This is a modified version of the ExportHelper check() method
		This one provides automatic checking for the file extension
		 based on what 'target_format' is (through 'format_ext_map')
		'''
		import os
		from bpy_extras.io_utils import _check_axis_conversion
		change_ext = False
		change_axis = _check_axis_conversion(self)

		check_extension = self.check_extension

		if check_extension is not None:
			filepath = self.filepath
			if os.path.basename(filepath):
				# If the current extension is one of the valid extensions
				#  (as defined by this class), strip the extension, and ensure
				#  that it has the correct one
				# (needed when switching extensions)
				base, ext = os.path.splitext(filepath)
				if ext[1:] in self.format_ext_map:
					filepath = base
				target_ext = self.format_ext_map[self.target_format]
				filepath = bpy.path.ensure_ext(filepath,
											   target_ext
											   if check_extension
											   else "")

				if filepath != self.filepath:
					self.filepath = filepath
					change_ext = True

		return (change_ext or change_axis)

	'''
	# Extend ExportHelper invoke function to support dynamic default values
	def invoke(self, context, event):

		self.use_frame_start = context.scene.frame_start
		self.use_frame_end = context.scene.frame_end
		# self.use_framerate = round(
		#     context.scene.render.fps / context.scene.render.fps_base)

		return super().invoke(context, event)
	'''

	def draw(self, context):
		layout = self.layout
		layout.prop(self, 'target_format', expand=True)
		layout.prop(self, 'use_selection')

		row = layout.row(align=True)
		row.prop(self, "global_scale")
		sub = row.row(align=True)
		sub.prop(self, "apply_unit_scale", text="")

		action_count = len(bpy.data.actions)

		sub = layout.split()
		sub.enabled = action_count > 0
		sub.prop(self, 'use_all_actions',
				 text='Export All Actions (%d actions)' % action_count)

		# Filename Options
		if self.use_all_actions and action_count > 0:
			sub = layout.column(align=True)
			sub.label(text="Filename Options:")
			box = sub.box()
			sub = box.column(align=True)

			sub.prop(self, 'filename_format')

			ex_num = action_count - 1
			ex_action = bpy.data.actions[ex_num].name
			ex_base = os.path.splitext(os.path.basename(self.filepath))[0]

			try:
				icon = 'NONE'
				from . import export_xanim
				template = export_xanim.CustomTemplate(self.filename_format)
				example = template.format(ex_action, ex_base, ex_num)
			except Exception as err:
				icon = 'ERROR'
				example = str(err)

			sub.label(text=example, icon=icon)

		# Notetracks
		col = layout.column(align=True)
		sub = col.row()
		sub = sub.split(factor=0.45)
		sub.prop(self, 'use_notetracks', text="Use Notetrack")
		sub.row().prop(self, 'use_notetrack_mode', expand=True)
		sub = col.column()
		sub.enabled = self.use_notetrack_mode != 'NONE'

		sub = sub.split()
		sub.enabled = self.use_notetracks
		sub.prop(self, 'use_notetrack_file')

		# Framerate
		layout.prop(self, 'use_custom_framerate')
		sub = layout.split()
		sub.enabled = self.use_custom_framerate
		sub.prop(self, 'use_framerate')

		# Frame Range
		sub = layout.row()
		sub.label(text="Frame Range:")
		sub.prop(self, 'use_frame_range_mode', text="")

		sub = layout.row(align=True)
		sub.enabled = self.use_frame_range_mode == 'CUSTOM'
		sub.prop(self, 'frame_start')
		sub.prop(self, 'frame_end')


class COD_MT_import_submenu(bpy.types.Menu):
	bl_idname = "COD_MT_import_submenu"
	bl_label = "Call of Duty"

	def draw(self, context):
		menu_func_xmodel_import(self, context)
		menu_func_xanim_import(self, context)


class COD_MT_export_submenu(bpy.types.Menu):
	bl_idname = "COD_MT_export_submenu"
	bl_label = "Call of Duty"

	def draw(self, context):
		menu_func_xmodel_export(self, context)
		menu_func_xanim_export(self, context)


def menu_func_xmodel_import(self, context):
	self.layout.operator(COD_MT_import_xmodel.bl_idname,
						 text="CoD XModel (.xmodel_export, .xmodel_bin)")


def menu_func_xanim_import(self, context):
	self.layout.operator(COD_MT_import_xanim.bl_idname,
						 text="CoD XAnim (.XANIM_EXPORT, .XANIM_BIN)")


def menu_func_xmodel_export(self, context):
	self.layout.operator(COD_MT_export_xmodel.bl_idname,
						 text="CoD XModel (.xmodel_export, .xmodel_bin)")


def menu_func_xanim_export(self, context):
	self.layout.operator(COD_MT_export_xanim.bl_idname,
						 text="CoD XAnim (.XANIM_EXPORT, .XANIM_BIN)")


def menu_func_import_submenu(self, context):
	self.layout.menu(COD_MT_import_submenu.bl_idname, text="Call of Duty")


def menu_func_export_submenu(self, context):
	self.layout.menu(COD_MT_export_submenu.bl_idname, text="Call of Duty")


'''
	CLASS REGISTRATION
	SEE https://wiki.blender.org/wiki/Reference/Release_Notes/2.80/Python_API/Addons
'''

classes = (
	BlenderCoD_Preferences,
	COD_MT_import_xmodel,
	COD_MT_import_xanim,
	COD_MT_export_xmodel,
	COD_MT_export_xanim,
	COD_MT_import_submenu,
	COD_MT_export_submenu,
	updater.UpdateOperator,
	updater.ConfirmUpdateOperator,
	updater.SimpleDialogConfirmOperator,
	updater.CancelDialogOperator,
	updater.ISeeHowItIsOperator
)



if __name__ == "__main__":
	register()

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


import traceback, bpy, os, sys, cProfile, pstats

from bpy.types import Operator, AddonPreferences
from bpy.props import ( BoolProperty, IntProperty, FloatProperty,
					   StringProperty, EnumProperty, CollectionProperty )
from bpy_extras.io_utils import ExportHelper, ImportHelper

# from bpy.utils import register_class, unregister_class

from . import pv_py_utils
from .pv_py_utils import console, log, pathlib, stdlib, sysframe
from .pv_py_utils.stdlib import *



bl_info = {
	"name": "pv_blender_cod",
	"author": "prov3ntus, shiversoftdev, Ma_rv, CoDEmanX, Flybynyt, SE2Dev",
	"version": ( 0, 9, 0 ),
	"blender": ( 3, 0, 0 ),
	"location": "File > Import  |  File > Export",
	"description": "Import/Export XModels and XAnims",
	"wiki_url": "https://github.com/w4133d/pv_blender_cod/",
	"tracker_url": "https://github.com/w4133d/pv_blender_cod/issues/",
	"support": "COMMUNITY",
	"category": "Import-Export"
}

sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), "PyCoD" ) )

from . import PyCoD, export_xmodel, export_xanim, import_xmodel, import_xanim, shared, updater
from .PyCoD import sanim, xmodel, xanim, xbin, _lz4, lz4
from .PyCoD.lz4 import block, frame, version




print()
print( "=" * 20, "BlenderCoD Init - pv", "=" * 20 )


def register():
	for cls in classes:
		bpy.utils.register_class(cls)

	# __name__ is the same as the package name in __init__.py (_pv_blender_cod)
	preferences = bpy.context.preferences.addons[ __name__ ].preferences

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

	# Check for update if auto-update is enabled.
	if preferences.auto_update_enabled:
		update_result = updater.check_for_update()

		if update_result == updater.UPDATE_FAILED:
			print( "[ pv_blender_cod ]\tpv_blender_cod update failed." )
		elif update_result == updater.UPDATE_AVAILABLE:
			bpy.app.timers.register( updater.delayed_update_prompt, first_interval = .1 )
		elif update_result == updater.UPDATE_UPTODATE:
			print( f"[ pv_blender_cod ]\tpv_blender_cod is up-to-date: v{updater.LOCAL_VERSION}\n" )
	
	# do imp updates here? add to a function?? - pv
	

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


class BlenderCoD_Preferences( AddonPreferences ):
	bl_idname = __name__

	use_submenu: BoolProperty(
		name="Group Import/Export Buttons",
		default=false,
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
		default=.0254
	) # type: ignore

	auto_update_enabled: BoolProperty(
		name = "Auto-update When Blender Starts",
		description = "Automatically check for pv_blender_cod updates when Blender starts",
		default = true
	) # type: ignore

	def draw(self, context):
		layout = self.layout

		row = layout.row()
		row.prop(self, "use_submenu")

		col1 = layout.row( align = true )
		# Auto-update toggle
		col1.prop( self, "auto_update_enabled" )

		# Update button
		col1.operator(
			"wm.update_addon",
			text="Check for Updates",
			icon='FILE_REFRESH'
		)

		# Scale options
		col2 = row.column(align=true)
		col2.label(text="Units:")
		sub = col2.split(align=true)
		sub.prop(self, "unit_enum", text="")
		sub = col2.split(align=true)
		sub.enabled = self.unit_enum == 'CUSTOM'
		sub.prop(self, "scale_length")


# To support reload properly, try to access a package var.
# If it's there, reload everything
if "bpy" in locals():
	print( "Reloading pv_blender_cod...")
	import imp

	modules = {
		# pv_blender_cod
		"import_xmodel": import_xmodel,
		"export_xmodel": export_xmodel,
		"import_xanim": import_xanim,
		"export_xanim": export_xanim,
		"updater": updater,
		"shared": shared,
		# PyCoD
		"PyCoD": PyCoD,
		"sanim": sanim,
		"xanim": xanim,
		"xmodel": xmodel,
		"xbin": xbin,
		"_lz4": _lz4,
		# LZ4
		"lz4": lz4,
		"block": block,
		"frame": frame,
		"version": version,
		# Utils
		"pv_py_utils": pv_py_utils,
		"console": console,
		"log": log,
		"pathlib": pathlib,
		"stdlib": stdlib,
		"sysframe": sysframe,
	}

	for _mod in modules:
		if _mod in locals():
			imp.reload( modules[ _mod ] )	
else:
	from . import import_xmodel, export_xmodel, import_xanim, export_xanim
	from . import shared
	from . import PyCoD
	from .PyCoD import sanim, xanim, xbin, xmodel, _lz4, lz4
	from .PyCoD.lz4 import block, frame, version
	from . import pv_py_utils
	from .pv_py_utils import console, log, pathlib, stdlib, sysframe


class COD_MT_import_xmodel( bpy.types.Operator, ImportHelper ): # type: ignore
	bl_idname = "import_scene.xmodel"
	bl_label = "Import XModel"
	bl_description = "Import a CoD XModel File"
	bl_options = {'PRESET'}

	filename_ext = ".xmodel_export;.xmodel_bin"
	filter_glob: StringProperty(
		default="*.xmodel_export;*.xmodel_bin",
		options={'HIDDEN'}
	) # type: ignore

	files: CollectionProperty( type=bpy.types.PropertyGroup ) # type: ignore

	ui_tab: EnumProperty(
		items=(('MAIN', "Main", "Main basic settings"),
			   ('ARMATURE', "Armature", "Armature-related settings"),
			   ),
		name="ui_tab",
		description="Import options categories",
		default='MAIN'
	) # type: ignore

	global_scale: FloatProperty(
		name="Scale",
		min=0.001, max=1000.0,
		default=1.0,
	) # type: ignore

	use_single_mesh: BoolProperty(
		name="Combine Meshes",
		description="Combine all meshes in the file into a single object",  # nopep8
		default=true
	) # type: ignore

	use_dup_tris: BoolProperty(
		name="Import Duplicate Tris",
		description=("Import tris that reuse the same vertices as another tri "
					 "(otherwise they are discarded)"),
		default=true
	) # type: ignore

	use_custom_normals: BoolProperty(
		name="Import Normals",
		description=("Import custom normals, if available "
					 "(otherwise Blender will recompute them)"),
		default=true
	) # type: ignore

	use_vertex_colors: BoolProperty(
		name="Import Vertex Colors",
		default=true
	) # type: ignore

	use_armature: BoolProperty(
		name="Import Armature",
		description="Import the skeleton",
		default=true
	) # type: ignore

	use_parents: BoolProperty(
		name="Import Relationships",
		description="Import the parent / child bone relationships",
		default=true
	) # type: ignore

	"""
	force_connect_children : BoolProperty(
		name="Force Connect Children",
		description=("Force connection of children bones to their parent, "
					 "even if their computed head/tail "
					 "positions do not match"),
		default=false,
	)
	"""  # nopep8

	attach_model: BoolProperty(
		name="Attach Model",
		description="Attach head to body, gun to hands, etc.",
		default=false
	) # type: ignore

	merge_skeleton: BoolProperty(
		name="Merge Skeletons",
		description="Merge imported skeleton with the selected skeleton",
		default=false
	) # type: ignore

	use_image_search: BoolProperty(
		name="Image Search",
		description=("Search subdirs for any associated images "
					 "(Warning, may be slow)"),
		default=true
	) # type: ignore

	def execute(self, context): # type: ignore
		self.report( {'INFO'}, "Importing XModel..." )

		from . import import_xmodel
		start_time = timer()

		keywords: dict = self.as_keywords(
			ignore=(
				"filter_glob",
				"check_existing",
				"ui_tab",
				"files",
				"filepath"
			)
		) # type: ignore

		errors = []
		for file in self.files:
			_result = import_xmodel.load(
				self, context,
				filepath = os.path.join( os.path.dirname( self.filepath ), file.name ),
				**keywords
			)

			if _result:
				errors.append( _result )


		if not errors.__len__():
			_rep_str = f"Import finished in {console.timef( timer() - start_time )}."
			self.report( { 'INFO' },  _rep_str )
			print( _rep_str )
			_ret_val = { 'FINISHED' }
		else:
			if errors.__len__() == 1:
				self.report( { 'ERROR' }, errors[ 0 ] )
			else:
				self.report( { 'ERROR' }, "There were multiple import errors. Check console for more details." )
			
			for _err in errors: shared.add_warning( _err )
			_ret_val = { 'CANCELLED' }
		
		shared.show_warnings()
		return _ret_val




	@classmethod
	def poll(self, context): # type: ignore
		return (context.scene is not None)

	def draw(self, context):
		layout = self.layout

		layout.prop(self, 'ui_tab', expand=true)
		if self.ui_tab == 'MAIN':
			# Orientation (Possibly)
			# Axis Options (Possibly)

			row = layout.row(align=true)
			row.prop(self, "global_scale")

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


class COD_MT_import_xanim( bpy.types.Operator, ImportHelper ):
	bl_idname = "import_scene.xanim"
	bl_label = "Import XAnim"
	bl_description = "Import a CoD xanim_export / xanim_bin File"
	bl_options = {'PRESET'}

	filename_ext = ".xanim_export;.NT_EXPORT;.xanim_bin"
	filter_glob: StringProperty(
		default="*.xanim_export;*.NT_EXPORT;*.xanim_bin",
		options={'HIDDEN'}
	)

	files: CollectionProperty(type=bpy.types.PropertyGroup)

	global_scale: FloatProperty(
		name="Scale",
		min=0.001, max=1000.0,
		default=1.0,
	)

	use_actions: BoolProperty(
		name="Import as Action(s)",
		description=("Import each animation as a separate action "
					 "instead of appending to the current action"),
		default=true
	)

	use_actions_skip_existing: BoolProperty(
		name="Skip Existing Actions",
		description="Skip animations that already have existing actions",
		default=false
	)

	use_notetracks: BoolProperty(
		name="Import Notetracks",
		description=("Import notes to scene timeline markers "
					 "(or action pose markers if 'Import as Action' is enabled)"),  # nopep8
		default=true
	)

	use_notetrack_file: BoolProperty(
		name="Import NT_EXPORT File",
		description=("Automatically import the matching NT_EXPORT file "
					 "(if present) for each xanim_export"),
		default=true
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
		default=false
	)

	anim_offset: FloatProperty(
		name="Animation Offset",
		description="Offset to apply to animation during import, in frames",
		default=1.0,
	)

	def execute(self, context):
		self.report( { 'INFO' }, "Importing XAnim..." )

		from . import import_xanim
		start_time = timer()

		ignored_properties = ( "filter_glob", "files" )
		result = import_xanim.load(
			self, context,
			**self.as_keywords( ignore = ignored_properties )
		)

		if not result:
			_time = console.timef( timer() - start_time )
			self.report( { 'INFO' }, "Import finished in %s." % _time )
			print( "Import finished in %s." % _time )

			_ret_val = { 'FINISHED' }
		else:
			self.report( { 'ERROR' }, result )

			_ret_val = { 'CANCELLED' }

		shared.show_warnings()
		return _ret_val

	@classmethod
	def poll(self, context):
		return (context.scene is not None)

	def draw(self, context):
		layout = self.layout

		row = layout.row(align=true)
		row.prop(self, "global_scale")

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


class COD_MT_export_xmodel( bpy.types.Operator, ExportHelper ):
	bl_idname = "export_scene.xmodel"
	bl_label = 'Export XModel'
	bl_description = "Export a CoD xmodel_export / xmodel_bin File"
	bl_options = {'PRESET'}

	filename_ext = ".xmodel_export"
	filter_glob: StringProperty(
		default="*.xmodel_export;*.xmodel_bin", options={'HIDDEN'}
	) # type: ignore

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
		name="XModel Version",
		description="xmodel_export format version for export",
		items=(
			( '', "Deprecated", '' ),
			('5', "Version 5", "CoD1 | CoD:UO"),
			('6', "Version 6", "CoD2 | CoD4 | World at War | Black Ops I"),
			( '', 'Black Ops III', '' ),
			('7', "Version 7", "Black Ops III")
		),
		default='7'
	) # type: ignore

	use_selection: BoolProperty(
		name="Selection Only",
		description=("Export selected meshes only "
					 "(object or weight paint mode)"),
		default=true
	) # type: ignore

	global_scale: FloatProperty(
		name="Global Scale",
		min=0.001, max=1000.0,
		step = 10,
		default=1.0,
	) # type: ignore

	use_vertex_colors: BoolProperty(
		name="Export Vertex Colors",
		description="If disabled, default full white will be used, as T7 expects.",
		default=true
	) # type: ignore

	# Might remove this at some point - pv
	use_vertex_colors_alpha_mode: EnumProperty(
		name="Vertex Color Source Layer",
		description="The target vertex color layer to use",
		items=(
			(
				'PRIMARY',
				"Active Layer",
				"Use the active vertex color layer"
			),
			(
				'SECONDARY',
				"Secondary Layer",
				"Use the first inactive (secondary) vertex color layer "
					"(If only one layer is present, the active layer is used)"
			),
		),
		default='PRIMARY'
	) # type: ignore

	should_merge_by_distance: BoolProperty(
		name="Merge by Distance",
		description=(
			"Perform a \"Merge by distance\" operation on export.\n"
			" - Try this if APE's output window shows the \"Vertex normal is 0\" error\n"
			" - This does not affect the original mesh"
		),
		default=false
	) # type: ignore

	vert_merge_distance: FloatProperty(
		name="Merge Distance",
		description="Distance option for \"Merge by Distance\" option above.\n" \
		"Click me to see the proper value - my last digit gets cut off",
		min=.00001, max=10.0,
		step = 1,
		default=.0001,
	) # type: ignore

	apply_modifiers: BoolProperty(
		name="Apply Modifiers",
		description="Apply all mesh modifiers (except Armature)",
		default=true
	) # type: ignore

	# Unused
	"""
	modifier_quality: EnumProperty(
		name="Modifier Quality",
		description="The quality at which to apply mesh modifiers",
		items=(('PREVIEW', "Preview", ""),
			   ('RENDER', "Render", ""),
			   ),
		default='PREVIEW'
	)
	"""

	use_armature: BoolProperty(
		name="Armature",
		description=("Export bones "
					 "(if disabled, only a 'tag_origin' bone will be written)"),  # nopep8
		default=false
	) # type: ignore

	use_weight_min: BoolProperty(
		name="Minimum Bone Weight",
		description=("Try this if you get 'too small weight' "
					 "errors when converting"),
		default=false,
	) # type: ignore

	use_weight_min_threshold: FloatProperty(
		name="Threshold",
		description="Smallest allowed weight (minimum value)",
		default=0.010097,
		min=0.0,
		max=1.0,
		precision=6
	) # type: ignore

	def execute( self, context ):
		self.report( { 'INFO' }, "Exporting XModel..." )

		print()
		print( '=' * 10 + " EXPORT XMODEL " + '=' * 10 )

		from . import export_xmodel
		start_time = timer()

		ignore = ( "filter_glob", "check_existing" )
		result = None

		try:
			results_path = 'M:/Black Ops III/steamapps/common/Call of Duty Black Ops III/model_export/_pv/_vtx_testingprofile_results.prof'
			cProfile.runctx('export_xmodel.save(self, context,**self.as_keywords( ignore=ignore ) )', globals(), locals(), results_path)

			p = pstats.Stats(results_path)
			p.strip_dirs().sort_stats('time').print_stats(20) # Top 20 functions by cumulative time
			p.sort_stats('cumulative').print_stats(20) # Top 20 functions by total time spent in them (and sub-calls)

			# result = export_xmodel.save(
			# 	self, context,
			# 	**self.as_keywords( ignore=ignore ) # type: ignore
			# )
		except Exception as _e:
			shared.add_warning(
				"An error occured while exporting the XModel!\n"
				"Please go to 'Blender Preferences' → 'Add-ons' → 'pv_blender_cod' → 'Report a Bug' and let me know!"
				"\nError:\n" + _e.__str__()
			)

			traceback.print_exc()

		
		if not result:
			_time = console.timef( timer() - start_time )
			str_finished = f"Export finished in { _time }."

			self.report( { 'INFO' }, str_finished )
			print( str_finished )

			_ret_val = { 'FINISHED' }
		else:
			# self.report( { 'ERROR' }, result )
			self.report( { 'INFO' }, result )
			_ret_val = { 'CANCELLED' }
		
		shared.show_warnings()
		return _ret_val

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
		change_ext = false
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
					change_ext = true

		return (change_ext or change_axis)

	# Extend ExportHelper invoke function to support dynamic default values
	def invoke(self, context, event):

		# self.use_frame_start = context.scene.frame_start
		self.use_frame_start = context.scene.frame_current

		# self.use_frame_end = context.scene.frame_end
		self.use_frame_end = context.scene.frame_current

		return super().invoke(context, event)

	def draw(self, context):
		layout: bpy.types.UILayout = self.layout # type: ignore


		# layout.separator( factor = 1 )


		#################
		## File Format ##
		#################


		box = layout.box()
		box.label(
			text = "Export Format",
			icon = 'FILE'
		)

		row = box.row()
		col = row.column( align = true )
		col.label( text = 'XModel Version' )
		col = row.column()
		col.prop(
			self, 'version',
			text = ''
		)
		box.prop(
			self, 'target_format',
			expand = true
		)


		# layout.separator( factor = 1 )


		#############
		## GENERAL ##
		#############

		box = layout.box()
		box.label(
			text = "General",
			icon = 'SETTINGS'
		)

		# Calculate number of selected mesh objects
		if context.mode in ( 'OBJECT', 'PAINT_WEIGHT' ):
			objects = bpy.data.objects
			n_selected = len(
				[ m for m in objects if m.type == 'MESH' and m.select_get() ]
			)
		else:
			n_selected = None

		_text = f"Selection Only "
		if n_selected: _text += f"({n_selected} mesh{'es' if n_selected - 1 else ''})"
		else: _text += '(No valid meshes)'

		box.prop(
			self, 'use_selection',
			text = _text
		) 
		box.prop(
			self, 'apply_modifiers'
		)
		box.prop(
			self, 'should_merge_by_distance'
		)
		row = box.row( align = true )
		row.enabled = self.should_merge_by_distance
		row.prop(
			self, 'vert_merge_distance'
		)


		# layout.separator( factor = 1 )


		################
		## VTX COLORS ##
		################

		if int( self.version ) >= 6:
			box = layout.box()
			box.label(
				text = 'Vertex Colors',
				icon = 'COLOR'
			)

			box.prop(
				self, 'use_vertex_colors'
			)
			box.enabled = self.use_vertex_colors
			box.label(
				text = "Vertex Color Layer",
				# icon = 'LAYER_USED'
			)

			box.prop(
				self, 'use_vertex_colors_alpha_mode',
				text = ''
			)


		##############
		## ARMATURE ##
		##############

		box = layout.box()
		box.label(
			text = "Armature / Joints",
			icon = 'ARMATURE_DATA'
		)

		box.prop(
			self, 'use_armature',
			text = 'Export Armature'
		)
		row = box.row()
		row.enabled = self.use_armature
		row.prop( self, 'use_weight_min' )
		row = box.row()
		row.active = self.use_weight_min
		row.prop( self, 'use_weight_min_threshold' )


		# layout.separator( factor = 1 )


		###########
		## SCALE ##
		###########

		box = layout.box()
		box.label(
			text = "Scale",
			icon = 'CON_SIZELIKE'
		)

		box.prop(
			self, "global_scale"
		)


class COD_MT_export_xanim( bpy.types.Operator, ExportHelper ):
	bl_idname = "export_scene.xanim"
	bl_label = 'Export XAnim'
	bl_description = "Export a CoD XAnim ASCII / Binary File"
	bl_options = {'PRESET'}

	filename_ext = ".xanim_export"
	filter_glob: StringProperty(
		default="*.xanim_export;*..xanim_bin", options={'HIDDEN'})

	# Used to map target_format values to actual file extensions
	format_ext_map = {
		'xanim_export': '.xanim_export',
		'xanim_bin': '.xanim_bin'
	}

	target_format: EnumProperty(
		name="Format",
		description="The target format to export to",
		items=(
			(
				'xanim_export', "ASCII (Export)",
				"Raw text format used from CoD1 to Black Ops I"
			),
			(
				'xanim_bin', "Binary (Bin)",
				"Binary animation format used by Black Ops III"
			)
		),
		default='xanim_bin'
	) # type: ignore

	use_selection: BoolProperty(
		name="Selection Only",
		description="Export selected bones only (pose mode)",
		default=false
	)

	global_scale: FloatProperty(
		name="Scale",
		min=0.001, max=1000.0,
		default=1.0,
	)

	use_all_actions: BoolProperty(
		name="Export All Actions",
		description="Export *all* actions rather than just the active one",
		default=false
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
		default=true
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
					 "the exported xanim_export file(s)"),
		default=false
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
		default=false
	)

	use_framerate: IntProperty(
		name="Framerate",
		description=("Set frames per second for export, "
					 "30 fps is commonly used."),
		default=30,
		min=1,
		max=1000
	)

	def execute( self, context ):
		self.report( { 'INFO' }, "Exporting XAnim..." )

		from . import export_xanim
		start_time = timer()
		result = export_xanim.save(
			self,
			context,
			**self.as_keywords( ignore = ( "filter_glob", "check_existing" ) ) )

		if not result:
			msg = f"Export finished in {console.timef( timer() - start_time )}."
			self.report( {'INFO'}, msg )
			_ret_val = {'FINISHED'}
		else:
			self.report( {'ERROR'}, result )
			_ret_val = {'CANCELLED'}
		
		shared.show_warnings()
		return _ret_val

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
		change_ext = false
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
					change_ext = true

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
		layout.prop(self, 'target_format', expand=true)
		layout.prop(self, 'use_selection')

		row = layout.row(align=true)
		row.prop(self, "global_scale")

		action_count = len(bpy.data.actions)

		sub = layout.split()
		sub.enabled = action_count > 0
		sub.prop(self, 'use_all_actions',
				 text='Export All Actions (%d actions)' % action_count)

		# Filename Options
		if self.use_all_actions and action_count > 0:
			sub = layout.column(align=true)
			sub.label(text="Filename Options:")
			box = sub.box()
			sub = box.column(align=true)

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
		col = layout.column(align=true)
		sub = col.row()
		sub = sub.split(factor=0.45)
		sub.prop(self, 'use_notetracks', text="Use Notetrack")
		sub.row().prop(self, 'use_notetrack_mode', expand=true)
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

		sub = layout.row(align=true)
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


def menu_func_xmodel_import( self, context ):
	self.layout.operator(
		COD_MT_import_xmodel.bl_idname,
		text = "Import XModel (.xmodel_[bin/export])"
	)


def menu_func_xanim_import( self, context ):
	self.layout.operator(
		COD_MT_import_xanim.bl_idname,
		text = "Import XAnim (.xanim_[bin/export])"
	)


def menu_func_xmodel_export( self, context ):
	self.layout.operator(
		COD_MT_export_xmodel.bl_idname,
		text = "Export XModel (.xmodel_[bin/export])"
	)


def menu_func_xanim_export( self, context ):
	self.layout.operator(
		COD_MT_export_xanim.bl_idname,
		text = "Export XAnim (.xanim_[bin/export])"
	)


def menu_func_import_submenu( self, context ):
	self.layout.menu(
		COD_MT_import_submenu.bl_idname,
		text = "Call of Duty"
	)


def menu_func_export_submenu( self, context ):
	self.layout.menu(
		COD_MT_export_submenu.bl_idname,
		text="Call of Duty"
	)


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
	updater.ViewFullChangelogOnGithubOperator,
	shared.PV_OT_message_list_popup,
)



if __name__ == "__main__":
	register()

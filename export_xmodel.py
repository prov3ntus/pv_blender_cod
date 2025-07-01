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

import bpy
import bmesh # type: ignore
import os
from itertools import repeat

from .pv_py_utils import console

from .pv_py_utils.stdlib import *

from . import shared as shared
from .PyCoD import xmodel as XModel

def update_step( operator, step, total_steps ):
	operator.report( { 'INFO' }, f"Progress: {( ( step / total_steps ) * 100 ):.2f}%" )


def _skip_notice( ob_name, mesh_name, notice ):
	vargs = ( ob_name, mesh_name, notice )
	print( "\nSkipped object \"%s\" (mesh \"%s\"): %s" % vargs )


def uv_layer_is_empty( uv_layer ):
	return all( _lyr.uv.length_squared == 0.0 for _lyr in uv_layer.data )


def validate_str_for_ape( _mtl_name: str ):
	"""Replaces any non-ascii / non-alpha-numeric character
	with an underscore `_`, as well as `lower()`s the mtl name.
	Crazy how no maintainer has added this before now.
		- pv [ 2025/04/07 ]
	"""

	return ''.join( c if c.isascii() and c.isalnum() else '_' for c in _mtl_name  ).lower()


def gather_exportable_objects(self, context,
							  use_selection,
							  use_armature,
							  use_armature_filter=true ):
	'''
	Gather relevent objects for export
	Returns a tuple in the format (armature, [objects])

	Args:
		use_selection - Only export selected objects
		use_armature - Include the armature
		use_armature_filter - Only export meshes that are influenced by the active armature
		Automatically include all objects that use the
							  active armature?
	'''  # nopep8

	armature = None
	# If we're using the filter, the exporting operation doesn't
	# export selected objects correctly, due to the filter check
	# intercepting the mesh before it can be appended to exportable_objs
	# This should default to false if armature is false. There is NO reason
	# to use the armature filter if we're not exporting an armature. - pv
	use_armature_filter = armature and use_armature_filter
	exportable_objs = []
	errored_objs = []

	# Do a quick check to see if the active object is an armature
	#  If it is - use it as the target armature
	if( context.active_object is not None
		and context.active_object.type == 'ARMATURE' ):
		armature = context.active_object

	# A list of objects we need to check *after* we find an armature
	# Used when use_armature_filter is enabled because we can't check
	#  the modifiers if we don't know what armature we're using yet
	secondary_objects = []

	def test_armature_filter(object):
		"""
		Test an object against the armature filter
		returns true if the object passed
		returns false if the object failed the test
		"""
		for modifier in object.modifiers:
			if modifier.type == 'ARMATURE' and modifier.object == armature:
				return true
		return false


	if use_selection: _objects = bpy.context.selected_objects
	else: _objects = bpy.data.objects

	# print( ( 'U' if use_selection else "Not u" ) + "sing selection", _objects )

	console.log( "Checking", _objects.__len__(), f"object{ 's' if _objects.__len__() - 1 else '' }..." )
	for obj in _objects:
		# print( f"[ DEBUG ] Checking '{ obj.name }' for export..." )

		# Either grab the active armature - or the first armature in the scene
		if(
			obj.type == 'ARMATURE' and use_armature
			and ( armature is None or obj == context.active_object )
			and len( obj.data.bones ) > 0
		):
			armature = obj
			continue

		if obj.type != 'MESH':
			# console.warning(
			# 	f"[ pv_blender_cod ] Skipping object '{obj.name}' of type '{obj.type}' as it's not "
			# 	"a mesh or an armature (or we're not exporting armatures)..."
			# )
			errored_objs.append( obj )
			continue

		if len( obj.material_slots ) < 1:
			shared.add_warning( f"Found no materials on object '{obj.name}' - skipping..." )
			# Extra info
			print( "--> You must have a material assigned to each polygon before exporting your mesh as an XModel!" )
			print( f"--> To fix this, assign materials to all polygons on '{obj.name}' before exporting." )
			errored_objs.append( obj )
			continue
		
		uv_layer = obj.data.uv_layers.active
		if not uv_layer or ( uv_layer and uv_layer_is_empty( uv_layer ) ):
			shared.add_warning( f"Mesh '{ obj.data.name }' has no UVs. Skipping..." )
			errored_objs.append( obj )
			continue

		if use_armature_filter:
			if armature is None:
				# Defer the check for this object until *after* we know
				#  which armature we're using
				secondary_objects.append( obj )
			else:
				if test_armature_filter( obj ):
					exportable_objs.append( obj )
			continue
		
		exportable_objs.append( obj )

	# Perform a secondary filter pass on all objects we missed
	#  (before the armature was found)
	if use_armature_filter:
		for obj in secondary_objects:
			if not test_armature_filter( obj ):
				continue

			exportable_objs.append(obj)

	"""
	# Fallback to exporting only the selected object if we couldn't find any
	if( use_armature and armature is None
		and len( exportable_objs ) == 0
		and context.active_object is not None
		and context.active_object.type == 'MESH'
		and context.active_object not in errored_objs
	):
		exportable_objs = [ context.active_object ]
	"""


	console.log( "Found", exportable_objs.__len__(), "exportable object(s) for conversion" )

	return armature, exportable_objs


def material_gen_image_dict(material):
	'''
	Generate a PyCoD compatible image dict from a given Blender material
	'''
	out = {}
	if not material:
		return out
	unk_count = 0
	#! Texture slots are deprecated
	"""for slot in material.texture_slots:
		if slot is None:
			continue
		texture = slot.texture
		if texture is None:
			continue
		if texture.type == 'IMAGE':
			try:
				tex_img = slot.texture.image
				if tex_img.source != 'FILE':
					image = tex_img.name
				else:
					image = os.path.basename(tex_img.filepath)
			except:
				image = "<undefined>"

			if slot.use_map_color_diffuse:
				out['color'] = image
			elif slot.use_map_normal:
				out['normal'] = image
			else:
				out['unk_%d' % unk_count] = image
				unk_count += 1"""
	return out


class ExportMesh(object):
	'''
	Internal class used for handling the conversion of mesh data into
	a PyCoD compatible format
	'''
	__slots__ = ( 'mesh', 'object', 'matrix', 'weights', 'materials' )

	def __init__( self, obj, mesh, global_materials ):
		self.mesh = mesh
		self.object = obj
		self.matrix = obj.matrix_world
		self.weights = [ [] for _ in repeat( None, len( mesh.vertices ) ) ]

		self.materials = []

		self.recalc_mtl_indices()
		# Map the mesh's mtl indices to our model's mtl indices
		self.gen_material_indices( global_materials )


	def clear( self ):
		self.mesh.user_clear()
		bpy.data.meshes.remove( self.mesh )


	def fix_too_many_weights( self ):
		"""Find places where we have too many weights and remove the lowest weights, then renormalize the total"""

		b_any_bad = false

		for v in range( 0, len( self.weights ) ):

			if len( self.weights[v] ) <= 15: # Even though ape says we can have 16, we cant. we can only have 15.
				continue

			b_any_bad = true

			self.weights[v].sort( key= lambda x: x[1], reverse=true ) # sort by the weight amount, descending order
			while len(self.weights[v]) > 15:
				self.weights[v].pop() # get rid of lowest

			length = sum( [ x[ 1 ] ** 2 for x in self.weights[ v ] ] ) ** 0.5 # calc the vector length
			self.weights[ v ] = [ ( x[ 0 ], x[ 1 ] / length ) for x in self.weights[ v ] ] # divide the entire array by the length (normalize it)

		return b_any_bad


	def add_weights( self, bone_table, weight_min_threshold = 0.0 ):
		ob = self.object
		if ob.vertex_groups is None:
			for i in range( len( self.weights ) ):
				self.weights[i] = [ ( 0, 1.0 ) ]
		else:
			# group_map[group_index] yields bone index or None
			group_map = [ None ] * len( ob.vertex_groups )
			for group_index, group in enumerate( ob.vertex_groups ):
				if group.name in bone_table:
					group_map[group_index] = bone_table.index( group.name )

			# For debugging blender's cleanup thing deleting the mesh b4 we're done w/ it
			# print( self.mesh.name, 'in bpy.data.meshes?', self.mesh.name in bpy.data.meshes )

			for vert_index, vert in enumerate( self.mesh.vertices ):
				for group in vert.groups:
					bone_index = group_map[ group.group ]
					if bone_index is not None:
						if group.weight < weight_min_threshold:
							continue  # Skip weights below the weight threshold

						self.weights[vert_index].append(
							( bone_index, group.weight )
						)

			# Any verts without weights will get a 1.0 weight to the root bone
			for weights in self.weights:
				if len(weights) == 0:
					weights.append( ( 0, 1.0 ) )
			
			b_any_bad = self.fix_too_many_weights()
			
			if b_any_bad:
				print("WARNING: Model had some verticies with too many weights."
				"Removed the lowest until restrictions of 16 weights or less were met")


	def recalc_mtl_indices( self ):		
		""" Makes sure that mtls are all indexed correctly, as sometimes either Blender or
		other programs that generate/import meshes do not generate mtl indices correctly,
		hence leading to an "index out of range" error in ExportMesh.gen_material_indices()
		"""
		materials = { _mtl.name: idx for idx, _mtl in enumerate( self.object.material_slots ) }

		
		# print( f"Material slots for { self.mesh.name }:" )
		# for idx, slot in enumerate( self.object.material_slots ):
		# 	print( f"Mtl { idx }: { slot.material.name if slot.material else 'None' }" )

		for poly in self.mesh.polygons:
			# Get the material assigned to the polygon
			mtl = self.object.material_slots[ poly.material_index ].material if poly.material_index < len( self.object.material_slots ) else None

			if not mtl:
				continue

			# Reassign to correct index (in case of mismatch)
			correct_index = materials.get( mtl.name, -1 )

			if correct_index == -1: continue
			
			poly.material_index = correct_index


	def gen_material_indices( self, global_materials: list ):
		"""Adds the mesh's materials into the global map of materials, as when
		we assign a material id to a polygon, it has to be from the global
		index, as xmodel requires.
		"""
		self.materials = [ None ] * len( self.mesh.materials )
		prev_len = global_materials.__len__() # debugging - pv

		for material_index, material in enumerate( self.mesh.materials ):
			"""
			if material in global_materials:
				# Make local materials list match the global index for the materials on it.
				self.materials[ material_index ] = global_materials.index( material ) # nopep8
			else:
				self.materials[ material_index ] = len( global_materials )
				global_materials.append( material )
			"""
			# Made what we're doing a lot clearer. Old implementation 
			# has been commented out and can be found above.

			if material not in global_materials:
				global_materials.append( material )
			
			# Make local materials list match the global index for the materials on it.
			# This essentially makes self.materials a map of local mtl indices to global ones,
			# as xmodel stores material info global to that xmodel, and we are merging multiple
			# meshes into 1 xmodel.
			self.materials[ material_index ] = global_materials.index( material )

		# print( "[ DEBUG ] gen_material_indices() RESULTS:" )
		# print( f"\tAdded { global_materials.__len__() - prev_len } mtls to global map of mtls" )

		# print( f"\tCurrent look of GLOBAL mtls:" )
		# print( global_materials )
		# print( f"\tCurrent look of local mtls:" )
		# print( self.materials )


	def to_xmodel_mesh(
			self,
			use_vtx_cols = true,
			use_alpha = false,
			use_alpha_mode = 'PRIMARY',
			global_scale = 1.0
		):

		mesh = XModel.Mesh( self.mesh.name )

		# calc_normals functions do not exist in blender 4.0/4.1+
		# because they re-calculate it when needed automatically.
		# So, we don't need to recalc. (which is why they removed
		# the function)
		if bpy.app.version < ( 4, 1, 0 ):
			if self.mesh.has_custom_normals:
				self.mesh.calc_normals_split() # Taken out in 4.1
			
			if bpy.app.version < ( 4, 0, 0 ):
				self.mesh.calc_normals() # Taken out in 4.0

		uv_layer = self.mesh.uv_layers.active
		vc_layer = self.mesh.vertex_colors.active if use_vtx_cols else None

		# Get the vertex layer to use for alpha
		vca_layer = None
		if use_alpha:
			if use_alpha_mode == 'PRIMARY':
				vca_layer = vc_layer
			elif use_alpha_mode == 'SECONDARY':
				for layer in self.mesh.vertex_colors:
					if layer is not vc_layer:
						vca_layer = layer
						break # Only need the first one we find


		# Apply transformation matrix to vertices
		for vert_index, vert in enumerate( self.mesh.vertices ):
			mesh_vert = XModel.Vertex()
			transformed_pos = self.matrix @ vert.co # Apply matrix transform
			mesh_vert.offset = tuple( transformed_pos * global_scale )
			mesh_vert.weights = self.weights[ vert_index ]
			mesh.verts.append( mesh_vert )

		# Extract 3x3 rotation matrix from transformation matrix (ignoring translation)
		normal_transform = self.matrix.to_3x3()
		invalid_mtl_idxs_encountered = false

		# print( f"[ DEBUG ] Materials on ExportMesh of '{ self.mesh.name }':", self.materials )
		# print( f"[ DEBUG ] Materials on actual mesh of '{ self.mesh.name }':", self.mesh.materials )
		for polygon in self.mesh.polygons:
			face = XModel.Face( 0, 0 )
			# print( f"[ DEBUG ] Number of indices for '{ self.mesh.name }':", face.indices.__len__() )
			# print( f"[ DEBUG ] Number of loop idx's on poly: { polygon.loop_indices.__len__() }" )
			# print( f"[ DEBUG ] Current mtl index of '{ self.mesh.name }': { polygon.material_index }" )
			# print( "polygon.material_index =", polygon.material_index )

			if polygon.material_index >= self.materials.__len__():
				invalid_mtl_idxs_encountered = true
				"""
				shared.raise_error(
					f"Material index for a polygon of '{ self.mesh.name }' is "
					"greater than the total count of all materials being exported.\n"
					f"( { polygon.material_index  } >= { self.materials.__len__() } )\n"
					f"Please fix/redo your materials!"
				)
				"""
				continue

			face.material_id = self.materials[ polygon.material_index ]

			for i, loop_index in enumerate( polygon.loop_indices ):
				loop = self.mesh.loops[ loop_index ]

				# Get UV coordinates
				uv = uv_layer.data[ loop_index ].uv

				# Get vertex colours (with optional alpha channel)
				if vca_layer is not None:
					vtx_col = vca_layer.data[ loop_index ].color
					rgba = ( vtx_col[0], vtx_col[1], vtx_col[2], vtx_col[3] if len(vtx_col) > 3 else 1.0 )
				elif vc_layer is not None:
					vtx_col = vc_layer.data[ loop_index ].color
					rgba = ( vtx_col[0], vtx_col[1], vtx_col[2], vtx_col[3] if len(vtx_col) > 3 else 1.0 )
				else:
					rgba = ( 1.0, 1.0, 1.0, 1.0 )

				# Apply transformation to normal
				transformed_normal = normal_transform @ loop.normal
				transformed_normal.normalize() # Ensure normal stays unit-length

				vert = XModel.FaceVertex(
					loop.vertex_index,
					transformed_normal, # Use transformed normal
					rgba,
					(uv.x, 1.0 - uv.y)
				)
				face.indices[ i ] = vert

			# Fix winding order
			face.indices[ 1 ], face.indices[ 2 ] = face.indices[ 2 ], face.indices[ 1 ]

			mesh.faces.append( face )

		if invalid_mtl_idxs_encountered:
			shared.add_warning(
				f"Skipped one or more polys on '{self.mesh.name}'; material indices were invalid."
			)
			# Extra info
			print( "--> Only the polygons with bad materials have been skipped." )
			print( f"--> To fix this issue, please remove & re-assign the materials on '{self.mesh.name}'." )

		return mesh



def save(
		export_operator, context, filepath,
		target_format = 'xmodel_bin',
		version = '7',
		use_selection = false,
		global_scale = 1.0,
		apply_modifiers = true,
		use_vertex_colors = true,
		use_vertex_colors_alpha = true,
		use_vertex_colors_alpha_mode = 'PRIMARY',
		should_merge_by_distance = true,
		vert_merge_distance = .0001,
		use_armature = true,
		use_weight_min = false,
		use_weight_min_threshold = 0.010097
	):

	# Disabled for now
	use_armature_pose = false
	use_frame_start = 0
	use_frame_end = 1

	# Apply unit conversion factor to the scale
	global_scale /= shared.calculate_unit_scale_factor( context.scene )

	# There's no context object right after object deletion, need to set one
	if context.object:
		last_mode = context.object.mode
	else:
		last_mode = 'OBJECT'

		for ob in bpy.data.objects:
			if ob.type == 'MESH':
				context.view_layer.objects.active = ob
				break
			else:
				return "No mesh to export!"

	armature, objects = gather_exportable_objects(
		export_operator, context,
		use_selection, use_armature
	)

	# If we were unable to detect any valid rigged objects
	# we'll use the selected mesh.
	if len( objects ) == 0:
		shared.add_warning( "No valid objects to export!" )
		return "There are no objects to export!"

	# Set up the argument keywords for save_model
	kwargs = {
		"target_format": target_format,
		"version": int(version),
		"global_scale": global_scale,
		"apply_modifiers": apply_modifiers,
		# "modifier_quality": modifier_quality, # Unused - pv
		"use_vertex_colors": use_vertex_colors,
		"use_vertex_colors_alpha": use_vertex_colors_alpha,
		"use_vertex_colors_alpha_mode": use_vertex_colors_alpha_mode,
		"should_merge_by_distance": should_merge_by_distance,
		"vert_merge_distance": vert_merge_distance,
		"use_armature": use_armature & (not use_armature_pose),
		"use_weight_min": use_weight_min,
		"use_weight_min_threshold": use_weight_min_threshold,
	}

	# Export single model
	result = None
	if not use_armature_pose:
		# print( "Not using armature pose so we export here" )
		result = save_model(
			export_operator,
			context,
			filepath,
			armature,
			objects,
			**kwargs
		)
	# Export pose models
	else:
		# Remember frame to set it back after export
		last_frame_current = context.scene.frame_current

		# Determine how to iterate over the frames
		if use_frame_start < use_frame_end:
			frame_order = 1
			frame_min = use_frame_start
			frame_max = use_frame_end
		else:
			frame_order = -1
			frame_min = use_frame_end
			frame_max = use_frame_start

		# String length of highest frame number for filename padding
		frame_strlen = len(str(frame_max))

		filepath_split = os.path.splitext( filepath )

		frame_range = range(
			use_frame_start, use_frame_end + frame_order, frame_order )
		for i_frame, frame in enumerate( frame_range, frame_min ):
			# Set frame for export - Don't do it directly to frame_current,
			#  as to_mesh() won't use updated frame!
			context.scene.frame_set( frame )

			# Generate filename including padded frame number
			vargs = ( filepath_split[ 0 ], frame_strlen,
					i_frame, filepath_split[ 1 ] )
			filepath_frame = "%s_%.*i%s" % vargs

			# Disable Armature for Pose animation export
			#  bone.tail_local not available for PoseBones
			result = save_model(
				export_operator,
				context,
				filepath_frame,
				armature,
				objects,
				**kwargs
			)

			# Abort on error
			if result is not None:
				context.scene.frame_set( last_frame_current )
				return result

		# Restore the frame the scene was at before we started exporting
		context.scene.frame_set( last_frame_current )


	# Restore mode to its previous state
	bpy.ops.object.mode_set( mode = last_mode, toggle = false )

	return result

tbl_cosmetics = [
	"j_teeth_lower", "j_teeth_upper", "j_tongue", "j_brow_a01", "j_brow_a01_le", "j_brow_a01_ri",
	"j_brow_a03_le", "j_brow_a03_ri", "j_brow_a05_le", "j_brow_a05_ri", "j_brow_a07_le",
	"j_brow_a07_ri", "j_brow_a09_le", "j_brow_a09_ri", "j_brow_b01_le", "j_brow_b01_ri",
	"j_cheek_a03_le", "j_cheek_a01_ri", "j_cheek_a01_le", "j_brow_b05_ri", "j_brow_b05_le",
	"j_brow_b03_ri", "j_brow_b03_le", "j_cheek_b03_ri", "j_cheek_b03_le", "j_cheek_b01_ri",
	"j_cheek_b01_le", "j_cheek_a07_ri", "j_cheek_a07_le", "j_cheek_a05_ri", "j_cheek_a05_le",
	"j_cheek_a03_ri", "j_cheek_c03_le", "j_cheek_c01_ri", "j_cheek_c01_le", "j_cheek_b09_ri",
	"j_cheek_b09_le", "j_cheek_b07_ri", "j_cheek_b07_le", "j_cheek_b05_ri", "j_cheek_b05_le",
	"j_chin_jaw", "j_chin_a03_ri", "j_chin_a03_le", "j_chin_a01_ri", "j_chin_a01_le", "j_chin_a01",
	"j_cheek_c05_ri", "j_cheek_c05_le", "j_cheek_c03_ri", "j_eye_a03_le", "j_eye_a01_ri",
	"j_eye_a01_le", "j_ear_b01_ri", "j_ear_b01_le", "j_ear_a03_ri", "j_ear_a03_le", "j_ear_a01_ri",
	"j_ear_a01_le", "j_eye_b01_ri", "j_eye_b01_le", "j_eye_a09_ri", "j_eye_a09_le", "j_eye_a07_ri",
	"j_eye_a07_le", "j_eye_a05_ri", "j_eye_a05_le", "j_eye_a03_ri", "j_eyelid_bot_05_le",
	"j_eyelid_bot_03_ri", "j_eyelid_bot_03_le", "j_eyelid_bot_01_ri", "j_eyelid_bot_01_le",
	"j_eye_b05_ri", "j_eye_b05_le", "j_eye_b03_ri", "j_eye_b03_le", "j_forehead_a01_le",
	"j_forehead_a01", "j_eyelid_top_07_ri", "j_eyelid_top_07_le", "j_eyelid_top_05_ri",
	"j_eyelid_top_05_le", "j_eyelid_top_03_ri", "j_eyelid_top_03_le", "j_eyelid_bot_05_ri",
	"j_forehead_b05_le", "j_forehead_b03_ri", "j_forehead_b03_le", "j_forehead_b01_ri",
	"j_forehead_b01_le", "j_forehead_b01", "j_forehead_a03_ri", "j_forehead_a03_le", "j_forehead_a01_ri",
	"j_jaw_a01_ri", "j_jaw_a01_le", "j_jaw_a01", "j_jaw", "j_forehead_b09_ri", "j_forehead_b09_le",
	"j_forehead_b07_ri", "j_forehead_b07_le", "j_forehead_b05_ri", "j_jaw_b01", "j_jaw_a09_ri",
	"j_jaw_a09_le", "j_jaw_a07_ri", "j_jaw_a07_le", "j_jaw_a05_ri", "j_jaw_a05_le", "j_jaw_a03_ri",
	"j_jaw_a03_le", "j_jaw_b09_le", "j_jaw_b07_ri", "j_jaw_b07_le", "j_jaw_b05_ri", "j_jaw_b05_le",
	"j_jaw_b03_ri", "j_jaw_b03_le", "j_jaw_b01_ri", "j_jaw_b01_le", "j_jaw_c07_le", "j_jaw_c05_ri",
	"j_jaw_c05_le", "j_jaw_c03_ri", "j_jaw_c03_le", "j_jaw_c01_ri", "j_jaw_c01_le", "j_jaw_c01",
	"j_jaw_b09_ri", "j_mouth_a07_le", "j_mouth_a05_ri", "j_mouth_a05_le", "j_mouth_a03_ri",
	"j_mouth_a03_le", "j_mouth_a01_ri", "j_mouth_a01_le", "j_mouth_a01", "j_jaw_c07_ri", "j_mouth_c01",
	"j_mouth_b03_ri", "j_mouth_b03_le", "j_mouth_b01_ri", "j_mouth_b01_le", "j_mouth_b01",
	"j_mouth_a09_ri", "j_mouth_a09_le", "j_mouth_a07_ri", "j_mouth_inner_le", "j_mouth_c07_ri",
	"j_mouth_c07_le", "j_mouth_c05_ri", "j_mouth_c05_le", "j_mouth_c03_ri", "j_mouth_c03_le",
	"j_mouth_c01_ri", "j_mouth_c01_le", "j_nose_a01_le", "j_nose_a01", "j_mouth_innerup_ri",
	"j_mouth_innerup_le", "j_mouth_innerup", "j_mouth_innerlow_ri", "j_mouth_innerlow_le", "j_mouth_innerlow",
	"j_mouth_inner_ri", "j_nose_c03_ri", "j_nose_c03_le", "j_nose_c01_ri", "j_nose_c01_le", "j_nose_c01",
	"j_nose_b01_ri", "j_nose_b01_le", "j_nose_b01", "j_nose_a01_ri", "j_uppercheek_a08_le",
	"j_uppercheek_a07_ri", "j_uppercheek_a07_le", "j_uppercheek_a05_ri", "j_uppercheek_a05_le",
	"j_uppercheek_a03_ri", "j_uppercheek_a03_le", "j_uppercheek_a01_ri", "j_uppercheek_a01_le",
	"j_uppercheek_a09_ri", "j_uppercheek_a09_le", "j_uppercheek_a08_ri"
]

def mark_cosmetic(bone, name):
	bone.cosmetic = name in tbl_cosmetics


def save_model(
		export_operator,
		context,
		filepath,
		armature,
		objects,
		target_format,
		version,
		global_scale,
		apply_modifiers,
		use_vertex_colors,
		use_vertex_colors_alpha,
		use_vertex_colors_alpha_mode,
		should_merge_by_distance,
		vert_merge_distance,
		use_armature,
		use_weight_min,
		use_weight_min_threshold
	):
	# Disabled
	use_armature_pose = false

	total_steps = ( objects.__len__() * 3 ) + 3
	current_step = 0
	scene = context.scene
	model = XModel.Model( "$pv_blender_cod_export" )

	meshes: list[ ExportMesh ] = []
	global_materials = []
	meshes_to_clean = []
	# prev_selected_objects = bpy.context.selected_objects
	# prev_active_object = bpy.context.view_layer.objects.active

	# Step 1
	# Get, setup and validate objects' meshes
	console.log( "Step 1 - Validate object meshes" )
	step_start_time = get_time()

	for obj in objects:
		current_step += 1
		# print( f"[ pv_blender_cod ] Exporting '{obj.name}'..." )
		# Set up modifiers whether to apply deformation or not
		mod_states = []
		for mod in obj.modifiers:
			mod_states.append( mod.show_viewport )
			if mod.type == 'ARMATURE':
				mod.show_viewport = ( mod.show_viewport
						 and use_armature_pose )
			else:
				mod.show_viewport = ( mod.show_viewport
						 and apply_modifiers )

		# Get mesh & apply modifiers

		try:
			# Get a copy of the mesh with modifiers applied
			depsgraph = context.evaluated_depsgraph_get()

			evaluated_obj = obj.evaluated_get( depsgraph )
			mesh = bpy.data.meshes.new_from_object(
                evaluated_obj,
				preserve_all_data_layers = true,
				depsgraph = depsgraph
            )
			meshes_to_clean.append( mesh )
		except RuntimeError as _e:
			shared.add_warning( f"RUNTIME ERROR getting object \"{ obj.name }\"'s mesh:\n{ _e }" )
			continue


		# Skip invalid meshes
		if len( mesh.vertices ) < 3:
			_skip_notice( obj.name, mesh.name, "Less than 3 vertices" )
			mesh.user_clear()
			bpy.data.meshes.remove( mesh )
			continue


		# === BMesh operations - Merge by distance & triangulation ===

		needs_triangulation = any( poly.vertices.__len__() > 3 for poly in mesh.polygons )
	
		if(	needs_triangulation
			or should_merge_by_distance
		):
			bm = bmesh.new()
			bm.from_mesh( mesh )

			if needs_triangulation:
				bmesh.ops.triangulate( bm, faces = list( bm.faces ) )
			
			if should_merge_by_distance:
				bmesh.ops.remove_doubles( bm, verts = bm.verts, dist = vert_merge_distance ) # type: ignore

			bm.to_mesh( mesh )
			bm.free()
		
			mesh.update()


		# Normal calculations are done automatically in Blender 4.1+
		if bpy.app.version < ( 4, 1, 0 ):
			mesh.calc_normals_split() # Taken out in 4.1 # type: ignore

		# Restore modifier settings
		for i, mod in enumerate( obj.modifiers ):
			mod.show_viewport = mod_states[ i ]
		
		# Check for materials that have not been assigned a name
		if any( _mtl is None for _mtl in mesh.materials ):
			shared.add_warning( f"Blank material found on mesh '{mesh.name}', object '{obj.name}'" )
			_skip_notice( obj.name, mesh.name, "Blank material found" )

			mesh.user_clear()
			bpy.data.meshes.remove( mesh )
			continue

		# print( "Appending obj '%s' to meshes with all its mtl info..." % obj.name )
		# print()
		# print( f"[ DEBUG ] MESH '{mesh.name}' HAS {mesh.materials.__len__()} MTL{'S' if mesh.materials.__len__() - 1 else ''}:" )
		# for _mtl in mesh.materials:
		# 	print( _mtl, ' | ', _mtl.name )
		# print()

		meshes.append( ExportMesh( obj, mesh, global_materials ) )

	console.log( "Finished in", console.timef( get_time() - step_start_time ) )

	# Step 2:
	# Build the bone hierarchy & transform matrices
	current_step += 1
	console.log( "Step 2 - Build bone hierarchy & transform matrices" )
	step_start_time = get_time()

	if use_armature and armature is not None:
		armature_matrix = armature.matrix_world
		bone_table = [ b.name for b in armature.data.bones ]
		for bone_index, bone in enumerate( armature.data.bones ):
			if bone.parent is not None:
				if bone.parent.name in bone_table:
					bone_parent_index = bone_table.index( bone.parent.name )
				else:
					# TODO: Add some sort of useful warning for when we try
					#  to export a bone that isn't actually in the bone table
					print( "WARNING - Bone", bone.parent.name, "is not in the bone table!" )
					bone_parent_index = 0
			else:
				bone_parent_index = -1

			model_bone = XModel.Bone( bone.name, bone_parent_index )
			mark_cosmetic( model_bone, bone.name )

			# Is this the way to go?
			#  Or will it fix the root only, but mess up all other roll angles?
			if bone_index == 0:
				matrix = [ (1, 0, 0), (0, 1, 0), (0, 0, 1) ]
				offset = (0, 0, 0)
			else:
				mtx = (
					armature_matrix @ bone.matrix_local
				).to_3x3().transposed()
				matrix = [ tuple( mtx[ 0 ] ), tuple( mtx[ 1 ] ), tuple( mtx[ 2 ] ) ]
				offset = ( armature_matrix @ bone.head_local ) * global_scale

			model_bone.offset = tuple( offset )
			model_bone.matrix = matrix
			model.bones.append( model_bone )
	else:
		# If there are no bones, or there is no armature
		#  create a dummy bone for tag_pos
		dummy_bone_name = "tag_origin"
		dummy_bone = XModel.Bone( dummy_bone_name, -1 )
		dummy_bone.offset = (0, 0, 0)
		dummy_bone.matrix = [ (1, 0, 0), (0, 1, 0), (0, 0, 1) ]
		model.bones.append( dummy_bone )
		bone_table = [ dummy_bone_name ]

	# Generate bone weights for verts
	if not use_weight_min:
		use_weight_min_threshold = 0.0
	
	console.log( "Finished in", console.timef( get_time() - step_start_time ) )

	# Step 3: Convert to PyCoD mesh
	console.log( "Step 3 - Convert to PyCoD mesh" )
	step_start_time = get_time()

	for mesh in meshes:
		current_step += 1

		mesh.add_weights( bone_table, use_weight_min_threshold )
		model.meshes.append(
			mesh.to_xmodel_mesh(
				use_vertex_colors,
				use_vertex_colors_alpha,
				use_vertex_colors_alpha_mode,
				global_scale
			) # type: ignore
		)

	console.log( "Finished in", console.timef( get_time() - step_start_time ) )


	# Step 4: Export materials
	current_step += 1
	console.log( "Step 4 - Export materials" )
	step_start_time = get_time()

	missing_count = 0
	for material in global_materials:
		# imgs = material_gen_image_dict(material)
		imgs = {} # material_gen_image_dict() just returns an empty dict anyway

		errored = false
		try:
			name = material.name
		except Exception as _e:
			name = "missing_mtl_" + str( missing_count )
			missing_count += 1
			errored = true

		if not errored:
			name = validate_str_for_ape( name )

		mtl = XModel.Material( name, "Lambert", imgs )
		model.materials.append( mtl )

	console.log( "Finished in", console.timef( get_time() - step_start_time ) )


	# Step 5:
	# Write to file
	current_step += 1
	console.log( "Step 5 - Write xmodel file" )
	step_start_time = get_time()
	
	header_msg = shared.get_metadata_string( filepath )

	if target_format == 'xmodel_bin':
		model.WriteFile_Bin(
			filepath, version=version,
			header_message=header_msg
		)
	else:
		model.WriteFile_Raw(
			filepath, version = version,
			header_message = f"// {header_msg}\n"
		)

	console.log( "Finished in", console.timef( get_time() - step_start_time ) )

	context.view_layer.update() # Do we need this?
	
	# Step 6:
	# Clean-up of temp meshes
	console.log( "Step 6 - Clean up temporary meshes" )
	step_start_time = get_time()
	
	for _mesh in meshes_to_clean:
		current_step += 1

		bpy.data.meshes.remove( _mesh )

	console.log( "Finished in", console.timef( get_time() - step_start_time ) )


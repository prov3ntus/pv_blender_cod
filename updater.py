


from typing import Union

from .pv_py_utils import console
from .pv_py_utils.stdlib import *
import webbrowser, bpy, requests, zipfile, shutil, os

from . import bl_info
from . import shared

LOCAL_VERSION = '.'.join( map( str, bl_info[ "version" ] ) )

LATEST_VER_URL = "https://github.com/w4133d/pv_blender_cod/releases/latest"
ADDON_NAME = "_pv_blender_cod"
BLENDER_ADDONS_PATH = bpy.utils.user_resource( 'SCRIPTS', path="addons" )
DOWNLOAD_URL = None
AUTO_UPDATE_PASSED = false # So we can hide the "Don't ask again" checkbox when checking for updates thru plugin preferences

NEW_VERSION = None
NEW_VER_DESC = None

# UpdateEnum
UPDATE_FAILED = -1
UPDATE_SUCCESS = 0
UPDATE_UPTODATE = 1
UPDATE_AVAILABLE = 2

def get_latest_version() -> Union[ Exception, str ]:
	"""Fetch latest version from GitHub releases"""

	global DOWNLOAD_URL
	global NEW_VER_DESC
	url = "https://api.github.com/repos/w4133d/pv_blender_cod/releases/latest"

	try:
		response = requests.get( url, timeout = 10 )
		response.raise_for_status()
		latest = response.json()

		DOWNLOAD_URL = latest[ "assets" ][ 0 ][ "browser_download_url" ]
		NEW_VER_DESC = latest[ "name" ]

		return latest[ "tag_name" ].strip( 'v' )
	except Exception as e:
		console.error( f"Failed to fetch latest version:\n{e}" )
		return e

def download_latest_zip( url, save_path ) -> bool:
	"""Download the latest plugin ZIP file"""
	try:
		response = requests.get( url, stream=true, timeout=15 )
		response.raise_for_status()
		with open( save_path, "wb" ) as file:
			for chunk in response.iter_content( chunk_size=8192 ):
				file.write( chunk )

		return true
	except Exception as e:
		print( f"[ pv_blender_cod ] Download failed: {e}" )

		return false

def install_update( zip_path ):
	"""Extract the downloaded ZIP and replace the current addon"""
	try:
		temp_extract_path = os.path.join( BLENDER_ADDONS_PATH, "_update_temp" )
		if os.path.exists( temp_extract_path ):
			shutil.rmtree( temp_extract_path) 

		with zipfile.ZipFile( zip_path, "r" ) as zip_ref:
			zip_ref.extractall( temp_extract_path )

		addon_path = os.path.join( BLENDER_ADDONS_PATH, ADDON_NAME )
		if os.path.exists( addon_path ):
			shutil.rmtree( addon_path ) # Remove old version

		shutil.move( os.path.join( temp_extract_path, ADDON_NAME ), addon_path )
		shutil.rmtree( temp_extract_path ) # Cleanup temp

		print("[ pv_bl_cod Updater ] Update installed successfully.")

		return true
	except Exception as e:
		print( f"[ pv_bl_cod Updater ] Update installation failed: {e}" )

		return false

def check_for_update() -> Union[ Exception, int ]:
	"""
	Check if a newer version is available and update if necessary
	
	:returns `UpdateEnum`: An update enum.

	.. UpdateEnum: ::
	`UPDATE_FAILED` = `-1`\n
	`UPDATE_SUCCESS` = `0`\n
	`UPDATE_UPTODATE` = `1`\n
	`UPDATE_AVAILABLE` = `2`
	"""
	global NEW_VERSION
	
	start = get_time()
	latest_version = get_latest_version()
	console.log(
		console.bold( f"Took {console.timef( get_time() - start )} to grab latest version from GitHub." ),
		color = console.bcolors.OKGREEN
	)
	

	if isinstance( latest_version, Exception ):
		return latest_version # Return exception
	
	if latest_version > LOCAL_VERSION:
		print( f"[ pv_blender_cod ] New version available: {latest_version}. Current version: {LOCAL_VERSION}." )
		NEW_VERSION = latest_version
		return UPDATE_AVAILABLE
	else:
		return UPDATE_UPTODATE

def update():
	"""Make sure to run updater.check_for_updates() first"""
	zip_path = os.path.join( BLENDER_ADDONS_PATH, "_pv_blender_cod.zip" )
	print( "DOWNLOAD URL:", DOWNLOAD_URL )
	if download_latest_zip( DOWNLOAD_URL, zip_path ):
		if install_update( zip_path ):
			os.remove( zip_path )
			print( "Update complete. Restarting addon..." )
			restart_addon()
			return UPDATE_SUCCESS

def restart_addon():
	"""Disables and re-enables the addon to apply updates"""
	bpy.ops.preferences.addon_disable( module = ADDON_NAME )
	bpy.ops.preferences.addon_enable( module = ADDON_NAME )
	print("pv_blender_cod restarted successfully.")

def delayed_update_prompt():
	if bpy.context.window_manager: # Making sure here that UI is ready
		bpy.ops.wm.confirm_update( 'INVOKE_DEFAULT' )
		return None # Stops timer loop (doesn't retry)
	
	return .5 # Retry after .5 seconds if UI isn't ready


class UpdateOperator( bpy.types.Operator ):
	"""Update Addon"""
	bl_idname = "wm.update_addon"
	bl_label = "Update pv_blender_cod"

	def execute(self, context):
		if gvar.is_updating:
			return
		
		gvar.is_updating = true

		print( "[ pv_blender_cod ] Checking for updates..." )
		updated = check_for_update()

		if updated is Exception:
			self.report( {'ERROR'}, f"BlenderCoD update failed: {updated}. - pv" )
		elif updated == UPDATE_AVAILABLE:
			bpy.ops.wm.confirm_update( 'INVOKE_DEFAULT' )
		elif updated == UPDATE_UPTODATE:
			self.report( {'INFO'}, f"BlenderCoD is up-to-date: v{LOCAL_VERSION} - pv" )

		# self.report( {'INFO'}, f"BlenderCoD updated successfully (v{LOCAL_VERSION}). - pv" )

		gvar.is_updating = false

		return {'FINISHED'}


class ViewFullChangelogOnGithubOperator( bpy.types.Operator ):
	bl_idname = "wm.view_full_gh_changelog_dialog"
	bl_label = "View Full Changelog (github.com)"
	bl_description = "Open the latest release page on GitHub " \
	"of pv_blender_cod for more information on this update."
	
	def execute( self, context ):
		webbrowser.open( LATEST_VER_URL )
		
		return { 'FINISHED' }


class ConfirmUpdateOperator(bpy.types.Operator):
	bl_idname = "wm.confirm_update"
	bl_label = "Addon Update Available:"

	dont_ask_again: bpy.props.BoolProperty(
		name="Don't Ask Again",
		description="BlenderCoD will no longer ask you to update on start-up."
		"You can re-enable this in Preferences > Addons > pv_blender_cod > Auto-update When Blender Starts",
		default=false
	) # type: ignore


	def execute( self, context ):
		shared.plugin_preferences.auto_update_enabled = not self.dont_ask_again

		self.report( { 'INFO' }, "Updating BlenderCoD..." )
		update()
		
		global AUTO_UPDATE_PASSED
		
		AUTO_UPDATE_PASSED = true

		return {'FINISHED'}


	def invoke(self, context, event):
		return context.window_manager.invoke_props_dialog( self, width = 600 )


	def cancel( self, context ):
		global AUTO_UPDATE_PASSED
		
		AUTO_UPDATE_PASSED = true

		shared.plugin_preferences.auto_update_enabled = not self.dont_ask_again

		return None

	def draw( self, context ):

		layout = self.layout
		# layout.scale_y = 1.2

		layout.label(
			text = "BlenderCoD Update - pv",
			icon = 'INFO'
		)
		layout.label(
			text = f"An update is available! Current: v{LOCAL_VERSION}. New: v{NEW_VERSION}.",
		)
		if NEW_VER_DESC is not None:
			layout.label(
				text = f"{NEW_VER_DESC}"
			)
		layout.label(
			text = "You can always check for updates in Preferences > Addons. Would you like to update now?",
		)

		global AUTO_UPDATE_PASSED

		if shared.plugin_preferences.auto_update_enabled and not AUTO_UPDATE_PASSED:
			# Checkbox inside dialog
			layout.prop( self, "dont_ask_again" )

			layout.separator()

		layout.operator(
			"wm.view_full_gh_changelog_dialog",
			text = "View Full Changelog (github.com)",
			icon = "URL"
		)


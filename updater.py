


LOCAL_VERSION = "0.8.5"



import bpy, requests, zipfile, shutil, os
from . import shared

GITHUB_REPO = "w4133d/pv_blender_cod"
ADDON_NAME = "_pv_blender_cod"
BLENDER_ADDONS_PATH = bpy.utils.user_resource('SCRIPTS', path="addons")
DOWNLOAD_URL = None

UPDATE_FAILED = -1
UPDATE_SUCCESS = 0
UPDATE_UPTODATE = 1
UPDATE_AVAILABLE = 2

NEW_VERSION = None

update_dialog = None

def get_latest_version():
	"""Fetch latest version from GitHub releases"""

	global DOWNLOAD_URL
	url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
	try:
		response = requests.get(url, timeout=10)
		response.raise_for_status()
		latest = response.json()
		DOWNLOAD_URL = latest["assets"][0]["browser_download_url"]
		return latest["tag_name"].strip( 'v' )
	except Exception as e:
		print(f"[ pv_bl_cod Updater ] Failed to fetch latest version: {e}")
		return e

def download_latest_zip(url, save_path):
	"""Download the latest plugin ZIP file"""
	try:
		response = requests.get(url, stream=True, timeout=15)
		response.raise_for_status()
		with open(save_path, "wb") as file:
			for chunk in response.iter_content(chunk_size=8192):
				file.write(chunk)

		return True
	except Exception as e:
		print( f"[ pv_blender_cod ] Download failed: {e}" )

		return False

def install_update(zip_path):
	"""Extract the downloaded ZIP and replace the current addon"""
	try:
		temp_extract_path = os.path.join(BLENDER_ADDONS_PATH, "_update_temp")
		if os.path.exists(temp_extract_path):
			shutil.rmtree(temp_extract_path)

		with zipfile.ZipFile(zip_path, "r") as zip_ref:
			zip_ref.extractall(temp_extract_path)

		addon_path = os.path.join(BLENDER_ADDONS_PATH, ADDON_NAME)
		if os.path.exists(addon_path):
			shutil.rmtree(addon_path) # Remove old version

		shutil.move(os.path.join(temp_extract_path, ADDON_NAME), addon_path)
		shutil.rmtree(temp_extract_path) # Cleanup temp

		print("[ pv_bl_cod Updater ] Update installed successfully.")

		return True
	except Exception as e:
		print(f"[ pv_bl_cod Updater ] Update installation failed: {e}")

		return False

def check_for_update():
	"""Check if a newer version is available and update if necessary"""
	global NEW_VERSION
	
	latest_version = get_latest_version()

	if latest_version is Exception:
		return latest_version # Return exception

	if latest_version > LOCAL_VERSION:
		print(f"[ pv_blender_cod ] New version available: {latest_version}. Current version: {LOCAL_VERSION}.")
		NEW_VERSION = latest_version
		return UPDATE_AVAILABLE
	else:
		return UPDATE_UPTODATE

def update():
	"""Make sure to run updater.check_for_updates() first"""
	zip_path = os.path.join(BLENDER_ADDONS_PATH, "_pv_blender_cod.zip")
	print( "DOWNLOAD URL:", DOWNLOAD_URL )
	if download_latest_zip(DOWNLOAD_URL, zip_path):
		if install_update(zip_path):
			os.remove(zip_path)
			print("Update complete. Restarting addon...")
			restart_addon()
			return UPDATE_SUCCESS

def restart_addon():
	"""Disables and re-enables the addon to apply updates"""
	bpy.ops.preferences.addon_disable(module=ADDON_NAME)
	bpy.ops.preferences.addon_enable(module=ADDON_NAME)
	print("pv_blender_cod restarted successfully.")

def delayed_update_prompt():
	if bpy.context.window_manager: # Ensure UI is ready
		bpy.ops.wm.confirm_update( 'INVOKE_DEFAULT' )
		return None # Stop timer
	
	return 1.5 # Retry after 1.5 seconds if UI isn't ready


class UpdateOperator(bpy.types.Operator):
	"""Update Addon"""
	bl_idname = "wm.update_addon"
	bl_label = "Update pv_blender_cod"

	def execute(self, context):
		print( "[ pv_blender_cod ] Checking for updates..." )
		updated = check_for_update()

		if updated is Exception:
			self.report( {'ERROR'}, f"BlenderCoD update failed: {updated}. - pv" )
		elif updated == UPDATE_AVAILABLE:
			bpy.ops.wm.confirm_update( 'INVOKE_DEFAULT' )
		elif updated == UPDATE_UPTODATE:
			self.report( {'INFO'}, f"BlenderCoD is up-to-date. (v{LOCAL_VERSION}) - pv" )

		# self.report( {'INFO'}, f"BlenderCoD updated successfully (v{LOCAL_VERSION}). - pv" )

		return {'FINISHED'}


class SimpleDialogConfirmOperator( bpy.types.Operator ):
	bl_idname = "wm.simple_dialog_confirm"
	bl_label = "Confirm"
	bl_description = "Click me if you're cool :)"

	def execute(self, context):
		print( "SimpleDialogConfirmOperator execute()" )

		global update_dialog
		if update_dialog: update_dialog.__apply_dont_ask_again__()

		self.report( { 'INFO' }, "Updating BlenderCoD..." )
		update()
		
		return { 'FINISHED' }

class CancelDialogOperator(bpy.types.Operator):
	bl_idname = "wm.cancel_dialog"
	bl_label = "Cancel"
	bl_description = "Why TF would you cancel bitch, like " \
	"I did not just spend a whole day and a half straight of my life " \
	"to make this whole damn auto-updater just so you " \
	"can sit there and fucking NOT USE IT BRUH LIKE PRESS YES, WTF!?"
	
	def execute(self, context):
		print( "Cancel dialog operator execute()" )

		global update_dialog
		if update_dialog: update_dialog.__apply_dont_ask_again__()

		# Damn... well fuck you, then.
		bpy.ops.wm.cancel_response( 'INVOKE_DEFAULT' )

		# return {'CANCELLED'} # This will run self.cancel()
		return { 'FINISHED' }

class ConfirmUpdateOperator(bpy.types.Operator):
	bl_idname = "wm.confirm_update"
	bl_label = "pv_blender_cod update"

	dont_ask_again: bpy.props.BoolProperty(
		name="Don't Ask Again",
		description="BlenderCoD will no longer ask you to update on start-up."
		"You can re-enable this in Preferences > Addons > pv_blender_cod > Auto-update When Blender Starts",
		default=False
	) # type: ignore

	def execute( self, context ):
		print( "Confirm update operator execute()" )
		# Store the preference to skip confirmation
		shared.plugin_preferences.dont_ask_again = self.dont_ask_again

		if shared.plugin_preferences.dont_ask_again:
			shared.plugin_preferences.auto_update_enabled = False
			self.report( { 'INFO' }, "BlenderCoD auto-updates disabled. - pv" )
			return { 'FINISHED' }

		if check_for_update() == UPDATE_AVAILABLE:
			self.report( { 'INFO' }, "Updating BlenderCoD..." )
			update()
		
		return {'FINISHED'}

	def invoke(self, context, event):
		global update_dialog
		# Store a reference to self so we can call __apply_dont_ask_again__()
		update_dialog = self
		return context.window_manager.invoke_popup( self, width = 400 )

	def cancel( self, context ):
		print( "Confirm update operator cancel()" )
		# We don't want to save the preference here if their mouse moves
		# away from the dialog and it cancels
		""" 	
		# Store the preference to skip confirmation
		shared.plugin_preferences.dont_ask_again = self.dont_ask_again

		if shared.plugin_preferences.dont_ask_again:
			shared.plugin_preferences.auto_update_enabled = False
			self.report({'INFO'}, "BlenderCoD auto-updates disabled. - pv")
		"""
		return None

	def __apply_dont_ask_again__( self ):
		# Store the preference to skip confirmation
		shared.plugin_preferences.dont_ask_again = self.dont_ask_again

		if self.dont_ask_again:
			shared.plugin_preferences.auto_update_enabled = False
			self.report({'INFO'}, "BlenderCoD auto-updates disabled. - pv")


	def draw( self, context ):
		layout = self.layout
		layout.scale_y = 1.2

		layout.label(
			text = "BlenderCoD Update - pv",
			icon = 'INFO'
		)
		layout.label(
			text = f"An update is available: Current: v{LOCAL_VERSION}. New: v{NEW_VERSION}.",
		)
		layout.label(
			text = "Would you like to update now?",
		)
		layout.label(
			text = "You can always check for BlenderCoD updates in Preferences > Addons.",
		)
		
		# Checkbox inside dialog
		layout.prop( self, "dont_ask_again" )

		layout.separator()

		vbox = layout.row()
		vbox.operator(
			"wm.simple_dialog_confirm", text = "Yes",
		)
		vbox.operator(
			"wm.cancel_dialog", text = "No",
		)

class ISeeHowItIsOperator( bpy.types.Operator ):
	bl_idname = "wm.cancel_response"
	bl_label = "Wow..."

	def execute( self, context ):
		return { 'FINISHED' }

	def invoke(self, context, event):
		return context.window_manager.invoke_props_dialog( self, width = 350 )

	def draw( self, context ):
		layout = self.layout

		layout.label(
			text = "Damn... well fuck you, then. I see how it is."
		)
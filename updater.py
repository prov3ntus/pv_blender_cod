import bpy, requests, zipfile, shutil, os
from . import shared

GITHUB_REPO = "w4133d/pv_blender_cod"
ADDON_NAME = "pv_blender_cod"
LOCAL_VERSION = "0.8.4"
BLENDER_ADDONS_PATH = bpy.utils.user_resource('SCRIPTS', path="addons")

def get_latest_version():
	"""Fetch latest version from GitHub releases"""
	url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
	try:
		response = requests.get(url, timeout=10)
		response.raise_for_status()
		latest = response.json()
		return latest["tag_name"].strip( 'v' ), latest["assets"][0]["browser_download_url"]
	except Exception as e:
		print(f"[ pv_bl_cod Updater ] Failed to fetch latest version: {e}")
		return None, None

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
		print(f"[ pv_bl_cod Updater ] Download failed: {e}")

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

UPDATE_FAILED = -1
UPDATE_SUCCESS = 0
UPDATE_UPTODATE = 1

def check_for_update():
	"""Check if a newer version is available and update if necessary"""
	latest_version, download_url = get_latest_version()

	if latest_version is None:
		print("[ pv_bl_cod Updater ] Could not check for updates.")
		return UPDATE_FAILED

	if latest_version > LOCAL_VERSION:
		print(f"[ pv_bl_cod Updater ] New version available: {latest_version}. Current version: {LOCAL_VERSION}. Updating...")
		zip_path = os.path.join(BLENDER_ADDONS_PATH, "update.zip")

		if download_latest_zip(download_url, zip_path):
			if install_update(zip_path):
				os.remove(zip_path)
				print("Update complete. Restarting addon...")
				restart_addon()
				return UPDATE_SUCCESS
	else:
		print( "[ pv_bl_cod Updater ] pv_blender_cod is up to date." )
	
	return UPDATE_UPTODATE

def restart_addon():
	"""Disables and re-enables the addon to apply updates"""
	bpy.ops.preferences.addon_disable(module=ADDON_NAME)
	bpy.ops.preferences.addon_enable(module=ADDON_NAME)
	print("Addon restarted successfully.")

class UpdateOperator(bpy.types.Operator):
	"""Update Addon"""
	bl_idname = "wm.update_addon"
	bl_label = "Update pv_blender_cod"

	def execute(self, context):
		if shared.plugin_preferences.auto_update_enabled:
			updated = check_for_update()

			if updated == UPDATE_FAILED:
				self.report( {'ERROR'}, "pv_blender_cod update failed." )
			elif updated == UPDATE_SUCCESS:
				self.report( {'INFO'}, f"pv_blender_cod updated successfully (v{LOCAL_VERSION})." )
			elif updated == UPDATE_UPTODATE:
				self.report( {'INFO'}, f"pv_blender_cod is up-to-date. (v{LOCAL_VERSION})" )

		return {'FINISHED'}


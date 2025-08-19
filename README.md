# pv_blender_cod

A Blender (3.X to 4.X) plugin for importing/exporting XModels and XAnims for Call of Duty.

The addon in blender is called "pv_blender_cod" in the addons window.

Make sure you _**UNCHECK**_ any other Blender COD addon, as they will conflict!

It's a continuation of the [BetterBetterBlenderCOD](https://github.com/shiversoftdev/BetterBetterBlenderCOD) addon previously maintained by Serious.

## Install Instructions

1. Go to [releases](https://github.com/w4133d/pv_blender_cod/releases/latest/) and download `_pv_blender_cod.zip`. **You don't extract it!**

2. In Blender, in the top left go to `Edit > Preferences > Add-ons` & click "Install" (or "Install from Disk"), then browse to where you saved `_pv_blender_cod.zip` and install it.
You can delete the `_pv_blender_cod.zip` afterwards if you like.

3. Check the checkbox to enable the plugin.

![image](https://github.com/user-attachments/assets/a31e249c-231d-4374-8ec1-2e8a5d173849)


## New Features

Here is a definitive list of features / fixes I've made to the plugin:

### Material Name Cleaner
Sanitises any material names. Upon export, any invalid characters are replaced with underscores, and the material name is lower-cased.

It's baffling that this wasn't added by any of the previous maintainers, tbh. This plugin was never really shown any love.


### Exporting Multiple Objects Fix
Using the "Export Selection" option when exporting XModels now **fully works** with no issues. You can also export all meshes in the scene, and it works fine.
You no longer have to join the mesh before exporting.


### Blender 4.X Bug Fixes
The plugin actually works in 4.X now 💀

Exporting XModels now apply modifiers. Custom weighted/split normals are preserved.
Only auto-triangulates if necessary upon export, as export triangulation was discarding some data (it no longer does this anyway anymore).


### Auto-updating
When a new update is released, you'll be notified about it when Blender opens. Updates will be checked for on startup, and you'll be prompted if there's an update available.
You can turn off auto-update checks in the plugin's settings.


### Nicer Warnings
Like CoDMayaTools, you are notified if any warnings occured during an operation.
The **first five** are shown on the pop-up.

For more info about the warnings, open the console in Blender by going to the top left, click **Window --> Toggle System Console**.

There will be descriptions of any warnings that occured. Only 5 show in the pop-up, but they all show in console. 
You should copy the output of the console and include it when creating an issue.


### Vertex Color Fixes
Fully preserves any vertex colours when importing / exporting XModels _(including alpha for material blending)_

Note: Painting alpha vertex colours isn't possible in Blender 3.X. You'd wanna use a plugin for it instead, specifically an old version of VertexColorPlus that you can download [here](https://github.com/oRazeD/VertexColorsPlus/archive/6e4a9fb18e88449487fe1cd631e5c8ec2f7fbaa4.zip).

For Blender 4.X, Blender supports alpha blending, but it's kinda hidden away (see below).

![image](https://github.com/user-attachments/assets/a9be7b96-5df4-4027-ab8e-a52b3bb70fa9)

Therefore, you won't need VertexColorsPlus for Blender 4.X (the plugin doesn't even work properly in 4.X anyway lmao).


## Known Issues / Current To-do List

There are some things I still need to add to / fix with the plugin; they're all detailed here, in order of highest to least priority:

- Look into XAnim importing & exporting and fix issues left by previous maintainers (and hence add 4.0+ support).
- Drag n' drop support for importing XModel/XAnims

---

The aim for this plugin is to support all versions of Blender (3.X AND 4.X).

As aforementioned above, I haven't gotten around to fixing XAnims yet so please be patient until I do.

Other than that, please **let me know if you encounter a problem** by opening an issue [here](https://github.com/w4133d/pv_blender_cod/issues/new/choose), and I'll fix it **as soon as I can**!

## Credits:

### All previous maintainers
[shiversoftdev](https://github.com/shiversoftdev)
[Ma_rv](https://github.com/marv7000/)
[CoDEManX](https://github.com/CoDEmanX)
Flybyny (couldn't find a GH profile)
[SE2Dev](https://github.com/SE2Dev).

### Special Thx:

VerK0 - Feature ideas / suggestions / fixes(being sexy)

Kurunvro - Tester

### Dependancies:

This plugin uses the [Python LZ4](https://pypi.org/project/lz4/) library.

ye

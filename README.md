# pv_blender_cod

A Blender (3.0+ to 4.0+) plugin for importing/exporting XModels and XAnims for Call of Duty.

The addon in blender is called "pv_blender_cod" in the addons window.

Make sure you _**UNCHECK**_ any other Blender COD addon, as they will conflict!

It's a continuation of the [BetterBetterBlenderCOD](https://github.com/shiversoftdev/BetterBetterBlenderCOD) addon previously maintained by Serious.

## New Features

Here is a definitive list of features / fixes I've made to the plugin:

### Cleans Material Names
Upon export, any invalid characters are replaced with underscores, and the material name is lower-cased.

It's baffling that this wasn't added by any of the previous maintainers, tbh.

### Exporting Multiple Objects Fix
Using the "Export Selection" option when exporting XModels now **fully works** with no issues. You can also export all meshes in the scene, and it works fine.
You no longer have to join the mesh before exporting.

### Blender 4.0+ Bug Fixes
Exporting XModels now apply modifiers. Custom weighted/split normals are preserved.
Only auto-triangulates if necessary upon export, as export triangulation was discarding some data (it no longer does this anyway anymore).

### Auto-updating
When a new update is released, you'll be notified about it in Blender. Updates will be checked for on startup, and you'll be prompted if there's an update available.

### Nicer Warnings
Like CoDMayaTools, you are notified if any warnings occured during an operation.
The **first five** are shown on the pop-up.

For more information about the (and to check out the errors that weren't shown if there are more than 5), open the console window by going in Blender to the top left, then click **Window --> Toggle System Console**.
There will be descriptions of any warnings, and overflow warnings (when there are more than 5 warnings in one export).

### Vertex Color Fixes
Preserves vertex colours when importing / exporting XModels. Also supports custom vertex color plugins, and can export the data from them.
You'd wanna use a plugin when exporting alpha vertex colors for blending, specifically [VertexColorPlus](https://github.com/oRazeD/VertexColorsPlus/). 

Alpha vertex colours are not otherwise possible to export in Blender (at least in 3.0).

If a vertex layer exists from a plugin, pv_blender_cod will use that instead when exporting.

---

The aim for this plugin is to support all versions from Blender 3.0+, **_including_** Blender 4.0+. I haven't gotten around to fixing XAnim support yet so please be patient until I do.

Other than that, please **let me know if you encounter a problem** by opening an issue here, and I'll fix it **as soon as I can**!

Credits are due to all previous maintainers: [shiversoftdev](https://github.com/shiversoftdev), [Ma_rv](https://github.com/marv7000/), [CoDEManX](https://github.com/CoDEmanX), Flybynyt & [SE2Dev](https://github.com/SE2Dev).

ye

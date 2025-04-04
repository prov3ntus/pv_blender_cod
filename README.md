# pv_blender_cod

A Blender (3.0+) plugin for importing/exporting XModels and XAnims

Make sure you _**UNCHECK**_ any other Blender COD addon, as they will conflict!

The addon in blender is called "pv_blender_cod" in the addons window.

It's a continuation of the [BetterBetterBlenderCOD](https://github.com/shiversoftdev/BetterBetterBlenderCOD) addon made by Serious.

Forked this originally for [Xela](https://x.com/MrXeIa), so he could export alpha vertex colours for Blender 3.0.

Alpha vertex colours were not possible to export in blender before (at least in 3.0).

My fork of BlenderCoD allows for compatibility with any vertex colour plugin
(specifically [VertexColorPlus](https://github.com/oRazeD/VertexColorsPlus/)),
which applies vertex colour sets and supports an alpha channel.
If that colour set exists, pv_blender_cod will use that one instead when exporting.

The plugin we used to add alpha vertex colours was a 3 year old version of
[VertexColorPlus](https://github.com/oRazeD/VertexColorsPlus/) that supported Blender 3.0 still.
The direct download to the source of the version that supports Blender 3.0 is
[here](https://github.com/oRazeD/VertexColorsPlus/archive/f94f5e781cff0488e1fdfdfcbff5a714989be146.zip) if anyone wants it.

It also fixes exporting separate meshes, and hence the "Export selected only" checkbox, when exporting an xmodel.

The most stable and supported version of Blender to use pv_blender_cod with is Blender 3.0.0. 
However other versions are supported. This plugin is supposed to support all versions of Blender 3.0+!
Please let me know if you run into any issues, I'll fix them ASAP for you.

Bear in mind, while I iron out the kinks for other Blender verisons,
you can always install [Blender 3.0.0](https://download.blender.org/release/Blender3.0/),
regardless of the current version of Blender you have installed.
Blender supports having multiple versions installed at once. A list of
downloads to all blender versions can be found [here](https://download.blender.org/release/).
Install the .msi option, it's the easiest one, and all your Blender installtions will be in
the same place.

The aim is to support all versions from Blender 3.0.0+. I've not teseted any other features
other than the xmodel exporter, so if you encounter any issues (and you  probably will!), please let me know 
either on discord (@prov3ntus or join the [DEVRAW discord](https://discord.gg/yMGJBCBJUV)) or open an issue here, and I'll fix it as soon as I can!

Stolen from Serious & Marv, adds support for cosmetic bones and auto-normalizes bones with too many weights. 

ye

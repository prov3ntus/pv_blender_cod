# pv_blender_cod

A Blender (3.0+) plugin for importing/exporting XModels and XAnims

Make sure you _**UNCHECK**_ any other Blender COD addon, as they will conflict!

The addon in blender is called "pv_blender_cod" in the addons window.

It's a continuation of the [BetterBetterBlenderCOD](https://github.com/shiversoftdev/BetterBetterBlenderCOD) addon made by Serious.
Some features, like exporting normals correctly, might not work for Blender 4.1 or higher. I'm working on it. Thank Blender for changing 
their API and not giving alternatives to deprecated functions.

:\

Forked this originally for Xela, so he could export alpha vertex colours for Blender 3.0.

Alpha vertex colours are hard to add in Blender. Xela was using Blender 3.0. As of now, the only thing my fork does differently from Serious' is 
it applies a vertex colour set that's been placed by a plugin if it exists, and uses that one instead when exporting.

The plugin we used to add alpha vtx colours was a 3 year old version of
[VertexColorPlus](https://github.com/oRazeD/VertexColorsPlus/) that supported Blender 3.0 still.
The direct download to the source of the version that supports Blender 3.0 is
[here](https://github.com/oRazeD/VertexColorsPlus/archive/f94f5e781cff0488e1fdfdfcbff5a714989be146.zip) if anyone wants it.

Stolen from Serious & Marv, adds support for cosmetic bones and auto-normalizes bones with too many weights

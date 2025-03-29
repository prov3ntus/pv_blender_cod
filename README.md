# pv_blender_cod

A Blender (3.0+) plugin for importing/exporting XModels and XAnims

It's a continuation of the [BetterBetterBlenderCOD](https://github.com/shiversoftdev/BetterBetterBlenderCOD) addon made by Serious.
Might not work for Blender 4.0 or higher. If support is wanted for this, or anything else, I'll add it.

Forked this originally for Xela, so he could export alpha vertex colours for Blender 3.0.

Alpha vertex colour support was only added to Blender 3.4 and higher. Xela was using Blender 3.0. As of now, the only thing my fork does differently from Serious' is 
it applies a vertex colour set that's been placed by a plugin if it exists, and uses that one instead when exporting.
Literally 3 lines of code I added to do so. 

The plugin we used to add alpha vtx colours was a 3 year old version of [VertexColorPlus](https://github.com/oRazeD/VertexColorsPlus/tree/f94f5e781cff0488e1fdfdfcbff5a714989be146)
that supported Blender 3.0 still. The direct download to the source of this version is [here](https://github.com/oRazeD/VertexColorsPlus/archive/f94f5e781cff0488e1fdfdfcbff5a714989be146.zip)
if anyone wants it.

Stolen from Serious & Marv, adds support for cosmetic bones and auto-normalizes bones with too many weights

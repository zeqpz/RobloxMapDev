# Westgate infill (buildings between the existing roads)

Roads are the live `Workspace.Map.Roads_v8` set in the Alamo County place (built in another session). The blocks were
read straight from those meshes (EditableMesh triangles rasterised at 4 studs): `road_grid.rle` ->
`python tools/westgate_blocks.py` -> `blocks.json` + `blocks.png` (13 lots, WG01..WG13, Roblox X/Z).

| Block | Size (studs) | Status |
|---|---|---|
| WG01 | 316 x 372 (X 1052..1368, Z -824..-452) | built: Sunset Plaza strip centre, Top Dog stand, El Sol taqueria, Desert Rose Motor Lodge, alley |
| WG02 | 312 x 528 | next |
| WG03 | 316 x 112 | |
| WG04 | 316 x 344 | |
| WG05-WG13 | see blocks.json (WG05/06/09/10/12/13 wrap the two loop streets) | |

The blocks east of x 1740 run past the survey edge and are not in blocks.json yet.

## How a block is built (owner order)
`blender/blocks/wgNN.py` with `bkit.py` (geometry, materials) + `bprops.py` (trim parts and props):
1. **M massing**: lots, alley, slabs, walls with real openings, roofs, glass, doors, stairs.
2. **T trim**: frames, sills, door hoods, bands, copings, fascia, standing seams, railings, stripes, wheel stops.
3. **C character**: signs (fictional), painted lettering, graffiti, drips, oil stains, cracks, rooftop units,
   swamp coolers, dishes, meters, poles + wires, dumpsters, plants, furniture, clutter.

Run in Blender: `WG_PASSES = "MTC"; WG_RENDER = ["overview", ...]; exec(open(r"...\blender\blocks\wg01.py").read())`.
Renders: `renders/westgate/wg01/<passes>_<shot>.png`. Exports: `exports/westgate/wg01/WG01_<Building>.fbx`
(+ `.fbm` texture folders). Object names `WG01_<Building>_<Pass>__<RobloxMaterial>_<HEX>`; `Sign_` / `Decal_`
objects carry an image from `textures/buildings/`.

## Install notes (WG01)
- Terrain inside the block ranges Y -0.3..3.8: flatten to Y 2 under the lot before importing (lot top is Y 2.8).
- The drained pool basin goes down to Y -3: carve terrain (air) in X 1172..1214, Z -598..-562.
- 3D Importer: Scale Unit Stud, Insert Using Scene Position ON (meshes are at world coordinates).
- Driveway aprons sit in the street gutters at the curb cuts (arterial, east street, south street).

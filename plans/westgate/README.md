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
(+ `.fbm` texture folders). Object names `WG01_<Building>.<Piece>__<RobloxMaterial>_<HEX>`; `Sign_` / `Decal_`
objects carry an image from `textures/buildings/`.

## Quality check (every build)
`WG_QA = True` runs `blender/bqa.py` on the oriented box of every solid primitive:
- **clash**: two different parts interpenetrating more than 0.04 studs (SAT depth); lots/slabs are "ground" and exempt
- **floating**: a part touching nothing (no other part, no ground) within 0.06 studs
- **loose**: a sign face or decal with nothing solid right behind it
Report: `plans/westgate/qa_wg01.txt`. WG01 status 2026-11-24: **0 clashes, 0 floating, 0 loose** (from ~140 problems
on the first run: plants through signs, roofs through walls, porch rafters through the tile roof, coolers through roofs,
sconces in window trim, conduit across bands, stair stringers in landings, mansard sunk into the front wall, ...).

## Doors + windows
Prototypes in `blender/bparts.py` (built once, placed many times):
- doors: frame + stops + threshold + optional casing; leaf 4.6 x 7.4 x 0.5 (flush steel / glass lite / panel / pair);
  lever + rose, deadbolt, peephole, kick plate, exposed hinges + closer on out-swing service doors
- storefront pair: wide stiles, mid rail, pull handles, lock cylinder, transom, PUSH + hours stickers
- windows: slider (2 sashes, meeting stiles, latch, pull, screen), fixed / casement (muntin grid), awning (obscure glass,
  hinged sash); recessed glass, sloped sill + drip, optional surround, interior blinds or curtains

## Chopped export
`exec(bexport.py)` with `BX_BLOCK = "WG01"` -> `exports/westgate/wg01/`:
`WG01_<Building>.fbx` (one object per piece x material), `WG01_Protos.fbx` (28 prototypes at the origin),
`WG01_Placements.lua` (181 door/window placements in Roblox coordinates), `manifest.json`.

## Install (WG01)
1. Run `studio/westgate/PrepTerrain_WG01.lua` (flattens terrain under the lot to Y 2 and carves the pool; one undo step).
2. 3D Importer (Scale Unit Stud, Insert Using Scene Position ON): the 5 building FBX + `WG01_Protos.fbx`.
3. Put `WG01_Placements.lua` into a ModuleScript `ServerStorage.WG01_Placements`.
4. Run `studio/westgate/InstallBlock.lua`: one Model per piece under `Workspace.Map.Westgate.WG01.<Building>`,
   materials/colours from names, collision rules, door/window clones. Signs/decals keep their imported textures.

---
name: blender-to-roblox-pipeline
description: How to model in Blender for Roblox and get it into Studio correctly - stud units, FBX export settings, importer settings, mesh/texture limits, UVs and trim sheets, collision fidelity, instancing, modular kit pivots and the common pitfalls (100x scale, flipped normals, sealed doorways, duplicate MeshIds). Use when modeling, exporting, importing or debugging a Blender asset for the RobloxMapDev map.
---

# Blender → Roblox Studio pipeline

Full sourced notes: `research/forum/blender-to-roblox-pipeline.md`. Kit: `blender/rmd_kit.py`.

## Units and export (Roblox Creator Docs)
- Blender **Unit System: None**. 1 Blender unit = 1 stud. Studio does no unit conversion.
- FBX export: **Apply Scalings = FBX Unit Scale**, Scale 1.0, Forward **-Z**, Up **Y**, Apply Transform,
  Selected Objects only, Mesh: apply modifiers, smoothing Face, triangulate. (`rmd_kit.export_fbx` does all of this
  from `sizes.json` `export`.)
- Why: Blender's FBX writer wraps the scene in a 0.01 root node Studio ignores - skip FBX Unit Scale and imports come
  in **100× too big**. Never use the importer's "Meter" unit.
- 3D Importer: Scale Unit **Stud**, World Forward Front, World Up Top, **Insert Using Scene Position** on.
- Verify once per machine: Blender's default 2-unit cube imports as 2 × 2 × 2 studs.
- Pick one forward axis for the whole kit (-Z) and never mix.

## Before every export
Apply transforms (Ctrl+A) → Merge by Distance → Recalculate Outside (Shift+N) → one material per mesh (separate by
material) → check triangle count → export selected.

## Limits
- 20,000 triangles per mesh (over that, Roblox auto-decimates badly). 2,048 studs max per axis. One UV set.
- Textures: 512² default, 256² minor, 1024² our ceiling (engine allows 4096 since 2026). ~51 px/stud.
  Normal maps OpenGL (+Y). One moderated map blanks the whole SurfaceAppearance - keep uploads clean.

## Collision and rendering
- CollisionFidelity cheapest→dearest: Box, Hull, Default, PreciseConvexDecomposition. Decor = Box.
- **A wall mesh with a door hole on Box/Hull seals the doorway.** Use Default, split the wall around the opening, or
  invisible collision parts.
- Large shapes: invisible Box collision parts instead of precise mesh collision.
- RenderFidelity Automatic (LOD swaps at ~250 / 500 studs).

## Materials
- SurfaceAppearance follows UVs; trim sheets are the preferred approach (forum + docs). MaterialVariants ignore UVs -
  use them on parts and simple boxy shapes (and terrain).
- Tiling past the 0-1 UV range: test in Studio before relying on it.

## Modular kit + instancing
- One snap grid (ours: modules on 4 studs, door module 8). Pivots at a consistent corner in Blender.
- Upload each repeated mesh **once**, then copy it in Studio. Re-importing makes a new MeshId, which breaks batching
  and adds draw calls. Convert reusable buildings to Packages before placing many.

## Pitfalls checklist
100× scale · unapplied rotation/scale · flipped or backface-culled faces · silent decimation over 20k · duplicate
MeshIds · sealed doorways from Box/Hull · moderated textures · mixed forward axes.

---
name: roblox-map-performance
description: Performance and workflow rules for a large Roblox roleplay city map - per-view triangle/draw-call/memory budgets, mesh instancing and Packages, decor collision/shadow settings, StreamingEnabled setup, SLIM, lighting for phones, roads and terrain approach, level-design rules for RP cities. Use when placing, organizing or reviewing map content in Roblox Studio, or planning districts.
---

# Large RP map: performance + workflow

Full sourced notes: `research/forum/large-map-performance-workflow.md`.

## Budgets (per view, test on a phone)
~500k triangles · ~500 draw calls · client memory < 1.3 GB (2 GB phones) · network receive < 50 KB/s.
Measure with Ctrl+F2 (render stats) and the Developer Console while driving the map; Studio under-reports client memory.

## Instancing
- Draw calls batch only for the same MeshId + material + texture (color/scale/rotation may differ).
- Upload each kit mesh once; copy it. Never import whole scenes with duplicate meshes. Packages for reusable buildings.
- Transparency exactly 0 or 1 (partial transparency breaks batching). Avoid unions and decals for repeated detail.

## Part settings
- Everything Anchored.
- Decor: CollisionFidelity Box, CanCollide/CanTouch/CanQuery **false**, CastShadow false on small/distant props,
  RenderFidelity Automatic/Performance.
- Exceptions: CanQuery **true** for anything bullets or NPC vision rays must hit; CanTouch true on seats.

## Streaming
StreamingEnabled on · ModelStreamingBehavior **Improved** · StreamOutBehavior Opportunistic ·
StreamingIntegrityMode PauseOutsideLoadedArea · default radii (min 64, target 1024).
One Model per building, Folders for grouping, **never** one Atomic model around the map; Persistent rarely.
Terrain at least 16 voxels thick. Test streaming at the fastest car's top speed.
SLIM (distant LODs) on static building Models once the place is published (beta since Dec 2025).

## Lighting
`Lighting.Technology` was replaced (Jul 2025) by LightingStyle + PrioritizeLightingQuality (not scriptable).
Start with LightingStyle **Soft** for a big sunny map on phones; test Realistic on a 2-3 GB Android first. Few,
small shadow-casting lights.

## Roads and terrain
- Flat grid: modular road mesh kit (straight tiles, intersection pads, curb + sidewalk strips) with simple invisible
  part colliders. Terrain only for slopes/mountains/desert ground. Road plugins only for curved ramps.
- Expanded Terrain + MaterialVariants on Sand for desert ground. Don't edit terrain in Team Create.

## Workflow + level design
- Sketch → greybox with placeholder packages → art passes. CollectionService tags for culling groups.
- Keep generators, asset-ID lists and placement data in Git; the place file is build output.
- Road hierarchy freeway → arterial → collector → local on a grid. Landmarks on corners at every point of interest;
  POIs ~40 s of travel apart; bulky props along main corridors.
- Interiors only where a job or roleplay function exists; the rest are hollow shells.
- Occlusion culling helps little in a flat one-story city: client-side hide of small tagged details beyond ~300 studs.

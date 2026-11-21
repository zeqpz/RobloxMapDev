# Large Roblox city map: performance and workflow research

Compiled 2026-11-21 for a big Southwest-US (Albuquerque/El Paso style) roleplay city: mostly one-story buildings, wide arterials, many props, Blender meshes imported into Studio, R6 avatars.

Sources are the Roblox Creator Docs (official), Roblox staff DevForum announcements, and community DevForum threads. Each bullet carries its source and date.

**Tags**
- **[OFFICIAL]**: Creator Docs or a Roblox staff announcement.
- **[EXPERT]**: MrChickenRocket's Roblox-published guest article (he is a former mobile engine developer), or an article reviewed by the Roblox rendering team.
- **[COMMUNITY]**: a forum opinion.
- **[UNVERIFIED]**: not confirmed against an official source, or contradicted elsewhere.
- **[SYNTHESIS]**: my own inference for this project, not taken from a source.

---

## 0. Key sources (read these first)

| Source | Date | Why |
|---|---|---|
| [Instance streaming docs](https://create.roblox.com/docs/workspace/streaming) | current | Official settings and the recommended values |
| [Improve performance docs](https://create.roblox.com/docs/performance-optimization/improve) | current | Draw calls, instancing, collisions, textures, shadows |
| [Design for performance docs](https://create.roblox.com/docs/performance-optimization/design) | current | Reuse, packages, transparency, quality levels |
| [SLIM docs](https://create.roblox.com/docs/workspace/streaming/slim) + [SLIM beta thread](https://devforum.roblox.com/t/client-beta-introducing-scalable-lightweight-interactive-models-slim/4034709) | 2025-10 to 2026-02 | LODs for distant models (replaces StreamingMesh) |
| [MrChickenRocket: Real world building and scripting optimization](https://devforum.roblox.com/t/real-world-building-and-scripting-optimization-for-roblox/3127146) | 2024-08 | Budgets, batching, kitbashing, culling; linked from the Creator Docs |
| [Optimization For Roblox Environments (BlackoutCedar)](https://devforum.roblox.com/t/optimization-for-roblox-environments/3844846) | 2025-07 | Artist-side checklist, reviewed with MrChickenRocket and the Roblox rendering team |
| [Unified Lighting is fully live](https://devforum.roblox.com/t/let-there-be-unified-light-unified-lighting-is-fully-live/3401512) | 2025-01, updated 2025-07 | `Technology` replaced by `LightingStyle` and `PrioritizeLightingQuality` |
| [Occlusion Culling now live](https://devforum.roblox.com/t/occlusion-culling-now-live-in-roblox-client/3300953) | 2024-12, updated 2025-06 | Automatic; supports terrain |
| [Upgrades to Model Streaming](https://devforum.roblox.com/t/upgrades-to-model-streaming/2699921) | 2023-11 | `ModelStreamingBehavior = Improved` |
| [Ruski's Tutorial #5: Open World Map](https://devforum.roblox.com/t/ruskis-tutorial-5-how-to-design-an-open-world-map/3554962) | 2025-03 | Layout, landmarks, workflow |
| [Creating a realistic city](https://devforum.roblox.com/t/creating-a-realistic-city/3053768) | 2024-07 | North American road hierarchy and grid |

---

## 1. Performance for big maps

### 1.1 Budgets (set them before building)

- **[EXPERT]** Mid-2024 budget for 60 FPS on 90%+ of phones without auto-dropping below Graphics Quality 10 ([MrChickenRocket](https://devforum.roblox.com/t/real-world-building-and-scripting-optimization-for-roblox/3127146)):
  - 500k triangles in scene.
  - 500 draw calls in scene.
  - Client memory under 1.3 GB, so 2 GB phones are supported.
  - Client network receive under 50 KB/s, which works out to about 40-60 moving physics assemblies at 0.4-0.9 KB/s each.
  - UI draw calls should stay under about 150.
  - His demo budgeted the map at 300k triangles / 300 draws, and players/effects at 200k / 200. He then split the map budget per zone (about 40k triangles / 40 draws each, with at most 8 zones in view).
- **[OFFICIAL]** The docs use a looser baseline-device example: under 1,000 draw calls and 1M triangles. This comes from one developer's test, not a platform limit ([Design for performance](https://create.roblox.com/docs/performance-optimization/design)).
- **[EXPERT]** How to measure:
  - Ctrl+F2 (Ctrl+Shift+F2 in Studio) shows render stats. Watch `Draw (scene)` and `Draw (shadow)` counts, and CPU vs GPU ms to tell which is the bottleneck.
  - Ctrl+F7 or F9 shows memory and receive bandwidth. Studio cannot measure client memory accurately, so test live and on a real device.
  - Ctrl+F6 opens the MicroProfiler.
- **[OFFICIAL]** In streaming playtests, Shift+Ctrl+F3 opens Network Stats, then Shift+1 cycles to the Streaming panel.
- **[OFFICIAL]** The 3D importer caps each mesh at 20,000 triangles ([mesh specifications](https://create.roblox.com/docs/art/modeling/specifications)). Meshes must be watertight with no zero-thickness geometry. Prefer quads and avoid N-gons.
  - **[COMMUNITY]** Staff once put the real cap at about 21k ([glTF thread](https://devforum.roblox.com/t/3d-importer-support-for-gltf-files-beta/2320761/15)).
  - **[COMMUNITY][UNVERIFIED]** One FBX import handles about 200 objects; bigger scenes need splitting ([BlackoutCedar 2025](https://devforum.roblox.com/t/optimization-for-roblox-environments/3844846)).

### 1.2 Draw calls, batching and mesh instancing (the most important building rule)

- **[OFFICIAL]** Identical meshes with the same MeshContent and matching textures or SurfaceAppearance are instanced into one draw call ([Improve performance](https://create.roblox.com/docs/performance-optimization/improve)).
  - Upload each mesh once and duplicate it in Studio.
  - Importing a whole map can give identical meshes separate asset IDs, which breaks instancing.
  - Find duplicate meshes and textures uploaded under different IDs.
- **[EXPERT]** Batching works on MeshId plus material.
  - Color, rotation and scale can vary freely.
  - His tree, four meshes per tree and placed many times, costs 2 draw calls in total.
  - Built-in parts (block, wedge) are meshes internally and batch the same way.
  - Make your own reusable kit meshes, such as a curb corner, a beveled plank or a beveled cube ([MrChickenRocket](https://devforum.roblox.com/t/real-world-building-and-scripting-optimization-for-roblox/3127146)).
- **[EXPERT]** To bake part-built houses into meshes:
  1. Union the parts per material.
  2. Use Export Selection to get an .obj.
  3. Reimport and reassemble.
  - Result in his test: from 100+ parts and 12 draw calls down to 6 meshes and 6 draws, and copies batch with each other.
- **[OFFICIAL]** Convert assets to Packages as you make them, so copies don't end up with duplicate IDs ([Design for performance](https://create.roblox.com/docs/performance-optimization/design), [env-art tutorial](https://create.roblox.com/docs/tutorials/curriculums/environmental-art/optimize-your-experience)).
  - When you simplify geometry, update the existing package instead of creating a new asset ID.
- **[OFFICIAL]** Combining meshes that form one component cuts draw calls (their example goes from 8 to 1). Only do this late, because a combined asset can't be recolored or moved per piece ([env-art tutorial](https://create.roblox.com/docs/tutorials/curriculums/environmental-art/optimize-your-experience)).
- **[EXPERT]** Group mesh pieces that share one SurfaceAppearance or texture set into a single mesh. Keep moving or animated pieces separate. Prefer MaterialService tiled materials over many SurfaceAppearances on non-hero assets ([BlackoutCedar](https://devforum.roblox.com/t/optimization-for-roblox-environments/3844846)).
  - His example: an elevator with 40 SurfaceAppearances (160 textures) could be cut to about 4 texture sets and 8 meshes.
- **[EXPERT]** Transparent objects do not batch: each one becomes its own draw call. Avoid partial transparency ([BlackoutCedar](https://devforum.roblox.com/t/optimization-for-roblox-environments/3844846)).
- **[OFFICIAL]** Use only Transparency 0 or 1, because layered partial transparency causes overdraw ([Design for performance](https://create.roblox.com/docs/performance-optimization/design)).
- **[COMMUNITY]** Shadows, particles and UI do not batch ([definitive optimization tutorial, 2026-05](https://devforum.roblox.com/t/the-definitive-tutorial-to-game-optimization-everything-you-need-to-know/4629258)).
- **[COMMUNITY]** Decals and Textures add extra surface geometry. Put them only on block parts, and set CastShadow off on invisible decal hosts ([build checklist 2024](https://devforum.roblox.com/t/how-to-optimize-your-builds-checklist/3232350)). **[UNVERIFIED]**

### 1.3 Texture memory

- **[OFFICIAL]** Texture memory scales with pixel dimensions, not file size: a 1024² texture uses 4x the memory of a 512² ([Improve performance](https://create.roblox.com/docs/performance-optimization/improve)).
  - Keep most images at 512² or below, and minor images below 256².
  - Use trim sheets for texture reuse across 3D maps.
  - Tint one texture with `SurfaceAppearance.Color` instead of uploading color variants.
  - Compressing before upload does not reduce runtime memory.
- **[OFFICIAL]** Built-in materials use much less memory than custom textures. Save custom textures for key assets ([Design for performance](https://create.roblox.com/docs/performance-optimization/design)).
- **[EXPERT]** Max texture size is 1024². One 1024² set is better than four 512² sets, because it means fewer draw calls. Solid-color metal or roughness maps can be 1 px ([BlackoutCedar](https://devforum.roblox.com/t/optimization-for-roblox-environments/3844846)).
- **[COMMUNITY]** Join objects that share a texture map, and leave free space in atlases for later additions ([Texture Atlases](https://devforum.roblox.com/t/3171224)).

### 1.4 RenderFidelity, LOD and SLIM

- **[OFFICIAL]** Many complex meshes, or many meshes set to `RenderFidelity = Precise`, raise triangle load. Use Automatic or Performance so lower-poly fallbacks can kick in ([Improve performance](https://create.roblox.com/docs/performance-optimization/improve)).
- **[COMMUNITY]** In Automatic mode, the highest LOD shows under 250 studs, medium at 250-500, and lowest past 500 ([2026 tutorial](https://devforum.roblox.com/t/the-definitive-tutorial-to-game-optimization-everything-you-need-to-know/4629258), citing the docs).
- **[EXPERT][UNVERIFIED]** Use Performance in "95% of cases" and Precise only for things like mountain ranges ([BlackoutCedar](https://devforum.roblox.com/t/optimization-for-roblox-environments/3844846)). This is stronger than the docs say, so test it visually.
- **[OFFICIAL]** SLIM (`Model.LevelOfDetail = SLIM`) uses cloud transcoding to build composite multi-LOD meshes for models that are streamed out. It cuts draw calls, triangles and memory, and all parts in a model switch LOD together ([SLIM docs](https://create.roblox.com/docs/workspace/streaming/slim)).
  - Requirements: StreamingEnabled, a published place, and Team Create.
  - Good candidates: static buildings and props. Bad candidates: anything modified at runtime, animated models, or models containing a Humanoid.
  - Group parts into Models by logical object (one building, one car). Use Folders for arbitrary organization, since SLIM ignores them.
  - Separate overlapping or coplanar parts by about 0.01 studs to avoid SLIM z-fighting.
  - Status: Client Beta since 2025-10-30, on all platforms since 2025-12-09 ([beta thread](https://devforum.roblox.com/t/client-beta-introducing-scalable-lightweight-interactive-models-slim/4034709)). It replaces StreamingMesh.
  - Roblox's blog example: draw calls fell from 2,402 to 1,454 and triangles from 20M to 3.35M ([Roblox newsroom, Dec 2025](https://about.roblox.com/newsroom/2025/12/introducing-roblox-slim-scalable-lightweight-interactive-models)).
- **[OFFICIAL]** SLIM avatars (`EnableSLIMAvatars`) exclude R6. They do nothing for this game.
- **[COMMUNITY]** SLIM does not affect terrain streaming ([per search summary of SLIM thread replies](https://devforum.roblox.com/t/client-beta-introducing-scalable-lightweight-interactive-models-slim/4034709?page=8)). **[UNVERIFIED]**

### 1.5 StreamingEnabled settings

Official recommended values ([streaming docs](https://create.roblox.com/docs/workspace/streaming)):

- **[OFFICIAL]** `StreamingEnabled = true` (the default for new places). Only Workspace descendants stream.
- **[OFFICIAL]** `StreamingMinRadius = 64` and `StreamingTargetRadius = 1024` are the defaults, and Roblox recommends keeping them.
  - Target must be greater than Min; the gap is a network buffer.
  - The docs elsewhere say that lowering both makes streaming more aggressive for memory.
- **[OFFICIAL]** `StreamOutBehavior = Opportunistic` (recommended over the LowMemory default). It frees memory beyond the target radius even without memory pressure.
- **[OFFICIAL]** `StreamingIntegrityMode = PauseOutsideLoadedArea` (recommended).
  - Use `Player.GameplayPaused` for a custom pause UI.
  - Call `GuiService:SetGameplayPausedNotificationEnabled(false)` to hide the default modal.
- **[OFFICIAL]** `ModelStreamingBehavior = Improved` (recommended). Models are sent only when one of their BaseParts is needed, not at join.
  - Improved has been available since 2023-11 ([announcement](https://devforum.roblox.com/t/upgrades-to-model-streaming/2699921)).
  - With Improved, a whole-city Model is not streamed atomically.
- **[OFFICIAL]** `ModelStreamingMode` options:
  - **Nonatomic** (default).
  - **Atomic**: all descendants arrive together. Use it when scripts need the whole model.
  - **Persistent**: never streams out. Reserve it for rare cases, because overuse hurts.
  - **PersistentPerPlayer**.
  - A Persistent model nested inside an Atomic model forces the Atomic model to behave as Persistent.
- **[OFFICIAL]** Opt into `PredictiveStreamingMode = Enabled`. It pre-streams likely respawn spots and recently left areas with no code changes.
- **[OFFICIAL]** Each extra `ReplicationFocus` adds server load: 9 moving foci cost about as much as 10 players.
- **[OFFICIAL]** Avoid large moving assemblies, because they stream in as one unit and cause spikes.
- **[OFFICIAL]** Streamed-out instances are parented to nil, not destroyed. Client scripts must tolerate parts appearing and disappearing.
- **[OFFICIAL][staff, 2025-04]** Never make the whole map one Atomic model. It caused 10k+ ping and endless lag in a race-map report.
  - Staff fix: a non-atomic root with many smaller Atomic child models ([bug thread](https://devforum.roblox.com/t/modelstreamingmode-atomic-on-maps-cause-game-to-crash-forever/3596105)).
  - Avoid Atomic models with very large instance counts, because they cause bursty networking.
- **[OFFICIAL]** With a small streaming radius, terrain features thinner than 16 voxels may vanish on clients. Make terrain thick ([custom terrain materials](https://create.roblox.com/docs/parts/custom-terrain-materials)).
- **[COMMUNITY]** Older threads (2021) report that chunks fail to load at driving speed, so cars fall through the road ([mega city map](https://devforum.roblox.com/t/how-to-make-a-mega-city-map/1527626)).
  - **[SYNTHESIS]** Test with the fastest vehicle. Pause-outside-loaded-area, predictive streaming and keeping road collision inside the min radius are the official mitigations. Old complaints may predate them.
- **[COMMUNITY]** Splitting very large worlds into several places linked by teleports is an option. Ultimate Driving splits its cities across places ([50k map thread](https://devforum.roblox.com/t/is-a-50k-studs-x-50k-studs-map-too-big/1454280)).
  - The docs note the trade-off: shorter initial join, but a join wait between places.

### 1.6 Culling (occlusion, distance, zones)

- **[OFFICIAL]** Occlusion culling is automatic and needs no setup ([announcement](https://devforum.roblox.com/t/occlusion-culling-now-live-in-roblox-client/3300953)).
  - Live on all platforms since 2025-01-27; terrain supported since 2025-06-23.
  - The Haunt saw about 33% better P10 Android frame times.
  - Limits: only opaque meshes occlude. Small-on-screen or highly detailed meshes don't occlude. Lights, VFX, UI and shadow casters are not culled.
  - "It won't help much for arena scenes, but it will greatly help interiors and cityscapes."
- **[SYNTHESIS]** A flat Southwest city of one-story buildings and wide roads has long, open sightlines, so expect little from occlusion culling outdoors. Rely on streaming, SLIM, prop discipline and distance culling. Interiors do benefit.
- **[EXPERT]** Manual distance culling:
  - Tag small details (`Detail_Small`) and parent them to nil on the client when they are more than 300 studs from the camera.
  - Only re-check after the camera moves, and spread checks at about 50 per frame ([MrChickenRocket](https://devforum.roblox.com/t/real-world-building-and-scripting-optimization-for-roblox/3127146)).
  - Zone visibility lists work the same way. Mass re-parenting has CPU cost, especially for unions.
  - **[SYNTHESIS]** This conflicts with streaming if done server-side. Do it client-side only, and only for streamed-in objects.

### 1.7 Collision, physics and anchoring

- **[OFFICIAL]** Anchor everything that doesn't need physics. Leave the default adaptive physics stepping on, because fixed 240 Hz costs more ([Improve performance](https://create.roblox.com/docs/performance-optimization/improve)).
- **[OFFICIAL]** CollisionFidelity:
  - Box for small or non-interactive parts.
  - Box or Hull for small-to-medium parts.
  - Invisible custom collision parts for large complex objects.
  - PreciseConvexDecomposition is the most expensive.
- **[OFFICIAL]** For decor, set CanCollide, CanTouch and CanQuery to false. Collision geometry stays in memory anyway, so also set Box or Hull.
- **[COMMUNITY]** Keep CanTouch on for Seats and VehicleSeats. Keep CanQuery on for anything bullets or raycasts must hit; this game has guns and the police vision system ([checklist](https://devforum.roblox.com/t/how-to-optimize-your-builds-checklist/3232350)).
- **[COMMUNITY]** CanQuery can only be turned off once CanCollide is off ([2026 tutorial](https://devforum.roblox.com/t/the-definitive-tutorial-to-game-optimization-everything-you-need-to-know/4629258)).
- **[COMMUNITY]** Blender buildings: check the "Show Decomposition Geometry" view. Often you turn mesh collision off and trace walls and floors with invisible parts ([Blender workflow 2024](https://devforum.roblox.com/t/best-workflow-for-building-in-roblox-utilizing-blender/3006347)).
  - Recalculate normals outside in Blender so backface culling doesn't create invisible walls.

### 1.8 Shadows and lights

- **[OFFICIAL]** Turn CastShadow off on small or distant parts and moving objects, and turn `Light.Shadows` off where it isn't needed ([Improve performance](https://create.roblox.com/docs/performance-optimization/improve)).
  - Limit light range and angle, use fewer lights, and disable lights outside a set range.
  - Profile with the LightGridCPU and ShadowMapSystem scopes.
- **[OFFICIAL]** Turn CastShadow off on foliage near the edges of the play area ([env-art tutorial](https://create.roblox.com/docs/tutorials/curriculums/environmental-art/optimize-your-experience)).
- **[EXPERT]** Shadow draws cost less than scene draws but still count. Keep shadow-casting lights away from moving geometry ([MrChickenRocket](https://devforum.roblox.com/t/real-world-building-and-scripting-optimization-for-roblox/3127146)).
  - A few small non-shadow lights are cheap and break up flat shading.
- **[EXPERT]** Shadow test: toggle CastShadow on one copy of a prop next to a copy with it on, then disable it on every sub-part that doesn't change the silhouette ([BlackoutCedar](https://devforum.roblox.com/t/optimization-for-roblox-environments/3844846)).
  - **[UNVERIFIED]** His claim that spot and surface lights beat point lights.
  - **[UNVERIFIED]** His claim that moving lights add many draws.
- **[COMMUNITY]** In Future, overlapping light radii cut one tester from 200 FPS to 80-90 ([Future vs ShadowMap 2025](https://devforum.roblox.com/t/future-vs-shadow-map-performance/3600758)).

### 1.9 Lighting technology (now Unified Lighting)

- **[OFFICIAL]** Since 2025-07, `Lighting.Technology` has been replaced by two properties ([Unified Lighting](https://devforum.roblox.com/t/let-there-be-unified-light-unified-lighting-is-fully-live/3401512)):
  - `LightingStyle`: Realistic or Soft.
  - `PrioritizeLightingQuality`: when Enabled, the engine keeps lighting quality and cuts draw distance first; when Disabled, it does the opposite.
  - Old setting mapping: Future = Realistic + Prioritize Enabled. ShadowMap = Soft + Prioritize Enabled. Voxel = Soft + Prioritize Disabled.
  - Realistic + Prioritize Disabled = Future with a shorter shading distance.
  - Neither property is scriptable, so you can't offer a per-player toggle.
- **[EXPERT]** For a big, sunny, mostly outdoor map, consider ShadowMap only, and be conservative with shadow-casting lights in Future ([MrChickenRocket](https://devforum.roblox.com/t/real-world-building-and-scripting-optimization-for-roblox/3127146)).
- **[COMMUNITY]** A large driving map in Future was unplayable on phones with under 2 GB RAM; replies recommend ShadowMap ([2024 thread](https://devforum.roblox.com/t/future-vs-shadowmap-performance/3246937)).
- **[SYNTHESIS]** For this map:
  - Start with Soft + PrioritizeLightingQuality Disabled, or Soft + Enabled if building shadows matter.
  - Keep draw distance a priority, since the Southwest city has wide-open sightlines.
  - Only try Realistic (Future) after measuring on a 2-3 GB Android phone.

---

## 2. Roads and terrain

### 2.1 Roads: meshes vs parts vs terrain (no consensus; trade-offs)

- **[COMMUNITY 2025-10]** Use modular custom meshes with PBR textures; roads are simple geometry and batching handles repetition ([parts or decals?](https://devforum.roblox.com/t/what%E2%80%99s-better-for-roads-parts-or-decals/4012581)).
- **[COMMUNITY 2024-03]** Build road segments in Blender and place or resize them in Studio ([realistic roads](https://devforum.roblox.com/t/best-way-to-make-realistic-roads/2861220)).
  - Use the Array and Curve modifiers for bends.
  - Keep triangle counts low.
  - Avoid unions, which are poorly optimized and buggy.
  - If a road surface sits proud of the ground, it needs real collision.
- **[COMMUNITY 2023-07]** Several builders still lay out parts by hand with Archimedes for precise, editable networks. Plugins struggled with ramps and exits ([how do you make roads](https://devforum.roblox.com/t/devs-how-do-you-make-your-roads-help-needed/2496394)).
- **[COMMUNITY 2025-07]** Terrain roads (Heisters): the asphalt is a custom terrain material ([Heisters terrain roads](https://devforum.roblox.com/t/heisters-using-terrain-for-roads/3820006)).
  - Lane lines are one transparent textured part per segment, laid out with Archimedes before the terrain is generated.
  - It blends cleanly on slopes and uses fewer parts.
  - A reply says the Roblox racing template does the same.
- **[COMMUNITY]** Decals for lines and sidewalks look blurry or pixelated up close ([parts vs textures](https://devforum.roblox.com/t/whats-better-creating-roads-using-multiple-parts-or-using-textures/1564175), [parts or decals](https://devforum.roblox.com/t/what%E2%80%99s-better-for-roads-parts-or-decals/4012581)).
- **[COMMUNITY 2024-10]** Curbs: use one low-poly curb mesh with a PBR texture, repeated, instead of rounded-cube kit pieces ([curbs thread](https://devforum.roblox.com/t/best-way-to-make-curbs-for-sidewalks/3226647)).
- **[EXPERT]** MrChickenRocket made a reusable corner mesh for rounded footpath edges, used everywhere and batched.
- **[SYNTHESIS]** For a mostly flat Southwest grid, modular mesh kits instanced in Studio are the best fit for draw calls:
  - Asphalt straight tiles of a few lengths, intersection pads (4-way, T, with or without turn lanes), curb and gutter strips, sidewalk slabs, driveway cuts and median pieces.
  - Each piece is uploaded once, uses one MaterialVariant or trim sheet, and has Box collision. Use thin invisible part colliders if the mesh hulls are bad.
  - Terrain roads are worth it only where the ground undulates (mesa edges, arroyos, hills).

### 2.2 Road plugins (status as of 2026)

- **QuickRoad (GeomTools)**: node-based splines; nodes are stored in ServerStorage for later editing. It was beta in 2022, and a 2025 post still recommends it ([QuickRoad](https://devforum.roblox.com/t/new-geomtools-plugin-quickroad-is-finally-here/2024127), [tips thread 2025-04](https://devforum.roblox.com/t/tips-tricks-for-building-in-roblox-studio-%E2%80%93-recommended-plugins-shortcuts-and-best-practices/3632450)).
- **Road Creator** (modernized TTP plugin, 2024-02, free): intersections with SnapTo points, plus a companion PowerPole plugin ([thread](https://devforum.roblox.com/t/road-creator-plugin/2849433)).
- **CivilArc Road Toolkit** (formerly Bezier Curve Road Generator, v2.1, updated 2025-11): plotted points, design-speed curve geometry, Finalize step ([thread](https://devforum.roblox.com/t/civilarc-road-toolkit-fmr-bezier-curved-road-generator/3165280)).
- **Macurly Roadways** (2026-07, early): nodes, camber and height, auto kerbs, guardrails, streetlights, powerlines and signage. Intersections were still in progress ([thread](https://devforum.roblox.com/t/advanced-roadway-generation-plugin/4716784)). **[UNVERIFIED]** Status unknown.
- **Beautiful Roads**: deprecated ([thread](https://devforum.roblox.com/t/beautiful-roads-plugin-deprecated/511940)).
- **[SYNTHESIS]** Since the source of truth is Blender, a scripted Blender road and kit placement step, exported as instance transforms and replayed in Studio with cloned kit meshes, avoids relying on any of these plugins. Spline plugins are most useful for one-off curved ramps.

### 2.3 Terrain and desert materials

- **[OFFICIAL]** Expanded Terrain (per place, off by default, needs a reopen) unlocks up to 62 custom paintable terrain materials ([custom terrain materials](https://create.roblox.com/docs/parts/custom-terrain-materials)).
  - Each material has a name, base material, optional MaterialVariant and color tint.
  - It also shrinks terrain's share of the place file and improves streaming and load times.
  - Deleting a material that is in use turns that terrain purple.
- **[OFFICIAL]** Terrain caveats:
  - Custom physical properties on a MaterialVariant are not respected by terrain slots.
  - Editing terrain in Team Create can cause meshing bugs.
  - After toggling Expanded Terrain in Team Create, exit, wait about 15 s, then reopen.
- **[OFFICIAL]** MaterialVariants live in MaterialService ([materials docs](https://create.roblox.com/docs/parts/materials)).
  - Each one has a BaseMaterial (use Sand for a desert sand variant) and a Studs Per Tile setting.
  - "Set as Override" applies a variant to every part and terrain voxel of that base material.
  - Parts store the variant by name, so every MaterialVariant must exist in MaterialService for reused packages to render correctly.
  - TerrainDetail customizes top, side and bottom faces.
- **[OFFICIAL]** The docs say built-in materials are cheaper than custom textures. Tiled MaterialVariants load each texture once ([BlackoutCedar, rendering-team reviewed](https://devforum.roblox.com/t/optimization-for-roblox-environments/3844846)).
- **[SYNTHESIS]** Desert palette ideas:
  - Sand (caliche or dirt variant), Ground and Mud (dry arroyo), Sandstone, Rock and Slate (mesas), Asphalt (roads, if they are terrain), Pavement and Concrete (lots).
  - Tint per district rather than adding textures.
- **[COMMUNITY]** Terrain vs parts for city ground: there's little measured difference ([2022 thread](https://devforum.roblox.com/t/smooth-terrain-or-part-terrain-for-a-realistic-city-game/1768044)). Keep terrain thin but at least 16 voxels where streaming is on.

---

## 3. Map-building workflow

### 3.1 Kits, packages, hierarchy

- **[EXPERT]** Kitbash: reuse and intersect a small set of meshes, and vary scale, rotation and color ([MrChickenRocket](https://devforum.roblox.com/t/real-world-building-and-scripting-optimization-for-roblox/3127146)).
  - A rule of thumb: if a mesh looks the same in wireframe as it does solid, it has too many triangles.
- **[OFFICIAL]** How Packages work ([docs](https://create.roblox.com/docs/projects/assets/packages)):
  - **Creating**: right-click > Convert to Package and set group ownership, which can't be transferred later. Wrap single objects in a Model first. Never delete or move the `PackageLink`.
  - **AutoUpdate**: turn it on via PackageLink. Copies update when a place opens, but a modified copy stops auto-updating. For nested packages, only the top-level AutoUpdate counts, and you must publish the child before the parent.
  - **Variation**: root attributes act as per-copy configuration that survives updates. Scripts must read them.
  - **Greyboxing**: use placeholder packages, which auto-update as detailed versions are published.
  - **Updating safely**: close other Studio windows before mass updates.
- **[OFFICIAL]** Use Models for logical objects (a building, a car) and Folders for organization. SLIM and streaming treat Models as intent; Folders are ignored ([SLIM thread](https://devforum.roblox.com/t/client-beta-introducing-scalable-lightweight-interactive-models-slim/4034709)).
- **[OFFICIAL]** Keep client-unneeded assets in ServerStorage, not ReplicatedStorage, because clients load all of ReplicatedStorage ([Design for performance](https://create.roblox.com/docs/performance-optimization/design)).
- **[EXPERT]** Use CollectionService tags for spot effects and culling groups (`Zone`, `Detail_Small`), rather than scripts inside props.
- **[SYNTHESIS]** Suggested hierarchy, so it plays well with Improved streaming and SLIM:

  ```
  Workspace.Map (Folder)
    Districts (Folder) > <District> (Folder) > Blocks (Folder) > Block_<id> (Folder)
      > Bldg_<type>_<id> (Model, SLIM, package copy)
      > Props (Folder) > Prop_<type> (Model per prop cluster)
    Roads (Folder) > <corridor> (Folder) > segment Models
    Terrain
  ```

  - Never use one Model for the whole map.
  - Keep Atomic for small interactive things (doors, ATMs) only.

### 3.2 Blender to Studio

- **[OFFICIAL]** Each mesh is capped at 20k triangles and must be watertight, with no zero-thickness geometry ([specs](https://create.roblox.com/docs/art/modeling/specifications)).
- **[COMMUNITY]** Export at scale 0.01 so Blender units become studs ([Blender workflow](https://devforum.roblox.com/t/best-workflow-for-building-in-roblox-utilizing-blender/3006347)). **[UNVERIFIED]** It depends on your Blender unit and FBX settings; verify with a 1-stud test cube.
- **[COMMUNITY]** Perfectly flat planes can import with zero size on one axis. Give them thickness ([search summary of import threads](https://devforum.roblox.com/t/best-way-to-import-a-large-map/2748667)).
- **[EXPERT]** Before export, delete interior faces (Select > Select All by Trait > Interior Faces). Bake fine detail into textures, keep silhouettes, and join objects that share a texture ([BlackoutCedar](https://devforum.roblox.com/t/optimization-for-roblox-environments/3844846)).
- **[COMMUNITY]** Modern boxy buildings can be built from Parts plus MaterialVariants, with meshes only for trim, frames and roofs ([Blender workflow](https://devforum.roblox.com/t/best-workflow-for-building-in-roblox-utilizing-blender/3006347)).
- **[OFFICIAL]** Do not import the whole city as one scene. Identical meshes get separate IDs and won't instance. Upload each kit mesh once, then place copies in Studio ([Improve performance](https://create.roblox.com/docs/performance-optimization/improve)).

### 3.3 Plugins builders recommend (2023 to 2026)

- **[COMMUNITY 2026-01]** F3X Building Tools, Archimedes (arcs and curved repeats), Performance Heatmap, Resurface, Beveler, Terrain Adjuster, stravant's plugins, Load Character, Part to Terrain, GapFill and Reflect ([best plugins 2026](https://devforum.roblox.com/t/the-best-plugins-for-builders/4207930)).
- **[COMMUNITY 2025]** Studio Build Suite (bulk resize), MaterialFlip, QuickRoad ([tips 2025](https://devforum.roblox.com/t/tips-tricks-for-building-in-roblox-studio-%E2%80%93-recommended-plugins-shortcuts-and-best-practices/3632450)).
- **[COMMUNITY 2023]** A stravant plugin pack (fan port), Reclass, a part counter, the Mesh Optimization Tools decomposition viewer (asset 414923656) and Asset Previewer ([best plugins 2023](https://devforum.roblox.com/t/best-building-plugins/2572030)).
- **[UNVERIFIED]** Model Reflow (stravant) and Brushtool did not appear in the threads I read. Both are widely known, but I didn't verify their current versions or prices.
- **Built-in**: the Studio collision-fidelity and decomposition visualization (viewport options), wireframe rendering, and the MicroProfiler.

### 3.4 Version control for maps

- **[OFFICIAL]** Fully managed Rojo keeps code and level layout in Git ([Rojo fully managed](https://create.roblox.com/docs/projects/rojo/fully-managed)).
  - Each area is a `.rbxm` under `src/Workspace/Areas/`, with one owner per area because two editors conflict.
  - Team Create is not supported in this mode.
  - For teams that edit levels in place in Team Create, the docs recommend "the Rojo + Packages workflow instead".
- **[OFFICIAL]** Rojo limits:
  - Live sync can't set `MeshPart.MeshId`, terrain or CSG; art changes need `rojo build` and a reopen.
  - Terrain is binary and belongs to one owner in its own file.
  - Re-uploading a mesh gives it a new asset ID.
  - Built places have no package-style links.
- **[OFFICIAL]** Studio Version History saves versions per place that you can view, compare and restore ([managing projects](https://create.roblox.com/docs/projects/managing)).
- **[COMMUNITY]** Common pattern: code goes through Rojo/Git, while builders work in Team Create and the place file is handled separately ([partially managed Rojo](https://devforum.roblox.com/t/partially-managed-rojo-git-workflow-in-teams/1381762)).
  - Argon is an alternative to Rojo, but Rojo is the most used ([Argon thread](https://devforum.roblox.com/t/argon-full-featured-tool-for-roblox-development/2021776)). **[UNVERIFIED]** Argon's current feature parity.
- **[SYNTHESIS]** For an agent-driven Blender pipeline:
  - Keep the generator scripts, kit manifest (mesh asset IDs) and placement data (JSON transforms) in Git.
  - Treat the place as a build artifact that a placement script reconstructs.
  - Keep terrain in a single owner's file and save the place to Roblox Version History after each pass.

---

## 4. Level design for roleplay cities

- **[COMMUNITY]** Design around gameplay and movement first. In a driving game, roads matter more than buildings ([city layout](https://devforum.roblox.com/t/how-to-city-layout/1347903), [city blocks](https://devforum.roblox.com/t/how-should-i-layout-my-city-blocks/357068)).
- **[COMMUNITY]** Map size should match travel speed: if a car crosses the map in under 10 seconds, it feels small ([50k thread](https://devforum.roblox.com/t/is-a-50k-studs-x-50k-studs-map-too-big/1454280)).
  - **[UNVERIFIED]** The Jailbreak map is about 5k studs long.
- **[COMMUNITY 2025]** Ruski's open-world rules ([Ruski #5](https://devforum.roblox.com/t/ruskis-tutorial-5-how-to-design-an-open-world-map/3554962)):
  - Every point of interest (POI) gets a distinct, tall landmark.
  - In cityscapes, put landmarks on street corners, where players slow down to turn.
  - Triangle rule: always keep at least 3 POIs on the horizon.
  - Keep POIs within about 40 s of travel of each other.
  - Draw overlapping "spheres of interest" around POIs and put in-between locations where they overlap.
  - Give each district its own color palette.
  - A compact map full of unique places beats a huge, repetitive one.
- **[COMMUNITY 2025]** Ruski's art tricks ([Ruski #5](https://devforum.roblox.com/t/ruskis-tutorial-5-how-to-design-an-open-world-map/3554962)):
  - Selective detailing: detail the main routes with large, bulky props such as trees, traffic lights and poles.
  - Recycle meshes.
  - Use atlases.
  - Barriers: if it isn't enterable, it shouldn't look enterable.
- **[COMMUNITY 2025]** Ruski's workflow ([Ruski #5](https://devforum.roblox.com/t/ruskis-tutorial-5-how-to-design-an-open-world-map/3554962)): POI list, landmarks and spawn → block out with real blocks → region borders → main paths → spheres → in-between spots → playtest the scale → secondary paths → details.
  - Industry order: sketch → greybox → iterative art passes ([city layout](https://devforum.roblox.com/t/how-to-city-layout/1347903)).
- **[COMMUNITY 2024]** Realistic North American cities use a road hierarchy (freeway → arterial → collector → local) on a planned grid ([Creating a realistic city](https://devforum.roblox.com/t/creating-a-realistic-city/3053768)).
  - Believable layouts follow hierarchy and zoning; that's what sells GTA's cities ([Ruski #5 reply](https://devforum.roblox.com/t/ruskis-tutorial-5-how-to-design-an-open-world-map/3554962)).
  - Phoenix-style cities are "built out rather than up" ([city blocks](https://devforum.roblox.com/t/how-should-i-layout-my-city-blocks/357068)), which fits the Albuquerque and El Paso sprawl.
- **[COMMUNITY]** Block size is anecdotal. One builder moved from 256×256 to 256×128-stud rectangular blocks with 2-3 buildings each, varied per block ([2019 thread](https://devforum.roblox.com/t/how-should-i-layout-my-city-blocks/357068)).
  - Wide roads are fine because "most robloxians don't know how to stay in their lane" ([2024 thread](https://devforum.roblox.com/t/seeking-opinions-in-building-location-and-placement-road-size/3099246)).
  - Size roads from the vehicle, and the vehicle from the character ([street scale thread](https://devforum.roblox.com/t/scaling-the-city-how-streets-should-be-made/1067805)).
- **[COMMUNITY]** Avoid repetition: vary color, size and greenery, add alleys and roundabouts, build interactive buildings first and filler last, and add easter eggs ([repetitive city thread](https://devforum.roblox.com/t/how-to-build-city-maps-that-arent-repetitive/336205)).
- **[COMMUNITY]** Roleplay staples: shops, cafes, a daycare, an apartment complex, parks, library, gym and community buildings, balanced between residential and commercial ([RP layout thread](https://devforum.roblox.com/t/help-needed-with-layout-for-roleplay-game/3257628)).
  - Use about 3 contrasting regions at a consistent level of detail ([open vs confined RP](https://devforum.roblox.com/t/open-or-confined-making-a-rp-town-map/306381)).
  - Players cluster around game functions (job sites), so put jobs where you want traffic.
- **[UNVERIFIED]** Non-DevForum advice: delete interiors of buildings players can't enter, and give the map one memorable central landmark ([Brookhaven guide site](https://robloxbrookhavenmaptemplatedownloadstudio.pages.dev)).
- **[SYNTHESIS]** Southwest RP specifics:
  - Arterials 6-7 lanes with a center turn lane or median.
  - Strip malls set back behind parking lots, gas stations on arterial corners, and low adobe or stucco one-story shells.
  - Landmarks (water tower, mountain backdrop, a big sign, a stadium) on corners and the skyline.
  - Enterable interiors only where a job or roleplay function exists; everything else is a hollow, collision-only shell.
  - Keep spawn, jobs and the police station within about 40 s of driving of each other.
  - Use long sightlines plus SLIM for the distant city, and keep prop density high only along main corridors.

---

## 5. Mobile and low-end

- **[EXPERT]** Budget for Quality 10 on phones: 500k triangles, 500 draws, under 1.3 GB memory, under 50 KB/s receive.
  - Lower quality settings automatically remove shadows, cut draw distance, simplify particles and beams, and drop water and glass shaders.
  - Staying under budget keeps players on Quality 10 ([MrChickenRocket](https://devforum.roblox.com/t/real-world-building-and-scripting-optimization-for-roblox/3127146)).
- **[OFFICIAL]** Draw distance at the lowest quality is at least 500 studs, but don't design around exact distances.
  - Test at both the lowest and highest Editor Quality Level.
  - Don't change effects based on `UserGameSettings.SavedQualityLevel`, because it interferes with auto-scaling.
  - Studio's emulator overstates memory ([Design for performance](https://create.roblox.com/docs/performance-optimization/design)).
- **[OFFICIAL]** Streaming is the most effective client memory optimization for large worlds ([Improve performance](https://create.roblox.com/docs/performance-optimization/improve)).
- **[COMMUNITY]** Run the MicroProfiler on a real phone: enable it in settings, then open `phoneIP:1338` in a browser ([2026 tutorial](https://devforum.roblox.com/t/the-definitive-tutorial-to-game-optimization-everything-you-need-to-know/4629258), citing the docs).
- **[OFFICIAL]** Occlusion culling and SLIM are available on Android and iOS (see 1.4 and 1.6). SLIM avatars don't apply to R6.
- **[COMMUNITY]** Future lighting on phones with under 2 GB RAM was unplayable on a big driving map ([thread](https://devforum.roblox.com/t/future-vs-shadowmap-performance/3246937)).
- **[COMMUNITY]** SmoothPlastic is the cheapest material, and DoubleSided should stay off ([2026 tutorial](https://devforum.roblox.com/t/the-definitive-tutorial-to-game-optimization-everything-you-need-to-know/4629258)). **[UNVERIFIED]** The material cost claim.

---

## 6. Items flagged as dubious or contested

- "Roblox's official culling feature is released, so manual culling isn't needed" ([checklist edit](https://devforum.roblox.com/t/how-to-optimize-your-builds-checklist/3232350)). This is true for occlusion only. Distance culling of small details is still useful on open maps.
- "RenderFidelity = Performance in 95% of cases" ([BlackoutCedar](https://devforum.roblox.com/t/optimization-for-roblox-environments/3844846)). The docs only say Automatic or Performance; check distant buildings visually.
- "Disable StreamingEnabled for performance" (2021 posts). This is superseded: Roblox now recommends streaming for large places, and the 2026 tutorial author disables it only for bandwidth-heavy RTS games.
- "Terrain burns a lot of polys", so use meshes for the ground (2021). This is old and contradicted by Expanded Terrain improvements and terrain occlusion (2025).

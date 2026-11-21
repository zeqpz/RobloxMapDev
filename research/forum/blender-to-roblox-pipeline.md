# Blender -> Roblox Studio pipeline (city RP map, R6)

Research date: 2026-11-21. Sources: Roblox Creator Docs (official), Roblox DevForum (staff + community), KatsBits.
Every claim is tagged with its source. **[UNVERIFIED]** = I could not confirm it or it comes from a single post.
**Gaps:** Reddit (r/robloxgamedev) refuses automated access, and searches restricted to Blender StackExchange
returned no Roblox-specific threads. Nothing below comes from those two sites.

Project context: R6 avatars (~5 studs tall), doors standardized at 4.6 W x 7.4 H x 0.5 D studs.

---

## 1. Units and scale

### What the official docs say (current)
- 1 stud = **28 cm** in Roblox's physics unit table; the engine itself does no unit conversion. https://create.roblox.com/docs/en-us/physics/units
- Studio does not convert meters/cm/feet from DCC tools: **a 2 m import becomes 2 studs**, so treat Blender units as studs. https://create.roblox.com/docs/resources/beyond-the-dark/building-architecture
- Blender setup: Scene Properties > Units > **Unit System = None**, Rotation = Degrees. https://create.roblox.com/docs/en-us/art/blender
- FBX scale has three accepted options (official table, "Adjust scale (FBX)"): https://create.roblox.com/docs/en-us/art/blender
  1. **Recommended:** Export > Transform > **Apply Scalings = FBX Unit Scale**, with *every other scale value left at 1.0*. Round-trips to Studio and back into Blender at the same size.
  2. Export > Transform > **Scale = 0.01**. Works in Studio, but the file comes back into Blender 100x too small.
  3. Scene Units > **Unit Scale = 0.01**. Works, but docs warn it causes "camera difficulties, issues with modifiers" in Blender.
  - Docs also warn: older tutorials/assets use inconsistent scale settings, so test them against your own workflow.
- Studio 3D Importer: File Geometry > **Scale Unit = Stud** (the default). https://create.roblox.com/docs/en-us/art/blender , https://create.roblox.com/docs/art/modeling/3d-importer
- The export-requirements page repeats: Apply Scalings = FBX Unit Scale; Path Mode = Copy + Embed Textures; disable Add Leaf Bones; disable Bake Animation for static meshes. https://create.roblox.com/docs/art/modeling/export-requirements

### Why FBX comes in 100x too big
- Blender's FBX writer scales objects x100 under a x0.01 root node, and Roblox drops the root scale, so 1 BU becomes 100 studs. OBJ imports 1:1. (2023 community post) https://devforum.roblox.com/t/modelling-units-versus-roblox-studs/2392679
- Same diagnosis in an accepted answer: "1 Blender unit is indeed 1 Stud ... if you export your model as an fbx, suddenly 1 Blender unit is 100 studs", hence the 0.01 export. https://devforum.roblox.com/t/how-do-blender-units-relate-to-studs/1446602
- KatsBits (updated 2026-09): FBX from Blender shows up 100x larger; set the FBX export Scale to 0.01. https://www.katsbits.com/codex/?p=8437
- The official Roblox Blender add-on exports at **0.01 by default** ("equates Blender Meters to Roblox Studs") and ignores the FBX dialog settings. https://devforum.roblox.com/t/reference-roblox-integration-for-blender/2546753?page=2

### Conflicts and traps
- **Do not set the importer's Scale Unit to Meter.** A 2023 test found Meter makes a 1 m cube import as **20 studs**, the old 1 stud = 5 cm convention, not 28 cm. Foot gave 6.1 studs. The poster called it a bug. **[UNVERIFIED whether still true]** https://devforum.roblox.com/t/modelling-units-versus-roblox-studs/2392679
- A 2025 "Realism 101" tutorial says to export at **".10"** with "Apply Scalings: FBX All" and **Apply Unit unchecked**. That disagrees with every other source and is probably a typo for .01. **[UNVERIFIED]** A different commenter reports that "FBX All + Apply Unit off" imports small. https://devforum.roblox.com/t/realism-101-building-in-roblox-using-blender/4081400
- Changing Unit Scale makes the Blender viewport clip/fade; fix it with View > Clip Start/End (N panel). https://devforum.roblox.com/t/how-to-create-modular-asset-pack-in-blender/3109987
- The legacy importer had a **"Rescale if too large"** box; uncheck it. https://devforum.roblox.com/t/realism-101-building-in-roblox-using-blender/4081400 . The current importer instead warns and scales down meshes over **2048 studs**. https://devforum.roblox.com/t/new-unified-smart-mesh-importer-beta/1583213

### Verifying scale
- Officially, import from Studio into Blender at **Scale 1**, Forward **Z**, Up **Y**, then build against it. https://create.roblox.com/docs/en-us/art/blender
- Community: "import a roblox character for scale". https://devforum.roblox.com/t/how-to-create-modular-asset-pack-in-blender/3109987
- Test a 1x1x1 cube or Blender's default 2 m cube; it should arrive as 2x2x2 studs. https://devforum.roblox.com/t/realism-101-building-in-roblox-using-blender/4081400 , https://www.katsbits.com/codex/?p=8437
- Studio-side reference: snap = 1 stud, and a 1x1-stud part exported from Studio fills one Blender grid square (1 m). https://devforum.roblox.com/t/how-do-blender-units-relate-to-studs/1446602
- Classic (R6-style) avatars are "around 5 studs tall". https://create.roblox.com/docs/studio/avatar-settings . A 7.4-stud door is therefore about 1.5x avatar height, a normal game exaggeration.

---

## 2. Export settings (FBX / OBJ / glTF)

### FBX, per official docs
- Include: **Limit to Selected Objects** on. https://create.roblox.com/docs/en-us/art/blender
- Transform: **Apply Scalings = FBX Unit Scale**, **Forward = "Z Forward"**, **Up = Y Up**. https://create.roblox.com/docs/en-us/art/blender
- Path Mode = Copy + Embed Textures (the PBR maps travel with the file). https://create.roblox.com/docs/art/modeling/export-requirements
- Studio side: World Forward = **Front**, World Up = **Top**, Scale Unit = **Stud**, and **Insert Using Scene Position** on, so pieces keep their Blender placement. https://create.roblox.com/docs/en-us/art/blender

### Axis conflict
- The official page says **"Z Forward"**. Blender's FBX default and most community posts use **-Z Forward / Y Up**, which differs by a 180-degree yaw. One DevForum fix: Ctrl+A apply all transforms, then export with -Z forward, Y up, Apply Transform checked. https://devforum.roblox.com/t/rotations-wrong-on-imported-fbx/3267661
- Blender maintainers warn that **Apply Transform** (experimental) misbehaves on parented hierarchies. https://developer.blender.org/T97043
- In practice: pick one convention and lock it into an export script, so every kit piece faces the same way. **[my inference]**

### Applying transforms, normals, cleanup (community consensus)
- Before export: Ctrl+A > Scale (or all), Merge by Distance, **Shift+N Recalculate Outside**, Shade Auto Smooth, and join objects that belong together. https://devforum.roblox.com/t/realism-101-building-in-roblox-using-blender/4081400
- Negative scale on one or three axes inverts face winding; apply the scale, then fix the normals. https://developer.blender.org/T96430 (via search), https://devforum.roblox.com/t/why-some-meshes-got-inverted-normals-in-roblox/2448060
- Smoothing: mark sharp edges (plus seams), use auto smooth, and bevel hard edges (1 segment if triangles are tight). https://devforum.roblox.com/t/realism-101-building-in-roblox-using-blender/4081400
- Triangulate: no official requirement found. glTF triangulates quads/n-gons on export anyway (Blender manual). https://docs.blender.org/manual/en/latest/addons/scene_gltf2.html . Docs want meshes "quads where possible" at the authoring stage. https://create.roblox.com/docs/art/modeling/specifications

### Format choice
- **OBJ:** imports 1:1 with no scale fix, but it is static only and carries one mesh group. https://devforum.roblox.com/t/how-do-blender-units-relate-to-studs/1446602 , https://devforum.roblox.com/t/models-are-huge-when-importing-them-to-roblox-studio/2022100
- **FBX and glTF:** only these two support multiple meshes + hierarchy, PBR textures, rigs, animation and vertex colors in the importer. https://create.roblox.com/docs/art/modeling/3d-importer
- **glTF/glb:** full release since Sept 2023. Staff: .gltf and .glb are handled identically; .glb embeds the textures. https://devforum.roblox.com/t/3d-importer-gltf-file-support-full-release/2584034 . Open Cloud import accepts glTF too (2024). https://devforum.roblox.com/t/3d-import-recap-mar-apr-2024/2979668
- KatsBits recommends glTF over FBX when the asset is anything but simple. https://www.katsbits.com/codex/?p=10511
- **glTF scale:** no source tested glTF-to-stud scale directly. glTF is meter-based with no 100x root node, so 1 BU should equal 1 stud. **[UNVERIFIED; test a cube]**

### One mesh vs many, pivots
- Importer defaults: **Import Only As Model** = on (one Model asset), **Merge Meshes** = off (on collapses everything into one MeshPart), **Set Pivot to Scene Origin** = on, per-object **Use Imported Pivot** = on. https://create.roblox.com/docs/art/modeling/3d-importer
- Turn **Upload to Roblox** off while iterating, so you don't spam your inventory with copies. https://create.roblox.com/docs/art/modeling/3d-importer
- **A mesh can have only one material.** Separate by material in Blender, or let the file split into one MeshPart per material. https://create.roblox.com/docs/art/modeling/texture-specifications , https://devforum.roblox.com/t/how-do-i-import-a-model-with-multiple-materials/2965633
- Name suffixes the importer converts: `_Att` becomes an Attachment, `_InnerCage`/`_OuterCage` become wraps. glTF adds a `_Node` suffix when a node and mesh share a name. https://create.roblox.com/docs/parts/meshes , https://create.roblox.com/docs/art/modeling/3d-importer

---

## 3. Mesh limits and import

| Limit | Value | Source |
|---|---|---|
| Triangles per mesh | **20,000** (staff: "actually 21K"; a 16-bit index-buffer limit). Over-limit meshes are **auto-simplified** with LOD tech, which looks bad on big reductions. | https://create.roblox.com/docs/art/modeling/specifications , https://devforum.roblox.com/t/3d-importer-support-for-gltf-files-beta/2320761 , https://devforum.roblox.com/t/new-unified-smart-mesh-importer-beta/1583213 |
| Size per MeshPart axis | **2048 studs**; larger imports are scaled down with a warning. | https://devforum.roblox.com/t/new-unified-smart-mesh-importer-beta/1583213 , search summary of https://create.roblox.com/docs/parts/meshes |
| Older 10k triangle limit | Obsolete since the 2021 importer. | https://devforum.roblox.com/t/exceed-10000-triangle-limit/1760555 |
| Meshes per file / scene | No stated limit (beta-era post). **[UNVERIFIED now]** | search summary of https://devforum.roblox.com/t/3d-importer-full-release/2057539 |
| UV sets | 1 per mesh. | https://create.roblox.com/docs/art/modeling/texture-specifications |

- Meshes should be watertight, have no zero-thickness faces, and use quads where possible (official, avatar-focused spec). https://create.roblox.com/docs/art/modeling/specifications
- Community norm for environment props: you "almost never should reach 1K poly" on non-deforming objects. Model blockouts in Studio, export glTF, then quadify, limited-dissolve, delete hidden faces and bake high-to-low. (One opinionated post.) https://devforum.roblox.com/t/realism-101-building-in-roblox-using-blender/4081400
- **Asset Manager:** bulk-imports images, meshes, packages, audio and models. Imports go through moderation first. It cannot import rigged/skinned meshes. https://create.roblox.com/docs/en-us/projects/assets/manager , https://create.roblox.com/docs/parts/meshes . Bulk import inside the 3D Importer was "being worked on" in 2024. **[UNVERIFIED if shipped]** https://devforum.roblox.com/t/3d-import-recap-mar-apr-2024/2979668
- **MeshPart vs SpecialMesh:** forum evidence is anecdotal; neither is clearly faster. Use MeshPart: it has CollisionFidelity, RenderFidelity and SurfaceAppearance. https://devforum.roblox.com/t/specialmesh-vs-meshpart/688384 . Batching follows MeshId either way. https://devforum.roblox.com/t/does-roblox-use-mesh-instancing/399564

### CollisionFidelity (official, cheapest to most expensive)
- **Box**: bounding box, for small/non-interactive objects. **Hull**: convex hull. **Default**: approximate shape that supports concavity. **PreciseConvexDecomposition**: most precise, but "most expensive performance cost", still not 1:1. **Tunable**: adds a CollisionPrecision slider. https://create.roblox.com/docs/workspace/collisions , https://create.roblox.com/docs/parts/meshes
- Docs say it is "generally safe to set any small anchored part's collision fidelity to Box". For large complex objects, build custom collision from small Box parts. Objects with no collision should still get Box/Hull fidelity, because collision geometry uses memory even with CanCollide off. https://create.roblox.com/docs/performance-optimization/improve
- Set CanTouch = false on objects that don't need touch events. https://create.roblox.com/docs/workspace/collisions
- Check collision shapes with Visualization Options > Collision fidelity (the viewport widget). https://create.roblox.com/docs/workspace/collisions
- Community: transparent collision parts shaped to the walkable volume, with mesh collision turned off. https://devforum.roblox.com/t/imported-mesh-collision-problem/1621880 (search summary)
- PreciseConvexDecomposition still lets players float on curved surfaces (2023 report). https://devforum.roblox.com/t/3d-importer-gltf-file-support-full-release/2584034
- **City-map pitfall [my inference from the definitions]:** a wall mesh with a door or window hole set to **Box or Hull fills the hole**, and the doorway blocks players. Either give door walls Default/Precise, split the wall into solid slabs around the opening, or use invisible Box-collision parts plus CanCollide=false on the mesh. "Can't walk in model" threads describe exactly this. https://devforum.roblox.com/t/cant-walk-in-model/1445127

### RenderFidelity
- Automatic (default) picks LOD by camera distance: **<250 studs Highest, 250–500 Medium, 500+ Lowest**. https://create.roblox.com/docs/parts/meshes
- Use Automatic/Performance, and avoid Precise on many meshes. https://create.roblox.com/docs/performance-optimization/improve

---

## 4. Materials and textures

### SurfaceAppearance (PBR)
- **MeshParts only**: parts have no UVs. Maps: ColorMap, NormalMap, RoughnessMap, MetalnessMap and an emissive mask. A SurfaceAppearance overrides Color/Material/TextureID. https://create.roblox.com/docs/art/modeling/surface-appearance , https://create.roblox.com/docs/resources/beyond-the-dark/building-architecture
- Normal maps must be **OpenGL tangent-space** (Blender bakes OpenGL by default; Substance's default DirectX preset must be switched). https://create.roblox.com/docs/art/modeling/texture-specifications
- Metalness workflow only; metalness is usually 0 or 1. AlphaMode: Overlay (default), Transparency (cutouts), TintMask, Opaque (beta). `SurfaceAppearance.Color` tints at no performance cost. https://create.roblox.com/docs/art/modeling/surface-appearance
- Properties can't be changed by script at runtime. https://create.roblox.com/docs/art/modeling/surface-appearance
- If both a SurfaceAppearance and a MaterialVariant are set, the SA maps win and the MV keeps the physical properties. https://create.roblox.com/docs/parts/meshes

### Resolution and memory
- **4K (4096x4096) textures are live in published games since 2026-01-30** for MeshPart, SurfaceAppearance, Texture, Decal and MaterialVariant, via texture streaming. Images up to 8K can be uploaded but are transcoded to 4K. https://devforum.roblox.com/t/4k-texture-rendering/4316229
- The texture-spec page says "up to 4096x4096" but elsewhere still says "1024x1024 pixel spaces"; that line is stale. https://create.roblox.com/docs/art/modeling/texture-specifications
- Official guidance: memory scales with pixel count (1024² = 4x 512²). Compressing or stripping alpha doesn't help. Most images "usually need at most 512x512", minor ones under 256. https://create.roblox.com/docs/performance-optimization/improve
- **Texel density reference (official):** 256 px per 5x5 studs, 512 per 10x10, 1024 per 20x20, i.e. **~51 px/stud**. Default part materials run 1024 px per 8 studs (128 px/stud). https://create.roblox.com/docs/art/modeling/texture-specifications
- Formats: .png, .jpg, .tga, .bmp. https://create.roblox.com/docs/art/modeling/texture-specifications

### Tiling vs trim sheets vs atlases
- A SurfaceAppearance **follows mesh UVs and has no tiling property**. To tile it, scale the UVs past 0–1 in Blender. https://devforum.roblox.com/t/tiling-pbr-textures/1298479 , https://devforum.roblox.com/t/surfaceappearance-texture-tiling/928282 . Conflict: the texture-spec page says "All UVs must be within the 0:1 space" (likely aimed at avatar assets). **[UNVERIFIED for environment meshes; test]**
- **MaterialVariants do NOT follow mesh UVs.** They project with StudsPerTile, so seams on MeshParts are uncontrollable (complaints as recent as 2025-07). Use MVs for tiling surfaces on parts or simple boxy meshes; use SurfaceAppearance for UV-mapped trims. https://devforum.roblox.com/t/materialvariant-obey-meshpart-uv-maps-property/2205123 , https://devforum.roblox.com/t/meshpart-using-a-material-variant-is-not-even-around-the-mesh-how-to-fix/2743462
- MVs live in MaterialService; parts store the variant *name*, so renaming or replacing a variant swaps the look everywhere. MVs carry physical properties; SAs don't. https://create.roblox.com/docs/parts/materials
- Trim sheets: Beyond the Dark used a handful of swappable trim sets for **~90% of its architecture**, with keeping meshes whole to cut draw calls. https://create.roblox.com/docs/resources/beyond-the-dark/building-architecture . Official perf docs also recommend trim and sprite sheets. https://create.roblox.com/docs/performance-optimization/improve
- Trim-sheet modeling tutorial (2024): quads in linear strips, inset large faces to create trim strips, keep texel density consistent, avoid "over-trimming", pair one tiling texture with one trim sheet. https://devforum.roblox.com/t/3171223 . Roblox caveat: one material per mesh, so "two materials" means two MeshParts.

---

## 5. Modular kit practice

- **Grid:** pick one grid for the whole project and every artist. Beyond the Dark used **16 studs**. https://create.roblox.com/docs/resources/beyond-the-dark/building-architecture . The Modern City kit uses **7.5 studs**, 45-degree rotate snap, and every piece's length is a multiple of 7.5. https://create.roblox.com/docs/tutorials/use-case-tutorials/modeling/assemble-modular-environments . A community kit uses 10 studs. https://devforum.roblox.com/t/uncopylocked-building-kit/3349134 . The Studio 1-stud snap matches the Blender 1 m grid. https://devforum.roblox.com/t/realism-101-building-in-roblox-using-blender/4081400
  - For this map: the 4.6 x 7.4 door doesn't divide evenly into a 7.5 or 16 grid. Put the door inside a wall *module* whose outer size sits on the grid (for example 8 W x 12 H studs), not the opening itself. **[my inference]**
- **Pivots:** consistent pivot placement is "of vital importance". Modern City puts it at the forward-most lower corner. Set pivots in Blender, because Studio Pivot Tools only fix parts. Moving several meshes at once averages their pivots and breaks alignment. https://create.roblox.com/docs/tutorials/use-case-tutorials/modeling/assemble-modular-environments
- **Few versatile pieces, few one-offs.** Every extra piece costs build time, memory and performance. https://create.roblox.com/docs/resources/beyond-the-dark/building-architecture
- **Packages:** convert each modular piece and material to a package *before* populating the map, with AutoUpdate on (1,000+ wall instances in Beyond the Dark). Importer has an **Import as Package** option. https://create.roblox.com/docs/resources/beyond-the-dark/building-architecture , https://create.roblox.com/docs/art/modeling/3d-importer
- **Naming:** `_SA` suffix for SurfaceAppearances (e.g. `Metal_Trim_A_SA`). https://create.roblox.com/docs/resources/beyond-the-dark/building-architecture . No official kit-piece naming standard found. **[gap]**
- **Instancing drives the kit decision.** Meshes batch into one draw call only with the same MeshId and the same SurfaceAppearance/TextureID (or same material). "Only upload each mesh in a map once and then duplicate them in Studio." Re-importing the same window creates a new ID and breaks batching. https://create.roblox.com/docs/performance-optimization/improve . Color doesn't break instancing; transparency does (each transparent part gets its own draw call; 2018 staff). https://devforum.roblox.com/t/part-instancing-pre-release-announcement/130333/1
  - So repeated windows, doors and trims should be **separate reused MeshParts**, not baked into one unique building mesh. Unique facades can be whole meshes, kept under 20k triangles and 2048 studs. **[synthesis]**
- **Interiors vs hollow shells:** no forum source compared them directly. **[gap]** Related official levers: instance streaming is on by default for new places, and you can lower StreamingMinRadius/TargetRadius and set models to LevelOfDetail = SLIM. https://create.roblox.com/docs/performance-optimization/improve

---

## 6. Common pitfalls (with fixes)

1. **100x scale on FBX.** Use Apply Scalings = FBX Unit Scale with everything else at 1.0, or export Scale 0.01. Never use importer Scale Unit = Meter. (Sources in §1)
2. **Invisible or see-through faces.** Roblox culls backfaces; Blender shows both sides. Fix with Face Orientation overlay (red = flipped) + Backface Culling preview, then Shift+N Recalculate Outside. Apply transforms first; watch for negative scale. DoubleSided / importer "Make Double Sided" is the costly last resort. https://devforum.roblox.com/t/models-faces-break-on-import/2484198 , https://devforum.roblox.com/t/i-recalculated-normals-but-it-looks-inverted-on-studio/2899964 , https://create.roblox.com/docs/art/modeling/3d-importer
3. **Unapplied rotation/scale** gives wrong sizes or rotations on import. Fix with Ctrl+A. https://devforum.roblox.com/t/models-are-huge-when-importing-them-to-roblox-studio/2022100 , https://devforum.roblox.com/t/rotations-wrong-on-imported-fbx/3267661
4. **Over 20k triangles** gets silently auto-decimated. Split the mesh or bake detail instead. https://devforum.roblox.com/t/3d-importer-support-for-gltf-files-beta/2320761
5. **Duplicate mesh IDs** (re-importing identical pieces) break instancing and add draw calls; the official docs include a script to find them. https://create.roblox.com/docs/performance-optimization/improve
6. **Collision cost and wrong shapes.** Default/Precise on everything costs memory and physics time. Box/Hull on walls with openings seals the doorways. (Sources in §3)
7. **Texture moderation.** One rejected map (often a noisy normal map) makes the whole SurfaceAppearance fail to load. Appeal or open a support ticket rather than spam re-uploads; moderation queues all Asset Manager imports. https://devforum.roblox.com/t/how-do-you-reliably-upload-normal-maps/1763891 , https://devforum.roblox.com/t/texture-always-gets-moderated-when-trying-to-upload/2967985 , https://create.roblox.com/docs/en-us/projects/assets/manager
8. **SurfaceAppearance intermittently "unavailable"** (2025): a CDN/transcode issue that fixes itself; reopening Studio helps. https://devforum.roblox.com/t/surfaceappearance-doesnt-apply-anymore/3651470
9. **Expecting MaterialVariant to follow UVs.** It doesn't; use SurfaceAppearance. (Sources in §4)
10. **DirectX normal maps** look inverted; Roblox is OpenGL-only. https://create.roblox.com/docs/art/modeling/texture-specifications
11. **Texture memory.** Many unique 1–4K maps cost memory by pixel count; reuse trim sheets and SA.Color tints. https://create.roblox.com/docs/performance-optimization/improve
12. **Multi-material meshes.** One material per MeshPart; separate by material in Blender. https://devforum.roblox.com/t/how-do-i-import-a-model-with-multiple-materials/2965633

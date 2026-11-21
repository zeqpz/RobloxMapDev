# RobloxMapDev

Tooling, standards, research and AI agents for building a realistic **Southwest-US roleplay city** in Roblox
(Albuquerque / El Paso flavor, Houston-inspired) for **R6 avatars**. Buildings are modeled in **Blender 5.2** (driven
by Claude through the MCP for Blender add-on), exported as FBX and assembled in **Roblox Studio**.

## What's here

| Path | What |
|---|---|
| [`standards/SIZING.md`](standards/SIZING.md) | The sizing standard. Door **4.6 × 7.4 × 0.5 studs** and everything derived from it |
| [`standards/sizes.json`](standards/sizes.json) | Same standard, machine-readable (the single source of truth) |
| [`blender/rmd_kit.py`](blender/rmd_kit.py) | Blender kit: stud-scale scene, R6 proxy, standard door + cutters, fit check, standard FBX export |
| [`studio/StandardSizes.lua`](studio/StandardSizes.lua) | Generated ModuleScript with the standard (`python tools/gen_luau_sizes.py`) |
| [`studio/ScaleAudit.lua`](studio/ScaleAudit.lua) | Command-bar audit: select a building Model, get pass/fix lines |
| [`research/city-reference/`](research/city-reference/) | ABQ + El Paso field research: `REPORT.html` + Street View / satellite / 3D reference photos, and the capture pipeline |
| [`research/forum/`](research/forum/) | Sourced DevForum/Creator-Docs research: Blender→Roblox pipeline, R6 scale, large-map performance |
| [`plans/map/MAP_PLAN.md`](plans/map/MAP_PLAN.md) | **Alamo County map sketch v2** (realistic street network) + 7-phase construction plan (terrain → roads → utilities → markings → shells → interiors → details); layout data `plans/map/layout.json` from `tools/map_layout.py` + `tools/render_map.py` |
| [`.claude/agents/`](.claude/agents/) | Claude Code agents: map-architect, blender-builder, standards-auditor, texture-artist, roblox-importer, reference-researcher |
| [`.claude/skills/`](.claude/skills/) | Skills: sizing standards, Blender→Roblox pipeline, map performance, Southwest style |
| [`.claude/workflows/build-building.js`](.claude/workflows/build-building.js) | Workflow: plan → model → audit/fix → texture → export → import → audit |

## Building a new building

1. Open Blender (the MCP for Blender add-on starts its server on `localhost:9876`) and, for the import step, Roblox Studio.
2. In Claude Code, opened in this repo, describe the building. For the full pipeline run the workflow:
   `run the build-building workflow with slug abq_flat_roof_house_a and this description: ...`
3. Or step by step: ask the **map-architect** for a plan (`plans/<slug>.md`), the **blender-builder** to model it,
   the **standards-auditor** to check it, the **texture-artist** for materials, then the **roblox-importer**.

## Viewing the city research

```powershell
python -m http.server 8842 --directory research/city-reference
```
Then open http://localhost:8842/REPORT.html. Images don't load if you open the file directly.

## Key rules (details in the skills)

- Mixed scale: heights at real scale (1 stud = 0.28 m), walkable widths fit the R6 (4 wide) and the camera, roads and
  cars at gameplay scale.
- Blender Unit System None; FBX Apply Scalings = FBX Unit Scale; importer Scale Unit = Stud.
- < 20k triangles per mesh; textures 512² (max 1024²); upload each repeated mesh once; decor without collision/shadows.
- Never put Box/Hull collision on a wall mesh with a door hole (it seals the doorway).
- Fictional brands only. Google imagery is reference, never textures.

Imagery in `research/city-reference` © Google, captured for internal design reference only. Keep this repository private.

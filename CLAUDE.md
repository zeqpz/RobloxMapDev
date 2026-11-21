# RobloxMapDev - notes for Claude

- Realistic Southwest-US RP city for Roblox, **R6 avatars**. Owner describes buildings one at a time; answer with the
  map-architect plan format (design notes + poly budget, modeling steps, material/texture plan, UV/optimization,
  FBX export settings) or run `.claude/workflows/build-building.js`.
- **Sizes come from `standards/sizes.json`** (door 4.6 × 7.4 × 0.5 studs). Never hard-code a size the file defines;
  after editing it run `python tools/gen_luau_sizes.py`.
- Blender: live instance over MCP for Blender (localhost:9876). Load `blender/rmd_kit.py`; Unit System None,
  1 unit = 1 stud; R6 proxy at every doorway/stair. Only one agent drives Blender at a time.
- Studio: Roblox Studio MCP. Confirm the active place before mutating; never start play tests yourself - ask the owner.
- Textures: Poly Haven / ambientCG first; OpenRouter key in `C:\Users\CooperHinkel\Documents\gamdevkey.txt` (never
  print or commit it). Google Maps/Earth imagery is reference only.
- Fictional brands only - no real logos or names on in-game buildings.
- City research: `research/city-reference` (serve with `python -m http.server 8842 --directory research/city-reference`;
  capture pipeline in its `tools/`, venv `.venv` not committed - recreate with `pip install playwright pillow`).

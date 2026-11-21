---
name: rmd-sizing-standards
description: The RobloxMapDev R6 sizing standard - door 4.6 x 7.4 x 0.5 studs and every size derived from it (windows, walls, ceilings, stairs, rails, furniture, hallways, grid modules, roads, sidewalks, parking, vehicles, poles). Use whenever you size, model, review or place anything for the map, in Blender or Roblox Studio.
---

# RobloxMapDev sizing standard

Source of truth: `standards/sizes.json` (studs). Human table: `standards/SIZING.md`. Studio module:
`studio/StandardSizes.lua` (generated with `python tools/gen_luau_sizes.py` - regenerate after editing the JSON).
Evidence: `research/forum/r6-scale-standards.md`.

## The rule (mixed scale)
- **Door = 4.6 W × 7.4 H × 0.5 D.** At Roblox's official 1 stud = 0.28 m that is a real 2.07 m door.
- **Heights at real scale** (0.28 m/stud): door, window sill 3.0 / head 7.4, ceilings 10 (house) / 12 (shop),
  floor-to-floor 11 / 13, stair rise 0.65, rail 3.3, counter 3.0, table 2.6, seat 1.6.
- **Walkable widths fit R6 + camera:** R6 is 5.25 tall, 4 wide across the arms, collision torso 2 wide.
  Hallway ≥ 7, public corridor ≥ 9, room ≥ 9 × 9, stairs 5.5 wide (run 1.1), public entrances double doors 9.2.
- **Roads and cars at gameplay scale:** lane 14 (highway 16), sidewalk 8/10, curb 0.55, stall 11 × 22,
  sedan 8 × 19 × 5.6.
- Exterior wall 1.0 thick, interior 0.5, never < 0.4 (camera pokes through).
- Grid: snap 1, modules on 4 (wall lengths 4/8/12/16), door module 8 long, pivot bottom-left-front corner.
- Compress blocks and lots to keep the map walkable; never shrink openings or heights.

## How to apply
- Look sizes up in `sizes.json` by key and cite the key in plans; don't restate numbers from memory - the file can
  change.
- In Blender: `rmd_kit.make_r6_proxy()` beside every doorway/stair, `rmd_kit.check_fit()` to measure.
- In Studio: select the building Model and run `studio/ScaleAudit.lua`.
- Anything the standard does not define: propose a value with the reasoning (real size × 1/0.28 for heights, R6/camera
  minimum for widths) and add it to `sizes.json` + `SIZING.md` once the owner agrees.

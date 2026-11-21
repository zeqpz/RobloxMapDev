# RobloxMapDev sizing standard (R6)

Everything is in **studs**. The machine-readable copy is [`sizes.json`](sizes.json), which feeds the Blender kit
(`blender/rmd_kit.py`) and the Studio module (`studio/StandardSizes.lua`). Change it there and regenerate with
`python tools/gen_luau_sizes.py`.

## The anchor: the door

| | Width | Height | Thickness |
|---|---|---|---|
| **Standard door** | **4.6** | **7.4** | **0.5** |

At Roblox's official unit (**1 stud = 0.28 m**), 7.4 studs is a 2.07 m (6'9") door: a real door.

## The rule: mixed scale

An R6 avatar is 5.25 studs tall (1.4 m) but 4 studs wide (1.1 m). It's short and very wide, so no single real-world scale
fits it. Forum consensus, and this standard:

1. **Heights use real scale** (0.28 m per stud): doors, ceilings, windows, stair risers, rails, counters. This is what makes
   buildings look realistic.
2. **Walkable widths fit the R6 and the camera**: hallways, stairs, rooms, doors for public entrances. A 4-stud body and a
   third-person camera need more room than a real person.
3. **Roads and vehicles use gameplay scale** (~1.2–1.4× real): lanes, stalls and cars sized so R6 drivers fit and players
   don't feel cramped.

Never shrink an opening or a height to make a building fit a lot. Compress the **blocks** (lot depth, block length)
instead.

## Openings

| Item | Size (W × H × D) | Notes |
|---|---|---|
| Door | 4.6 × 7.4 × 0.5 | 0.3 frame; rough opening 5.2 × 7.7; handle at 3.5 |
| Double door / shop entrance | 9.2 × 7.4 (storefront 9.2 × 8.0) | use for public entrances; 4.6 is tight for traffic |
| Garage door | 10 × 8 single, 18 × 8 double | |
| Roll-up shutter | 12 × 9 | |
| Window | sill 3.0, head 7.4 (height 4.4); widths 3 / 4 / 6 / 8 | head lines up with the door head |
| Storefront glass | sill 1.0, head 8.0, transom to 10 | |

## Walls, floors, heights

| Item | Studs |
|---|---|
| Exterior wall | 1.0 thick (brick 1.0; never under 0.4, or the camera pokes through) |
| Interior wall | 0.5 thick |
| Slab | 1.0 |
| House ceiling / floor-to-floor | 10 / 11 |
| Shop/office ceiling / floor-to-floor | 12 / 13 (storefront 14) |
| One-story house | wall top 11, with parapet 13 |
| Parapet | 1.5–2.5 |
| Strip-mall façade | 18–21 |
| Big-box parapet | 33–40 |
| Gas canopy | 18 clearance, 3.5 fascia |

## Circulation and furniture

| Item | Studs |
|---|---|
| Hallway (home) | ≥ 7 wide |
| Public corridor | ≥ 9 wide |
| Smallest room | 9 × 9 (camera) |
| Stairs | rise 0.65, run 1.1, width 5.5, landing 5.5 (R6 can step up to ~2.5) |
| Ramp | ≤ 10° |
| Railing | 3.3 tall |
| Counter / bar | 3.0 / 3.8 |
| Table / desk | 2.6 |
| Chair seat | 1.6 |
| Bed | 2.0 |

## Grid and modules

- Snap 1 stud; modules on a **4-stud** grid. Wall modules are 4 / 8 / 12 / 16 long.
- **Door module = 8 long**: the 4.6 door plus frames, centred.
- Pivot every module at its bottom-left-front corner, on the grid.

## Site and roads

| Item | Studs |
|---|---|
| Lane (street / highway) | 14 / 16 |
| Turn lane / parking lane / bike lane | 14 / 10 / 6 |
| Median | 14–24 |
| Residential street curb-to-curb | 34–40 |
| Alley | 16–20 |
| Sidewalk residential / commercial | 8 / 10 |
| Curb height × width | 0.55 × 0.5 |
| Parking stall | 11 × 22 |
| Yard fence / arterial wall | 4.4–6.6 / 8.8 |
| Streetlight / utility pole | 28 / 34 |
| Signal mast clearance | 19 |
| Sedan / pickup / SUV / box truck | 8 × 19 × 5.6 / 8.5 × 22 × 7 / 8.4 × 20 × 6.8 / 10 × 32 × 13 |

## Performance budgets

- Per view: ~500k triangles, ~500 draw calls. Client memory < 1.3 GB.
- Each mesh < 20k triangles. Textures 512² default, 256² minor, 1024² max (normal maps OpenGL).
- Decor: Anchored, CollisionFidelity Box, CanCollide/CanTouch/CanQuery off, CastShadow off on small props. Keep
  CanQuery **on** for anything bullets or NPC vision must hit.
- Walls with door holes: never Box/Hull collision on the whole mesh (it fills the hole). Split the wall around the
  opening or add invisible collision parts.
- Streaming: on, ModelStreamingBehavior Improved, one Model per building, never one Atomic model for the map.

## Export (Blender → Studio)

Blender Unit System **None** (1 Blender unit = 1 stud). FBX: Apply Scalings **FBX Unit Scale**, scale 1.0, Forward -Z,
Up Y, apply transforms, selected only. In the 3D Importer, set Scale Unit to **Stud** and turn on Insert Using Scene
Position. Check: Blender's 2-unit cube must import as 2 × 2 × 2 studs.

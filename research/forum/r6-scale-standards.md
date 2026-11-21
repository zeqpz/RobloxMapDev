# R6 scale standards for a realistic city RP map

Researched 2026-11-21. Fixed by the owner: **door 4.6 W x 7.4 H x 0.5 T studs**.
R6 body: 5 studs tall (feet to top of head), 4 studs wide across the arms, 1 stud deep. Head 2x1x1, Torso 2x2x1, each limb 1x2x1.

Tags used below:
- **[SRC]**: stated in the linked source.
- **[DERIVED]**: my arithmetic from a sourced number. No source states it.
- **[UNVERIFIED]**: taken from a search-engine snippet, from general engine knowledge, or from a page I could not read in full. Check in Studio before relying on it.

Access notes:
- Some DevForum threads now return "That page is private" (HTTP 403) to logged-out readers, among them the main door thread `t/what-should-be-the-ideal-door-size/2200910`. Its numbers below come only from search snippets.
- Reddit (r/robloxgamedev, r/ROBLOXStudio) blocks the research tools, so nothing from Reddit is included.
- I found **no published measurements** for ER:LC, Southwest Florida, Greenville, Brookhaven or Bloxburg. Treat any claim about those games' scale as unknown.

---

## 1. Stud-to-meter conventions

### Conventions in use
- **0.28 m per stud is the official figure.** Roblox's Units doc says "1 stud = 28 cm" [SRC] https://create.roblox.com/docs/physics/units
- A Roblox physics product manager says the Game Settings > World dialog "show[s] that there are 28 centimeters per stud" [SRC] https://devforum.roblox.com/t/units-on-roblox/2418615
- The Beyond the Dark doc agrees: "The closest real-world scale for a single stud in Roblox is 28 centimeters." [SRC] https://create.roblox.com/docs/resources/beyond-the-dark/building-architecture
- The same Beyond the Dark doc warns that Studio imports units 1:1: "if you set your units to meters, Studio converts 2 meters to 2 studs." [SRC] (same URL)
- **0.28 m comes from the World settings.** The Game Settings World panel (April 2019) turns 35 studs/s² "realistic" gravity into 9.8 m/s², which gives 3.571 studs = 1 m [SRC] https://devforum.roblox.com/t/understanding-roblox-physics-and-their-conversions-to-real-units/1847678
- **20 studs per meter is the old, physics-only convention.** It derives from default gravity 196.2 studs/s² = 20 × 9.81, and from a 2012 Roblox blog post. At that scale a 5-stud character is 25 cm tall, so nobody builds to it [SRC] https://devforum.roblox.com/t/how-many-studs-is-there-in-a-meter/103417 and https://devforum.roblox.com/t/converting-real-world-measurements-to-studs/318197
- **About 0.30 m per stud (1 stud = 1 ft) is the builders' convention.** One poster: "I typically use 1 Stud = 1 Foot … puts the character at 5 feet tall (1.5m)" [SRC] https://devforum.roblox.com/t/how-many-studs-is-there-in-a-meter/103417
- An early reply in the same thread, citing a VR best-practices article, says "For default sized Roblox characters, 1 stud should be treated as 30 centimeters." [SRC] (same URL)
- A flight-sim developer also uses 1 stud = 1 ft [SRC] https://devforum.roblox.com/t/scaling-down-a-game/1009351
- **0.32 to 0.36 m per stud is one city builder's range.** He uses Revit and QGIS: "I use a range of like 0.32 - 0.36 Meters per Stud" [SRC] https://devforum.roblox.com/t/how-to-city-layout/1347903
- **4.46 studs per meter (1 ft = 1.36 studs) is a width-matched scale.** It was proposed because 1 ft/stud "matches the character's height pretty well, but does not match the character's width". It is calibrated from train-track gauge [SRC] https://devforum.roblox.com/t/how-many-studs-is-there-in-a-meter/103417
- **Other one-offs** from a summary post: 1 stud = 1 m (mesh export), 5 cm (gravity), 33.4 cm (VR), 30 cm (attributed to zeuxcg) [SRC] https://devforum.roblox.com/t/converting-real-world-measurements-to-studs/318197
- **The common advice is to scale to the character, not to the meter.** Representative quotes:
  - "scaling your builds to a roblox character rather than exact real life measurements. Your builds will look strange if using exact real life measurements" [SRC] https://devforum.roblox.com/t/converting-real-world-measurements-to-studs/318197
  - Keep a "size test" rig (R6/R15) and drag it around the build [SRC] https://devforum.roblox.com/t/scaling-buildings-properly/1054615
  - Scale a real floor plan until one room fits the rig [SRC] https://devforum.roblox.com/t/floor-plan-help/3167796
- **Vehicles look small at true 1:1 scale.** One poster asked whether it is normal "that Vehicles look small in Roblox also when its the same size as Real world". In the same thread: "video game doorways (especially 3rd-person view game doorways) can be vastly oversized compared to the characters" [SRC] https://devforum.roblox.com/t/what-is-the-real-world-size-in-roblox/1998881

### What the R6 body implies
- Matching R6 height to a 1.75 m adult gives **0.35 m/stud**. At 0.28 m/stud an R6 is only **1.40 m** tall [DERIVED].
- **R6 is extremely wide.** 4 studs across the arms is 1.12 m at 0.28 or 1.40 m at 0.35. A real adult's shoulders are about 0.45 m. **No single scale fits both R6 height and width** [DERIVED]. A poster in the 1863780 thread makes the same point: an R6 in real life would be "6 feet tall, shoulder span of 4 feet" [SRC] https://devforum.roblox.com/t/how-to-convert-studs-to-real-world-units/1863780
- **The owner's door is real-world size at 0.28 m/stud.** 7.4 × 0.28 = 2.07 m, about a real 6'8"–6'9" door. A real 80 in (2.03 m) door would be 7.26 studs [DERIVED]. One poster did this exact sum: at 0.28 m a door is "~7.24 studs high and ~3.26 studs wide" [SRC] https://devforum.roblox.com/t/how-many-studs-is-there-in-a-meter/103417
- **So the map's vertical scale is effectively 0.28 m/stud.** Widths cannot follow 0.28, because a real 0.91 m door is 3.26 studs, narrower than the 4-stud R6. That is why the owner chose 4.6 [DERIVED].

### R6 vs R15/Rthro
- Roblox docs: "classic style avatars are around 5 studs tall. More humanoid style proportions are around 6 to 6.5 studs." Custom Scale can force an absolute height in studs [SRC] https://create.roblox.com/docs/studio/avatar-settings
- On the door thread, a reply warned that Rthro players can reach about 7.5 studs and recommended 10 x 5 doors "to be safe". Another reply noted that Game Settings can make all players the same size [SRC] https://devforum.roblox.com/t/quick-question-on-door/393398
- Another poster gives the default R6/R15 at about 5.125 studs high x 4 wide [UNVERIFIED: search snippet of the private thread 2200910]
- R15 games may allow height scaling of 95–105% [UNVERIFIED: search snippet]
- **R6-only removes the Rthro worry.** A 7.4-stud door leaves 2.4 studs over a 5-stud head. If R15/Rthro are ever enabled, a 6.5-stud Rthro clears a 7.4 door by only 0.9 [DERIVED].

---

## 2. Interior dimensions

### What the sources say
- **Doors:**
  - 7.5–8.0 H x 5–6 W "so avatars don't look cramped", and "about 8 high and 5 wide" [UNVERIFIED: snippets of private thread 2200910]
  - 10 H x 5 W "to be safe" for Rthro [SRC] https://devforum.roblox.com/t/quick-question-on-door/393398
  - Roblox's own greybox sample "keeps every doorway and hallway at least 10 studs wide" so two players can pass. That is a combat-map sample, not a realism target [SRC] https://create.roblox.com/docs/tutorials/curriculums/environmental-art/greybox-your-environment
- **Ceiling heights:**
  - "I currently have it at 8 studs of height on the inside, but I feel like this is a little claustrophobic." Replies suggested "1 1/2 - 2 Robloxians" (7.5–10), "10 or even 12 studs", "15 is the max limit", and 20 as an upper option [SRC] https://devforum.roblox.com/t/what-is-your-recommended-house-ceiling-height/1260037
  - A house tutorial says to leave room "to move the camera freely (not having a very low ceiling)" [SRC] https://devforum.roblox.com/t/ruskis-tutorial-2-how-to-design-a-simple-house/330237
- **Walls:**
  - Roblox greybox sample: "every wall at least 10 studs tall" (taller than the 5-stud default jump) [SRC] https://create.roblox.com/docs/tutorials/curriculums/environmental-art/greybox-your-environment
  - The house tutorial keeps "the walls .7 studs thick" and overhangs the roof 1–2 studs plus 1 stud of shingle [SRC] https://devforum.roblox.com/t/ruskis-tutorial-2-how-to-design-a-simple-house/330237
- **Modular grids in official samples:**
  - Modern City kit: 7.5-stud increments [SRC] https://create.roblox.com/docs/tutorials/use-case-tutorials/modeling/assemble-modular-environments
  - Beyond the Dark station: 16-stud grid [SRC] https://create.roblox.com/docs/resources/beyond-the-dark/building-architecture
  - Battle Royale build system: cells 20x16x20, walls 20x16x1, floors 20x1x20 [SRC] https://create.roblox.com/docs/resources/battle-royale/building-system
- **Stairs and step-up:**
  - Humanoids walk onto ledges up to about 2.5 studs without jumping. Lowering HipHeight reduces this [SRC] https://devforum.roblox.com/t/how-to-change-the-maximum-height-that-an-object-can-be-so-that-a-humanoid-can-still-walk-over-it/1544732
  - There is no step-height property. The workarounds are HipHeight or invisible wedge ramps over steps [SRC] https://devforum.roblox.com/t/how-to-change-a-players-step-height/2739025
  - R15 struggles on stairs where R6 physics climbs cleanly [UNVERIFIED: snippet]
- **Furniture:** No Roblox-specific furniture chart was found.
  - A non-Roblox (Second Life) forum gives 0.75 m seat and 1.25 m table [UNVERIFIED: snippet, odd numbers, ignore]
  - Chairs get awkward if R6 legs are made to reach the floor [UNVERIFIED: snippet of 2200910]

### Real-world references used for conversion
- US IRC stairs: riser ≤ 7¾ in (196 mm), tread ≥ 10 in (254 mm), width ≥ 36 in, handrail 34–38 in, headroom ≥ 6'8" [SRC] https://timnath.org/wp-content/uploads/2022/03/2018-RESIDENTIAL-STAIR-GUIDE.pdf and https://www.KnoxCounty.org/codes/pdfs/construction_info/Stairs.pdf
- Guards 36 in residential / 42 in commercial-IBC [UNVERIFIED: not in the fetched code guides; the 42 in apartment figure comes from a snippet]

### Proposed set for this map
These are [DERIVED] values. Vertical sizes follow 0.28 m/stud to match the door. Horizontal sizes are widened for the 4-stud R6 and the third-person camera.

| Element | Real-world | @0.28 | Community/official | **Proposed (studs)** |
|---|---|---|---|---|
| Interior door | 0.91 x 2.03 m | 3.3 x 7.3 | 5–6 x 7.5–8 (snippet), 5 x 10 | **4.6 x 7.4 x 0.5 (fixed)** |
| Double / shop door | 1.8 x 2.1 m | 6.5 x 7.5 | n/a | **8.6–9.2 W x 7.4 H** (two leaves) |
| Garage door (1 car) | 2.7 x 2.1 m | 9.8 x 7.6 | n/a | **11–12 W x 8–8.5 H** (Roblox cars are oversize, see §4) |
| Floor-to-ceiling, home | 2.4–2.7 m | 8.6–9.6 | 8 "claustrophobic", 10–12 suggested | **10** (header above door = 2.6) |
| Floor-to-ceiling, office/shop | 2.7–3.0 m | 9.6–10.7 | 12–15 | **11–12** |
| Ground-floor retail / lobby | 3.5–4.5 m | 12.5–16 | 15 "max" for houses | **14–16** |
| Floor slab | 0.2–0.3 m | 0.7–1.1 | n/a | **1** |
| Floor-to-floor (storey) | 2.9–3.1 m apt, 3.5–4 m office | 10.4–14.3 | n/a | **11 residential, 13 office, 16 ground retail** |
| Exterior wall | 0.2–0.35 m | 0.7–1.25 | 0.7 (tutorial) | **1.0** (≥ 0.4 for camera, see §3) |
| Interior partition | 0.10–0.15 m | 0.4–0.5 | n/a | **0.5** (matches door thickness) |
| Window sill, home | 0.8–0.9 m | 2.9–3.2 | "suitable height for a player looking through" | **2.8–3.2** (R6 eyes ≈ 4.5) |
| Window head | aligned with door head | 7.3 | n/a | **7.4** (align with door) |
| Storefront sill | 0.3–0.6 m | 1–2 | n/a | **1–1.5** |
| Stair riser | ≤ 0.196 m | ≤ 0.7 | humanoid steps ≤ ~2.5 | **0.6–0.7** (11-stud storey = 16 × 0.6875) |
| Stair tread | ≥ 0.254 m | ≥ 0.9 | n/a | **1.0–1.2** (R6 foot is 1 deep) |
| Stair width | ≥ 0.91 m | ≥ 3.3 | n/a | **5–6** (R6 is 4 wide; 8+ for two abreast) |
| Stair headroom | ≥ 2.03 m | ≥ 7.3 | n/a | **≥ 7.4** |
| Handrail | 0.86–0.97 m | 3.1–3.5 | none found | **3.0** |
| Guard / balcony rail | 0.91–1.07 m | 3.3–3.8 | none found | **3.0–3.5** (R6 hips at 2, shoulders at 4) |
| Hallway, home | 0.9–1.1 m | 3.3–4 | 10 (greybox sample) | **6 min, 7–8 typical** |
| Corridor, public/office | 1.5–2.4 m | 5.4–8.6 | 10 (greybox) | **8–10** (two R6s pass at ≥ 8.5) |
| Kitchen counter | 0.91 m | 3.25 | none | **3.0** (2.6 if proportioned to R6 height) |
| Dining table | 0.74 m | 2.6 | none | **2.4–2.6** |
| Chair seat | 0.45 m | 1.6 | legs-to-floor awkward | **1.5–2.0** (R6 has no knees; seated legs stick straight out) |
| Bar counter / stool | 1.07 m / 0.76 m | 3.8 / 2.7 | none | **3.6 / 2.6** |
| Bed top | 0.5–0.65 m | 1.8–2.3 | none | **1.8–2.0**; single **5 x 8**, double **7 x 8**, queen **8 x 8.5** (R6 is 4 wide and 5 long) |
| Smallest room (WC) | 1.5 x 2 m | 5 x 7 | n/a | **≥ 8 x 8** for camera |
| Bedroom / living | 3x3.5 / 4x5 m | 11x12.5 / 14x18 | n/a | **≥ 14 x 14 / 18–24** |

---

## 3. Camera (third and first person)

- **Poppercam is the default occlusion mode.** It is "the feature that prevents the camera from clipping through walls" [SRC] https://devforum.roblox.com/t/smooth-zoom-poppercam-are-coming/196318 (snippet; thread not fetched)
- Players' min/max zoom are set by `CameraMinZoomDistance` / `CameraMaxZoomDistance`. Setting both to the same value locks zoom [SRC] https://create.roblox.com/docs/workspace/camera
- A later update clamps zoom to that range "regardless of poppercam" [UNVERIFIED: snippet]
- Defaults: min 0.5 [UNVERIFIED: forum code comment]. Max 400 on the Player, possibly 128 on StarterPlayer [UNVERIFIED: conflicting].
- Default starting zoom is about 12.5 studs [UNVERIFIED: commonly quoted, not confirmed in any fetched source].
- **Thin walls let the camera clip.** It pushed through parts 0.2–0.4 studs thick because the near plane is 0.1 while the cutoff logic assumed 0.5. Staff said the bug would be fixed; walls ≥ 0.4 never clipped [SRC] https://devforum.roblox.com/t/camera-clipping-into-parts-with-thickness-04/35461
- Other suggested fixes: two-layer walls, setting `DevCameraOcclusionMode` to Zoom, and raycast zoom limits [UNVERIFIED: snippets] https://devforum.roblox.com/t/3rd-person-camera-clipping-wall/2880287
- **No source gives a minimum room or hallway size for the camera.** My inference [DERIVED]:
  - Poppercam pulls the camera in front of any wall closer than the zoom distance. A 6-stud hallway viewed from behind therefore puts the camera about 2–3 studs behind the head.
  - A **10-stud ceiling** keeps the orbiting camera (pivot at head, about 4.5 studs up) from hitting the ceiling at normal pitch.
  - Rooms **≥ 12–14 studs** deep let the camera sit near its default distance.
  - Keep **all walls ≥ 0.5 studs**. The owner's 0.5 door is fine.
  - Avoid thin decorative parts with CanQuery on near head height in hallways; they make the camera pop.
- **First person** [DERIVED from R6 geometry]:
  - Eye height is about 4.5 studs (HRP centre at 3 + head centre 1.5 above it). That is 1.26 m at 0.28, so the world reads as "child-height".
  - Window sills ≤ 3.2, counters ≤ 3 and rails ≤ 3.5 all stay below the eye line.
- **R6 collision** [UNVERIFIED: general engine knowledge, check in Studio]. Only Torso/Head (and the 2x2x1 HumanoidRootPart) collide for R6. Arms and legs are non-collidable, so the physical width is 2 studs. A 4.6 door is easy to pass physically. Visually the arms clear the jamb by only 0.3 per side.

---

## 4. Outdoor scale

### Roads
- One lane is 16 studs: "The scale must be consistent and make sense with a lane width of ~16 studs (It should fit with some extra room)" [SRC] https://devforum.roblox.com/t/car-modelers-wanted/14945
- A reply in the same thread: "I tend to use widths of around 20 (give or take some) because that fits better with the character size." [SRC] (same URL)
- "each lane should be roughly 1.5x the size of a car" and "a road needs to be 4x or 5x times wider than the character" [SRC] https://devforum.roblox.com/t/question-about-road-sizes/490325
- A road tutorial used a road surface 16 wide x 0.3 thick, lines 0.6 wide, and a sidewalk 4 wide. Note it is one creator's choice, and 4 is narrow for R6 [SRC] https://devforum.roblox.com/t/how-to-create-roads/1465262
- Road lines at 1 stud = 1 ft: dashes about 4–5 ft long with 6–7 ft gaps [SRC] https://devforum.roblox.com/t/tips-on-constructing-roads/604495
- "most robbloxians don't know how to stay in their lane. Wide roads are fine." [SRC] https://devforum.roblox.com/t/seeking-opinions-in-building-location-and-placement-road-size/3099246
- A bus-sim developer's real 7 m street looked right only after widening it to 105–110%. Advice in the thread: size the vehicle to the dummy, then the road to the vehicle [SRC] https://devforum.roblox.com/t/scaling-the-city-how-streets-should-be-made/1067805
- Real urban lanes: NACTO says "10 feet generally provide adequate safety in urban settings". Wider lanes are for truck and transit routes [SRC] https://nacto.org/publication/urban-street-design-guide/street-design-elements/lane-width/

### City blocks
- One builder settled on 256 x 128-stud blocks. Another warned that one building in a 256 block makes "the players character … seem like an ant" [SRC] https://devforum.roblox.com/t/how-should-i-layout-my-city-blocks/357068

### Vehicles
- **No published A-Chassis default dimensions.** The repo README has none [SRC] https://github.com/lisphm/A-Chassis
- An A-Chassis weight-brick example is 5 W x 8 H x 17 L [UNVERIFIED: search snippet only]
- **Roblox cars are effectively built at "lane ≈ 16".** At 1.5x a car per lane (Jontizm), a car is about 10–11 studs wide [DERIVED]. That is wider than true 0.28 scale, where a 1.85 m sedan is 6.6 studs.
- **R6 forces wide cars.** Two seated 4-wide R6s side by side need ≥ 8 studs of cabin, so realistic-RP cars usually run 7.5–9 studs wide [DERIVED; UNVERIFIED for specific games].

### Not found
- No sourced Roblox numbers for curb height, parking stalls or streetlight height. Real-world references for these are converted in the table below [UNVERIFIED for real-world parking, curb and light figures; standard US practice, not fetched].

### Proposed outdoor set
These are [DERIVED] values, keeping the 0.28 vertical scale and widening for R6 and Roblox driving.

| Element | Real-world | @0.28 | Community | **Proposed (studs)** |
|---|---|---|---|---|
| Travel lane | 3.0–3.6 m | 10.7–12.9 | 16, ~20, 1.5x car | **14** city street, **16** arterial/highway |
| Parking lane (parallel) | 2.1–2.6 m | 7.5–9.3 | n/a | **10** |
| Sidewalk | 1.5–3 m (5–10 ft) | 5.4–10.7 | 4 (tutorial) | **8 min, 10–12 downtown** |
| Curb height | 0.15 m (6 in) | 0.54 | n/a | **0.5–0.6** (humanoids step it automatically; easy for cars) |
| Sedan (L x W x H) | 4.8 x 1.85 x 1.45 m | 17 x 6.6 x 5.2 | n/a | **18–20 x 7.5–8.5 x 5.5–6** |
| SUV / pickup | 5.2–5.9 x 2.0 x 1.8–1.9 m | 18.5–21 x 7.1 x 6.6 | n/a | **20–23 x 8.5–9 x 7** |
| Police/ambulance van, box truck | 6–8 m long | 21–29 | n/a | **24–30 long, 9–10 wide, 9–11 tall** |
| Parking stall (90°) | 2.6–2.75 x 5.5 m | 9.3–9.8 x 19.6 | n/a | **11–12 x 22** |
| Parking aisle (two-way) | 7.3 m (24 ft) | 26 | n/a | **26–30** |
| Streetlight, residential | 4.5–6 m | 16–21 | none found | **18–22** |
| Streetlight, arterial | 9–12 m | 32–43 | none found | **30–36** |
| Traffic-signal clearance | ≥ 4.6–5.2 m | 16.5–18.5 | n/a | **17–18** |
| Building storey | see §2 | 11 / 13 | n/a | 5-storey apartment ≈ **55 + 2 parapet** |

---

## 5. Published scale guides or reference sheets

- **No Roblox-wide R6 scale chart exists** on the DevForum, Creator Docs or in the RP-game communities I could reach. The closest material:
  - Roblox Units doc (0.28 m) https://create.roblox.com/docs/physics/units
  - Units on Roblox announcement https://devforum.roblox.com/t/units-on-roblox/2418615
  - Avatar Settings heights https://create.roblox.com/docs/studio/avatar-settings
  - Greybox curriculum (10-stud doorways and walls) https://create.roblox.com/docs/tutorials/curriculums/environmental-art/greybox-your-environment
  - Modern City 7.5-stud kit https://create.roblox.com/docs/tutorials/use-case-tutorials/modeling/assemble-modular-environments
  - "Studify" and a "Studs Calculator" plugin do meter-to-stud conversion only. The calculator is marked broken [SRC] https://devforum.roblox.com/t/studify-easily-convert-studs-to-real-world-metrics/1895364 and https://devforum.roblox.com/t/studs-calculator/188991
- **Method for the named RP games:**
  - Screenshot a game whose scale you like next to your own (known-height) character, then measure lengths relative to it [SRC] https://devforum.roblox.com/t/scaling-the-city-how-streets-should-be-made/1067805
  - Do this in ER:LC, Southwest Florida and Greenville with an R6 avatar to replace the [DERIVED] vehicle and road numbers above.

---

## Where the 7.4-stud door conflicts with common advice

- **Height: compatible.** 7.4 sits at the bottom of the community 7.5–8 range and equals a real door at the official 0.28 m/stud. It is only a problem if Rthro/R15 scaling is ever enabled; one source advises 10 tall for that.
- **Width: narrower than advised.** 4.6 is below the community 5–6 and far below the 10-stud greybox sample. It leaves 0.3 studs per side for R6 arms. Physically fine (torso collision is 2 wide). Visually tight, and the camera pops forward when following a player through. Double doors, shop entrances and public corridors should be wider than real-world proportion suggests.
- **Ceilings must rise with it.** An 8-stud ceiling, which one poster already called claustrophobic, would leave a 0.6-stud header over a 7.4 door. Use **≥ 9.5–10** so the header looks real (about 0.7 m at 0.28) and the camera has room.
- **Mixed scale is unavoidable.** Building every width at 0.28 m would give 3.3-stud stairs, 3.3-stud hallways, 3.5-stud twin beds and 6.6-stud-wide cars, all too small for a 4-stud-wide R6. Keep **heights at 0.28 m/stud** and size **widths and clearances to the R6 body**:
  - widths ≥ R6 + 1 (5+)
  - two-person passages ≥ 8.5
  - furniture footprints ≥ 4–5 wide
  - vehicles 7.5–9 wide on 14–16-stud lanes.

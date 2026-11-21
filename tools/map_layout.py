"""Alamo County map layout v2 - realistic street network. Single source for the 2D sketch AND Studio placement.

    python tools/map_layout.py      -> plans/map/layout.json   (then: python tools/render_map.py)

Studs. Map space: x west->east, z north->south. Playable city 0..3072, scenery ring -512..3584 (4096 x 4096 =
4 default 2048-stud baseplates). Studio world position = (x - 1536, 0, z - 1536).

What makes it read like a real Southwest city:
  - Camino Real (old Route 66) bends through town; Alameda Ave / Dyer St is an old diagonal highway cutting
    SW->NE across the grid, making a Five Points junction and the triangular spawn park.
  - I-66 freeway on the north edge with a diamond interchange at Mesa Blvd; Dyer St merges onto it.
  - Foothill Blvd curves along the mountains; River Rd follows the river; Valley Rd runs along the south.
  - Arroyo Seco (concrete channel) cuts across the south: only Mesa, Foothill, River Rd and the rail line bridge it.
  - The rail line runs N-S beside downtown with grade crossings.
  - Each district has its own street pattern: tight downtown grid, 1960s long blocks (Northside), curving
    subdivision with cul-de-sacs (Westside), a barrio grid rotated to the diagonal with alleys (Southside),
    a wide grid of fourplexes (War Zone), big industrial blocks, winding rural lanes (South Valley, Ranch Road).
"""
import json
import math
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon, box, mapping
from shapely.ops import unary_union, nearest_points
from shapely import affinity

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "plans" / "map"
S = json.loads((ROOT / "standards" / "sizes.json").read_text(encoding="utf-8"))
PLAY, RING = 3072, 512
LO, HI = -RING, PLAY + RING
LANE = S["roads"]["lane"]

CLASS = {   # curb-to-curb (ctc) and sidewalk each side, from the sizing standard
    "freeway": dict(ctc=4 * 16 + 2 * 12, sidewalk=0, desc="I-66, 2+2 lanes x16, 12 shoulders, elevated"),
    "ramp": dict(ctc=22, sidewalk=0, desc="1 lane + shoulders"),
    "arterial": dict(ctc=6 * LANE + 16, sidewalk=10, desc="3+3 lanes x14, 16 landscaped median"),
    "avenue": dict(ctc=4 * LANE + 14, sidewalk=10, desc="2+2 lanes x14, 14 centre turn lane"),
    "collector": dict(ctc=2 * LANE + 2 * 10, sidewalk=8, desc="1+1 lanes, parking both sides"),
    "local": dict(ctc=36, sidewalk=8, desc="2-way, no lines"),
    "lane": dict(ctc=30, sidewalk=6, desc="narrow barrio street"),
    "alley": dict(ctc=18, sidewalk=0, desc="dirt / broken asphalt"),
    "rural": dict(ctc=28, sidewalk=0, desc="1+1, dirt shoulders"),
}
for c in CLASS.values():
    c["row"] = c["ctc"] + 2 * c["sidewalk"]

roads, specials, lots, notes = [], [], [], []


# ------------------------------------------------------------------ helpers
def bez(p0, p1, p2, p3, n=24):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def smooth(pts, r=0.18, n=8):
    """Round the corners of a polyline (Chaikin-style) so arterials bend instead of kinking."""
    if len(pts) < 3:
        return pts
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        p = (b[0] + (a[0] - b[0]) * r, b[1] + (a[1] - b[1]) * r)
        q = (b[0] + (c[0] - b[0]) * r, b[1] + (c[1] - b[1]) * r)
        out += bez(p, b, b, q, n)[0:]
    out.append(pts[-1])
    return out


def road(rid, name, cls, pts, bridge_ok=False, **kw):
    roads.append(dict(id=rid, name=name, cls=cls, pts=[(round(x, 1), round(z, 1)) for x, z in pts], **kw))


def rect(cx, cz, w, d, ang=0.0):
    return affinity.rotate(box(cx - w / 2, cz - d / 2, cx + w / 2, cz + d / 2), ang, origin=(cx, cz))


def poly_pts(p):
    return [(round(x, 1), round(z, 1)) for x, z in list(p.exterior.coords)[:-1]]


def special(sid, name, kind, district, lot_poly, bldg=None, h=0, stories=1, num=None, **kw):
    rec = dict(id=sid, name=name, kind=kind, district=district, poly=poly_pts(lot_poly))
    if bldg is not None:
        rec["bldg"] = dict(poly=poly_pts(bldg), h=h, stories=stories)
    if num:
        rec["num"] = num
    rec.update({k: (poly_pts(v) if isinstance(v, Polygon) else v) for k, v in kw.items()})
    specials.append(rec)
    return rec


# ------------------------------------------------------------------ 1. boundary + major roads
road("i66", "I-66", "freeway", [(LO, 170), (HI, 170)])
road("ramp_sw", "I-66 ramp", "ramp", bez((1380, 222), (1520, 236), (1600, 270), (1638, 318)))
road("ramp_se", "I-66 ramp", "ramp", bez((2020, 222), (1880, 236), (1800, 270), (1752, 318)))
road("ramp_nw", "I-66 ramp", "ramp", bez((1380, 118), (1520, 104), (1600, 70), (1638, 20)))
road("ramp_ne", "I-66 ramp", "ramp", bez((2020, 118), (1880, 104), (1800, 70), (1752, 20)))

road("mesa", "Mesa Blvd", "arterial", smooth([(1695, -60), (1695, 700), (1690, 1250), (1690, 1590), (1700, 2200),
                                             (1715, 2560), (1730, 3040)]))
CAMINO = smooth([(70, 1762), (500, 1736), (920, 1688), (1200, 1622), (1450, 1594), (1690, 1590),
                 (2100, 1590), (2450, 1560), (2750, 1500), (2945, 1478)])
road("camino", "Camino Real (old Route 66)", "arterial", CAMINO)
road("foothill", "Foothill Blvd", "avenue", smooth([(2600, 222), (2820, 380), (2930, 700), (2960, 1050), (2945, 1478),
                                                     (2985, 1800), (2900, 2150), (2720, 2550), (2520, 2850),
                                                     (2300, 3045)], r=0.3))
road("river", "River Rd", "collector", smooth([(85, 222), (62, 600), (110, 1000), (72, 1400), (70, 1762),
                                              (118, 2150), (92, 2550), (160, 2900), (260, 3045)], r=0.35))
road("valley", "Valley Rd", "rural", smooth([(260, 3045), (900, 3010), (1730, 3040), (2300, 3045)], r=0.3))
# the old diagonal highway: Alameda Ave (SW) -> Five Points -> Dyer St (NE) -> merges onto I-66
FIVE = (920, 1688)
road("alameda", "Alameda Ave", "avenue", [(105, 2752), FIVE])
DIAG_END = (1690, 820)      # where Dyer St crosses Mesa Blvd
road("dyer", "Dyer St", "avenue", [FIVE, DIAG_END] + bez(DIAG_END, (2040, 440), (2180, 300), (2330, 224))[1:])

RAIL = smooth([(2200, LO), (2200, 700), (2195, 1590), (2210, 2400), (2240, PLAY + 40), (2260, HI)], r=0.3)
ARROYO = smooth([(HI, 2200), (3050, 2300), (2600, 2420), (2150, 2480), (1700, 2520), (1250, 2600), (800, 2700),
                 (400, 2820), (0, 2930), (LO, 2985)], r=0.35)
RIVER = [(-230 + 70 * math.sin(i / 6.0), LO + i * (HI - LO) / 40) for i in range(41)]

# ------------------------------------------------------------------ 2. DOWNTOWN grid (east of Mesa, west of rail)
RR_X = 2150
road("railroad", "Railroad Ave", "local", [(RR_X, 330), (RR_X, 2400)])
for nm, z in (("Gold Ave", 1080), ("Silver Ave", 1340), ("Lead Ave", 1840), ("Coal Ave", 2080)):
    road(nm.split()[0].lower(), nm, "local", [(1750, z), (RR_X, z)])
road("uptown", "Uptown Ave", "local", [(1750, 640), (RR_X, 640)])

# ------------------------------------------------------------------ 3. NORTHSIDE 1960s long blocks (Ash St -> Mesa, above the diagonal)
ASH = 700
road("ash", "Ash St", "collector", [(ASH, 222), (ASH, 1690)])
road("menaul", "Menaul Ave", "collector", [(ASH, 700), (1665, 700)])
DIAG = LineString([FIVE, DIAG_END])


def to_diag_x(z):     # x where the Dyer diagonal crosses a given z
    return FIVE[0] + (FIVE[1] - z) * ((DIAG_END[0] - FIVE[0]) / (FIVE[1] - DIAG_END[1]))


for i, z in enumerate((440, 960, 1220, 1480)):     # 260 apart: two 105-deep lots back to back
    xe = 1665 if z <= DIAG_END[1] else to_diag_x(z) - 30
    if xe - ASH > 120:
        road(f"north_l{i}", f"{['Aspen', 'Birch', 'Cedar', 'Elm', 'Fir', 'Hazel', 'Ivy'][i]} Ave", "local", [(ASH + 32, z), (xe, z)])
for i, x in enumerate((1000, 1340)):
    zs = min(1640, FIVE[1] - (x - FIVE[0]) * ((FIVE[1] - DIAG_END[1]) / (DIAG_END[0] - FIVE[0]))) - 30
    road(f"north_n{i}", ["Pinon St", "Sage St"][i], "local", [(x, 222 + 44), (x, zs)])

# ------------------------------------------------------------------ 4. WESTSIDE curving subdivision + cul-de-sacs
W1 = bez((75, 520), (300, 360), (480, 780), (ASH - 32, 640), 40)
W2 = bez((82, 1180), (330, 1330), (480, 900), (ASH - 32, 1060), 40)
road("coyote", "Coyote Trail", "collector", W1)
road("mesaverde", "Mesa Verde Dr", "local", W2)
road("sunset", "Sunset Loop", "local", bez((280, 660), (120, 820), (380, 960), (500, 830), 30))
road("quail", "Quail Run", "local", bez((500, 830), (590, 1250), (300, 1420), (100, 1440), 30))
culdesacs = []
for base, every, side_flip in ((W1, 6, 1), (W2, 7, -1)):
    ls = LineString(base)
    for k, d in enumerate(range(130, int(ls.length) - 100, 150)):
        p, p2 = ls.interpolate(d), ls.interpolate(d + 2)
        tx, tz = p2.x - p.x, p2.y - p.y
        nl = math.hypot(tx, tz) or 1
        nx, nz = -tz / nl, tx / nl
        s = 1 if k % 2 == 0 else -1
        end = (p.x + nx * s * 120, p.y + nz * s * 120)
        stub = LineString([(p.x + nx * s * 30, p.y + nz * s * 30), end]).buffer(34)
        others = [LineString(r["pts"]) for r in roads if r["pts"] != [(round(x, 1), round(z, 1)) for x, z in base]]
        if any(stub.intersects(o) for o in others) or any(stub.intersects(LineString(c[0]).buffer(34)) for c in culdesacs):
            continue
        if not (100 < end[0] < ASH - 60 and 260 < end[1] < 1460):
            continue
        culdesacs.append(([(p.x, p.y), end], end))

# ------------------------------------------------------------------ 5. SOUTHSIDE barrio - grid rotated to Alameda, with alleys
BARELAS_X = 1300
road("barelas", "Barelas St", "local", [(BARELAS_X, 1650), (BARELAS_X, 2560)])
BARRIO = Polygon([(900, 1755), (BARELAS_X - 28, 1690), (BARELAS_X - 28, 2570), (800, 2665), (420, 2780), (150, 2850),
                  (140, 2700)]).difference(LineString(ARROYO).buffer(70))
BARRIO = max(getattr(BARRIO, "geoms", [BARRIO]), key=lambda g: g.area)
ux, uz = (FIVE[0] - 105) / math.dist(FIVE, (105, 2752)), (FIVE[1] - 2752) / math.dist(FIVE, (105, 2752))
vx, vz = -uz, ux          # perpendicular, pointing SE into the barrio
if vx < 0:
    vx, vz = -vx, -vz


def clipped_lines(geom_line, region):
    g = geom_line.intersection(region)
    if g.is_empty:
        return []
    parts = [g] if g.geom_type == "LineString" else list(getattr(g, "geoms", []))
    return [list(p.coords) for p in parts if p.length > 90]


barrio_streets, barrio_alleys = [], []
for k in range(1, 5):     # streets parallel to Alameda, 220 apart, alley halfway
    off = k * 220
    a = (105 + vx * off - ux * 600, 2752 + vz * off - uz * 600)
    b = (FIVE[0] + vx * off + ux * 600, FIVE[1] + vz * off + uz * 600)
    barrio_streets += clipped_lines(LineString([a, b]), BARRIO)
    off2 = off - 110      # alley halfway between
    a = (105 + vx * off2 - ux * 600, 2752 + vz * off2 - uz * 600)
    b = (FIVE[0] + vx * off2 + ux * 600, FIVE[1] + vz * off2 + uz * 600)
    barrio_alleys += clipped_lines(LineString([a, b]), BARRIO)
for k in range(1, 7):     # cross streets perpendicular to Alameda
    s0 = k * 250
    a = (105 + ux * s0 - vx * 50, 2752 + uz * s0 - vz * 50)
    b = (a[0] + vx * 1400, a[1] + vz * 1400)
    barrio_streets += clipped_lines(LineString([a, b]), BARRIO)
for i, pts in enumerate(barrio_streets):
    road(f"barrio_s{i}", f"Barrio St {i + 1}", "lane", pts)
for i, pts in enumerate(barrio_alleys):
    road(f"barrio_a{i}", "alley", "alley", pts)

# ------------------------------------------------------------------ 6. SOUTH VALLEY rural lanes (west of Alameda) + graveyard
road("camposanto", "Camposanto Rd", "rural", smooth([(85, 2140), (300, 2150), (520, 2120), (628, 2140)], r=0.4))
road("isleta", "Isleta Ln", "rural", smooth([(95, 2440), (220, 2420), (360, 2450)], r=0.4))
road("acequia", "Acequia Rd", "rural", bez((300, 2150), (330, 2280), (260, 2380), (220, 2420), 16))

# ------------------------------------------------------------------ 7. EASTSIDE: industrial blocks, War Zone grid, Ranch Road
road("commerce", "Commerce Rd", "collector", [(RR_X, 1000), (2958, 1000)])
road("dock1", "Dock St", "local", [(2450, 1030), (2450, 1440)])
road("dock2", "Kiln St", "local", [(2700, 1000), (2700, 720)])
road("ranch", "Ranch Road", "rural", smooth([(2932, 720), (3060, 690), (3180, 610), (3280, 520), (3360, 470)], r=0.4))
road("corrales", "Corrales Ln", "rural", smooth([(2240, 420), (2450, 470), (2650, 430), (2850, 470), (2885, 520)], r=0.4))
road("trotter", "Trotter Ln", "rural", smooth([(2450, 470), (2470, 620), (2560, 680)], r=0.4))
FOOT = LineString([p for p in roads if p["id"] == "foothill"][0]["pts"])
ARR = LineString(ARROYO)
for i, z in enumerate((1770, 2010, 2250)):
    far = LineString([(RR_X, z), (3100, z)])
    xe = min(far.intersection(FOOT).x if not far.intersection(FOOT).is_empty else 2900, 2950) - 40
    road(f"wz_l{i}", f"{['Kathryn', 'Trumbull', 'Zuni'][i]} Ave", "local", [(RR_X, z), (xe, z)])
for i, x in enumerate((2450, 2700)):
    zl = LineString([(x, 1560), (x, 2700)]).intersection(ARR)
    road(f"wz_n{i}", ["Utah St", "Texas St"][i], "local", [(x, 1600), (x, (zl.y if not zl.is_empty else 2380) - 50)])

# ------------------------------------------------------------------ 8. VALLEY (south of the arroyo)
road("bridge_st", "Bridge St", "local", [(1755, 2800), (2150, 2800)])
road("mhp_loop", "Mobile home loop", "alley", [(1800, 2860), (2150, 2860), (2150, 2990), (1800, 2990), (1800, 2860)])
road("valley_l", "Chamisa Ln", "rural", smooth([(700, 3020), (760, 2880), (1000, 2810), (1300, 2790), (1690, 2780)], r=0.4))

for i, (pts, end) in enumerate(culdesacs):
    road(f"cds{i}", "cul-de-sac", "local", pts, bulb=[round(end[0], 1), round(end[1], 1)])

# ------------------------------------------------------------------ 9. buildings + sites (lots are drawn around the buildings)
# spawn park = the triangle between Camino Real, Mesa Blvd and Dyer St
rbuf = {r["id"]: LineString(r["pts"]).buffer(CLASS[r["cls"]]["row"] / 2 + 2) for r in roads}
tri = Polygon([FIVE, (1690, 900), (1690, 1590)] + [p for p in CAMINO if FIVE[0] < p[0] < 1690][::-1])
park = tri.difference(unary_union([rbuf["mesa"], rbuf["camino"], rbuf["dyer"]])).buffer(-4)
park = max(getattr(park, "geoms", [park]), key=lambda g: g.area)
special("spawn_park", "SPAWN - Triangle Plaza Park", "park", "Downtown", park,
        features=["central fountain plaza + 4 spawn pads under shade canopies", "gazebo/bandstand", "map + job kiosk",
                  "basketball court", "playground", "palm + cottonwood groves, gravel xeriscape beds",
                  "bus stops on Camino Real and Mesa Blvd", "restroom shell"])

DT = "Downtown"
x0, x1 = 1750 + 4, RR_X - 26 - 4          # between Mesa sidewalk and Railroad Ave
# block Gold-Silver
special("court", "Court Building", "interior", DT, box(x0, 1106, x0 + 220, 1314), box(x0 + 20, 1130, x0 + 200, 1250), 46, 3, 4)
special("post", "Post Office", "interior", DT, box(x0 + 230, 1106, x1, 1314), box(x0 + 245, 1135, x0 + 345, 1225), 18, 1, 5,
        extras=["mail-truck lot + dock at rear"])
# block Silver-Camino
special("police", "Police Station", "interior", DT, box(x0, 1366, x0 + 235, 1528), box(x0 + 15, 1380, x0 + 175, 1480), 28, 2, 6,
        extras=["sally port + secure lot", "fire lane at entrance"])
special("music", "Music Studio", "interior", DT, box(x0 + 245, 1366, x1, 1528), box(x0 + 260, 1385, x0 + 350, 1465), 26, 2, 15,
        extras=["old brick building by the tracks", "live room, 2 booths, control room, lounge", "alley load-in door"])
# block Camino-Lead
special("gas", "Gas Station", "interior", DT, box(x0, 1652, x0 + 200, 1814), box(x0 + 110, 1720, x0 + 190, 1790), 18, 1, 3,
        canopy=box(x0 + 15, 1665, x0 + 105, 1720), extras=["6 pumps", "price pylon at corner"])
special("conv", "Convenience Store", "interior", DT, box(x0 + 210, 1652, x1, 1814), box(x0 + 230, 1700, x0 + 330, 1780), 17, 1, 2)
# block Lead-Coal
special("gun", "Gun Shop", "interior", DT, box(x0, 1866, x0 + 160, 2054), box(x0 + 20, 1900, x0 + 110, 2010), 18, 1, 1,
        extras=["barred windows", "range at rear"])
special("gym", "Gym", "interior", DT, box(x0 + 170, 1866, x1, 2054), box(x0 + 185, 1880, x0 + 340, 2030), 24, 1, 8)
# south-west of the main intersection: strip mall + fast food between Barelas St and Mesa
special("strip_mall", "Strip mall", "interior", DT, box(BARELAS_X + 30, 1652, 1626, 1900),
        box(BARELAS_X + 40, 1815, 1616, 1890), 20, 1,
        bays=[["Clothing Shop", 110, 10], ["Hair Shop", 55, 11], ["Tattoo Shop", 55, 12], ["Laundromat", 56, None]],
        extras=["parking in front", "fire lane along storefronts", "tow-away signs"])
special("fastfood", "Fast Food", "interior", DT, box(1450, 1930, 1626, 2100), box(1500, 1975, 1570, 2035), 16, 1, 9,
        extras=["drive-thru lane loop", "menu board", "pylon sign"])
# Eastside / Ranch Road / Valley
special("warehouse", "Warehouse", "interior", "Eastside", box(2245, 1030, 2420, 1440), box(2260, 1100, 2400, 1400), 34, 1, 13,
        extras=["6 docks on the rail spur", "truck court"])
special("prison", "Prison", "interior", "Ranch Road", box(3300, 300, 3560, 720), box(3340, 380, 3520, 560), 30, 2, 7,
        extras=["double fence + razor wire", "4 guard towers", "sally port gate on Ranch Road", "yard"])
special("graveyard", "Graveyard (Camposanto)", "site", "South Valley", box(180, 1835, 560, 2110),
        box(470, 1990, 530, 2060), 22, 1, 14,
        extras=["adobe wall + iron gate on Camposanto Rd", "chapel", "gravel paths", "junipers + cypress", "headstone rows"])
# landmark / filler shells
special("tower", "Alamo Tower (offices)", "landmark", DT, box(1756, 800, 1960, 1054), box(1780, 860, 1900, 980), 160, 12)
special("silos", "Grain silos (landmark)", "landmark", "Eastside", box(2245, 720, 2420, 980), box(2290, 760, 2370, 840), 110, 1)
special("tow", "Tow + impound yard", "yard", "Eastside", box(2470, 1030, 2930, 1250), box(2490, 1050, 2560, 1100), 16, 1)
special("junk", "Junkyard", "yard", "Valley", box(1000, 2850, 1350, 3000), None)
special("truckstop", "Truck stop", "shell", "Valley", box(1760, 2620, 2140, 2770), box(1950, 2650, 2080, 2730), 20, 1,
        canopy=box(1780, 2640, 1920, 2700))
special("mhp", "Mobile home park", "mhp", "Valley", box(1785, 2845, 2165, 3005), None)
special("motel", "Route 66 Motel", "shell", "Westside", box(560, 1480, 780, 1690), box(575, 1500, 765, 1550), 24, 2)
special("grocery", "Grocery big box", "shell", "Westside", box(120, 1500, 520, 1700), box(150, 1520, 450, 1640), 34, 1)
special("church", "Church", "shell", "Southside", box(1450, 2130, 1626, 2330), box(1480, 2160, 1580, 2290), 34, 1)
special("school", "School", "shell", "Northside", box(1030, 262, 1300, 408), box(1050, 280, 1280, 380), 24, 1)
special("ranch1", "Ranch", "ranch", "Ranch Road", box(2260, 260, 2560, 400), box(2380, 300, 2440, 340), 16, 1)
special("ranch2", "Ranch", "ranch", "Ranch Road", box(2620, 480, 2880, 690), box(2700, 560, 2760, 600), 16, 1)
special("ranch3", "Ranch", "ranch", "Ranch Road", box(2240, 490, 2430, 690), box(2300, 560, 2360, 600), 16, 1)

# ------------------------------------------------------------------ 10. auto-fill houses + strip shells along streets
DISTRICTS = {   # polygon, style, frontage, depth, footprint scale
    "Westside": (Polygon([(110, 230), (ASH - 30, 230), (ASH - 30, 1460), (110, 1460)]), "tract", 56, 90),
    "Northside": (Polygon([(ASH + 30, 230), (1665, 230), (1665, DIAG_END[1] - 20), (FIVE[0] - 10, FIVE[1] - 60), (ASH + 30, 1670)]), "ranchhouse", 62, 105),
    "Southside": (BARRIO, "brick", 46, 72),
    "War Zone": (Polygon([(RR_X + 50, 1610), (2960, 1610), (2900, 2150), (2780, 2380), (RR_X + 50, 2440)]), "fourplex", 58, 95),
    "South Valley": (Polygon([(110, 2120), (640, 2120), (300, 2560), (110, 2600)]), "southvalley", 100, 150),
    "Valley": (Polygon([(300, 2900), (1750, 2620), (1750, 3030), (300, 3030)]), "southvalley", 120, 160),
}
blocked = unary_union([LineString(r["pts"]).buffer(CLASS[r["cls"]]["row"] / 2 + 3) for r in roads]
                      + [LineString(RAIL).buffer(26), LineString(ARROYO).buffer(36)]
                      + [Polygon(s["poly"]).buffer(6) for s in specials])
placed = []
FILL_CLASSES = {"local", "lane", "collector", "rural"}
for r in roads:
    if r["cls"] not in FILL_CLASSES:
        continue
    ls = LineString(r["pts"])
    half = CLASS[r["cls"]]["row"] / 2
    for side in (1, -1):
        d = 20.0
        while d < ls.length - 20:
            p, p2 = ls.interpolate(d), ls.interpolate(min(d + 2, ls.length))
            tx, tz = p2.x - p.x, p2.y - p.y
            nl = math.hypot(tx, tz) or 1
            tx, tz = tx / nl, tz / nl
            nx, nz = -tz * side, tx * side
            dist_name = next((n for n, (pg, *_) in DISTRICTS.items() if pg.contains(Point(p.x + nx * (half + 40), p.y + nz * (half + 40)))), None)
            if not dist_name:
                d += 30
                continue
            _, style, fr, dp = DISTRICTS[dist_name]
            cx, cz = p.x + tx * fr / 2 + nx * (half + 4 + dp / 2), p.y + tz * fr / 2 + nz * (half + 4 + dp / 2)
            ang = math.degrees(math.atan2(tz, tx))
            lotp = rect(cx, cz, fr - 2, dp, ang)
            if (DISTRICTS[dist_name][0].contains(lotp.centroid) and not lotp.intersects(blocked)
                    and not any(lotp.intersects(q) for q in placed[-400:])):
                bw, bd = (fr * 0.62, dp * 0.45) if style != "fourplex" else (fr * 0.8, dp * 0.55)
                bcx, bcz = cx - nx * (dp / 2 - bd / 2 - 14), cz - nz * (dp / 2 - bd / 2 - 14)
                lots.append(dict(id=f"h{len(lots)}", kind="house", district=dist_name, style=style, road=r["id"],
                                 poly=poly_pts(lotp), bldg=dict(poly=poly_pts(rect(bcx, bcz, bw, bd, ang)), h=13, stories=1)))
                placed.append(lotp.buffer(-1))
                d += fr
            else:
                d += 12

# commercial strip shells along the busy roads where nothing else stands
COMM = {"camino", "mesa", "alameda", "dyer", "foothill", "menaul", "commerce"}
for r in roads:
    if r["id"] not in COMM:
        continue
    ls = LineString(r["pts"])
    half = CLASS[r["cls"]]["row"] / 2
    for side in (1, -1):
        d = 40.0
        while d < ls.length - 40:
            p, p2 = ls.interpolate(d), ls.interpolate(min(d + 2, ls.length))
            tx, tz = p2.x - p.x, p2.y - p.y
            nl = math.hypot(tx, tz) or 1
            tx, tz = tx / nl, tz / nl
            nx, nz = -tz * side, tx * side
            fr, dp = 130, 140
            cx, cz = p.x + tx * fr / 2 + nx * (half + 4 + dp / 2), p.y + tz * fr / 2 + nz * (half + 4 + dp / 2)
            ang = math.degrees(math.atan2(tz, tx))
            lotp = rect(cx, cz, fr - 4, dp, ang)
            if (Polygon([(0, 0), (PLAY, 0), (PLAY, PLAY), (0, PLAY)]).contains(lotp) and not lotp.intersects(blocked)
                    and not any(lotp.intersects(q) for q in placed)):
                bcx, bcz = cx - nx * (dp / 2 - 36), cz - nz * (dp / 2 - 36)
                lots.append(dict(id=f"c{len(lots)}", kind="shop", district="commercial strip", road=r["id"],
                                 poly=poly_pts(lotp), bldg=dict(poly=poly_pts(rect(bcx, bcz, fr * 0.7, 60, ang)), h=18, stories=1)))
                placed.append(lotp.buffer(-1))
                d += fr
            else:
                d += 20

# ------------------------------------------------------------------ 11. junctions: signals, stops, rail crossings, bridges
def classify(a, b):
    big = {"arterial", "avenue"}
    ca, cb = a["cls"], b["cls"]
    if "freeway" in (ca, cb):
        return None
    if "ramp" in (ca, cb):
        return "signal"
    if ca in big and cb in big | {"collector"} or cb in big and ca in big | {"collector"}:
        return "signal"
    if {"collector"} == {ca, cb}:
        return "allway"
    if ca in {"local", "lane", "rural"} or cb in {"local", "lane", "rural"}:
        return "stop" if (ca not in {"alley"} and cb not in {"alley"}) else None
    return None


junctions = []
geo = [(r, LineString(r["pts"])) for r in roads]
for i in range(len(geo)):
    for j in range(i + 1, len(geo)):
        (ra, la), (rb, lb) = geo[i], geo[j]
        if ra["cls"] == "freeway" or rb["cls"] == "freeway":
            continue
        tol = (CLASS[ra["cls"]]["row"] + CLASS[rb["cls"]]["row"]) / 2 + 4
        if la.distance(lb) > tol:
            continue
        pa, pb = nearest_points(la, lb)
        kind = classify(ra, rb)
        if not kind:
            continue
        pt = ((pa.x + pb.x) / 2, (pa.y + pb.y) / 2)
        if any(math.dist(pt, j2["at"]) < 40 for j2 in junctions):
            continue
        junctions.append(dict(at=[round(pt[0], 1), round(pt[1], 1)], kind=kind, roads=[ra["id"], rb["id"]]))
rail_x, bridges = [], []
for r, ls in geo:
    g = ls.intersection(LineString(RAIL))
    for p in getattr(g, "geoms", [g]):
        if not p.is_empty and p.geom_type == "Point" and r["cls"] != "freeway":
            rail_x.append(dict(at=[round(p.x, 1), round(p.y, 1)], road=r["id"]))
    g = ls.intersection(ARR)
    for p in getattr(g, "geoms", [g]):
        if not p.is_empty and p.geom_type == "Point":
            bridges.append(dict(at=[round(p.x, 1), round(p.y, 1)], road=r["id"], width=CLASS[r["cls"]]["row"]))

# ------------------------------------------------------------------ 12. utilities: streetlights + power poles
lights, poles = [], []
for r, ls in geo:
    c = CLASS[r["cls"]]
    if r["cls"] in ("arterial", "avenue"):
        step, sides = 100, (1, -1)
    elif r["cls"] in ("collector",):
        step, sides = 120, (1,)
    else:
        step, sides = 0, ()
    for side in sides:
        d = 30.0
        while step and d < ls.length:
            p, p2 = ls.interpolate(d), ls.interpolate(min(d + 2, ls.length))
            tx, tz = p2.x - p.x, p2.y - p.y
            nl = math.hypot(tx, tz) or 1
            off = c["ctc"] / 2 + 3
            lights.append([round(p.x - tz / nl * off * side, 1), round(p.y + tx / nl * off * side, 1)])
            d += step
    if r["cls"] in ("local", "lane", "collector", "rural", "alley"):
        d = 40.0
        off = c["row"] / 2 + 3 if r["cls"] != "alley" else 6
        while d < ls.length:
            p, p2 = ls.interpolate(d), ls.interpolate(min(d + 2, ls.length))
            tx, tz = p2.x - p.x, p2.y - p.y
            nl = math.hypot(tx, tz) or 1
            poles.append([round(p.x + tz / nl * off, 1), round(p.y - tx / nl * off, 1)])
            d += 120


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = dict(name="Alamo County", version=2, units="studs", playable=[0, 0, PLAY, PLAY], extents=[LO, LO, HI, HI],
                studio_origin="world = (x - 1536, 0, z - 1536)",
                baseplates="playable 3072 x 3072 (2.25 baseplates); with scenery ring 4096 x 4096 = 4 baseplates",
                road_classes=CLASS, roads=roads, specials=specials, lots=lots, junctions=junctions,
                rail=dict(pts=[(round(x, 1), round(z, 1)) for x, z in RAIL], crossings=rail_x),
                arroyo=dict(pts=[(round(x, 1), round(z, 1)) for x, z in ARROYO], bridges=bridges, width=60),
                river=[(round(x, 1), round(z, 1)) for x, z in RIVER], lights=lights, poles=poles,
                districts={n: poly_pts(v[0]) for n, v in DISTRICTS.items()})
    (OUT / "layout.json").write_text(json.dumps(data), encoding="utf-8")
    from collections import Counter
    cnt = Counter(l["kind"] for l in lots)
    length = Counter()
    for r, ls in geo:
        length[r["cls"]] += ls.length
    print("roads", len(roads), {k: round(v) for k, v in length.items()})
    print("specials", len(specials), "lots", dict(cnt), "junctions", Counter(j["kind"] for j in junctions))
    print("rail crossings", len(rail_x), "bridges", len(bridges), "lights", len(lights), "poles", len(poles))
    print("spawn park area", round(park.area), "sq studs")


if __name__ == "__main__":
    main()

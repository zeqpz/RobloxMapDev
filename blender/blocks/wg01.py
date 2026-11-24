"""Westgate block WG01 (Roblox X 1052..1368, Z -824..-452; Blender x same, y = -Z: 452..824, north = +y).

exec(open(r"<repo>/blender/blocks/wg01.py").read())     with optional globals before exec:
  WG_PASSES = "MTC"        which passes to build (M massing, T trim, C character)
  WG_RENDER = [...]        shot names to render to renders/westgate/wg01/<passes>_<shot>.png
  WG_EXPORT = True         export exports/westgate/wg01/<building>.fbx (no context/ground)

Layout (arterial on the west, I-40 frontage road north, minor streets east + south):
  north half   Sunset Plaza: 7-bay 1970s strip centre (metal mansard, storefronts) facing a 2-row parking lot;
               Top Dog walk-up hot-dog stand on the corner pad
  mid-block    concrete alley with utility poles, dumpsters, service doors
  south half   Desert Rose Motor Lodge: two-storey L (wing A east, wing B south), office + porte-cochere, drained pool,
               courtyard parking; El Sol taqueria on the arterial with a tile porch and painted lettering
Grades: street 2.2, sidewalk/lot 2.8, building floors 3.3 (Roblox Y).
"""
import importlib
import math
import os
import random
import sys

import bpy

REPO = r"C:\Users\CooperHinkel\Documents\ClaudeRoblox\RobloxMapDev"
sys.path.append(os.path.join(REPO, "blender"))
import bkit
import bprops as bp
importlib.reload(bkit)
importlib.reload(bp)
from bkit import Kit

PASSES = globals().get("WG_PASSES", "MTC")
LG, FF = 2.8, 3.3
ST = 2.2                     # street asphalt
rng = random.Random(1)

ASPH = "Asphalt_58585A"
CONC = "Concrete_BDB6A8"
CURBC = "Concrete_A9A397"
MULCH = "Pebble_9E6A4C"
PAINT_W = "SmoothPlastic_E6E3D8"
PAINT_Y = "SmoothPlastic_D8B23A"
PAINT_R = "SmoothPlastic_B03A2E"
PAINT_B = "SmoothPlastic_2F5FA8"


# ====================================================================== scene
def scene():
    sc = bpy.data.scenes.get("WG01") or bpy.data.scenes.new("WG01")
    bpy.context.window.scene = sc
    sc.unit_settings.system = "NONE"
    for ob in list(sc.collection.all_objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for c in list(sc.collection.children_recursive):
        bpy.data.collections.remove(c)
    for m in list(bpy.data.meshes):
        if m.users == 0:
            bpy.data.meshes.remove(m)
    return sc


def coll(sc, name):
    c = bpy.data.collections.new(name)
    sc.collection.children.link(c)
    return c


# ====================================================================== helpers
def island(k, x0, x1, y0, y1, mulch=MULCH, plants=0):
    """Raised landscape island: concrete curb ring + rock-mulch top (+ plants in the character pass)."""
    if "M" in PASSES:
        k.P("M").box(mulch, x0 + 0.5, x1 - 0.5, y0 + 0.5, y1 - 0.5, LG - 0.2, LG + 0.35)
    if "T" in PASSES:
        k.P("T")
        k.box(CURBC, x0, x1, y0, y0 + 0.5, LG - 0.2, LG + 0.5)
        k.box(CURBC, x0, x1, y1 - 0.5, y1, LG - 0.2, LG + 0.5)
        k.box(CURBC, x0, x0 + 0.5, y0 + 0.5, y1 - 0.5, LG - 0.2, LG + 0.5)
        k.box(CURBC, x1 - 0.5, x1, y0 + 0.5, y1 - 0.5, LG - 0.2, LG + 0.5)
    if "C" in PASSES and plants:
        k.P("C")
        for i in range(plants):
            x = rng.uniform(x0 + 2, x1 - 2)
            y = rng.uniform(y0 + 2, y1 - 2)
            r = rng.random()
            if r < 0.4:
                bp.yucca(k, x, y, LG + 0.35, rng)
            elif r < 0.7:
                bp.boulder(k, x, y, LG + 0.35, rng, s=rng.uniform(1.2, 2.2))
            else:
                bp.juniper(k, x, y, LG + 0.35, rng, r=rng.uniform(1.6, 2.6))


def apron(k, axis, curb, out, a0, a1, flare=3.0):
    """Driveway apron in the street gutter: ramps from street level up to the curb top. axis = curb direction."""
    zt, zb = LG + 0.04, ST - 0.05
    o = curb + out * 5.0                      # out = toward the street
    if axis == "y":                           # curb runs along y (west/east street)
        pts = [(curb, a0 - flare, zb), (curb, a1 + flare, zb), (o, a1, zb), (o, a0, zb)]
        top = [(curb, a0 - flare, zt), (curb, a1 + flare, zt), (o, a1, ST + 0.02), (o, a0, ST + 0.02)]
    else:
        pts = [(a0 - flare, curb, zb), (a1 + flare, curb, zb), (a1, o, zb), (a0, o, zb)]
        top = [(a0 - flare, curb, zt), (a1 + flare, curb, zt), (a1, o, ST + 0.02), (a0, o, ST + 0.02)]
    # order rings CCW
    import mathutils
    def ccw(r):
        a = sum(r[i][0] * r[(i + 1) % 4][1] - r[(i + 1) % 4][0] * r[i][1] for i in range(4))
        return r if a > 0 else r[::-1]
    b, t = ccw(pts), ccw(top)
    if b != pts:
        t = top[::-1]
    k.hexa(CONC, b + t)


def stalls(k, x0, y0, n, w, depth, axis="x", nose=+1, stops=True, oil=True, accessible=()):
    """A row of n stalls starting at (x0, y0) along axis; stripes + wheel stops (T), oil stains (C)."""
    for i in range(n + 1):
        a = i * w
        if "T" in PASSES:
            k.P("T")
            if axis == "x":
                ys = (y0 + 1.0, y0 + depth - 0.5) if nose > 0 else (y0 - depth + 0.5, y0 - 1.0)
                k.box(PAINT_W, x0 + a - 0.2, x0 + a + 0.2, min(ys), max(ys), LG, LG + 0.03)
            else:
                xs = (x0 + 1.0, x0 + depth - 0.5) if nose > 0 else (x0 - depth + 0.5, x0 - 1.0)
                k.box(PAINT_W, min(xs), max(xs), y0 + a - 0.2, y0 + a + 0.2, LG, LG + 0.03)
    for i in range(n):
        c = (i + 0.5) * w
        if axis == "x":
            sx, sy = x0 + c, y0 + nose * (depth - 2.0)
            yaw = 0.0
        else:
            sx, sy = x0 + nose * (depth - 2.0), y0 + c
            yaw = math.pi / 2
        if "T" in PASSES and stops:
            k.P("T")
            bp.wheel_stop(k, sx, sy, LG, yaw)
        if i in accessible:
            if "T" in PASSES:
                k.P("T")
                if axis == "x":
                    k.box(PAINT_B, x0 + i * w + 0.3, x0 + (i + 1) * w - 0.3, min(y0, y0 + nose * depth), max(y0, y0 + nose * depth), LG, LG + 0.025)
                else:
                    k.box(PAINT_B, min(x0, x0 + nose * depth), max(x0, x0 + nose * depth), y0 + i * w + 0.3, y0 + (i + 1) * w - 0.3, LG, LG + 0.025)
            if "C" in PASSES:
                k.P("C")
                mx = sx if axis == "x" else x0 + nose * depth * 0.45
                my = y0 + nose * depth * 0.45 if axis == "x" else sy
                k.plane("Decal_accessible", (mx, my, LG + 0.04), 5.0, 6.5, "z+")
        if "C" in PASSES and oil and rng.random() < 0.6:
            k.P("C")
            mx = sx if axis == "x" else x0 + nose * depth * 0.5
            my = y0 + nose * depth * 0.5 if axis == "x" else sy
            k.plane(f"Decal_decal_oil_{rng.randrange(3)}", (mx + rng.uniform(-1, 1), my + rng.uniform(-1, 1), LG + 0.035),
                    rng.uniform(4, 7), rng.uniform(4, 7), "z+")


def storefront(k, y_face, out, o0, o1, door_at, door_w=9.2, mullion=5.5, bars=False):
    """Aluminium storefront in an opening o0..o1 of a wall whose outer face is y_face (out = +1 north)."""
    gy0, gy1 = sorted((y_face - out * 0.55, y_face - out * 0.4))
    d0, d1 = door_at, door_at + door_w
    if "M" in PASSES:
        k.P("M")
        for a, b in ((o0, d0), (d1, o1)):
            if b - a > 0.3:
                k.box("Glass_2B3438", a, b, gy0, gy1, FF + 1.0, FF + 10.0)
        k.box("Glass_2B3438", d0, d1, gy0, gy1, FF + 8.3, FF + 10.0)                   # transom
        for a, b in ((d0, d0 + door_w / 2 - 0.05), (d0 + door_w / 2 + 0.05, d1)):      # door leaves
            k.box("Glass_243036", a, b, gy0 - out * 0.05, gy1 - out * 0.05, FF, FF + 8.0)
    if "T" in PASSES:
        k.P("T")
        f0, f1 = sorted((y_face - out * 0.7, y_face - out * 0.25))
        k.box(bp.AL, o0, o1, f0, f1, FF + 9.9, FF + 10.3)                              # head
        k.box(bp.AL, o0, o0 + 0.4, f0, f1, FF, FF + 10.0)                              # jambs
        k.box(bp.AL, o1 - 0.4, o1, f0, f1, FF, FF + 10.0)
        for a, b in ((o0, d0), (d1, o1)):
            if b - a > 0.3:
                k.box(bp.AL, a, b, f0, f1, FF, FF + 1.0)                                # kick plate
                n = max(1, round((b - a) / mullion))
                for i in range(1, n):
                    m = a + i * (b - a) / n
                    k.box(bp.AL, m - 0.18, m + 0.18, f0, f1, FF + 1.0, FF + 10.0)
        k.box(bp.AL, d0, d1, f0, f1, FF + 8.0, FF + 8.4)                                # transom bar
        for m in (d0, d1):
            k.box(bp.AL, m - 0.2, m + 0.2, f0, f1, FF, FF + 10.0)
        s0, s1 = sorted((y_face - out * 0.75, y_face - out * 0.15))
        for a in (d0, d0 + door_w / 2 + 0.05):                                          # stiles + rails + pulls
            b = a + door_w / 2 - 0.05
            k.box(bp.AL, a, a + 0.5, s0, s1, FF, FF + 8.0)
            k.box(bp.AL, b - 0.5, b, s0, s1, FF, FF + 8.0)
            k.box(bp.AL, a, b, s0, s1, FF, FF + 0.9)
            k.box(bp.AL, a, b, s0, s1, FF + 7.5, FF + 8.0)
        for a in (d0 + door_w / 2 - 0.8, d0 + door_w / 2 + 0.6):
            p0, p1 = sorted((y_face + out * 0.0, y_face + out * 0.35))
            k.box("Metal_C9CBCB", a, a + 0.2, p0, p1, FF + 3.0, FF + 5.6)
    if bars and "C" in PASSES:
        k.P("C")
        b0, b1 = sorted((y_face + out * 0.15, y_face + out * 0.35))
        for a, b in ((o0, d0), (d1, o1)):
            x = a + 0.4
            while x < b - 0.3:
                k.box("Metal_1E1E1E", x, x + 0.14, b0, b1, FF + 1.0, FF + 9.6)
                x += 0.7
            for z in (FF + 1.2, FF + 5.0, FF + 9.4):
                k.box("Metal_1E1E1E", a, b, b0, b1, z, z + 0.14)


# ====================================================================== context (preview only, not exported)
def context(sc):
    k = Kit("WG01_Context", coll(sc, "WG01_Context"))
    k.P("M")
    road, walk = "Asphalt_3A3A3C", "Concrete_C6C0B4"
    # streets: west arterial (x 984..1043.5), east (1376..1404), south (416..444.5), north frontage (830..860)
    k.box(road, 940, 1460, 380, 452 - 8, ST - 0.4, ST)
    k.box(road, 940, 1460, 824 + 8, 900, ST - 0.4, ST)
    k.box(road, 940, 1052 - 8, 380, 900, ST - 0.4, ST)
    k.box(road, 1368 + 8, 1460, 380, 900, ST - 0.4, ST)
    for (x0, x1, y0, y1) in ((1044, 1052, 444, 832), (1368, 1376, 444, 832), (1044, 1376, 444, 452), (1044, 1376, 824, 832)):
        k.box(walk, x0, x1, y0, y1, ST - 0.2, LG)
    # far sidewalks + neighbouring lots (dirt) to frame the shots
    k.box(walk, 976, 984, 380, 900, ST - 0.2, LG)
    k.box(walk, 1404, 1412, 380, 900, ST - 0.2, LG)
    k.box(walk, 940, 1460, 408, 416, ST - 0.2, LG)
    k.box(walk, 940, 1460, 860, 868, ST - 0.2, LG)
    k.box("Ground_B89B72", 600, 1900, 0, 1300, 1.0, 1.95)
    # lane paint
    for y in range(390, 900, 40):
        k.box(PAINT_W, 1013.5, 1014.0, y, y + 10, ST, ST + 0.02)
    k.box(PAINT_Y, 1013.0, 1013.4, 380, 900, ST, ST + 0.02)
    k.box(PAINT_Y, 1014.6, 1015.0, 380, 900, ST, ST + 0.02)
    return k.finish()


# ====================================================================== site: lots, alley, islands, poles
def site(sc):
    k = Kit("WG01_Site", coll(sc, "WG01_Site"))
    if "M" in PASSES:
        k.P("M")
        k.box(ASPH, 1052, 1368, 738, 824, LG - 0.6, LG)                     # north lot
        k.box(ASPH, 1052, 1138, 678, 738, LG - 0.6, LG)                     # plaza side lot
        k.box(ASPH, 1052, 1368, 452, 658, LG - 0.6, LG)                     # south lot + courtyard
        k.box("Concrete_A39D91", 1052, 1368, 658, 678, LG - 0.6, LG - 0.02)  # alley
        k.box("Concrete_8F897D", 1052, 1368, 667.3, 668.7, LG - 0.6, LG - 0.06)   # valley gutter
        k.box(CONC, 1136, 1360, 738, 748.5, LG - 0.3, FF)                   # plaza walk
        k.box(CONC, 1138, 1358, 678, 738, LG - 0.3, FF)                     # plaza slab
        k.box(CONC, 1058, 1098, 782, 818, LG - 0.3, LG + 0.2)               # stand patio
        k.box(CONC, 1060, 1068, 603, 649, LG - 0.3, FF)                      # taqueria porch
        k.box(CONC, 1068, 1112, 604, 648, LG - 0.3, FF)
        k.box(CONC, 1068, 1112, 466, 506, LG - 0.3, FF)                      # motel office
        k.box(CONC, 1326, 1356, 458, 646, LG - 0.3, FF)                      # wing A + walk
        k.box(CONC, 1150, 1326, 458, 488, LG - 0.3, FF)                      # wing B + walk
        # drained pool: deck ring + basin
        k.box(CONC, 1166, 1220, 556, 562, LG - 0.3, LG + 0.25)
        k.box(CONC, 1166, 1220, 598, 604, LG - 0.3, LG + 0.25)
        k.box(CONC, 1166, 1172, 562, 598, LG - 0.3, LG + 0.25)
        k.box(CONC, 1214, 1220, 562, 598, LG - 0.3, LG + 0.25)
        k.box("Plaster_8DB4BE", 1172, 1214, 562, 563, -2.6, LG + 0.25)
        k.box("Plaster_8DB4BE", 1172, 1214, 597, 598, -2.6, LG + 0.25)
        k.box("Plaster_8DB4BE", 1172, 1173, 563, 597, -2.6, LG + 0.25)
        k.box("Plaster_8DB4BE", 1213, 1214, 563, 597, -2.6, LG + 0.25)
        k.box("Plaster_A9C3C6", 1173, 1213, 563, 597, -3.0, -2.6)
        # CMU wall between alley and motel courtyard, with a gate gap
        k.box("Concrete_B5AE9F", 1146, 1290, 655.5, 656.5, LG, LG + 6.5)
        k.box("Concrete_B5AE9F", 1310, 1368, 655.5, 656.5, LG, LG + 6.5)
        # driveway aprons (street gutters)
        apron(k, "y", 1043.5, -1, 770, 794)            # arterial -> north lot aisle
        apron(k, "y", 1043.5, -1, 658, 678)            # arterial -> alley
        apron(k, "y", 1376.5, +1, 770, 794)            # east street -> north lot aisle
        apron(k, "y", 1376.5, +1, 658, 678)            # east street -> alley
        apron(k, "x", 444.5, -1, 1112, 1146)           # south street -> motel drive
    # landscape islands
    island(k, 1100, 1368, 816, 824, plants=14)
    island(k, 1052, 1060, 738, 770, plants=3)
    island(k, 1052, 1060, 794, 824, plants=0)
    island(k, 1100, 1108, 794, 816, plants=2)
    island(k, 1100, 1108, 748, 770, plants=2)
    island(k, 1360, 1368, 748, 770, plants=1)
    island(k, 1360, 1368, 794, 816, plants=1)
    island(k, 1052, 1060, 458, 600, plants=12)
    island(k, 1146, 1368, 452, 458, plants=0)
    island(k, 1052, 1112, 452, 458, plants=3)
    # parking rows
    stalls(k, 1108, 794, 23, 11.0, 22.0, "x", +1, accessible=())
    stalls(k, 1108, 770, 23, 11.0, 22.0, "x", -1, accessible=(9, 10))
    stalls(k, 1304, 500, 13, 11.0, 22.0, "y", +1, accessible=(0,))          # motel wing A row (nose east)
    stalls(k, 1180, 510, 11, 11.0, 22.0, "x", -1)                           # wing B row (nose south)
    stalls(k, 1140, 600, 4, 11.0, 22.0, "y", -1)                             # taqueria side (nose west)
    stalls(k, 1060, 700, 3, 11.0, 22.0, "x", +1)                             # plaza side lot (nose north)
    if "T" in PASSES:
        k.P("T")
        # fire lane: red curb along the plaza walk ends + bollards
        k.box(PAINT_R, 1136, 1140, 748.0, 748.6, FF - 0.01, FF + 0.01)
        for x in (1137.5, 1358.5):
            bp.bollard(k, x, 742, FF)
        # pool fence + ladder
        bp.railing(k, "Metal_2E2E2E", (1164, 554), (1222, 554), LG + 0.25, h=4.2, pitch=0.55, r=0.06)
        bp.railing(k, "Metal_2E2E2E", (1164, 606), (1222, 606), LG + 0.25, h=4.2, pitch=0.55, r=0.06)
        bp.railing(k, "Metal_2E2E2E", (1164, 554), (1164, 606), LG + 0.25, h=4.2, pitch=0.55, r=0.06)
        bp.railing(k, "Metal_2E2E2E", (1222, 554), (1222, 606), LG + 0.25, h=4.2, pitch=0.55, r=0.06)
        for yy in (566, 568.5):
            k.tube("Metal_C9CBCB", (1210.5, yy, LG + 3.5), (1212.6, yy, LG + 0.2), 0.12)
            k.tube("Metal_C9CBCB", (1212.6, yy, LG + 0.2), (1212.6, yy, -2.6), 0.12)
        k.box("Concrete_D2CBBE", 1171, 1215, 561, 562, LG + 0.25, LG + 0.4)    # pool coping
        k.box("Concrete_D2CBBE", 1171, 1215, 598, 599, LG + 0.25, LG + 0.4)
        # CMU wall cap
        k.box("Concrete_C9C2B2", 1146, 1290, 655.3, 656.7, LG + 6.5, LG + 6.8)
        k.box("Concrete_C9C2B2", 1310, 1368, 655.3, 656.7, LG + 6.5, LG + 6.8)
    if "C" in PASSES:
        k.P("C")
        # asphalt cracks + patches
        for _ in range(16):
            x, y = rng.uniform(1110, 1360), rng.uniform(745, 815)
            k.plane(f"Decal_decal_cracks_{rng.randrange(3)}", (x, y, LG + 0.03), rng.uniform(14, 26), rng.uniform(14, 26), "z+")
        for _ in range(18):
            x, y = rng.uniform(1120, 1320), rng.uniform(490, 650)
            k.plane(f"Decal_decal_cracks_{rng.randrange(3)}", (x, y, LG + 0.03), rng.uniform(14, 26), rng.uniform(14, 26), "z+")
        for _ in range(6):
            x, y = rng.uniform(1060, 1360), rng.uniform(660, 676)
            k.plane(f"Decal_decal_cracks_{rng.randrange(3)}", (x, y, LG + 0.0), rng.uniform(8, 14), rng.uniform(8, 12), "z+")
        # utility poles + lines along the alley (south side), service drops
        poles = []
        for x in (1066, 1146, 1226, 1306, 1362):
            poles.append(bp.utility_pole(k, x, 657.5 if x != 1362 else 660, LG, h=34, arm_yaw=math.pi / 2, transformer=(x == 1226)))
        for a, b in zip(poles[:-1], poles[1:]):
            for i in (0, 1, 3):
                bp.wire(k, a[i], b[i], sag=1.6)
        bp.wire(k, poles[1][2], (1160, 678.6, 16.5), sag=1.0)
        bp.wire(k, poles[3][2], (1300, 678.6, 16.5), sag=1.0)
        bp.wire(k, poles[2][1], (1240, 652, 24.5), sag=1.0)
        # lot lights
        for x in (1170, 1290):
            bp.shoebox_light(k, x, 820, LG + 0.35, h=26, heads=((0, -1),))
        bp.shoebox_light(k, 1250, 548, LG, h=24, heads=((1, 0), (-1, 0)))
        # dumpsters, pallets, barrels, cart, tumbleweeds, news boxes
        bp.dumpster(k, 1180, 671, LG, 0.0)
        bp.dumpster(k, 1262, 671, LG, 0.05, color="Metal_2D4F7A")
        bp.dumpster(k, 1128, 646, LG, math.pi / 2)
        bp.pallet(k, 1200, 674, LG, 0.1)
        bp.pallet(k, 1201, 674, LG + 0.5, 0.4)
        bp.barrel(k, 1320, 673, LG)
        bp.barrel(k, 1322.4, 674, LG, color="Metal_2F6B3E")
        bp.shopping_cart(k, 1236, 760, LG, 0.7)
        for x, y in ((1150, 659), (1290, 659), (1366, 760), (1160, 818), (1060, 520)):
            bp.tumbleweed(k, x, y, LG, rng, r=rng.uniform(0.9, 1.5))
        bp.news_box(k, 1150, 742, FF)
        bp.news_box(k, 1153, 742, FF, color="Metal_B83A2E")
        # graffiti on the alley CMU wall + plaza rear
        k.plane("Decal_decal_tag_0", (1200, 656.55, LG + 3.2), 14, 5.2, "y+")
        k.plane("Decal_decal_tag_3", (1335, 656.55, LG + 3.0), 12, 4.5, "y+")
        # signs: plaza pylon, tow-away, customer parking
        x, y = 1056, 760
        k.box("Plaster_C9B38F", x - 4.5, x + 4.5, y - 1.5, y + 1.5, LG + 0.35, LG + 4.0)
        k.box("Metal_4A4C4E", x - 0.4, x + 0.4, y - 0.4, y + 0.4, LG + 4.0, LG + 12)
        k.sign("plaza_pylon", (x, y, LG + 21), 8.0, 16.0, "x-", depth=1.2, cabinet="Metal_3A2A20", both=True)
        for (sx, sy, nrm) in ((1054, 768, "x-"), (1370, 768, "x+")):
            k.box("Metal_9EA2A3", sx - 0.12, sx + 0.12, sy - 0.12, sy + 0.12, LG, LG + 8)
            k.plane("Sign_tow_away", (sx + (-0.15 if nrm == "x-" else 0.15), sy, LG + 9.2), 2.4, 1.8, nrm)
        k.box("Metal_9EA2A3", 1140, 1140.24, 818, 818.24, LG + 0.35, LG + 7)
        k.plane("Sign_customer_parking", (1140.12, 817.85, LG + 8.0), 2.4, 1.8, "y-")
    return k.finish()


# ====================================================================== Sunset Plaza (strip centre)
BAYS = [30, 30, 32, 30, 30, 32, 32]
TENANT = ["plaza_lucky7", "plaza_ink", "plaza_pho", "plaza_cuts", "plaza_lease", "plaza_bail", "plaza_cash"]
PX0, PX1, PY0, PY1 = 1140, 1356, 678, 738
RZ, PT = FF + 14.0, FF + 16.5


def plaza(sc):
    k = Kit("WG01_Plaza", coll(sc, "WG01_Plaza"))
    wall = "Plaster_D9C7A3"
    xs = [PX0]
    for w in BAYS:
        xs.append(xs[-1] + w)
    bays = list(zip(xs[:-1], xs[1:]))
    front_open = [(a + 2.6, b - 2.6, FF, FF + 10.0) for a, b in bays]
    rear_open = []
    for a, b in bays:
        rear_open.append((a + 5.0, a + 9.6, FF, FF + 7.4))           # service door
        rear_open.append((a + 20.0, a + 23.0, FF + 6.0, FF + 8.2))   # restroom window
    if "M" in PASSES:
        k.P("M")
        k.wall(wall, "x", PY1 - 1, PY1, PX0, PX1, FF, PT, front_open)
        k.wall("Plaster_D2C2A0", "x", PY0, PY0 + 1, PX0, PX1, FF, PT, rear_open)
        k.wall("Plaster_D2C2A0", "y", PX0, PX0 + 1, PY0 + 1, PY1 - 1, FF, PT, [(700, 712, FF + 3.0, FF + 7.4)])
        k.wall("Plaster_D2C2A0", "y", PX1 - 1, PX1, PY0 + 1, PY1 - 1, FF, PT)
        k.box("Concrete_8E8A84", PX0 + 1, PX1 - 1, PY0 + 1, PY1 - 1, RZ - 0.8, RZ)          # roof
        # interior backdrop behind the glass (dark, so the storefronts read as deep)
        k.box("Concrete_3B3936", PX0 + 1, PX1 - 1, PY1 - 14, PY1 - 13, FF, RZ - 0.8)
        k.box("Concrete_6E675E", PX0 + 1, PX1 - 1, PY1 - 13, PY1 - 1, FF - 0.05, FF + 0.05)
        k.box("Plaster_E8E2D4", PX0 + 1, PX1 - 1, PY1 - 13, PY1 - 1, FF + 11.5, FF + 11.8)  # ceiling tiles
        for (a, b), (o0, o1, _, _) in zip(bays, front_open):
            door_at = o0 + 1.0 if (a // 1) % 2 == 0 else o1 - 1.0 - 9.2
            storefront(k, PY1, +1, o0, o1, door_at, bars=a in (xs[5], xs[6]))
            # back doors
            k.box("Metal_7D7A72", a + 5.0, a + 9.6, PY0 + 0.35, PY0 + 0.55, FF, FF + 7.4)
            k.box("Glass_3A4449", a + 20.0, a + 23.0, PY0 + 0.4, PY0 + 0.55, FF + 6.0, FF + 8.2)
        # mansard: standing-seam metal roof on the front, hip ends, soffit, posts
        y0, y1, ztop, zbot = PY1, PY1 + 10.5, PT + 0.3, FF + 10.3
        k.slab4("Metal_B8B6AE", [(PX0 - 2, y1, zbot), (PX1 + 2, y1, zbot), (PX1 + 2, y0, ztop), (PX0 - 2, y0, ztop)], 0.4)
        for xe, s in ((PX0 - 2, -1), (PX1 + 2, 1)):
            tri = [(xe, y0, ztop), (xe, y1, zbot), (xe, y0, zbot)]
            k.face("Metal_B8B6AE", tri if s < 0 else tri[::-1])
            k.face("Metal_B8B6AE", tri[::-1] if s < 0 else tri)
        k.box("Plaster_E3D6BC", PX0 - 2, PX1 + 2, y0, y1, zbot - 0.4, zbot - 0.05)
        for x in xs:
            k.box(wall, x - 0.7, x + 0.7, y1 - 1.6, y1 - 0.2, FF, zbot - 0.4)
    if "T" in PASSES:
        k.P("T")
        y1, ztop, zbot = PY1 + 10.5, PT + 0.3, FF + 10.3
        k.box("Metal_6F6B62", PX0 - 2.2, PX1 + 2.2, y1 - 0.1, y1 + 0.5, zbot - 0.7, zbot + 0.5)    # fascia
        k.box("Metal_9C998F", PX0 - 2.2, PX1 + 2.2, PY1 - 0.3, PY1 + 0.6, ztop - 0.2, ztop + 0.3)  # ridge cap
        x = PX0 - 1.5
        while x < PX1 + 2:                                                                       # standing seams
            k.tube("Metal_A8A69E", (x, PY1 + 0.3, ztop + 0.05), (x, y1 - 0.2, zbot + 0.25), 0.08, segs=4)
            x += 2.0
        for xx in xs:                                                                            # post cap/base
            k.box("Plaster_C4B08A", xx - 0.95, xx + 0.95, y1 - 1.85, y1 + 0.05, FF, FF + 1.2)
            k.box("Plaster_C4B08A", xx - 0.9, xx + 0.9, y1 - 1.8, y1, zbot - 1.2, zbot - 0.4)
        for xx in xs:
            k.box("Plaster_CDBB95", xx - 2.2, xx + 2.2, PY1, PY1 + 0.3, FF, FF + 10.4)
        k.box("Plaster_9C8466", PX0 - 0.15, PX1 + 0.15, PY0 - 0.15, PY0 + 0.01, FF - 0.5, FF + 1.4)   # base band
        k.box("Plaster_9C8466", PX0 - 0.15, PX0 + 0.01, PY0, PY1, FF - 0.5, FF + 1.4)
        k.box("Plaster_9C8466", PX1 - 0.01, PX1 + 0.15, PY0, PY1, FF - 0.5, FF + 1.4)
        bp.coping(k, "Metal_8F8C84", PX0, PX1, PY0, PY1, PT)
        k.box("Plaster_CBB993", PX0 - 0.2, PX1 + 0.2, PY0 - 0.2, PY0, PT - 2.0, PT - 1.6)    # rear reveal band
        for a, b in zip(xs[:-1], xs[1:]):
            bp.frame(k, "Metal_5E5A52", "x", PY0, -1, a + 5.0, a + 9.6, FF, FF + 7.4, sill=False)
            bp.frame(k, "Plaster_E6DCC6", "x", PY0, -1, a + 20.0, a + 23.0, FF + 6.0, FF + 8.2)
            k.box("Metal_7E7A70", a + 3.8, a + 10.8, PY0 - 3.2, PY0, FF + 8.6, FF + 8.9)              # door hood
            for xx in (a + 4.0, a + 10.6):
                k.tube("Metal_5E5A52", (xx, PY0 - 3.0, FF + 8.6), (xx, PY0, FF + 10.2), 0.07, segs=4)
            k.box("Metal_C9CBCB", a + 8.6, a + 8.8, PY0 - 0.25, PY0, FF + 3.3, FF + 3.6)              # lever
        for xx in (PX0 + 30, PX0 + 92, PX0 + 152, PX0 + 210):                                  # scuppers + downspouts
            k.box("Metal_8F8C84", xx - 0.7, xx + 0.7, PY0 - 0.9, PY0, RZ - 0.4, RZ + 0.4)
            k.box("Metal_8F8C84", xx - 0.9, xx + 0.9, PY0 - 1.5, PY0 - 0.2, RZ - 2.2, RZ - 0.4)
            k.box("Metal_8F8C84", xx - 0.4, xx + 0.4, PY0 - 1.1, PY0 - 0.3, FF + 0.3, RZ - 2.2)
            k.box("Concrete_A39D91", xx - 0.8, xx + 0.8, PY0 - 3.0, PY0 - 0.2, LG - 0.02, LG + 0.15)
        bp.frame(k, "Plaster_E6DCC6", "y", PX0, -1, 700, 712, FF + 3.0, FF + 7.4)
    if "C" in PASSES:
        k.P("C")
        y1 = PY1 + 10.5
        for (a, b), t in zip(bays, TENANT):                                                    # tenant boards
            cx = (a + b) / 2
            k.sign(t, (cx, y1 + 0.35, FF + 13.9), min(22.0, b - a - 6), 5.5, "y+", depth=0.6, cabinet="Metal_2B2B2D")
            for dx in (-6, 6):
                k.tube("Metal_4A4C4E", (cx + dx, y1 + 0.1, FF + 15.8), (cx + dx, PY1 + 4.0, FF + 15.0), 0.08, segs=4)
        # storefront life
        a, b = bays[0]
        for i in range(6):                                                                      # laundromat washers
            x = a + 4 + i * 4.0
            k.box("Metal_E4E4DE", x, x + 3.2, PY1 - 6, PY1 - 3.2, FF, FF + 3.6)
            k.box("Glass_6C7A80", x + 0.7, x + 2.5, PY1 - 3.25, PY1 - 3.15, FF + 1.1, FF + 2.9)
        a, b = bays[3]
        for i in range(3):                                                                      # barber chairs
            x = a + 7 + i * 7
            k.box("Fabric_7A1F1F", x, x + 2.4, PY1 - 7, PY1 - 4.6, FF + 1.6, FF + 3.4)
            k.box("Fabric_7A1F1F", x, x + 2.4, PY1 - 7, PY1 - 6.6, FF + 3.4, FF + 6.0)
            k.box("Metal_C9CBCB", x + 0.9, x + 1.5, PY1 - 6.1, PY1 - 5.5, FF, FF + 1.6)
            k.box("Glass_9FB0B6", x - 0.5, x + 2.9, PY1 - 12.9, PY1 - 12.8, FF + 4.0, FF + 9.0)  # mirror
        bp.barber_pole(k, bays[3][0] + 2.2, PY1 + 0.8, FF + 6.0)
        a, b = bays[4]                                                                          # vacant: papered glass
        k.box("SmoothPlastic_E9E4D6", a + 3.0, b - 3.0, PY1 - 0.7, PY1 - 0.62, FF + 1.2, FF + 9.8)
        k.plane("Sign_plaza_lease", ((a + b) / 2, PY1 - 0.4, FF + 6.0), 8.0, 2.0, "y+")
        for (a, b), col in zip([bays[1], bays[2], bays[5]], ["Neon_FF3B30", "Neon_FF6A00", "Neon_3BC8FF"]):
            k.box(col, a + 15, a + 19, PY1 - 0.9, PY1 - 0.75, FF + 6.2, FF + 7.4)             # OPEN signs
        for x in (PX0 + 70, PX0 + 150):                                                         # benches + cans
            k.box("Wood_8C6A48", x, x + 6, PY1 + 2.0, PY1 + 3.5, FF + 1.5, FF + 1.8)
            for xx in (x + 0.4, x + 5.4):
                k.box("Metal_3A3A3A", xx, xx + 0.2, PY1 + 2.2, PY1 + 3.3, FF, FF + 1.5)
            k.cyl("Metal_5E5A52", x + 9, PY1 + 3.5, FF, 1.0, 3.2, segs=10)
        # roof: RTUs, exhaust, dish, hatch
        for i, (a, b) in enumerate(bays):
            bp.rtu(k, a + 15 + rng.uniform(-4, 4), PY0 + 22 + rng.uniform(-4, 6), RZ, yaw=0)
        k.cyl("Metal_9EA2A3", bays[2][0] + 8, PY0 + 12, RZ, 1.4, 2.6, segs=12)
        k.cyl("Metal_7E7A70", bays[2][0] + 8, PY0 + 12, RZ + 2.6, 1.9, 0.5, segs=12, r2=0.6)
        bp.satellite(k, bays[1][0] + 25, PY1 - 4, RZ)
        k.box("Metal_8F8C84", PX0 + 100, PX0 + 103, PY0 + 40, PY0 + 43, RZ, RZ + 1.4)
        # rear: meters, wall packs, grease barrel, smoker chairs, crates, graffiti, drips
        for i, (a, b) in enumerate(bays):
            bp.wall_pack(k, "x", PY0, -1, a + 7.3, FF + 9.4)
            if i % 2 == 0:
                k.plane(f"Decal_decal_drip_{i % 3}", (a + 14, PY0 - 0.04, RZ - 4.5), 4.5, 9.0, "y-")
        bp.meter_bank(k, "x", PY0, -1, PX0 + 112, FF + 4.0, n=7)
        bp.barrel(k, bays[2][0] + 13, PY0 - 2.2, LG, color="Metal_4F4A3C")
        for dx in (0, 2.4):
            bp.chair(k, bays[3][0] + 13 + dx, PY0 - 2.2, LG, math.pi)
        k.box("SmoothPlastic_2E5CA8", bays[3][0] + 18, bays[3][0] + 19.4, PY0 - 2.6, PY0 - 1.2, LG, LG + 1.0)
        k.plane("Decal_decal_tag_1", (PX0 + 58, PY0 - 0.05, FF + 4.5), 13, 4.8, "y-")
        k.plane("Decal_decal_tag_2", (PX0 + 182, PY0 - 0.05, FF + 4.0), 12, 4.5, "y-")
        k.plane("Decal_decal_tag_4", (PX0 - 0.05, 722, FF + 5.0), 14, 5.2, "x-")
        k.plane("Decal_decal_patch", (PX0 + 125, PY0 - 0.04, FF + 7.0), 8, 8, "y-")
    return k.finish()


# ====================================================================== Top Dog walk-up stand
def topdog(sc):
    k = Kit("WG01_TopDog", coll(sc, "WG01_TopDog"))
    X0, X1, Y0, Y1 = 1066, 1090, 790, 810
    F0 = LG + 0.2
    top, par = F0 + 11.0, F0 + 12.4
    brick = "Brick_8E4A33"
    if "M" in PASSES:
        k.P("M")
        k.wall(brick, "y", X0, X0 + 1, Y0, Y1, F0, par, [(795, 805, F0 + 3.2, F0 + 7.2)])
        k.wall(brick, "x", Y0, Y0 + 1, X0 + 1, X1, F0, par, [(1080, 1084.6, F0, F0 + 7.4)])
        k.wall(brick, "x", Y1 - 1, Y1, X0 + 1, X1, F0, par, [(1072, 1076, F0 + 4.0, F0 + 7.0)])
        k.wall(brick, "y", X1 - 1, X1, Y0 + 1, Y1 - 1, F0, par, [(797, 801.6, F0, F0 + 7.4)])
        k.box("Concrete_8E8A84", X0 + 1, X1 - 1, Y0 + 1, Y1 - 1, top - 0.8, top)
        k.box("Glass_2E3A3E", X0 + 0.45, X0 + 0.6, 795, 805, F0 + 3.2, F0 + 7.2)
        k.box("Metal_8C2F28", 1080, 1084.6, Y0 + 0.35, Y0 + 0.55, F0, F0 + 7.4)
        k.box("Glass_2E3A3E", 1072, 1076, Y1 - 0.6, Y1 - 0.45, F0 + 4.0, F0 + 7.0)
        k.box("Metal_6A6A6A", X1 - 0.55, X1 - 0.35, 797, 801.6, F0, F0 + 7.4)
        k.box("Concrete_3B3936", X0 + 1, X1 - 1, Y0 + 1, Y1 - 1, F0, F0 + 0.05)
        k.box("Metal_B8BCBE", X0 + 1.5, X0 + 3, 794, 806, F0, F0 + 3.2)                     # inside counter
    if "T" in PASSES:
        k.P("T")
        k.box("Brick_6E3A2A", X0 - 0.12, X1 + 0.12, Y0 - 0.12, Y1 + 0.12, top - 1.6, top - 0.8)    # soldier course
        bp.coping(k, "Metal_7A7A78", X0, X1, Y0, Y1, par)
        k.box("Concrete_A8A08F", X0 - 0.15, X1 + 0.15, Y0 - 0.15, Y1 + 0.15, F0 - 0.4, F0 + 0.6)   # base
        k.box("Metal_B8BCBE", X0 - 1.6, X0 + 0.2, 794.5, 805.5, F0 + 3.0, F0 + 3.25)           # shelf
        for yy in (795.5, 804.5):
            k.tube("Metal_B8BCBE", (X0 - 1.4, yy, F0 + 3.0), (X0, yy, F0 + 1.6), 0.06, segs=4)
        bp.frame(k, "Metal_B8BCBE", "y", X0, -1, 795, 805, F0 + 3.2, F0 + 7.2, sill=False)
        k.box("Metal_B8BCBE", X0 - 0.3, X0 + 0.1, 799.9, 800.1, F0 + 3.2, F0 + 7.2)           # slider meeting rail
        bp.frame(k, "Concrete_C8BFAE", "x", Y0, -1, 1080, 1084.6, F0, F0 + 7.4, sill=False)
        bp.frame(k, "Concrete_C8BFAE", "x", Y1, +1, 1072, 1076, F0 + 4.0, F0 + 7.0)
        bp.frame(k, "Concrete_C8BFAE", "y", X1, +1, 797, 801.6, F0, F0 + 7.4, sill=False)
        # red standing-seam awning over the walk-up window
        k.slab4("Metal_A3261E", [(X0 - 5.0, 793.5, F0 + 8.7), (X0 - 5.0, 806.5, F0 + 8.7), (X0, 806.5, F0 + 10.2), (X0, 793.5, F0 + 10.2)], 0.25)
        for yy in (794, 806):
            k.tube("Metal_3A3A3A", (X0 - 4.8, yy, F0 + 8.6), (X0, yy, F0 + 7.6), 0.07, segs=4)
        yy = 793.6
        while yy < 806.5:
            k.tube("Metal_C23B30", (X0 - 0.05, yy, F0 + 10.25), (X0 - 4.95, yy, F0 + 8.75), 0.05, segs=4)
            yy += 1.3
    if "C" in PASSES:
        k.P("C")
        # roof sign on a steel frame, readable from the arterial (west) and the lot (east)
        for yy in (793, 807):
            k.box("Metal_3A3A3A", 1077.8, 1078.4, yy - 0.3, yy + 0.3, top, top + 6.0)
            k.tube("Metal_3A3A3A", (1074, yy, top), (1078, yy, top + 4.5), 0.12, segs=4)
        k.sign("topdog_roof", (1078.1, 800, top + 9.2), 20.0, 6.3, "x-", depth=0.8, cabinet="Metal_A3261E", both=True)
        k.plane("Sign_topdog_menu", (X0 - 0.08, 808.4, F0 + 6.2), 2.4, 3.0, "x-")
        bp.rtu(k, 1082, 800, top, sx=5.0, sy=3.6, sz=2.8)
        bp.picnic_table(k, 1061.5, 786.5, LG + 0.2, math.pi / 2)
        bp.picnic_table(k, 1061.5, 814, LG + 0.2, math.pi / 2)
        k.cyl("Metal_5E5A52", 1064.5, 791, LG + 0.2, 1.0, 3.2, segs=10)
        k.plane("Decal_decal_drip_2", (1086, Y0 - 0.05, top - 3.0), 4.0, 7.0, "y-")
        k.plane("Decal_decal_oil_1", (1086, 787, LG + 0.23), 5, 4, "z+")
        bp.wall_pack(k, "x", Y0, -1, 1086, F0 + 8.2)
        k.plane("Decal_decal_tag_3", (X1 + 0.05, 805, F0 + 3.8), 8.0, 3.0, "x+")
    return k.finish()


# ====================================================================== El Sol taqueria
def elsol(sc):
    k = Kit("WG01_ElSol", coll(sc, "WG01_ElSol"))
    X0, X1, Y0, Y1 = 1068, 1112, 604, 648
    yel, org, red = "Plaster_E2B52C", "Plaster_D9692A", "Plaster_A8352C"
    top, par = FF + 12.0, FF + 14.2
    wopen = [(607, 619, FF + 2.5, FF + 8.0), (622, 631.2, FF, FF + 8.0), (634, 645, FF + 2.5, FF + 8.0)]
    nopen = [(1076, 1086, FF + 3.0, FF + 7.4), (1092, 1102, FF + 3.0, FF + 7.4), (1105, 1109.6, FF, FF + 7.4)]
    sopen = [(1078, 1086, FF + 3.0, FF + 7.4), (1094, 1102, FF + 3.0, FF + 7.4)]
    eopen = [(612, 616.6, FF, FF + 7.4), (628, 631, FF + 6.0, FF + 8.0)]
    if "M" in PASSES:
        k.P("M")
        k.wall(yel, "y", X0, X0 + 1, Y0, Y1, FF, par, wopen)
        k.wall(yel, "x", Y1 - 1, Y1, X0 + 1, X1, FF, par, nopen)
        k.wall(yel, "x", Y0, Y0 + 1, X0 + 1, X1, FF, par, sopen)
        k.wall(yel, "y", X1 - 1, X1, Y0 + 1, Y1 - 1, FF, par, eopen)
        k.box(yel, X0, X0 + 1, 616, 636, par, par + 2.2)                    # stepped parapet
        k.box(yel, X0, X0 + 1, 621, 631, par + 2.2, par + 3.6)
        k.box("Concrete_8E8A84", X0 + 1, X1 - 1, Y0 + 1, Y1 - 1, top - 0.8, top)
        k.box("Glass_2B3438", X0 + 0.4, X0 + 0.55, 607, 619, FF + 2.5, FF + 8.0)
        k.box("Glass_2B3438", X0 + 0.4, X0 + 0.55, 634, 645, FF + 2.5, FF + 8.0)
        k.box("Glass_243036", X0 + 0.35, X0 + 0.5, 622, 626.55, FF, FF + 8.0)
        k.box("Glass_243036", X0 + 0.35, X0 + 0.5, 626.65, 631.2, FF, FF + 8.0)
        for a, b, z0, z1 in nopen:
            k.box("Glass_2B3438" if b - a > 5 else "Metal_7D3A2A", a, b, Y1 - 0.6, Y1 - 0.45, z0, z1)
        for a, b, z0, z1 in sopen:
            k.box("Glass_2B3438", a, b, Y0 + 0.45, Y0 + 0.6, z0, z1)
        k.box("Metal_7D7A72", X1 - 0.55, X1 - 0.35, 612, 616.6, FF, FF + 7.4)
        k.box("Glass_3A4449", X1 - 0.55, X1 - 0.4, 628, 631, FF + 6.0, FF + 8.0)
        k.box("Concrete_3B3936", X0 + 1, X1 - 1, Y0 + 1, Y1 - 1, FF, FF + 0.05)
        k.box("Plaster_EFE6D2", X0 + 1, X1 - 1, Y0 + 1, Y1 - 1, FF + 10.5, FF + 10.8)
        # porch: tile shed roof on wood posts
        k.slab4("ClayRoofTiles_A8532E", [(1059.8, 602.5, FF + 8.9), (1059.8, 649.5, FF + 8.9), (X0, 649.5, FF + 10.9), (X0, 602.5, FF + 10.9)], 0.6)
        for yy in (604.6, 616.5, 636.5, 647.4):
            k.box("Wood_D9742E", 1060.6, 1061.6, yy - 0.5, yy + 0.5, FF, FF + 8.6)
    if "T" in PASSES:
        k.P("T")
        k.box(red, X0 - 0.15, X1 + 0.15, Y0 - 0.15, Y1 + 0.15, FF - 0.5, FF + 1.6)             # base band
        bp.coping(k, "Concrete_B5634A", X0, X1, Y0, Y1, par, w=0.6, h=0.4)
        k.box("Concrete_B5634A", X0 - 0.3, X0 + 1.3, 615.7, 636.3, par + 2.2, par + 2.55)
        k.box("Concrete_B5634A", X0 - 0.3, X0 + 1.3, 620.7, 631.3, par + 3.6, par + 3.95)
        k.box(org, X0 - 0.12, X1 + 0.12, Y0 - 0.12, Y1 + 0.12, top - 2.4, top - 1.9)            # orange band
        green = "Wood_2F6B3E"
        for a, b, z0, z1 in wopen:
            bp.frame(k, green, "y", X0, -1, a, b, z0, z1, sill=(z0 > FF), w=0.4)
        for a, b, z0, z1 in nopen:
            bp.frame(k, green, "x", Y1, +1, a, b, z0, z1, sill=(z0 > FF), w=0.4)
        for a, b, z0, z1 in sopen:
            bp.frame(k, green, "x", Y0, -1, a, b, z0, z1, w=0.4)
        for a, b, z0, z1 in eopen:
            bp.frame(k, "Concrete_C8BFAE", "y", X1, +1, a, b, z0, z1, sill=(z0 > FF))
        for yy in (607 + 6, 634 + 5.5):                                                          # window muntins
            k.box(green, X0 - 0.35, X0 + 0.1, yy - 0.15, yy + 0.15, FF + 2.5, FF + 8.0)
        # vigas: log ends through the parapet line (front + north + south)
        for yy in range(606, 648, 4):
            k.tube("Wood_7A5232", (X0 + 0.2, yy, top + 0.4), (X0 - 1.5, yy, top + 0.4), 0.42, segs=8)
        for xx in range(1072, 1112, 4):
            k.tube("Wood_7A5232", (xx, Y1 - 0.2, top + 0.4), (xx, Y1 + 1.5, top + 0.4), 0.42, segs=8)
            k.tube("Wood_7A5232", (xx, Y0 + 0.2, top + 0.4), (xx, Y0 - 1.5, top + 0.4), 0.42, segs=8)
        k.box("Wood_8A4E24", 1060.2, 1062.0, 602.5, 649.5, FF + 8.4, FF + 9.0)                    # porch beam
        yy = 603.5
        while yy < 649:
            k.box("Wood_8A4E24", 1059.9, X0, yy - 0.15, yy + 0.15, FF + 8.9, FF + 9.2)
            yy += 2.5
        for yy in (604.6, 616.5, 636.5, 647.4):
            k.box("Concrete_A8A08F", 1060.3, 1061.9, yy - 0.8, yy + 0.8, FF, FF + 0.6)
            for dy in (-1, 1):
                k.tube("Wood_D9742E", (1061.1, yy, FF + 7.2), (1061.1, yy + dy * 1.6, FF + 8.4), 0.12, segs=4)
    if "C" in PASSES:
        k.P("C")
        k.decal("elsol_wall_name", (1090, Y1 + 0.06, FF + 9.2), 24.0, 6.0, "y+")
        k.decal("elsol_wall_menu", (X0 - 0.06, 626, FF + 12.3), 24.0, 4.6, "x-")
        k.decal("elsol_wall_name", (1090, Y0 - 0.06, FF + 9.2), 24.0, 6.0, "y-")
        k.decal("decal_drip_0", (X1 + 0.05, 640, top - 2.0), 3.5, 7.0, "x+")
        # pole sign on two steel posts with braces (corner of the lot, faces the arterial both ways)
        for yy in (586, 596):
            k.box("Metal_E2DED2", 1055.6, 1056.4, yy - 0.4, yy + 0.4, LG + 0.35, LG + 17.0)
            k.tube("Metal_E2DED2", (1056, yy, LG + 9.0), (1056, 591, LG + 17.0), 0.1, segs=4)
        k.sign("elsol_pole", (1056, 591, LG + 21.0), 14.0, 7.0, "x-", depth=0.9, cabinet="Metal_B8B2A2", both=True)
        bp.swamp_cooler(k, 1100, 626, top)
        bp.satellite(k, 1106, 642, top, yaw=2.4)
        k.box("Metal_9EA2A3", 1096, 1098, 612, 614, top, top + 3.0)                              # hood exhaust
        k.box("Metal_7E7A70", 1095.5, 1098.5, 611.5, 614.5, top + 3.0, top + 3.6)
        for yy, col in ((609, "SmoothPlastic_E9E6DC"), (612, "SmoothPlastic_C0392B"), (640, "SmoothPlastic_E9E6DC"), (643, "SmoothPlastic_2E7D32")):
            bp.chair(k, 1064.5, yy, FF, math.pi / 2, col)
        k.cyl("SmoothPlastic_E9E6DC", 1064.5, 610.5, FF, 1.4, 0.15, segs=10)
        k.cyl("SmoothPlastic_E9E6DC", 1064.5, 610.5, FF + 2.5, 1.6, 0.12, segs=12)
        k.cyl("Metal_9EA2A3", 1064.5, 610.5, FF, 0.1, 2.5, segs=5)
        bp.flag(k, 1057, 603, LG, "Fabric_2E7D32")
        bp.flag(k, 1057, 650, LG, "Fabric_C0392B")
        bp.barrel(k, X1 + 2.2, 620, LG, color="Metal_4F4A3C")
        bp.barrel(k, X1 + 2.2, 622.4, LG, color="Metal_2E4F86")
        k.cyl("Concrete_A8532E", 1062.5, 632.5, FF, 0.9, 1.4, segs=8, r2=1.1)
        bp.juniper(k, 1062.5, 632.5, FF + 1.4, rng, r=1.0)
    return k.finish()


# ====================================================================== Desert Rose Motor Lodge
MA_X0, MA_X1, MA_Y0, MA_Y1 = 1332, 1356, 458, 646          # wing A (east)
MB_X0, MB_X1, MB_Y0, MB_Y1 = 1150, 1332, 458, 482          # wing B (south)
F2, MRZ, MPT = FF + 11.0, FF + 22.0, FF + 24.2


def motel(sc):
    k = Kit("WG01_Motel", coll(sc, "WG01_Motel"))
    wall, accent = "Plaster_E6D5B8", "Plaster_C9785F"
    roomsA = [490 + 14 * i for i in range(11)]                 # along y on the west face of wing A
    roomsB = [1154 + 14 * i for i in range(12)]                # along x on the north face of wing B

    def room_ops(starts, floor):
        out = []
        for a in starts:
            out.append((a + 1.5, a + 6.1, floor, floor + 7.4))
            out.append((a + 7.5, a + 13.5, floor + 3.0, floor + 7.4))
        return out
    opsA = room_ops(roomsA, FF) + room_ops(roomsA, F2)
    opsB = room_ops(roomsB, FF) + room_ops(roomsB, F2)
    bathA = [(a + 9, a + 12, z + 5.0, z + 7.4) for a in roomsA for z in (FF, F2)]
    bathB = [(a + 9, a + 12, z + 5.0, z + 7.4) for a in roomsB for z in (FF, F2)]
    door_cols = ["Metal_2F8F8B", "Metal_2F8F8B", "Metal_C96F5A", "Metal_2F8F8B", "Metal_E0B23A"]
    boarded = {("A", 3, F2), ("B", 7, FF), ("B", 2, F2)}
    if "M" in PASSES:
        k.P("M")
        k.wall(wall, "y", MA_X0, MA_X0 + 1, MB_Y1, MA_Y1, FF, MPT, opsA)
        k.wall(wall, "y", MA_X1 - 1, MA_X1, MA_Y0, MA_Y1, FF, MPT, bathA)
        k.wall(wall, "x", MA_Y1 - 1, MA_Y1, MA_X0 + 1, MA_X1 - 1, FF, MPT)
        k.wall(wall, "x", MB_Y1 - 1, MB_Y1, MB_X0, MA_X0, FF, MPT, opsB)
        k.wall(wall, "x", MB_Y0, MB_Y0 + 1, MB_X0, MA_X1 - 1, FF, MPT, bathB)
        k.wall(wall, "y", MB_X0, MB_X0 + 1, MB_Y0 + 1, MB_Y1 - 1, FF, MPT, [(466, 474, FF + 3, FF + 7.4), (466, 474, F2 + 3, F2 + 7.4)])
        # roofs (overhang the upper walkways), walkway slabs, posts
        k.box("Concrete_8E8A84", MA_X0 - 6.5, MA_X1 - 1, MB_Y1 - 6.5 + 6.5, MA_Y1 - 1, MRZ - 0.8, MRZ)
        k.box("Concrete_8E8A84", MB_X0 - 0.5, MA_X1 - 1, MB_Y0 + 1, MB_Y1 + 6.5, MRZ - 0.8, MRZ)
        k.box("Concrete_8E8A84", MA_X0 - 6.5, MA_X0, MB_Y1, MB_Y1 + 6.5, MRZ - 0.8, MRZ)
        k.box("Concrete_B3AC9C", MA_X0 - 6, MA_X0, MB_Y1, MA_Y1 + 4, F2 - 0.8, F2)                 # walkway A
        k.box("Concrete_B3AC9C", MB_X0 - 6, MA_X0 - 6, MB_Y1, MB_Y1 + 6, F2 - 0.8, F2)            # walkway B
        k.box("Concrete_B3AC9C", MB_X0 - 6, MB_X0, MB_Y1 - 8, MB_Y1, F2 - 0.8, F2)                # landing W
        k.box("Concrete_B3AC9C", MA_X0 - 12, MA_X0 - 6, MA_Y1 - 2, MA_Y1 + 4, F2 - 0.8, F2)       # landing N
        for y in [488 + 14 * i for i in range(12)]:
            k.box("Metal_4A4C4E", MA_X0 - 6, MA_X0 - 5.3, y - 0.35, y + 0.35, FF, MRZ - 0.8)
        for x in [1152 + 14 * i for i in range(13)]:
            k.box("Metal_4A4C4E", x - 0.35, x + 0.35, MB_Y1 + 5.3, MB_Y1 + 6, FF, MRZ - 0.8)
        # glass + doors
        for i, a in enumerate(roomsA):
            for z in (FF, F2):
                col = door_cols[(i + int(z)) % len(door_cols)]
                k.box(col, MA_X0 + 0.35, MA_X0 + 0.55, a + 1.5, a + 6.1, z, z + 7.4)
                if ("A", i, z) in boarded:
                    k.box("Wood_B08A5C", MA_X0 - 0.15, MA_X0 + 0.1, a + 7.3, a + 13.7, z + 2.8, z + 7.6)
                else:
                    k.box("Glass_2B3438", MA_X0 + 0.4, MA_X0 + 0.55, a + 7.5, a + 13.5, z + 3.0, z + 7.4)
                k.box("Glass_3A4449", MA_X1 - 0.55, MA_X1 - 0.4, a + 9, a + 12, z + 5.0, z + 7.4)
        for i, a in enumerate(roomsB):
            for z in (FF, F2):
                col = door_cols[(i + 2 + int(z)) % len(door_cols)]
                k.box(col, a + 1.5, a + 6.1, MB_Y1 - 0.55, MB_Y1 - 0.35, z, z + 7.4)
                if ("B", i, z) in boarded:
                    k.box("Wood_B08A5C", a + 7.3, a + 13.7, MB_Y1 - 0.1, MB_Y1 + 0.15, z + 2.8, z + 7.6)
                else:
                    k.box("Glass_2B3438", a + 7.5, a + 13.5, MB_Y1 - 0.55, MB_Y1 - 0.4, z + 3.0, z + 7.4)
                k.box("Glass_3A4449", a + 9, a + 12, MB_Y0 + 0.4, MB_Y0 + 0.55, z + 5.0, z + 7.4)
        k.box("Glass_2B3438", MB_X0 + 0.4, MB_X0 + 0.55, 466, 474, FF + 3, FF + 7.4)
        k.box("Glass_2B3438", MB_X0 + 0.4, MB_X0 + 0.55, 466, 474, F2 + 3, F2 + 7.4)
        # stairs (walkable treads) at the north end of wing A and the west end of wing B
        bp.stairs(k, "Concrete_B3AC9C", MA_X0 - 9, MA_Y1 - 2 - 17 * 1.1, 0, 1, 5.5, FF, F2)
        bp.stairs(k, "Concrete_B3AC9C", MB_X0 - 3 + 17 * 1.1 + 6, MB_Y1 + 9, -1, 0, 5.5, FF, F2)
        k.box("Concrete_B3AC9C", MB_X0 - 6, MB_X0 + 3 + 0.2, MB_Y1 + 6, MB_Y1 + 11.75, F2 - 0.8, F2)
        # office + porte-cochere
        OX0, OX1, OY0, OY1 = 1070, 1110, 468, 504
        otop, opar = FF + 12, FF + 14
        k.wall(wall, "x", OY1 - 1, OY1, OX0, OX1, FF, opar, [(1080, 1098, FF + 1.0, FF + 9.0), (1100, 1104.6, FF, FF + 7.4)])
        k.wall(wall, "y", OX0, OX0 + 1, OY0, OY1 - 1, FF, opar, [(476, 496, FF + 2.5, FF + 8.5)])
        k.wall(wall, "x", OY0, OY0 + 1, OX0 + 1, OX1, FF, opar, [(1090, 1094.6, FF, FF + 7.4)])
        k.wall(wall, "y", OX1 - 1, OX1, OY0 + 1, OY1 - 1, FF, opar, [(482, 492, FF + 3, FF + 7.4)])
        k.box("Concrete_8E8A84", OX0 + 1, OX1 - 1, OY0 + 1, OY1 - 1, otop - 0.8, otop)
        k.box("Glass_2B3438", 1080, 1098, OY1 - 0.55, OY1 - 0.4, FF + 1.0, FF + 9.0)
        k.box("Glass_243036", 1100, 1104.6, OY1 - 0.55, OY1 - 0.35, FF, FF + 7.4)
        k.box("Glass_2B3438", OX0 + 0.4, OX0 + 0.55, 476, 496, FF + 2.5, FF + 8.5)
        k.box("Metal_7D7A72", 1090, 1094.6, OY0 + 0.35, OY0 + 0.55, FF, FF + 7.4)
        k.box("Glass_2B3438", OX1 - 0.55, OX1 - 0.4, 482, 492, FF + 3, FF + 7.4)
        k.box("Concrete_3B3936", OX0 + 1, OX1 - 1, OY0 + 1, OY1 - 1, FF, FF + 0.05)
        k.box("Wood_7A5232", 1082, 1096, OY1 - 6, OY1 - 4, FF, FF + 3.6)                       # front desk
        k.box(wall, 1110, 1148, 474, 506, FF + 12.6, FF + 14.0)                                  # porte-cochere roof
        for x, y in ((1112, 476), (1112, 504), (1146, 476), (1146, 504)):
            k.box(wall, x - 0.9, x + 0.9, y - 0.9, y + 0.9, LG, FF + 12.6)
    if "T" in PASSES:
        k.P("T")
        # roof fascia band + coping, slab-edge fascia, base band, corner trims
        k.box(accent, MA_X0 - 6.7, MA_X0 - 6.3, MB_Y1 + 6.3, MA_Y1 + 0.2, MRZ - 1.8, MRZ + 0.4)
        k.box(accent, MB_X0 - 0.7, MA_X0 - 6.3, MB_Y1 + 6.3, MB_Y1 + 6.7, MRZ - 1.8, MRZ + 0.4)
        k.box(accent, MA_X0 - 6.3, MA_X0 - 5.9, MB_Y1 + 5.9, MA_Y1 + 4.2, F2 - 1.4, F2 + 0.15)
        k.box(accent, MB_X0 - 6, MA_X0 - 5.9, MB_Y1 + 5.9, MB_Y1 + 6.3, F2 - 1.4, F2 + 0.15)
        bp.coping(k, "Metal_8F8C84", MA_X0, MA_X1, MA_Y0, MA_Y1, MPT)
        bp.coping(k, "Metal_8F8C84", MB_X0, MA_X0, MB_Y0, MB_Y1, MPT)
        for (x0, x1, y0, y1) in ((MA_X1 - 0.01, MA_X1 + 0.15, MA_Y0, MA_Y1), (MB_X0, MA_X1, MB_Y0 - 0.15, MB_Y0 + 0.01),
                                 (MB_X0 - 0.15, MB_X0 + 0.01, MB_Y0, MB_Y1), (MA_X0, MA_X1, MA_Y1 - 0.01, MA_Y1 + 0.15)):
            k.box(accent, x0, x1, y0, y1, FF - 0.5, FF + 1.2)
            k.box(accent, x0, x1, y0, y1, F2 - 0.6, F2 + 0.2)                                    # floor line band
        for x, y in ((MA_X1, MA_Y0), (MA_X1, MA_Y1), (MB_X0, MB_Y0), (MB_X0, MB_Y1)):
            k.box("Plaster_D9C4A0", x - 0.7, x + 0.7, y - 0.7, y + 0.7, FF, MPT)
        # door + window frames
        for a in roomsA:
            for z in (FF, F2):
                bp.frame(k, "Plaster_F2EDE2", "y", MA_X0, -1, a + 1.5, a + 6.1, z, z + 7.4, sill=False)
                bp.frame(k, bp.AL, "y", MA_X0, -1, a + 7.5, a + 13.5, z + 3.0, z + 7.4, w=0.3)
                bp.frame(k, "Plaster_F2EDE2", "y", MA_X1, +1, a + 9, a + 12, z + 5.0, z + 7.4, w=0.25)
        for a in roomsB:
            for z in (FF, F2):
                bp.frame(k, "Plaster_F2EDE2", "x", MB_Y1, +1, a + 1.5, a + 6.1, z, z + 7.4, sill=False)
                bp.frame(k, bp.AL, "x", MB_Y1, +1, a + 7.5, a + 13.5, z + 3.0, z + 7.4, w=0.3)
                bp.frame(k, "Plaster_F2EDE2", "x", MB_Y0, -1, a + 9, a + 12, z + 5.0, z + 7.4, w=0.25)
        # railings: upper walkways + landings + stairs
        R = "Metal_2E2E2E"
        bp.railing(k, R, (MA_X0 - 5.9, MB_Y1 + 6.1), (MA_X0 - 5.9, MA_Y1 - 2), F2)
        bp.railing(k, R, (MA_X0 - 12, MA_Y1 + 3.9), (MA_X0 - 0.2, MA_Y1 + 3.9), F2)
        bp.railing(k, R, (MB_X0 + 3.2, MB_Y1 + 5.9), (MA_X0 - 6.2, MB_Y1 + 5.9), F2)
        bp.railing(k, R, (MB_X0 - 5.9, MB_Y1 - 8), (MB_X0 - 5.9, MB_Y1 + 11.7), F2)
        for z0, (p, q) in ((FF, ((MA_X0 - 11.9, MA_Y1 - 2 - 18.7), (MA_X0 - 11.9, MA_Y1 - 2))),
                           (FF, ((MA_X0 - 6.1, MA_Y1 - 2 - 18.7), (MA_X0 - 6.1, MA_Y1 - 2)))):
            k.tube(R, (p[0], p[1], z0 + 3.3), (q[0], q[1], F2 + 3.3), 0.14)
            for t in range(0, 19, 3):
                yy = p[1] + t
                zz = z0 + (F2 - z0) * t / 18.7
                k.box(R, p[0] - 0.1, p[0] + 0.1, yy - 0.1, yy + 0.1, zz, zz + 3.3)
        xs0 = MB_X0 - 3 + 17 * 1.1 + 6
        for yy in (MB_Y1 + 6.15, MB_Y1 + 11.85):
            k.tube(R, (xs0, yy, FF + 3.3), (xs0 - 18.7, yy, F2 + 3.3), 0.14)
            for t in range(0, 19, 3):
                xx = xs0 - t
                zz = FF + (F2 - FF) * t / 18.7
                k.box(R, xx - 0.1, xx + 0.1, yy - 0.1, yy + 0.1, zz, zz + 3.3)
        # office trim
        OX0, OX1, OY0, OY1 = 1070, 1110, 468, 504
        bp.coping(k, "Metal_8F8C84", OX0, OX1, OY0, OY1, FF + 14)
        k.box(accent, OX0 - 0.15, OX1 + 0.15, OY0 - 0.15, OY1 + 0.15, FF - 0.5, FF + 1.2)
        k.box(accent, 1109.8, 1148.3, 473.8, 506.2, FF + 12.3, FF + 12.7)
        k.box("Metal_8F8C84", 1109.7, 1148.3, 473.7, 506.3, FF + 14.0, FF + 14.3)
        bp.frame(k, bp.AL, "x", OY1, +1, 1080, 1098, FF + 1.0, FF + 9.0)
        bp.frame(k, bp.AL, "x", OY1, +1, 1100, 1104.6, FF, FF + 7.4, sill=False)
        bp.frame(k, bp.AL, "y", OX0, -1, 476, 496, FF + 2.5, FF + 8.5)
        for xx in (1086, 1092):
            k.box(bp.AL, xx - 0.15, xx + 0.15, OY1, OY1 + 0.25, FF + 1.0, FF + 9.0)
    if "C" in PASSES:
        k.P("C")
        n = 0
        for i, a in enumerate(roomsA):
            for z in (FF, F2):
                n += 1
                k.plane(f"Decal_room_{(n - 1) % 30 + 1:02d}", (MA_X0 - 0.08, a + 3.8, z + 6.3), 1.0, 1.0, "x-")
                bp.ptac(k, "y", MA_X0, -1, a + 10.5, z + 1.0)
                if ("A", i, z) not in boarded:
                    k.box(["Fabric_B8865A", "Fabric_7A6A9C", "Fabric_C9B48A", "Fabric_8C3A2E"][(i + int(z)) % 4],
                          MA_X0 + 0.7, MA_X0 + 0.8, a + 7.5, a + 13.5, z + 3.0, z + 7.3)
                if rng.random() < 0.35:
                    bp.chair(k, MA_X0 - 2.0, a + 8.0, z, math.pi / 2 * 3, "SmoothPlastic_E9E6DC")
                if rng.random() < 0.3:
                    k.plane(f"Decal_decal_drip_{rng.randrange(3)}", (MA_X0 - 0.05, a + 10.5, z + 1.2), 3.2, 2.4, "x-")
        for i, a in enumerate(roomsB):
            for z in (FF, F2):
                n += 1
                k.plane(f"Decal_room_{(n - 1) % 30 + 1:02d}", (a + 3.8, MB_Y1 + 0.08, z + 6.3), 1.0, 1.0, "y+")
                bp.ptac(k, "x", MB_Y1, +1, a + 10.5, z + 1.0)
                if ("B", i, z) not in boarded:
                    k.box(["Fabric_B8865A", "Fabric_7A6A9C", "Fabric_C9B48A", "Fabric_8C3A2E"][(i + int(z) + 1) % 4],
                          a + 7.5, a + 13.5, MB_Y1 - 0.8, MB_Y1 - 0.7, z + 3.0, z + 7.3)
                if rng.random() < 0.3:
                    bp.chair(k, a + 8.0, MB_Y1 + 2.0, z, 0.0, "SmoothPlastic_E9E6DC")
        # roof: swamp coolers every other room + dishes
        for a in roomsA[::2]:
            bp.swamp_cooler(k, MA_X0 + 12, a + 7, MRZ, s=0.85)
        for a in roomsB[1::2]:
            bp.swamp_cooler(k, a + 7, MB_Y0 + 12, MRZ, s=0.85)
        bp.satellite(k, MA_X1 - 3, 600, MRZ)
        bp.satellite(k, 1200, MB_Y0 + 3, MRZ, yaw=2.0)
        # ice machine + vending under the stairs, housekeeping cart, laundry bags
        k.box("Metal_C9CBCB", MA_X0 - 4.6, MA_X0 - 0.4, MA_Y1 - 26, MA_Y1 - 22, FF, FF + 6.2)
        k.box("Metal_B83A2E", MA_X0 - 4.6, MA_X0 - 0.4, MA_Y1 - 21, MA_Y1 - 17.5, FF, FF + 6.6)
        k.box("Glass_1F2A30", MA_X0 - 4.7, MA_X0 - 4.6, MA_Y1 - 20.5, MA_Y1 - 18, FF + 2.5, FF + 6.0)
        k.box("Metal_9EA2A3", 1240, 1244, MB_Y1 + 1.0, MB_Y1 + 3.0, FF, FF + 3.5)
        k.box("Fabric_E9E6DC", 1240.2, 1243.8, MB_Y1 + 1.2, MB_Y1 + 2.8, FF + 3.5, FF + 4.4)
        # graffiti + drips on the street-facing backs; pool trash
        k.plane("Decal_decal_tag_0", (MA_X1 + 0.06, 520, FF + 4.0), 14, 5.2, "x+")
        k.plane("Decal_decal_tag_4", (1240, MB_Y0 - 0.06, FF + 4.0), 14, 5.2, "y-")
        for x in range(1170, 1330, 34):
            k.plane(f"Decal_decal_drip_{x % 3}", (x, MB_Y0 - 0.05, MPT - 4.5), 4.0, 8.0, "y-")
        bp.shopping_cart(k, 1192, 574, -2.6, 0.9)
        for x, y in ((1180, 590), (1204, 570)):
            k.cyl("Rubber_202020", x, y, -2.6, 1.3, 0.9, segs=10)
        bp.tumbleweed(k, 1176, 566, -2.6, rng)
        bp.tumbleweed(k, 1210, 594, -2.6, rng)
        # signs: tall pole sign at the arterial corner + office sign
        k.cyl("Metal_2F6E73", 1056.5, 528, LG + 0.35, 0.8, 20.0, segs=10)
        k.sign("motel_pole", (1056.5, 528, LG + 30.0), 10.0, 20.0, "x-", depth=1.2, cabinet="Metal_1F4E55", both=True)
        k.plane("Sign_motel_office", (1069.92, 486, FF + 10.6), 8.0, 2.0, "x-")
        k.plane("Sign_motel_office", (1090, 504.08, FF + 10.6), 8.0, 2.0, "y+")
        k.box("Neon_FF3B30", 1088, 1094, 503.3, 503.4, FF + 7.4, FF + 8.4)                  # VACANCY neon behind glass
        bp.wall_pack(k, "x", MB_Y0, -1, 1200, FF + 9.0)
        bp.wall_pack(k, "y", MA_X1, +1, 560, FF + 9.0)
    return k.finish()


# ====================================================================== render
SHOTS = {
    "overview": ((975, 905, 175), (1215, 640, 4), 26),
    "plaza": ((1188, 792, 7.5), (1246, 738, 11), 24),
    "topdog": ((1036, 778, 6.5), (1080, 800, 10), 26),
    "alley": ((1058, 668, 7.5), (1300, 668, 9), 24),
    "courtyard": ((1172, 640, 10), (1330, 494, 12), 22),
    "elsol": ((1032, 592, 6.5), (1082, 628, 10), 24),
    "motel_street": ((1392, 430, 8), (1330, 520, 14), 24),
    "plaza_rear": ((1205, 664, 6.5), (1246, 680, 9), 22),
}


def lights(sc):
    sun = bpy.data.lights.get("WG_Sun") or bpy.data.lights.new("WG_Sun", "SUN")
    sun.energy = 4.6
    sun.color = (1.0, 0.95, 0.86)
    sun.angle = math.radians(1.5)
    so = bpy.data.objects.new("WG_Sun", sun)
    so.rotation_euler = (math.radians(48), math.radians(10), math.radians(-128))
    sc.collection.objects.link(so)
    w = bpy.data.worlds.get("WG_World") or bpy.data.worlds.new("WG_World")
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    bg = nt.nodes.new("ShaderNodeBackground")
    out = nt.nodes.new("ShaderNodeOutputWorld")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.78, 0.76, 0.72, 1)
    ramp.color_ramp.elements[1].position = 0.45
    ramp.color_ramp.elements[1].color = (0.25, 0.45, 0.85, 1)
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.8
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    sc.world = w
    try:
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass


def render(sc, shots, tag):
    import mathutils
    try:
        sc.render.engine = "BLENDER_EEVEE"
    except TypeError:
        sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.render.resolution_x, sc.render.resolution_y = 1600, 900
    try:
        sc.eevee.taa_render_samples = 48
    except AttributeError:
        pass
    cam = bpy.data.cameras.get("WG_Cam") or bpy.data.cameras.new("WG_Cam")
    cam.clip_start, cam.clip_end = 0.2, 5000
    ob = bpy.data.objects.get("WG_Cam") or bpy.data.objects.new("WG_Cam", cam)
    if ob.name not in sc.collection.objects:
        sc.collection.objects.link(ob)
    sc.camera = ob
    od = os.path.join(REPO, "renders", "westgate", "wg01")
    os.makedirs(od, exist_ok=True)
    out = []
    for nm in shots:
        loc, tgt, lens = SHOTS[nm]
        cam.lens = lens
        ob.location = loc
        ob.rotation_euler = (mathutils.Vector(tgt) - mathutils.Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(od, f"{tag}_{nm}.png")
        bpy.ops.render.render(write_still=True, scene=sc.name)
        out.append(sc.render.filepath)
    return out


def tri_report(objs):
    big = []
    tot = 0
    for o in objs:
        t = sum(len(p.vertices) - 2 for p in o.data.polygons)
        tot += t
        if t > 18000:
            big.append((o.name, t))
    return tot, big


sc = scene()
lights(sc)
ctx = context(sc)
built = []
for fn in (site, plaza, topdog, elsol, motel):
    built += fn(sc)
for o in built + ctx:
    o.data.shade_flat() if hasattr(o.data, "shade_flat") else None
tot, big = tri_report(built)
print(f"WG01 passes={PASSES}: {len(built)} objects, {tot:,} tris, over-budget: {big}")
if globals().get("WG_RENDER"):
    print(render(sc, WG_RENDER, PASSES))
if globals().get("WG_EXPORT"):
    k = importlib.import_module("rmd_kit")
    importlib.reload(k)
    groups = {}
    for o in built:
        groups.setdefault(o.name.split("_")[1], []).append(o.name)
    for g, names in groups.items():
        k.export_fbx(os.path.join(REPO, "exports", "westgate", "wg01", f"WG01_{g}.fbx"), names, apply_modifiers=False)

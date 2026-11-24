"""Westgate block WG01 (Roblox X 1052..1368, Z -824..-452; Blender x same, y = -Z: 452..824, north = +y).

exec(open(r"<repo>/blender/blocks/wg01.py").read())     optional globals before exec:
  WG_PASSES = "MTC"     passes to build (M massing, T trim, C character)
  WG_RENDER = [...]     shots -> renders/westgate/wg01/<passes>_<shot>.png
  WG_QA = True          clash / floating checks (bqa) -> plans/westgate/qa_wg01.txt
Layout: Sunset Plaza strip centre + Top Dog stand (north half), alley, El Sol taqueria + Desert Rose Motor Lodge (south).
Grades: street 2.2, sidewalk / lot 2.8, building floors 3.3 (Roblox Y). Doors/windows are prototypes (bparts).
Pieces (k.S) become separate Roblox models in the chopped export (bexport.py).
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
import bparts
import bprops as bp
import bqa
for _m in (bkit, bparts, bp, bqa):
    importlib.reload(_m)
from bkit import Kit, yaw_out

PASSES = globals().get("WG_PASSES", "MTC")
bparts.PASSES = PASSES
LG, FF = 2.8, 3.3
ST = 2.2
rng = random.Random(1)
HAS = PASSES.__contains__
KITS = []

ASPH = "Asphalt_58585A"
CONC = "Concrete_BDB6A8"
CURBC = "Concrete_A9A397"
MULCH = "Pebble_9E6A4C"
PAINT_W = "SmoothPlastic_E6E3D8"
PAINT_Y = "SmoothPlastic_D8B23A"
PAINT_R = "SmoothPlastic_B03A2E"
PAINT_B = "SmoothPlastic_2F5FA8"
OUT = {"N": (0, 1), "S": (0, -1), "E": (1, 0), "W": (-1, 0)}


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


def coll(sc, name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or sc.collection).children.link(c)
    return c


def newkit(name, sc):
    k = Kit(name, coll(sc, name))
    KITS.append(k)
    return k


# ====================================================================== shared helpers
def place_on(k, proto, face, along, z, wall_face):
    """Place a prototype in a wall: face = outward side 'N','S','E','W'; wall_face = outer face coordinate;
    along = opening centre along the wall; z = bottom of the opening."""
    nx, ny = OUT[face]
    if face in "NS":
        k.place(proto, along, wall_face, z, yaw_out(nx, ny))
    else:
        k.place(proto, wall_face, along, z, yaw_out(nx, ny))


def _minus(span, gaps):
    out = [span]
    for g0, g1 in sorted(gaps):
        nxt = []
        for a, b in out:
            if g1 <= a or g0 >= b:
                nxt.append((a, b))
            else:
                if g0 > a:
                    nxt.append((a, g0))
                if g1 < b:
                    nxt.append((g1, b))
        out = nxt
    return [(a, b) for a, b in out if b - a > 0.05]


def band(k, mat, x0, x1, y0, y1, z0, z1, proud=0.15, gaps=None, faces="NSEW"):
    """Band on the outside of a rectangular footprint (touching the wall faces) with gaps at openings."""
    gaps = gaps or {}
    with k.part("band"):
        for f in faces:
            if f in "NS":
                yy0, yy1 = (y1, y1 + proud) if f == "N" else (y0 - proud, y0)
                for a, b in _minus((x0 - proud, x1 + proud), gaps.get(f, ())):
                    k.box(mat, a, b, yy0, yy1, z0, z1)
            else:
                xx0, xx1 = (x1, x1 + proud) if f == "E" else (x0 - proud, x0)
                for a, b in _minus((y0, y1), gaps.get(f, ())):
                    k.box(mat, xx0, xx1, a, b, z0, z1)


def cap(k, mat, axis, f0, f1, a0, a1, z, w=0.15, h=0.35):
    """Coping cap over a wall segment (thickness f0..f1, length a0..a1)."""
    if axis == "x":
        k.box(mat, a0 - w, a1 + w, f0 - w, f1 + w, z, z + h)
    else:
        k.box(mat, f0 - w, f1 + w, a0 - w, a1 + w, z, z + h)


def quoin(k, mat, x, y, sx, sy, z0, z1, proud=0.18, leg=1.2):
    """Corner trim wrapping an outside corner at (x, y); sx/sy = outward directions of the two faces."""
    xa, xb = sorted((x, x + sx * proud))
    ya, yb = sorted((y, y - sy * leg))
    k.box(mat, xa, xb, ya, yb, z0, z1)
    xa, xb = sorted((x + sx * proud, x - sx * leg))
    ya, yb = sorted((y, y + sy * proud))
    k.box(mat, xa, xb, ya, yb, z0, z1)


# things standing in the landscape islands that plants must keep clear of: (x, y, radius)
BLOCKS = [(1056, 760, 5.5), (1056, 586, 2.0), (1056, 596, 2.0), (1056.5, 528, 2.5), (1170, 820, 2.0), (1290, 820, 2.0),
          (1054, 768, 1.0), (1364, 768, 1.0), (1140, 818, 1.0), (1160, 818, 2.0), (1056, 520, 2.0), (1057, 603, 1.0)]
PLANTED = []


def _free(x, y, r):
    return all((x - bx) ** 2 + (y - by) ** 2 > (r + br) ** 2 for bx, by, br in BLOCKS + PLANTED)


def island(k, x0, x1, y0, y1, mulch=MULCH, plants=0):
    with k.ground():
        if HAS("M"):
            k.P("M").box(mulch, x0 + 0.5, x1 - 0.5, y0 + 0.5, y1 - 0.5, LG - 0.2, LG + 0.35)
        if HAS("T"):
            k.P("T")
            k.box(CURBC, x0, x1, y0, y0 + 0.5, LG - 0.2, LG + 0.5)
            k.box(CURBC, x0, x1, y1 - 0.5, y1, LG - 0.2, LG + 0.5)
            k.box(CURBC, x0, x0 + 0.5, y0 + 0.5, y1 - 0.5, LG - 0.2, LG + 0.5)
            k.box(CURBC, x1 - 0.5, x1, y0 + 0.5, y1 - 0.5, LG - 0.2, LG + 0.5)
    if HAS("C") and plants:
        k.P("C")
        for i in range(plants):
            for _try in range(40):
                x = rng.uniform(x0 + 2.6, x1 - 2.6)
                y = rng.uniform(y0 + 2.6, y1 - 2.6)
                if _free(x, y, 2.7):
                    break
            else:
                continue
            PLANTED.append((x, y, 2.7))
            r = rng.random()
            if r < 0.4:
                bp.yucca(k, x, y, LG + 0.35, rng)
            elif r < 0.7:
                bp.boulder(k, x, y, LG + 0.35, rng, s=rng.uniform(1.2, 2.2))
            else:
                bp.juniper(k, x, y, LG + 0.35, rng, r=rng.uniform(1.4, 2.0))


def apron(k, axis, curb, out, a0, a1, flare=3.0):
    zt, zb = LG + 0.04, ST - 0.05
    o = curb + out * 5.0
    if axis == "y":
        bot = [(curb, a0 - flare, zb), (curb, a1 + flare, zb), (o, a1, zb), (o, a0, zb)]
        top = [(curb, a0 - flare, zt), (curb, a1 + flare, zt), (o, a1, ST + 0.02), (o, a0, ST + 0.02)]
    else:
        bot = [(a0 - flare, curb, zb), (a1 + flare, curb, zb), (a1, o, zb), (a0, o, zb)]
        top = [(a0 - flare, curb, zt), (a1 + flare, curb, zt), (a1, o, ST + 0.02), (a0, o, ST + 0.02)]
    a = sum(bot[i][0] * bot[(i + 1) % 4][1] - bot[(i + 1) % 4][0] * bot[i][1] for i in range(4))
    if a < 0:
        bot, top = bot[::-1], top[::-1]
    with k.ground():
        k.hexa(CONC, bot + top)


def stalls(k, x0, y0, n, w, depth, axis="x", nose=+1, stops=True, oil=True, accessible=()):
    """A row of n stalls; (x0, y0) is the aisle-side corner, nose points away from the aisle."""
    for i in range(n + 1):
        a = i * w
        if HAS("T"):
            k.P("T")
            with k.ground():
                if axis == "x":
                    ys = (y0 + 1.0, y0 + depth - 0.5) if nose > 0 else (y0 - depth + 0.5, y0 - 1.0)
                    k.box(PAINT_W, x0 + a - 0.2, x0 + a + 0.2, min(ys), max(ys), LG, LG + 0.03)
                else:
                    xs = (x0 + 1.0, x0 + depth - 0.5) if nose > 0 else (x0 - depth + 0.5, x0 - 1.0)
                    k.box(PAINT_W, min(xs), max(xs), y0 + a - 0.2, y0 + a + 0.2, LG, LG + 0.03)
    for i in range(n):
        c = (i + 0.5) * w
        if axis == "x":
            sx, sy, yaw = x0 + c, y0 + nose * (depth - 2.0), 0.0
        else:
            sx, sy, yaw = x0 + nose * (depth - 2.0), y0 + c, math.pi / 2
        if HAS("T") and stops:
            k.P("T")
            bp.wheel_stop(k, sx, sy, LG, yaw)
        if i in accessible and HAS("T"):
            k.P("T")
            with k.ground():
                if axis == "x":
                    k.box(PAINT_B, x0 + i * w + 0.3, x0 + (i + 1) * w - 0.3, min(y0, y0 + nose * depth), max(y0, y0 + nose * depth), LG, LG + 0.025)
                else:
                    k.box(PAINT_B, min(x0, x0 + nose * depth), max(x0, x0 + nose * depth), y0 + i * w + 0.3, y0 + (i + 1) * w - 0.3, LG, LG + 0.025)
        if i in accessible and HAS("C"):
            k.P("C")
            mx = sx if axis == "x" else x0 + nose * depth * 0.45
            my = y0 + nose * depth * 0.45 if axis == "x" else sy
            k.plane("Decal_accessible", (mx, my, LG + 0.04), 5.0, 6.5, "z+")
        if HAS("C") and oil and rng.random() < 0.6:
            k.P("C")
            mx = sx if axis == "x" else x0 + nose * depth * 0.5
            my = y0 + nose * depth * 0.5 if axis == "x" else sy
            k.plane(f"Decal_decal_oil_{rng.randrange(3)}", (mx + rng.uniform(-1, 1), my + rng.uniform(-1, 1), LG + 0.035),
                    rng.uniform(4, 7), rng.uniform(4, 7), "z+")


# ====================================================================== context (preview only, not exported)
def context(sc):
    k = Kit("WG01_Context", coll(sc, "WG01_Context"))
    road, walk = "Asphalt_3A3A3C", "Concrete_C6C0B4"
    k.box(road, 940, 1460, 380, 444, ST - 0.4, ST)
    k.box(road, 940, 1460, 832, 900, ST - 0.4, ST)
    k.box(road, 940, 1044, 444, 832, ST - 0.4, ST)
    k.box(road, 1376, 1460, 444, 832, ST - 0.4, ST)
    for (x0, x1, y0, y1) in ((1044, 1052, 444, 832), (1368, 1376, 444, 832), (1052, 1368, 444, 452), (1052, 1368, 824, 832)):
        k.box(walk, x0, x1, y0, y1, ST - 0.2, LG)
    k.box(walk, 976, 984, 380, 900, ST - 0.2, LG)
    k.box(walk, 1404, 1412, 380, 900, ST - 0.2, LG)
    k.box(walk, 940, 1460, 408, 416, ST - 0.2, LG)
    k.box(walk, 940, 1460, 860, 868, ST - 0.2, LG)
    k.box("Ground_B89B72", 600, 1900, 0, 1300, 1.0, 1.95)
    for y in range(390, 900, 40):
        k.box(PAINT_W, 1013.5, 1014.0, y, y + 10, ST, ST + 0.02)
    k.box(PAINT_Y, 1013.0, 1013.4, 380, 900, ST, ST + 0.02)
    k.box(PAINT_Y, 1014.6, 1015.0, 380, 900, ST, ST + 0.02)
    return k.finish()


# ====================================================================== site: lots, alley, islands, poles
def site(sc):
    k = newkit("WG01_Site", sc)
    if HAS("M"):
        k.P("M").S("Paving")
        with k.ground():
            k.box(ASPH, 1052, 1368, 738, 824, LG - 0.6, LG)
            k.box(ASPH, 1052, 1138, 678, 738, LG - 0.6, LG)
            k.box(ASPH, 1052, 1368, 452, 658, LG - 0.6, LG)
            k.S("Alley")
            k.box("Concrete_A39D91", 1052, 1368, 658, 678, LG - 0.6, LG - 0.02)
            k.box("Concrete_8F897D", 1052, 1368, 667.3, 668.7, LG - 0.6, LG - 0.06)
            k.S("Slabs")
            k.box(CONC, 1136, 1360, 738, 748.5, LG - 0.3, FF)
            k.box(CONC, 1138, 1358, 678, 738, LG - 0.3, FF)
            k.box(CONC, 1058, 1098, 782, 818, LG - 0.3, LG + 0.2)
            k.box(CONC, 1060, 1068, 603, 649, LG - 0.3, FF)
            k.box(CONC, 1068, 1112, 604, 648, LG - 0.3, FF)
            k.box(CONC, 1068, 1112, 466, 506, LG - 0.3, FF)
            k.box(CONC, 1324.8, 1356, 458, 646, LG - 0.3, FF)          # wing A + ground walk (post bases)
            k.box(CONC, 1150, 1324.8, 458, 489.2, LG - 0.3, FF)        # wing B + ground walk
            k.box(CONC, 1316, 1324.8, 620, 650, LG - 0.3, FF)          # under stair A
            k.box(CONC, 1144, 1172, 489.2, 496, LG - 0.3, FF)          # under stair B
            k.S("Pool")
            k.box(CONC, 1166, 1220, 556, 562, LG - 0.3, LG + 0.25)
            k.box(CONC, 1166, 1220, 598, 604, LG - 0.3, LG + 0.25)
            k.box(CONC, 1166, 1172, 562, 598, LG - 0.3, LG + 0.25)
            k.box(CONC, 1214, 1220, 562, 598, LG - 0.3, LG + 0.25)
            k.box("Plaster_8DB4BE", 1172, 1214, 562, 563, -2.6, LG + 0.25)
            k.box("Plaster_8DB4BE", 1172, 1214, 597, 598, -2.6, LG + 0.25)
            k.box("Plaster_8DB4BE", 1172, 1173, 563, 597, -2.6, LG + 0.25)
            k.box("Plaster_8DB4BE", 1213, 1214, 563, 597, -2.6, LG + 0.25)
            k.box("Plaster_A9C3C6", 1173, 1213, 563, 597, -3.0, -2.6)
        k.S("Aprons")
        apron(k, "y", 1043.5, -1, 770, 794)
        apron(k, "y", 1043.5, -1, 658, 678)
        apron(k, "y", 1376.5, +1, 770, 794)
        apron(k, "y", 1376.5, +1, 658, 678)
        apron(k, "x", 444.5, -1, 1112, 1146)
        k.S("BlockWall")
        with k.part("cmu_wall"):
            for a, b in ((1146, 1290), (1310, 1368)):
                k.P("M").box("Concrete_B5AE9F", a, b, 655.5, 656.5, LG, LG + 6.5)
                for x in range(int(a) + 16, int(b) - 4, 16):
                    k.box("Concrete_B5AE9F", x - 0.6, x + 0.6, 654.9, 655.5, LG, LG + 6.5)
                if HAS("T"):
                    k.P("T").box("Concrete_C9C2B2", a, b, 655.3, 656.7, LG + 6.5, LG + 6.8)
    k.S("Landscape")
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
    k.S("Striping")
    stalls(k, 1108, 794, 22, 11.0, 22.0, "x", +1)
    stalls(k, 1108, 770, 22, 11.0, 22.0, "x", -1, accessible=(9, 10))
    stalls(k, 1304, 500, 11, 11.0, 20.0, "y", +1, accessible=(0,))
    stalls(k, 1180, 510, 11, 11.0, 20.0, "x", -1)
    stalls(k, 1140, 600, 4, 11.0, 22.0, "y", -1)
    stalls(k, 1060, 700, 3, 11.0, 22.0, "x", +1)
    if HAS("T"):
        k.P("T").S("Striping")
        with k.ground():
            k.box(PAINT_R, 1136, 1140, 748.0, 748.5, FF - 0.02, FF + 0.01)
        for x in (1137.5, 1358.5):
            bp.bollard(k, x, 742, FF)
        k.S("Pool")
        with k.part("pool_fence"):
            for seg in (((1166.4, 556.4), (1219.6, 556.4)), ((1166.4, 603.6), (1219.6, 603.6)), ((1166.4, 556.4), (1166.4, 603.6)), ((1219.6, 556.4), (1219.6, 603.6))):
                bp.railing(k, "Metal_2E2E2E", seg[0], seg[1], LG + 0.25, h=4.2, pitch=0.55, r=0.06)
        with k.part("pool_ladder"):
            for yy in (566, 568.5):
                k.tube("Metal_C9CBCB", (1210.5, yy, LG + 3.5), (1212.6, yy, LG + 0.25), 0.12)
                k.tube("Metal_C9CBCB", (1212.6, yy, LG + 0.25), (1212.6, yy, -2.6), 0.12)
            for zz in (-1.6, -0.4, 0.8):
                k.box("Metal_C9CBCB", 1212.45, 1212.75, 566, 568.5, zz, zz + 0.12)
        with k.ground():
            k.box("Concrete_D2CBBE", 1171, 1215, 561, 562, LG + 0.25, LG + 0.4)
            k.box("Concrete_D2CBBE", 1171, 1215, 598, 599, LG + 0.25, LG + 0.4)
    if HAS("C"):
        k.P("C").S("Wear")
        for _ in range(16):
            x, y = rng.uniform(1110, 1355), rng.uniform(745, 815)
            k.plane(f"Decal_decal_cracks_{rng.randrange(3)}", (x, y, LG + 0.03), rng.uniform(12, 22), rng.uniform(12, 22), "z+")
        for _ in range(18):
            x, y = rng.uniform(1125, 1300), rng.uniform(515, 650)
            k.plane(f"Decal_decal_cracks_{rng.randrange(3)}", (x, y, LG + 0.03), rng.uniform(12, 22), rng.uniform(12, 22), "z+")
        for _ in range(6):
            x, y = rng.uniform(1060, 1360), rng.uniform(660, 676)
            k.plane(f"Decal_decal_cracks_{rng.randrange(3)}", (x, y, LG + 0.0), rng.uniform(8, 14), rng.uniform(8, 12), "z+")
        k.S("Utility")
        pxs = (1066, 1146, 1226, 1306, 1362)
        poles = [bp.utility_pole(k, x, 657.5 if x != 1362 else 660, LG, h=34, arm_yaw=math.pi / 2, transformer=(x == 1226))
                 for x in pxs]
        for a, b in zip(poles[:-1], poles[1:]):
            for i in (0, 1, 3):
                bp.wire(k, a[i], b[i], sag=1.6)
        for (px, i, wx, wy, wz, face) in ((1146, 4, 1166, 678, 16.2, "S"), (1306, 4, 1286, 678, 16.2, "S")):
            pole = poles[pxs.index(px)]
            ny = -1 if face == "S" else 1
            y0, y1 = sorted((wy, wy + ny * 0.5))
            with k.part("weatherhead"):
                k.box("Metal_8F9293", wx - 0.15, wx + 0.15, y0, y1, wz - 4.0, wz + 1.0)
                k.box("Metal_3A3A3A", wx - 0.25, wx + 0.25, y0 - 0.05, y1, wz + 1.0, wz + 1.35)
            bp.wire(k, pole[i], (wx, wy + ny * 0.25, wz + 1.6), sag=1.0)
        k.S("Lighting")
        for x in (1170, 1290):
            bp.shoebox_light(k, x, 820, LG + 0.35, h=26, heads=((0, -1),))
        bp.shoebox_light(k, 1250, 548, LG, h=24, heads=((1, 0), (-1, 0)))
        k.S("Clutter")
        bp.dumpster(k, 1180, 671, LG, 0.0)
        bp.dumpster(k, 1262, 671, LG, 0.05, color="Metal_2D4F7A")
        bp.dumpster(k, 1128, 651.5, LG, math.pi / 2)
        bp.pallet(k, 1200, 674, LG, 0.1)
        bp.pallet(k, 1200.3, 674.2, LG + 0.52, 0.4)
        bp.barrel(k, 1320, 673, LG)
        bp.barrel(k, 1322.4, 674, LG, color="Metal_2F6B3E")
        bp.shopping_cart(k, 1236, 760, LG, 0.7)
        for x, y, z in ((1150, 659.5, LG - 0.6), (1290, 659.5, LG - 0.6), (1366, 760, LG - 0.35), (1160, 818, LG), (1056, 520, LG - 0.4)):
            bp.tumbleweed(k, x, y, z, rng, r=rng.uniform(0.9, 1.5))
        bp.news_box(k, 1150, 742, FF)
        bp.news_box(k, 1153, 742, FF, color="Metal_B83A2E")
        k.plane("Decal_decal_tag_0", (1200, 656.55, LG + 3.2), 14, 5.2, "y+")
        k.plane("Decal_decal_tag_3", (1335, 656.55, LG + 3.0), 12, 4.5, "y+")
        k.S("Signs")
        x, y = 1056, 760
        with k.part("pylon"):
            k.box("Plaster_C9B38F", x - 1.6, x + 1.6, y - 4.5, y + 4.5, LG + 0.35, LG + 4.0)
            k.box("Concrete_A39D91", x - 1.8, x + 1.8, y - 4.7, y + 4.7, LG + 4.0, LG + 4.3)
            k.box("Metal_4A4C4E", x - 0.5, x + 0.5, y - 0.5, y + 0.5, LG + 4.3, LG + 13.0)
            k.sign("plaza_pylon", (x, y, LG + 21.0), 8.0, 16.0, "x-", depth=1.2, cabinet="Metal_3A2A20", both=True)
        for (sx, sy, nrm) in ((1054, 768, "x-"), (1364, 768, "x+")):
            with k.part("tow_sign"):
                k.box("Metal_9EA2A3", sx - 0.12, sx + 0.12, sy - 0.12, sy + 0.12, LG, LG + 10.3)
                k.plane("Sign_tow_away", (sx + (-0.14 if nrm == "x-" else 0.14), sy, LG + 9.2), 2.4, 1.8, nrm)
        with k.part("cust_sign"):
            k.box("Metal_9EA2A3", 1140, 1140.24, 818, 818.24, LG + 0.35, LG + 9.2)
            k.plane("Sign_customer_parking", (1140.12, 817.98, LG + 8.0), 2.4, 1.8, "y-")
    return k.finish()


# ====================================================================== Sunset Plaza (strip centre)
BAYS = [30, 30, 32, 30, 30, 32, 32]
TENANT = ["plaza_lucky7", "plaza_ink", "plaza_pho", "plaza_cuts", "plaza_lease", "plaza_bail", "plaza_cash"]
PX0, PX1, PY0, PY1 = 1140, 1356, 678, 738
RZ, PT = FF + 14.0, FF + 16.5
MZT, MZB, MY1 = PT + 0.45, FF + 10.3, PY1 + 10.5


def mansard_z(y):
    return MZT - (y - PY1) / (MY1 - PY1) * (MZT - MZB)


def mansard_n():
    from mathutils import Vector
    return Vector((0, (MZT - MZB), (MY1 - PY1))).normalized()


def storefront_glazing(k, y_face, o0, o1):
    """Fixed aluminium storefront glazing between o0..o1 (kick plate, glass, mullions, transom bar, head, jambs)."""
    gy0, gy1 = y_face - 0.55, y_face - 0.4
    f0, f1 = y_face - 0.7, y_face - 0.25
    with k.part("glazing"):
        if HAS("M"):
            k.P("M").box("Glass_2B3438", o0 + 0.4, o1 - 0.4, gy0, gy1, FF + 1.0, FF + 9.9)
        if HAS("T"):
            k.P("T")
            k.box(bp.AL, o0, o1, f0, f1, FF + 9.9, FF + 10.0)
            k.box(bp.AL, o0, o0 + 0.4, f0, f1, FF, FF + 9.9)
            k.box(bp.AL, o1 - 0.4, o1, f0, f1, FF, FF + 9.9)
            k.box(bp.AL, o0 + 0.4, o1 - 0.4, f0, f1, FF, FF + 1.0)
            n = max(1, round((o1 - o0) / 5.5))
            for i in range(1, n):
                m = o0 + i * (o1 - o0) / n
                k.box(bp.AL, m - 0.18, m + 0.18, gy1, f1, FF + 1.0, FF + 9.9)
            k.box(bp.AL, o0 + 0.4, o1 - 0.4, gy1, f1, FF + 8.0, FF + 8.3)


def plaza(sc):
    k = newkit("WG01_Plaza", sc)
    wall = "Plaster_D9C7A3"
    xs = [PX0]
    for w in BAYS:
        xs.append(xs[-1] + w)
    bays = list(zip(xs[:-1], xs[1:]))
    front_open = [(a + 2.6, b - 2.6, FF, FF + 10.0) for a, b in bays]
    rear_door = [(a + 4.7, a + 9.9) for a, b in bays]
    rear_win = [(a + 20.0, a + 23.0) for a, b in bays]
    rear_open = [(d0, d1, FF, FF + 7.7) for d0, d1 in rear_door] + [(w0, w1, FF + 6.0, FF + 8.2) for w0, w1 in rear_win]
    doors_at = []
    if HAS("M"):
        k.P("M").S("Front")
        k.wall(wall, "x", PY1 - 1, PY1, PX0, PX1, FF, PT, front_open)
        k.S("Rear")
        k.wall("Plaster_D2C2A0", "x", PY0, PY0 + 1, PX0, PX1, FF, PT, rear_open)
        k.S("SideW")
        k.wall("Plaster_D2C2A0", "y", PX0, PX0 + 1, PY0 + 1, PY1 - 1, FF, PT, [(700, 712, FF + 3.0, FF + 7.4)])
        k.S("SideE")
        k.wall("Plaster_D2C2A0", "y", PX1 - 1, PX1, PY0 + 1, PY1 - 1, FF, PT)
        k.S("Roof")
        k.box("Concrete_8E8A84", PX0 + 1, PX1 - 1, PY0 + 1, PY1 - 1, RZ - 0.8, RZ)
        k.S("Interior")
        with k.part("interior"):
            k.box("Concrete_3B3936", PX0 + 1, PX1 - 1, PY1 - 14, PY1 - 13, FF, FF + 11.5)
            k.box("Concrete_6E675E", PX0 + 1, PX1 - 1, PY1 - 13, PY1 - 1, FF - 0.05, FF + 0.05)
            k.box("Plaster_E8E2D4", PX0 + 1, PX1 - 1, PY1 - 13, PY1 - 1, FF + 11.5, FF + 11.8)
            for x in xs[1:-1]:
                k.box("Plaster_CFC6B4", x - 0.25, x + 0.25, PY1 - 13, PY1 - 1, FF + 0.05, FF + 11.5)
    k.proto("storefront_door", bparts.storefront_door)
    k.proto("door_service", bparts.door, style="flush", leaf="Metal_8C8679", frame="Metal_6E6A62", outswing=True,
            closer=True, kick=True, hand=-1)
    k.proto("win_restroom", bparts.window, style="awning", w=3.0, h=2.2, obscure=True, open_frac=0.6, sill="Concrete_D2C8B4")
    for i, ((a, b), (o0, o1, _, _)) in enumerate(zip(bays, front_open)):
        k.S(f"Bay{i + 1}")
        d0 = o0 + 1.4 if i % 2 == 0 else o1 - 1.4 - 9.2
        doors_at.append(d0)
        k.place("storefront_door", d0 + 4.6, PY1, FF, 0.0)
        storefront_glazing(k, PY1, o0, d0 - 0.4)
        storefront_glazing(k, PY1, d0 + 9.6, o1)
        k.S("Rear")
        place_on(k, "door_service", "S", (rear_door[i][0] + rear_door[i][1]) / 2, FF, PY0)
        place_on(k, "win_restroom", "S", rear_win[i][0] + 1.5, FF + 6.0, PY0)
    k.S("SideW")
    k.proto("win_slider_12", bparts.window, style="slider", w=12.0, h=4.4, blinds=0.7)
    place_on(k, "win_slider_12", "W", 706, FF + 3.0, PX0)
    if HAS("M"):
        k.P("M").S("Mansard")
        from mathutils import Vector
        with k.part("mansard"):
            k.slab4("Metal_B8B6AE", [(PX0 - 2, MY1, MZB), (PX1 + 2, MY1, MZB), (PX1 + 2, PY1, MZT), (PX0 - 2, PY1, MZT)], 0.4)
            for xe, s in ((PX0 - 2, -1), (PX1 + 2, 1)):
                tri = [(xe, PY1, MZT), (xe, MY1, MZB), (xe, PY1, MZB)]
                k.face("Metal_B8B6AE", tri if s < 0 else tri[::-1])
                k.face("Metal_B8B6AE", tri[::-1] if s < 0 else tri)
            k.box("Plaster_E3D6BC", PX0 - 2, PX1 + 2, PY1, MY1 - 0.4, MZB - 0.8, MZB - 0.4)
            if HAS("T"):
                k.P("T")
                k.box("Metal_6F6B62", PX0 - 2.2, PX1 + 2.2, MY1, MY1 + 0.5, MZB - 0.9, MZB + 0.4)
                k.box("Metal_9C998F", PX0 - 2.2, PX1 + 2.2, PY1 - 0.3, PY1 + 0.6, MZT - 0.1, MZT + 0.35)
                n = mansard_n()
                x = PX0 - 1.5
                while x < PX1 + 2:
                    p0 = Vector((x, PY1 + 0.7, mansard_z(PY1 + 0.7))) + n * 0.08
                    p1 = Vector((x, MY1 - 0.3, mansard_z(MY1 - 0.3))) + n * 0.08
                    k.tube("Metal_A8A69E", p0, p1, 0.07, segs=4)
                    x += 2.0
        for j, x in enumerate(xs):
            with k.part(f"post{j}"):
                k.P("M").box(wall, x - 0.7, x + 0.7, MY1 - 1.8, MY1 - 0.4, FF, MZB - 0.8)
                if HAS("T"):
                    k.P("T")
                    k.box("Plaster_C4B08A", x - 0.95, x + 0.95, MY1 - 2.05, MY1 - 0.15, FF, FF + 1.2)
                    k.box("Plaster_C4B08A", x - 0.9, x + 0.9, MY1 - 2.0, MY1 - 0.2, MZB - 1.6, MZB - 0.8)
    if HAS("T"):
        k.P("T").S("Front")
        with k.part("pilasters"):
            for x in xs:
                k.box("Plaster_CDBB95", max(x - 2.2, PX0), min(x + 2.2, PX1), PY1, PY1 + 0.3, FF, MZB - 0.8)
        k.S("Rear")
        band(k, "Plaster_9C8466", PX0, PX1, PY0, PY1, FF - 0.5, FF + 1.4, faces="SEW",
             gaps={"S": [(d0 - 0.6, d1 + 0.6) for d0, d1 in rear_door]})
        band(k, "Plaster_CBB993", PX0, PX1, PY0, PY1, PT - 2.0, PT - 1.6, proud=0.2, faces="SEW")
        with k.part("coping"):
            cap(k, "Metal_8F8C84", "x", PY0, PY0 + 1, PX0, PX1, PT)
            cap(k, "Metal_8F8C84", "y", PX0, PX0 + 1, PY0 + 1, PY1 - 1, PT)
            cap(k, "Metal_8F8C84", "y", PX1 - 1, PX1, PY0 + 1, PY1 - 1, PT)
        for a, b in bays:
            with k.part("door_hood"):
                k.box("Metal_7E7A70", a + 3.8, a + 10.8, PY0 - 3.2, PY0, FF + 8.6, FF + 8.9)
                for xx in (a + 4.0, a + 10.6):
                    k.tube("Metal_5E5A52", (xx, PY0 - 3.0, FF + 8.6), (xx, PY0 - 0.08, FF + 10.2), 0.07, segs=4)
        for xx in (PX0 + 30, PX0 + 92, PX0 + 152, PX0 + 210):
            with k.part("downspout"):
                k.box("Metal_8F8C84", xx - 0.7, xx + 0.7, PY0 - 0.9, PY0, RZ - 0.4, RZ + 0.4)
                k.box("Metal_8F8C84", xx - 0.9, xx + 0.9, PY0 - 1.5, PY0 - 0.2, RZ - 2.2, RZ - 0.4)
                k.box("Metal_8F8C84", xx - 0.4, xx + 0.4, PY0 - 1.1, PY0 - 0.3, FF + 0.3, RZ - 2.2)
                for zz in (FF + 3, FF + 8):
                    k.box("Metal_6E6A62", xx - 0.5, xx + 0.5, PY0 - 0.3, PY0, zz, zz + 0.2)
                k.box("Concrete_A39D91", xx - 0.8, xx + 0.8, PY0 - 3.0, PY0 - 0.2, LG - 0.02, LG + 0.15)
        with k.part("roof_ladder"):
            lx = PX1 - 18
            for dx in (-0.9, 0.9):
                k.box("Metal_5E5A52", lx + dx - 0.12, lx + dx + 0.12, PY0 - 0.9, PY0 - 0.66, FF + 7.5, PT + 3.5)
                k.box("Metal_5E5A52", lx + dx - 0.12, lx + dx + 0.12, PY0 - 0.66, PY0, FF + 7.6, FF + 7.8)
                k.box("Metal_5E5A52", lx + dx - 0.12, lx + dx + 0.12, PY0 - 0.66, PY0 - 0.15, PT - 1.0, PT - 0.8)
            zz = FF + 8.0
            while zz < PT + 0.5:
                k.box("Metal_5E5A52", lx - 0.78, lx + 0.78, PY0 - 0.83, PY0 - 0.73, zz, zz + 0.1)
                zz += 1.0
            for zz in (FF + 12, FF + 15, PT + 1.0):
                for p, q in (((lx - 1.0, PY0 - 0.8), (lx - 1.4, PY0 - 3.2)), ((lx + 1.0, PY0 - 0.8), (lx + 1.4, PY0 - 3.2)),
                             ((lx - 1.4, PY0 - 3.2), (lx + 1.4, PY0 - 3.2))):
                    k.tube("Metal_5E5A52", (p[0], p[1], zz), (q[0], q[1], zz), 0.06, segs=4)
            for dx in (-1.4, 0.0, 1.4):
                k.box("Metal_5E5A52", lx + dx - 0.05, lx + dx + 0.05, PY0 - 3.25, PY0 - 3.15, FF + 12, PT + 1.05)
    if HAS("C"):
        k.P("C").S("Signs")
        from mathutils import Vector
        n = mansard_n()
        for (a, b), t in zip(bays, TENANT):
            cx = (a + b) / 2
            zc = FF + 13.9
            with k.part("tenant_sign"):
                k.sign(t, (cx, MY1 + 0.85, zc), min(22.0, b - a - 6), 5.5, "y+", depth=0.6, cabinet="Metal_2B2B2D")
                for dx in (-6, 6):
                    p0 = Vector((cx + dx, MY1 + 0.55, zc + 1.6))
                    yt = PY1 + 3.5
                    p1 = Vector((cx + dx, yt, mansard_z(yt))) + n * 0.02
                    k.tube("Metal_4A4C4E", p0, p1, 0.06, segs=4)
        k.S("Storefronts")
        a, b = bays[0]
        with k.part("washers"):
            for i in range(6):
                x = a + 4 + i * 4.0
                k.box("Metal_E4E4DE", x, x + 3.2, PY1 - 6, PY1 - 3.2, FF + 0.05, FF + 3.6)
                k.box("Glass_6C7A80", x + 0.7, x + 2.5, PY1 - 3.2, PY1 - 3.1, FF + 1.1, FF + 2.9)
        a, b = bays[3]
        for i in range(3):
            x = a + 7 + i * 7
            with k.part("barber_chair"):
                k.box("Fabric_7A1F1F", x, x + 2.4, PY1 - 7, PY1 - 4.6, FF + 1.6, FF + 3.4)
                k.box("Fabric_7A1F1F", x, x + 2.4, PY1 - 7, PY1 - 6.6, FF + 3.4, FF + 6.0)
                k.box("Metal_C9CBCB", x + 0.9, x + 1.5, PY1 - 6.1, PY1 - 5.5, FF + 0.05, FF + 1.6)
            k.box("Glass_9FB0B6", x - 0.5, x + 2.9, PY1 - 13.0, PY1 - 12.9, FF + 4.0, FF + 9.0)
        bp.barber_pole(k, a - 0.6, PY1 + 0.72, FF + 5.2)
        a, b = bays[4]
        k.box("SmoothPlastic_E9E4D6", a + 3.0, b - 3.0, PY1 - 0.79, PY1 - 0.71, FF + 1.2, FF + 9.8)
        k.plane("Sign_plaza_lease", ((a + b) / 2, PY1 - 0.38, FF + 6.0), 8.0, 2.0, "y+")
        for (a, b), col in zip([bays[1], bays[2], bays[5]], ["Neon_FF3B30", "Neon_FF6A00", "Neon_3BC8FF"]):
            o0 = a + 2.6
            k.box(col, o0 + 1.5, o0 + 5.5, PY1 - 0.6, PY1 - 0.55, FF + 6.2, FF + 7.4)
        for i in (5, 6):
            a, b = bays[i]
            o0, o1 = a + 2.6, b - 2.6
            with k.part("bars"):
                for s0, s1 in ((o0, doors_at[i] - 0.4), (doors_at[i] + 9.6, o1)):
                    x = s0 + 0.3
                    while x < s1 - 0.3:
                        k.box("Metal_1E1E1E", x, x + 0.14, PY1 + 0.02, PY1 + 0.2, FF + 1.0, FF + 9.3)
                        x += 0.7
                    for z in (FF + 1.2, FF + 5.0, FF + 9.1):
                        k.box("Metal_1E1E1E", s0 - 0.3, s1 + 0.3, PY1, PY1 + 0.22, z, z + 0.14)
        k.S("Walk")
        for x in (PX0 + 70, PX0 + 150):
            with k.part("bench"):
                k.box("Wood_8C6A48", x, x + 6, PY1 + 2.0, PY1 + 3.5, FF + 1.5, FF + 1.8)
                for xx in (x + 0.4, x + 5.4):
                    k.box("Metal_3A3A3A", xx, xx + 0.2, PY1 + 2.2, PY1 + 3.3, FF, FF + 1.5)
            k.cyl("Metal_5E5A52", x + 9, PY1 + 3.5, FF, 1.0, 3.2, segs=10)
        k.S("Roof")
        for i, (a, b) in enumerate(bays):
            bp.rtu(k, a + 15 + rng.uniform(-4, 4), PY0 + 22 + rng.uniform(-4, 6), RZ, yaw=0)
            with k.part("vent_stack"):
                k.cyl("Metal_9EA2A3", a + 6, PY0 + 6, RZ, 0.3, 2.2, segs=8)
                k.cyl("Rubber_202020", a + 6, PY0 + 6, RZ, 0.55, 0.25, segs=8)
        with k.part("hood_fan"):
            k.cyl("Metal_9EA2A3", bays[2][0] + 8, PY0 + 12, RZ, 1.4, 2.6, segs=12)
            k.cyl("Metal_7E7A70", bays[2][0] + 8, PY0 + 12, RZ + 2.6, 1.9, 0.5, segs=12, r2=0.6)
        bp.satellite(k, bays[1][0] + 25, PY1 - 6, RZ)
        k.box("Metal_8F8C84", PX0 + 100, PX0 + 103, PY0 + 40, PY0 + 43, RZ, RZ + 1.4)
        with k.part("conduit"):
            k.box("Metal_9EA2A3", PX0 + 20, PX1 - 20, PY0 + 9, PY0 + 9.3, RZ + 0.4, RZ + 0.7)
            for x in range(int(PX0 + 20), int(PX1 - 19), 8):
                k.box("Wood_8A7050", x - 0.4, x + 0.4, PY0 + 8.75, PY0 + 9.55, RZ, RZ + 0.4)
        k.S("Rear")
        for i, (a, b) in enumerate(bays):
            bp.wall_pack(k, "x", PY0, -1, a + 7.3, FF + 9.4)
            if i % 2 == 0:
                k.plane(f"Decal_decal_drip_{i % 3}", (a + 14, PY0 - 0.04, RZ - 4.5), 4.5, 9.0, "y-")
        bp.meter_bank(k, "x", PY0, -1, PX0 + 120, FF + 3.4, n=7)
        bp.barrel(k, bays[2][0] + 13, PY0 - 2.2, LG, color="Metal_4F4A3C")
        for dx in (0, 2.4):
            bp.chair(k, bays[3][0] + 13 + dx, PY0 - 2.2, LG, math.pi)
        k.box("SmoothPlastic_2E5CA8", bays[3][0] + 18, bays[3][0] + 19.4, PY0 - 2.6, PY0 - 1.2, LG, LG + 1.0)
        k.plane("Decal_decal_tag_1", (PX0 + 58, PY0 - 0.05, FF + 4.5), 13, 4.8, "y-")
        k.plane("Decal_decal_tag_2", (PX0 + 182, PY0 - 0.05, FF + 4.0), 12, 4.5, "y-")
        k.plane("Decal_decal_tag_4", (PX0 - 0.05, 722, FF + 5.0), 14, 5.2, "x-")
        k.plane("Decal_decal_patch", (PX0 + 125, PY0 - 0.04, FF + 11.0), 8, 6, "y-")
    return k.finish(PROTOS)


# ====================================================================== Top Dog walk-up stand
def topdog(sc):
    k = newkit("WG01_TopDog", sc)
    X0, X1, Y0, Y1 = 1066, 1090, 790, 810
    F0 = LG + 0.2
    top, par = F0 + 11.0, F0 + 12.4
    brick = "Brick_8E4A33"
    k.S("Shell")
    if HAS("M"):
        k.P("M")
        k.wall(brick, "y", X0, X0 + 1, Y0, Y1, F0, par, [(795, 805, F0 + 3.2, F0 + 7.2)])
        k.wall(brick, "x", Y0, Y0 + 1, X0 + 1, X1, F0, par, [(1079.7, 1084.9, F0, F0 + 7.7)])
        k.wall(brick, "x", Y1 - 1, Y1, X0 + 1, X1, F0, par, [(1072, 1076, F0 + 4.0, F0 + 7.0)])
        k.wall(brick, "y", X1 - 1, X1, Y0 + 1, Y1 - 1, F0, par, [(796.7, 801.9, F0, F0 + 7.7)])
        k.box("Concrete_8E8A84", X0 + 1, X1 - 1, Y0 + 1, Y1 - 1, top - 0.8, top)
        with k.part("inside"):
            k.box("Concrete_3B3936", X0 + 1, X1 - 1, Y0 + 1, Y1 - 1, F0, F0 + 0.05)
            k.box("Metal_B8BCBE", X0 + 1.5, X0 + 3, 794, 806, F0 + 0.05, F0 + 3.2)
    k.proto("win_serve", bparts.window, style="slider", w=10.0, h=4.0, sill=None, screen=False, frame="Metal_B8BCBE")
    place_on(k, "win_serve", "W", 800, F0 + 3.2, X0)
    k.proto("door_steel_red", bparts.door, style="flush", leaf="Metal_8C2F28", frame="Concrete_C8BFAE", kick=True, hand=1)
    place_on(k, "door_steel_red", "S", 1082.3, F0, Y0)
    k.proto("door_steel_grey", bparts.door, style="flush", leaf="Metal_6A6A6A", frame="Metal_6E6A62", outswing=True, closer=True)
    place_on(k, "door_steel_grey", "E", 799.3, F0, X1)
    k.proto("win_slider_4", bparts.window, style="slider", w=4.0, h=3.0, blinds=1.0)
    place_on(k, "win_slider_4", "N", 1074, F0 + 4.0, Y1)
    if HAS("T"):
        k.P("T")
        band(k, "Brick_6E3A2A", X0, X1, Y0, Y1, top - 1.6, top - 0.8, proud=0.12)
        band(k, "Concrete_A8A08F", X0, X1, Y0, Y1, F0 - 0.4, F0 + 0.6, gaps={"S": [(1079.1, 1085.5)], "E": [(796.1, 802.5)]})
        with k.part("coping"):
            cap(k, "Metal_7A7A78", "y", X0, X0 + 1, Y0, Y1, par)
            cap(k, "Metal_7A7A78", "y", X1 - 1, X1, Y0, Y1, par)
            cap(k, "Metal_7A7A78", "x", Y0, Y0 + 1, X0 + 1, X1 - 1, par)
            cap(k, "Metal_7A7A78", "x", Y1 - 1, Y1, X0 + 1, X1 - 1, par)
        with k.part("shelf"):
            k.box("Metal_B8BCBE", X0 - 1.6, X0, 794.5, 805.5, F0 + 3.0, F0 + 3.2)
            for yy in (795.5, 804.5):
                k.tube("Metal_B8BCBE", (X0 - 1.4, yy, F0 + 3.0), (X0 - 0.06, yy, F0 + 1.6), 0.06, segs=4)
        with k.part("awning"):
            k.slab4("Metal_A3261E", [(X0 - 5.0, 793.5, F0 + 7.9), (X0 - 5.0, 806.5, F0 + 7.9), (X0 - 0.08, 806.5, F0 + 9.3), (X0 - 0.08, 793.5, F0 + 9.3)], 0.25)
            for yy in (794, 806):
                k.tube("Metal_3A3A3A", (X0 - 4.8, yy, F0 + 7.6), (X0 - 0.06, yy, F0 + 6.6), 0.07, segs=4)
            yy = 793.9
            while yy < 806.4:
                k.tube("Metal_C23B30", (X0 - 0.3, yy, F0 + 9.26), (X0 - 4.9, yy, F0 + 7.96), 0.05, segs=4)
                yy += 1.3
    if HAS("C"):
        k.P("C").S("Roof")
        with k.part("roof_sign"):
            for yy in (793, 807):
                k.box("Metal_3A3A3A", 1077.8, 1078.4, yy - 0.3, yy + 0.3, top, top + 6.0)
                k.tube("Metal_3A3A3A", (1074, yy, top + 0.1), (1077.75, yy, top + 4.5), 0.12, segs=4)
            k.sign("topdog_roof", (1078.1, 800, top + 9.15), 20.0, 6.3, "x-", depth=0.8, cabinet="Metal_A3261E", both=True)
        bp.rtu(k, 1083, 800, top, sx=5.0, sy=3.6, sz=2.8)
        k.S("Shell")
        k.plane("Sign_topdog_menu", (X0 - 0.06, 808.4, F0 + 6.2), 2.4, 3.0, "x-")
        k.plane("Decal_decal_drip_2", (1086, Y0 - 0.05, top - 3.0), 4.0, 7.0, "y-")
        bp.wall_pack(k, "x", Y0, -1, 1087, F0 + 8.2)
        k.plane("Decal_decal_tag_3", (X1 + 0.05, 806, F0 + 3.8), 6.0, 2.2, "x+")
        k.S("Patio")
        k.plane("Decal_decal_oil_1", (1086, 787, LG + 0.23), 5, 4, "z+")
        bp.picnic_table(k, 1061.5, 786.5, LG + 0.2, math.pi / 2)
        bp.picnic_table(k, 1061.5, 814, LG + 0.2, math.pi / 2)
        k.cyl("Metal_5E5A52", 1064.5, 791.5, LG + 0.2, 1.0, 3.2, segs=10)
    return k.finish(PROTOS)


# ====================================================================== El Sol taqueria
def elsol(sc):
    k = newkit("WG01_ElSol", sc)
    X0, X1, Y0, Y1 = 1068, 1112, 604, 648
    yel, org, red = "Plaster_E2B52C", "Plaster_D9692A", "Plaster_A8352C"
    top, par = FF + 12.0, FF + 14.2
    green = "Wood_2F6B3E"
    wopen = [(607, 619, FF + 2.5, FF + 8.0), (621.7, 631.5, FF, FF + 8.3), (634, 645, FF + 2.5, FF + 8.0)]
    nopen = [(1076, 1086, FF + 3.0, FF + 7.4), (1092, 1102, FF + 3.0, FF + 7.4), (1104.7, 1109.9, FF, FF + 7.7)]
    sopen = [(1078, 1086, FF + 3.0, FF + 7.4), (1094, 1102, FF + 3.0, FF + 7.4)]
    eopen = [(611.7, 616.9, FF, FF + 7.7), (628, 631, FF + 6.0, FF + 8.0)]
    k.S("Shell")
    if HAS("M"):
        k.P("M")
        k.wall(yel, "y", X0, X0 + 1, Y0, Y1, FF, par, wopen)
        k.wall(yel, "x", Y1 - 1, Y1, X0 + 1, X1, FF, par, nopen)
        k.wall(yel, "x", Y0, Y0 + 1, X0 + 1, X1, FF, par, sopen)
        k.wall(yel, "y", X1 - 1, X1, Y0 + 1, Y1 - 1, FF, par, eopen)
        with k.part("parapet_step"):
            k.box(yel, X0, X0 + 1, 616, 636, par, par + 2.2)
            k.box(yel, X0, X0 + 1, 621, 631, par + 2.2, par + 3.6)
        k.S("Roof")
        k.box("Concrete_8E8A84", X0 + 1, X1 - 1, Y0 + 1, Y1 - 1, top - 0.8, top)
        k.S("Interior")
        with k.part("interior"):
            k.box("Concrete_3B3936", X0 + 1, X1 - 1, Y0 + 1, Y1 - 1, FF, FF + 0.05)
            k.box("Plaster_EFE6D2", X0 + 1, X1 - 1, Y0 + 1, Y1 - 1, FF + 10.5, FF + 10.8)
            k.box("Wood_7A5232", X0 + 14, X0 + 16, 608, 640, FF + 0.05, FF + 3.6)
    k.S("Shell")
    k.proto("win_elsol_12", bparts.window, style="casement", w=12.0, h=5.5, frame=green, sill="Concrete_B5634A",
            muntins=(3, 2), screen=False, blinds=0.35)
    place_on(k, "win_elsol_12", "W", 613, FF + 2.5, X0)
    k.proto("win_elsol_11", bparts.window, style="casement", w=11.0, h=5.5, frame=green, sill="Concrete_B5634A",
            muntins=(3, 2), screen=False, blinds=0.35)
    place_on(k, "win_elsol_11", "W", 639.5, FF + 2.5, X0)
    k.proto("door_elsol_pair", bparts.door, style="lite", w=9.2, h=8.0, pair=True, leaf="Wood_6B3E22", frame=green,
            casing=green, hw=bparts.BRASS)
    place_on(k, "door_elsol_pair", "W", 626.6, FF, X0)
    k.proto("win_elsol_10", bparts.window, style="casement", w=10.0, h=4.4, frame=green, sill="Concrete_B5634A",
            muntins=(2, 2), screen=False, blinds=0.5)
    k.proto("win_elsol_8", bparts.window, style="casement", w=8.0, h=4.4, frame=green, sill="Concrete_B5634A",
            muntins=(2, 2), screen=False, blinds=0.5)
    for a, b, z0, z1 in nopen[:2]:
        place_on(k, "win_elsol_10", "N", (a + b) / 2, z0, Y1)
    for a, b, z0, z1 in sopen:
        place_on(k, "win_elsol_8", "S", (a + b) / 2, z0, Y0)
    k.proto("door_back_steel", bparts.door, style="flush", leaf="Metal_7D7A72", frame="Metal_6E6A62", outswing=True,
            closer=True, kick=True)
    place_on(k, "door_back_steel", "N", 1107.3, FF, Y1)
    place_on(k, "door_back_steel", "E", 614.3, FF, X1)
    k.proto("win_bath_3", bparts.window, style="awning", w=3.0, h=2.0, obscure=True, open_frac=0.8, sill="Concrete_C8BFAE")
    place_on(k, "win_bath_3", "E", 629.5, FF + 6.0, X1)
    k.S("Porch")
    with k.part("porch"):
        zr0, zr1, xr0 = FF + 8.9, FF + 10.9, 1059.8

        def zu(x):
            return zr0 + (x - xr0) / (X0 - xr0) * (zr1 - zr0) - 0.6
        if HAS("M"):
            k.P("M")
            k.slab4("ClayRoofTiles_A8532E", [(xr0, 602.5, zr0), (xr0, 649.5, zr0), (X0 - 0.15, 649.5, zu(X0 - 0.15) + 0.6), (X0 - 0.15, 602.5, zu(X0 - 0.15) + 0.6)], 0.6)
            for yy in (604.6, 616.5, 636.5, 647.4):
                k.box("Wood_D9742E", 1060.6, 1061.6, yy - 0.5, yy + 0.5, FF, zu(1060.2) - 0.9)
        if HAS("T"):
            k.P("T")
            k.box("Wood_8A4E24", 1060.2, 1062.0, 602.5, 649.5, zu(1060.2) - 0.9, zu(1060.2) - 0.3)
            yy = 603.5
            while yy < 649:
                k.slab4("Wood_8A4E24", [(1060.0, yy - 0.15, zu(1060.0)), (1060.0, yy + 0.15, zu(1060.0)),
                                        (X0 - 0.12, yy + 0.15, zu(X0 - 0.12)), (X0 - 0.12, yy - 0.15, zu(X0 - 0.12))], 0.3)
                yy += 2.5
            for yy in (604.6, 616.5, 636.5, 647.4):
                k.box("Concrete_A8A08F", 1060.3, 1061.9, yy - 0.8, yy + 0.8, FF, FF + 0.6)
                for dy in (-1, 1):
                    k.tube("Wood_D9742E", (1061.1, yy + dy * 0.45, zu(1060.2) - 2.2), (1061.1, yy + dy * 1.6, zu(1060.2) - 0.95), 0.12, segs=4)
    if HAS("T"):
        k.P("T").S("Shell")
        band(k, red, X0, X1, Y0, Y1, FF - 0.5, FF + 1.6, gaps={"W": [(621.1, 632.1)], "N": [(1104.1, 1110.5)], "E": [(611.1, 617.5)]})
        band(k, org, X0, X1, Y0, Y1, top - 2.4, top - 1.9, proud=0.12, faces="NSE")
        with k.part("coping"):
            cap(k, "Concrete_B5634A", "y", X0, X0 + 1, Y0, 615.7, par, w=0.3, h=0.4)
            cap(k, "Concrete_B5634A", "y", X0, X0 + 1, 636.3, Y1, par, w=0.3, h=0.4)
            cap(k, "Concrete_B5634A", "y", X0, X0 + 1, 616, 620.7, par + 2.2, w=0.3, h=0.4)
            cap(k, "Concrete_B5634A", "y", X0, X0 + 1, 631.3, 636, par + 2.2, w=0.3, h=0.4)
            cap(k, "Concrete_B5634A", "y", X0, X0 + 1, 621, 631, par + 3.6, w=0.3, h=0.4)
            cap(k, "Concrete_B5634A", "y", X1 - 1, X1, Y0, Y1, par, w=0.3, h=0.4)
            cap(k, "Concrete_B5634A", "x", Y0, Y0 + 1, X0 + 1.3, X1 - 1.3, par, w=0.3, h=0.4)
            cap(k, "Concrete_B5634A", "x", Y1 - 1, Y1, X0 + 1.3, X1 - 1.3, par, w=0.3, h=0.4)
        with k.part("vigas"):
            for yy in range(606, 648, 4):
                k.tube("Wood_7A5232", (X0, yy, top + 0.6), (X0 - 1.5, yy, top + 0.6), 0.42, segs=8)
            for xx in range(1072, 1112, 4):
                k.tube("Wood_7A5232", (xx, Y1, top + 0.6), (xx, Y1 + 1.5, top + 0.6), 0.42, segs=8)
                k.tube("Wood_7A5232", (xx, Y0, top + 0.6), (xx, Y0 - 1.5, top + 0.6), 0.42, segs=8)
    if HAS("C"):
        k.P("C").S("Shell")
        k.decal("elsol_wall_name", (1090, Y1 + 0.17, FF + 9.2), 24.0, 5.4, "y+")
        k.decal("elsol_wall_menu", (X0 - 0.06, 626, FF + 12.3), 24.0, 4.6, "x-")
        k.decal("elsol_wall_name", (1090, Y0 - 0.17, FF + 9.2), 24.0, 5.4, "y-")
        k.decal("decal_drip_0", (X1 + 0.05, 640, top - 2.0), 3.5, 7.0, "x+")
        k.S("PoleSign")
        with k.part("pole_sign"):
            for yy in (586, 596):
                k.box("Metal_E2DED2", 1055.6, 1056.4, yy - 0.4, yy + 0.4, LG + 0.35, LG + 17.5)
            k.tube("Metal_E2DED2", (1056, 586.4, LG + 9.0), (1056, 591, LG + 17.4), 0.1, segs=4)
            k.tube("Metal_E2DED2", (1056, 595.6, LG + 9.0), (1056, 591, LG + 17.4), 0.1, segs=4)
            k.sign("elsol_pole", (1056, 591, LG + 21.0), 14.0, 7.0, "x-", depth=0.9, cabinet="Metal_B8B2A2", both=True)
        k.S("Roof")
        bp.swamp_cooler(k, 1098, 626, top)
        bp.satellite(k, 1106, 642, top, yaw=2.4)
        with k.part("hood_exhaust"):
            k.box("Metal_9EA2A3", 1092, 1094, 612, 614, top, top + 3.0)
            k.box("Metal_7E7A70", 1091.5, 1094.5, 611.5, 614.5, top + 3.0, top + 3.6)
        k.S("Porch")
        for yy, col in ((607.4, "SmoothPlastic_E9E6DC"), (613.6, "SmoothPlastic_C0392B"), (640, "SmoothPlastic_E9E6DC"), (643, "SmoothPlastic_2E7D32")):
            bp.chair(k, 1064.5, yy, FF, math.pi / 2, col)
        with k.part("table"):
            k.cyl("SmoothPlastic_E9E6DC", 1064.5, 610.5, FF, 1.4, 0.15, segs=10)
            k.cyl("Metal_9EA2A3", 1064.5, 610.5, FF + 0.15, 0.1, 2.35, segs=5)
            k.cyl("SmoothPlastic_E9E6DC", 1064.5, 610.5, FF + 2.5, 1.6, 0.12, segs=12)
        bp.flag(k, 1057, 603, LG, "Fabric_2E7D32")
        bp.flag(k, 1057, 650.5, LG, "Fabric_C0392B")
        bp.barrel(k, X1 + 2.2, 621, LG, color="Metal_4F4A3C")
        bp.barrel(k, X1 + 2.2, 623.4, LG, color="Metal_2E4F86")
        with k.part("planter"):
            k.cyl("Concrete_A8532E", 1063.0, 633.5, FF, 0.9, 1.4, segs=8, r2=1.1)
            bp.juniper(k, 1063.0, 633.5, FF + 1.4, rng, r=1.0)
    return k.finish(PROTOS)


# ====================================================================== Desert Rose Motor Lodge
MA_X0, MA_X1, MA_Y0, MA_Y1 = 1332, 1356, 458, 646
MB_X0, MB_X1, MB_Y0, MB_Y1 = 1150, 1332, 458, 482
F2, MRZ, MPT = FF + 11.0, FF + 22.0, FF + 24.2
POST_A_X = (1325.0, 1325.7)
POST_B_Y = (488.3, 489.0)


def _boarded_window(k, w, h):
    """Glass with plywood screwed over the opening (character)."""
    if "M" in bparts.PASSES:
        k.P("M")
        k.box("Glass_2B3438", -w / 2, w / 2, -0.55, -0.45, 0, h)
    if "C" in bparts.PASSES:
        k.P("C")
        k.box("Wood_B08A5C", -w / 2 - 0.3, w / 2 + 0.3, 0.0, 0.18, -0.3, h + 0.3)
        for x in (-w / 2, 0.0, w / 2):
            for z in (-0.1, h / 2, h + 0.1):
                k.box("Metal_6E6A62", x - 0.06, x + 0.06, 0.18, 0.21, z - 0.06, z + 0.06)
        k.box("Wood_9C7A4E", -w / 2 - 0.3, w / 2 + 0.3, 0.18, 0.22, h * 0.45, h * 0.55)


def motel(sc):
    k = newkit("WG01_Motel", sc)
    wall, accent = "Plaster_E6D5B8", "Plaster_C9785F"
    roomsA = [490 + 14 * i for i in range(11)]
    roomsB = [1154 + 14 * i for i in range(12)]

    def ops(starts, floor):
        o = []
        for a in starts:
            o.append((a + 1.2, a + 6.4, floor, floor + 7.7))
            o.append((a + 7.5, a + 13.5, floor + 3.0, floor + 7.4))
        return o
    opsA = ops(roomsA, FF) + ops(roomsA, F2)
    opsB = ops(roomsB, FF) + ops(roomsB, F2)
    bathA = [(a + 9, a + 12, z + 5.0, z + 7.4) for a in roomsA for z in (FF, F2)]
    bathB = [(a + 9, a + 12, z + 5.0, z + 7.4) for a in roomsB for z in (FF, F2)]
    door_cols = ["2F8F8B", "2F8F8B", "C96F5A", "2F8F8B", "E0B23A"]
    curtain_cols = ["B8865A", "7A6A9C", "C9B48A", "8C3A2E"]
    boarded = {("A", 3, F2), ("B", 7, FF), ("B", 2, F2)}
    if HAS("M"):
        k.P("M")
        k.S("WingA_Court").wall(wall, "y", MA_X0, MA_X0 + 1, MB_Y1, MA_Y1, FF, MPT, opsA)
        k.S("WingA_Back").wall(wall, "y", MA_X1 - 1, MA_X1, MA_Y0, MA_Y1, FF, MPT, bathA)
        k.S("WingA_End").wall(wall, "x", MA_Y1 - 1, MA_Y1, MA_X0 + 1, MA_X1 - 1, FF, MPT)
        k.S("WingB_Court").wall(wall, "x", MB_Y1 - 1, MB_Y1, MB_X0, MA_X0, FF, MPT, opsB)
        k.S("WingB_Back").wall(wall, "x", MB_Y0, MB_Y0 + 1, MB_X0, MA_X1 - 1, FF, MPT, bathB)
        k.S("WingB_End").wall(wall, "y", MB_X0, MB_X0 + 1, MB_Y0 + 1, MB_Y1 - 1, FF, MPT,
                              [(466, 474, FF + 3, FF + 7.4), (466, 474, F2 + 3, F2 + 7.4)])
        k.S("Roof")
        k.box("Concrete_8E8A84", MA_X0 + 1, MA_X1 - 1, MA_Y0 + 1, MA_Y1 - 1, MRZ - 0.8, MRZ)
        k.box("Concrete_8E8A84", MB_X0 + 1, MA_X0 + 1, MB_Y0 + 1, MB_Y1 - 1, MRZ - 0.8, MRZ)
        k.box("Concrete_8E8A84", POST_A_X[0], MA_X0, POST_B_Y[1], MA_Y1, MRZ - 0.8, MRZ)
        k.box("Concrete_8E8A84", MB_X0 - 0.5, MA_X0, MB_Y1, POST_B_Y[1], MRZ - 0.8, MRZ)
        k.S("Walkways")
        k.box("Concrete_B3AC9C", 1326.1, MA_X0, 487.9, MA_Y1 + 4, F2 - 0.8, F2)
        k.box("Concrete_B3AC9C", 1144, MA_X0, MB_Y1, 487.9, F2 - 0.8, F2)
        k.box("Concrete_B3AC9C", 1319.4, 1326.1, MA_Y1 - 2, MA_Y1 + 4, F2 - 0.8, F2)
        k.box("Concrete_B3AC9C", 1144, 1153.3, 487.9, 494.7, F2 - 0.8, F2)
        for y in [488.3 + 14 * i for i in range(11)]:
            k.box("Metal_4A4C4E", POST_A_X[0], POST_A_X[1], y, y + 0.7, FF, MRZ - 0.8)
        for x in [1166 + 14 * i for i in range(12)]:
            if x < 1324:
                k.box("Metal_4A4C4E", x - 0.35, x + 0.35, POST_B_Y[0], POST_B_Y[1], FF, MRZ - 0.8)
        k.S("Stairs")
        bp.stairs(k, "Concrete_B3AC9C", 1322.0, MA_Y1 - 2 - 17 * 1.1, 0, 1, 5.0, FF, F2)
        bp.stairs(k, "Concrete_B3AC9C", 1153.3 + 17 * 1.1, 492.0, -1, 0, 5.0, FF, F2)
    for col in set(door_cols):
        k.proto(f"door_motel_{col}", bparts.door, style="flush", leaf=f"Metal_{col}", frame="Plaster_F2EDE2",
                hw=bparts.BRASS, peephole=True)
    for j, cc in enumerate(curtain_cols):
        k.proto(f"win_motel_{j}", bparts.window, style="slider", w=6.0, h=4.4, surround="Plaster_F2EDE2",
                curtains=f"Fabric_{cc}", blinds=None if j % 2 else 0.4)
    k.proto("win_boarded", _boarded_window, 6.0, 4.4)
    k.proto("win_bath", bparts.window, style="awning", w=3.0, h=2.4, obscure=True, open_frac=0.0, sill="Plaster_F2EDE2")
    for wing, rooms, face, wf in (("A", roomsA, "W", MA_X0), ("B", roomsB, "N", MB_Y1)):
        k.S(f"Wing{wing}_Court")
        for i, a in enumerate(rooms):
            for z in (FF, F2):
                place_on(k, f"door_motel_{door_cols[(i + (2 if wing == 'B' else 0) + int(z)) % len(door_cols)]}", face, a + 3.8, z, wf)
                if (wing, i, z) in boarded:
                    place_on(k, "win_boarded", face, a + 10.5, z + 3.0, wf)
                else:
                    place_on(k, f"win_motel_{(i + int(z)) % 4}", face, a + 10.5, z + 3.0, wf)
        k.S(f"Wing{wing}_Back")
        bface, bwf = ("E", MA_X1) if wing == "A" else ("S", MB_Y0)
        for a in rooms:
            for z in (FF, F2):
                place_on(k, "win_bath", bface, a + 10.5, z + 5.0, bwf)
    k.S("WingB_End")
    for z in (FF, F2):
        place_on(k, "win_motel_1", "W", 470, z + 3.0, MB_X0)
    if HAS("T"):
        k.P("T").S("Roof")
        with k.part("fascia"):
            k.box(accent, POST_A_X[0] - 0.4, POST_A_X[0], POST_B_Y[1] + 0.4, MA_Y1, MRZ - 1.8, MRZ + 0.4)
            k.box(accent, MB_X0 - 0.5, POST_A_X[0], POST_B_Y[1], POST_B_Y[1] + 0.4, MRZ - 1.8, MRZ + 0.4)
            k.box(accent, MB_X0 - 0.9, MB_X0 - 0.5, MB_Y1, POST_B_Y[1] + 0.4, MRZ - 1.8, MRZ + 0.4)
        with k.part("coping"):
            cap(k, "Metal_8F8C84", "y", MA_X1 - 1, MA_X1, MA_Y0, MA_Y1, MPT)
            cap(k, "Metal_8F8C84", "y", MA_X0, MA_X0 + 1, MB_Y1, MA_Y1, MPT)
            cap(k, "Metal_8F8C84", "x", MA_Y1 - 1, MA_Y1, MA_X0 + 1, MA_X1 - 1, MPT)
            cap(k, "Metal_8F8C84", "x", MB_Y0, MB_Y0 + 1, MB_X0, MA_X1 - 1, MPT)
            cap(k, "Metal_8F8C84", "x", MB_Y1 - 1, MB_Y1, MB_X0, MA_X0, MPT)
            cap(k, "Metal_8F8C84", "y", MB_X0, MB_X0 + 1, MB_Y0 + 1, MB_Y1 - 1, MPT)
        k.S("Walkways")
        with k.part("slab_edge"):
            k.box(accent, POST_A_X[1], 1326.1, POST_B_Y[1], MA_Y1 - 2, F2 - 1.4, F2 + 0.15)
            k.box(accent, 1153.3, POST_A_X[1], 487.9, POST_B_Y[0], F2 - 1.4, F2 + 0.15)
        R = "Metal_2E2E2E"
        bp.railing(k, R, (1326.4, 488.6), (1326.4, MA_Y1 - 2.2), F2)
        bp.railing(k, R, (1319.6, MA_Y1 + 3.8), (MA_X0 - 0.3, MA_Y1 + 3.8), F2)
        bp.railing(k, R, (1153.6, 487.6), (1326.1, 487.6), F2)
        bp.railing(k, R, (1144.2, MB_Y1 + 0.3), (1144.2, 494.5), F2)
        k.S("Bands")
        band(k, accent, MB_X0, MA_X1, MA_Y0, MA_Y1, FF - 0.5, FF + 1.2, faces="E")
        band(k, accent, MB_X0, MA_X1, MA_Y0, MA_Y1, F2 - 0.6, F2 + 0.2, faces="E")
        band(k, accent, MB_X0, MA_X1, MB_Y0, MB_Y1, FF - 0.5, FF + 1.2, faces="SW")
        band(k, accent, MB_X0, MA_X1, MB_Y0, MB_Y1, F2 - 0.6, F2 + 0.2, faces="SW")
        band(k, accent, MA_X0 + 0.15, MA_X1, MA_Y0, MA_Y1, FF - 0.5, FF + 1.2, faces="N")
        band(k, accent, MA_X0 + 0.15, MA_X1, MA_Y0, MA_Y1, F2 - 0.6, F2 + 0.2, faces="N")
        with k.part("quoins"):
            for (x, y, sx, sy) in ((MA_X1, MA_Y0, 1, -1), (MA_X1, MA_Y1, 1, 1), (MB_X0, MB_Y0, -1, -1)):
                for z0, z1 in ((FF + 1.2, F2 - 0.6), (F2 + 0.2, MPT)):
                    quoin(k, "Plaster_D9C4A0", x, y, sx, sy, z0, z1)
    OX0, OX1, OY0, OY1 = 1070, 1110, 468, 504
    k.S("Office")
    if HAS("M"):
        k.P("M")
        k.wall(wall, "x", OY1 - 1, OY1, OX0, OX1, FF, FF + 14, [(1080, 1098, FF + 1.0, FF + 9.0), (1099.7, 1104.9, FF, FF + 7.7)])
        k.wall(wall, "y", OX0, OX0 + 1, OY0, OY1 - 1, FF, FF + 14, [(476, 496, FF + 2.5, FF + 8.5)])
        k.wall(wall, "x", OY0, OY0 + 1, OX0 + 1, OX1, FF, FF + 14, [(1089.7, 1094.9, FF, FF + 7.7)])
        k.wall(wall, "y", OX1 - 1, OX1, OY0 + 1, OY1 - 1, FF, FF + 14, [(482, 492, FF + 3, FF + 7.4)])
        k.box("Concrete_8E8A84", OX0 + 1, OX1 - 1, OY0 + 1, OY1 - 1, FF + 11.2, FF + 12)
        with k.part("office_inside"):
            k.box("Concrete_3B3936", OX0 + 1, OX1 - 1, OY0 + 1, OY1 - 1, FF, FF + 0.05)
            k.box("Wood_7A5232", 1082, 1096, OY1 - 6, OY1 - 4, FF + 0.05, FF + 3.6)
        k.S("PorteCochere")
        with k.part("porte_cochere"):
            k.box(wall, OX1, 1140, 474, 506, FF + 12.6, FF + 14.0)
            for x, y in ((1114, 476), (1114, 504), (1138, 476), (1138, 504)):
                k.box(wall, x - 0.9, x + 0.9, y - 0.9, y + 0.9, LG, FF + 12.6)
                if HAS("T"):
                    k.P("T").box(accent, x - 1.1, x + 1.1, y - 1.1, y + 1.1, LG, LG + 1.0)
                    k.P("M")
            if HAS("T"):
                k.P("T")
                k.box(accent, OX1, 1140.3, 473.7, 474, FF + 12.3, FF + 14.0)
                k.box(accent, OX1, 1140.3, 506, 506.3, FF + 12.3, FF + 14.0)
                k.box(accent, 1140, 1140.3, 474, 506, FF + 12.3, FF + 14.0)
                k.box("Metal_8F8C84", OX1 + 0.2, 1140.45, 473.55, 506.45, FF + 14.0, FF + 14.3)
    k.S("Office")
    k.proto("win_office_front", bparts.window, style="fixed", w=18.0, h=8.0, muntins=(3, 1), screen=False, blinds=0.25)
    place_on(k, "win_office_front", "N", 1089, FF + 1.0, OY1)
    k.proto("win_office_west", bparts.window, style="fixed", w=20.0, h=6.0, muntins=(4, 1), screen=False, blinds=0.3)
    place_on(k, "win_office_west", "W", 486, FF + 2.5, OX0)
    k.proto("win_slider_10", bparts.window, style="slider", w=10.0, h=4.4, blinds=0.6)
    place_on(k, "win_slider_10", "E", 487, FF + 3, OX1)
    k.proto("door_office", bparts.door, style="lite", leaf=bparts.AL, frame=bparts.AL, hw=bparts.SS)
    place_on(k, "door_office", "N", 1102.3, FF, OY1)
    k.proto("door_back_steel", bparts.door, style="flush", leaf="Metal_7D7A72", frame="Metal_6E6A62", outswing=True,
            closer=True, kick=True)
    place_on(k, "door_back_steel", "S", 1092.3, FF, OY0)
    if HAS("T"):
        k.P("T")
        with k.part("coping"):
            cap(k, "Metal_8F8C84", "x", OY0, OY0 + 1, OX0, OX1, FF + 14)
            cap(k, "Metal_8F8C84", "x", OY1 - 1, OY1, OX0, OX1, FF + 14)
            cap(k, "Metal_8F8C84", "y", OX0, OX0 + 1, OY0 + 1, OY1 - 1, FF + 14)
            cap(k, "Metal_8F8C84", "y", OX1 - 1, OX1, OY0 + 1, 473.4, FF + 14)
            cap(k, "Metal_8F8C84", "y", OX1 - 1, OX1, 506.6, OY1 - 1, FF + 14)
        band(k, accent, OX0, OX1, OY0, OY1, FF - 0.5, FF + 1.2, faces="NSW", gaps={"N": [(1079.4, 1098.6), (1099.1, 1105.5)], "S": [(1089.1, 1095.5)]})
    if HAS("C"):
        k.P("C")
        for wing, rooms in (("A", roomsA), ("B", roomsB)):
            k.S(f"Wing{wing}_Court")
            n0 = 0 if wing == "A" else 22
            for i, a in enumerate(rooms):
                for z in (FF, F2):
                    num = (n0 + i * 2 + (z > FF)) % 30 + 1
                    if wing == "A":
                        k.plane(f"Decal_room_{num:02d}", (MA_X0 + 0.2, a + 3.8, z + 6.3), 1.0, 1.0, "x-")
                        bp.ptac(k, "y", MA_X0, -1, a + 10.5, z + 0.9)
                        with k.part("sconce"):
                            k.box("Metal_3A3A3A", MA_X0 - 0.5, MA_X0, a + 6.5, a + 7.0, z + 6.6, z + 7.4)
                            k.box("Glass_F2E6C4", MA_X0 - 0.55, MA_X0 - 0.5, a + 6.6, a + 6.9, z + 6.7, z + 7.3)
                        k.box("Fabric_5A4632", MA_X0 - 2.2, MA_X0 - 0.2, a + 2.4, a + 5.2, z, z + 0.05)
                        if rng.random() < 0.35:
                            bp.chair(k, MA_X0 - 2.6, a + 8.4, z, math.pi / 2 * 3, "SmoothPlastic_E9E6DC")
                        if rng.random() < 0.3:
                            k.plane(f"Decal_decal_drip_{rng.randrange(3)}", (MA_X0 - 0.05, a + 12.3, z + 1.0), 1.6, 1.4, "x-")
                    else:
                        k.plane(f"Decal_room_{num:02d}", (a + 3.8, MB_Y1 - 0.2, z + 6.3), 1.0, 1.0, "y+")
                        bp.ptac(k, "x", MB_Y1, +1, a + 10.5, z + 0.9)
                        with k.part("sconce"):
                            k.box("Metal_3A3A3A", a + 6.5, a + 7.0, MB_Y1, MB_Y1 + 0.5, z + 6.6, z + 7.4)
                            k.box("Glass_F2E6C4", a + 6.6, a + 6.9, MB_Y1 + 0.5, MB_Y1 + 0.55, z + 6.7, z + 7.3)
                        k.box("Fabric_5A4632", a + 2.4, a + 5.2, MB_Y1 + 0.2, MB_Y1 + 2.2, z, z + 0.05)
                        if rng.random() < 0.3 and not (z == FF and a == 1238):
                            bp.chair(k, a + 8.4, MB_Y1 + 2.6, z, 0.0, "SmoothPlastic_E9E6DC")
        k.S("Roof")
        for a in roomsA[::2]:
            bp.swamp_cooler(k, MA_X0 + 11, a + 7, MRZ, s=0.85)
        for a in roomsB[1::2]:
            bp.swamp_cooler(k, a + 7, MB_Y0 + 11, MRZ, s=0.85)
        bp.satellite(k, MA_X1 - 4, 600, MRZ)
        bp.satellite(k, 1200, MB_Y0 + 4, MRZ, yaw=2.0)
        k.S("Amenities")
        with k.part("ice_machine"):
            k.box("Metal_C9CBCB", 1336, 1340, MA_Y1 + 0.2, MA_Y1 + 4.4, LG, LG + 6.2)
            k.box("Metal_8F9293", 1336.5, 1339.5, MA_Y1 + 4.4, MA_Y1 + 4.5, LG + 2.0, LG + 3.0)
        with k.part("vending"):
            k.box("Metal_B83A2E", 1342, 1345.5, MA_Y1 + 0.2, MA_Y1 + 4.4, LG, LG + 6.6)
            k.box("Glass_1F2A30", 1342.5, 1345, MA_Y1 + 4.4, MA_Y1 + 4.5, LG + 2.5, LG + 6.0)
        with k.part("cart"):
            k.box("Metal_9EA2A3", 1246.5, 1250.5, MB_Y1 + 1.0, MB_Y1 + 3.0, FF + 0.6, FF + 3.5)
            k.box("Fabric_E9E6DC", 1246.7, 1250.3, MB_Y1 + 1.2, MB_Y1 + 2.8, FF + 3.5, FF + 4.4)
            for dx in (0.4, 3.6):
                for dy in (1.3, 2.7):
                    k.cyl("Rubber_202020", 1246.5 + dx, MB_Y1 + dy, FF, 0.3, 0.6, segs=6)
        k.S("WingA_Back")
        k.plane("Decal_decal_tag_0", (MA_X1 + 0.06, 520, FF + 3.4), 14, 5.2, "x+")
        bp.meter_bank(k, "y", MA_X1, +1, 560, FF + 1.6, n=6)
        bp.wall_pack(k, "y", MA_X1, +1, 600, FF + 9.0)
        bp.wall_pack(k, "y", MA_X1, +1, 520, F2 + 9.0)
        k.S("WingB_Back")
        k.plane("Decal_decal_tag_4", (1240, MB_Y0 - 0.06, FF + 3.4), 14, 5.2, "y-")
        for x in range(1172, 1330, 34):
            k.plane(f"Decal_decal_drip_{x % 3}", (x, MB_Y0 - 0.05, MPT - 4.5), 4.0, 8.0, "y-")
        bp.wall_pack(k, "x", MB_Y0, -1, 1202, FF + 9.0)
        bp.wall_pack(k, "x", MB_Y0, -1, 1202, F2 + 9.0)
        for x in (1190, 1270):
            with k.part("downspout"):
                k.box("Metal_8F8C84", x - 0.4, x + 0.4, MB_Y0 - 0.95, MB_Y0 - 0.15, FF + 0.3, MPT - 1.6)
                k.box("Metal_8F8C84", x - 0.7, x + 0.7, MB_Y0 - 1.0, MB_Y0, MPT - 1.6, MPT - 0.5)
                for zz in (FF + 4, F2 + 4):
                    k.box("Metal_6E6A62", x - 0.5, x + 0.5, MB_Y0 - 0.2, MB_Y0, zz, zz + 0.2)
        k.S("Pool")
        bp.shopping_cart(k, 1192, 574, -2.6, 0.9)
        for x, y in ((1180, 590), (1204, 570)):
            k.cyl("Rubber_202020", x, y, -2.6, 1.3, 0.9, segs=10)
        bp.tumbleweed(k, 1176, 566, -3.1, rng, r=1.1)
        bp.tumbleweed(k, 1206, 592, -3.1, rng, r=1.1)
        k.S("PoleSign")
        with k.part("motel_pole"):
            k.cyl("Concrete_A6A096", 1056.5, 528, LG + 0.35, 1.3, 1.2, segs=12)
            k.cyl("Metal_2F6E73", 1056.5, 528, LG + 1.55, 0.8, 18.85, segs=10)
            k.sign("motel_pole", (1056.5, 528, LG + 30.4), 10.0, 20.0, "x-", depth=1.2, cabinet="Metal_1F4E55", both=True)
        k.S("Office")
        k.plane("Sign_motel_office", (1069.94, 486, FF + 10.6), 8.0, 2.0, "x-")
        k.plane("Sign_motel_office", (1089, 504.06, FF + 10.6), 8.0, 2.0, "y+")
        k.box("Neon_FF3B30", 1086, 1092, OY1 - 0.62, OY1 - 0.5, FF + 6.4, FF + 7.4)
    return k.finish(PROTOS)


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
    "door_motel": ((1318, 545, 6.5), (1332, 543.5, 6.8), 32),
    "win_motel": ((1322, 553, 19.0), (1332, 550, 17.2), 32),
    "door_plaza": ((1193, 754, 6.0), (1197, 738, 7.5), 28),
    "win_elsol": ((1056, 641, 7.0), (1068, 639, 8.0), 30),
    "stair_motel": ((1300, 655, 9.0), (1324, 636, 10), 24),
    "porte": ((1126, 455, 6.0), (1128, 492, 12), 22),
    "service_door": ((1176, 666, 6.0), (1177, 678, 6.5), 30),
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
    cam.type = "PERSP"
    cam.clip_start, cam.clip_end = 0.1, 5000
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


sc = scene()
lights(sc)
ctx = context(sc)
PROTOS = coll(sc, "WG01_Protos")
PROTOS.hide_render = True
PROTOS.hide_viewport = True
built = []
for fn in (site, plaza, topdog, elsol, motel):
    built += fn(sc)
elems = [e for k_ in KITS for e in k_.elems]
planes = [p for k_ in KITS for p in k_.planes]
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in built if not o.get("proto"))
uniq = {}
for o in built:
    if o.get("proto"):
        uniq[o.data.name] = sum(len(p.vertices) - 2 for p in o.data.polygons)
pieces = {o.get("piece") for o in built}
print(f"WG01 passes={PASSES}: {len(built)} objects, {len(pieces)} pieces, {len(uniq)} prototype meshes, "
      f"{tris:,} shell tris + {sum(uniq.values()):,} prototype tris, {len(elems)} QA solids")
WG_KITS = KITS
if globals().get("WG_QA"):
    res = bqa.check(elems, planes)
    txt = bqa.report(res, limit=400)
    open(os.path.join(REPO, "plans", "westgate", "qa_wg01.txt"), "w").write(txt)
    print(txt[:7000])
if globals().get("WG_RENDER"):
    print(render(sc, WG_RENDER, PASSES))

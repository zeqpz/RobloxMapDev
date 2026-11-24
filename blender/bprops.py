"""Reusable building parts + character props for the Westgate blocks (all take a bkit.Kit; Blender coords, studs).

Trim parts:      frame(), sill(), railing(), stairs(), coping()
Character props: rtu(), swamp_cooler(), ptac(), meter_bank(), dumpster(), utility_pole(), wire(), shoebox_light(),
                 wall_pack(), bollard(), wheel_stop(), yucca(), juniper(), boulder(), tumbleweed(), picnic_table(),
                 chair(), pallet(), barrel(), shopping_cart(), news_box(), barber_pole(), satellite(), flag()
"""
import math
import random

AL = "Metal_3A3129"          # dark-bronze aluminium
STEEL = "Metal_4A4C4E"
GALV = "Metal_9EA2A3"


# ====================================================================== trim
def frame(k, mat, axis, face, out, a0, a1, zb, zt, w=0.35, d=0.3, sill=True, head=True, jambs=True):
    """Trim around an opening in a wall. axis: wall direction ('x' or 'y'); face: outer face coordinate; out: +1/-1
    direction of the outside. Projects d from the face."""
    f0, f1 = sorted((face, face + out * d))

    def B(s0, s1, h0, h1, g0=f0, g1=f1):
        if axis == "x":
            k.box(mat, s0, s1, g0, g1, h0, h1)
        else:
            k.box(mat, g0, g1, s0, s1, h0, h1)
    if jambs:
        B(a0 - w, a0, zb - (w if sill else 0), zt)
        B(a1, a1 + w, zb - (w if sill else 0), zt)
    if head:
        B(a0 - w, a1 + w, zt, zt + w * 1.2)
    if sill:
        s0, s1 = sorted((face, face + out * (d + 0.25)))
        B(a0 - w - 0.2, a1 + w + 0.2, zb - w - 0.05, zb, s0, s1)


def railing(k, mat, p0, p1, z, h=3.3, pitch=0.6, post_every=8.0, r=0.09):
    """Steel pipe guard: top + mid rails, square pickets, heavier posts."""
    x0, y0 = p0
    x1, y1 = p1
    L = math.hypot(x1 - x0, y1 - y0)
    if L < 0.5:
        return
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    k.tube(mat, (x0, y0, z + h), (x1, y1, z + h), r * 1.6)
    k.tube(mat, (x0, y0, z + 0.4), (x1, y1, z + 0.4), r * 1.2)
    n = max(1, int(L / pitch))
    for i in range(n + 1):
        t = i * L / n
        x, y = x0 + ux * t, y0 + uy * t
        k.box(mat, x - r, x + r, y - r, y + r, z + 0.4, z + h)
    m = max(1, int(L / post_every))
    for i in range(m + 1):
        t = i * L / m
        x, y = x0 + ux * t, y0 + uy * t
        k.box(mat, x - 0.22, x + 0.22, y - 0.22, y + 0.22, z, z + h + 0.15)


def stairs(k, mat, x, y, dirx, diry, width, z0, z1, side=1, rise=0.65, run=1.1, stringer="Metal_4A4C4E"):
    """Straight exterior stair starting at (x, y, z0) climbing along (dirx, diry) to z1. Treads are boxes (walkable)."""
    n = max(1, round((z1 - z0) / rise))
    rr = (z1 - z0) / n
    px, py = -diry, dirx                                 # width direction
    for i in range(n):
        cx = x + dirx * (i + 0.5) * run
        cy = y + diry * (i + 0.5) * run
        zt = z0 + (i + 1) * rr
        hw = width / 2
        xs = sorted((cx - dirx * run / 2 - px * hw, cx + dirx * run / 2 + px * hw))
        ys = sorted((cy - diry * run / 2 - py * hw, cy + diry * run / 2 + py * hw))
        k.box(mat, xs[0], xs[1], ys[0], ys[1], zt - 0.25, zt)
    L = n * run
    for s in (-1, 1):                                    # stringers + handrail on both sides
        ox, oy = px * s * (width / 2 + 0.15), py * s * (width / 2 + 0.15)
        a = (x + ox, y + oy, z0 - 0.6)
        b = (x + ox + dirx * L, y + oy + diry * L, z1 - 1.15)
        k.tube(stringer, a, b, 0.25, segs=4)
        hx, hy = px * s * (width / 2 + 0.15), py * s * (width / 2 + 0.15)
        for i in range(0, n + 1, 3):
            t = i * run
            zz = z0 + i * rr
            bx, by = x + hx + dirx * t, y + hy + diry * t
            k.box(stringer, bx - 0.09, bx + 0.09, by - 0.09, by + 0.09, zz - 0.35, zz + 3.3)
        k.tube(stringer, (x + hx, y + hy, z0 + 3.3), (x + hx + dirx * L, y + hy + diry * L, z1 + 3.3), 0.13, segs=6)
    return x + dirx * L, y + diry * L


def coping(k, mat, x0, x1, y0, y1, z, w=0.45, h=0.35):
    """Cap on top of a parapet ring given the building's outer footprint."""
    k.box(mat, x0 - 0.15, x1 + 0.15, y0 - 0.15, y0 + w, z, z + h)
    k.box(mat, x0 - 0.15, x1 + 0.15, y1 - w, y1 + 0.15, z, z + h)
    k.box(mat, x0 - 0.15, x0 + w, y0 + w, y1 - w, z, z + h)
    k.box(mat, x1 - w, x1 + 0.15, y0 + w, y1 - w, z, z + h)


# ====================================================================== rooftop + wall equipment
def rtu(k, x, y, z, sx=7.0, sy=4.5, sz=3.6, yaw=0.0):
    """Packaged rooftop unit on a curb with a condenser fan grille."""
    k.box("Metal_C9C6BC", x - sx / 2, x + sx / 2, y - sy / 2, y + sy / 2, z, z + 0.6)
    k.box("Metal_D6D3C8", x - sx / 2 + 0.1, x + sx / 2 - 0.1, y - sy / 2 + 0.1, y + sy / 2 - 0.1, z + 0.6, z + sz)
    k.cyl("Metal_2A2A2A", x + sx * 0.22, y, z + sz, 1.3, 0.12, segs=12)
    for i in range(-2, 3):
        k.box("Metal_8E8C84", x - sx / 2 + 0.05, x - sx / 2 + 0.12, y + i * 0.7 - 0.1, y + i * 0.7 + 0.1, z + 1.0, z + sz - 0.4)
    k.box("Metal_9EA2A3", x - sx / 2 - 0.4, x - sx / 2, y - 0.6, y + 0.6, z, z + 1.8)        # gas/elec stub


def swamp_cooler(k, x, y, z, face="y-", s=1.0):
    """Evaporative cooler (very Albuquerque): louvred box on a stand with a duct into the roof."""
    w, d, h = 5.0 * s, 4.0 * s, 4.0 * s
    k.box(STEEL, x - w / 2, x + w / 2, y - d / 2, y + d / 2, z, z + 0.8)
    k.box("Metal_B5B1A4", x - w / 2, x + w / 2, y - d / 2, y + d / 2, z + 0.8, z + 0.8 + h)
    k.box("Metal_A19D90", x - w / 2 - 0.15, x + w / 2 + 0.15, y - d / 2 - 0.15, y + d / 2 + 0.15, z + 0.8 + h, z + 1.1 + h)
    for i in range(7):                                   # louvres on two faces
        zz = z + 1.3 + i * (h - 1.0) / 7
        k.box("Metal_8C887B", x - w / 2 + 0.3, x + w / 2 - 0.3, y - d / 2 - 0.12, y - d / 2, zz, zz + 0.18)
        k.box("Metal_8C887B", x - w / 2 - 0.12, x - w / 2, y - d / 2 + 0.3, y + d / 2 - 0.3, zz, zz + 0.18)
    k.box("Metal_9EA2A3", x + w / 2, x + w / 2 + 2.2, y - 1.0, y + 1.0, z + 1.5, z + 3.5)   # duct
    k.box("Metal_9EA2A3", x + w / 2 + 1.0, x + w / 2 + 2.2, y - 1.0, y + 1.0, z, z + 1.5)
    k.box("Metal_8C887B", x + w / 2 + 0.8, x + w / 2 + 2.4, y - 1.2, y + 1.2, z, z + 0.3)        # roof jack


def ptac(k, axis, face, out, a, z):
    """Through-wall motel AC sleeve + grille under a window."""
    f0, f1 = sorted((face, face + out * 0.45))
    if axis == "x":
        k.box("Metal_C2BEB2", a - 1.8, a + 1.8, f0, f1, z, z + 1.4)
        for i in range(5):
            zz = z + 0.2 + i * 0.24
            g0, g1 = sorted((face + out * 0.45, face + out * 0.5))
            k.box("Metal_6E6A60", a - 1.6, a + 1.6, g0, g1, zz, zz + 0.1)
    else:
        k.box("Metal_C2BEB2", f0, f1, a - 1.8, a + 1.8, z, z + 1.4)
        for i in range(5):
            zz = z + 0.2 + i * 0.24
            g0, g1 = sorted((face + out * 0.45, face + out * 0.5))
            k.box("Metal_6E6A60", g0, g1, a - 1.6, a + 1.6, zz, zz + 0.1)


def meter_bank(k, axis, face, out, a, z, n=3):
    """Electric meters on a backboard + conduit up the wall."""
    f0, f1 = sorted((face, face + out * 0.25))
    for i in range(n):
        aa = a + (i - (n - 1) / 2) * 1.4
        if axis == "x":
            k.box("Metal_8F9293", aa - 0.55, aa + 0.55, f0, f1, z, z + 1.6)
            g0, g1 = sorted((face + out * 0.25, face + out * 0.55))
            k.box("Glass_C9D4D6", aa - 0.3, aa + 0.3, g0, g1, z + 0.75, z + 1.35)
        else:
            k.box("Metal_8F9293", f0, f1, aa - 0.55, aa + 0.55, z, z + 1.6)
            g0, g1 = sorted((face + out * 0.25, face + out * 0.55))
            k.box("Glass_C9D4D6", g0, g1, aa - 0.3, aa + 0.3, z + 0.75, z + 1.35)
    if axis == "x":
        k.box("Metal_9EA2A3", a - 0.15, a + 0.15, f0, f1 + out * 0.05, z + 1.6, z + 8)
    else:
        k.box("Metal_9EA2A3", f0, f1 + out * 0.05, a - 0.15, a + 0.15, z + 1.6, z + 8)


def wall_pack(k, axis, face, out, a, z):
    f0, f1 = sorted((face, face + out * 0.9))
    if axis == "x":
        k.box("Metal_3A3A3A", a - 0.8, a + 0.8, f0, f1, z, z + 1.1)
        g0, g1 = sorted((face + out * 0.9, face + out * 0.95))
        k.box("Glass_F2E6C4", a - 0.6, a + 0.6, g0, g1, z + 0.1, z + 0.8)
    else:
        k.box("Metal_3A3A3A", f0, f1, a - 0.8, a + 0.8, z, z + 1.1)
        g0, g1 = sorted((face + out * 0.9, face + out * 0.95))
        k.box("Glass_F2E6C4", g0, g1, a - 0.6, a + 0.6, z + 0.1, z + 0.8)


def satellite(k, x, y, z, yaw=0.6):
    k.box(STEEL, x - 0.15, x + 0.15, y - 0.15, y + 0.15, z, z + 2.2)
    c, s = math.cos(yaw), math.sin(yaw)
    k.cyl("Metal_D8D6D0", x + c * 0.6, y + s * 0.6, z + 1.8, 1.3, 0.25, segs=12, r2=1.4)
    k.tube(STEEL, (x, y, z + 2.0), (x + c * 1.7, y + s * 1.7, z + 2.5), 0.06)


# ====================================================================== site props
def dumpster(k, x, y, z, yaw=0.0, color="Metal_2F5B3A"):
    k.obox(color, x, y, z + 0.5, 7.0, 4.6, 4.2, yaw)
    c, s = math.cos(yaw), math.sin(yaw)
    k.obox("Rubber_1E1E1E", x - s * 0.6, y + c * 0.6, z + 4.7, 7.2, 4.0, 0.25, yaw + 0.0)        # lid
    for dx in (-3.0, 3.0):
        for dy in (-1.8, 1.8):
            k.cyl("Rubber_202020", x + c * dx - s * dy, y + s * dx + c * dy, z, 0.35, 0.5, segs=6)
    k.obox(color, x + c * 3.65, y + s * 3.65, z + 2.5, 0.3, 3.6, 0.4, yaw)                     # pocket


def utility_pole(k, x, y, z, h=34.0, arm_yaw=0.0, transformer=False, rack_dir=(0, 1)):
    """Wood distribution pole: crossarm, braces, pin insulators; optional can transformer."""
    k.cyl("Wood_6B5038", x, y, z - 2, 0.55, h + 2, segs=8, r2=0.42)
    c, s = math.cos(arm_yaw), math.sin(arm_yaw)
    top = z + h - 1.5
    k.obox("Wood_5E4630", x, y, top, 8.5, 0.45, 0.45, arm_yaw)
    for d in (-1, 1):
        k.tube(STEEL, (x, y, top - 2.0), (x + c * d * 2.5, y + s * d * 2.5, top), 0.06, segs=4)
    pins = []
    for d in (-3.6, -1.2, 1.2, 3.6):
        px, py = x + c * d, y + s * d
        k.cyl("Glass_6E8A6A", px, py, top + 0.45, 0.22, 0.6, segs=6, r2=0.14)
        pins.append((px, py, top + 1.11))
    # secondary rack (spool insulators) on the pole face toward rack_dir, for service drops to buildings
    rx, ry = rack_dir
    for dz in (0.0, 0.8):
        k.box("Metal_6E6A62", x + rx * 0.42 - 0.12, x + rx * 0.42 + 0.12, y + ry * 0.42 - 0.12, y + ry * 0.42 + 0.12, top - 4.6 + dz, top - 4.4 + dz)
        k.cyl("Glass_D8D2C4", x + rx * 0.62, y + ry * 0.62, top - 4.75 + dz, 0.16, 0.5, segs=6)
    pins.append((x + rx * 0.95, y + ry * 0.95, top - 3.75))
    if transformer:
        k.cyl("Metal_7E8584", x + s * 1.3, y - c * 1.3, z + h - 9, 1.15, 3.6, segs=10)
        k.cyl("Metal_6B7271", x + s * 1.3, y - c * 1.3, z + h - 5.4, 1.2, 0.3, segs=10)
    return pins


def wire(k, a, b, sag=1.4, r=0.05, segs=8, mat="Rubber_141414"):
    pts = []
    for i in range(segs + 1):
        t = i / segs
        x = a[0] + (b[0] - a[0]) * t
        y = a[1] + (b[1] - a[1]) * t
        z = a[2] + (b[2] - a[2]) * t - sag * 4 * t * (1 - t)
        pts.append((x, y, z))
    for p, q in zip(pts[:-1], pts[1:]):
        k.tube(mat, p, q, r, segs=4)


def shoebox_light(k, x, y, z, h=24.0, heads=((1, 0),)):
    k.cyl("Concrete_A6A096", x, y, z - 0.5, 1.0, 2.5, segs=10)
    k.cyl(GALV, x, y, z + 2.0, 0.3, h - 2.0, segs=8, r2=0.22)
    for dx, dy in heads:
        hx, hy = x + dx * 2.2, y + dy * 2.2
        k.tube(GALV, (x, y, z + h - 0.5), (hx, hy, z + h - 0.5), 0.1, segs=4)
        k.box("Metal_3A3A3A", hx - 1.2, hx + 1.2, hy - 0.9, hy + 0.9, z + h - 1.0, z + h - 0.3)
        k.box("Glass_F7EBD0", hx - 1.0, hx + 1.0, hy - 0.7, hy + 0.7, z + h - 1.05, z + h - 1.0)


def bollard(k, x, y, z, color="Metal_D9A821"):
    k.cyl(color, x, y, z, 0.45, 3.4, segs=10)
    k.cyl(color, x, y, z + 3.4, 0.45, 0.25, segs=10, r2=0.1)


def wheel_stop(k, x, y, z, yaw=0.0):
    k.obox("Concrete_B8B2A4", x, y, z, 6.0, 0.6, 0.45, yaw)


def yucca(k, x, y, z, rng, n=14, h=3.0):
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.2, 0.2)
        tilt = rng.uniform(0.25, 1.0)
        L = h * rng.uniform(0.7, 1.1)
        tip = (x + math.cos(a) * L * tilt, y + math.sin(a) * L * tilt, z + L * (1.1 - tilt * 0.5))
        k.tube("Grass_6C7A4A", (x, y, z + 0.2), tip, 0.09, segs=3)
    k.cyl("Grass_5A6B3C", x, y, z, 0.35, 0.5, segs=6)


def juniper(k, x, y, z, rng, r=2.4):
    for i in range(5):
        a = rng.uniform(0, 6.28)
        d = rng.uniform(0, r * 0.5)
        rr = r * rng.uniform(0.5, 0.8)
        k.cyl("Grass_4E5E3A", x + math.cos(a) * d, y + math.sin(a) * d, z, rr, rr * 0.9, segs=7, r2=rr * 0.35)


def boulder(k, x, y, z, rng, s=1.6):
    k.obox("Rock_B9A58C", x, y, z - 0.3, s * rng.uniform(1.0, 1.6), s * rng.uniform(0.8, 1.3), s * rng.uniform(0.6, 1.0), rng.uniform(0, 3))
    k.obox("Rock_A8957C", x + 0.2, y - 0.1, z - 0.1, s * 0.9, s * 0.9, s * 0.95, rng.uniform(0, 3))


def tumbleweed(k, x, y, z, rng, r=1.2):
    for i in range(6):
        a = rng.uniform(0, 6.28)
        b = rng.uniform(-1, 1)
        p0 = (x + math.cos(a) * r, y + math.sin(a) * r, z + r + b * r * 0.8)
        p1 = (x - math.cos(a) * r, y - math.sin(a) * r, z + r - b * r * 0.8)
        k.tube("Wood_9C8460", p0, p1, 0.05, segs=3)


def picnic_table(k, x, y, z, yaw=0.0):
    k.obox("Wood_8C6A48", x, y, z + 2.4, 6.0, 2.6, 0.25, yaw)
    c, s = math.cos(yaw), math.sin(yaw)
    for d in (-1.9, 1.9):
        k.obox("Wood_8C6A48", x - s * d, y + c * d, z + 1.4, 6.0, 0.9, 0.2, yaw)
    for e in (-2.4, 2.4):
        k.obox(STEEL, x + c * e, y + s * e, z, 0.2, 4.6, 0.2, yaw)
        k.obox(STEEL, x + c * e, y + s * e, z, 0.2, 0.2, 2.4, yaw)


def chair(k, x, y, z, yaw=0.0, color="SmoothPlastic_E9E6DC"):
    k.obox(color, x, y, z + 1.4, 1.6, 1.6, 0.18, yaw)
    c, s = math.cos(yaw), math.sin(yaw)
    k.obox(color, x - s * 0.75, y + c * 0.75, z + 1.5, 1.6, 0.15, 1.7, yaw)
    for dx in (-0.65, 0.65):
        for dy in (-0.65, 0.65):
            k.box(color, x + c * dx - s * dy - 0.08, x + c * dx - s * dy + 0.08, y + s * dx + c * dy - 0.08,
                  y + s * dx + c * dy + 0.08, z, z + 1.4)


def pallet(k, x, y, z, yaw=0.0):
    c, s = math.cos(yaw), math.sin(yaw)
    for d in (-1.6, 0, 1.6):
        k.obox("Wood_8A7050", x - s * d, y + c * d, z, 4.2, 0.4, 0.4, yaw)
    for i in range(6):
        d = -1.75 + i * 0.7
        k.obox("Wood_9C8058", x + c * d, y + s * d, z + 0.4, 0.5, 3.8, 0.12, yaw)


def barrel(k, x, y, z, color="Metal_2E4F86"):
    k.cyl(color, x, y, z, 0.95, 3.0, segs=12)
    for zz in (0.9, 2.0):
        k.cyl(color, x, y, z + zz, 1.0, 0.12, segs=12, cap=False)


def shopping_cart(k, x, y, z, yaw=0.0):
    c, s = math.cos(yaw), math.sin(yaw)
    k.obox("Metal_B7B9BA", x, y, z + 1.4, 3.2, 2.0, 0.1, yaw)
    for d in (-1, 1):
        k.obox("Metal_B7B9BA", x - s * d * 1.0, y + c * d * 1.0, z + 1.4, 3.2, 0.08, 1.8, yaw)
    k.obox("Metal_B7B9BA", x - c * 1.6, y - s * 1.6, z + 1.4, 0.08, 2.0, 1.8, yaw)
    k.obox("Metal_B7B9BA", x + c * 1.6, y + s * 1.6, z + 1.4, 0.08, 2.0, 1.8, yaw)
    k.tube("SmoothPlastic_C0392B", (x - c * 2.0 - s * 1.0, y - s * 2.0 + c * 1.0, z + 3.4),
           (x - c * 2.0 + s * 1.0, y - s * 2.0 - c * 1.0, z + 3.4), 0.1, segs=5)
    for dx in (-1.3, 1.3):
        for dy in (-0.8, 0.8):
            k.cyl("Rubber_202020", x + c * dx - s * dy, y + s * dx + c * dy, z, 0.28, 0.28, segs=6)


def news_box(k, x, y, z, color="Metal_2D6AA8"):
    k.box(color, x - 0.9, x + 0.9, y - 0.8, y + 0.8, z + 1.0, z + 4.0)
    k.box(STEEL, x - 0.08, x + 0.08, y - 0.08, y + 0.08, z, z + 1.0)
    k.box("Glass_9FB3B8", x - 0.7, x + 0.7, y - 0.85, y - 0.8, z + 2.4, z + 3.6)


def barber_pole(k, x, y, z):
    k.cyl("Metal_C9C9C9", x, y, z, 0.42, 0.3, segs=10)
    cols = ["SmoothPlastic_C0392B", "SmoothPlastic_F2F2F2", "SmoothPlastic_2E4F9E", "SmoothPlastic_F2F2F2"]
    for i in range(12):
        k.cyl(cols[i % 4], x, y, z + 0.3 + i * 0.25, 0.32, 0.25, segs=10, cap=False)
    k.cyl("Metal_C9C9C9", x, y, z + 3.3, 0.42, 0.4, segs=10, r2=0.2)


def flag(k, x, y, z, color="Fabric_C0392B", h=12.0):
    k.cyl("Metal_9EA2A3", x, y, z, 0.08, h, segs=5)
    pts = [(x, y, z + h - 0.3), (x + 1.8, y, z + h - 1.2), (x + 1.6, y, z + 3.0), (x, y, z + 2.5)]
    k.face(color, pts)
    k.face(color, pts[::-1])


# ====================================================================== every helper above is one QA part
def _as_part(fn):
    def wrapped(k, *a, **kw):
        with k.part(fn.__name__):
            return fn(k, *a, **kw)
    wrapped.__name__ = fn.__name__
    wrapped.__doc__ = fn.__doc__
    return wrapped


for _n, _f in list(globals().items()):
    if callable(_f) and not _n.startswith("_") and getattr(_f, "__module__", None) == __name__:
        globals()[_n] = _as_part(_f)

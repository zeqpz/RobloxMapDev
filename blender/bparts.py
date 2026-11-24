"""Door + window assemblies (prototypes) for the building kit. Build with  k.proto(name, fn, ...)  and place with
k.place(name, x, y, z, yaw)  - see bkit.py for the local frame (origin = bottom centre of the opening on the outer wall
plane, +y outward, wall occupies -T..0).

Sizes follow standards/sizes.json: door 4.6 x 7.4 x 0.5, frame 0.3 -> rough opening 5.2 x 7.7; storefront door 4.6 x 8;
window frame 0.25, glass inset 0.2. Parts are split across passes (slab/glass = M, frame/casing/hardware/sill = T,
blinds/screens/stickers = C) so the owner's massing -> trim -> character order still applies inside each assembly.
"""
import math

PASSES = "MTC"
SS = "Metal_B9BCBE"           # stainless / satin chrome hardware
BRASS = "Metal_B8964A"
AL = "Metal_3A3129"           # dark bronze aluminium
RUB = "Rubber_1E1E1E"


def door_ro(w=4.6, h=7.4):
    """rough opening for a door leaf (or a pair when w = 9.2)"""
    return w + 0.6, h + 0.3


def _lever(k, x, y, z, hand, mat=SS):
    """lever handle on the face at plane y (pointing +y), hand = +1 handle to the +x side"""
    k.tube(mat, (x, y, z), (x, y + 0.12, z), 0.18, segs=8)            # rose
    k.tube(mat, (x, y + 0.12, z), (x, y + 0.26, z), 0.06, segs=6)      # spindle
    xa, xb = sorted((x + hand * 0.08, x - hand * 0.75))                 # lever points away from the latch edge
    k.box(mat, xa, xb, y + 0.26, y + 0.38, z - 0.06, z + 0.06)


def door(k, style="flush", w=4.6, h=7.4, T=1.0, hand=1, outswing=False, leaf="Metal_2F8F8B", frame="Metal_8C8A84",
         casing=None, hw=SS, peephole=False, kick=False, closer=False, lite=None, pair=False, threshold=True):
    """Hinged door assembly. style: 'flush' (steel/motel), 'lite' (glass panel in stile+rail leaf), 'panel' (2 raised
    panels). pair=True -> two leaves of w/2 each (w is then the pair width)."""
    W, H = door_ro(w, h)
    sf = -0.22                                              # exterior face of the leaf
    st = 0.5                                                # leaf thickness (owner standard)
    if "T" in PASSES:
        k.P("T")
        k.box(frame, -W / 2, -w / 2, -T, 0, 0, H)            # jambs
        k.box(frame, w / 2, W / 2, -T, 0, 0, H)
        k.box(frame, -w / 2, w / 2, -T, 0, h, H)             # head
        for s in (-1, 1):                                    # stops
            k.box(frame, s * w / 2 - (0.14 if s > 0 else 0), s * w / 2 + (0.14 if s < 0 else 0), sf, sf + 0.14, 0.12, h)
        k.box(frame, -w / 2, w / 2, sf, sf + 0.14, h - 0.14, h)
        if threshold:
            k.box("Metal_A7A49A", -w / 2, w / 2, -T, 0.12, 0, 0.1)
        if casing:
            k.box(casing, -W / 2 - 0.4, -W / 2, 0, 0.12, 0, H + 0.45)
            k.box(casing, W / 2, W / 2 + 0.4, 0, 0.12, 0, H + 0.45)
            k.box(casing, -W / 2 - 0.55, W / 2 + 0.55, 0, 0.16, H, H + 0.45)
            k.box(casing, -W / 2 - 0.6, W / 2 + 0.6, 0, 0.22, H + 0.45, H + 0.6)          # head cap
    leaves = [(-w / 2, w / 2, hand)] if not pair else [(-w / 2, -0.03, -1), (0.03, w / 2, 1)]
    for x0, x1, hd in leaves:
        lw = x1 - x0
        cx = (x0 + x1) / 2
        z0, z1 = 0.12, h - 0.04
        if "M" in PASSES:
            k.P("M")
            if style == "lite":
                st_w, top, bot = 0.6, 0.65, 1.5
                k.box(leaf, x0 + 0.02, x0 + st_w, sf - st, sf, z0, z1)
                k.box(leaf, x1 - st_w, x1 - 0.02, sf - st, sf, z0, z1)
                k.box(leaf, x0 + st_w, x1 - st_w, sf - st, sf, z0, z0 + bot)
                k.box(leaf, x0 + st_w, x1 - st_w, sf - st, sf, z1 - top, z1)
                gz0 = z0 + bot if lite is None else lite[0]
                k.box("Glass_2B3438", x0 + st_w, x1 - st_w, sf - st * 0.6, sf - st * 0.4, z0 + bot, z1 - top)
            else:
                k.box(leaf, x0 + 0.02, x1 - 0.02, sf - st, sf, z0, z1)
        if "T" in PASSES:
            k.P("T")
            if style == "lite":                              # glazing beads around the lite, on the outer face
                gx0, gx1, gz0, gz1 = x0 + 0.6, x1 - 0.6, z0 + 1.5, z1 - 0.65
                k.box(leaf, gx0, gx1, sf, sf + 0.06, gz0, gz0 + 0.12)
                k.box(leaf, gx0, gx1, sf, sf + 0.06, gz1 - 0.12, gz1)
                k.box(leaf, gx0, gx0 + 0.12, sf, sf + 0.06, gz0 + 0.12, gz1 - 0.12)
                k.box(leaf, gx1 - 0.12, gx1, sf, sf + 0.06, gz0 + 0.12, gz1 - 0.12)
            if style == "panel":
                for pz0, pz1 in ((0.9, 3.4), (4.0, h - 0.8)):
                    k.box(leaf, x0 + 0.55, x1 - 0.55, sf, sf + 0.06, pz0, pz1)
            hx = cx + hd * (lw / 2 - 0.45)
            _lever(k, hx, sf, 3.5, hd, hw)
            k.tube(hw, (hx, sf, 4.4), (hx, sf + 0.1, 4.4), 0.16, segs=8)       # deadbolt
            k.tube("Metal_3A3A3A", (hx, sf + 0.1, 4.4), (hx, sf + 0.12, 4.4), 0.08, segs=6)
            if peephole:
                k.tube(BRASS, (cx, sf, 5.6), (cx, sf + 0.06, 5.6), 0.07, segs=6)
            if kick:
                k.box(SS, x0 + 0.2, x1 - 0.2, sf, sf + 0.03, z0 + 0.05, z0 + 0.95)
            if outswing:                                     # exposed hinges on the hinge edge
                hxe = cx - hd * (lw / 2)
                for zz in (0.9, 3.8, 6.6):
                    k.cyl(hw, hxe - hd * 0.02, sf + 0.08, zz, 0.09, 0.55, segs=6)
            if closer:
                hxe = cx - hd * (lw / 2 - 0.9)
                k.box("Metal_8A8C8E", hxe - 0.75, hxe + 0.75, sf, sf + 0.35, h - 0.75, h - 0.35)
                k.box("Metal_8A8C8E", hxe - 0.05, hxe + 0.05, sf + 0.35, 0.05, h - 0.2, h - 0.12)
                k.box("Metal_8A8C8E", hxe - 0.05, hxe + 0.8, sf + 0.15, sf + 0.25, h - 0.3, h - 0.22)


def storefront_door(k, w=9.2, h=8.0, T=1.0, frame=AL, hw=SS):
    """Glass + aluminium storefront pair with transom: wide stiles, mid rail, push bars / pulls, floor closers."""
    th = h + 2.0
    if "T" in PASSES:
        k.P("T")
        k.box(frame, -w / 2 - 0.4, -w / 2, -T * 0.7, 0, 0, th)
        k.box(frame, w / 2, w / 2 + 0.4, -T * 0.7, 0, 0, th)
        k.box(frame, -w / 2, w / 2, -T * 0.7, 0, h, h + 0.4)
        k.box(frame, -w / 2, w / 2, -T * 0.7, 0, th - 0.4, th)
        k.box("Metal_A7A49A", -w / 2, w / 2, -T * 0.7, 0.1, 0, 0.08)
    if "M" in PASSES:
        k.P("M")
        k.box("Glass_2B3438", -w / 2, w / 2, -0.4, -0.3, h + 0.4, th - 0.4)
    for x0, x1, hd in ((-w / 2 + 0.03, -0.03, -1), (0.03, w / 2 - 0.03, 1)):
        if "M" in PASSES:
            k.P("M")
            k.box("Glass_243036", x0 + 0.55, x1 - 0.55, -0.38, -0.3, 1.2, h - 0.6)
        if "T" in PASSES:
            k.P("T")
            k.box(frame, x0, x0 + 0.55, -0.5, -0.15, 0.05, h - 0.05)
            k.box(frame, x1 - 0.55, x1, -0.5, -0.15, 0.05, h - 0.05)
            k.box(frame, x0 + 0.55, x1 - 0.55, -0.5, -0.15, 0.05, 1.2)
            k.box(frame, x0 + 0.55, x1 - 0.55, -0.5, -0.15, h - 0.6, h - 0.05)
            k.box(frame, x0 + 0.55, x1 - 0.55, -0.45, -0.2, 3.3, 3.6)                     # mid rail
            px = x1 - 0.95 if hd < 0 else x0 + 0.95                                      # pull handles
            k.box(hw, px - 0.09, px + 0.09, -0.15 + 0.3, -0.15 + 0.45, 2.6, 5.2)
            for zz in (2.8, 5.0):
                k.box(hw, px - 0.06, px + 0.06, -0.15, -0.15 + 0.3, zz - 0.06, zz + 0.06)
            lx = x1 - 0.3 if hd < 0 else x0 + 0.3
            k.tube("Metal_C9A23A", (lx, -0.15, 3.0), (lx, -0.08, 3.0), 0.1, segs=6)          # lock cylinder
    if "C" in PASSES:
        k.P("C")
        k.plane("Decal_door_push", (-w / 4, -0.29, 4.4), 1.4, 0.45, "y+")
        k.plane("Decal_door_hours", (w / 4, -0.29, 5.6), 1.8, 2.2, "y+")


def window(k, style="slider", w=6.0, h=4.4, T=1.0, frame=AL, sill="Concrete_D8CFBE", surround=None, screen=True,
           blinds=None, curtains=None, muntins=(1, 1), obscure=False, open_frac=0.0):
    """Window assembly in a w x h opening (sill at local z 0). style: 'slider' (two sashes, meeting stiles), 'fixed',
    'casement' (single sash, muntin grid), 'awning' (bathroom, obscure glass, hinged at top)."""
    fw = 0.25
    gy0, gy1 = -0.5, -0.42                                   # glass plane
    glass = "Glass_B5C2C4" if obscure else "Glass_2B3438"
    if "T" in PASSES:
        k.P("T")
        k.box(frame, -w / 2, -w / 2 + fw, -0.75, -0.15, 0, h)
        k.box(frame, w / 2 - fw, w / 2, -0.75, -0.15, 0, h)
        k.box(frame, -w / 2 + fw, w / 2 - fw, -0.75, -0.15, h - fw, h)
        k.box(frame, -w / 2 + fw, w / 2 - fw, -0.75, -0.15, 0, 0.32)                         # sill track
        if sill:
            k.box(sill, -w / 2 - 0.3, w / 2 + 0.3, 0.0, 0.42, -0.32, 0.0)                    # exterior sill
            k.box(sill, -w / 2 - 0.3, w / 2 + 0.3, 0.3, 0.42, -0.42, -0.32)                  # drip lip
        if surround:
            k.box(surround, -w / 2 - 0.42, -w / 2, 0, 0.1, 0, h + 0.42)
            k.box(surround, w / 2, w / 2 + 0.42, 0, 0.1, 0, h + 0.42)
            k.box(surround, -w / 2 - 0.42, w / 2 + 0.42, 0, 0.1, h, h + 0.42)
    x0, x1, z0, z1 = -w / 2 + fw, w / 2 - fw, 0.32, h - fw
    if style == "slider":
        mid = 0.0
        sashes = [(x0, mid + 0.1, -0.38, -0.3), (mid - 0.1, x1, -0.56, -0.48)]
        for sx0, sx1, sy0, sy1 in sashes:
            if "M" in PASSES:
                k.P("M")
                k.box(glass, sx0 + 0.16, sx1 - 0.16, sy0 + 0.02, sy1 - 0.02, z0 + 0.16, z1 - 0.16)
            if "T" in PASSES:
                k.P("T")
                k.box(frame, sx0, sx0 + 0.16, sy0, sy1, z0, z1)
                k.box(frame, sx1 - 0.16, sx1, sy0, sy1, z0, z1)
                k.box(frame, sx0 + 0.16, sx1 - 0.16, sy0, sy1, z0, z0 + 0.16)
                k.box(frame, sx0 + 0.16, sx1 - 0.16, sy0, sy1, z1 - 0.16, z1)
        if "T" in PASSES:
            k.P("T")
            k.box(frame, x1 - 0.45, x1 - 0.3, -0.48, -0.4, (z0 + z1) / 2 - 0.3, (z0 + z1) / 2 + 0.3)   # pull
            k.box("Metal_9A9A94", -0.25, -0.05, -0.32, -0.26, (z0 + z1) / 2 - 0.08, (z0 + z1) / 2 + 0.08)  # latch
        if screen and "C" in PASSES:
            k.P("C")
            k.box("Fabric_3B3D3E", 0.02, x1, -0.26, -0.24, z0, z1)
            k.box(frame, 0.02, x1, -0.28, -0.22, z1 - 0.08, z1)
            k.box(frame, 0.02, x1, -0.28, -0.22, z0, z0 + 0.08)
    elif style in ("fixed", "casement"):
        if "M" in PASSES:
            k.P("M")
            k.box(glass, x0, x1, gy0, gy1, z0, z1)
        if "T" in PASSES and muntins != (1, 1):
            k.P("T")
            cols, rows = muntins
            for i in range(1, cols):
                mx = x0 + (x1 - x0) * i / cols
                k.box(frame, mx - 0.08, mx + 0.08, gy1, gy1 + 0.1, z0, z1)
            for j in range(1, rows):
                mz = z0 + (z1 - z0) * j / rows
                k.box(frame, x0, x1, gy1, gy1 + 0.1, mz - 0.08, mz + 0.08)
    elif style == "awning":
        ang = 0.25 * open_frac
        if "M" in PASSES:
            k.P("M")
            # sash hinged at the top, kicked out by `ang` radians
            hz = z1
            ln = z1 - z0
            dy = math.sin(ang) * ln
            dz = ln - math.cos(ang) * ln
            k.slab4(glass, [(x0 + 0.1, gy1 + dy, z0 + dz + 0.02), (x1 - 0.1, gy1 + dy, z0 + dz + 0.02), (x1 - 0.1, gy1, hz), (x0 + 0.1, gy1, hz)], 0.08) if ang > 0.01 else k.box(glass, x0, x1, gy0, gy1, z0, z1)
    if blinds is not None and "C" in PASSES:
        k.P("C")
        down = blinds                                    # fraction of the window covered from the top
        k.box("SmoothPlastic_E6E0D0", x0, x1, -0.92, -0.82, z1 - 0.3, z1)                          # head rail
        zz = z1 - 0.4
        while zz > z1 - (z1 - z0) * down:
            k.box("SmoothPlastic_E6E0D0", x0 + 0.05, x1 - 0.05, -0.92, -0.82, zz - 0.04, zz)
            zz -= 0.34
        k.box("SmoothPlastic_D8D0BC", x0 + 0.05, x1 - 0.05, -0.93, -0.81, zz - 0.06, zz + 0.02)    # bottom rail
    if curtains and "C" in PASSES:
        k.P("C")
        gap = 0.6
        k.box(curtains, x0, -gap / 2, -0.97, -0.9, z0, z1)
        k.box(curtains, gap / 2, x1, -0.97, -0.9, z0, z1)

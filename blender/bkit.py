"""Building kit v2 for the Westgate blocks (Blender, 1 unit = 1 stud, Blender x = Roblox X, y = -Roblox Z, z = Roblox Y).

Owner build order -> passes:  M massing | T trim | C character   (k.P("T") switches; WG_PASSES picks what is built)
Export is CHOPPED into pieces:  k.S("FacadeN") sets the current piece; every piece becomes its own Roblox Model with one
MeshPart per material, named  <Bldg>.<Piece>__<RobloxMaterial>_<HEX>  (Sign_/Decal_ = image planes).
Repeated assemblies (doors, windows, ...) are PROTOTYPES: k.proto(name, fn) builds once in local space, k.place(name,
x, y, z, yaw) instances it (linked duplicates in Blender, cloned by the Studio installer = one MeshId each in Roblox).

QA: every solid primitive is recorded as an oriented box (k.elems) with its part id; bqa.check() finds parts that
stick into other parts and parts that float. Primitives inside `with k.part("name"):` belong to one part (allowed to
overlap each other, e.g. a railing's pickets and rails).
Local prototype frame: origin = bottom centre of the opening on the OUTER wall plane, +y = outward, x = along the wall.
"""
import math
import os
from contextlib import contextmanager

import bmesh
import bpy
from mathutils import Matrix, Vector

REPO = r"C:\Users\CooperHinkel\Documents\ClaudeRoblox\RobloxMapDev"
TEXB = os.path.join(REPO, "textures", "buildings")
TEXR = os.path.join(REPO, "textures", "roadkit")
UVS = 8.0                     # box-projected UVs: studs per UV unit
EX, EY, EZ = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def yaw_out(nx, ny):
    """yaw that turns local +y onto the outward normal (nx, ny)"""
    return math.atan2(-nx, ny)


# ====================================================================== geometry collector
class Kit:
    _uid = 0

    def __init__(self, bldg, collection=None):
        self.bldg = bldg
        self.coll = collection
        self.bms = {}
        self.pass_ = "M"
        self.piece = "Main"
        self._part = None
        self.elems = []           # oriented boxes for QA
        self.planes = []          # image planes (decals/signs) for QA
        self.protos = {}          # name -> Kit (local space)
        self.places = []          # (proto, Matrix, piece)
        self.tags = set()

    # ------------------------------------------------------------------ state
    def P(self, p):
        self.pass_ = p
        return self

    def S(self, piece):
        self.piece = piece
        return self

    @contextmanager
    def part(self, name="part"):
        old = self._part
        if old is None:
            Kit._uid += 1
            self._part = f"{self.piece}/{name}#{Kit._uid}"
        try:
            yield self
        finally:
            self._part = old

    def _pid(self):
        if self._part:
            return self._part
        Kit._uid += 1
        return f"{self.piece}/e#{Kit._uid}"

    def _rec(self, c, axes, half, mat, ground=False):
        if mat.startswith(("Decal_", "Sign_")):
            return
        self.elems.append(dict(c=Vector(c), ax=[Vector(a).normalized() for a in axes], h=tuple(half), part=self._pid(),
                               piece=f"{self.bldg}.{self.piece}", mat=mat, ground=ground or ("ground" in self.tags)))

    @contextmanager
    def ground(self):
        self.tags.add("ground")
        try:
            yield self
        finally:
            self.tags.discard("ground")

    def _bm(self, mat):
        key = (self.piece, mat)
        if key not in self.bms:
            bm = bmesh.new()
            bm.loops.layers.uv.new("UVMap")
            self.bms[key] = bm
        return self.bms[key]

    # ------------------------------------------------------------------ faces
    def face(self, mat, pts, uvs=None):
        bm = self._bm(mat)
        uvl = bm.loops.layers.uv.active
        vs = [bm.verts.new(p) for p in pts]
        try:
            f = bm.faces.new(vs)
        except ValueError:
            return None
        if uvs is None:
            n = (Vector(pts[1]) - Vector(pts[0])).cross(Vector(pts[2]) - Vector(pts[0]))
            ax = max(range(3), key=lambda i: abs(n[i])) if n.length > 1e-9 else 2
            for lp, p in zip(f.loops, pts):
                if ax == 2:
                    lp[uvl].uv = (p[0] / UVS, p[1] / UVS)
                elif ax == 0:
                    lp[uvl].uv = (p[1] / UVS, p[2] / UVS)
                else:
                    lp[uvl].uv = (p[0] / UVS, p[2] / UVS)
        else:
            for lp, uv in zip(f.loops, uvs):
                lp[uvl].uv = uv
        return f

    def hexa(self, mat, c, rec=True):
        """8 corners: bottom (0..3) then top (4..7), each ring counter-clockwise seen from above."""
        for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            self.face(mat, [c[i] for i in f])
        if rec:
            xs, ys, zs = zip(*c)
            self._rec(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2), (EX, EY, EZ),
                      ((max(xs) - min(xs)) / 2, (max(ys) - min(ys)) / 2, (max(zs) - min(zs)) / 2), mat)

    # ------------------------------------------------------------------ solids
    def box(self, mat, x0, x1, y0, y1, z0, z1):
        if x1 - x0 < 1e-4 or y1 - y0 < 1e-4 or z1 - z0 < 1e-4:
            return
        self.hexa(mat, [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], rec=False)
        self._rec(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (EX, EY, EZ), ((x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2), mat)

    def obox(self, mat, cx, cy, z0, sx, sy, sz, yaw=0.0):
        c, s = math.cos(yaw), math.sin(yaw)
        pts = []
        for z in (z0, z0 + sz):
            for dx, dy in ((-sx / 2, -sy / 2), (sx / 2, -sy / 2), (sx / 2, sy / 2), (-sx / 2, sy / 2)):
                pts.append((cx + dx * c - dy * s, cy + dx * s + dy * c, z))
        self.hexa(mat, pts, rec=False)
        self._rec((cx, cy, z0 + sz / 2), ((c, s, 0), (-s, c, 0), EZ), (sx / 2, sy / 2, sz / 2), mat)

    def prism(self, mat, poly2d, z0, z1, top=True, bottom=False):
        n = len(poly2d)
        area = sum(poly2d[i][0] * poly2d[(i + 1) % n][1] - poly2d[(i + 1) % n][0] * poly2d[i][1] for i in range(n))
        if area < 0:
            poly2d = poly2d[::-1]
        if top:
            self.face(mat, [(x, y, z1) for x, y in poly2d])
        if bottom:
            self.face(mat, [(x, y, z0) for x, y in poly2d[::-1]])
        for i in range(n):
            (ax, ay), (bx, by) = poly2d[i], poly2d[(i + 1) % n]
            self.face(mat, [(ax, ay, z0), (bx, by, z0), (bx, by, z1), (ax, ay, z1)])
        xs, ys = zip(*poly2d)
        self._rec(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (z0 + z1) / 2), (EX, EY, EZ),
                  ((max(xs) - min(xs)) / 2, (max(ys) - min(ys)) / 2, (z1 - z0) / 2), mat)

    def slab4(self, mat, quad, t):
        """Thick sloped plate from 4 top corners (CCW from above, a parallelogram); thickness t straight down."""
        top = [Vector(p) for p in quad]
        bot = [p - EZ * t for p in top]
        self.hexa(mat, [tuple(p) for p in bot + top], rec=False)
        e1, e2 = top[1] - top[0], top[3] - top[0]
        n = e1.cross(e2).normalized()
        c = (top[0] + top[2]) / 2 - EZ * t / 2
        tn = t * abs(n.z)                                  # thickness measured along the plate normal
        self._rec(c, (e1, e2, n), (e1.length / 2, e2.length / 2, tn / 2), mat)

    def cyl(self, mat, x, y, z0, r, h, segs=10, r2=None, cap=True):
        r2 = r if r2 is None else r2
        ring0 = [(x + r * math.cos(2 * math.pi * i / segs), y + r * math.sin(2 * math.pi * i / segs), z0) for i in range(segs)]
        ring1 = [(x + r2 * math.cos(2 * math.pi * i / segs), y + r2 * math.sin(2 * math.pi * i / segs), z0 + h) for i in range(segs)]
        for i in range(segs):
            j = (i + 1) % segs
            self.face(mat, [ring0[i], ring0[j], ring1[j], ring1[i]])
        if cap:
            self.face(mat, ring1)
            self.face(mat, ring0[::-1])
        rr = max(r, r2) * 0.93                             # inscribed-ish box: no false clashes at the rim
        self._rec((x, y, z0 + h / 2), (EX, EY, EZ), (rr, rr, h / 2), mat)

    def tube(self, mat, p0, p1, r, segs=6):
        p0, p1 = Vector(p0), Vector(p1)
        ax = p1 - p0
        if ax.length < 1e-6:
            return
        w = ax.normalized()
        ref = EZ if abs(w.z) < 0.9 else EX
        u = w.cross(ref).normalized()
        v = w.cross(u)
        r0 = [p0 + (u * math.cos(2 * math.pi * i / segs) + v * math.sin(2 * math.pi * i / segs)) * r for i in range(segs)]
        r1 = [q + ax for q in r0]
        for i in range(segs):
            j = (i + 1) % segs
            self.face(mat, [r0[i], r1[i], r1[j], r0[j]])
        self.face(mat, list(r1))
        self.face(mat, list(r0)[::-1])
        self._rec((p0 + p1) / 2, (w, u, v), (ax.length / 2, r * 0.85, r * 0.85), mat)

    # ------------------------------------------------------------------ image planes
    def plane(self, mat, c, w, h, normal, uv=(0, 0, 1, 1)):
        """Vertical (normal 'x+','x-','y+','y-') or horizontal ('z+') textured quad, UV 0..1 by default."""
        cx, cy, cz = c
        u0, v0, u1, v1 = uv
        if normal == "z+":
            pts = [(cx - w / 2, cy - h / 2, cz), (cx + w / 2, cy - h / 2, cz), (cx + w / 2, cy + h / 2, cz), (cx - w / 2, cy + h / 2, cz)]
            nv = EZ
        else:
            rx, ry = {"y-": (1, 0), "y+": (-1, 0), "x+": (0, 1), "x-": (0, -1)}[normal]
            pts = [(cx - rx * w / 2, cy - ry * w / 2, cz - h / 2), (cx + rx * w / 2, cy + ry * w / 2, cz - h / 2),
                   (cx + rx * w / 2, cy + ry * w / 2, cz + h / 2), (cx - rx * w / 2, cy - ry * w / 2, cz + h / 2)]
            nv = {"y-": -EY, "y+": EY, "x+": EX, "x-": -EX}[normal]
        self.face(mat, pts, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
        self.planes.append(dict(c=Vector(c), n=nv, w=w, h=h, mat=mat, piece=f"{self.bldg}.{self.piece}", part=self._pid()))

    def decal(self, tex, c, w, h, normal):
        self.plane("Decal_" + tex, c, w, h, normal)

    def sign(self, tex, c, w, h, normal, depth=0.5, cabinet="Metal_2B2B2D", both=False):
        cx, cy, cz = c
        with self.part("sign_" + tex):
            off = depth / 2 + 0.02
            if normal[0] == "y":
                self.box(cabinet, cx - w / 2, cx + w / 2, cy - depth / 2, cy + depth / 2, cz - h / 2, cz + h / 2)
                self.plane("Sign_" + tex, (cx, cy + (off if normal == "y+" else -off), cz), w * 0.96, h * 0.92, normal)
                if both:
                    back = "y-" if normal == "y+" else "y+"
                    self.plane("Sign_" + tex, (cx, cy + (off if back == "y+" else -off), cz), w * 0.96, h * 0.92, back)
            else:
                self.box(cabinet, cx - depth / 2, cx + depth / 2, cy - w / 2, cy + w / 2, cz - h / 2, cz + h / 2)
                self.plane("Sign_" + tex, (cx + (off if normal == "x+" else -off), cy, cz), w * 0.96, h * 0.92, normal)
                if both:
                    back = "x-" if normal == "x+" else "x+"
                    self.plane("Sign_" + tex, (cx + (off if back == "x+" else -off), cy, cz), w * 0.96, h * 0.92, back)

    # ------------------------------------------------------------------ walls with openings
    def wall(self, mat, axis, fixed0, fixed1, a0, a1, z0, z1, openings=()):
        """Wall between fixed0..fixed1 (thickness axis) spanning a0..a1 along `axis` ('x' or 'y'), with rectangular
        openings [(a_start, a_end, z_bottom, z_top)] cut through (stacked openings allowed). Non-overlapping boxes."""
        ops = [o for o in openings if o[1] > a0 and o[0] < a1]
        cuts = sorted({a0, a1} | {min(max(v, a0), a1) for o in ops for v in (o[0], o[1])})

        def B(s0, s1, h0, h1):
            if axis == "x":
                self.box(mat, s0, s1, fixed0, fixed1, h0, h1)
            else:
                self.box(mat, fixed0, fixed1, s0, s1, h0, h1)
        with self.part("wall"):
            for s0, s1 in zip(cuts[:-1], cuts[1:]):
                if s1 - s0 < 1e-4:
                    continue
                mid = (s0 + s1) / 2
                holes = sorted((max(zb, z0), min(zt, z1)) for o0, o1, zb, zt in ops if o0 < mid < o1)
                cur = z0
                for zb, zt in holes:
                    if zb > cur:
                        B(s0, s1, cur, zb)
                    cur = max(cur, zt)
                if cur < z1:
                    B(s0, s1, cur, z1)

    # ------------------------------------------------------------------ prototypes
    def proto(self, name, fn, *args, **kw):
        if name not in self.protos:
            pk = Kit("P_" + name)
            pk.pass_ = self.pass_
            pk.S(name)
            with pk.part(name):
                fn(pk, *args, **kw)
            self.protos[name] = pk
        return name

    def place(self, name, x, y, z, yaw=0.0):
        m = Matrix.Translation((x, y, z)) @ Matrix.Rotation(yaw, 4, "Z")
        self.places.append((name, m, self.piece))
        R = m.to_3x3()
        Kit._uid += 1
        pid = f"{self.piece}/{name}@{Kit._uid}"
        for e in self.protos[name].elems:
            self.elems.append(dict(c=m @ e["c"], ax=[R @ a for a in e["ax"]], h=e["h"], part=pid,
                                   piece=f"{self.bldg}.{self.piece}", mat=e["mat"], ground=False, proto=name))
        for p in self.protos[name].planes:
            self.planes.append(dict(c=m @ p["c"], n=R @ p["n"], w=p["w"], h=p["h"], mat=p["mat"],
                                    piece=f"{self.bldg}.{self.piece}", part=pid))

    # ------------------------------------------------------------------ build objects
    def _meshes(self, bms, prefix):
        out = []
        for (piece, mat), bm in bms.items():
            if not bm.faces:
                bm.free()
                continue
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
            me = bpy.data.meshes.new(f"{prefix}.{piece}__{mat}")
            bm.to_mesh(me)
            bm.free()
            me.validate()
            me.materials.append(material(mat))
            out.append((piece, mat, me))
        return out

    def finish(self, proto_coll=None):
        objs = []
        sub = self.coll
        for piece, mat, me in self._meshes(self.bms, self.bldg):
            ob = bpy.data.objects.new(me.name, me)
            ob["piece"] = f"{self.bldg}.{piece}"
            sub.objects.link(ob)
            objs.append(ob)
        self.bms = {}
        # prototypes: one mesh set each (in proto_coll at the origin), linked duplicates at every placement
        inst = None
        for name, pk in self.protos.items():
            if not getattr(pk, "_meshes_built", None):
                pk._meshes_built = self._meshes(pk.bms, "P")
                pk.bms = {}
                if proto_coll is not None:
                    for piece, mat, me in pk._meshes_built:
                        po = bpy.data.objects.new(me.name, me)
                        po["proto"] = name
                        proto_coll.objects.link(po)
        for name, m, piece in self.places:
            if inst is None:
                inst = bpy.data.collections.new(self.coll.name + "_Inst")
                self.coll.children.link(inst)
            for _, mat, me in self.protos[name]._meshes_built:
                ob = bpy.data.objects.new(f"{self.bldg}.{piece}.{name}__{mat}", me)
                ob.matrix_world = m
                ob["proto"] = name
                ob["piece"] = f"{self.bldg}.{piece}"
                inst.objects.link(ob)
                objs.append(ob)
        return objs


# ====================================================================== preview materials (Roblox material + colour)
ROUGH = {"Plaster": 0.92, "Concrete": 0.9, "Brick": 0.92, "Metal": 0.45, "CorrodedMetal": 0.7, "DiamondPlate": 0.5,
         "Glass": 0.05, "Wood": 0.75, "WoodPlanks": 0.8, "ClayRoofTiles": 0.8, "Asphalt": 0.92, "Pavement": 0.9,
         "Sand": 1.0, "Ground": 1.0, "Grass": 0.95, "Rock": 0.9, "SmoothPlastic": 0.5, "Fabric": 0.95, "Neon": 0.5,
         "Slate": 0.85, "Rubber": 0.9, "Cobblestone": 0.9, "Pebble": 0.95}


def _img(path, cs):
    name = os.path.basename(path)
    im = bpy.data.images.get(name)
    if im is None:
        im = bpy.data.images.load(path)
    im.colorspace_settings.name = cs
    return im


def material(key):
    m = bpy.data.materials.get("BK_" + key)
    if m:
        return m
    m = bpy.data.materials.new("BK_" + key)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"])
    kind, _, rest = key.partition("_")
    if kind in ("Sign", "Decal"):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = _img(os.path.join(TEXB, rest + ".png"), "sRGB")
        tex.extension = "CLIP"
        nt.links.new(tex.outputs["Color"], bs.inputs["Base Color"])
        nt.links.new(tex.outputs["Alpha"], bs.inputs["Alpha"])
        bs.inputs["Roughness"].default_value = 0.9 if kind == "Decal" else 0.5
        try:
            m.surface_render_method = "DITHERED"
        except AttributeError:
            m.blend_method = "HASHED"
        m.diffuse_color = (0.8, 0.8, 0.8, 1)
        return m
    col = srgb(rest if len(rest) == 6 else "888888")
    m.diffuse_color = col
    bs.inputs["Roughness"].default_value = ROUGH.get(kind, 0.8)
    uv = nt.nodes.new("ShaderNodeTexCoord")
    base = nt.nodes.new("ShaderNodeRGB")
    base.outputs[0].default_value = col
    color_out = base.outputs[0]
    bump_h = None
    if kind in ("Asphalt", "Pavement"):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = _img(os.path.join(TEXR, "asphalt_albedo.png"), "sRGB")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (0.5, 0.5, 0.5)
        nt.links.new(uv.outputs["UV"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        nt.links.new(base.outputs[0], mix.inputs[6])
        nt.links.new(tex.outputs["Color"], mix.inputs[7])
        base.outputs[0].default_value = tuple(min(1, c * 3.2) for c in col[:3]) + (1,)
        color_out = mix.outputs[2]
    elif kind == "Brick":
        br = nt.nodes.new("ShaderNodeTexBrick")
        br.inputs["Scale"].default_value = 1.0
        br.inputs["Mortar Size"].default_value = 0.012
        br.inputs["Brick Width"].default_value = 0.1
        br.inputs["Row Height"].default_value = 0.035
        nt.links.new(uv.outputs["UV"], br.inputs["Vector"])
        br.inputs["Color1"].default_value = col
        br.inputs["Color2"].default_value = tuple(c * 0.8 for c in col[:3]) + (1,)
        br.inputs["Mortar"].default_value = (0.45, 0.42, 0.38, 1)
        color_out = br.outputs["Color"]
        bump_h = br.outputs["Fac"]
    else:
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = {"Plaster": 60.0, "Concrete": 40.0, "Sand": 30.0, "Ground": 25.0,
                                             "Grass": 50.0, "Rock": 30.0, "CorrodedMetal": 20.0}.get(kind, 30.0)
        nz.inputs["Detail"].default_value = 8.0
        nt.links.new(uv.outputs["UV"], nz.inputs["Vector"])
        big = nt.nodes.new("ShaderNodeTexNoise")
        big.inputs["Scale"].default_value = 2.5
        nt.links.new(uv.outputs["UV"], big.inputs["Vector"])
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        amt = {"Plaster": 0.25, "Concrete": 0.3, "CorrodedMetal": 0.6, "Sand": 0.35, "Ground": 0.4, "Grass": 0.45,
               "Rock": 0.5, "Wood": 0.3, "WoodPlanks": 0.35, "Pebble": 0.5}.get(kind, 0.12)
        mix.inputs["Factor"].default_value = amt
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = (0.55, 0.55, 0.55, 1)
        ramp.color_ramp.elements[1].color = (1.25, 1.25, 1.25, 1)
        nt.links.new(big.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(base.outputs[0], mix.inputs[6])
        nt.links.new(ramp.outputs["Color"], mix.inputs[7])
        color_out = mix.outputs[2]
        if kind in ("Plaster", "Concrete", "Rock", "Sand", "Ground", "CorrodedMetal", "ClayRoofTiles", "Pebble"):
            bump_h = nz.outputs["Fac"]
    nt.links.new(color_out, bs.inputs["Base Color"])
    if bump_h is not None:
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.25 if kind != "Brick" else 0.5
        bump.inputs["Distance"].default_value = 0.05
        nt.links.new(bump_h, bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], bs.inputs["Normal"])
    if kind in ("Metal", "DiamondPlate"):
        bs.inputs["Metallic"].default_value = 0.35
        bs.inputs["Roughness"].default_value = 0.55
    if kind == "Glass":
        bs.inputs["Roughness"].default_value = 0.18
        bs.inputs["Specular IOR Level"].default_value = 0.35
    if kind == "Neon":
        bs.inputs["Emission Color"].default_value = col
        bs.inputs["Emission Strength"].default_value = 4.0
    return m

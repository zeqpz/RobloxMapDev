"""Render plans/map/layout.json (v2) as a labelled 2D sketch -> plans/map/map_sketch.svg.   python tools/render_map.py"""
import html
import json
import math
from pathlib import Path

from shapely.geometry import LineString, Polygon, Point
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "plans" / "map"
L = json.loads((OUT / "layout.json").read_text(encoding="utf-8"))
LO, _, HI, _ = L["extents"]
PLAY = L["playable"][2]
W = HI - LO
CLS = L["road_classes"]
C = dict(desert="#e9d7b2", ground="#dcc49c", sidewalk="#ece7dd", asphalt="#55524d", median="#a3ab72",
         park="#93bf6c", path="#efe4c8", lot="#c3beb4", yard="#c9b48f", interior="#c4502b", shell="#cbb595",
         house="#e9dbc2", houseedge="#9b8768", landmark="#7d6552", mountain="#b08a68", river="#5b9bc4",
         bosque="#7fa45a", text="#2a2622", pole="#6b4a2b", light="#f2c230", rail="#4a3b2e", arroyo="#d6cfbf")
el = []


def esc(s):
    return html.escape(str(s))


def path_of(geom):
    gs = getattr(geom, "geoms", [geom])
    d = []
    for g in gs:
        if g.is_empty or g.geom_type != "Polygon":
            continue
        for ring in [g.exterior] + list(g.interiors):
            d.append("M" + " L".join(f"{x:.1f},{z:.1f}" for x, z in ring.coords) + " Z")
    return " ".join(d)


def fillgeom(geom, fill, stroke="none", sw=0, extra=""):
    el.append(f'<path d="{path_of(geom)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" fill-rule="evenodd" {extra}/>')


def pline(pts, stroke, sw, extra=""):
    el.append(f'<polyline points="{" ".join(f"{x:.1f},{z:.1f}" for x, z in pts)}" fill="none" stroke="{stroke}" '
              f'stroke-width="{sw}" stroke-linejoin="round" {extra}/>')


def text(x, z, s, size=26, fill=C["text"], anchor="middle", weight=500, rot=0, halo=True):
    tr = f' transform="rotate({rot:.1f} {x:.1f} {z:.1f})"' if rot else ""
    h = f'stroke="#fffdf8" stroke-width="{size * 0.22:.1f}" paint-order="stroke" ' if halo else ""
    el.append(f'<text x="{x:.1f}" y="{z:.1f}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" '
              f'fill="{fill}" {h}dominant-baseline="middle"{tr}>{esc(s)}</text>')


def circle(x, z, r, fill, stroke="none", sw=0):
    el.append(f'<circle cx="{x:.1f}" cy="{z:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')


def angle_at(ls, d):
    p, q = ls.interpolate(max(0, d - 5)), ls.interpolate(min(ls.length, d + 5))
    a = math.degrees(math.atan2(q.y - p.y, q.x - p.x))
    return a + 180 if a > 90 else (a - 180 if a < -90 else a)


# ------------------------------------------------------------------ ground, scenery
el.append(f'<rect x="{LO}" y="{LO}" width="{W}" height="{W}" fill="{C["desert"]}"/>')
mpts = [(3060 + 40 * math.sin(i * 0.9) + 25 * math.sin(i * 2.3), LO + i * (HI - LO) / 30) for i in range(31)]
mtn = Polygon(mpts + [(HI, HI), (HI, LO)])
bench = Polygon([(3280, 230), (3600, 230), (3600, 760), (3280, 760)])
mtn = mtn.difference(bench.buffer(20))
fillgeom(mtn, C["mountain"])
for k in range(1, 7):
    pts = [(x + k * 70, z) for x, z in mpts]
    segs, cur = [], []
    for p in pts:
        if bench.buffer(30).contains(Point(p)):
            if len(cur) > 1:
                segs.append(cur)
            cur = []
        else:
            cur.append(p)
    if len(cur) > 1:
        segs.append(cur)
    for sgm in segs:
        pline(sgm, "#8d6a4c", 5, 'opacity="0.45"')
fillgeom(bench, "#cdb48c", "#8d6a4c", 3)
text(3420, 1700, "SIERRA ALAMO (mountain backdrop)", 40, "#4a3523", rot=90, weight=800)
fillgeom(Polygon([(LO, LO), (-60, LO), (-60, HI), (LO, HI)]), C["bosque"])
pline(L["river"], C["river"], 70, 'stroke-linecap="round"')
for i in range(90):
    circle(LO + 25 + (i * 137) % 420, LO + (i * 389) % W, 15, "#5f8a3e")
text(-110, 1300, "RIO ALAMO + BOSQUE", 40, "#1e3d57", rot=-90, weight=800)
el.append(f'<rect x="0" y="0" width="{PLAY}" height="{PLAY}" fill="{C["ground"]}"/>')
TINT = {"Westside": "#e8dcc4", "Northside": "#e3d9c3", "Southside": "#e6d2b8", "War Zone": "#e2d5bf",
        "South Valley": "#e4d6b4", "Valley": "#e6d8b6"}
for n, pts in L["districts"].items():
    fillgeom(Polygon(pts), TINT.get(n, "#e5dac6"), extra='opacity="0.9"')
pline(L["arroyo"]["pts"], "#a59d8d", L["arroyo"]["width"] + 10)
pline(L["arroyo"]["pts"], C["arroyo"], L["arroyo"]["width"])
pline(L["arroyo"]["pts"], "#b9b2a3", 6, 'stroke-dasharray="30 20"')

# ------------------------------------------------------------------ lots + buildings
for l in L["lots"]:
    lp = Polygon(l["poly"])
    if l["kind"] == "shop":
        fillgeom(lp, C["lot"], "#8f897e", 2)
        fillgeom(Polygon(l["bldg"]["poly"]), C["shell"], "#3b2a1f", 2)
    else:
        fillgeom(lp, "#e2d3b5", "#b9a37f", 1.2)
        fillgeom(Polygon(l["bldg"]["poly"]), C["house"], C["houseedge"], 1.5)

for s in L["specials"]:
    lp = Polygon(s["poly"])
    k = s["kind"]
    minx, minz, maxx, maxz = lp.bounds
    if k == "park":
        fillgeom(lp, C["park"], "#5d8a3f", 4)
        c = lp.centroid
        for vx, vz in s["poly"][::max(1, len(s["poly"]) // 3)][:3]:
            pline([(c.x, c.y), (vx, vz)], C["path"], 16)
        circle(c.x, c.y, 64, C["path"]); circle(c.x, c.y, 26, C["river"])
        for i in range(4):
            a = i * math.pi / 2 + math.pi / 4
            el.append(f'<rect x="{c.x + 96 * math.cos(a) - 13:.0f}" y="{c.y + 96 * math.sin(a) - 13:.0f}" width="26" height="26" '
                      f'fill="#fff" stroke="{C["interior"]}" stroke-width="5"/>')
        for i in range(160):
            tx, tz = minx + (i * 97) % (maxx - minx), minz + (i * 211) % (maxz - minz)
            if lp.buffer(-12).contains(Point(tx, tz)) and Point(tx, tz).distance(c) > 120:
                circle(tx, tz, 10, "#4e7c32")
        text(c.x, c.y - 112, "SPAWN", 40, "#fff", weight=900, halo=False)
        text(c.x + 20, c.y + 120, "Triangle Plaza Park", 28, weight=800)
        continue
    if s["id"] == "graveyard":
        fillgeom(lp, "#cdbf98", "#a0623d", 8)
        for gx in range(int(minx) + 25, int(maxx) - 100, 16):
            for gz in range(int(minz) + 25, int(maxz) - 30, 22):
                if (gx - minx) % 96 > 70:
                    continue
                el.append(f'<rect x="{gx}" y="{gz}" width="6" height="10" fill="#8e8a84"/>')
        for i in range(18):
            circle(minx + 15 + (i * 61) % (maxx - minx - 30), minz + 12 + (i * 37) % (maxz - minz - 24), 8, "#3f6b33")
    elif k == "mhp":
        fillgeom(lp, "#d9caa9", "#9b8768", 3)
        for i in range(int((maxx - minx) // 34)):
            for jz in (minz + 22, maxz - 70):
                el.append(f'<rect x="{minx + 10 + i * 34:.0f}" y="{jz:.0f}" width="16" height="48" fill="#f1ece2" stroke="#8d806b" stroke-width="2"/>')
    elif k == "ranch":
        fillgeom(lp, "#d8c08f", "#8b6b3e", 3, 'stroke-dasharray="12 8"')
    else:
        fillgeom(lp, C["yard"] if k == "yard" else C["lot"], "#8f897e", 3, 'stroke-dasharray="10 8"' if k == "yard" else "")
    if s.get("canopy"):
        fillgeom(Polygon(s["canopy"]), "#f1ede6", C["interior"] if k == "interior" else "#6d6a64", 6)
    if s.get("bldg"):
        bp = Polygon(s["bldg"]["poly"])
        fill = {"interior": C["interior"], "site": "#b98d6a", "landmark": C["landmark"], "ranch": C["house"]}.get(k, C["shell"])
        if s.get("bays"):
            bminx, bminz, bmaxx, bmaxz = bp.bounds
            bx = bminx
            for name, bw, num in s["bays"]:
                el.append(f'<rect x="{bx:.0f}" y="{bminz:.0f}" width="{bw}" height="{bmaxz - bminz:.0f}" '
                          f'fill="{C["interior"] if num else C["shell"]}" stroke="#3b2a1f" stroke-width="3"/>')
                if num:
                    circle(bx + bw / 2, (bminz + bmaxz) / 2, 19, "#fff", "#3b2a1f", 3)
                    text(bx + bw / 2, (bminz + bmaxz) / 2 + 1, num, 22, weight=800, halo=False)
                bx += bw
        else:
            fillgeom(bp, fill, "#3b2a1f", 3)
    if s.get("num") and not s.get("bays"):
        anchor = Polygon(s["bldg"]["poly"]).centroid if s.get("bldg") else lp.centroid
        circle(anchor.x, anchor.y, 23, "#fff", "#3b2a1f", 3)
        text(anchor.x, anchor.y + 1, s["num"], 26, weight=800, halo=False)
    if s.get("bays"):
        text((minx + maxx) / 2, minz + 26, "Strip mall", 23, weight=800)
    elif k == "mhp":
        text((minx + maxx) / 2, (minz + maxz) / 2, s["name"], 24, weight=800)
    else:
        text((minx + maxx) / 2, maxz - 16, s["name"], (23 if len(s["name"]) < 13 else 19) if k in ("interior", "site") else 18,
             weight=800 if k in ("interior", "site") else 600)

# ------------------------------------------------------------------ roads
ground = [r for r in L["roads"] if r["cls"] not in ("freeway", "ramp")]
sw = unary_union([LineString(r["pts"]).buffer(CLS[r["cls"]]["row"] / 2, cap_style="flat" if r["cls"] in ("arterial", "avenue") else "round")
                  for r in ground if CLS[r["cls"]]["sidewalk"]] + [Point(r["bulb"]).buffer(30) for r in ground if r.get("bulb")])
fillgeom(sw, C["sidewalk"])
dirt = unary_union([LineString(r["pts"]).buffer(CLS[r["cls"]]["ctc"] / 2) for r in ground if r["cls"] in ("rural", "alley")])
fillgeom(dirt, "#8d806e")
asph = unary_union([LineString(r["pts"]).buffer(CLS[r["cls"]]["ctc"] / 2, cap_style="flat" if r["cls"] in ("arterial", "avenue") else "round")
                    for r in ground if r["cls"] not in ("rural", "alley")] + [Point(r["bulb"]).buffer(22) for r in ground if r.get("bulb")])
fillgeom(asph, C["asphalt"])
for b in L["arroyo"]["bridges"]:
    circle(b["at"][0], b["at"][1], b["width"] / 2 + 8, "none", "#f7f3ea", 5)
for r in ground:
    ls = LineString(r["pts"])
    if r["cls"] == "arterial":
        pline(r["pts"], C["median"], 16)
        offs, col, dash = (-36, -22, 22, 36), "#f5f2ea", 'stroke-dasharray="20 30"'
    elif r["cls"] == "avenue":
        for off in (-6, 6):
            o = ls.offset_curve(off)
            if o.geom_type == "LineString" and not o.is_empty:
                pline(list(o.coords), "#f2c230", 2)
        offs, col, dash = (-21, 21), "#f5f2ea", 'stroke-dasharray="20 30"'
    elif r["cls"] == "collector":
        pline(r["pts"], "#f2c230", 2.5)
        continue
    else:
        continue
    for off in offs:
        o = ls.offset_curve(off)
        if o.geom_type == "LineString" and not o.is_empty:
            pline(list(o.coords), col, 1.6, dash)
pline(L["rail"]["pts"], "#9c8f7e", 22)
pline(L["rail"]["pts"], C["rail"], 12, 'stroke-dasharray="3 6"')
pline(L["rail"]["pts"], C["rail"], 3)
for x in L["rail"]["crossings"]:
    for dx in (-26, 26):
        circle(x["at"][0] + dx, x["at"][1], 7, "#fff", "#c02f24", 3)
for r in L["roads"]:
    if r["cls"] in ("freeway", "ramp"):
        pline(r["pts"], "#3d3b38", CLS[r["cls"]]["ctc"] + 8)
        pline(r["pts"], "#6c6964", CLS[r["cls"]]["ctc"])
        if r["cls"] == "freeway":
            for off in (-22, 0, 22):
                pline([(x, z + off) for x, z in r["pts"]], "#f4f1ea", 2, 'stroke-dasharray="30 30"' if off else "")
for x, z in L["poles"]:
    circle(x, z, 3.5, C["pole"])
for x, z in L["lights"]:
    circle(x, z, 4.2, C["light"], "#6d5a1f", 1)
for j in L["junctions"]:
    x, z = j["at"]
    if j["kind"] == "signal":
        for dx, dz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            circle(x + dx * 52, z + dz * 52, 9, "#2b2b2b"); circle(x + dx * 52, z + dz * 52, 4.5, "#3ec46d")
    else:
        circle(x, z, 9 if j["kind"] == "stop" else 12, "#d23a2e", "#fff", 2)

# ------------------------------------------------------------------ labels + furniture
SHOW = {"camino": 0.3, "mesa": 0.2, "alameda": 0.45, "dyer": 0.25, "foothill": 0.55, "river": 0.3, "valley": 0.5,
        "ash": 0.12, "menaul": 0.5, "coyote": 0.55, "commerce": 0.6, "railroad": 0.1, "gold": 0.5, "silver": 0.5,
        "lead": 0.5, "coal": 0.5, "barelas": 0.85, "ranch": 0.5, "camposanto": 0.35, "corrales": 0.3, "mesaverde": 0.45}
for r in L["roads"]:
    t = SHOW.get(r["id"])
    if t is None:
        continue
    ls = LineString(r["pts"])
    p = ls.interpolate(ls.length * t)
    text(p.x, p.y, r["name"].upper(), 24 if r["cls"] in ("arterial", "avenue") else 16, "#ffffff",
         rot=angle_at(ls, ls.length * t), weight=800, halo=False)
text(2800, 170, "I-66", 30, "#ffffff", weight=900, halo=False)
text(1990, 2470, "ARROYO SECO", 22, "#6c6455", rot=7, weight=800, halo=False)
text(2236, 2900, "RAIL", 18, C["rail"], rot=88, weight=800)
text(850, 1640, "FIVE POINTS", 22, weight=900)
for name, (x, z, sz) in {"WESTSIDE": (380, 1090, 50), "NORTHSIDE": (1150, 580, 50), "DOWNTOWN": (1960, 1590, 30),
                         "SOUTHSIDE": (760, 2250, 50), "WAR ZONE": (2560, 2000, 50), "EASTSIDE": (2690, 1330, 50),
                         "RANCH ROAD": (2700, 330, 46), "SOUTH VALLEY": (330, 2560, 40), "VALLEY": (1150, 2930, 44),
                         "UPTOWN": (2030, 470, 36)}.items():
    text(x, z, name, sz, "#5a3d27", weight=900)
for i in range(2):
    for j in range(2):
        bx, bz = LO + i * 2048, LO + j * 2048
        el.append(f'<rect x="{bx}" y="{bz}" width="2048" height="2048" fill="none" stroke="#1f5fa8" stroke-width="6" '
                  f'stroke-dasharray="40 24" opacity="0.6"/>')
        text(bx + 160, bz + 50, f"Baseplate {j * 2 + i + 1}", 30, "#1f5fa8", weight=800)
el.append(f'<rect x="0" y="0" width="{PLAY}" height="{PLAY}" fill="none" stroke="#7a2b18" stroke-width="8" stroke-dasharray="18 12"/>')
text(PLAY - 330, PLAY + 26, "playable 3072 x 3072 studs", 26, "#7a2b18", weight=700)
text(1536, LO + 110, "ALAMO COUNTY - map sketch v2", 54, weight=900)
lx, lz = 120, 3255
el.append(f'<rect x="{lx - 40}" y="{lz - 50}" width="2950" height="200" fill="#fffdf8" stroke="#7a6448" stroke-width="4" opacity="0.96"/>')
items = [("box", C["interior"], "Required interior / site (#)"), ("box", C["shell"], "Exterior-only shell"),
         ("box", C["house"], "House lot"), ("box", C["lot"], "Parking / yard"), ("box", C["park"], "Spawn park"),
         ("road", C["asphalt"], "Paved road (yellow = centre line)"), ("dirt", "#8d806e", "Dirt alley / rural lane"),
         ("sig", None, "Traffic signal"), ("stop", None, "Stop sign (big = all-way)"), ("light", None, "Streetlight"),
         ("pole", None, "Power pole (120 apart)"), ("rail", None, "Rail line + crossing gates"),
         ("arroyo", None, "Arroyo (concrete) + bridge"), ("fwy", None, "I-66 (elevated)"), ("bp", None, "Baseplate (2048)")]
for i, (kind, col, label) in enumerate(items):
    ix, iz = lx + (i % 5) * 580, lz + (i // 5) * 52
    if kind == "box":
        el.append(f'<rect x="{ix}" y="{iz - 15}" width="44" height="30" fill="{col}" stroke="#3b2a1f" stroke-width="2"/>')
    elif kind in ("road", "dirt"):
        el.append(f'<rect x="{ix}" y="{iz - 11}" width="44" height="22" fill="{col}"/>')
        if kind == "road":
            el.append(f'<line x1="{ix}" y1="{iz}" x2="{ix + 44}" y2="{iz}" stroke="#f2c230" stroke-width="3"/>')
    elif kind == "sig":
        circle(ix + 22, iz, 12, "#2b2b2b"); circle(ix + 22, iz, 6, "#3ec46d")
    elif kind == "stop":
        circle(ix + 22, iz, 11, "#d23a2e", "#fff", 2)
    elif kind == "light":
        circle(ix + 22, iz, 8, C["light"], "#6d5a1f", 2)
    elif kind == "pole":
        circle(ix + 22, iz, 6, C["pole"])
    elif kind == "rail":
        el.append(f'<line x1="{ix}" y1="{iz}" x2="{ix + 44}" y2="{iz}" stroke="{C["rail"]}" stroke-width="10" stroke-dasharray="3 5"/>')
    elif kind == "arroyo":
        el.append(f'<rect x="{ix}" y="{iz - 12}" width="44" height="24" fill="{C["arroyo"]}" stroke="#a59d8d" stroke-width="3"/>')
    elif kind == "fwy":
        el.append(f'<rect x="{ix}" y="{iz - 12}" width="44" height="24" fill="#6c6964" stroke="#3d3b38" stroke-width="3"/>')
    elif kind == "bp":
        el.append(f'<rect x="{ix}" y="{iz - 14}" width="44" height="28" fill="none" stroke="#1f5fa8" stroke-width="3" stroke-dasharray="8 5"/>')
    text(ix + 58, iz + 1, label, 25, anchor="start", weight=600, halo=False)
el.append(f'<polygon points="{HI - 140},{LO + 70} {HI - 170},{LO + 170} {HI - 140},{LO + 145} {HI - 110},{LO + 170}" fill="{C["text"]}"/>')
text(HI - 140, LO + 205, "N", 34, weight=900)
el.append(f'<rect x="{LO + 60}" y="{HI - 70}" width="500" height="14" fill="{C["text"]}"/>'
          f'<rect x="{LO + 310}" y="{HI - 70}" width="250" height="14" fill="#fff" stroke="{C["text"]}" stroke-width="2"/>')
text(LO + 310, HI - 96, "500 studs (140 m)", 26, weight=700)

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{LO} {LO} {W} {W}" width="2400" height="2400" '
       f'font-family="Segoe UI, system-ui, sans-serif">\n' + "\n".join(el) + "\n</svg>\n")
(OUT / "map_sketch.svg").write_text(svg, encoding="utf-8")
print("wrote", OUT / "map_sketch.svg", len(el), "elements")

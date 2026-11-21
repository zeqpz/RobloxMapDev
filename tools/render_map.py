"""Render plans/map/layout.json as a labelled 2D sketch: plans/map/map_sketch.svg.   python tools/render_map.py"""
import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "plans" / "map"
L = json.loads((OUT / "layout.json").read_text(encoding="utf-8"))
LO, _, HI, _ = L["extents"]
PLAY = L["playable"][2]
W = HI - LO

COL = dict(desert="#e9d7b2", ground="#dcc49c", sidewalk="#ece7dd", asphalt="#55524d", median="#a3ab72",
           park="#93bf6c", parkpath="#efe4c8", lot="#bdb7ad", yard="#c9b48f", interior="#c4502b", shell="#cbb595",
           house="#e6d6bb", houseedge="#9b8768", landmark="#7d6552", mountain="#b08a68", river="#5b9bc4",
           bosque="#7fa45a", freeway="#8b8781", arroyo="#d8d2c4", text="#2a2622", pole="#6b4a2b", light="#f2c230")
DIST = {"Downtown": "#f6efe4", "Westside": "#efe2cc", "Northside": "#e9dfcb", "Southside": "#ead8c0",
        "Eastside": "#e2dbd0", "Ranch Road": "#e7d6b5"}

el = []


def esc(s):
    return html.escape(str(s))


def rect(x, z, w, d, fill, stroke="none", sw=0, extra=""):
    el.append(f'<rect x="{x:.1f}" y="{z:.1f}" width="{w:.1f}" height="{d:.1f}" fill="{fill}" stroke="{stroke}" '
              f'stroke-width="{sw}" {extra}/>')


def text(x, z, s, size=26, fill=COL["text"], anchor="middle", weight=500, rot=0, halo=True):
    tr = f' transform="rotate({rot} {x:.1f} {z:.1f})"' if rot else ""
    h = (f'stroke="#fffdf8" stroke-width="{size * 0.22:.1f}" paint-order="stroke" ' if halo else "")
    el.append(f'<text x="{x:.1f}" y="{z:.1f}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" '
              f'fill="{fill}" {h}dominant-baseline="middle"{tr}>{esc(s)}</text>')


def line(x1, z1, x2, z2, stroke, sw, extra=""):
    el.append(f'<line x1="{x1:.1f}" y1="{z1:.1f}" x2="{x2:.1f}" y2="{z2:.1f}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')


# ------------------------------------------------------------------ terrain ring
rect(LO, LO, W, W, COL["desert"])
for s in L["scenery"]:
    x, z, w, d = s["x"], s["z"], s["w"], s["d"]
    if s["kind"] == "mountain":
        pts = []
        steps = 18
        for i in range(steps + 1):
            t = i / steps
            pts.append((x + 40 + 60 * math.sin(t * 9.0) + 25 * math.sin(t * 23), z + t * d))
        poly = " ".join(f"{px:.0f},{pz:.0f}" for px, pz in pts) + f" {x + w},{z + d} {x + w},{z}"
        el.append(f'<polygon points="{poly}" fill="{COL["mountain"]}" opacity="0.9"/>')
        for k in range(1, 6):   # contour hatching
            off = k * w / 6
            path = " ".join(f"{px + off * 0.9:.0f},{pz:.0f}" for px, pz in pts)
            el.append(f'<polyline points="{path}" fill="none" stroke="#8d6a4c" stroke-width="5" opacity="0.5"/>')
        text(x + w * 0.55, z + d * 0.5, s["name"], 40, "#4a3523", rot=90, weight=700)
    elif s["kind"] == "river":
        rect(x, z, w, d, COL["bosque"])
        pts = [(x + w * 0.45 + 70 * math.sin(i / 10 * 3.1), z + i / 40 * d) for i in range(41)]
        el.append('<polyline points="' + " ".join(f"{a:.0f},{b:.0f}" for a, b in pts) +
                  f'" fill="none" stroke="{COL["river"]}" stroke-width="70" stroke-linecap="round"/>')
        for i in range(70):
            tx, tz = x + 30 + (i * 137) % max(1, w - 60), z + (i * 389) % d
            el.append(f'<circle cx="{tx}" cy="{tz}" r="16" fill="#5f8a3e" opacity="0.8"/>')
        text(x + w * 0.5, z + d * 0.62, s["name"], 40, "#1e3d57", rot=-90, weight=700)
    elif s["kind"] == "freeway":
        rect(x, z, w, d, COL["freeway"])
        line(x, z + d / 2, x + w, z + d / 2, "#f4f1ea", 3, 'stroke-dasharray="40 30"')
        text(2600, z - 40, s["name"], 32, weight=700)
    elif s["kind"] == "arroyo":
        rect(x, z, w, d, COL["arroyo"], "#a29a8a", 4)
        text(x + 700, z + d / 2, s["name"], 28)
    elif s["kind"] == "desert":
        line(x, z + d * 0.75, x + w, z + d * 0.75, "#6b5a48", 8, 'stroke-dasharray="6 18"')
        text(x + 2200, z + d * 0.75 - 30, "rail line", 26)
        text(x + w / 2, z + d * 0.45, s["name"], 34, weight=600)

# playable ground + district tints
rect(0, 0, PLAY, PLAY, COL["ground"], "#7a6448", 6)
for r in range(4):
    for c in range(4):
        pass

# ------------------------------------------------------------------ lots (under roads' sidewalks visually fine)
dist_boxes = {}
for l in L["lots"]:
    b = dist_boxes.setdefault(l["district"], [1e9, 1e9, -1e9, -1e9])
    b[0], b[1] = min(b[0], l["x"]), min(b[1], l["z"])
    b[2], b[3] = max(b[2], l["x"] + l["w"]), max(b[3], l["z"] + l["d"])

for l in L["lots"]:
    x, z, w, d, k = l["x"], l["z"], l["w"], l["d"], l["kind"]
    if k == "park":
        rect(x, z, w, d, COL["park"], "#5d8a3f", 4)
        cx, cz = x + w / 2, z + d / 2
        for (a, b2) in [((x, z), (x + w, z + d)), ((x + w, z), (x, z + d)), ((cx, z), (cx, z + d)), ((x, cz), (x + w, cz))]:
            line(a[0], a[1], b2[0], b2[1], COL["parkpath"], 16)
        el.append(f'<circle cx="{cx}" cy="{cz}" r="70" fill="{COL["parkpath"]}"/>')
        el.append(f'<circle cx="{cx}" cy="{cz}" r="30" fill="{COL["river"]}"/>')
        for i in range(4):   # spawn pads
            ang = i * math.pi / 2 + math.pi / 4
            el.append(f'<rect x="{cx + 105 * math.cos(ang) - 14:.0f}" y="{cz + 105 * math.sin(ang) - 14:.0f}" width="28" '
                      f'height="28" fill="#ffffff" stroke="{COL["interior"]}" stroke-width="5"/>')
        rect(x + 30, z + 30, 90, 60, "#c9a36b", "#8a6a3c", 3)            # basketball
        rect(x + w - 120, z + 30, 90, 70, "#e3c46c", "#8a6a3c", 3)       # playground
        el.append(f'<circle cx="{x + w - 80}" cy="{z + d - 80}" r="26" fill="#f6efe2" stroke="#8a6a3c" stroke-width="4"/>')
        for i in range(36):
            tx, tz = x + 20 + (i * 97) % (w - 40), z + 20 + (i * 211) % (d - 40)
            if abs(tx - cx) > 40 and abs(tz - cz) > 40:
                el.append(f'<circle cx="{tx}" cy="{tz}" r="11" fill="#4e7c32" opacity="0.85"/>')
        text(cx, cz - 115, "SPAWN", 40, "#ffffff", weight=800, halo=False)
        text(cx, z + d - 22, "Plaza Park (spawn)", 30, weight=700)
        continue
    if k in ("parking", "yard"):
        rect(x, z, w, d, COL["lot"] if k == "parking" else COL["yard"], "#8f897e", 3,
             'stroke-dasharray="10 8"' if k == "yard" else "")
    if k == "house" and l.get("style") == "mobile":
        rect(x, z, w, d, "#d9caa9", "#9b8768", 3)
        for i in range(int(w // 34)):
            for j in range(int(d // 70)):
                rect(x + 8 + i * 34, z + 10 + j * 70, 16, 50, "#f1ece2", "#8d806b", 2)
        text(x + w / 2, z + d / 2, l["name"], 26, weight=700)
        continue
    bl = l.get("bldg")
    if l.get("canopy"):
        c = l["canopy"]
        rect(x, z, w, d, COL["lot"], "#8f897e", 3)
        rect(c["x"], c["z"], c["w"], c["d"], "#f1ede6", "#c4502b" if k == "interior" else "#6d6a64", 6)
    elif k in ("interior", "shell", "landmark") and bl:
        rect(x, z, w, d, COL["lot"], "#8f897e", 3)
    if bl:
        fill = {"interior": COL["interior"], "shell": COL["shell"], "landmark": COL["landmark"],
                "house": COL["house"], "yard": COL["shell"], "parking": COL["shell"]}[k]
        rect(bl["x"], bl["z"], bl["w"], bl["d"], fill, "#3b2a1f" if k != "house" else COL["houseedge"],
             3 if k != "house" else 1.5)
        if l.get("bays"):
            bx = bl["x"]
            for name, bw, num in l["bays"]:
                rect(bx, bl["z"], bw, bl["d"], COL["interior"] if num else COL["shell"], "#3b2a1f", 3)
                if num:
                    el.append(f'<circle cx="{bx + bw / 2}" cy="{bl["z"] + bl["d"] / 2}" r="20" fill="#fff" stroke="#3b2a1f" stroke-width="3"/>')
                    text(bx + bw / 2, bl["z"] + bl["d"] / 2 + 1, num, 24, weight=800, halo=False)
                bx += bw
        elif l.get("num"):
            el.append(f'<circle cx="{bl["x"] + bl["w"] / 2}" cy="{bl["z"] + bl["d"] / 2}" r="24" fill="#fff" stroke="#3b2a1f" stroke-width="3"/>')
            text(bl["x"] + bl["w"] / 2, bl["z"] + bl["d"] / 2 + 1, l["num"], 28, weight=800, halo=False)
    if k in ("interior", "shell", "landmark", "yard", "parking") and not l.get("bays"):
        text(x + w / 2, z + d - 18, l["name"], 22 if k != "interior" else 24, weight=700 if k == "interior" else 500)
    if l.get("bays"):
        text(x + w / 2, z + 30, "Strip mall: Clothing · Hair · Tattoo", 24, weight=700)

# ------------------------------------------------------------------ roads
order = {"loop": 0, "rural": 0, "alley": 1, "local": 2, "collector": 3, "arterial": 4}
roads = sorted(L["roads"], key=lambda r: order[r["cls"]])
for r in roads:     # sidewalks first
    if r["sidewalk"]:
        line(r["x1"], r["z1"], r["x2"], r["z2"], COL["sidewalk"], r["row"], 'stroke-linecap="butt"')
for r in roads:
    line(r["x1"], r["z1"], r["x2"], r["z2"], COL["asphalt"] if r["cls"] != "rural" else "#7a6f60", r["ctc"], 'stroke-linecap="butt"')
for r in roads:
    if r["cls"] == "arterial":
        line(r["x1"], r["z1"], r["x2"], r["z2"], COL["median"], 16)
        horiz = r["z1"] == r["z2"]
        for off in (-36, -22, 22, 36):
            if horiz:
                line(r["x1"], r["z1"] + off, r["x2"], r["z2"] + off, "#f5f2ea", 1.5, 'stroke-dasharray="20 30"')
            else:
                line(r["x1"] + off, r["z1"], r["x2"] + off, r["z2"], "#f5f2ea", 1.5, 'stroke-dasharray="20 30"')
    elif r["cls"] in ("collector", "loop", "rural"):
        line(r["x1"], r["z1"], r["x2"], r["z2"], "#f2c230", 2.5)

# street lights along arterials (both sides) + powerlines along locals/collectors
for r in L["roads"]:
    horiz = r["z1"] == r["z2"]
    length = abs(r["x2"] - r["x1"]) + abs(r["z2"] - r["z1"])
    if r["cls"] == "arterial":
        n = int(length // 100)
        for i in range(n + 1):
            t = i * 100
            for side in (-1, 1):
                off = side * (r["ctc"] / 2 + 3)
                px, pz = (r["x1"] + t, r["z1"] + off) if horiz else (r["x1"] + off, r["z1"] + t)
                el.append(f'<circle cx="{px:.0f}" cy="{pz:.0f}" r="4.5" fill="{COL["light"]}" stroke="#6d5a1f" stroke-width="1"/>')
    if r["cls"] in ("local", "collector", "rural"):
        off = r["ctc"] / 2 + r["sidewalk"] + 3
        if horiz:
            line(r["x1"], r["z1"] - off, r["x2"], r["z2"] - off, COL["pole"], 2, 'stroke-dasharray="6 6" opacity="0.8"')
            for i in range(int(length // 120) + 1):
                el.append(f'<circle cx="{r["x1"] + i * 120:.0f}" cy="{r["z1"] - off:.0f}" r="4" fill="{COL["pole"]}"/>')
        else:
            line(r["x1"] + off, r["z1"], r["x2"] + off, r["z2"], COL["pole"], 2, 'stroke-dasharray="6 6" opacity="0.8"')
            for i in range(int(length // 120) + 1):
                el.append(f'<circle cx="{r["x1"] + off:.0f}" cy="{r["z1"] + i * 120:.0f}" r="4" fill="{COL["pole"]}"/>')

# intersections: signals where arterial meets arterial/collector, stop signs where local meets collector/arterial
def inter(a, b):
    ah, bh = a["z1"] == a["z2"], b["z1"] == b["z2"]
    if ah == bh:
        return None
    h, v = (a, b) if ah else (b, a)
    x, z = v["x1"], h["z1"]
    tol = 70   # locals stop at the block edge, half a ROW short of the crossing road's centreline
    if min(h["x1"], h["x2"]) - tol <= x <= max(h["x1"], h["x2"]) + tol and min(v["z1"], v["z2"]) - tol <= z <= max(v["z1"], v["z2"]) + tol:
        return x, z
    return None


rs = L["roads"]
for i in range(len(rs)):
    for j in range(i + 1, len(rs)):
        p = inter(rs[i], rs[j])
        if not p:
            continue
        cls = {rs[i]["cls"], rs[j]["cls"]}
        if "arterial" in cls and cls & {"arterial", "collector"}:
            for dx, dz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                el.append(f'<circle cx="{p[0] + dx * 58:.0f}" cy="{p[1] + dz * 58:.0f}" r="9" fill="#2b2b2b"/>'
                          f'<circle cx="{p[0] + dx * 58:.0f}" cy="{p[1] + dz * 58:.0f}" r="4.5" fill="#3ec46d"/>')
        elif "local" in cls and cls & {"collector", "arterial", "loop"}:
            loc = rs[i] if rs[i]["cls"] == "local" else rs[j]
            lh = loc["z1"] == loc["z2"]
            # sign sits at the local street's end, just before the crossing road
            ex = min((loc["x1"], loc["x2"]), key=lambda v: abs(v - p[0])) if lh else p[0]
            ez = p[1] if lh else min((loc["z1"], loc["z2"]), key=lambda v: abs(v - p[1]))
            el.append(f'<circle cx="{ex:.0f}" cy="{ez:.0f}" r="10" fill="#d23a2e" stroke="#fff" stroke-width="2"/>')

# street names
named = {}
for r in L["roads"]:
    if r["cls"] in ("arterial", "collector", "rural") or (r["cls"] == "local" and r["name"] in ("Plaza St", "Court St", "Center St", "Market St")):
        key = r["name"]
        horiz = r["z1"] == r["z2"]
        if r["cls"] == "loop":
            continue
        positions = [0.18, 0.62] if r["cls"] == "arterial" else [0.3]
        for t in positions:
            x = r["x1"] + (r["x2"] - r["x1"]) * t
            z = r["z1"] + (r["z2"] - r["z1"]) * t
            text(x, z, r["name"].upper(), 24 if r["cls"] != "local" else 18, "#ffffff", rot=0 if horiz else -90,
                 weight=800, halo=False)
text(PLAY / 2, 64, "LOOP 66", 22, "#ffffff", weight=800, halo=False)
text(PLAY / 2, PLAY - 64, "LOOP 66", 22, "#ffffff", weight=800, halo=False)

# district labels
for name, (x0, z0, x1, z1) in dist_boxes.items():
    if name == "Downtown":
        lx, lz = 2115, 1110
    elif name == "Eastside":
        lx, lz = 2655, 2120
    elif name == "Ranch Road":
        lx, lz = 2660, 330
    else:
        lx, lz = (x0 + x1) / 2, (z0 + z1) / 2
    text(lx, lz, name.upper(), 56, "#5a3d27", weight=900)

# baseplate overlay (4 x 2048)
for i in range(2):
    for j in range(2):
        bx, bz = LO + i * 2048, LO + j * 2048
        rect(bx, bz, 2048, 2048, "none", "#1f5fa8", 6, 'stroke-dasharray="40 24" opacity="0.65"')
        text(bx + 160, bz + 50, f"Baseplate {j * 2 + i + 1}", 30, "#1f5fa8", weight=800)
rect(0, 0, PLAY, PLAY, "none", "#7a2b18", 8, 'stroke-dasharray="18 12"')
text(PLAY - 330, PLAY + 26, "playable 3072 x 3072 studs", 26, "#7a2b18", weight=700)


# legend (south desert strip, above the rail line)
lx, lz = 160, 3300
rect(lx - 40, lz - 60, 2860, 150, "#fffdf8", "#7a6448", 4, 'opacity="0.95"')
items = [
    ("box", COL["interior"], "Required interior building (#)"), ("box", COL["shell"], "Exterior-only shell"),
    ("box", COL["house"], "House lot"), ("box", COL["lot"], "Parking / yard"), ("box", COL["park"], "Spawn park"),
    ("road", COL["asphalt"], "Road (arterial has green median)"), ("sig", None, "Traffic signal"),
    ("stop", None, "Stop sign"), ("light", None, "Streetlight (100-stud spacing)"), ("pole", None, "Power line + pole (120)"),
]
for i, (kind, col, label) in enumerate(items):
    ix, iz = lx + (i % 5) * 560, lz + (i // 5) * 60
    if kind == "box":
        rect(ix, iz - 16, 44, 32, col, "#3b2a1f", 2)
    elif kind == "road":
        rect(ix, iz - 12, 44, 24, col); line(ix, iz, ix + 44, iz, COL["median"], 6)
    elif kind == "sig":
        el.append(f'<circle cx="{ix + 22}" cy="{iz}" r="12" fill="#2b2b2b"/><circle cx="{ix + 22}" cy="{iz}" r="6" fill="#3ec46d"/>')
    elif kind == "stop":
        el.append(f'<circle cx="{ix + 22}" cy="{iz}" r="12" fill="#d23a2e" stroke="#fff" stroke-width="2"/>')
    elif kind == "light":
        el.append(f'<circle cx="{ix + 22}" cy="{iz}" r="9" fill="{COL["light"]}" stroke="#6d5a1f" stroke-width="2"/>')
    elif kind == "pole":
        line(ix, iz, ix + 44, iz, COL["pole"], 3, 'stroke-dasharray="6 6"')
        el.append(f'<circle cx="{ix + 22}" cy="{iz}" r="6" fill="{COL["pole"]}"/>')
    text(ix + 60, iz + 1, label, 26, anchor="start", weight=600, halo=False)
text(1536, LO + 150, "ALAMO COUNTY - map sketch v1", 52, weight=900)

# north arrow + scale bar
el.append(f'<polygon points="{HI - 140},{LO + 70} {HI - 170},{LO + 170} {HI - 140},{LO + 145} {HI - 110},{LO + 170}" fill="{COL["text"]}"/>')
text(HI - 140, LO + 205, "N", 34, weight=900)
sx, sz = LO + 60, HI - 70
rect(sx, sz, 500, 14, COL["text"])
rect(sx + 250, sz, 250, 14, "#ffffff", COL["text"], 2)
text(sx + 250, sz - 26, "500 studs (140 m)", 26, weight=700)

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{LO} {LO} {W} {W}" width="2000" height="2000" '
       f'font-family="Segoe UI, system-ui, sans-serif">\n' + "\n".join(el) + "\n</svg>\n")
(OUT / "map_sketch.svg").write_text(svg, encoding="utf-8")
print("wrote", OUT / "map_sketch.svg", len(el), "elements")

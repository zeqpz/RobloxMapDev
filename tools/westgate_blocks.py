"""Decode the Westgate road raster (sampled from the live Roads_v8 meshes in Studio) and extract the buildable blocks.

python tools/westgate_blocks.py -> plans/westgate/blocks.json + blocks.png
Grid: x0 = 900, z0 = -1000 (Roblox world), 4 studs per cell, 275 x 620 cells.
Classes: '.' open ground, 'A' road asphalt, 'S' sidewalk, 'F' freeway, 'p' freeway landscaping pavers.
Blocks = connected open-ground areas fully enclosed by sidewalk (lots between the roads). Polygons are in Roblox world
x/z, traced from the raster and then snapped back out to the sidewalk edge (+0 studs); building setbacks are applied
by the planner, not here.
"""
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "plans" / "westgate"
X0, Z0, STEP, NX, NZ = 900, -1000, 4, 275, 620
CODE = {".": 0, "p": 1, "A": 2, "S": 3, "F": 4}


def decode(path):
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("="):
            rows += [rows[-1]] * int(line[1:])
            continue
        row = []
        for ch, n in re.findall(r"([.pASF])(\d*)", line):
            row += [CODE[ch]] * (int(n) if n else 1)
        assert len(row) == NX, (len(rows), len(row))
        rows.append(row)
    g = np.array(rows, np.uint8)
    assert g.shape == (NZ, NX), g.shape
    return g


def main():
    g = decode(OUT / "road_grid.rle")
    open_ = g == 0
    lab, n = ndi.label(open_)
    blocks = []
    for i in range(1, n + 1):
        m = lab == i
        ys, xs = np.nonzero(m)
        if m.sum() < 60:            # < ~1000 sq studs: slivers, median noses
            continue
        if xs.min() == 0 or ys.min() == 0 or xs.max() == NX - 1 or ys.max() == NZ - 1:
            continue                # touches the survey edge: outside Westgate's road ring
        # must be ringed by sidewalk (not just enclosed by freeway)
        ring = ndi.binary_dilation(m, iterations=2) & ~m
        if (g[ring] == 3).mean() < 0.5:
            continue
        cells = [box(X0 + x * STEP, Z0 + y * STEP, X0 + (x + 1) * STEP, Z0 + (y + 1) * STEP) for y, x in zip(ys, xs)]
        poly = unary_union(cells).buffer(0.5, join_style=2).buffer(-0.5, join_style=2).simplify(1.5)
        if poly.geom_type != "Polygon":
            poly = max(poly.geoms, key=lambda p: p.area)
        minx, minz, maxx, maxz = poly.bounds
        blocks.append(dict(area=round(poly.area), bounds=[round(v) for v in (minx, minz, maxx, maxz)],
                           rect=round(poly.area / ((maxx - minx) * (maxz - minz)), 2),
                           poly=[[round(x, 1), round(z, 1)] for x, z in poly.exterior.coords]))
    blocks.sort(key=lambda b: (b["bounds"][1], b["bounds"][0]))
    for k, b in enumerate(blocks):
        b["id"] = f"WG{k + 1:02d}"
    (OUT / "blocks.json").write_text(json.dumps(blocks, indent=1))
    # preview
    col = np.array([[214, 196, 160], [150, 170, 120], [70, 70, 74], [200, 200, 196], [110, 110, 140]], np.uint8)
    img = Image.fromarray(col[g]).resize((NX * 2, NZ * 2), Image.NEAREST)
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    for b in blocks:
        pts = [((x - X0) / STEP * 2, (z - Z0) / STEP * 2) for x, z in b["poly"]]
        d.line(pts, fill=(220, 40, 40), width=2)
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        d.text((cx - 10, cy - 6), b["id"], fill=(0, 0, 0))
    img.save(OUT / "blocks.png")
    for b in blocks:
        w, h = b["bounds"][2] - b["bounds"][0], b["bounds"][3] - b["bounds"][1]
        print(f'{b["id"]}: {w:4d} x {h:4d} studs, area {b["area"]:7d}, rect-fill {b["rect"]}, bounds {b["bounds"]}')


if __name__ == "__main__":
    main()

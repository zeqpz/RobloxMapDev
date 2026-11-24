"""Quality checks for kit-built blocks (pure Python, runs inside Blender on Kit.elems / Kit.planes).

check(elems, planes) -> dict(clashes, floating, loose_planes)
  clashes       pairs of solids from DIFFERENT parts that interpenetrate deeper than PEN (oriented-box SAT depth);
                ground elements (lot slabs etc.) are exempt - things are allowed to be set into the ground.
  floating      parts that touch nothing else (no other part and no ground within TOUCH).
  loose_planes  decals/sign faces with no solid directly behind them (within 0.15).
Every solid is an oriented box (cylinders/tubes use an inscribed box), so a reported clash is a real overlap.
"""
import math
from collections import defaultdict

from mathutils import Vector

PEN = 0.04
TOUCH = 0.06
CELL = 8.0


def _aabb(e):
    c, ax, h = e["c"], e["ax"], e["h"]
    ext = Vector((sum(abs(ax[i][k]) * h[i] for i in range(3)) for k in range(3)))
    return c - ext, c + ext


def sat_depth(a, b, margin=0.0):
    """Smallest overlap along the 15 SAT axes (<= 0 means separated). margin inflates both boxes."""
    T = b["c"] - a["c"]
    axes = list(a["ax"]) + list(b["ax"])
    for u in a["ax"]:
        for v in b["ax"]:
            w = u.cross(v)
            if w.length > 1e-6:
                axes.append(w.normalized())
    best = 1e9
    for L in axes:
        ra = sum(a["h"][i] * abs(a["ax"][i].dot(L)) for i in range(3)) + margin
        rb = sum(b["h"][i] * abs(b["ax"][i].dot(L)) for i in range(3)) + margin
        ov = ra + rb - abs(T.dot(L))
        if ov <= 0:
            return ov
        best = min(best, ov)
    return best


def _inside(p, e, margin=0.02):
    d = p - e["c"]
    return all(abs(d.dot(e["ax"][i])) <= e["h"][i] + margin for i in range(3))


def check(elems, planes, pen=PEN, ignore=()):
    grid = defaultdict(list)
    boxes = []
    for i, e in enumerate(elems):
        lo, hi = _aabb(e)
        boxes.append((lo, hi))
        for gx in range(int(math.floor(lo.x / CELL)), int(math.floor(hi.x / CELL)) + 1):
            for gy in range(int(math.floor(lo.y / CELL)), int(math.floor(hi.y / CELL)) + 1):
                grid[(gx, gy)].append(i)
    seen = set()
    clashes = []
    touched = defaultdict(bool)
    for cell, ids in grid.items():
        n = len(ids)
        for ii in range(n):
            i = ids[ii]
            ei = elems[i]
            loi, hii = boxes[i]
            for jj in range(ii + 1, n):
                j = ids[jj]
                ej = elems[j]
                if ei["part"] == ej["part"]:
                    continue
                key = (i, j) if i < j else (j, i)
                if key in seen:
                    continue
                seen.add(key)
                loj, hij = boxes[j]
                if (loi.x > hij.x + TOUCH or loj.x > hii.x + TOUCH or loi.y > hij.y + TOUCH or loj.y > hii.y + TOUCH
                        or loi.z > hij.z + TOUCH or loj.z > hii.z + TOUCH):
                    continue
                d = sat_depth(ei, ej)
                if d > -TOUCH:
                    touched[ei["part"]] = True
                    touched[ej["part"]] = True
                if d > pen and not ei["ground"] and not ej["ground"]:
                    if any(s in ei["part"] or s in ej["part"] for s in ignore):
                        continue
                    clashes.append(dict(depth=round(d, 3), a=f'{ei["piece"]} | {ei["part"]} | {ei["mat"]}',
                                        b=f'{ej["piece"]} | {ej["part"]} | {ej["mat"]}',
                                        at=tuple(round(v, 1) for v in ((ei["c"] + ej["c"]) / 2))))
    parts = defaultdict(list)
    for e in elems:
        if not e["ground"]:
            parts[e["part"]].append(e)
    floating = []
    for p, es in parts.items():
        if not touched[p]:
            zmin = min(_aabb(e)[0].z for e in es)
            floating.append(dict(part=p, piece=es[0]["piece"], at=tuple(round(v, 1) for v in es[0]["c"]), zmin=round(zmin, 2)))
    loose = []
    for pl in planes:
        ok = False
        for d in (0.03, 0.08, 0.15):                     # something solid right behind the face
            p = pl["c"] - pl["n"] * d
            cx, cy = int(math.floor(p.x / CELL)), int(math.floor(p.y / CELL))
            if any(_inside(p, elems[i]) for i in grid.get((cx, cy), ())):
                ok = True
                break
        if not ok:
            loose.append(dict(mat=pl["mat"], piece=pl["piece"], at=tuple(round(v, 1) for v in pl["c"])))
    # one entry per pair of parts (deepest overlap), so a report line = one thing to fix
    agg = {}
    for c in clashes:
        pa, pb = c["a"].split(" | ")[1], c["b"].split(" | ")[1]
        key = tuple(sorted((pa, pb)))
        if key not in agg or c["depth"] > agg[key]["depth"]:
            agg[key] = dict(c, n=agg.get(key, {}).get("n", 0) + 1)
        else:
            agg[key]["n"] += 1
    clashes = sorted(agg.values(), key=lambda c: -c["depth"])
    return dict(clashes=clashes, floating=floating, loose_planes=loose)


def report(res, limit=60):
    out = [f'clashes {len(res["clashes"])}, floating parts {len(res["floating"])}, loose decals/signs {len(res["loose_planes"])}']
    for c in res["clashes"][:limit]:
        a, b = c["a"].split(" | "), c["b"].split(" | ")
        out.append(f'  CLASH {c["depth"]:.2f} at {c["at"]}: {a[1]} [{a[2]}]  X  {b[1]} [{b[2]}]  ({c.get("n", 1)} hits)')
    for f in res["floating"][:limit]:
        out.append(f'  FLOAT {f["part"]} at {f["at"]} zmin {f["zmin"]}')
    for l in res["loose_planes"][:limit]:
        out.append(f'  LOOSE {l["mat"]} {l["piece"]} at {l["at"]}')
    return "\n".join(out)

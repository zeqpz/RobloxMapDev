"""Alamo County map layout - the single source for the 2D sketch AND later Studio greybox placement.

    python tools/map_layout.py      -> plans/map/layout.json + plans/map/map_sketch.svg

Coordinates are studs. Map space: x west->east, z north->south, playable city 0..3072, scenery ring -512..3584
(4096 x 4096 = 4 default 2048-stud baseplates). Studio world position = (x - 1536, 0, z - 1536), so the main
intersection (Camino Real x Mesa Blvd) is the world origin.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "plans" / "map"
S = json.loads((ROOT / "standards" / "sizes.json").read_text(encoding="utf-8"))

PLAY, RING = 3072, 512
LO, HI = -RING, PLAY + RING
# road classes: right-of-way (ROW) and curb-to-curb (CTC), from the sizing standard
LANE, SW_C, SW_R = S["roads"]["lane"], S["roads"]["sidewalk_commercial"], S["roads"]["sidewalk_residential"]
CLASS = {
    "arterial": dict(ctc=6 * LANE + 16, sidewalk=SW_C, lanes="3+3, 16 median"),       # 100 ctc / 120 ROW
    "collector": dict(ctc=2 * LANE + 2 * 10, sidewalk=SW_R, lanes="1+1, parking both sides"),  # 48 / 64
    "loop": dict(ctc=2 * LANE + 2 * 14, sidewalk=0, lanes="1+1, 14 shoulders"),       # 56 / 56
    "local": dict(ctc=36, sidewalk=SW_R, lanes="2-way, no lines"),                     # 36 / 52
    "alley": dict(ctc=18, sidewalk=0, lanes="dirt/broken asphalt"),
    "rural": dict(ctc=2 * LANE, sidewalk=0, lanes="1+1, dirt shoulders"),
}
for c in CLASS.values():
    c["row"] = c["ctc"] + 2 * c["sidewalk"]

roads, lots, notes = [], [], []


def road(rid, name, cls, x1, z1, x2, z2):
    roads.append(dict(id=rid, name=name, cls=cls, x1=x1, z1=z1, x2=x2, z2=z2, **CLASS[cls]))


def lot(lid, name, kind, district, x, z, w, d, bldg=None, **kw):
    """kind: interior (enterable, required), shell (exterior only), park, parking, yard, house, landmark."""
    rec = dict(id=lid, name=name, kind=kind, district=district, x=x, z=z, w=w, d=d)
    if bldg:
        rec["bldg"] = bldg      # dict(x, z, w, d, h, stories) in map space
    rec.update(kw)
    lots.append(rec)
    return rec


# ------------------------------------------------------------------ road grid
A, C, LP = CLASS["arterial"]["row"], CLASS["collector"]["row"], CLASS["loop"]["row"]
MID, QW, QE = 1536, 768, 2304
road("camino", "Camino Real (old Route 66)", "arterial", 0, MID, PLAY, MID)
road("mesa", "Mesa Blvd", "arterial", MID, 0, MID, PLAY)
road("c_ash", "Ash St", "collector", QW, 64, QW, PLAY - 64)
road("c_juniper", "Juniper St", "collector", QE, 64, QE, PLAY - 64)
road("c_2nd", "2nd Ave", "collector", 64, QW, PLAY - 64, QW)
road("c_6th", "6th Ave", "collector", 64, QE, PLAY - 64, QE)
road("loop_n", "Loop 66", "loop", 64, 64, PLAY - 64, 64)
road("loop_s", "Loop 66", "loop", 64, PLAY - 64, PLAY - 64, PLAY - 64)
road("loop_w", "Loop 66", "loop", 64, 64, 64, PLAY - 64)
road("loop_e", "Loop 66", "loop", PLAY - 64, 64, PLAY - 64, PLAY - 64)
road("ranch", "Ranch Road", "rural", PLAY - 64, 340, 3170, 340)

# superblock interiors (between road edges)
half = {"loop": LP / 2, "collector": C / 2, "arterial": A / 2}
COL = [(64 + half["loop"], QW - half["collector"]), (QW + half["collector"], MID - half["arterial"]),
       (MID + half["arterial"], QE - half["collector"]), (QE + half["collector"], PLAY - 64 - half["loop"])]
ROW = COL  # symmetric grid


def block(r, c):
    (x0, x1), (z0, z1) = COL[c - 1], ROW[r - 1]
    return x0, z0, x1, z1


# ------------------------------------------------------------------ residential fill
def houses(district, x0, z0, x1, z1, prefix, frontage=64, depth=110, local_every=None, style="stucco"):
    """E-W local streets inside a block, house lots facing them on both sides, alley-free."""
    height = z1 - z0
    n_local = 2 if height > 600 else 1
    zs = [z0 + height * (i + 1) / (n_local + 1) for i in range(n_local)]
    lr = CLASS["local"]["row"]
    for i, zc in enumerate(zs):
        road(f"{prefix}_l{i}", f"{prefix.split('_')[0].title()} local {i + 1}", "local", x0, zc, x1, zc)
    strips = []
    edges = [z0] + [v for zc in zs for v in (zc - lr / 2, zc + lr / 2)] + [z1]
    for a, b in zip(edges[::2], edges[1::2]):
        strips.append((a, b))
    n = 0
    for (a, b) in strips:
        rows = [(a, "s")] if b - a < 2 * depth else [(a, "n"), (b - depth, "s")]
        if b - a < 2 * depth:   # one row, face the nearer local street
            rows = [(a if a > z0 else b - depth, "s" if a > z0 else "n")]
        for (za, face) in rows:
            x = x0 + 4
            while x + frontage <= x1 - 4:
                bw, bd = frontage * 0.62, depth * 0.42
                bz = za + (10 if face == "n" else depth - bd - 22) if False else za + (depth - bd) / 2
                lot(f"{prefix}_h{n}", "House", "house", district, x, za, frontage, depth,
                    bldg=dict(x=x + (frontage - bw) / 2, z=bz, w=bw, d=bd, h=13, stories=1), style=style)
                n += 1
                x += frontage
    return n


# ------------------------------------------------------------------ DOWNTOWN (required interiors cluster here)
x0, z0, x1, z1 = block(2, 2)                      # NW of the main intersection
road("plaza_st", "Plaza St", "local", 1010, z0, 1010, z1)
road("court_st", "Court St", "local", x0, 1010, x1, 1010)
lr = CLASS["local"]["row"] / 2
lot("spawn_park", "SPAWN - Plaza Park", "park", "Downtown", 1010 + lr, 1010 + lr, x1 - 1010 - lr, z1 - 1010 - lr,
    features=["central fountain plaza + spawn pads under shade canopies", "gazebo/bandstand", "map + job board kiosk",
              "basketball court", "playground", "palm + cottonwood groves, gravel xeriscape beds",
              "bus stop on Camino Real", "taxi/ride pickup bay on Mesa Blvd", "public restrooms (shell)"])
lot("court", "Court Building", "interior", "Downtown", 1010 + lr, z0, 264, 1010 - lr - z0,
    bldg=dict(x=1060, z=z0 + 20, w=190, d=120, h=46, stories=3), num=4)
lot("post", "Post Office", "interior", "Downtown", 1036 + 264, z0, x1 - 1300, 1010 - lr - z0,
    bldg=dict(x=1320, z=z0 + 30, w=110, d=90, h=18, stories=1), num=5, extras=["mail-truck lot + loading dock at rear"])
lot("city_lot", "Public parking + bus depot", "parking", "Downtown", x0, 1010 + lr, 1010 - lr - x0, z1 - 1010 - lr)
lot("tower", "Alamo Tower (office landmark)", "landmark", "Downtown", x0, z0, 1010 - lr - x0, 1010 - lr - z0,
    bldg=dict(x=x0 + 30, z=z0 + 30, w=120, d=120, h=160, stories=12))

x0, z0, x1, z1 = block(2, 3)                      # NE of the main intersection
road("dt_ne_l", "Center St", "local", x0, 1000, x1, 1000)
lot("police", "Police Station", "interior", "Downtown", x0, 1160, 320, z1 - 1160,
    bldg=dict(x=x0 + 30, z=1190, w=170, d=120, h=28, stories=2), num=6,
    extras=["sally port + secure fenced lot behind", "public lot facing Mesa Blvd", "fire lane at entrance"])
lot("gym", "Gym", "interior", "Downtown", x0 + 360, 1200, x1 - x0 - 360, z1 - 1200,
    bldg=dict(x=x0 + 400, z=1230, w=150, d=170, h=24, stories=1), num=8)
lot("clinic", "Clinic", "shell", "Downtown", x0, z0, 300, 1000 - lr - z0, bldg=dict(x=x0 + 30, z=z0 + 30, w=200, d=110, h=20, stories=1))
lot("apts_dt", "Apartments", "shell", "Downtown", x0 + 330, z0, x1 - x0 - 330, 1000 - lr - z0,
    bldg=dict(x=x0 + 360, z=z0 + 20, w=260, d=120, h=40, stories=3))
lot("bank", "Bank", "shell", "Downtown", x0, 1000 + lr, 300, 1150 - 1000 - lr, bldg=dict(x=x0 + 40, z=1000 + lr + 15, w=140, d=90, h=22, stories=1))

x0, z0, x1, z1 = block(3, 2)                      # SW of the main intersection: Route 66 strip
lot("fastfood", "Fast Food (drive-thru)", "interior", "Downtown", 1300, z0, x1 - 1300, 170,
    bldg=dict(x=1340, z=z0 + 40, w=70, d=60, h=16, stories=1), num=9, extras=["drive-thru lane loop", "menu board", "pylon sign"])
strip = lot("strip_mall", "Strip mall", "interior", "Downtown", x0 + 10, z0, 1300 - x0 - 30, 240,
            bldg=dict(x=x0 + 40, z=z0 + 150, w=400, d=80, h=20, stories=1),
            bays=[["Clothing Shop", 110, 10], ["Hair Shop", 60, 11], ["Tattoo Shop", 60, 12],
                  ["Laundromat (shell)", 70, None], ["Vacant / for lease", 100, None]],
            extras=["parking in front (11x22 stalls)", "fire lane along storefronts", "tow-away signs at entries"])
road("dt_sw_l", "Route 66 local", "local", x0, 1940, x1, 1940)
lot("motel", "Route 66 Motel", "shell", "Downtown", x0 + 10, 1940 + lr, 360, z1 - 1940 - lr,
    bldg=dict(x=x0 + 30, z=1990, w=300, d=50, h=24, stories=2))
lot("autoshop", "Auto repair", "shell", "Downtown", x0 + 400, 1940 + lr, x1 - x0 - 400, z1 - 1940 - lr,
    bldg=dict(x=x0 + 440, z=2000, w=140, d=90, h=20, stories=1))

x0, z0, x1, z1 = block(3, 3)                      # SE of the main intersection
lot("gas", "Gas Station", "interior", "Downtown", x0, z0, 220, 200,
    bldg=dict(x=x0 + 120, z=z0 + 110, w=80, d=60, h=18, stories=1), num=3,
    canopy=dict(x=x0 + 20, z=z0 + 25, w=90, d=55, h=21.5), extras=["6 pumps under canopy", "price pylon at corner"])
lot("conv", "Convenience Store", "interior", "Downtown", x0 + 240, z0, 170, 170,
    bldg=dict(x=x0 + 270, z=z0 + 70, w=90, d=70, h=17, stories=1), num=2)
lot("gun", "Gun Shop", "interior", "Downtown", x0 + 430, z0, 170, 180,
    bldg=dict(x=x0 + 460, z=z0 + 60, w=80, d=100, h=18, stories=1), num=1, extras=["barred windows", "range at rear"])
road("dt_se_l", "Market St", "local", x0, 1900, x1, 1900)
lot("church", "Church", "shell", "Downtown", x0, 1900 + lr, 260, z1 - 1900 - lr, bldg=dict(x=x0 + 60, z=1980, w=120, d=160, h=34, stories=1))
lot("laund2", "Tire shop + taqueria", "shell", "Downtown", x0 + 290, 1900 + lr, x1 - x0 - 290, z1 - 1900 - lr,
    bldg=dict(x=x0 + 320, z=1990, w=220, d=80, h=18, stories=1))

# ------------------------------------------------------------------ EASTSIDE industrial
x0, z0, x1, z1 = block(2, 4)
lot("warehouse", "Warehouse", "interior", "Eastside", x0 + 40, 1060, 420, z1 - 1060,
    bldg=dict(x=x0 + 80, z=1150, w=300, d=170, h=34, stories=1), num=13, extras=["6 loading docks", "truck court + fenced yard"])
lot("tow", "Tow + impound yard", "yard", "Eastside", x0 + 40, z0 + 20, 380, 240, bldg=dict(x=x0 + 60, z=z0 + 40, w=70, d=50, h=16, stories=1))
lot("rail", "Rail spur + grain silos (landmark)", "landmark", "Eastside", x1 - 120, z0, 120, z1 - z0,
    bldg=dict(x=x1 - 100, z=z0 + 120, w=60, d=60, h=110, stories=1))
x0, z0, x1, z1 = block(3, 4)
lot("junk", "Junkyard", "yard", "Eastside", x0 + 20, z0 + 20, 360, 300)
lot("ind2", "Small warehouses (shells)", "shell", "Eastside", x0 + 400, z0 + 20, x1 - x0 - 420, 300,
    bldg=dict(x=x0 + 420, z=z0 + 60, w=180, d=120, h=26, stories=1))
lot("trucks", "Truck stop", "shell", "Eastside", x0 + 20, z0 + 360, x1 - x0 - 40, z1 - z0 - 380,
    bldg=dict(x=x0 + 60, z=z0 + 420, w=120, d=80, h=20, stories=1))

# ------------------------------------------------------------------ RANCH ROAD (foothills) + PRISON
x0, z0, x1, z1 = block(1, 4)
for i, (rx, rz) in enumerate([(x0 + 20, z0 + 20), (x0 + 330, z0 + 20), (x0 + 20, z0 + 360), (x0 + 330, z0 + 360)]):
    lot(f"ranch{i}", "Ranch (big lot, corral)", "house", "Ranch Road", rx, rz, 290, 300,
        bldg=dict(x=rx + 90, z=rz + 100, w=70, d=50, h=16, stories=1), style="ranch")
lot("prison", "Prison", "interior", "Ranch Road", 3170, 120, 400, 460,
    bldg=dict(x=3230, z=200, w=260, d=200, h=30, stories=2), num=7,
    extras=["double fence + razor wire perimeter", "4 guard towers", "sally port gate on Ranch Road", "yard + basketball court"])
x0, z0, x1, z1 = block(4, 4)
lot("mhp", "Mobile home park", "house", "Southside", x0 + 20, z0 + 20, x1 - x0 - 40, z1 - z0 - 40, style="mobile")

# ------------------------------------------------------------------ WESTSIDE
x0, z0, x1, z1 = block(2, 1)
lot("grocery", "Grocery big box", "shell", "Westside", x0 + 20, 1160, x1 - x0 - 40, z1 - 1160,
    bldg=dict(x=x0 + 120, z=1180, w=360, d=150, h=34, stories=1))
houses("Westside", x0, z0, x1, 1140, "west_a", style="stucco")
x0, z0, x1, z1 = block(3, 1)
lot("carlot", "Used car lot", "yard", "Westside", x0 + 20, z0, 320, 200, bldg=dict(x=x0 + 30, z=z0 + 20, w=50, d=40, h=14, stories=1))
lot("gas2", "Gas station (shell, 2nd)", "shell", "Westside", x0 + 360, z0, x1 - x0 - 380, 200,
    bldg=dict(x=x0 + 440, z=z0 + 110, w=70, d=50, h=17, stories=1), canopy=dict(x=x0 + 380, z=z0 + 20, w=80, d=50, h=21.5))
houses("Westside", x0, z0 + 230, x1, z1, "west_b", style="stucco")
x0, z0, x1, z1 = block(1, 1)
houses("Westside", x0, z0, x1, z1, "west_c", style="tract")

# ------------------------------------------------------------------ NORTHSIDE
for c in (2, 3):
    x0, z0, x1, z1 = block(1, c)
    houses("Northside", x0, z0, x1, z1, f"north_{c}", style="ranchhouse")

# ------------------------------------------------------------------ SOUTHSIDE
x0, z0, x1, z1 = block(4, 1)
houses("Southside", x0, z0, x1, z1, "south_a", frontage=96, depth=150, style="southvalley")
x0, z0, x1, z1 = block(4, 2)
houses("Southside", x0, z0, x1, z1, "south_b", frontage=56, style="brick")
x0, z0, x1, z1 = block(4, 3)
houses("Southside", x0, z0, x1, z1, "south_c", style="fourplex")

# ------------------------------------------------------------------ scenery ring (not playable)
scenery = [
    dict(id="mountains", name="Sierra Alamo (mountain backdrop)", kind="mountain", x=3250, z=650, w=HI - 3250, d=HI - 650 - 0),
    dict(id="mountains_n", name="Foothills", kind="mountain", x=3600 - 10, z=LO, w=HI - 3590, d=650 - LO),
    dict(id="river", name="Rio Alamo + bosque", kind="river", x=LO, z=LO, w=RING - 60, d=HI - LO),
    dict(id="interstate", name="I-66 (elevated, scenery)", kind="freeway", x=LO, z=-300, w=HI - LO, d=60),
    dict(id="desert_s", name="Desert + rail line", kind="desert", x=0, z=PLAY + 40, w=PLAY, d=RING - 40),
    dict(id="arroyo", name="Arroyo Seco (concrete channel)", kind="arroyo", x=0, z=PLAY + 140, w=PLAY + 200, d=40),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = dict(
        name="Alamo County", units="studs", playable=[0, 0, PLAY, PLAY], extents=[LO, LO, HI, HI],
        studio_origin="world = (x - 1536, 0, z - 1536); main intersection = world origin",
        baseplates="playable 3072 x 3072 = 2.25 baseplates; with scenery 4096 x 4096 = 4 baseplates (2048 each)",
        road_classes=CLASS, roads=roads, lots=lots, scenery=scenery)
    (OUT / "layout.json").write_text(json.dumps(data, indent=1), encoding="utf-8")
    req = sorted([l for l in lots if l.get("num")] + [dict(name=b[0], num=b[2]) for b in strip["bays"] if b[2]],
                 key=lambda r: r["num"])
    print(f"roads {len(roads)}  lots {len(lots)}  houses {sum(1 for l in lots if l['kind'] == 'house')}")
    for r in req:
        print(f"  {r['num']:2d} {r['name']}")


if __name__ == "__main__":
    main()

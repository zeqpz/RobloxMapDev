"""Sign faces, painted wall lettering and wear decals for the Westgate buildings (PIL, no downloads, fictional names).

python tools/wg_textures.py -> textures/buildings/<name>.png (RGBA where it is a decal)
Roblox: sign faces -> Decal / SurfaceAppearance ColorMap on the sign mesh; wear decals -> Decal (Transparency via alpha).
"""
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "textures" / "buildings"
OUT.mkdir(parents=True, exist_ok=True)


def font(size, kind="bold"):
    names = {"bold": ["arialbd.ttf"], "black": ["ariblk.ttf", "arialbd.ttf"], "serif": ["georgiab.ttf", "timesbd.ttf"],
             "script": ["BRUSHSCI.TTF", "segoesc.ttf", "georgiai.ttf"], "cond": ["impact.ttf", "arialbd.ttf"],
             "regular": ["arial.ttf"]}[kind]
    for n in names:
        try:
            return ImageFont.truetype(n, size)
        except OSError:
            continue
    return ImageFont.load_default()


def weather(img, amount=0.25, seed=0):
    """Sun fade + grime speckle on an RGB(A) sign."""
    rng = np.random.default_rng(seed)
    a = np.asarray(img.convert("RGBA"), np.float32)
    h, w = a.shape[:2]
    noise = rng.normal(0, 1, (h // 8 + 1, w // 8 + 1))
    noise = np.asarray(Image.fromarray(((noise - noise.min()) / np.ptp(noise) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
    fade = 1 - amount * 0.5 * noise[..., None]
    a[..., :3] = a[..., :3] * fade + 210 * (1 - fade) * 0.35
    grime = np.clip(rng.normal(0, 1, (h, w)) * 0.5, 0, 1)[..., None] * amount * 40
    a[..., :3] -= grime
    # vertical dirt streaks from the top edge
    for _ in range(int(w / 40)):
        x = rng.integers(0, w)
        ln = rng.integers(h // 6, h // 2)
        a[:ln, max(0, x - 2):x + 2, :3] *= 0.9
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def save(img, name):
    img.save(OUT / f"{name}.png", optimize=True)
    print(name, img.size)


# ------------------------------------------------------------------ strip-mall tenant boards (panel signs on the mansard)
TENANTS = [
    ("plaza_lucky7", "LUCKY 7 LAUNDRY", "COIN-OP  WASH & FOLD", (24, 82, 150), (250, 245, 230)),
    ("plaza_ink", "INK DESERT", "TATTOO  &  PIERCING", (20, 20, 22), (220, 40, 40)),
    ("plaza_pho", "PHO MESA", "Vietnamese Kitchen", (238, 228, 200), (150, 30, 30)),
    ("plaza_cuts", "Q'S CUTS", "BARBER SHOP  -  WALK INS", (245, 245, 245), (30, 60, 140)),
    ("plaza_bail", "ALAMO BAIL BONDS", "24 HRS  -  SE HABLA ESPANOL", (250, 210, 40), (20, 20, 20)),
    ("plaza_cash", "CASH NOW", "CHECKS CASHED  -  LOANS", (30, 120, 60), (255, 255, 255)),
]


def tenant_boards():
    for name, big, small, bg, fg in TENANTS:
        img = Image.new("RGBA", (1024, 256), bg + (255,))
        d = ImageDraw.Draw(img)
        d.rectangle([6, 6, 1017, 249], outline=fg, width=6)
        d.text((512, 105), big, fill=fg, font=font(118 if len(big) < 12 else 92, "black"), anchor="mm")
        d.text((512, 205), small, fill=fg, font=font(44), anchor="mm")
        save(weather(img, 0.35, hash(name) % 100), name)
    img = Image.new("RGBA", (1024, 256), (235, 232, 222, 255))
    d = ImageDraw.Draw(img)
    d.text((512, 100), "FOR LEASE", fill=(170, 30, 30), font=font(120, "black"), anchor="mm")
    d.text((512, 205), "505-555-0142   1,400 SQ FT", fill=(40, 40, 40), font=font(46), anchor="mm")
    save(weather(img, 0.5, 9), "plaza_lease")
    # plaza pylon sign
    img = Image.new("RGBA", (512, 1024), (60, 40, 30, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 511, 300], fill=(214, 120, 52))
    d.ellipse([140, 30, 372, 262], fill=(250, 200, 70))
    for k in range(5):
        d.rectangle([0, 150 + k * 30, 511, 162 + k * 30], fill=(214, 120, 52))
    d.text((256, 272), "SUNSET PLAZA", fill=(255, 250, 235), font=font(52, "black"), anchor="mm")
    rows = ["LAUNDRY", "TATTOO", "PHO MESA", "BARBER", "BAIL BONDS", "CASH NOW"]
    for i, r in enumerate(rows):
        y = 320 + i * 115
        d.rectangle([20, y, 491, y + 100], fill=(240, 236, 224))
        d.text((256, y + 50), r, fill=(40, 30, 25), font=font(58, "bold"), anchor="mm")
    save(weather(img, 0.45, 3), "plaza_pylon")


# ------------------------------------------------------------------ hot dog stand roof sign + menu
def top_dog():
    img = Image.new("RGBA", (1024, 320), (250, 196, 40, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 1023, 319], outline=(170, 40, 30), width=14)
    # cartoon dog: sausage body + ears, original simple shape
    d.rounded_rectangle([560, 120, 980, 230], radius=55, fill=(170, 90, 40))
    d.ellipse([900, 80, 1000, 180], fill=(170, 90, 40))
    d.polygon([(935, 85), (965, 40), (975, 100)], fill=(120, 60, 25))
    d.ellipse([955, 115, 972, 132], fill=(20, 20, 20))
    for x in (600, 680, 850, 920):
        d.rectangle([x, 220, x + 18, 275], fill=(150, 80, 35))
    d.line([(560, 170), (515, 130)], fill=(150, 80, 35), width=16)
    d.text((285, 120), "TOP DOG", fill=(170, 40, 30), font=font(112, "black"), anchor="mm")
    d.text((290, 250), "CHILE DOGS  -  FRITO PIE", fill=(40, 30, 20), font=font(44), anchor="mm")
    save(weather(img, 0.4, 5), "topdog_roof")
    img = Image.new("RGBA", (512, 640), (30, 30, 32, 255))
    d = ImageDraw.Draw(img)
    d.text((256, 50), "MENU", fill=(250, 196, 40), font=font(64, "black"), anchor="mm")
    items = [("Chile Dog", "3.25"), ("Foot Long", "4.50"), ("Frito Pie", "4.75"), ("Corn Dog", "2.50"),
             ("Green Chile Fries", "3.95"), ("Horchata", "2.25"), ("Fountain Drink", "1.75")]
    for i, (a, b) in enumerate(items):
        y = 130 + i * 68
        d.text((40, y), a, fill=(245, 240, 230), font=font(40, "bold"), anchor="lm")
        d.text((472, y), b, fill=(245, 240, 230), font=font(40, "bold"), anchor="rm")
    save(weather(img, 0.3, 6), "topdog_menu")


# ------------------------------------------------------------------ taqueria: hand-painted wall lettering + sign
def el_sol():
    img = Image.new("RGBA", (1024, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((512, 128), "EL SOL", fill=(196, 34, 30, 255), font=font(200, "black"), anchor="mm")
    save(weather(img, 0.3, 11), "elsol_wall_name")
    img = Image.new("RGBA", (1024, 200), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((512, 100), "TACOS  BURRITOS  MENUDO", fill=(200, 40, 30, 255), font=font(92, "cond"), anchor="mm")
    save(weather(img, 0.35, 12), "elsol_wall_menu")
    img = Image.new("RGBA", (1024, 512), (250, 248, 236, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 400, 1023, 511], fill=(30, 130, 70))
    d.ellipse([40, 60, 300, 320], fill=(250, 190, 30))
    for k in range(12):
        a = k * math.pi / 6
        d.line([(170 + 130 * math.cos(a), 190 + 130 * math.sin(a)), (170 + 175 * math.cos(a), 190 + 175 * math.sin(a))], fill=(250, 150, 30), width=14)
    d.text((660, 150), "El Sol", fill=(200, 35, 30), font=font(170, "script"), anchor="mm")
    d.text((660, 300), "TAQUERIA  MEXICANA", fill=(200, 35, 30), font=font(58, "bold"), anchor="mm")
    d.text((512, 455), "Desayuno  -  Comida  -  Todo el Dia", fill=(255, 255, 255), font=font(46, "bold"), anchor="mm")
    save(weather(img, 0.45, 13), "elsol_pole")


# ------------------------------------------------------------------ motel
def motel():
    img = Image.new("RGBA", (512, 1024), (20, 70, 80, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([12, 12, 499, 1011], outline=(240, 200, 120), width=10)
    d.text((256, 110), "DESERT", fill=(250, 240, 220), font=font(104, "black"), anchor="mm")
    d.text((256, 235), "ROSE", fill=(240, 110, 120), font=font(150, "script"), anchor="mm")
    d.text((256, 360), "MOTOR LODGE", fill=(250, 240, 220), font=font(58, "bold"), anchor="mm")
    for y, t in ((480, "COLOR TV"), (560, "WEEKLY RATES"), (640, "AIR COOLED")):
        d.text((256, y), t, fill=(240, 200, 120), font=font(56, "bold"), anchor="mm")
    d.rectangle([40, 730, 472, 860], fill=(15, 15, 15))
    d.text((256, 795), "VACANCY", fill=(250, 60, 60), font=font(84, "black"), anchor="mm")
    d.text((256, 940), "OFFICE  >", fill=(250, 240, 220), font=font(64, "bold"), anchor="mm")
    save(weather(img, 0.55, 21), "motel_pole")
    img = Image.new("RGBA", (512, 128), (240, 236, 220, 255))
    d = ImageDraw.Draw(img)
    d.text((256, 64), "OFFICE", fill=(20, 70, 80), font=font(92, "black"), anchor="mm")
    save(weather(img, 0.35, 22), "motel_office")
    for n in range(1, 31):
        img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.text((64, 64), str(100 + n if n <= 15 else 200 + n - 15), fill=(230, 200, 120, 255), font=font(70, "bold"), anchor="mm")
        img.save(OUT / f"room_{n:02d}.png")


# ------------------------------------------------------------------ generic signs
def misc_signs():
    def plate(name, lines, bg, fg, size=(512, 384), border=None):
        img = Image.new("RGBA", size, bg + (255,))
        d = ImageDraw.Draw(img)
        if border:
            d.rectangle([8, 8, size[0] - 9, size[1] - 9], outline=border, width=10)
        n = len(lines)
        for i, (t, s) in enumerate(lines):
            d.text((size[0] / 2, size[1] * (i + 0.5) / n), t, fill=fg, font=font(s, "black"), anchor="mm")
        save(weather(img, 0.35, hash(name) % 50), name)
    plate("tow_away", [("TOW-AWAY", 66), ("ZONE", 66), ("Unauthorized vehicles", 30), ("towed at owner's expense", 30)],
          (250, 250, 248), (200, 20, 20), border=(200, 20, 20))
    plate("no_trespass", [("NO", 90), ("TRESPASSING", 70)], (250, 250, 248), (20, 20, 20), border=(20, 20, 20))
    plate("customer_parking", [("CUSTOMER", 70), ("PARKING ONLY", 60)], (250, 250, 248), (30, 80, 160), border=(30, 80, 160))
    img = Image.new("RGBA", (384, 512), (30, 80, 180, 255))
    d = ImageDraw.Draw(img)
    d.ellipse([162, 70, 222, 130], fill=(255, 255, 255))
    d.line([(192, 140), (192, 290), (290, 290), (320, 400)], fill=(255, 255, 255), width=26)
    d.line([(192, 210), (280, 210)], fill=(255, 255, 255), width=24)
    d.arc([80, 220, 260, 420], 60, 300, fill=(255, 255, 255), width=24)
    d.text((192, 470), "RESERVED", fill=(255, 255, 255), font=font(54, "black"), anchor="mm")
    save(weather(img, 0.3, 31), "accessible")


# ------------------------------------------------------------------ wear decals (alpha)
def decals():
    rng = random.Random(4)
    # grime drips (under sills, roof scuppers)
    for k in range(3):
        img = Image.new("RGBA", (256, 512), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for _ in range(26):
            x = rng.uniform(10, 246)
            ln = rng.uniform(80, 480)
            w = rng.uniform(2, 9)
            a = rng.randint(30, 90)
            d.line([(x, 0), (x + rng.uniform(-4, 4), ln)], fill=(40, 32, 24, a), width=int(w))
        d.rectangle([0, 0, 255, 24], fill=(40, 32, 24, 70))
        save(img.filter(ImageFilter.GaussianBlur(2.5)), f"decal_drip_{k}")
    # oil stains for parking stalls
    for k in range(3):
        img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for _ in range(9):
            cx, cy = rng.uniform(80, 176), rng.uniform(70, 186)
            r = rng.uniform(20, 70)
            d.ellipse([cx - r, cy - r * 0.8, cx + r, cy + r * 0.8], fill=(10, 10, 10, rng.randint(40, 90)))
        save(img.filter(ImageFilter.GaussianBlur(9)), f"decal_oil_{k}")
    # asphalt crack network (dark lines)
    for k in range(3):
        img = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for _ in range(10):
            x, y = rng.uniform(0, 1024), rng.uniform(0, 1024)
            ang = rng.uniform(0, 6.28)
            pts = [(x, y)]
            for _ in range(rng.randint(20, 60)):
                ang += rng.gauss(0, 0.5)
                x += math.cos(ang) * 12
                y += math.sin(ang) * 12
                pts.append((x, y))
                if rng.random() < 0.08:          # alligator branch
                    bx, by, ba = x, y, ang + rng.choice([-1.3, 1.3])
                    br = [(bx, by)]
                    for _ in range(rng.randint(4, 12)):
                        ba += rng.gauss(0, 0.6)
                        bx += math.cos(ba) * 9
                        by += math.sin(ba) * 9
                        br.append((bx, by))
                    d.line(br, fill=(12, 12, 12, 200), width=3)
            d.line(pts, fill=(12, 12, 12, 230), width=4)
        save(img.filter(ImageFilter.GaussianBlur(0.8)), f"decal_cracks_{k}")
    # graffiti tags: original letter-ish strokes, spray colours with outlines
    cols = [(230, 230, 235), (40, 40, 40), (200, 40, 40), (40, 120, 220), (250, 190, 40), (160, 60, 180)]
    for k in range(5):
        img = Image.new("RGBA", (1024, 384), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        fill = cols[rng.randrange(len(cols))]
        out = cols[rng.randrange(len(cols))]
        x = 80
        for _ in range(rng.randint(3, 5)):          # loopy glyphs
            pts = []
            cx, cy = x, 190
            for t in range(16):
                a = t / 15 * rng.uniform(4, 8)
                pts.append((cx + math.cos(a) * rng.uniform(30, 80) + t * 6, cy + math.sin(a * 1.3) * rng.uniform(40, 120)))
            d.line(pts, fill=out + (255,), width=34, joint="curve")
            d.line(pts, fill=fill + (255,), width=20, joint="curve")
            x += rng.uniform(150, 210)
        for _ in range(30):                          # overspray
            px, py = rng.uniform(60, 960), rng.uniform(60, 330)
            d.ellipse([px, py, px + 4, py + 4], fill=fill + (120,))
        if rng.random() < 0.6:
            d.line([(70, 320), (x, 300)], fill=out + (255,), width=10)
        save(img.filter(ImageFilter.GaussianBlur(1.2)), f"decal_tag_{k}")
    # stucco patch (lighter mismatched paint rectangle)
    img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for _ in range(4):
        x, y = rng.uniform(40, 300), rng.uniform(40, 300)
        d.rectangle([x, y, x + rng.uniform(80, 200), y + rng.uniform(60, 180)], fill=(240, 228, 205, 170))
    save(img.filter(ImageFilter.GaussianBlur(3)), "decal_patch")


if __name__ == "__main__":
    tenant_boards()
    top_dog()
    el_sol()
    motel()
    misc_signs()
    decals()


def door_stickers():
    img = Image.new("RGBA", (256, 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((128, 40), "PUSH", fill=(240, 240, 240, 255), font=font(56, "bold"), anchor="mm")
    save(img, "door_push")
    img = Image.new("RGBA", (256, 320), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((128, 30), "HOURS", fill=(245, 245, 245, 255), font=font(40, "black"), anchor="mm")
    for i, (a, b) in enumerate((("MON-FRI", "9-7"), ("SAT", "10-6"), ("SUN", "CLOSED"))):
        d.text((20, 90 + i * 60), a, fill=(235, 235, 235, 255), font=font(30, "bold"), anchor="lm")
        d.text((236, 90 + i * 60), b, fill=(235, 235, 235, 255), font=font(30, "bold"), anchor="rm")
    d.text((128, 290), "NO LOITERING", fill=(230, 80, 70, 255), font=font(26, "bold"), anchor="mm")
    save(img, "door_hours")


if __name__ == "__main__":
    door_stickers()

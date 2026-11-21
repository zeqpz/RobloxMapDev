"""Reference-photo capture for the city research (Google Maps Street View / satellite + Google Earth 3D).

  python tools/capture.py geocode            # resolve every subject's search string -> data/geocode.json
  python tools/capture.py street abq|ep      # Street View shots       (Maps, software GL - renders headless)
  python tools/capture.py sat abq|ep         # satellite plan views    (Maps)
  python tools/capture.py earth abq|ep       # photoreal 3D obliques   (Google Earth web, needs the GPU)
Re-runnable: shots whose file already exists are skipped. Metadata -> data/shots.jsonl (one JSON per shot).
"""
import io, json, math, os, re, sys, time, urllib.parse, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops, ImageFilter, ImageStat

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from subjects import SUBJECTS  # noqa: E402

DATA = ROOT / "data"; DATA.mkdir(exist_ok=True)
SHOTS = ROOT / "shots"
GEO = DATA / "geocode.json"
ELEV = DATA / "elev.json"
LOG = DATA / "shots.jsonl"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36")
SOFT = ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]
GPU = ["--use-angle=d3d11", "--ignore-gpu-blocklist", "--enable-gpu"]
BBOX = {"abq": (34.90, 35.25, -106.85, -106.40), "ep": (31.60, 32.05, -106.65, -106.15)}
HIDE = """(() => { if (document.getElementById('cleanshot')) return;
 const s=document.createElement('style'); s.id='cleanshot';
 s.textContent='body *{visibility:hidden !important} canvas.bigc{visibility:visible !important}';
 document.head.appendChild(s);
 document.querySelectorAll('canvas').forEach(c=>{ if(c.width>=1000) c.classList.add('bigc'); }); })()"""
UNHIDE = "document.getElementById('cleanshot')?.remove()"
ONLY = sys.argv[3] if len(sys.argv) > 3 else ""
MONTHS = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (19|20)\d\d"


# ------------------------------------------------------------------ geo helpers
def offset(lat, lng, dist_m, bearing_deg):
    r = 6371000.0
    b = math.radians(bearing_deg); la = math.radians(lat); lo = math.radians(lng)
    la2 = math.asin(math.sin(la) * math.cos(dist_m / r) + math.cos(la) * math.sin(dist_m / r) * math.cos(b))
    lo2 = lo + math.atan2(math.sin(b) * math.sin(dist_m / r) * math.cos(la),
                          math.cos(dist_m / r) - math.sin(la) * math.sin(la2))
    return math.degrees(la2), math.degrees(lo2)


def bearing(lat1, lng1, lat2, lng2):
    la1, la2 = math.radians(lat1), math.radians(lat2); dl = math.radians(lng2 - lng1)
    x = math.sin(dl) * math.cos(la2)
    y = math.cos(la1) * math.sin(la2) - math.sin(la1) * math.cos(la2) * math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def dist(lat1, lng1, lat2, lng2):
    kx = 111320 * math.cos(math.radians(lat1))
    return math.hypot((lat2 - lat1) * 110540, (lng2 - lng1) * kx)


def load(p, default):
    return json.loads(p.read_text()) if p.exists() else default


def log(rec):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def browser(p, gpu=False, vh=900):
    b = p.chromium.launch(channel="chrome", headless=True,
                          args=(GPU if gpu else SOFT) + ["--disable-blink-features=AutomationControlled"],
                          ignore_default_args=["--enable-automation"])
    ctx = b.new_context(viewport={"width": 1600, "height": vh}, locale="en-US", user_agent=UA)
    return b, ctx.new_page()


def settle(pg, min_ms=3500, max_ms=14000, clip=None):
    """Wait until two screenshots 700 ms apart barely differ (tiles finished loading)."""
    pg.wait_for_timeout(min_ms)
    prev, t0 = None, time.time()
    while (time.time() - t0) * 1000 < max_ms - min_ms:
        im = Image.open(io.BytesIO(pg.screenshot(type="jpeg", quality=40, clip=clip))).convert("L").resize((320, 180))
        if prev is not None and ImageStat.Stat(ImageChops.difference(im, prev)).mean[0] < 0.6:
            return
        prev = im
        pg.wait_for_timeout(700)


def save_jpg(png_bytes, path, crop=None):
    im = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    if crop:
        im = im.crop(crop)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, quality=87, optimize=True)
    st = ImageStat.Stat(im.convert("L").resize((160, 90)))
    return st.stddev[0]


# ------------------------------------------------------------------ geocode
def geocode_all():
    geo = load(GEO, {})
    with sync_playwright() as p:
        b, pg = browser(p)
        for s in SUBJECTS:
            if s["id"] in geo:
                continue
            q = urllib.parse.quote_plus(s["q"])
            pg.goto(f"https://www.google.com/maps/search/{q}", wait_until="domcontentloaded")
            lat = lng = None; name = ""
            for _ in range(24):
                pg.wait_for_timeout(500)
                m = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", pg.url)
                if m:
                    lat, lng = float(m.group(1)), float(m.group(2))
                    name = urllib.parse.unquote_plus(pg.url.split("/place/")[1].split("/")[0]) if "/place/" in pg.url else ""
                    break
                links = pg.locator('a[href*="/maps/place/"]')
                if links.count() > 0 and _ > 6:
                    href = links.first.get_attribute("href") or ""
                    m = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", href)
                    if m:
                        lat, lng = float(m.group(1)), float(m.group(2))
                        name = urllib.parse.unquote_plus(href.split("/place/")[1].split("/")[0])
                        break
            la0, la1, lo0, lo1 = BBOX[s["city"]]
            ok = lat is not None and la0 < lat < la1 and lo0 < lng < lo1
            geo[s["id"]] = dict(lat=lat, lng=lng, name=name, ok=ok)
            print(f"{'OK ' if ok else 'BAD'} {s['id']:26s} {lat} {lng}  {name[:70]}", flush=True)
            GEO.write_text(json.dumps(geo, indent=1))
        b.close()


# ------------------------------------------------------------------ street view
def pano_state(pg):
    u = urllib.parse.unquote(pg.url)
    m = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+),[\d.]+a", u)
    pid = re.search(r"!1s([A-Za-z0-9_\-]{10,})!2e", u)
    if not m or "!1e1" not in u or not pid:
        return None
    return float(m.group(1)), float(m.group(2)), pid.group(1)


def sv_meta(pg):
    try:
        txt = pg.evaluate("document.body.innerText")
    except Exception:
        txt = ""
    d = re.search(r"Image capture: ([A-Z][a-z]+ \d{4})", txt)
    date = d.group(1) if d else ((re.search(MONTHS, txt) or [""])[0] if re.search(MONTHS, txt) else "")
    lines = [l.strip() for l in txt.splitlines() if l.strip()]
    place = ""
    for i, l in enumerate(lines):
        if l == "Google Street View" and i >= 2:
            place = ", ".join(lines[max(0, i - 2):i]); break
    return date, place


def pano_url(lat, lng, pid, h, pitch=0, fov=90):
    return f"https://www.google.com/maps/@{lat},{lng},3a,{fov}y,{h % 360:.1f}h,{90 + pitch}t/data=!3m4!1e1!3m2!1s{pid}!2e0"


def open_viewpoint(pg, lat, lng, h, pitch=0, fov=90):
    pg.goto(f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat:.6f},{lng:.6f}"
            f"&heading={h % 360:.0f}&pitch={pitch}&fov={fov}", wait_until="domcontentloaded")
    for _ in range(16):
        pg.wait_for_timeout(500)
        st = pano_state(pg)
        if st:
            return st
        try:
            if "No Street View imagery" in pg.evaluate("document.body.innerText"):
                return None
        except Exception:
            pass
    return None


def shoot_sv(pg, s, k, st, h, pitch, fov, label, done):
    path = SHOTS / s["city"] / s["cat"] / f"{s['id']}__sv{k:02d}.jpg"
    plat, plng, pid = st
    key = (pid, round(h / 20))
    if key in done:
        return False
    done.add(key)
    if path.exists():
        return True
    pg.goto(pano_url(plat, plng, pid, h, pitch, fov), wait_until="domcontentloaded")
    settle(pg, 3000, 12000)
    date, place = sv_meta(pg)
    pg.evaluate(HIDE); pg.wait_for_timeout(250)
    sd = save_jpg(pg.screenshot(), path)
    pg.evaluate(UNHIDE)
    if sd < 6:                       # black / blank frame
        path.unlink(missing_ok=True); print("   blank", path.name); return False
    log(dict(file=str(path.relative_to(ROOT)).replace("\\", "/"), id=s["id"], city=s["city"], cat=s["cat"],
             title=s["title"], kind="street", view=label, heading=round(h % 360), lat=plat, lng=plng, pano=pid,
             date=date, place=place, url=pano_url(plat, plng, pid, h, pitch, fov)))
    print(f"   {path.name}  h={h % 360:.0f} {label}  {date}", flush=True)
    return True


def street(city):
    geo = load(GEO, {})
    with sync_playwright() as p:
        b, pg = browser(p)
        for s in SUBJECTS:
            if s["city"] != city or s["mode"] == "area" or not geo.get(s["id"], {}).get("ok") or (ONLY and ONLY not in s["id"]):
                continue
            g = geo[s["id"]]; tl, tg = g["lat"], g["lng"]
            print(s["id"], flush=True)
            done, k = set(), 0
            pitch = s.get("pitch", 0)
            try:
                if s["mode"] == "orbit":
                    for (dm, bb) in [(0, 0), (45, 0), (45, 90), (45, 180), (45, 270), (80, 45), (80, 225)]:
                        if k >= s.get("max_sv", 5):
                            break
                        vl, vg = offset(tl, tg, dm, bb) if dm else (tl, tg)
                        st = open_viewpoint(pg, vl, vg, bearing(vl, vg, tl, tg) if dm else 0, 2)
                        if not st or dist(st[0], st[1], tl, tg) > 110:
                            continue
                        h = bearing(st[0], st[1], tl, tg)
                        d = dist(st[0], st[1], tl, tg)
                        fov = 90 if d > 25 else 100
                        if shoot_sv(pg, s, k, st, h, 4, fov, f"toward target from {round(d)} m", done):
                            k += 1
                elif s["mode"] == "walk":
                    br = s["bearing"]
                    for i in range(s.get("n", 3)):
                        vl, vg = offset(tl, tg, i * s.get("step", 70), br)
                        st = open_viewpoint(pg, vl, vg, br + 90)
                        if not st:
                            continue
                        views = [(br + 90, "left/right side"), (br - 90, "other side")]
                        if i == 0:
                            views.append((br, "down the street"))
                        if i == s.get("n", 3) - 1:
                            views.append((br + 45, "diagonal"))
                        for h, lab in views:
                            if shoot_sv(pg, s, k, st, h, 2, 90, lab, done):
                                k += 1
                elif s["mode"] == "look":
                    st = open_viewpoint(pg, tl, tg, s["headings"][0])
                    if st:
                        for h in s["headings"]:
                            if shoot_sv(pg, s, k, st, h, pitch, 90, f"heading {h}", done):
                                k += 1
            except Exception as e:
                print("   ERR", s["id"], str(e)[:160], flush=True)
        b.close()


# ------------------------------------------------------------------ satellite plan views
def sat(city):
    geo = load(GEO, {})
    with sync_playwright() as p:
        b, pg = browser(p)
        for s in SUBJECTS:
            if s["city"] != city or not s.get("sat") or not geo.get(s["id"], {}).get("ok"):
                continue
            g = geo[s["id"]]
            path = SHOTS / s["city"] / s["cat"] / f"{s['id']}__sat.jpg"
            if path.exists():
                continue
            url = f"https://www.google.com/maps/@{g['lat']},{g['lng']},{s['sat']}m/data=!3m1!1e3"
            try:
                pg.goto(url, wait_until="domcontentloaded")
                settle(pg, 4000, 12000)
                pg.evaluate(HIDE); pg.wait_for_timeout(250)
                save_jpg(pg.screenshot(), path)
                pg.evaluate(UNHIDE)
                log(dict(file=str(path.relative_to(ROOT)).replace("\\", "/"), id=s["id"], city=city, cat=s["cat"],
                         title=s["title"], kind="satellite", view=f"plan view, ~{s['sat']} m across",
                         lat=g["lat"], lng=g["lng"], url=url))
                print("sat", path.name, flush=True)
            except Exception as e:
                print("   ERR", s["id"], str(e)[:160], flush=True)
        b.close()


# ------------------------------------------------------------------ Google Earth 3D obliques
def elevation(lat, lng, cache):
    key = f"{lat:.5f},{lng:.5f}"
    if key not in cache:
        url = f"https://epqs.nationalmap.gov/v1/json?x={lng}&y={lat}&units=Meters&wkid=4326&includeDate=False"
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                cache[key] = float(json.load(r)["value"])
        except Exception:
            cache[key] = 1520.0 if lat > 33 else 1140.0
        ELEV.write_text(json.dumps(cache, indent=1))
    return cache[key]


DEEP = r"""(mode) => {
  const els = []; const walk = (root) => { for (const el of root.querySelectorAll('*')) {
      els.push(el); if (el.shadowRoot) walk(el.shadowRoot); } };
  walk(document);
  if (mode === 'pct') {
    const v = els.filter(e => !e.children.length && /^\s*\d{1,3}\s*%\s*$/.test(e.textContent || ''))
                 .map(e => parseInt(e.textContent)); return v.length ? Math.min(...v) : -1; }
  if (mode === 'debug') {
    return els.filter(e => !e.children.length && /%/.test(e.textContent || '')).map(e => e.tagName + ':' + e.textContent.trim()).slice(0, 10); }
  const PH = ['Access the data catalog', 'Find and manage', 'New from Google Earth', 'Now available',
              'Analyze sites', 'Starter Map Project'];
  const VA = innerWidth * innerHeight; let n = 0;
  const up = (el) => el.parentElement || (el.getRootNode && el.getRootNode().host) || null;
  for (const e of els) {
    if (e.children.length) continue;
    const t = (e.textContent || '').trim();
    if (!PH.some(p => t.startsWith(p))) continue;
    let el = e, nx;
    while ((nx = up(el)) && nx !== document.body && nx !== document.documentElement) {
      const r = nx.getBoundingClientRect(); if (r.width * r.height > 0.45 * VA) break; el = nx; }
    if (el.style.display !== 'none') { el.style.setProperty('display', 'none', 'important'); n++; } }
  return n; }"""


def earth_dismiss(pg):
    try:
        pg.keyboard.press("Escape")
        return pg.evaluate(DEEP, "hide")
    except Exception:
        return 0


def sharpness(png):
    im = Image.open(io.BytesIO(png)).convert("L").crop((0, 100, 1600, 880)).resize((800, 390))
    return ImageStat.Stat(im.filter(ImageFilter.FIND_EDGES)).mean[0]


def panel_open(png):
    im = Image.open(io.BytesIO(png)).convert("L").crop((320, 500, 1500, 800))
    st = ImageStat.Stat(im)
    return st.mean[0] > 225 and st.stddev[0] < 25


def earth_wait_sharp(pg, max_ms, need):
    """Earth streams low-res tiles first; wait until edge energy is high and has stopped rising."""
    t0 = time.time(); prev = 0.0; e = 0.0
    while (time.time() - t0) * 1000 < max_ms:
        e = sharpness(pg.screenshot())
        if e >= need and abs(e - prev) < 0.04 * e:
            break
        prev = e
        pg.wait_for_timeout(1500)
    pg.wait_for_timeout(800)
    return e


def earth_wait_loaded(pg, max_ms):
    """Earth's status bar shows a load percentage; wait for 100 %, then a short settle."""
    t0 = time.time(); last = -1
    while (time.time() - t0) * 1000 < max_ms:
        try:
            last = pg.evaluate(DEEP, "pct")
        except Exception:
            last = -1
        if last >= 100:
            break
        pg.wait_for_timeout(600)
    pg.wait_for_timeout(1800)
    return last


EARTH_CROP = (0, 92, 1600, 880)   # drop the toolbar (top) and the controls/status bar (bottom)
# Earth web (Flutter) keeps onboarding state in localStorage: mark every promo/coach card as seen,
# keep the projects panel closed, and use the "Clean" map style (no POI pins/labels).
EARTH_PREFS = """(() => { if (location.host !== 'earth.google.com') return;
  const set = (k, v) => { try { localStorage.setItem('earth.' + k, JSON.stringify(v)); } catch (e) {} };
  set('promotions.coachcard.numTimesSeen', '99'); set('promotions.earthMatePromoCard.numTimesSeen', '99');
  set('promotions.earthLogo.numTimesSeen', '99');
  set('promotions.hasDismissedInfraLayersExplorePromotionDialog', 'true');
  set('LayerState', JSON.stringify({layer_style_category: [[], [], [], []], layer_visibility: {}, style_index: 0}));
})()"""   # drop the toolbar (top) and the controls/status bar (bottom)


def earth_jobs(city, houses=False):
    """(subject, lat, lng, views, file-stem) jobs. houses=True builds close-up orbits of single houses
    from the residential Street View walks: target = 16 m off the street in the side-view direction."""
    geo = load(GEO, {})
    subj = {s["id"]: s for s in SUBJECTS}
    jobs = []
    if houses:
        recs = [json.loads(l) for l in LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
        by = {}
        for r in recs:
            if r.get("city") == city and r.get("cat") == "houses" and r.get("kind") == "street"                     and r.get("view") in ("left/right side", "other side"):
                by.setdefault(r["id"], []).append(r)
        for sid, rs in by.items():
            if ONLY and ONLY not in sid:
                continue
            rs.sort(key=lambda r: r["file"])
            picks = [rs[i] for i in (2, 5) if i < len(rs)]
            for n, r in enumerate(picks):
                tl, tg = offset(r["lat"], r["lng"], 16, r["heading"])
                views = [(h, 55, 75, "3D house close-up") for h in (45, 135, 225, 315)]
                jobs.append((subj[sid], tl, tg, views, f"{sid}__house{n + 1}_3d", Path(r["file"]).name))
        return jobs
    for s in SUBJECTS:
        if s["city"] != city or not geo.get(s["id"], {}).get("ok") or (ONLY and ONLY not in s["id"]):
            continue
        if s.get("vista"):
            views = [(v["h"], v["t"], v["d"], "city vista") for v in s["vista"]]
        elif s.get("earth"):
            d = s.get("earth_d", 170)
            views = [(h, 58, d, "3D corner oblique") for h in (45, 135, 225, 315)]
        elif s.get("earth_area"):
            d = s.get("earth_d", 700)
            views = [(h, 62, d, "3D neighborhood oblique") for h in (20, 140, 260)]
        else:
            continue
        g = geo[s["id"]]
        jobs.append((s, g["lat"], g["lng"], views, f"{s['id']}__3d", ""))
    return jobs


def earth(city, houses=False):
    cache = load(ELEV, {})
    jobs = earth_jobs(city, houses)
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(DATA / os.environ.get("EARTH_PROFILE", "earth_profile")), channel="chrome", headless=True,
            args=GPU + ["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
            viewport={"width": 1600, "height": 1000}, locale="en-US", user_agent=UA)
        ctx.add_init_script(EARTH_PREFS)
        pg = ctx.pages[0] if ctx.pages else ctx.new_page()
        for s, lat, lng, views, stem, src in jobs:
            alt = elevation(lat, lng, cache)
            print(stem, f"ground {alt:.0f} m", flush=True)
            for k, (h, t, d, lab) in enumerate(views):
                path = SHOTS / s["city"] / s["cat"] / f"{stem}{k:02d}.jpg"
                if path.exists():
                    continue
                url = f"https://earth.google.com/web/@{lat:.6f},{lng:.6f},{alt:.0f}a,{d}d,35y,{h}h,{t}t,0r"
                try:
                    pg.goto(url, wait_until="domcontentloaded")
                    pg.wait_for_timeout(6000)
                    need = 12 if lab == "city vista" else 20
                    sharp = round(earth_wait_sharp(pg, 50000 if k == 0 else 32000, need), 1)
                    png = pg.screenshot()
                    if panel_open(png):                       # Earth's projects/home panel covers the view
                        print("   panel open - reloading", path.name, flush=True)
                        pg.keyboard.press("Escape"); pg.reload(wait_until="domcontentloaded")
                        pg.wait_for_timeout(6000); earth_wait_sharp(pg, 32000, need)
                        png = pg.screenshot()
                        if panel_open(png):
                            print("   skip (panel)", path.name, flush=True); continue
                    sd = save_jpg(png, path, crop=EARTH_CROP)
                    if sd < 8:
                        path.unlink(missing_ok=True); print("   blank", path.name); continue
                    rec = dict(file=str(path.relative_to(ROOT)).replace("\\", "/"), id=s["id"], city=city,
                               cat=s["cat"], title=s["title"], kind="3d", view=f"{lab}, looking {h} deg",
                               heading=h, lat=lat, lng=lng, url=url, sharp=sharp)
                    if src:
                        rec["house_from"] = src
                    log(rec)
                    print("  ", path.name, f"h={h} sharp={sharp}", flush=True)
                except Exception as e:
                    print("   ERR", stem, str(e)[:160], flush=True)
        ctx.close()


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "geocode":
        geocode_all()
    else:
        {"street": street, "sat": sat, "earth": earth,
         "houses3d": lambda c: earth(c, houses=True)}[cmd](sys.argv[2])

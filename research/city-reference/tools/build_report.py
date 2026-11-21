"""Build REPORT.html (+ thumbnails) from data/shots.jsonl, tools/subjects.py and tools/findings.html.

  python tools/build_report.py
findings.html is hand-written HTML; {{shot:FILE_STEM}} embeds a clickable thumbnail with caption,
{{row:STEM,STEM,...}} a row of them.
"""
import html, json, re, sys
from collections import OrderedDict, defaultdict
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from subjects import SUBJECTS  # noqa: E402

THUMBS = ROOT / "thumbs"
CITY = {"abq": "Albuquerque, NM", "ep": "El Paso, TX"}
CATS = OrderedDict([("houses", "Houses & hoods"), ("shops", "Shops & food"), ("commercial", "Commercial strips"),
                    ("gas_stations", "Gas stations"), ("stores", "Stores"), ("offices", "Offices"),
                    ("civic", "Civic (police, school, hospital, church)"), ("roads", "Roads"),
                    ("terrain", "Terrain")])
KIND = {"street": "Street View", "3d": "3D oblique", "satellite": "Satellite"}
KORDER = {"satellite": 0, "street": 1, "3d": 2}


def thumb(rel):
    src = ROOT / rel
    dst = THUMBS / Path(rel).relative_to("shots")
    if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
        dst.parent.mkdir(parents=True, exist_ok=True)
        im = Image.open(src).convert("RGB"); im.thumbnail((520, 300))
        im.save(dst, quality=80, optimize=True)
    return str(dst.relative_to(ROOT)).replace("\\", "/")


def load_shots():
    recs = OrderedDict()
    for line in (ROOT / "data" / "shots.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if (ROOT / r["file"]).exists():
            recs[r["file"]] = r          # last write wins
    # images whose metadata line was lost: rebuild a minimal record from the file name + geocode
    geo = json.loads((ROOT / "data" / "geocode.json").read_text())
    subj = {s["id"]: s for s in SUBJECTS}
    for p in sorted((ROOT / "shots").glob("*/*/*.jpg")):
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        sid, _, tail = p.stem.partition("__")
        if rel in recs or sid not in subj:
            continue
        s, g = subj[sid], geo.get(sid, {})
        kind = "satellite" if tail == "sat" else ("3d" if "3d" in tail else "street")
        recs[rel] = dict(file=rel, id=sid, city=s["city"], cat=s["cat"], title=s["title"], kind=kind, view="",
                         url=f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={g.get('lat')},{g.get('lng')}")
    for r in recs.values():
        r["stem"] = Path(r["file"]).stem
        r["thumb"] = thumb(r["file"])
    return list(recs.values())


def caption(r):
    bits = [KIND.get(r["kind"], r["kind"]), r.get("view", "")]
    if r.get("date"):
        bits.append(r["date"])
    return " · ".join(b for b in bits if b)


def fig(r, big=False):
    cap = html.escape(caption(r))
    return (f'<figure class="shot{" big" if big else ""}" data-city="{r["city"]}" data-cat="{r["cat"]}" '
            f'data-kind="{r["kind"]}"><a href="{r["file"]}" class="lb" data-cap="{html.escape(r["title"])} — {cap}" '
            f'data-maps="{html.escape(r["url"])}"><img loading="lazy" src="{r["thumb"]}" alt="{cap}"></a>'
            f'<figcaption><span>{cap}</span> <a class="maps" href="{html.escape(r["url"])}" target="_blank" '
            f'rel="noopener">Maps ↗</a></figcaption></figure>')


def render_findings(text, by_stem):
    def one(stem):
        r = by_stem.get(stem.strip())
        return fig(r) if r else f'<div class="missing">missing: {html.escape(stem)}</div>'
    text = re.sub(r"\{\{row:([^}]+)\}\}", lambda m: '<div class="row">' + "".join(one(s) for s in m.group(1).split(",")) + "</div>", text)
    text = re.sub(r"\{\{shot:([^}]+)\}\}", lambda m: one(m.group(1)), text)
    return text


def main():
    shots = load_shots()
    by_stem = {r["stem"]: r for r in shots}
    by_subj = defaultdict(list)
    for r in shots:
        by_subj[r["id"]].append(r)
    for v in by_subj.values():
        v.sort(key=lambda r: (KORDER.get(r["kind"], 9), r["file"]))
    findings = render_findings((ROOT / "tools" / "findings.html").read_text(encoding="utf-8"), by_stem)

    n = defaultdict(int)
    for r in shots:
        n[r["kind"]] += 1
    dates = sorted({r["date"].split()[-1] for r in shots if r.get("date")})
    stats = (f'{len(shots)} images · {n["street"]} Street View · {n["3d"]} 3D obliques · {n["satellite"]} satellite · '
             f'{len(by_subj)} locations · Street View dated {dates[0]}–{dates[-1]}' if dates else f"{len(shots)} images")

    idx, toc = [], []
    for city, cname in CITY.items():
        idx.append(f'<section class="city" id="idx-{city}"><h2>{cname} — photo index</h2>')
        toc.append(f'<li><a href="#idx-{city}">{cname} photos</a><ul>')
        for cat, cn in CATS.items():
            subs = [s for s in SUBJECTS if s["city"] == city and s["cat"] == cat and by_subj.get(s["id"])]
            if not subs:
                continue
            aid = f"idx-{city}-{cat}"
            cnt = sum(len(by_subj[s["id"]]) for s in subs)
            toc.append(f'<li><a href="#{aid}">{cn} <small>{cnt}</small></a></li>')
            idx.append(f'<h3 id="{aid}">{cn}</h3>')
            for s in subs:
                rs = by_subj[s["id"]]
                kinds = ", ".join(f'{sum(1 for r in rs if r["kind"] == k)} {KIND[k]}' for k in KIND if any(r["kind"] == k for r in rs))
                idx.append(f'<article class="subject" id="{s["id"]}"><header><h4>{html.escape(s["title"])}</h4>'
                           f'<p class="meta">{html.escape(s["q"])} · {kinds}</p></header>'
                           f'<div class="grid">{"".join(fig(r) for r in rs)}</div></article>')
        idx.append("</section>")
        toc.append("</ul></li>")

    page = TEMPLATE.replace("{{STATS}}", html.escape(stats)).replace("{{FINDINGS}}", findings) \
                   .replace("{{INDEX}}", "\n".join(idx)).replace("{{TOC}}", "\n".join(toc))
    (ROOT / "REPORT.html").write_text(page, encoding="utf-8")
    print("REPORT.html:", stats)


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Southwest City Reference</title>
<style>
:root{--bg:#f6f4ef;--panel:#fff;--ink:#1f1d1a;--muted:#6d675e;--line:#e3ded4;--accent:#b5562f;--accent2:#2f6f8f;--chip:#efe9de}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#16150f;--panel:#1f1e18;--ink:#ece8df;--muted:#a59f93;--line:#34322a;--accent:#e08a5f;--accent2:#7db7d3;--chip:#2a2820}}
:root[data-theme="dark"]{--bg:#16150f;--panel:#1f1e18;--ink:#ece8df;--muted:#a59f93;--line:#34322a;--accent:#e08a5f;--accent2:#7db7d3;--chip:#2a2820}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:var(--accent2)}
.wrap{display:grid;grid-template-columns:250px minmax(0,1fr);max-width:1500px;margin:0 auto}
nav.toc{position:sticky;top:0;height:100vh;overflow:auto;padding:22px 16px;border-right:1px solid var(--line);font-size:13.5px}
nav.toc ul{list-style:none;margin:0;padding-left:0}nav.toc ul ul{padding-left:12px;margin:4px 0 10px}
nav.toc li{margin:3px 0}nav.toc a{color:var(--ink);text-decoration:none}nav.toc a:hover{color:var(--accent)}
nav.toc small{color:var(--muted)}
main{padding:28px 32px 80px;min-width:0}
h1{font-size:30px;margin:0 0 4px;letter-spacing:-.01em}h2{font-size:23px;margin:46px 0 10px;padding-top:8px;border-top:2px solid var(--ink)}
h3{font-size:18px;margin:30px 0 8px;color:var(--accent)}h4{margin:0;font-size:15.5px}
.lede{color:var(--muted);margin:0 0 18px}.stats{display:inline-block;background:var(--chip);padding:6px 10px;border-radius:6px;font-size:13px}
.prose{max-width:900px}.prose li{margin:3px 0}
table{border-collapse:collapse;width:100%;max-width:980px;margin:10px 0 16px;font-size:14px;background:var(--panel)}
th,td{border:1px solid var(--line);padding:6px 9px;text-align:left;vertical-align:top}th{background:var(--chip)}
.row{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px;margin:10px 0 18px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:8px}
figure.shot{margin:0;background:var(--panel);border:1px solid var(--line);border-radius:6px;overflow:hidden}
figure.shot img{display:block;width:100%;aspect-ratio:16/9;object-fit:cover;background:var(--chip)}
figure.shot figcaption{font-size:11.5px;color:var(--muted);padding:5px 7px;display:flex;justify-content:space-between;gap:6px}
figure.shot a.maps{white-space:nowrap;text-decoration:none}
.subject{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px;margin:12px 0}
.subject header{margin-bottom:8px}.meta{margin:2px 0 0;color:var(--muted);font-size:12.5px}
.filters{position:sticky;top:0;z-index:5;background:var(--bg);padding:10px 0;border-bottom:1px solid var(--line);display:flex;flex-wrap:wrap;gap:6px}
.filters button{border:1px solid var(--line);background:var(--panel);color:var(--ink);padding:5px 10px;border-radius:999px;cursor:pointer;font-size:13px}
.filters button.on{background:var(--ink);color:var(--bg)}
.callout{border-left:4px solid var(--accent);background:var(--panel);padding:10px 14px;margin:14px 0;max-width:900px}
.missing{color:#c33;font-size:12px}
#lb{position:fixed;inset:0;background:rgba(10,10,8,.92);display:none;z-index:50;align-items:center;justify-content:center;flex-direction:column}
#lb.on{display:flex}#lb img{max-width:96vw;max-height:84vh}#lb .cap{color:#eee;font-size:14px;margin-top:10px;padding:0 16px;text-align:center}
#lb .cap a{color:#9cd}#lb button{position:absolute;top:12px;right:16px;font-size:26px;background:none;border:0;color:#fff;cursor:pointer}
@media (max-width:860px){.wrap{display:block}nav.toc{position:static;height:auto;border-right:0;border-bottom:1px solid var(--line)}main{padding:18px 16px 60px}}
</style></head><body>
<div class="wrap">
<nav class="toc"><strong>Contents</strong><ul>
<li><a href="#overview">Overview</a></li><li><a href="#abq">Albuquerque findings</a></li><li><a href="#ep">El Paso findings</a></li>
<li><a href="#kit">Shared building kit</a></li><li><a href="#roads">Roads</a></li><li><a href="#terrain">Terrain & plants</a></li>
<li><a href="#build">What to build first</a></li><li><a href="#method">How these were captured</a></li>
{{TOC}}</ul></nav>
<main>
<h1>Southwest City Reference — Albuquerque &amp; El Paso</h1>
<p class="lede">Street-level, satellite and 3D reference for a Houston-inspired Southwest roleplay city in Roblox.</p>
<p class="stats">{{STATS}}</p>
{{FINDINGS}}
<div class="filters" id="filters">
<button data-f="all" class="on">All</button><button data-f="city:abq">Albuquerque</button><button data-f="city:ep">El Paso</button>
<button data-f="kind:street">Street View</button><button data-f="kind:3d">3D obliques</button><button data-f="kind:satellite">Satellite</button>
</div>
{{INDEX}}
<p class="lede" style="margin-top:40px">Imagery © Google (Street View, Maps satellite, Google Earth). Captured for internal design reference only.</p>
</main></div>
<div id="lb"><button aria-label="Close">×</button><img alt=""><div class="cap"></div></div>
<script>
const links=[...document.querySelectorAll('a.lb')];const lb=document.getElementById('lb');let cur=-1;
function show(i){const vis=links.filter(a=>a.offsetParent!==null);if(!vis.length)return;cur=(i+vis.length)%vis.length;const a=vis[cur];
 lb.querySelector('img').src=a.getAttribute('href');lb.querySelector('.cap').innerHTML=a.dataset.cap.replace(/</g,'&lt;')+' · <a target="_blank" rel="noopener" href="'+a.dataset.maps+'">open in Google Maps ↗</a>';lb.classList.add('on');}
links.forEach(a=>a.addEventListener('click',e=>{e.preventDefault();const vis=links.filter(x=>x.offsetParent!==null);show(vis.indexOf(a));}));
lb.addEventListener('click',e=>{if(e.target===lb||e.target.tagName==='BUTTON')lb.classList.remove('on');});
document.addEventListener('keydown',e=>{if(!lb.classList.contains('on'))return;if(e.key==='Escape')lb.classList.remove('on');if(e.key==='ArrowRight')show(cur+1);if(e.key==='ArrowLeft')show(cur-1);});
document.querySelectorAll('#filters button').forEach(b=>b.addEventListener('click',()=>{
 document.querySelectorAll('#filters button').forEach(x=>x.classList.toggle('on',x===b));const f=b.dataset.f;
 document.querySelectorAll('section.city figure.shot').forEach(fg=>{let ok=true;if(f!=='all'){const[k,v]=f.split(':');ok=fg.dataset[k]===v;}fg.style.display=ok?'':'none';});
 document.querySelectorAll('section.city .subject').forEach(s=>{s.style.display=[...s.querySelectorAll('figure.shot')].some(x=>x.style.display!=='none')?'':'none';});
 document.querySelectorAll('section.city').forEach(sec=>{sec.style.display=[...sec.querySelectorAll('.subject')].some(x=>x.style.display!=='none')?'':'none';});}));
</script></body></html>"""

if __name__ == "__main__":
    main()

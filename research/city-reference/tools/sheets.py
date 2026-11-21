"""Contact sheets for reviewing captures:  python tools/sheets.py OUTDIR [glob-filter]"""
import glob, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
pat = sys.argv[2] if len(sys.argv) > 2 else "*"
files = sorted(glob.glob(str(ROOT / "shots" / "**" / f"{pat}.jpg"), recursive=True))
COLS, TW, TH, LH, PER = 4, 400, 225, 16, 16
try:
    font = ImageFont.truetype("arial.ttf", 13)
except OSError:
    font = ImageFont.load_default()
for n in range(0, len(files), PER):
    chunk = files[n:n + PER]
    rows = (len(chunk) + COLS - 1) // COLS
    sheet = Image.new("RGB", (COLS * TW, rows * (TH + LH)), "white")
    d = ImageDraw.Draw(sheet)
    for i, f in enumerate(chunk):
        im = Image.open(f).convert("RGB"); im.thumbnail((TW, TH))
        x, y = (i % COLS) * TW, (i // COLS) * (TH + LH)
        sheet.paste(im, (x, y + LH))
        d.text((x + 3, y + 1), Path(f).stem, fill="black", font=font)
    sheet.save(out / f"sheet_{pat.replace('*', '')}_{n // PER:02d}.jpg", quality=78)
print(len(files), "files ->", (len(files) + PER - 1) // PER, "sheets")

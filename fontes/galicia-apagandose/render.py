#!/usr/bin/env python3
"""Xera v/galicia-apagandose/ (index.html, datos.json e thumb.png) desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py   (necesita Pillow)
"""
import json
import math
import shutil
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "galicia-apagandose"
miles = lambda n: f"{n:,}".replace(",", ".")

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
anos, E = d["anos"], d["e"]
ult = len(anos) - 1
apag = sum(1 for e in E if e[4][0] not in "-0" and e[4][ult] == "0")
bal = sum(1 for e in E if e[4][ult] == "0")
poucos = sum(1 for e in E if e[4][ult] == "1")
parr = json.loads((HERE / "data" / "coord.json").read_text())["parroquia"]

page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
for k, v in {"APAG": miles(apag), "NENT": miles(len(E)), "BAL": miles(bal), "POUCOS": miles(poucos),
             "A0": anos[0], "A1": anos[-1], "PARR": miles(parr)}.items():
    page = page.replace(f"__{k}__", str(v))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")
shutil.copyfile(HERE / "data" / "datos.json", OUT / "datos.json")

# Miniatura: o mapa en 2025, con brillo
S, M = 1200, 60
xs, ys = [e[0] for e in E], [e[1] for e in E]
kx = math.cos(math.radians(42.8))
sc = (S - 2 * M) / max((max(xs) - min(xs)) * kx, max(ys) - min(ys))
w = (max(xs) - min(xs)) * kx * sc
P = lambda x, y: ((S - w) / 2 + (x - min(xs)) * kx * sc, M + (max(ys) - y) * sc)
base = Image.new("RGB", (S, S), "#0d1017")
dr = ImageDraw.Draw(base)
for r in d["contorno"]:
    dr.polygon([P(x, y) for x, y in r], fill="#131826", outline="#252d40")
luz = Image.new("RGB", (S, S), "black")
dl = ImageDraw.Draw(luz)
RAD = [0, .7, .8, .9, 1, 1.2, 1.5, 2, 3, 4.5]
baleiras = []
for e in E:
    c = e[4][ult]
    x, y = P(e[0], e[1])
    if c == "0":
        baleiras.append((x, y))
    elif c != "-":
        r = RAD[int(c)]
        dl.ellipse([x - r, y - r, x + r, y + r], fill=(255, 216, 138) if int(c) > 4 else (150, 125, 80))
glow = luz.filter(ImageFilter.GaussianBlur(4)).point(lambda v: v * .6)
img = ImageChops.add(ImageChops.add(base, glow), luz)
di = ImageDraw.Draw(img)
for x, y in baleiras:
    di.ellipse([x - 2.6, y - 2.6, x + 2.6, y + 2.6], fill="#7f9ee6")
img.resize((600, 600), Image.LANCZOS).quantize(64).save(OUT / "thumb.png", optimize=True)
print("ok:", OUT, f"apagadas {apag} · baleiras {bal} · 1-4 {poucos} · entidades {len(E)}")

#!/usr/bin/env python3
"""Xera v/monte-concellos/ (index.html, datos.json e thumb.png) desde data/datos.json.

Pasos completos:  python3 descargar.py  →  python3 prep.py  →  python3 render.py   (Pillow)
"""
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "monte-concellos"
COL = {"e": "#1b8fa6", "c": "#2e6b3a", "f": "#b5762a"}
miles = lambda n: f"{round(n):,}".replace(",", ".")

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
anos = d["anos"]
y0, y1 = str(anos[0]), str(anos[-1])
T, T0 = d["total"][y1], d["total"][y0]
arb = T["e"] + T["c"] + T["f"]
C = d["concellos"]
ar = lambda c, y: sum(c["ha"][y].values())
metade = sum(1 for c in C if ar(c, y1) and c["ha"][y1]["e"] > ar(c, y1) / 2)
pce = round(T["e"] / arb * 100)
h1 = f"O eucalipto xa é máis da metade do monte en <em>{metade} concellos</em>"
dek = (f"Cada árbore do mapa son <b>{d['unidade']} hectáreas</b> de monte. En {y1} Galicia tiña "
       f"<b>{miles(T['e'])} ha de eucalipto</b> ({pce} % do monte arborado), {miles(T['c'])} de piñeiro "
       f"e {miles(T['f'])} de frondosas. Dende {y0} o eucalipto gañou {miles(T['e'] - T0['e'])} ha.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
for k, v in {"H1": h1, "DEK": dek, "TITULO": f"O eucalipto xa é máis da metade do monte en {metade} concellos",
             "U": d["unidade"], "A1": y1, "S05": miles(T["s05"])}.items():
    page = page.replace(f"__{k}__", str(v))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")
shutil.copyfile(HERE / "data" / "datos.json", OUT / "datos.json")

# Miniatura: as árbores de {y1}
xs = [x for c in C for r in c["pol"] for x, _ in r]
ys = [y for c in C for r in c["pol"] for _, y in r]
S, M = 1200, 50
sc = (S - 2 * M) / max(max(xs) - min(xs), max(ys) - min(ys))
ox = (S - (max(xs) - min(xs)) * sc) / 2
P = lambda x, y: (ox + (x - min(xs)) * sc, M + (y - min(ys)) * sc)
im = Image.new("RGB", (S, S), "#f6f1e6")
dr = ImageDraw.Draw(im)
for c in C:
    for r in c["pol"]:
        dr.polygon([P(x, y) for x, y in r], fill="#efe8d8", outline="#d9d0bc")
s = 5.5
for c in C:
    k = 0
    for e in "ecf":
        for _ in range(round(c["ha"][y1][e] / d["unidade"])):
            if k >= len(c["pt"]):
                break
            x, y = P(*c["pt"][k])
            k += 1
            if e == "e":
                dr.ellipse([x - .75 * s, y - 1.6 * s, x + .75 * s, y + 1.6 * s], fill=COL[e])
            elif e == "c":
                dr.polygon([(x, y - 1.45 * s), (x + 1.05 * s, y + 1.3 * s), (x - 1.05 * s, y + 1.3 * s)], fill=COL[e])
            else:
                dr.ellipse([x - 1.05 * s, y - 1.05 * s, x + 1.05 * s, y + 1.05 * s], fill=COL[e])
im.resize((600, 600), Image.LANCZOS).quantize(48).save(OUT / "thumb.png", optimize=True)
print("ok:", OUT, f"metade {metade} · eucalipto {miles(T['e'])} ha ({pce} %)")

#!/usr/bin/env python3
"""Xera v/vacas-persoas/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "vacas-persoas"
A0 = 2005  # en 2002-2003 o rexistro contaba as vacas doutro xeito
DIV = ["#2f4f8f", "#4a6fb5", "#7f98c8", "#b4c1db", "#e7e3d8", "#b9d1b0", "#86b07f", "#58904f", "#3f7d3c", "#24561f"]
STEP = [-3, -2, -1, -.35, .35, 1, 1.6, 2.2, 3]
miles = lambda n: f"{round(n):,}".replace(",", ".")

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
C = d["concellos"]
a1 = str(d["anos"][-1])
a0 = str(A0)
n = sum(1 for c in C if c["vac"].get(a1, 0) > c["pob"][a1])
n0 = sum(1 for c in C if c["vac"].get(a0, 0) > c["pob"][a0])
nug = sum(1 for c in C if sum(c["ug"].values()) > c["pob"]["2020"])
v1, v0 = sum(c["vac"].get(a1, 0) for c in C), sum(c["vac"].get(a0, 0) for c in C)
dek = (f"Eran {n0} en {A0}, e non porque haxa máis vacas: en Galicia hai hoxe un {round((1 - v1 / v0) * 100)} % menos. "
       f"O que baixa máis rápido é a xente. Se ademais das vacas contamos porcos, galiñas e ovellas "
       f"en unidades gandeiras, son <b>{nug} concellos</b> con máis gando ca persoas.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
for k, v in {"DATA": json.dumps(d, ensure_ascii=False, separators=(",", ":")), "N": n, "NUG": nug,
             "DEK": dek, "A0": A0, "A1": a1}.items():
    page = page.replace(f"__{k}__", str(v))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")


def col(r):
    if r <= 0:
        return DIV[4]
    lg, i = math.log2(r), 0
    while i < len(STEP) and lg > STEP[i]:
        i += 1
    return DIV[i]


R = 20
pos = [((i * math.sqrt(3) * R + (math.sqrt(3) * R / 2 if j % 2 else 0)), -j * 1.5 * R) for i, j in (c["h"] for c in C)]
x0, x1 = min(p[0] for p in pos) - R, max(p[0] for p in pos) + R
y0, y1 = min(p[1] for p in pos) - R, max(p[1] for p in pos) + R
sc = 560 / max(x1 - x0, y1 - y0)
ox, oy = (600 - (x1 - x0) * sc) / 2, (600 - (y1 - y0) * sc) / 2
hexes = []
for c, (x, y) in zip(C, pos):
    pts = " ".join(f"{ox + (x - x0 + (R - 1) * math.cos(math.radians(60 * k - 30))) * sc:.1f},"
                   f"{oy + (y - y0 + (R - 1) * math.sin(math.radians(60 * k - 30))) * sc:.1f}" for k in range(6))
    hexes.append(f'<polygon points="{pts}" fill="{col(c["vac"].get(a1, 0) / c["pob"][a1])}"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#f7f4ec"/>{"".join(hexes)}</svg>', encoding="utf-8")
print("ok:", OUT, f"máis vacas: {n} (en {A0}: {n0}) · todo o gando: {nug}")

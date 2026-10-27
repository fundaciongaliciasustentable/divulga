#!/usr/bin/env python3
"""Xera v/galicia-minuto/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "galicia-minuto"
ANO = 31_557_600
COL = {"Saúde e emerxencias": "#6a3d9a", "Viaxes": "#d95f02", "Economía": "#1f78b4", "Campo, monte e mar": "#33a02c", "Auga, enerxía e lixo": "#e7298a"}

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
C = {c["k"]: c for c in d["c"]}
mil = lambda v: f"{v:,.0f}".replace(",", ".")
per_min = lambda k: C[k]["v"] / ANO * 60
dek = (f"Cada minuto, en media, saen das farmacias <b>{mil(per_min('far'))} medicamentos</b>, das granxas "
       f"{mil(per_min('lei'))} litros de leite e das bateas {mil(per_min('mex'))} quilos de mexillón. "
       f"Os contadores empezan a sumar cando abres a páxina.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: un reloxo co anel dividido polos cinco temas e puntos a caer
el = ['<circle cx="300" cy="300" r="200" fill="none" stroke="#efede7" stroke-width="44"/>']
temas = list(COL)
for i, t in enumerate(temas):
    a0, a1 = -math.pi / 2 + i * 2 * math.pi / 5 + 0.04, -math.pi / 2 + (i + 1) * 2 * math.pi / 5 - 0.04
    x0, y0, x1, y1 = 300 + 200 * math.cos(a0), 300 + 200 * math.sin(a0), 300 + 200 * math.cos(a1), 300 + 200 * math.sin(a1)
    el.append(f'<path d="M{x0:.1f},{y0:.1f}A200,200 0 0 1 {x1:.1f},{y1:.1f}" fill="none" stroke="{COL[t]}" stroke-width="44"/>')
el.append('<text x="300" y="338" text-anchor="middle" font-family="Barlow Condensed,Arial Narrow,sans-serif" font-weight="700" font-size="150" fill="#1f2328">1:00</text>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT)

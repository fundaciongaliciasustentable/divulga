#!/usr/bin/env python3
"""Xera v/nucleos-espana/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "nucleos-espana"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
mil = lambda v: f"{v:,.0f}".replace(",", ".")
pc = lambda v: f"{v:.1f}".replace(".", ",")
C = d["ccaa"]
tot = sum(c["es"] for c in C)
G = next(c for c in C if c["c"] == "GA")
seg = sorted(C, key=lambda c: -c["es"])[1]
dens_g = G["es"] / G["km2"] * 100
dens_r = (tot - G["es"]) / (d["km2_es"] - G["km2"]) * 100
dek = (f"Das <b>{mil(tot)}</b> entidades singulares de poboación que o INE conta en España a 1 de xaneiro de {d['ano']}, "
       f"<b>{mil(G['es'])} están en Galicia</b>: o <b>{pc(G['es'] / tot * 100)} %</b>, nun territorio que é o "
       f"{pc(G['km2'] / d['km2_es'] * 100)} % da superficie. Hai {mil(dens_g)} por cada 100 km², fronte a {pc(dens_r)} no resto "
       f"do Estado; a seguinte, {seg['n']}, ten {mil(seg['es'])}.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__ANO__", str(d["ano"])))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: o pictograma en grella común (1 punto = 100 entidades), as dez primeiras comunidades
el = []
filas = sorted(C, key=lambda c: -c["es"])[:10]
K, s = 44, 11.5
y = 150
for c in filas:
    n = round(c["es"] / 100)
    for i in range(n):
        el.append(f'<circle cx="{47 + (i % K) * s:.1f}" cy="{y + (i // K) * s:.1f}" r="4.4" '
                  f'fill="{"#c2185b" if c["c"] == "GA" else "#9aa0a8"}"/>')
    y += (-(-n // K)) * s + 14
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT, f"({(OUT / 'index.html').stat().st_size / 1024:.0f} KB)")
print(dek)

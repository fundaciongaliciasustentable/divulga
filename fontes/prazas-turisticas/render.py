#!/usr/bin/env python3
"""Xera v/prazas-turisticas/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "prazas-turisticas"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
C, G = d["conc"], d["gal"]
f1 = lambda v: f"{v:.1f}".replace(".", ",")
mil = lambda v: f"{v:,.0f}".replace(",", ".")
MES = ["xaneiro", "febreiro", "marzo", "abril", "maio", "xuño", "xullo", "agosto", "setembro", "outubro", "novembro", "decembro"]
mes = f"{MES[int(d['mes'][5:]) - 1]} de {d['mes'][:4]}"
r = lambda c: c["t"] / c["hab"] * 100
o = sorted(C, key=lambda c: -r(c))
top = o[0]
mais = [c for c in o if c["t"] > c["hab"]]
outros = [c["n"] for c in mais[1:]]
vut = G["ti"]["v"] / G["t"] * 100
dek = (f"En {mes}, o rexistro turístico da Xunta sumaba <b>{mil(G['t'])} prazas</b> de aloxamento en Galicia, "
       f"{f1(G['t'] / G['hab'] * 100)} por cada 100 habitantes, e o {vut:.0f} % eran de vivendas de uso turístico. "
       f"O concello máis turístico é <b>{top['n']}</b>: {f1(r(top))} prazas por cada 100 veciños"
       + (f"; {' e '.join(outros)} tamén teñen máis camas para visitantes ca habitantes." if outros else "."))
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__MES__", mes).replace("__MESN__", MES[int(d["mes"][5:]) - 1]).replace("__ANO0__", str(d["anos"][0]))
        .replace("__POB__", str(d["pob_ano"])))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: a dispersión logarítmica coas diagonais
COR = {"h": "#3b6e8f", "a": "#86aecb", "r": "#6b8f47", "c": "#c9a227", "b": "#8b5e3c", "v": "#d9824b"}
X0, X1, Y0, Y1 = math.log10(150), math.log10(300000), math.log10(3), math.log10(60000)
sx = lambda v: 40 + (math.log10(v) - X0) / (X1 - X0) * 520
sy = lambda v: 560 - (math.log10(max(v, 3)) - Y0) / (Y1 - Y0) * 520
el = [f'<line x1="{sx(150):.0f}" y1="{sy(150 * k / 100):.0f}" x2="{sx(300000):.0f}" y2="{sy(300000 * k / 100):.0f}" stroke="#b9b6ad" '
      f'stroke-width="{3 if k == 100 else 1.5}" stroke-dasharray="{"" if k == 100 else "8 6"}"/>' for k in (1, 10, 100)]
for c in C:
    if c["t"]:
        dom = max(c["ti"], key=c["ti"].get)
        el.append(f'<circle cx="{sx(c["hab"]):.0f}" cy="{sy(c["t"]):.0f}" r="7" fill="{COR[dom]}" stroke="#fff"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/><clipPath id="c"><rect x="30" y="30" width="540" height="540"/></clipPath>'
                               f'<g clip-path="url(#c)">{"".join(el)}</g></svg>', encoding="utf-8")
print("ok:", OUT, (OUT / "index.html").stat().st_size // 1024, "KB")
print(dek)

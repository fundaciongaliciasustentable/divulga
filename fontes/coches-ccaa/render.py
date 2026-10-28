#!/usr/bin/env python3
"""Xera v/coches-ccaa/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "coches-ccaa"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
mil = lambda v: f"{v:,.0f}".replace(",", ".")
pc = lambda v: f"{v:.1f}".replace(".", ",")
C, ES = d["ccaa"], d["es"]
G = next(c for c in C if c["c"] == "GA")
MD = next(c for c in C if c["c"] == "MD")
pos = lambda k, rev=True: sorted(C, key=lambda c: -c[k] if rev else c[k]).index(G) + 1
ordn = lambda n: {1: "a cifra máis alta", 2: "a segunda cifra máis alta", 3: "a terceira cifra máis alta"}.get(n, f"a {n}.ª cifra")
dek = (f"Galicia ten <b>{mil(G['tur1000'])} turismos por cada 1.000 habitantes</b>, {ordn(pos('tur1000'))} de {len(C)} "
       f"comunidades e cidades autónomas (España: {mil(ES['tur1000'])}). Pero só o <b>{pc(G['cero_p'])} %</b> do seu parque leva "
       f"a etiqueta CERO, fronte ao {pc(ES['cero_p'])} % de España, e un {pc(G['sin_p'])} % non ten ningunha. "
       f"O que entra vai máis rápido: o {pc(G['cero_m'])} % dos turismos matriculados en {d['ano']} en Galicia eran CERO "
       f"(España: {pc(ES['cero_m'])} %).")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__ANO__", str(d["ano"])).replace("__RENT__", f"o {pc(MD['rent'] / ES['rent'] * 100)} %"))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: o gráfico de pendentes
R = [c for c in C if c["c"] not in ("CE", "ML")]
vmax = max(max(c["cero_p"], c["cero_m"]) for c in R)
sy = lambda v: 540 - v / vmax * 470
el = ['<line x1="130" x2="130" y1="60" y2="545" stroke="#e5e2da" stroke-width="2"/>',
      '<line x1="470" x2="470" y1="60" y2="545" stroke="#e5e2da" stroke-width="2"/>']
for c in sorted(R, key=lambda c: c["c"] == "GA"):
    col, w = ("#c2185b", 7) if c["c"] == "GA" else ("#a9aeb5", 3)
    el.append(f'<line x1="130" x2="470" y1="{sy(c["cero_p"]):.0f}" y2="{sy(c["cero_m"]):.0f}" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/>')
    for x, v in ((130, c["cero_p"]), (470, c["cero_m"])):
        el.append(f'<circle cx="{x}" cy="{sy(v):.0f}" r="{w + 2}" fill="{col}"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT, f"({(OUT / 'index.html').stat().st_size / 1024:.0f} KB)")
print(dek)

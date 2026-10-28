#!/usr/bin/env python3
"""Xera v/vivenda-salario/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "vivenda-salario"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
P, G = d["prov"], d["gal"]
mil = lambda v: f"{v:,.0f}".replace(",", ".")
dec = lambda v, n=1: f"{v:.{n}f}".replace(".", ",")
pos = {p["n"]: i + 1 for i, p in enumerate(P)}
ga = [p for p in P if p["cc"] == "Galicia"]
dek = (f"Unha vivenda de {d['m2']} m² ao valor tasado medio de {d['ano']} custaba en Galicia <b>{dec(G['a'])} anos</b> de salario "
       f"medio ({mil(G['m2'] * d['m2'])} € fronte a {mil(G['s'])} € ao ano). Entre as {len(P)} provincias, vai dos {dec(P[0]['a'])} anos "
       f"de {P[0]['n']} aos {dec(P[-1]['a'])} de {P[-1]['n']}. As galegas: "
       + ", ".join(f"{p['n']} <b>{dec(p['a'])}</b> (posto {pos[p['n']]})" for p in ga[:-1])
       + f" e {ga[-1]['n']} <b>{dec(ga[-1]['a'])}</b> (posto {pos[ga[-1]['n']]} de {len(P)}).")
ogd = f"Anos de salario medio para pagar unha vivenda de {d['m2']} m²: {dec(G['a'])} en Galicia, {dec(P[0]['a'])} en {P[0]['n']}."
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__ANO__", str(d["ano"])).replace("__M2__", str(d["m2"])).replace("__OGD__", ogd))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: oito filas de casas (de máis a menos anos), coas galegas en magenta
CASA = "M1 9.5L10 2l9 7.5V19H1z"
fil = [P[0], P[3], P[10], ga[0], ga[1], P[30], ga[-1], P[-1]]
el = []
for f, p in enumerate(fil):
    y = 48 + f * 66
    cor = "#c2185b" if p["cc"] == "Galicia" else "#b9b4aa"
    el.append(f'<clipPath id="c{f}"><rect x="30" y="{y}" width="{p["a"] * 45:.1f}" height="60"/></clipPath><g clip-path="url(#c{f})">')
    for k in range(math.ceil(p["a"])):
        el.append(f'<path d="{CASA}" fill="{cor}" transform="translate({30 + k * 45},{y + 6}) scale(2.1)"/>')
    el.append("</g>")
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT, (OUT / "index.html").stat().st_size // 1000, "KB")
print(dek)

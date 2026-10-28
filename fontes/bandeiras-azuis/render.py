#!/usr/bin/env python3
"""Xera v/bandeiras-azuis/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "bandeiras-azuis"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
A, C, CC = d["anos"], d["conc"], d["ccaa"]
U = len(A) - 1
d1 = lambda v: f"{v:.1f}".replace(".", ",")
gal = next(c for c in CC if c["n"] == "Galicia")
total = sorted(CC, key=lambda c: -c["b"])
pk = sorted((c for c in CC if c["km"]), key=lambda c: -c["b"] / c["km"])
pt, pk_g = total.index(gal) + 1, pk.index(gal) + 1
con = sorted((c for c in C if c["b"][U]), key=lambda c: -c["b"][U])
top = con[0]
mx = max(d["serie"], key=lambda s: s[1])
ORD = {1: "primeira", 2: "segunda", 3: "terceira", 4: "cuarta", 5: "quinta", 6: "sexta", 7: "sétima", 8: "oitava", 9: "novena", 10: "décima"}

ref = next(c for c in pk if c["km"] > 100)  # a primeira con costa longa (Ceuta e Melilla teñen 20 e 9 km)
dek = (f"En {A[U]} ondean <b>{gal['b']} bandeiras azuis</b> en praias galegas, repartidas en {len(con)} dos 313 concellos; "
       f"{top['n']} encabeza a lista con {top['b'][U]}, seguido de {con[1]['n']} ({con[1]['b'][U]}). Galicia é a "
       f"{ORD.get(pt, pt)} comunidade en número de bandeiras, pero ten tanta costa que, por quilómetro, baixa ao posto "
       f"{pk_g} de {len(pk)}: <b>{d1(gal['b'] / gal['km'] * 100)} por cada 100 km</b>, fronte a "
       f"{d1(ref['b'] / ref['km'] * 100)} na {ref['n']}. O máximo da serie galega foron as {mx[1]} de {mx[0]}.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__ULT__", str(A[U])).replace("__A0__", str(A[0])))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: bandeiriñas azuis na súa posición, sobre o contorno de Galicia
xs = [p[0] for c in C for r in c["pol"] for p in r]
ys = [p[1] for c in C for r in c["pol"] for p in r]
x0, y0, s = min(xs), min(ys), 540 / max(max(xs) - min(xs), max(ys) - min(ys))
T = lambda x, y: (30 + (x - x0) * s, 40 + (y - y0) * s)
el = []
for c in C:
    for r in c["pol"]:
        if len(r) > 8:
            el.append('<path d="M' + "L".join(f"{a:.0f},{b:.0f}" for a, b in (T(*p) for p in r[::3])) + 'Z"/>')
el.insert(0, '<g fill="#ebe8e1" stroke="#ebe8e1" stroke-width="2">')
el.insert(len([1 for x in el if x.endswith('Z"/>')]) + 1, '</g>')
for p in sorted(d["praias"], key=lambda p: p["xy"][1]):
    x, y = T(*p["xy"])
    hl = p["c"] == top["id"]
    el.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x:.0f}" y2="{y - 22:.0f}" stroke="#1f2328" stroke-width="2"/>'
              f'<path d="M{x:.0f},{y - 22:.0f}l15,5l-15,5z" fill="{"#c2185b" if hl else "#1f5fa8"}"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT, (OUT / "index.html").stat().st_size // 1024, "KB")
print(dek)

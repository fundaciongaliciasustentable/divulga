#!/usr/bin/env python3
"""Xera v/galego-concellos/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "galego-concellos"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
pc = lambda v: f"{v * 100:.1f}".replace(".", ",") + " %"
C = d["conc"]
g = d["agr"]["gal"]
v1, v2 = g["s1"] / g["t1"], g["s2"] / g["t2"]
baixan = sum(1 for c in C if c["s2"] / c["t2"] < c["s1"] / c["t1"])
o = sorted(C, key=lambda c: -c["s2"] / c["t2"])
top, fondo = o[0], o[-1]
dek = (f"No Censo de 2011, o <b>{pc(v2)}</b> da poboación galega de 5 e máis anos dicía falar sempre en galego, "
       f"{(v1 - v2) * 100:.0f} puntos menos ca en 2001 ({pc(v1)}). O uso habitual baixou en <b>{baixan} dos 313 concellos</b>, "
       f"e a distancia entre eles é enorme: do {pc(top['s2'] / top['t2'])} de {top['n']} ao {pc(fondo['s2'] / fondo['t2'])} de "
       f"{fondo['n']}. Busca o teu.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: o diagrama de dispersión 2001 → 2011
COR = {"A Coruña": "#2E6B8A", "Lugo": "#6B8F47", "Ourense": "#8B5E3C", "Pontevedra": "#6B4C8A"}
el = ['<line x1="60" y1="540" x2="540" y2="60" stroke="#5f636b" stroke-width="2" stroke-dasharray="8 8"/>']
for c in C:
    x, y = c["s1"] / c["t1"], c["s2"] / c["t2"]
    el.append(f'<circle cx="{60 + x * 480:.0f}" cy="{540 - y * 480:.0f}" r="7" fill="{COR[c["pr"]]}" fill-opacity=".8" stroke="#fff"/>')
el.append(f'<circle cx="{60 + v1 * 480:.0f}" cy="{540 - v2 * 480:.0f}" r="13" fill="none" stroke="#c2185b" stroke-width="5"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT, (OUT / "index.html").stat().st_size // 1024, "KB")
print(dek)

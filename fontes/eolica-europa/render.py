#!/usr/bin/env python3
"""Xera v/eolica-europa/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "eolica-europa"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
miles = lambda v: f"{v:,.0f}".replace(",", ".")
dec = lambda v: f"{v:.1f}".replace(".", ",")
A, P = d["anos"], d["paises"]
L = len(A) - 1
UE = next(p for p in P if p["id"] == "EU27_2020")
G = next(p for p in P if p["id"] == "GZ")
PS = [p for p in P if p is not UE]
hab = lambda p: p["mw"][L] * 1e6 / p["pob"][L]
km = lambda p: (p["mw"][L] - p["mar"][L]) * 1000 / p["km2"]
rh = sorted(PS, key=lambda p: -hab(p))
rk = sorted(PS, key=lambda p: -km(p))
ph, pk = rh.index(G) + 1, rk.index(G) + 1
DK = next(p for p in P if p["id"] == "DK")
ES = next(p for p in P if p["id"] == "ES")
ante = " e ".join(p["n"] for p in rh[:ph - 1])
dek = (f"A finais de {A[L]}, Galicia tiña <b>{miles(G['mw'][L])} MW eólicos</b>: <b>{miles(hab(G))} vatios por habitante</b>, "
       f"{dec(hab(G) / hab(UE))} veces a media da UE e {'máis' if hab(G) > hab(DK) else 'menos'} ca {DK['n']} ({miles(hab(DK))}). "
       f"Sería o posto {ph} de {len(PS)}{', só por detrás de ' + ante if ante else ''}. "
       f"En eólica en terra por km² é a {pk}.ª, con {miles(km(G))} kW, {dec(km(G) / km(ES))} veces a densidade de España.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__ANOS__", f"{A[0]}-{A[L]}").replace("__AREA__", "2024"))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: a nube de puntos do último ano
xm = max(hab(p) for p in PS) * 1.08
ym = max(km(p) for p in PS) * 1.08
el = ['<line x1="60" y1="540" x2="560" y2="540" stroke="#d6d2c8" stroke-width="2"/>',
      '<line x1="60" y1="540" x2="60" y2="50" stroke="#d6d2c8" stroke-width="2"/>']
for p in sorted(PS, key=lambda p: -p["mw"][L]):
    x, y = 60 + hab(p) / xm * 500, 540 - km(p) / ym * 490
    r = max(7, math.sqrt(p["mw"][L]) / 6)
    el.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{max(r, 16) if p is G else r:.1f}" '
              f'fill="{"#c2185b" if p is G else "#9aa1a8"}" stroke="#fbfaf7" stroke-width="2" opacity="{1 if p is G else .8}"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("dek:", dek)
print("ok:", OUT, (OUT / "index.html").stat().st_size // 1024, "KB")

#!/usr/bin/env python3
"""Xera v/castros/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "castros"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
c = lambda v: f"{v:.1f}".replace(".", ",")
mil = lambda v: f"{v:,.0f}".replace(",", ".")
n = len(d["c"])
dek = (f"Antes das aldeas houbo castros: poboados fortificados da Idade do Ferro, nos outeiros e nos cabos. "
       f"OpenStreetMap ten <b>{mil(n)}</b>, e debuxados como estrelas Galicia aparece coma un ceo cheo. "
       f"Cada castro ten outro, en media, a {c(d['nn'])} km, e case a metade do país está a menos de 2 km dun deles. "
       f"E aínda faltan moitos por cartografar.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: as estrelas sobre fondo escuro
k = 560 / max(d["W"], d["H"])
ox, oy = (600 - d["W"] * k) / 2, (600 - d["H"] * k) / 2
random.seed(3)
el = [f'<circle cx="{ox + x * k:.1f}" cy="{oy + y * k:.1f}" r="{random.uniform(1.0, 2.2):.1f}" fill="#ffe6a8" '
      f'fill-opacity="{random.uniform(.6, 1):.2f}"/>' for x, y, *_ in d["c"]]
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#0a0e1a"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT)

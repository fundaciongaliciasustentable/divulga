#!/usr/bin/env python3
"""Xera v/camino-compostela/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "camino-compostela"
miles = lambda n: f"{round(n):,}".replace(",", ".")

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
u = d["serie"][-1]
sar = d["saida"][0]
pS = sar[1] / d["saidaTotal"] * 100
fr = next(c for c in d["camino"] if c[0] == "Francés")
h1 = "Un de cada tres peregrinos sae de <em>Sarria</em>"
dek = (f"En {u[0]} recolleron a Compostela <b>{miles(u[1])} peregrinos</b>, un récord. O camiño Francés leva o "
       f"{round(fr[1] / u[1] * 100)} %, e a maioría dos que chegan por el empezan en Sarria, a uns 115 km: "
       f"pouco máis do mínimo para conseguir a Compostela. Cada liña ten o grosor dos peregrinos que a percorren.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
for k, v in {"DATA": json.dumps(d, ensure_ascii=False, separators=(",", ":")), "H1": h1, "DEK": dek,
             "TITULO": "Un de cada tres peregrinos sae de Sarria",
             "SAIDAP": round(d["saidaTotal"] / u[1] * 100)}.items():
    page = page.replace(f"__{k}__", str(v))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: os camiños e as saídas, sen texto
X0, Y0, X1, Y1 = -9.45, 41.0, -5.2, 43.85
kx = math.cos(math.radians(42.4))
W = 600
H = W * (Y1 - Y0) / ((X1 - X0) * kx)
oy = (600 - H) / 2
px = lambda p: ((p[0] - X0) / (X1 - X0) * W, oy + (Y1 - p[1]) / (Y1 - Y0) * H)
seg = {(tuple(a), tuple(b)): v for a, b, v, _ in d["tramos"]}
mx = max(seg.values())
land = "".join(f'<path d="M{" L".join(f"{x:.1f},{y:.1f}" for x, y in map(px, r))}Z" fill="#e8e1d2" stroke="#d3c9b4"/>' for r in d["contorno"])
lines = "".join(f'<line x1="{px(a)[0]:.1f}" y1="{px(a)[1]:.1f}" x2="{px(b)[0]:.1f}" y2="{px(b)[1]:.1f}" stroke="#2a6bb5" '
                f'stroke-opacity=".85" stroke-width="{2 + v / mx * 34:.1f}" stroke-linecap="round"/>' for (a, b), v in sorted(seg.items(), key=lambda kv: kv[1]))
circ = "".join(f'<circle cx="{px(p)[0]:.1f}" cy="{px(p)[1]:.1f}" r="{math.sqrt(v / sar[1]) * 30:.1f}" fill="#b97a00" fill-opacity=".8" stroke="#f4f0e7" stroke-width="2"/>'
               for n, v, p in d["saida"])
(OUT / "thumb.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<clipPath id="c"><rect width="600" height="600"/></clipPath><rect width="600" height="600" fill="#f4f0e7"/>'
                               f'<g clip-path="url(#c)">{land}{lines}{circ}</g></svg>', encoding="utf-8")
print("ok:", OUT, f"Sarria {pS:.1f} %")

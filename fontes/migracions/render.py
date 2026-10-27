#!/usr/bin/env python3
"""Xera v/migracions/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "migracions"
miles = lambda n: f"{round(n):,}".replace(",", ".")

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
T = d["total"]
r = T["ei"] / T["ee"]
P = sorted(d["paises"], key=lambda p: -p["i"])
h1 = ('Por cada persoa que <span class="o">marcha</span> ao estranxeiro, '
      f'<span class="i">chegan {"case tres" if 2.5 <= r < 3 else f"{r:.1f}".replace(".", ",")}</span>')
dek = (f"En {d['ano']} mudáronse a Galicia desde o estranxeiro <b>{miles(T['ei'])} persoas</b> e marcharon {miles(T['ee'])}. "
       f"As que máis, de {P[0]['n']} e {P[1]['n']}. Co resto de España tamén hai saldo a favor, pero moito máis pequeno: "
       f"{miles(T['si'])} chegadas e {miles(T['se'])} saídas. Cada arco ten o grosor das persoas que fixeron ese camiño.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
for k, v in {"DATA": json.dumps(d, ensure_ascii=False, separators=(",", ":")), "H1": h1, "DEK": dek, "ANO": d["ano"],
             "TITULO": "Por cada persoa que marcha de Galicia ao estranxeiro, chegan case tres"}.items():
    page = page.replace(f"__{k}__", str(v))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: o Atlántico cos arcos de chegada
gx, gy = d["galicia"]
x0, y0, w = 150, 60, 380  # recorte arredor de América e Europa
sc = 600 / w
tx = lambda x: (x - x0) * sc
ty = lambda y: (y - y0) * sc
mx = max(p["i"] for p in d["paises"])
arcs = []
for p in sorted(d["paises"], key=lambda p: p["i"]):
    if not p.get("xy") or not p["i"]:
        continue
    (x1, y1), (x2, y2) = p["xy"], (gx, gy)
    L = math.hypot(x2 - x1, y2 - y1) or 1
    k = .25 * (1 if x1 < x2 else -1)
    cx, cy = (x1 + x2) / 2 - (y2 - y1) * k, (y1 + y2) / 2 + (x2 - x1) * k
    arcs.append(f'<path d="M{tx(x1):.1f},{ty(y1):.1f}Q{tx(cx):.1f},{ty(cy):.1f} {tx(x2):.1f},{ty(y2):.1f}" fill="none" '
                f'stroke="#1a8a73" stroke-opacity=".8" stroke-linecap="round" stroke-width="{max(1.5, p["i"] / mx * 22):.1f}"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#f6f5f1"/><g transform="translate({-x0 * sc:.1f},{-y0 * sc:.1f}) scale({sc:.3f})">'
                               f'<path d="{d["mundo"]}" fill="#e6e3da" stroke="#d2cdbf" stroke-width=".6"/></g>{"".join(arcs)}'
                               f'<circle cx="{tx(gx):.1f}" cy="{ty(gy):.1f}" r="8" fill="#1f2328" stroke="#fff" stroke-width="3"/></svg>', encoding="utf-8")
print("ok:", OUT, f"ratio {r:.2f}")

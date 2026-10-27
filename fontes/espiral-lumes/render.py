#!/usr/bin/env python3
"""Xera v/espiral-lumes/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
import math
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "espiral-lumes"
MES = ["xaneiro", "febreiro", "marzo", "abril", "maio", "xuño", "xullo", "agosto",
       "setembro", "outubro", "novembro", "decembro"]
RAMP = [(10, "#b8461c"), (100, "#d9631f"), (1000, "#ef8a2c"), (10000, "#f7ac4c"), (math.inf, "#fcd08a")]

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
u = date.fromisoformat(d["ultimoEFFIS"])
c16 = next(c for c in d["comp"] if c["y"] == 2016)
miles = lambda n: f"{n:,}".replace(",", ".")

page = ((HERE / "viz.tpl.html").read_text(encoding="utf-8")
        .replace("__DATA__", json.dumps({"anos": d["anos"]}, ensure_ascii=False, separators=(",", ":")))
        .replace("__ANOFIN__", str(d["anos"][-1]["y"]))
        .replace("__ULTIMO__", f"{u.day} de {MES[u.month - 1]} de {u.year}")
        .replace("__C16E__", miles(c16["egif"]))
        .replace("__C16S__", miles(c16["effis"])))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: a mesma espiral, sen texto
N, R0 = len(d["anos"]), 40
S = (280 - R0) / N


def pos(i, doy):
    f = doy / 365.25
    r, a = R0 + (i + f) * S, f * 2 * math.pi
    return r * math.sin(a), -r * math.cos(a)


track = "".join(
    '<path d="' + "".join(("L" if k else "M") + "%.1f,%.1f" % pos(i, min(k * 6, 365.25)) for k in range(62)) + '"/>'
    for i in range(N))
dots = []
# Miniatura: só os lumes >=200 ha (o 19% dos rexistros) abonda para debuxar o
# mesmo patrón de anos malos — mantén a peza interactiva (JS, __DATA__ arriba)
# a resolución completa (>=5 ha) e deixa o thumb.svg lixeiro para a portada.
for i, a in enumerate(d["anos"]):
    for doy, ha in sorted((p for p in a["d"] if p[1] >= 200), key=lambda p: -p[1]):
        x, y = pos(i, doy)
        dots.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{max(.5, .175 * math.sqrt(ha)):.1f}" '
                    f'fill="{next(c for t, c in RAMP if ha < t)}"/>')
thumb = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-300 -300 600 600" width="600" height="600">'
         f'<rect x="-300" y="-300" width="600" height="600" fill="#191514"/>'
         f'<g fill="none" stroke="#3b302c" stroke-width=".8">{track}</g>'
         f'<g fill-opacity=".82" style="mix-blend-mode:screen">{"".join(dots)}</g></svg>')
(OUT / "thumb.svg").write_text(thumb, encoding="utf-8")
print("ok:", OUT / "index.html", f"({len(page) // 1024} KB)", "+ thumb.svg", f"({len(thumb) // 1024} KB)")

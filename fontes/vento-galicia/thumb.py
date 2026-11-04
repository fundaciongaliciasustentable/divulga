#!/usr/bin/env python3
"""Miniatura v/vento-galicia/thumb.svg (600×600, sen texto): silueta de Galicia, a grella
de vento (Global Wind Atlas) e os aeroxeradores agrupados en celas de 0,02°.
Usa as capas xa xeradas por prep.py. Uso: python -I thumb.py (con shapely)"""
import json
import math
from collections import Counter
from pathlib import Path

from shapely.geometry import shape
from shapely.ops import polygonize, unary_union

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
V = RAIZ / "v" / "vento-galicia"
cont = json.loads((RAIZ / "assets/terreo/galicia-contorno.geojson").read_text())
gal = unary_union(list(polygonize(unary_union([shape(f["geometry"]) for f in cont["features"]])))).simplify(0.01)

X0, X1, Y0, Y1 = -9.35, -6.70, 41.78, 43.82
K = math.cos(math.radians(42.8))
esc = 520 / max((X1 - X0) * K, Y1 - Y0)
ox = (600 - (X1 - X0) * K * esc) / 2
oy = (600 - (Y1 - Y0) * esc) / 2


def px(lon, lat):
    return ox + (lon - X0) * K * esc, oy + (Y1 - lat) * esc


def camino(g):
    polys = g.geoms if g.geom_type == "MultiPolygon" else [g]
    d = []
    for pol in polys:
        if pol.area < 0.002:
            continue
        pts = [px(*c) for c in pol.exterior.coords]
        d.append("M" + "L".join(f"{x:.0f},{y:.0f}" for x, y in pts) + "Z")
    return "".join(d)


CORES = [(4, "#26364a"), (5, "#2f5f7a"), (6, "#3f8f9a"), (7, "#77c1a8"), (8, "#c8e6a0"), (9, "#f6f2b5")]


def cor(v):
    for lim, c in reversed(CORES):
        if v >= lim:
            return c
    return CORES[0][1]


partes = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">',
          '<rect width="600" height="600" fill="#0e1012"/>',
          f'<path d="{camino(gal)}" fill="#161c1f" stroke="#f2f0e8" stroke-opacity=".35" stroke-width="1"/>',
          '<g fill-opacity=".45">']
vento = json.loads((V / "capas/vento.geojson").read_text())
for f in vento["features"]:
    c = cor(f["properties"]["v"])
    pts = f["geometry"]["coordinates"][::3]   # un terzo da grella abonda
    partes.append(f'<g fill="{c}">' + "".join(
        f'<circle cx="{x:.0f}" cy="{y:.0f}" r="3"/>' for x, y in (px(*p) for p in pts)) + "</g>")
partes.append("</g>")
aero = json.loads((V / "capas/aeroxeradores.geojson").read_text())
celas = Counter()
for f in aero["features"]:
    for lon, lat in f["geometry"]["coordinates"]:
        celas[(round(lon / 0.02), round(lat / 0.02))] += 1
partes.append('<g fill="#f6e7a8">')
for (i, j), n in celas.items():
    x, y = px(i * 0.02, j * 0.02)
    partes.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{1.0 + math.sqrt(n) * 0.55:.1f}"/>')
partes.append("</g></svg>")
(V / "thumb.svg").write_text("".join(partes), encoding="utf-8")
print(V / "thumb.svg", (V / "thumb.svg").stat().st_size // 1024, "KB")

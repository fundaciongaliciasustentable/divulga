#!/usr/bin/env python3
"""Miniatura v/rural-sen-transporte/thumb.svg (600×600, fondo escuro, sen texto):
contorno de Galicia, rede de bus do mércores (tramos con 4 viaxes ou máis) e tren.
Le as capas xa xeradas por prep.py. Uso (precisa shapely): python3 thumb.py"""
import json
import math
from pathlib import Path

from shapely.geometry import LineString

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
V = RAIZ / "v" / "rural-sen-transporte"
W, M = 600, 34
O, E, S, N = -9.35, -6.7, 41.8, 43.82
K = math.cos(math.radians(42.8))
esc = (W - 2 * M) / max((E - O) * K, N - S)
dx = (W - (E - O) * K * esc) / 2
dy = (W - (N - S) * esc) / 2


def px(c):
    return ((c[0] - O) * K * esc + dx, (N - c[1]) * esc + dy)


def liñas(g):
    cs = g["coordinates"]
    if g["type"] in ("LineString",):
        cs = [cs]
    elif g["type"] in ("Polygon",):
        pass
    elif g["type"] == "MultiPolygon":
        cs = [r for p in cs for r in p]
    return cs


def d(cs, tol=1.0):
    """Path SVG en píxeles enteiros, simplificado (Douglas-Peucker) para que pese pouco."""
    out = []
    for l in cs:
        if len(l) < 2:
            continue
        g = LineString([px(c) for c in l]).simplify(tol)
        pts = []
        for x, y in g.coords:
            p = (round(x), round(y))
            if not pts or pts[-1] != p:
                pts.append(p)
        if len(pts) > 1:   # primeiro punto absoluto e o resto relativo: menos bytes
            rel = " ".join(f"{b[0] - a[0]} {b[1] - a[1]}" for a, b in zip(pts, pts[1:]))
            out.append(f"M{pts[0][0]} {pts[0][1]}l{rel}")
    return "".join(out)


cont = json.load(open(RAIZ / "assets" / "terreo" / "galicia-contorno.geojson"))["features"]
contorno = "".join(d(liñas(f["geometry"]) if f["geometry"]["type"] != "MultiLineString"
                     else f["geometry"]["coordinates"]) for f in cont)
bus = json.load(open(V / "capas" / "bus.geojson"))["features"]
GROSO = {1: 0.7, 2: 1.2, 3: 2.0, 4: 3.0}
capas_bus = []
for f in bus:
    c = f["properties"]["c"]
    if c == 0:
        continue
    g = f["geometry"]
    cs = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
    capas_bus.append(f'<path d="{d(cs)}" stroke-width="{GROSO[c]}"/>')
tren = json.load(open(V / "capas" / "tren.geojson"))["features"]
tr = d([f["geometry"]["coordinates"] for f in tren])

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {W}" width="{W}" height="{W}">
<rect width="{W}" height="{W}" fill="#0e1012"/>
<path d="{contorno}" fill="none" stroke="#f2f0e8" stroke-opacity=".35" stroke-width="1.2"/>
<g fill="none" stroke="#f2b134" stroke-opacity=".8" stroke-linecap="round" stroke-linejoin="round">{"".join(capas_bus)}</g>
<path d="{tr}" fill="none" stroke="#7fd3f0" stroke-width="2.6" stroke-linecap="round"/>
</svg>'''
(V / "thumb.svg").write_text(svg, encoding="utf-8")
print(V / "thumb.svg", round(len(svg.encode()) / 1024), "KB")

#!/usr/bin/env python3
"""Miniatura v/costa-morte-courel/thumb.svg (600×600, sen texto): liñas de perfil do relevo de
Galicia sacadas do MDT de 25 m do IGN, o contorno e a ruta do voo coas súas once paradas.
Uso (precisa numpy, tifffile e shapely):  python3 thumb.py
"""
import json
import math
from pathlib import Path

import numpy as np
import tifffile
from shapely.geometry import Point, shape
from shapely.ops import polygonize, unary_union
from shapely.prepared import prep

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
MDT = AQUI.parent / "terreo" / "data" / "raw"
contorno = json.loads((RAIZ / "assets" / "terreo" / "galicia-contorno.geojson").read_text())
liñas = unary_union([shape(f["geometry"]) for f in contorno["features"]])
galicia = max(polygonize(liñas), key=lambda p: p.area)
dentro = prep(galicia.buffer(0.01))

W = 600
LON0, LON1, LAT0, LAT1 = -9.4, -6.65, 41.75, 43.85
KX = math.cos(math.radians(42.8))
ESC = (W - 70) / max((LON1 - LON0) * KX, LAT1 - LAT0)
OX = (W - (LON1 - LON0) * KX * ESC) / 2
OY = (W - (LAT1 - LAT0) * ESC) / 2 + 20


def xy(lon, lat):
    return OX + (lon - LON0) * KX * ESC, OY + (LAT1 - lat) * ESC


cache = {}


def altura(lon, lat):
    lo, la = math.floor(lon * 2) / 2, math.floor((lat - 0.25) * 2) / 2 + 0.25
    f = MDT / f"mdt25_+{la:.2f}_{lo:.2f}.tif"
    if f not in cache:
        cache[f] = tifffile.imread(f) if f.exists() else None
    a = cache[f]
    if a is None:
        return 0
    n = a.shape[0]
    r, c = int((la + 0.5 - lat) / 0.5 * n), int((lon - lo) / 0.5 * n)
    return max(0, int(a[min(r, n - 1), min(c, n - 1)]))


partes = []
NF = 40
for k in range(NF):
    lat = LAT1 - 0.03 - k * (LAT1 - LAT0 - 0.06) / (NF - 1)
    tramo = []
    for lon in np.arange(LON0, LON1, 0.015):
        if dentro.contains(Point(lon, lat)):
            x, y = xy(lon, lat)
            tramo.append(f"{x:.0f},{y - altura(lon, lat) * 0.042:.0f}")
        elif tramo:
            if len(tramo) > 2:
                partes.append(tramo)
            tramo = []
    if len(tramo) > 2:
        partes.append(tramo)
perfil = "".join(f'<polyline points="{" ".join(t)}"/>' for t in partes)

cont = []
for g in getattr(liñas, "geoms", [liñas]):
    s = g.simplify(0.01)
    pts = " ".join(f"{x:.0f},{y:.0f}" for x, y in (xy(*c) for c in s.coords))
    if len(s.coords) > 3:
        cont.append(f'<polyline points="{pts}"/>')

paradas = json.loads((AQUI / "datos.json").read_text())["paradas"][1:-1]
ruta = [xy(*p["camara"]["centro"]) for p in paradas]
fin = max(range(len(ruta)), key=lambda i: ruta[i][0])
camiño = " ".join(f"{x:.0f},{y:.0f}" for x, y in ruta)
puntos = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{9 if i in (0, fin) else 6}"/>'
                 for i, (x, y) in enumerate(ruta))

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {W}" width="{W}" height="{W}">
<rect width="{W}" height="{W}" fill="#0e1012"/>
<g fill="none" stroke="#7a8a6a" stroke-width="1.3" stroke-opacity=".75" stroke-linejoin="round">{perfil}</g>
<g fill="none" stroke="#f2f0e8" stroke-width="1.2" stroke-opacity=".6">{"".join(cont)}</g>
<polyline points="{camiño}" fill="none" stroke="#c9a86a" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"/>
<g fill="#c9a86a" stroke="#0e1012" stroke-width="2.5">{puntos}</g>
</svg>'''
dest = RAIZ / "v" / "costa-morte-courel" / "thumb.svg"
dest.write_text(svg, encoding="utf-8")
print(dest, f"{len(svg.encode()) / 1024:.0f} KB")

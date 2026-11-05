#!/usr/bin/env python3
"""Miniatura v/rios-fora-do-leito/thumb.svg (600×600, fondo escuro, sen texto).

Contorno de Galicia (assets/terreo/galicia-contorno.geojson), rede fluvial principal
(capas/rede.geojson) e os ríos de Galicia-Costa acesos pola crecida de outubro
(capas/rios-crecida.geojson). Uso: python3 thumb.py (despois de prep.py)
"""
import json
import math
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
V = RAIZ / "v" / "rios-fora-do-leito"
W = 600
LON0, LON1, LAT0, LAT1 = -9.35, -6.7, 41.8, 43.82
KX = math.cos(math.radians(42.8))
esc = (W - 60) / max((LON1 - LON0) * KX, LAT1 - LAT0)
ox = (W - (LON1 - LON0) * KX * esc) / 2
oy = (W - (LAT1 - LAT0) * esc) / 2


def xy(c):
    return ((c[0] - LON0) * KX * esc + ox, (LAT1 - c[1]) * esc + oy)


def liñas(g):
    if g["type"] == "LineString":
        return [g["coordinates"]]
    if g["type"] == "MultiLineString":
        return g["coordinates"]
    return []


def camiño(lineas, paso=1.6):
    d = []
    for ln in lineas:
        pts, ult = [], None
        for c in ln:
            p = xy(c)
            if ult is None or math.dist(p, ult) >= paso:
                pts.append(p)
                ult = p
        if len(pts) > 1:
            d.append("M" + "L".join(f"{x:.0f},{y:.0f}" for x, y in pts))
    return "".join(d)


def cor(r):
    if r is None or r < 2:
        return None
    return "#f2c14e" if r < 4 else "#f08a3c" if r < 8 else "#e4572e"


contorno = json.loads((RAIZ / "assets" / "terreo" / "galicia-contorno.geojson").read_text())
rede = json.loads((V / "capas" / "rede.geojson").read_text())
crec = json.loads((V / "capas" / "rios-crecida.geojson").read_text())

partes = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {W}" width="{W}" height="{W}">',
          f'<rect width="{W}" height="{W}" fill="#0e1012"/>']
c = camiño([l for f in contorno["features"] for l in liñas(f["geometry"])], 2)
partes.append(f'<path d="{c}" fill="none" stroke="#f2f0e8" stroke-opacity=".35" stroke-width="1.2"/>')
for f in rede["features"]:
    p = f["properties"]["p"]
    d = camiño(liñas(f["geometry"]), 2.5 if p == 0 else 1.6)
    partes.append(f'<path d="{d}" fill="none" stroke="#6fa8c9" stroke-opacity="{0.85 if p else 0.35}" '
                  f'stroke-width="{2 if p else 0.8}" stroke-linecap="round" stroke-linejoin="round"/>')
for f in sorted(crec["features"], key=lambda f: f["properties"]["r"] or 0):
    k = cor(f["properties"]["r"])
    if k:
        d = camiño(liñas(f["geometry"]), 1.6)
        partes.append(f'<path d="{d}" fill="none" stroke="{k}" stroke-width="2.6" '
                      f'stroke-linecap="round" stroke-linejoin="round"/>')
partes.append("</svg>")
out = V / "thumb.svg"
out.write_text("".join(partes), encoding="utf-8")
print(out, f"{out.stat().st_size / 1024:.0f} KB")

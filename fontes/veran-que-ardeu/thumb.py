#!/usr/bin/env python3
"""Precisa shapely. Debuxa v/veran-que-ardeu/thumb.svg (600×600, sen texto): contorno de Galicia,
áreas queimadas de 2025 e focos de agosto, desde as capas de prep.py."""
import json
import math
from pathlib import Path

from shapely.geometry import mapping, shape

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
V = RAIZ / "v" / "veran-que-ardeu"
W, M = 600, 40
O, S, E, N = -9.35, 41.8, -6.7, 43.8
K = math.cos(math.radians(42.8))
esc = (W - 2 * M) / max((E - O) * K, N - S)
dx = (W - (E - O) * K * esc) / 2
dy = (W - (N - S) * esc) / 2


def xy(p):
    return f"{dx + (p[0] - O) * K * esc:.0f},{dy + (N - p[1]) * esc:.0f}"


def linea(a):
    """Puntos en píxeles enteiros, sen repetir o anterior (aforra bytes)."""
    out = []
    for p in a:
        q = xy(p)
        if not out or out[-1] != q:
            out.append(q)
    return out


def aneis(g):
    t = g["type"]
    if t in ("LineString",):
        return [g["coordinates"]]
    if t in ("MultiLineString", "Polygon"):
        return g["coordinates"]
    if t == "MultiPolygon":
        return [a for pol in g["coordinates"] for a in pol]
    return []


def simple(g, tol):
    return mapping(shape(g).simplify(tol, preserve_topology=True))


def camino(g, pechar):
    return "".join("M" + "L".join(linea(a)) + ("Z" if pechar else "") for a in aneis(g) if len(linea(a)) > 2)


contorno = json.loads((RAIZ / "assets" / "terreo" / "galicia-contorno.geojson").read_text())
lumes = json.loads((V / "capas" / "lumes.geojson").read_text())
focos = json.loads((V / "capas" / "focos.geojson").read_text())
cor = lambda d: "#ffd166" if d < 13 else ("#ff4d1f" if d < 18 else "#e0568a")

partes = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {W}" width="{W}" height="{W}">',
          f'<rect width="{W}" height="{W}" fill="#0e1012"/>']
partes.append('<path fill="#1c2420" stroke="#f2f0e8" stroke-opacity=".45" stroke-width="1.2" d="'
              + "".join(camino(simple(f["geometry"], 0.004), False) for f in contorno["features"]) + '"/>')
partes.append('<path fill="#ff7a45" fill-opacity=".55" stroke="#ffb08a" stroke-width=".8" d="'
              + "".join(camino(simple(f["geometry"], 0.006), True) for f in lumes["features"]) + '"/>')
for f in focos["features"]:
    pts = sorted({",".join(str(int(v) // 4 * 4) for v in xy(p).split(",")) for p in f["geometry"]["coordinates"]})  # un punto por cada 4 px
    # cada foco é un trazo de lonxitude 0 con remate redondo: un círculo en poucos bytes
    partes.append(f'<path stroke="{cor(f["properties"]["d"])}" stroke-opacity=".9" stroke-width="4.2" '
                  f'stroke-linecap="round" d="' + "".join(f"M{q}h0" for q in pts) + '"/>')
partes.append("</svg>")
(V / "thumb.svg").write_text("".join(partes), encoding="utf-8")
print(V / "thumb.svg", (V / "thumb.svg").stat().st_size // 1024, "KB")

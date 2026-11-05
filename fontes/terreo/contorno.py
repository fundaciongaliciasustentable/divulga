#!/usr/bin/env python3
"""Xera assets/terreo/galicia-contorno.geojson (liña de Galicia) e galicia-fora.geojson
(máscara: un rectángulo amplo co oco de Galicia, para escurecer o que queda fóra).

Fonte: contorno do IGN (WFS INSPIRE unidades administrativas, CC BY 4.0) gardado en
mapasgs/pipeline/satelite/galicia-ign.geojson. Simplifícase a ~0,0015° (≈150 m).
Uso: python3 contorno.py [ruta a galicia-ign.geojson]
"""
import json
import sys
from pathlib import Path

ORIXE = Path(sys.argv[1] if len(sys.argv) > 1 else
             Path.home() / "Proxectos/mapasgs/pipeline/satelite/galicia-ign.geojson")
DEST = Path(__file__).resolve().parent.parent.parent / "assets" / "terreo"
TOL = 0.0015


def dp(pts, tol):
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    pila = [(0, len(pts) - 1)]
    while pila:
        a, b = pila.pop()
        (x1, y1), (x2, y2) = pts[a], pts[b]
        dx, dy = x2 - x1, y2 - y1
        n = (dx * dx + dy * dy) ** 0.5 or 1e-12
        mx, mi = -1, -1
        for i in range(a + 1, b):
            d = abs(dy * pts[i][0] - dx * pts[i][1] + x2 * y1 - y2 * x1) / n
            if d > mx:
                mx, mi = d, i
        if mx > tol:
            keep[mi] = True
            pila += [(a, mi), (mi, b)]
    return [p for p, k in zip(pts, keep) if k]


g = json.loads(ORIXE.read_text(encoding="utf-8"))
geom = g["features"][0]["geometry"] if "features" in g else g["geometry"]
aneis = []
for pol in geom["coordinates"]:
    ani = pol[0]
    # anel pechado: pártese no punto máis afastado do inicio para que DP non colapse
    k = max(range(len(ani)), key=lambda i: (ani[i][0] - ani[0][0]) ** 2 + (ani[i][1] - ani[0][1]) ** 2)
    simp = dp(ani[:k + 1], TOL)[:-1] + dp(ani[k:], TOL)
    ext = [[round(x, 4), round(y, 4)] for x, y in simp]
    if len(ext) >= 8:   # fóra illotes minúsculos
        aneis.append(ext)
DEST.mkdir(parents=True, exist_ok=True)
attr = "Contorno: © Instituto Geográfico Nacional, CC BY 4.0"
(DEST / "galicia-contorno.geojson").write_text(json.dumps({
    "type": "FeatureCollection", "attribution": attr,
    "features": [{"type": "Feature", "properties": {"nome": "Galicia"},
                  "geometry": {"type": "MultiLineString", "coordinates": aneis}}]},
    separators=(",", ":")), encoding="utf-8")
marco = [[-12, 39], [-3, 39], [-3, 46], [-12, 46], [-12, 39]]
(DEST / "galicia-fora.geojson").write_text(json.dumps({
    "type": "FeatureCollection", "attribution": attr,
    "features": [{"type": "Feature", "properties": {},
                  "geometry": {"type": "Polygon", "coordinates": [marco] + [a[::-1] for a in aneis]}}]},
    separators=(",", ":")), encoding="utf-8")
for f in ("galicia-contorno.geojson", "galicia-fora.geojson"):
    print(f, (DEST / f).stat().st_size // 1024, "KB")

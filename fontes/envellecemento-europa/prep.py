#!/usr/bin/env python3
"""Idade mediana da poboación nas rexións NUTS 3 da UE, con xeometría simplificada → data/datos.json

Fontes (gardadas en data/raw/):
  - Eurostat, demo_r_pjanind3 «Population structure indicators by NUTS 3 region», indicador MEDAGEPOP
    (idade mediana), dende 2014. Inclúe tamén os niveis NUTS 2 e de país:
    https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_r_pjanind3?format=JSON&lang=EN&indic_de=MEDAGEPOP&sinceTimePeriod=2014
  - Eurostat, demo_pjanind, idade mediana da UE-27 (EU27_2020):
    https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_pjanind?format=JSON&lang=EN&indic_de=MEDAGEPOP&geo=EU27_2020&sinceTimePeriod=2014
  - Eurostat GISCO, NUTS 2024, escala 1:20 millóns, proxección ETRS89-LAEA (EPSG:3035), nivel 3:
    https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_20M_2024_3035_LEVL_3.geojson
    e nivel 0 (contornos de país, para o trazo):
    https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_20M_2024_3035_LEVL_0.geojson

A xeometría recórtase á Europa continental (as rexións ultraperiféricas e Chipre quedan fóra do mapa
pero si no ranking), simplifícase (Douglas-Peucker, 3 km) e gárdase en quilómetros enteiros como
camiños SVG relativos.
"""
import json
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
URLS = {
    "medage.json": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_r_pjanind3?format=JSON&lang=EN&indic_de=MEDAGEPOP&sinceTimePeriod=2014",
    "medage_ue.json": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_pjanind?format=JSON&lang=EN&indic_de=MEDAGEPOP&geo=EU27_2020&sinceTimePeriod=2014",
    "nuts3_20m.geojson": "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_20M_2024_3035_LEVL_3.geojson",
    "nuts0_20m.geojson": "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_20M_2024_3035_LEVL_0.geojson",
}
EU = "AT BE BG CY CZ DE DK EE EL ES FI FR HR HU IE IT LT LU LV MT NL PL PT RO SE SI SK".split()
PAIS = {"AT": "Austria", "BE": "Bélxica", "BG": "Bulgaria", "CY": "Chipre", "CZ": "Chequia", "DE": "Alemaña", "DK": "Dinamarca",
        "EE": "Estonia", "EL": "Grecia", "ES": "España", "FI": "Finlandia", "FR": "Francia", "HR": "Croacia", "HU": "Hungría",
        "IE": "Irlanda", "IT": "Italia", "LT": "Lituania", "LU": "Luxemburgo", "LV": "Letonia", "MT": "Malta", "NL": "Países Baixos",
        "PL": "Polonia", "PT": "Portugal", "RO": "Romanía", "SE": "Suecia", "SI": "Eslovenia", "SK": "Eslovaquia"}
# Caixa do mapa en metros EPSG:3035 (x0, y0, x1, y1)
BOX = (2500000, 1380000, 6000000, 5450000)
TOL = 3000  # m

RAW.mkdir(parents=True, exist_ok=True)
for f, u in URLS.items():
    if not (RAW / f).exists():
        (RAW / f).write_bytes(urlopen(Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=300).read())
        print("descargado", f)

# --- Datos
d = json.loads((RAW / "medage.json").read_text(encoding="utf-8"))
g = d["dimension"]["geo"]["category"]
T = d["dimension"]["time"]["category"]["index"]
nT, v = len(T), d["value"]
val = lambda geo, y: v.get(str(g["index"][geo] * nT + T[y]))
anos = sorted(T)
ok = lambda x, n: len(x) == n and x[:2] in EU and not x.endswith("Z" * (n - 2))
ult = max(y for y in anos if sum(1 for x in g["index"] if ok(x, 5) and val(x, y) is not None) > 1000)
a0 = min(y for y in anos if all(val(x, y) is not None for x in ("ES111", "ES112", "ES113", "ES114")))
n3 = {x: [g["label"][x], val(x, ult), val(x, a0)] for x in g["index"] if ok(x, 5) and val(x, ult) is not None}
n2 = {x: [g["label"][x], val(x, ult)] for x in g["index"] if ok(x, 4) and val(x, ult) is not None}
paises = {x: val(x, ult) for x in EU}
ue_js = json.loads((RAW / "medage_ue.json").read_text(encoding="utf-8"))
ue = ue_js["value"].get(str(ue_js["dimension"]["time"]["category"]["index"][ult]))


# --- Xeometría
def dp(pts, tol):
    """Douglas-Peucker iterativo. Os aneis pechados pártense polo punto máis afastado do inicial."""
    if len(pts) < 4:
        return pts
    if pts[0] == pts[-1]:
        x0, y0 = pts[0]
        k = max(range(len(pts)), key=lambda i: (pts[i][0] - x0) ** 2 + (pts[i][1] - y0) ** 2)
        return dp(pts[:k + 1], tol)[:-1] + dp(pts[k:], tol)
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    pila = [(0, len(pts) - 1)]
    while pila:
        a, b = pila.pop()
        (x1, y1), (x2, y2) = pts[a], pts[b]
        dx, dy = x2 - x1, y2 - y1
        L = (dx * dx + dy * dy) ** .5 or 1e-9
        mx, mi = -1, -1
        for i in range(a + 1, b):
            x0, y0 = pts[i]
            dd = abs(dy * x0 - dx * y0 + x2 * y1 - y2 * x1) / L
            if dd > mx:
                mx, mi = dd, i
        if mx > tol:
            keep[mi] = True
            pila += [(a, mi), (mi, b)]
    return [p for p, k in zip(pts, keep) if k]


def area(r):
    return abs(sum(r[i][0] * r[i - 1][1] - r[i - 1][0] * r[i][1] for i in range(len(r)))) / 2


def camino(geom, tol, amin):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    out, rings = [], []
    for poly in polys:
        for k, ring in enumerate(poly):
            if not any(BOX[0] <= x <= BOX[2] and BOX[1] <= y <= BOX[3] for x, y in ring):
                continue
            rings.append((area(ring), ring))
    if not rings:
        return None
    big = max(a for a, _ in rings)
    for a, ring in rings:
        if a < amin and a < big:
            continue
        r = dp(ring, tol)
        q = []
        for x, y in r:
            p = (round((x - BOX[0]) / 1000), round((BOX[3] - y) / 1000))
            if not q or p != q[-1]:
                q.append(p)
        if len(q) < 3:
            continue
        s = f"M{q[0][0]} {q[0][1]}" + "l" + " ".join(f"{q[i][0] - q[i - 1][0]} {q[i][1] - q[i - 1][1]}" for i in range(1, len(q))) + "z"
        out.append(s)
    return "".join(out) or None


geo3 = json.loads((RAW / "nuts3_20m.geojson").read_text(encoding="utf-8"))
shapes, fondo = {}, []
for f in geo3["features"]:
    p = f["properties"]
    c = p["NUTS_ID"]
    if c in n3:
        s = camino(f["geometry"], TOL, 6e6)
        if s:
            shapes[c] = s
    elif p["CNTR_CODE"] not in EU:
        s = camino(f["geometry"], TOL * 2, 1.5e8)
        if s:
            fondo.append(s)
geo0 = json.loads((RAW / "nuts0_20m.geojson").read_text(encoding="utf-8"))
contornos = "".join(filter(None, (camino(f["geometry"], TOL * 1.5, 1e8) for f in geo0["features"] if f["properties"]["CNTR_CODE"] in EU)))
out = {"ult": int(ult), "a0": int(a0), "w": (BOX[2] - BOX[0]) // 1000, "h": (BOX[3] - BOX[1]) // 1000,
       "n3": n3, "n2": n2, "paises": paises, "ue": ue, "pais": PAIS, "shp": shapes, "fondo": "".join(fondo), "cont": contornos}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
posto = lambda c, t: 1 + sum(1 for x in t if t[x][1] > t[c][1])  # empates: mesmo posto
print(f"ok: {len(n3)} NUTS 3 en {ult} ({len(shapes)} no mapa), {len(n2)} NUTS 2; UE {ue}; tamaño {(HERE / 'data' / 'datos.json').stat().st_size / 1024:.0f} KB")
for c in ("ES113", "ES112", "ES111", "ES114"):
    print(f"  {n3[c][0]:11} {n3[c][1]} (en {a0}: {n3[c][2]}) · posto {posto(c, n3)} de {len(n3)}")
print(f"  Galicia NUTS 2: {n2['ES11'][1]} · posto {posto('ES11', n2)} de {len(n2)}")

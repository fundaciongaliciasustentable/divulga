#!/usr/bin/env python3
"""Renda neta media por persoa e por fogar en cada concello galego → data/datos.json

Fonte: INE, Atlas de Distribución de Renda dos Fogares (ADRH), «Indicadores de renta media y
mediana», unha táboa por provincia (concellos, distritos e seccións censais), último ano 2024
(rendas declaradas en 2024; o INE publícaas con dous anos de atraso):
  A Coruña   https://www.ine.es/jaxiT3/Tabla.htm?t=30989  CSV https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/30989.csv
  Lugo       https://www.ine.es/jaxiT3/Tabla.htm?t=31088  CSV https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/31088.csv
  Ourense    https://www.ine.es/jaxiT3/Tabla.htm?t=31133  CSV https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/31133.csv
  Pontevedra https://www.ine.es/jaxiT3/Tabla.htm?t=31160  CSV https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/31160.csv
Agregados (España, Galicia e provincias): táboa 53689
  https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/53689.csv
Os CSV gárdanse en data/raw/. Das táboas lense a renda neta media por persoa e por fogar de cada
concello e, para Vigo (36057) e A Coruña (15030), de cada sección censal.
Polígonos dos concellos: ../../../galicia-agora/data-out/concellos-parroquias/data.geojson
(nivel == 'concello'), proxectados e simplificados aquí mesmo (Douglas-Peucker) para o SVG.
"""
import csv
import json
import math
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
GEO = HERE.parents[2] / "galicia-agora" / "data-out" / "concellos-parroquias" / "data.geojson"
TAB = {"15": 30989, "27": 31088, "32": 31133, "36": 31160}
ANO = "2024"
RAW.mkdir(parents=True, exist_ok=True)


def baixa(t):
    f = RAW / f"ine_{t}.csv"
    if not f.exists():
        f.write_bytes(urlopen(Request(f"https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/{t}.csv",
                                      headers={"User-Agent": "Mozilla/5.0"}), timeout=600).read())
    return f


def num(s):
    s = s.strip('" ').replace(".", "").replace(",", ".")
    return float(s) if s and s not in ("-", "..") else None
IND = {"Renta neta media por persona": "p", "Renta neta media por hogar": "h"}
conc, secc = {}, {"15030": [], "36057": []}
for pr, t in TAB.items():
    for r in csv.reader(baixa(t).open(encoding="utf-8-sig"), delimiter=";"):
        if len(r) < 6 or r[4] != ANO or r[3] not in IND:
            continue
        cod, nome = r[0][:5], r[0][6:]
        v = num(r[5])
        if v is None:
            continue
        if not r[1]:
            conc.setdefault(cod, {"n": nome})[IND[r[3]]] = round(v)
        elif r[2] and cod in secc:
            s = r[2][:10]
            x = next((x for x in secc[cod] if x["id"] == s), None)
            if not x:
                x = {"id": s, "d": int(s[5:7])}
                secc[cod].append(x)
            x[IND[r[3]]] = round(v)

agr = {}
for r in csv.reader(baixa(53689).open(encoding="utf-8-sig"), delimiter=";"):
    if len(r) < 7 or r[5] != ANO or r[4] not in IND or r[3]:
        continue
    if r[1] in ("", "Galicia"):
        k = r[2] or r[1] or "España"
        agr.setdefault(k, {})[IND[r[4]]] = round(num(r[6]))
agr = {{"Coruña, A": "A Coruña"}.get(k, k): v for k, v in agr.items()}


# --- xeometría: proxección equirrectangular corrixida e Douglas-Peucker -----------------------
def dp(pts, eps):
    if len(pts) < 4:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1e-9
    imax, dmax = 0, -1
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / L if (dx or dy) else math.hypot(x - x1, y - y1)
        if d > dmax:
            imax, dmax = i, d
    if dmax <= eps:
        return [pts[0], pts[-1]]
    return dp(pts[:imax + 1], eps)[:-1] + dp(pts[imax:], eps)


gj = json.loads(GEO.read_text(encoding="utf-8"))
fs = [f for f in gj["features"] if f["properties"].get("nivel") == "concello"]
K = math.cos(math.radians(42.75))
allp = [(x * K, -y) for f in fs for poly in (f["geometry"]["coordinates"] if f["geometry"]["type"] == "MultiPolygon"
                                             else [f["geometry"]["coordinates"]]) for ring in poly for x, y in ring]
x0, x1 = min(p[0] for p in allp), max(p[0] for p in allp)
y0, y1 = min(p[1] for p in allp), max(p[1] for p in allp)
S = 1000 / (x1 - x0)
W, H = 1000, round((y1 - y0) * S)
out = []
for f in fs:
    g = f["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    d = ""
    for poly in polys:
        ring = [((x * K - x0) * S, (-y - y0) * S) for x, y in poly[0]]
        r = dp(ring, 1.2)
        if len(r) < 4:
            continue
        r = [(round(x), round(y)) for x, y in r]
        d += "M" + "L".join(f"{x},{y}" for x, y in r) + "Z"
    p = f["properties"]
    cod = p["codigo_ine"]
    c = conc[cod]
    out.append({"id": cod, "n": p["nome"], "pr": p["provincia"], "p": c["p"], "h": c["h"], "d": d})

print(len(out), "concellos;", sum(len(c["d"]) for c in out) // 1000, "KB de xeometría")
for c in sorted(out, key=lambda c: -c["p"])[:5] + sorted(out, key=lambda c: c["p"])[:5]:
    print(f"  {c['n']:22} {c['p']:>7} €/persoa  {c['h']:>7} €/fogar")
for k, v in secc.items():
    v.sort(key=lambda x: x["id"])
    print(k, len(v), "seccións", min(x["p"] for x in v), "–", max(x["p"] for x in v))
print(agr)
res = {"ano": int(ANO), "W": W, "H": H, "conc": out, "secc": secc, "agr": agr}
(HERE / "data" / "datos.json").write_text(json.dumps(res, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json")

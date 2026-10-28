#!/usr/bin/env python3
"""Poboación nada no estranxeiro en cada concello galego, por país de nacemento → data/datos.json

Fonte (descárgase en data/raw/ se falta): INE, Censo de Poboación (censo anual) a 1 de xaneiro de
2025, «Población por sexo y país de nacimiento (principales países)», unha táboa por provincia,
con datos por municipio (e sección censal, que aquí non se usa):
  66404 A Coruña · 66426 Lugo · 66436 Ourense · 66442 Pontevedra
  https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/<táboa>?nult=1&tip=AM
  (ficha: https://www.ine.es/jaxiT3/Tabla.htm?t=<táboa>)
O INE dá os 14 países de nacemento máis frecuentes en España e agrupa o resto por continente
(«Otros países de Europa», «… de América», «… de África», «… de Asia», «Oceanía»).
Nado no estranxeiro = total − nados en España. Non é o mesmo ca nacionalidade estranxeira: inclúe
moitos fillos e netos de emigrantes galegos nados en América ou Europa que teñen nacionalidade española.
Xeometría: galicia-agora (concellos-parroquias/data.geojson), simplificada aquí, e centro de
cada concello (punto medio da caixa do maior polígono, axustado ao interior).
"""
import json
import math
import time
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
CONCELLOS = Path("/Users/perezgulin/Proxectos/galicia-agora/data-out/concellos-parroquias/data.geojson")
TAB = {"15": 66404, "27": 66426, "32": 66436, "36": 66442}

for pr, t in TAB.items():
    f = RAW / f"ine_{t}.json"
    if not f.exists():
        f.write_bytes(urlopen(Request(f"https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{t}?nult=1&tip=AM",
                                      headers={"User-Agent": "Mozilla/5.0"}), timeout=600).read())
        time.sleep(1)

# País (nome do INE) → [clave, nome galego, grupo]
PAIS = {"Argentina": "Arxentina", "Bolivia": "Bolivia", "China": "China", "Colombia": "Colombia", "Cuba": "Cuba",
        "Ecuador": "Ecuador", "Francia": "Francia", "Marruecos": "Marrocos", "Perú": "Perú", "Reino Unido": "Reino Unido",
        "República Dominicana": "Rep. Dominicana", "Rumanía": "Romanía", "Ucrania": "Ucraína", "Venezuela": "Venezuela",
        "Otros países de Europa": "Resto de Europa", "Otros países de América": "Resto de América",
        "Otros países de África": "Resto de África", "Otros países de Asia": "Resto de Asia", "Oceanía": "Oceanía"}
dat, ano = {}, None
for pr, t in TAB.items():
    for s in json.loads((RAW / f"ine_{t}.json").read_text(encoding="utf-8")):
        md = {m["T3_Variable"]: m for m in s["MetaData"]}
        if "Municipios" not in md or md["Sexo"]["Nombre"] != "Total" or not s["Data"]:
            continue
        c, p = md["Municipios"]["Codigo"], md["Países"]["Nombre"]
        v = s["Data"][0]
        ano = v["Anyo"]
        if v["Valor"] is None:
            print("sen dato:", md["Municipios"]["Nombre"], p, v)
            continue
        dat.setdefault(c, {})[p] = round(v["Valor"])

# ---------- Xeometría ----------
fs = [f for f in json.loads(CONCELLOS.read_text(encoding="utf-8"))["features"] if f["properties"]["nivel"] == "concello"]
KX = math.cos(math.radians(42.8))
rings = lambda g: g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
allpts = [p for f in fs for pol in rings(f["geometry"]) for r in pol for p in r]
LON0, LAT1 = min(p[0] for p in allpts), max(p[1] for p in allpts)
S = 1000 / ((max(p[0] for p in allpts) - LON0) * KX)
proj = lambda p: ((p[0] - LON0) * KX * S, (LAT1 - p[1]) * S)


def dp(pts, tol):
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1e-9
    dmax, imax = 0, 0
    for i in range(1, len(pts) - 1):
        d = abs(dy * pts[i][0] - dx * pts[i][1] + x2 * y1 - y2 * x1) / L
        if d > dmax:
            dmax, imax = d, i
    if dmax > tol:
        return dp(pts[:imax + 1], tol)[:-1] + dp(pts[imax:], tol)
    return [pts[0], pts[-1]]


def dp_anel(r, tol):
    """Douglas-Peucker nun anel pechado: pártese polo vértice máis afastado do primeiro."""
    k = max(range(len(r)), key=lambda i: (r[i][0] - r[0][0]) ** 2 + (r[i][1] - r[0][1]) ** 2)
    return dp(r[:k + 1], tol)[:-1] + dp(r[k:], tol)


def area(r):
    return sum(r[i][0] * r[i - 1][1] - r[i - 1][0] * r[i][1] for i in range(len(r))) / 2


def centro(r):
    """Centroide do anel; se cae fóra (concellos con forma de C), punto interior máis próximo na súa horizontal."""
    A = area(r)
    cx = sum((r[i - 1][0] + r[i][0]) * (r[i][0] * r[i - 1][1] - r[i - 1][0] * r[i][1]) for i in range(len(r))) / (6 * A)
    cy = sum((r[i - 1][1] + r[i][1]) * (r[i][0] * r[i - 1][1] - r[i - 1][0] * r[i][1]) for i in range(len(r))) / (6 * A)
    xs = sorted(r[i - 1][0] + (cy - r[i - 1][1]) * (r[i][0] - r[i - 1][0]) / (r[i][1] - r[i - 1][1])
                for i in range(len(r)) if (r[i - 1][1] > cy) != (r[i][1] > cy))
    tramos = [(xs[k], xs[k + 1]) for k in range(0, len(xs) - 1, 2)]
    if tramos and not any(a <= cx <= b for a, b in tramos):
        a, b = max(tramos, key=lambda t: t[1] - t[0])
        cx = (a + b) / 2
    return round(cx, 1), round(cy, 1)


def poligono(f, tol=1.4):
    out, maior = [], None
    for pol in rings(f["geometry"]):
        r = [proj(p) for p in pol[0]]
        if maior is None or abs(area(r)) > abs(area(maior)):
            maior = r
        if abs(area(r)) < 8:
            continue
        q = []
        for x, y in dp_anel(r, tol):
            p = [round(x), round(y)]
            if not q or q[-1] != p:
                q.append(p)
        if len(q) >= 4:
            out.append(q)
    return out, centro(maior)


conc = []
for f in fs:
    p = f["properties"]
    c = p["codigo_ine"]
    d = dat[c]
    pol, ce = poligono(f)
    fora = d["Total"] - d["España"]
    paises = {k: d.get(k, 0) for k in PAIS}
    conc.append({"id": c, "n": p["nome"], "pr": p["provincia"], "pol": pol, "c": ce, "t": d["Total"], "f": fora,
                 "p": [paises[k] for k in PAIS]})
    assert abs(sum(paises.values()) - fora) <= 2, (p["nome"], sum(paises.values()), fora)
T, F = sum(o["t"] for o in conc), sum(o["f"] for o in conc)
gp = [sum(o["p"][i] for o in conc) for i in range(len(PAIS))]
print(ano, "Galicia:", F, "nados fóra de", T, f"({F / T:.1%})")
print("países:", sorted(zip(PAIS.values(), gp), key=lambda x: -x[1]))
r = sorted(conc, key=lambda o: -o["f"] / o["t"])
print("máis %:", [(o["n"], f"{o['f'] / o['t']:.1%}") for o in r[:10]])
print("menos %:", [(o["n"], f"{o['f'] / o['t']:.1%}") for o in r[-5:]])
out = {"ano": ano, "paises": list(PAIS.values()), "conc": sorted(conc, key=lambda o: o["n"])}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json", (HERE / "data" / "datos.json").stat().st_size // 1024, "KB")

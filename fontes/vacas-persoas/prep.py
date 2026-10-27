#!/usr/bin/env python3
"""Vacas, gando e persoas por concello → data/datos.json

Fontes (en data/, descárganse se faltan):
  ige_62.csv       IGE, efectivos de gando bovino por concello (Medio Rural), 2002-2025
                   https://www.ige.gal/igebdt/igeapi/csv/datos/62
  ige_10332.csv    IGE, Censo agrario 2020: cabezas e unidades gandeiras (UGT) por especie e concello
                   https://www.ige.gal/igebdt/igeapi/csv/datos/10332
  ine_<táboa>.json INE, Padrón municipal por provincia (2868, 2880, 2885, 2890), con códigos
                   https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/<táboa>?nult=30&tip=AM

Os concellos fusionados (Oza-Cesuras 2013, Cerdedo-Cotobade 2016) súmanse nos anos anteriores.
O mapa é un cartograma de hexágonos: un hexágono por concello, o máis preto posible do seu
centro real (asignación óptima con scipy). Necesita shapely e scipy.
"""
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
from scipy.optimize import linear_sum_assignment
from shapely.geometry import Point, shape
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
CONCELLOS = Path("/Users/perezgulin/Proxectos/galicia-agora/data-out/concellos-parroquias/data.geojson")
FUSIONS = {"15902": ["15026", "15063"], "36902": ["36011", "36012"]}
VELLO = {v: k for k, vs in FUSIONS.items() for v in vs}
URLS = {"ige_62.csv": "https://www.ige.gal/igebdt/igeapi/csv/datos/62",
        "ige_10332.csv": "https://www.ige.gal/igebdt/igeapi/csv/datos/10332",
        **{f"ine_{t}.json": f"https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{t}?nult=30&tip=AM"
           for t in (2868, 2880, 2885, 2890)}}
for nome, url in URLS.items():
    if not (DATA / nome).exists():
        DATA.mkdir(exist_ok=True)
        (DATA / nome).write_bytes(urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=400).read())
num = lambda s: float(s) if s not in ("", None) else None

# Gando bovino por concello e ano
bov = defaultdict(lambda: defaultdict(dict))  # concello → ano → {vacas, bovinos, leite}
CAMPO = {"Número de vacas": "vacas", "Número de bovinos": "bovinos", "Número de vacas de muxidura": "leite"}
for x in csv.DictReader((DATA / "ige_62.csv").open(encoding="latin1")):
    c, k = x["CodEspazo"], CAMPO.get(x["Explotacións e bovinos"])
    if len(c) != 5 or not k or num(x["DatoN"]) is None:
        continue
    c = VELLO.get(c, c)
    d = bov[c][int(x["Tempo"])]
    d[k] = d.get(k, 0) + num(x["DatoN"])

# Poboación
pob = defaultdict(dict)
for t in (2868, 2880, 2885, 2890):
    for s in json.loads((DATA / f"ine_{t}.json").read_text()):
        md = {m["T3_Variable"]: m for m in s["MetaData"]}
        if md.get("Sexo", {}).get("Codigo") != "0" or "Municipios" not in md:
            continue
        c = VELLO.get(md["Municipios"]["Codigo"], md["Municipios"]["Codigo"])
        for v in s["Data"]:
            if v["Valor"] is not None:
                pob[c][v["Anyo"]] = pob[c].get(v["Anyo"], 0) + v["Valor"]

# Censo agrario 2020: UGT e cabezas
ESP = {"Bovino": "b", "Porcino": "p", "Aves de curral": "a", "Ovino e Caprino": "o"}
ug, cab, reservado = defaultdict(dict), defaultdict(dict), defaultdict(list)
for x in csv.DictReader((DATA / "ige_10332.csv").open(encoding="latin1")):
    c, e, m = x["CodEspazo"], ESP[x["Tipo de gando"]], x["Características básicas da explotación"]
    if len(c) != 5:
        continue
    v = num(x["DatoN"])
    if m == "UGT":
        if v is None and x["DatoT"] == "..":
            reservado[c].append(e)
        ug[c][e] = round(v or 0)
    elif m == "Cabezas":
        cab[c][e] = round(v or 0)

# Concellos e cartograma de hexágonos
fs = [f for f in json.loads(CONCELLOS.read_text(encoding="utf-8"))["features"] if f["properties"]["nivel"] == "concello"]
KX = math.cos(math.radians(42.8))
geo = {f["properties"]["codigo_ine"]: shape(f["geometry"]).buffer(0) for f in fs}
cen = {c: g.representative_point() for c, g in geo.items()}
gal = unary_union(list(geo.values())).buffer(0.03)
ids = sorted(geo)
pts = np.array([[cen[c].x * KX, cen[c].y] for c in ids])
# radio do hexágono (graos de latitude): o maior que deixe ~1,03 celas por concello dentro de Galicia
r, cells = 0.08, []
x0, y0, x1, y1 = gal.bounds
while len(cells) < 1.03 * len(ids):
    r *= 0.98
    cells = []
    dy, dx = 1.5 * r, math.sqrt(3) * r
    for j in range(int((y1 - y0) / dy) + 2):
        for i in range(int((x1 - x0) * KX / dx) + 2):
            cx, cy = x0 * KX + i * dx + (dx / 2 if j % 2 else 0), y0 + j * dy
            if gal.contains(Point(cx / KX, cy)):
                cells.append((i, j, cx, cy))
cpt = np.array([[c[2], c[3]] for c in cells])
cost = ((pts[:, None, :] - cpt[None, :, :]) ** 2).sum(-1)
fila, col = linear_sum_assignment(cost)
print("hexágonos dispoñibles", len(cells), "concellos", len(ids))
hexpos = {ids[a]: (cells[b][0], cells[b][1]) for a, b in zip(fila, col)}

anos_b = sorted({y for c in bov.values() for y in c})
out = []
for f in fs:
    p = f["properties"]
    c = p["codigo_ine"]
    out.append({"id": c, "n": p["nome"], "pr": p["provincia"], "h": hexpos[c],
                "pob": {y: round(pob[c][y]) for y in anos_b if y in pob[c]},
                "vac": {y: round(bov[c][y].get("vacas", 0)) for y in anos_b if y in bov[c]},
                "bov": round(bov[c][anos_b[-1]].get("bovinos", 0)),
                "lei": round(bov[c][anos_b[-1]].get("leite", 0)),
                "ug": ug.get(c, {}), "cab": cab.get(c, {}), "res": reservado.get(c, [])})
out.sort(key=lambda o: o["n"])

ult = anos_b[-1]
mais = [o for o in out if o["vac"].get(ult, 0) > o["pob"][ult]]
print(ult, "concellos con máis vacas ca persoas:", len(mais))
for y in anos_b:
    print(" ", y, sum(1 for o in out if o["vac"].get(y, 0) > o["pob"].get(y, 1e12)),
          "vacas", sum(o["vac"].get(y, 0) for o in out), "persoas", sum(o["pob"].get(y, 0) for o in out))
ugm = [o for o in out if sum(o["ug"].values()) > o["pob"].get(2020, 1e12)]
print("2020 concellos con máis UG de gando ca persoas:", len(ugm))
top = sorted(out, key=lambda o: -o["vac"].get(ult, 0) / o["pob"][ult])[:8]
print("máis vacas por persoa:", [(o["n"], round(o["vac"][ult] / o["pob"][ult], 2)) for o in top])
(DATA / "datos.json").write_text(json.dumps({"anos": anos_b, "concellos": out}, ensure_ascii=False,
                                            separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json", (DATA / "datos.json").stat().st_size // 1024, "KB")

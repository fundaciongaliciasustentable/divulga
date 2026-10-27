#!/usr/bin/env python3
"""Os castros de Galicia segundo OpenStreetMap → data/datos.json

Fonte: OpenStreetMap (© colaboradores de OSM, ODbL), consulta Overpass de todos os
historic=archaeological_site dentro de Galicia (ISO3166-2 ES-GA), gardada en data/raw/osm.json.
O catálogo de patrimonio da Xunta non se publica como datos abertos, así que OSM é a mellor
fonte libre, e incompleta: hai castros sen cartografar.

Que contamos como castro: o tipo fortification/hillfort, a civilización castro_culture/celtic,
ou un nome que empeza por Castro, Castriño, Castrelo, Croa ou Coroa; nunca túmulos, petróglifos,
mámoas e demais. Un mesmo castro pode estar como punto e como área: os que distan menos de
250 m xúntanse. Concellos: /Users/perezgulin/Proxectos/galicia-agora (o mesmo xeojson que usa
monte-concellos) e o contorno de Galicia de galicia-apagandose.
"""
import json
import math
import re
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
from scipy.sparse.csgraph import minimum_spanning_tree
from scipy.spatial import cKDTree
from shapely.geometry import Point, shape
from shapely.prepared import prep

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
CONCELLOS = Path("/Users/perezgulin/Proxectos/galicia-agora/data-out/concellos-parroquias/data.geojson")
CONTORNO = HERE.parent / "galicia-apagandose" / "data" / "galicia.geojson"
Q = """[out:json][timeout:180];
area["ISO3166-2"="ES-GA"]->.g;
nwr["historic"="archaeological_site"](area.g);
out center tags;"""
NON = {"tumulus", "petroglyph", "megalith", "necropolis", "tomb", "chapel", "mineral_extraction", "roman_villa",
       "bridge", "dolmen"}
NOME = re.compile(r"(?i)^(o |a |os |as )?(castro|castros|castriño|castrelo|castrove|croa|coroa)\b")

f = RAW / "osm.json"
if not f.exists():
    RAW.mkdir(parents=True, exist_ok=True)
    f.write_bytes(urlopen(Request("https://overpass-api.de/api/interpreter", data=urlencode({"data": Q}).encode(),
                                  headers={"User-Agent": "Divulga FGS"}), timeout=240).read())
el = json.loads(f.read_text(encoding="utf-8"))["elements"]


def castro(t):
    s, c, n = t.get("archaeological_site", ""), t.get("historic:civilization", ""), t.get("name", "")
    if s in NON or t.get("fortification_type") in ("castle", "tower"):
        return False
    return s in ("fortification", "hillfort") or c in ("castro_culture", "celtic") or bool(NOME.match(n))


pts = []
for e in el:
    t = e.get("tags", {})
    if not castro(t):
        continue
    lat, lon = (e["lat"], e["lon"]) if "lat" in e else (e["center"]["lat"], e["center"]["lon"])
    pts.append({"lat": lat, "lon": lon, "n": t.get("name", ""), "area": e["type"] != "node", "id": f"{e['type'][0]}{e['id']}"})

# Metros aproximados (equirectangular a 43° N), para distancias
LAT0 = 42.8
mx = lambda lon: lon * 111_320 * math.cos(math.radians(LAT0))
my = lambda lat: lat * 110_574
XY = np.array([[mx(p["lon"]), my(p["lat"])] for p in pts])
# Xuntar duplicados (< 250 m): quédase o que ten nome, e se os dous teñen, a área
orde = sorted(range(len(pts)), key=lambda i: (not pts[i]["n"], not pts[i]["area"]))
arbore, fora = cKDTree(XY), set()
for i in orde:
    if i in fora:
        continue
    for j in arbore.query_ball_point(XY[i], 250):
        if j != i:
            fora.add(j)
keep = [i for i in range(len(pts)) if i not in fora]
pts = [pts[i] for i in keep]
XY = XY[keep]
print("castros:", len(pts), "· xuntados por duplicados:", len(fora))

# Concello de cada castro
gj = json.loads(CONCELLOS.read_text(encoding="utf-8"))
conc = []
for ft in gj["features"]:
    p = ft["properties"]
    if p.get("nivel") == "concello":  # o xeojson trae tamén as parroquias
        g = shape(ft["geometry"])
        conc.append((str(p["codigo_ine"]), p["nome"], g, prep(g)))
conc = {c[0]: c for c in conc}.values()
conts = {}
for p in pts:
    pt = Point(p["lon"], p["lat"])
    c = next((c for c in conc if c[3].contains(pt)), None)
    p["c"] = c[0] if c else None
    if c:
        conts[c[0]] = conts.get(c[0], 0) + 1
km2 = {c[0]: c[2].area * (111.32 * math.cos(math.radians(c[2].centroid.y))) * 110.574 for c in conc}
nome = {c[0]: c[1] for c in conc}
top = sorted(conts.items(), key=lambda kv: -kv[1])[:10]
dens = sorted(((k, v / km2[k] * 100) for k, v in conts.items() if km2[k] > 20), key=lambda kv: -kv[1])[:10]
print("máis castros:", [(nome[k], v) for k, v in top])
print("máis densos /100 km²:", [(nome[k], round(v, 1)) for k, v in dens])

# Veciño máis próximo e árbore de expansión mínima (as liñas da constelación)
dd, _ = cKDTree(XY).query(XY, k=2)
nn = dd[:, 1]
pares = cKDTree(XY).query_pairs(6000, output_type="ndarray")
from scipy.sparse import coo_matrix
w = np.linalg.norm(XY[pares[:, 0]] - XY[pares[:, 1]], axis=1)
mst = minimum_spanning_tree(coo_matrix((w, (pares[:, 0], pares[:, 1])), shape=(len(pts), len(pts)))).tocoo()
arestas = [(int(a), int(b)) for a, b, v in zip(mst.row, mst.col, mst.data) if v <= 4000]

# Parte do territorio a menos de 2 km dun castro (mostraxe en reixa de 500 m)
gal = shape(json.loads(CONTORNO.read_text(encoding="utf-8"))["geometry"])
minx, miny, maxx, maxy = gal.bounds
gp = prep(gal)
mostra = [(x, y) for x in np.arange(minx, maxx, 0.006) for y in np.arange(miny, maxy, 0.0045) if gp.contains(Point(x, y))]
MX = np.array([[mx(x), my(y)] for x, y in mostra])
dm, _ = cKDTree(XY).query(MX)
print(f"a menos de 2 km dun castro: {np.mean(dm < 2000):.0%} do territorio · distancia mediana ao máis próximo {np.median(dm) / 1000:.1f} km")

# Proxección para o SVG: lonxitude escalada polo coseno da latitude
W = 1000
x0, x1 = minx - 0.05, maxx + 0.05
k = W / ((x1 - x0) * math.cos(math.radians(LAT0)))
X = lambda lon: round((lon - x0) * math.cos(math.radians(LAT0)) * k, 1)
Y = lambda lat: round((maxy + 0.05 - lat) * k, 1)
H = Y(miny - 0.05)
contorno = []
simp = gal.simplify(0.004)
for poly in getattr(simp, "geoms", [simp]):
    if poly.area < 0.0004:
        continue
    contorno.append([[X(a), Y(b)] for a, b in poly.exterior.coords])
out = {"W": W, "H": H, "c": [[X(p["lon"]), Y(p["lat"]), p["n"], p["c"]] for p in pts], "e": arestas, "contorno": contorno,
       "conc": {k: nome[k] for k in conts}, "top": top, "dens": [[k, round(v, 1)] for k, v in dens],
       "nn": round(float(np.median(nn)) / 1000, 2), "dous": round(float(np.mean(dm < 2000)), 3),
       "med": round(float(np.median(dm)) / 1000, 2), "km2": round(sum(km2.values()))}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"veciño máis próximo (mediana) {out['nn']} km · arestas {len(arestas)} · ok: data/datos.json")

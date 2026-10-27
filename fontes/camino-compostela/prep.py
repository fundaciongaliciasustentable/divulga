#!/usr/bin/env python3
"""Peregrinos que recollen a Compostela: camiños, puntos de saída, países e serie 2004-2025
→ data/datos.json

Fontes (en data/):
  oficina.json         cifras de 2019-2025 transcritas do informe público da Oficina do Peregrino
  pdf/pAAAA.pdf        informes anuais 2004-2018 da Oficina (total do ano)
  countries-50m.json   Natural Earth vía world-atlas 2.0.2 (contorno de España, Portugal e Francia)
Os trazados dos camiños son esquemáticos: pasan polas localidades principais de cada ruta. O grosor
de cada tramo son os peregrinos que saíron dun punto anterior dese camiño (20 puntos de saída coñecidos).
Necesita pypdf e shapely.
"""
import json
import re
from pathlib import Path

from pypdf import PdfReader
from shapely.geometry import Polygon, box, mapping
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
SANTIAGO = (-8.545, 42.880)
# lonxitude, latitude das localidades polas que se debuxa cada camiño
P = {
    "SJPP": (-1.237, 43.163), "Roncesvalles": (-1.320, 43.009), "Pamplona": (-1.645, 42.812), "Logroño": (-2.445, 42.466),
    "Burgos": (-3.700, 42.343), "León": (-5.567, 42.599), "Astorga": (-6.056, 42.457), "Ponferrada": (-6.598, 42.546),
    "O Cebreiro": (-7.043, 42.708), "Sarria": (-7.414, 42.781), "Melide": (-8.015, 42.914), "Arzúa": (-8.164, 42.927),
    "Porto": (-8.611, 41.150), "Barcelos": (-8.616, 41.531), "Ponte de Lima": (-8.583, 41.767), "Valença": (-8.643, 42.028),
    "Tui": (-8.644, 42.047), "O Porriño": (-8.620, 42.161), "Redondela": (-8.609, 42.283), "Pontevedra": (-8.645, 42.431),
    "Caldas": (-8.639, 42.604), "Padrón": (-8.661, 42.739), "Póvoa": (-8.761, 41.383), "Viana": (-8.830, 41.693),
    "Caminha": (-8.838, 41.875), "A Guarda": (-8.874, 41.902), "Baiona": (-8.851, 42.119), "Vigo": (-8.722, 42.240),
    "Ferrol": (-8.236, 43.483), "Pontedeume": (-8.170, 43.407), "Betanzos": (-8.212, 43.280), "Bruma": (-8.357, 43.060),
    "Oviedo": (-5.845, 43.362), "Grado": (-6.071, 43.388), "Tineo": (-6.414, 43.337), "Grandas": (-6.876, 43.215),
    "Fonsagrada": (-7.067, 43.123), "Lugo": (-7.556, 43.012), "Irun": (-1.789, 43.338), "Donostia": (-1.981, 43.318),
    "Bilbao": (-2.935, 43.263), "Santander": (-3.810, 43.462), "Gijón": (-5.661, 43.532), "Avilés": (-5.925, 43.556),
    "Luarca": (-6.536, 43.543), "Ribadeo": (-7.040, 43.536), "Mondoñedo": (-7.362, 43.428), "Vilalba": (-7.680, 43.298),
    "Zamora": (-5.745, 41.503), "Puebla": (-6.640, 42.100), "A Gudiña": (-7.139, 42.061), "Ourense": (-7.864, 42.336),
    "Silleda": (-8.246, 42.697), "O Barco": (-6.980, 42.416), "Monforte": (-7.514, 42.521), "Chantada": (-7.771, 42.609),
    "Lalín": (-8.111, 42.661), "Negreira": (-8.736, 42.909), "Olveiroa": (-9.026, 43.001), "Fisterra": (-9.263, 42.908),
    "Muxía": (-9.218, 43.104), "Santiago": SANTIAGO,
}
RUTAS = {
    "Francés": ["SJPP", "Roncesvalles", "Pamplona", "Logroño", "Burgos", "León", "Astorga", "Ponferrada", "O Cebreiro", "Sarria", "Melide", "Arzúa", "Santiago"],
    "Portugués": ["Porto", "Barcelos", "Ponte de Lima", "Valença", "Tui", "O Porriño", "Redondela", "Pontevedra", "Caldas", "Padrón", "Santiago"],
    "Portugués Costa": ["Porto", "Póvoa", "Viana", "Caminha", "A Guarda", "Baiona", "Vigo", "Redondela", "Pontevedra", "Caldas", "Padrón", "Santiago"],
    "Inglés": ["Ferrol", "Pontedeume", "Betanzos", "Bruma", "Santiago"],
    "Primitivo": ["Oviedo", "Grado", "Tineo", "Grandas", "Fonsagrada", "Lugo", "Melide", "Arzúa", "Santiago"],
    "Norte": ["Irun", "Donostia", "Bilbao", "Santander", "Gijón", "Avilés", "Luarca", "Ribadeo", "Mondoñedo", "Vilalba", "Arzúa", "Santiago"],
    "Vía da Prata": ["Zamora", "Puebla", "A Gudiña", "Ourense", "Silleda", "Santiago"],
    "De Inverno": ["Ponferrada", "O Barco", "Monforte", "Chantada", "Lalín", "Silleda", "Santiago"],
    "Muxía-Fisterra": ["Santiago", "Negreira", "Olveiroa", "Fisterra", "Muxía"],
}
# punto de saída → (camiño, localidade do trazado onde empeza)
SAIDA_RUTA = {"Sarria": ("Francés", "Sarria"), "Tui": ("Portugués", "Tui"), "Saint-Jean-Pied-de-Port": ("Francés", "SJPP"),
              "Ferrol": ("Inglés", "Ferrol"), "Porto": ("Portugués", "Porto"), "Porto (costa)": ("Portugués Costa", "Porto"),
              "Vigo": ("Portugués Costa", "Vigo"), "Valença do Minho": ("Portugués", "Valença"), "Oviedo": ("Primitivo", "Oviedo"),
              "Baiona": ("Portugués Costa", "Baiona"), "Lugo": ("Primitivo", "Lugo"), "León": ("Francés", "León"),
              "O Cebreiro": ("Francés", "O Cebreiro"), "Ponferrada": ("Francés", "Ponferrada"), "Irun": ("Norte", "Irun"),
              "Ourense": ("Vía da Prata", "Ourense"), "Roncesvalles": ("Francés", "Roncesvalles"), "A Guarda": ("Portugués Costa", "A Guarda"),
              "O Porriño": ("Portugués", "O Porriño"), "Astorga": ("Francés", "Astorga")}
SAIDA = {"Sarria": "Sarria", "Tui": "Tui", "Saint-Jean-Pied-de-Port": "SJPP", "Ferrol": "Ferrol", "Porto": "Porto",
         "Porto (costa)": "Póvoa", "Vigo": "Vigo", "Valença do Minho": "Valença", "Oviedo": "Oviedo", "Baiona": "Baiona",
         "Lugo": "Lugo", "León": "León", "O Cebreiro": "O Cebreiro", "Ponferrada": "Ponferrada", "Irun": "Irun",
         "Ourense": "Ourense", "Roncesvalles": "Roncesvalles", "A Guarda": "A Guarda", "O Porriño": "O Porriño",
         "Astorga": "Astorga"}
BBOX = (-9.6, 40.9, -0.9, 43.95)

of = json.loads((DATA / "oficina.json").read_text(encoding="utf-8"))
tot = {int(k): v for k, v in of["totais"].items()}
for y in range(2004, 2019):
    t = re.sub(r"\s+", " ", " ".join(p.extract_text() or "" for p in PdfReader(DATA / "pdf" / f"p{y}.pdf").pages))
    m = re.search(r"recibieron ([\d.]+) peregrinos", t) or re.search(r"([\d.]{6,8}) peregrinos", t)
    tot[y] = int(m.group(1).replace(".", ""))
print({y: tot[y] for y in sorted(tot)})

# Contorno: decodificación mínima de TopoJSON (arcos cuantizados e en deltas)
topo = json.loads((DATA / "countries-50m.json").read_text())
sc, tr = topo["transform"]["scale"], topo["transform"]["translate"]
arcs = []
for a in topo["arcs"]:
    x = y = 0
    pts = []
    for dx, dy in a:
        x += dx
        y += dy
        pts.append((x * sc[0] + tr[0], y * sc[1] + tr[1]))
    arcs.append(pts)
arc = lambda i: arcs[i] if i >= 0 else arcs[~i][::-1]
ring = lambda idx: [p for k, i in enumerate(idx) for p in (arc(i) if k == 0 else arc(i)[1:])]
polys = []
for g in topo["objects"]["countries"]["geometries"]:
    if g.get("properties", {}).get("name") not in ("Spain", "Portugal", "France", "Andorra"):
        continue
    for poly in (g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]]):
        polys.append(Polygon(ring(poly[0]), [ring(h) for h in poly[1:]]).buffer(0))
terra = unary_union(polys).intersection(box(*BBOX)).simplify(0.01)
contorno = [[[round(x, 3), round(y, 3)] for x, y in p.exterior.coords]
            for p in getattr(terra, "geoms", [terra]) if p.area > 0.002]

cam = {n: (v, py) for n, v, py in of["camino_2025"]}
# Peregrinos que percorren cada tramo: os que saíron dun punto anterior do mesmo camiño. Só se
# coñece a saída dos 20 puntos máis habituais, así que os tramos levan unha cota inferior.
tramos = {}
for n, v in of["saida_2025"]:
    ruta, ini = SAIDA_RUTA[n]
    pts = RUTAS[ruta]
    for a, b in zip(pts[pts.index(ini):], pts[pts.index(ini) + 1:]):
        t = tramos.setdefault((a, b), {"v": 0, "r": set()})
        t["v"] += v
        t["r"].add(ruta)
for ruta, pts in RUTAS.items():  # os tramos sen saídas coñecidas debúxanse finos
    if ruta == "Muxía-Fisterra":
        continue
    for a, b in zip(pts, pts[1:]):
        tramos.setdefault((a, b), {"v": 0, "r": set()})["r"].add(ruta)
print("peregrinos con saída coñecida:", sum(v for _, v in of["saida_2025"]), "· tramo máis cargado:", max(t["v"] for t in tramos.values()))
out = {
    "serie": [[y, tot.get(y)] for y in range(2004, 2026)],
    "esp": of["espanois"], "ext": of["estranxeiros"],
    "camino": of["camino_2025"], "pais": of["pais_2025"], "motivo": of["motivo_2025"],
    "saida": [[n, v, P[SAIDA[n]]] for n, v in of["saida_2025"]], "saidaTotal": of["saida_total_2025"],
    "rutas": [[n, cam[n][0], [P[k] for k in ks]] for n, ks in RUTAS.items()],
    "tramos": [[P[a], P[b], t["v"], sorted(t["r"])] for (a, b), t in tramos.items()],
    "lugares": {k: P[k] for k in ("Santiago", "Porto", "Oviedo", "León", "Burgos", "Pamplona", "Ourense", "Lugo", "Vigo", "Ferrol", "Zamora", "Bilbao", "Santander", "Irun")},
    "contorno": contorno, "bbox": BBOX,
}
(DATA / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json", (DATA / "datos.json").stat().st_size // 1024, "KB", len(contorno), "polígonos")

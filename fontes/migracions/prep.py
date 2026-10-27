#!/usr/bin/env python3
"""Inmigración e emigración de Galicia por procedencia e destino → data/datos.json

Fontes (en data/, descárganse se faltan):
  ige_10614.csv / ige_10613.csv  IGE: inmigracións por procedencia e emigracións por destino, 2021-2024
  ige_568.csv / ige_567.csv      IGE: as mesmas, serie 1992-2021 (Estatística de variacións residenciais)
  ine_69695.json / ine_69710.json INE: inmigracións desde o estranxeiro por país de procedencia e
                                  emigracións ao estranxeiro por país de destino, por comunidade
  countries-110m.json, countries-50m.json  Natural Earth vía world-atlas 2.0.2
Os mapas usan a proxección Equal Earth.
"""
import csv
import json
import math
from pathlib import Path
from urllib.request import Request, urlopen

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
URLS = {**{f"ige_{c}.csv": f"https://www.ige.gal/igebdt/igeapi/csv/datos/{c}" for c in (10614, 10613, 568, 567)},
        **{f"ine_{t}.json": f"https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{t}?nult=6&tip=AM" for t in (69695, 69710)},
        **{f"countries-{r}.json": f"https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-{r}.json" for r in ("110m", "50m")}}
for n, u in URLS.items():
    if not (DATA / n).exists():
        (DATA / n).write_bytes(urlopen(Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=300).read())
GALICIA = (-8.54, 42.88)

# nome do INE → (nome en galego, nome en Natural Earth)
PAIS = {
    "Bélgica": ("Bélxica", "Belgium"), "Bulgaria": ("Bulgaria", "Bulgaria"), "Dinamarca": ("Dinamarca", "Denmark"),
    "Finlandia": ("Finlandia", "Finland"), "Francia": ("Francia", "France"), "Irlanda": ("Irlanda", "Ireland"),
    "Italia": ("Italia", "Italy"), "Países Bajos": ("Países Baixos", "Netherlands"), "Polonia": ("Polonia", "Poland"),
    "Portugal": ("Portugal", "Portugal"), "Alemania": ("Alemaña", "Germany"), "Rumanía": ("Romanía", "Romania"),
    "Suecia": ("Suecia", "Sweden"), "Lituania": ("Lituania", "Lithuania"), "Noruega": ("Noruega", "Norway"),
    "Reino Unido": ("Reino Unido", "United Kingdom"), "Suiza": ("Suíza", "Switzerland"), "Ucrania": ("Ucraína", "Ukraine"),
    "Moldavia": ("Moldavia", "Moldova"), "Rusia": ("Rusia", "Russia"), "Argelia": ("Alxeria", "Algeria"),
    "Gambia": ("Gambia", "Gambia"), "Ghana": ("Ghana", "Ghana"), "Guinea": ("Guinea", "Guinea"),
    "Guinea Ecuatorial": ("Guinea Ecuatorial", "Eq. Guinea"), "Mali": ("Malí", "Mali"), "Marruecos": ("Marrocos", "Morocco"),
    "Mauritania": ("Mauritania", "Mauritania"), "Nigeria": ("Nixeria", "Nigeria"), "Senegal": ("Senegal", "Senegal"),
    "Estados Unidos de América": ("Estados Unidos", "United States of America"), "México": ("México", "Mexico"),
    "Canadá": ("Canadá", "Canada"), "Cuba": ("Cuba", "Cuba"), "Honduras": ("Honduras", "Honduras"),
    "Nicaragua": ("Nicaragua", "Nicaragua"), "República Dominicana": ("Rep. Dominicana", "Dominican Rep."),
    "Argentina": ("Arxentina", "Argentina"), "Bolivia": ("Bolivia", "Bolivia"), "Brasil": ("Brasil", "Brazil"),
    "Colombia": ("Colombia", "Colombia"), "Chile": ("Chile", "Chile"), "Ecuador": ("Ecuador", "Ecuador"),
    "Paraguay": ("Paraguai", "Paraguay"), "Perú": ("Perú", "Peru"), "Uruguay": ("Uruguai", "Uruguay"),
    "Venezuela": ("Venezuela", "Venezuela"), "Bangladesh": ("Bangladesh", "Bangladesh"), "China": ("China", "China"),
    "Filipinas": ("Filipinas", "Philippines"), "India": ("India", "India"), "Pakistán": ("Paquistán", "Pakistan"),
}
OUTRO = {"Otro país de la Unión Europea sin España": "Resto da UE", "Otro país del resto de Europa": "Resto de Europa",
         "Otro país de África": "Resto de África", "Otro país de Centro América y Caribe": "Resto de Centroamérica",
         "Otro país de Sudamérica": "Resto de Sudamérica", "Otro país de Asia": "Resto de Asia", "Oceanía": "Oceanía"}
CONT = {"Europa": ["Bélgica", "Bulgaria", "Dinamarca", "Finlandia", "Francia", "Irlanda", "Italia", "Países Bajos", "Polonia",
                   "Portugal", "Alemania", "Rumanía", "Suecia", "Lituania", "Noruega", "Reino Unido", "Suiza", "Ucrania",
                   "Moldavia", "Rusia", "Otro país de la Unión Europea sin España", "Otro país del resto de Europa"],
        "África": ["Argelia", "Gambia", "Ghana", "Guinea", "Guinea Ecuatorial", "Mali", "Marruecos", "Mauritania", "Nigeria",
                   "Senegal", "Otro país de África"],
        "América": ["Estados Unidos de América", "México", "Canadá", "Cuba", "Honduras", "Nicaragua", "República Dominicana",
                    "Otro país de Centro América y Caribe", "Argentina", "Bolivia", "Brasil", "Colombia", "Chile", "Ecuador",
                    "Paraguay", "Perú", "Uruguay", "Venezuela", "Otro país de Sudamérica"],
        "Asia e Oceanía": ["Bangladesh", "China", "Filipinas", "India", "Pakistán", "Otro país de Asia", "Oceanía"]}
CONT_DE = {p: c for c, ps in CONT.items() for p in ps}
CCAA = {"Andalucía": (-5.98, 37.39), "Aragón": (-0.88, 41.65), "Asturias": (-5.85, 43.36), "Baleares": (2.65, 39.57),
        "Canarias": (-15.43, 28.12), "Cantabria": (-3.81, 43.46), "Castela - A Mancha": (-4.03, 39.86),
        "Castela e León": (-4.72, 41.65), "Cataluña": (2.17, 41.39), "Ceuta": (-5.32, 35.89), "Estremadura": (-6.34, 38.92),
        "A Rioxa": (-2.45, 42.47), "Madrid": (-3.70, 40.42), "Melilla": (-2.94, 35.29), "Murcia": (-1.13, 37.99),
        "Navarra": (-1.64, 42.81), "País Vasco": (-2.67, 42.85), "Valencia": (-0.38, 39.47)}


def equal_earth(lon, lat):
    A1, A2, A3, A4 = 1.340264, -0.081106, 0.000893, 0.003796
    M = math.sqrt(3) / 2
    p = math.asin(M * math.sin(math.radians(lat)))
    p2 = p * p
    p6 = p2 * p2 * p2
    x = math.radians(lon) * math.cos(p) / (M * (A1 + 3 * A2 * p2 + p6 * (7 * A3 + 9 * A4 * p2)))
    y = p * (A1 + A2 * p2 + p6 * (A3 + A4 * p2))
    return x, y


def topo_polys(fn, filtro=None):
    t = json.loads((DATA / fn).read_text())
    sc, tr = t["transform"]["scale"], t["transform"]["translate"]
    arcs = []
    for a in t["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in a:
            x += dx
            y += dy
            pts.append((x * sc[0] + tr[0], y * sc[1] + tr[1]))
        arcs.append(pts)
    arc = lambda i: arcs[i] if i >= 0 else arcs[~i][::-1]
    ring = lambda idx: [p for k, i in enumerate(idx) for p in (arc(i) if k == 0 else arc(i)[1:])]
    out = {}
    for g in t["objects"]["countries"]["geometries"]:
        n = g.get("properties", {}).get("name")
        if g["type"] not in ("Polygon", "MultiPolygon") or (filtro and n not in filtro):
            continue
        polys = [Polygon(ring(p[0]), [ring(h) for h in p[1:]]).buffer(0) for p in (g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]])]
        out[n] = unary_union(polys)
    return out


# --- fluxos 2024 por país (INE) ---
def ine(t):
    d = json.loads((DATA / f"ine_{t}.json").read_text())
    r = {}
    for s in d:
        if not s["Nombre"].startswith("Galicia."):
            continue
        n = s["Nombre"].split(".")[1].strip()
        r[n] = {x["Anyo"]: x["Valor"] for x in s["Data"] if x["Valor"] is not None}
    return r


inm, emi = ine(69695), ine(69710)
ANO = max(inm["Total"])
paises = []
for n in list(PAIS) + list(OUTRO):
    paises.append({"n": PAIS[n][0] if n in PAIS else OUTRO[n], "c": CONT_DE[n], "en": PAIS[n][1] if n in PAIS else None,
                   "i": round(inm.get(n, {}).get(ANO, 0)), "e": round(emi.get(n, {}).get(ANO, 0))})
print(ANO, "estranxeiro: chegan", inm["Total"][ANO], "marchan", emi["Total"][ANO],
      "· suma países", sum(p["i"] for p in paises), sum(p["e"] for p in paises))

# --- fluxos 2024 coas comunidades e serie (IGE) ---
def ige(c, k):
    r = {}
    for x in csv.DictReader((DATA / f"ige_{c}.csv").open(encoding="latin1")):
        if x["Espazo"].strip() == "12 Galicia" and x["Nacionalidade"].strip() == "Total":
            r[(int(x["Tempo"]), x[k].strip())] = float(x["DatoN"] or 0)
    return r


i2, e2, i1, e1 = ige(10614, "Orixe"), ige(10613, "Destino"), ige(568, "Orixe"), ige(567, "Destino")
ccaa = [{"n": n, "p": CCAA[n], "i": round(i2[(ANO, n)]), "e": round(e2[(ANO, n)])} for n in CCAA]
serie = []
for y in range(2002, ANO + 1):
    I, E = (i1, e1) if y <= 2020 else (i2, e2)
    serie.append({"y": y, "ei": round(I[(y, "Estranxeiro")]), "ee": round(E[(y, "Estranxeiro")]),
                  "si": round(I[(y, "Resto de España")]), "se": round(E[(y, "Resto de España")])})

# --- mapa do mundo e de España ---
mundo = topo_polys("countries-110m.json")
mundo.pop("Antarctica", None)
W = 1000
x0, y0 = equal_earth(-180, 0)[0], equal_earth(0, 85)[1]
xs = W / (2 * -x0)
P = lambda lon, lat: (lambda q: (round((q[0] - x0) * xs, 1), round((y0 - q[1]) * xs, 1)))(equal_earth(lon, lat))
def path(g, proj):
    d = []
    for p in getattr(g, "geoms", [g]):
        if p.area < 0.3 and proj is P:
            continue
        if p.bounds[2] - p.bounds[0] > 180:  # polígonos que cruzan o antimeridiano (Fixi, Chukotka)
            continue
        d.append("M" + "L".join(f"{a},{b}" for a, b in (proj(*c) for c in p.exterior.coords)) + "Z")
    return "".join(d)
mapa = "".join(path(g.simplify(0.3), P) for g in mundo.values())
for p in paises:
    if p["en"]:
        c = mundo[p["en"]].representative_point() if p["en"] not in ("France", "United States of America", "Norway", "Russia") else None
        pt = {"France": (2.3, 46.6), "United States of America": (-98, 39), "Norway": (9.5, 61), "Russia": (45, 56)}.get(p["en"])
        p["xy"] = P(*(pt or (c.x, c.y)))
paises = [{k: v for k, v in p.items() if k != "en"} for p in paises]

esp = topo_polys("countries-50m.json", {"Spain", "Portugal", "France", "Morocco", "Andorra"})
BB = box(-10, 35.0, 4.6, 44.2)
SW, SH = 560, 470
SX = lambda lon, lat: (round((lon + 10) / 14.6 * SW, 1), round((44.2 - lat) / 9.2 * SH, 1))
espana = {n: path(g.intersection(BB).simplify(0.02), SX) for n, g in esp.items()}
for c in ccaa:
    c["xy"] = SX(*c["p"]) if c["n"] != "Canarias" else (40, SH - 30)
out = {"ano": ANO, "galicia": P(*GALICIA), "galiciaE": SX(*GALICIA), "paises": paises, "ccaa": ccaa,
       "total": {"ei": round(inm["Total"][ANO]), "ee": round(emi["Total"][ANO]), "si": round(i2[(ANO, "Resto de España")]), "se": round(e2[(ANO, "Resto de España")])},
       "serie": serie, "mundo": mapa, "mundoH": round((y0 - equal_earth(0, -58)[1]) * xs), "espana": espana}
(DATA / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json", (DATA / "datos.json").stat().st_size // 1024, "KB")

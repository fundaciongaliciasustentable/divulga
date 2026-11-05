#!/usr/bin/env python3
"""As rías que traballan: extrae as capas e as cifras da peza.

Uso (precisa shapely):  python3 fontes/rias-que-traballan/prep.py

Descarga en data/raw/ o que falte (non vai ao git):
  · mgs/<capa>/data.geojson e meta.json, de https://mapas.galiciasustentable.org/data/<capa>/
    (zonas-producion-moluscos, inundacion-costeira, lonxas-2025, estado-masas-auga)
  · pescadegalicia/pescafresca2025.csv  notas de primeira venda 2025 (Consellería do Mar)
  · pescadegalicia/acuicultura.csv      produción de acuicultura 2003-2025 (Consellería do Mar)

Escribe:
  · v/rias-que-traballan/capas/{zonas,bateas,lonxas,augas,inundacion}.geojson (< 200 KB cada unha)
  · v/rias-que-traballan/thumb.svg
  · fontes/rias-que-traballan/data/cifras.json (todas as cifras calculadas que cita a peza)
"""
import csv
import json
import math
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

from shapely.geometry import mapping, shape
from shapely.ops import unary_union

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
RAW = AQUI / "data" / "raw"
SAIDA = RAIZ / "v" / "rias-que-traballan"
CAPAS = SAIDA / "capas"
MGS = "https://mapas.galiciasustentable.org/data/{}/{}"
PF = "https://www.pescadegalicia.gal/descargas/pescafresca/pescafresca2025.csv"
ACUI = "https://www.pescadegalicia.gal/descargas/acuicultura/acuicultura.csv"


def baixa(url, dest):
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        print("descargando", url)
        urllib.request.urlretrieve(url, dest)
    return dest


def capa(nome):
    for f in ("data.geojson", "meta.json"):
        baixa(MGS.format(nome, f), RAW / "mgs" / nome / f)
    return json.loads((RAW / "mgs" / nome / "data.geojson").read_text(encoding="utf-8"))


def redondea(o, n=5):
    if isinstance(o, float):
        return round(o, n)
    if isinstance(o, (list, tuple)):
        return [redondea(x, n) for x in o]
    return o


def xeom(g, tol):
    s = shape(g).simplify(tol, preserve_topology=True)
    if s.is_empty:
        return None
    m = mapping(s)
    return {"type": m["type"], "coordinates": redondea(m["coordinates"], 4 if tol >= 3e-4 else 5)}


def garda(nome, feats):
    CAPAS.mkdir(parents=True, exist_ok=True)
    p = CAPAS / f"{nome}.geojson"
    p.write_text(json.dumps({"type": "FeatureCollection", "features": feats},
                            ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    kb = p.stat().st_size / 1024
    print(f"{p.relative_to(RAIZ)}: {len(feats)} elementos, {kb:.0f} KB")
    assert kb < 200, p


def num(s):
    return float(s.replace(",", "."))


cifras = {}

# 1. Zonas de produción de moluscos e polígonos de bateas (Augas de Galicia, PHGC 2021-2027)
mol = capa("zonas-producion-moluscos")["features"]
zonas = [f for f in mol if f["properties"]["tipo"] == "zona"]
bateas = [f for f in mol if f["properties"]["tipo"] == "poligono_bateas"]
garda("zonas", [{"type": "Feature", "properties": {"clase": f["properties"]["clase"]},
                 "geometry": xeom(f["geometry"], 6e-4)} for f in zonas])
garda("bateas", [{"type": "Feature", "properties": {"ria": f["properties"]["ria"]},
                  "geometry": xeom(f["geometry"], 5e-5)} for f in bateas])
area_ria = Counter()
for f in bateas:
    area_ria[f["properties"]["ria"]] += f["properties"]["superficie_km2"]
cifras["zonas_producion"] = len(zonas)
cifras["zonas_por_clase"] = dict(Counter(f["properties"]["clase"] for f in zonas))
cifras["poligonos_bateas"] = len(bateas)
cifras["poligonos_por_ria"] = dict(Counter(f["properties"]["ria"] for f in bateas))
cifras["bateas_km2_total"] = round(sum(area_ria.values()), 1)
cifras["bateas_km2_por_ria"] = {k: round(v, 2) for k, v in area_ria.most_common()}

# 2. Lonxas: notas de primeira venda 2025, por lonxa e grupo (cálculo FGS)
lonx = capa("lonxas-2025")["features"]
csvp = baixa(PF, RAW / "pescadegalicia" / "pescafresca2025.csv")
grupo = defaultdict(Counter)       # lonxa → grupo → €
especie = defaultdict(Counter)     # lonxa → especie → €
esp_gal = Counter()
grupo_gal = Counter()
zona_grupo = defaultdict(Counter)
datas = set()
for r in csv.reader(csvp.open(encoding="utf-8-sig"), delimiter=";"):
    d, g, _cod, esp, _prov, zona, lonxa, _kg, imp, _pr = r
    imp = num(imp)
    grupo[lonxa][g] += imp
    especie[lonxa][esp] += imp
    esp_gal[esp] += imp
    grupo_gal[g] += imp
    zona_grupo[zona][g] += imp
    datas.add(d)
total = sum(grupo_gal.values())
cifras["primeira_venda_total_eur"] = round(total)
cifras["lonxas_con_vendas"] = len(grupo)
cifras["dias_con_vendas"] = len(datas)
cifras["grupos_galicia_eur"] = {k: round(v) for k, v in grupo_gal.most_common()}
cifras["especies_galicia_top"] = {k: round(v) for k, v in esp_gal.most_common(12)}
cifras["zona_bivalvos_eur"] = {z: round(c["Bivalvos"]) for z, c in sorted(zona_grupo.items())}
cifras["lonxas"] = {}
for l in sorted(grupo, key=lambda x: -sum(grupo[x].values())):
    t = sum(grupo[l].values())
    cifras["lonxas"][l] = {"total_eur": round(t), "bivalvos_eur": round(grupo[l]["Bivalvos"]),
                           "peixes_eur": round(grupo[l]["Peixes"]),
                           "especies_top": {k: round(v) for k, v in especie[l].most_common(4)}}
for e in ("Percebe", "Polbo", "Pescada", "Ameixa xaponesa", "Berberecho"):
    tot = Counter({l: especie[l][e] for l in especie if especie[l][e]})
    cifras[f"especie_{e}"] = {"galicia_eur": round(esp_gal[e]),
                              "top": {k: round(v) for k, v in tot.most_common(5)}}

feats = []
for f in lonx:
    p = f["properties"]
    if p["ambito"] != "lonxa" or not f["geometry"]:
        continue
    l = p["lonxa"]
    nome = p["nome"].rstrip(".")
    feats.append({"type": "Feature",
                  "properties": {"n": nome, "t": round(p["importe_total"] / 1e6, 2),
                                 "b": round(grupo[l]["Bivalvos"] / 1e6, 2)},
                  "geometry": {"type": "Point", "coordinates": redondea(f["geometry"]["coordinates"], 4)}})
garda("lonxas", feats)

# 3. Mexillón de acuicultura (Pesca de Galicia), 2025
acsv = baixa(ACUI, RAW / "pescadegalicia" / "acuicultura.csv")
for r in csv.reader(acsv.open(encoding="utf-8-sig"), delimiter=";"):
    if r[0] == "2025" and r[3] == "Mexillón":
        cifras["mexillon_2025_kg"] = round(num(r[4]))
        cifras["mexillon_2025_eur"] = round(num(r[5]))

# 4. Estado das masas de auga costeiras e de transición (PHGC 2021-2027)
masas = capa("estado-masas-auga")["features"]
aug = []
cont = defaultdict(Counter)
for f in masas:
    p = f["properties"]
    cat = p["categoria"]
    if cat not in ("costeira", "transicion") or p["natureza"] != "natural":
        continue
    cont[cat][p["estado_global"]] += 1
    aug.append({"type": "Feature",
                "properties": {"c": cat, "e": 0 if p["estado_global"] == "peor que bo" else 1},
                "geometry": xeom(f["geometry"], 8e-4 if cat == "costeira" else 2e-4)})
garda("augas", aug)
cifras["augas_naturais"] = {k: dict(v) for k, v in cont.items()}
cifras["augas_peor_que_bo"] = sorted(f["properties"]["nome"] for f in masas
                                     if f["properties"]["categoria"] in ("costeira", "transicion")
                                     and f["properties"]["natureza"] == "natural"
                                     and f["properties"]["estado_global"] == "peor que bo")

# 5. Zonas inundables costeiras, período de retorno de 100 anos
inu = capa("inundacion-costeira")["features"]
t100 = [f for f in inu if f["properties"]["periodo_retorno"] == 100]
garda("inundacion", [{"type": "Feature", "properties": {},
                      "geometry": xeom(f["geometry"], 2e-5)} for f in t100])
cifras["inundacion_t100_tramos"] = len(t100)
cifras["inundacion_t100_km2"] = round(sum(f["properties"]["superficie_km2"] for f in t100), 1)
cifras["inundacion_t100_km2_por_zona"] = {f["properties"]["zona"]: f["properties"]["superficie_km2"]
                                         for f in sorted(t100, key=lambda f: -f["properties"]["superficie_km2"])}
cifras["inundacion_cota_max_m"] = [min(f["properties"]["cota_max_m"] for f in t100),
                                   max(f["properties"]["cota_max_m"] for f in t100)]

(AQUI / "data" / "cifras.json").write_text(json.dumps(cifras, ensure_ascii=False, indent=1), encoding="utf-8")
print(AQUI / "data" / "cifras.json")

# 6. Miniatura 600×600: costa das Rías Baixas, polígonos de bateas e lonxas
W = 600
X0, X1, Y0, Y1 = -9.32, -8.50, 42.14, 42.92
LAT = math.cos(math.radians(42.5))
esc = W / max((X1 - X0) * LAT, (Y1 - Y0))
dx = (W - (X1 - X0) * LAT * esc) / 2


def pt(x, y):
    return f"{(x - X0) * LAT * esc + dx:.0f},{(Y1 - y) * esc:.0f}"


def camiño(geom):
    s = shape(geom)
    pol = getattr(s, "geoms", [s])
    out = []
    for p in pol:
        for anel in [p.exterior, *p.interiors]:
            c = list(anel.coords)
            out.append("M" + "L".join(pt(*q[:2]) for q in c) + "Z")
    return "".join(out)


contorno = json.loads((RAIZ / "assets" / "terreo" / "galicia-contorno.geojson").read_text())
liñas = []
for ft in contorno["features"]:
    g = shape(ft["geometry"]).simplify(0.003)
    for ln in getattr(g, "geoms", [g]):
        c = [q for q in ln.coords]
        liñas.append("M" + "L".join(pt(*q[:2]) for q in c))
bat = unary_union([shape(f["geometry"]).buffer(0).simplify(0.0002).buffer(0) for f in bateas])
circ = []
for f in feats:
    x, y = f["geometry"]["coordinates"]
    if X0 <= x <= X1 and Y0 <= y <= Y1:
        r = 2.5 + 2.2 * math.sqrt(f["properties"]["t"])
        cx, cy = pt(x, y).split(",")
        circ.append(f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}"/>')
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {W}" width="{W}" height="{W}">'
       f'<rect width="{W}" height="{W}" fill="#0e1012"/>'
       f'<path d="{"".join(liñas)}" fill="none" stroke="#f2f0e8" stroke-opacity=".7" stroke-width="1.4"/>'
       f'<path d="{camiño(mapping(bat))}" fill="#f2c14e" fill-rule="evenodd"/>'
       f'<g fill="none" stroke="#e8794a" stroke-width="2">{"".join(circ)}</g></svg>')
(SAIDA / "thumb.svg").write_text(svg, encoding="utf-8")
print(f"thumb.svg: {len(svg) / 1024:.0f} KB")

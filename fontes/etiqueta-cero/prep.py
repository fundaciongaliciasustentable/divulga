#!/usr/bin/env python3
"""Vehículos con etiqueta CERO en cada concello galego, 2020-2025 → data/datos.json

Reformulación: a peza pedía tamén o autoconsumo solar por concello, pero non hai ningunha fonte
oficial que o publique a ese nivel. O rexistro galego (procedemento IN407B da Consellería de
Economía) non ten datos abertos, e o Rexistro administrativo de autoconsumo do Ministerio só se
difunde agregado. A peza queda co parque de vehículos da DGT, que si é municipal e oficial.

Fonte (gárdase en data/raw/ se falta):
  DatosMunicipalesGeneral_<ano>.xlsx  DGT, «DGT en cifras» → «Datos municipales – información
        general», un Excel por ano co parque de vehículos de cada municipio de España a 31 de
        decembro: por tipo de vehículo, por propulsión e por distintivo ambiental (B, C, ECO, 0 e
        sen distintivo), coa poboación de cada municipio.
        https://www.dgt.es/menusecundario/dgt-en-cifras/dgt-en-cifras-resultados/dgt-en-cifras-detalle/Datos-municipales-informacion-general-2025/
        https://www.dgt.es/export/sites/web-DGT/.galleries/downloads/dgt-en-cifras/informacion_municipal/Datos-municipales-general/DatosMunicipalesGeneral_<ano>.xlsx
Xeometría: concellos de galicia-agora (data-out/concellos-parroquias/data.geojson): centroide de
cada concello e contorno das provincias. Fusións: Oza-Cesuras (15902 = 15026 + 15063) e
Cerdedo-Cotobade (36902 = 36011 + 36012). Necesita openpyxl e shapely.
"""
import json
from collections import defaultdict
from pathlib import Path
from urllib.request import Request, urlopen

import openpyxl
from shapely.geometry import shape
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
CONCELLOS = Path("/Users/perezgulin/Proxectos/galicia-agora/data-out/concellos-parroquias/data.geojson")
URL = ("https://www.dgt.es/export/sites/web-DGT/.galleries/downloads/dgt-en-cifras/informacion_municipal/"
       "Datos-municipales-general/DatosMunicipalesGeneral_{}.xlsx")
ANOS = list(range(2020, 2026))
FUSIONS = {"15902": ["15026", "15063"], "36902": ["36011", "36012"]}
VELLO = {v: k for k, vs in FUSIONS.items() for v in vs}
CAMPOS = {"pob": "Población Total", "par": "Parque Total", "tur": "Parque Turismos", "el": "Electrificado",
          "z": "Distintivo 0", "eco": "Distintivo ECO"}
RAW.mkdir(parents=True, exist_ok=True)

# Xeometría
X0, Y1, KX = -9.4, 43.9, 0.7325  # KX = cos(42,9°); unidades: 1/1000 de grao de latitude
pr = lambda lon, lat: [round((lon - X0) * KX * 1000), round((Y1 - lat) * 1000)]
fs = [f for f in json.loads(CONCELLOS.read_text(encoding="utf-8"))["features"] if f["properties"]["nivel"] == "concello"]
geo, porprov = {}, defaultdict(list)
for f in fs:
    p = f["properties"]
    g = shape(f["geometry"]).buffer(0)
    geo[p["codigo_ine"]] = {"pr": p["provincia"], "xy": pr(*g.representative_point().coords[0])}
    porprov[p["provincia"]].append(g)
provs = {}
for n, gs in porprov.items():
    u = unary_union(gs).simplify(0.004)
    provs[n] = [[pr(x, y) for x, y in q.exterior.coords] for q in getattr(u, "geoms", [u]) if q.area > 1e-4]

conc = {c: {"id": c, "n": None, **geo[c], **{k: [0] * len(ANOS) for k in CAMPOS}} for c in geo}
ccaa = defaultdict(lambda: {k: [0] * len(ANOS) for k in CAMPOS})
for i, a in enumerate(ANOS):
    f = RAW / f"DatosMunicipalesGeneral_{a}.xlsx"
    if not f.exists():
        f.write_bytes(urlopen(Request(URL.format(a), headers={"User-Agent": "Mozilla/5.0"}), timeout=300).read())
        print("descargado", f.name)
    rows = list(openpyxl.load_workbook(f, read_only=True).active.iter_rows(values_only=True))
    ix = {h: j for j, h in enumerate(rows[0])}
    for r in rows[1:]:
        if not r[0] or not r[3]:
            continue
        for k, h in CAMPOS.items():
            ccaa[r[3]][k][i] += r[ix[h]] or 0
        c = VELLO.get(str(r[0]), str(r[0]))
        if c not in conc:
            if r[3] == "Galicia" and not str(r[0]).endswith("000"):
                print("AVISO: código sen xeometría", a, r[0], r[1])
            continue
        if a == ANOS[-1]:
            n = r[1].split(", ")
            conc[c]["n"] = f"{n[1]} {n[0]}" if len(n) == 2 and n[1] in ("A", "O", "As", "Os") else r[1]
        for k, h in CAMPOS.items():
            conc[c][k][i] += r[ix[h]] or 0
# a poboación dos municipios «sen especificar» é nula, pero os seus vehículos van no total da comunidade
C = sorted(conc.values(), key=lambda c: c["n"])
assert all(c["n"] for c in C)
CC = {n: v for n, v in ccaa.items() if v["pob"][-1]}
esp = {k: [sum(v[k][i] for v in CC.values()) for i in range(len(ANOS))] for k in CAMPOS}
por = lambda d, i=-1: d["z"][i] / d["pob"][i] * 1000
for n, v in sorted(CC.items(), key=lambda x: -por(x[1])):
    print(f"  {n:28} {por(v):5.1f} CERO/1.000 hab · {v['z'][-1]:7,} ({v['z'][0]:,} en {ANOS[0]})")
print(f"  {'España':28} {por(esp):5.1f}")
g = CC["Galicia"]
print("Galicia:", [round(por(g, i), 1) for i in range(len(ANOS))])
for c in sorted(C, key=lambda c: -por(c))[:10]:
    print(f"  {c['n']:26} {por(c):6.1f} · {c['z'][-1]} CERO · {c['pob'][-1]} hab · eléctricos puros {c['el'][-1]}")
out = {"anos": ANOS, "conc": C, "provs": provs, "ccaa": CC, "esp": esp}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json", (HERE / "data" / "datos.json").stat().st_size // 1024, "KB")

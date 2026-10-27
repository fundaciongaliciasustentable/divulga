#!/usr/bin/env python3
"""Superficie queimada diaria en Galicia, 1983-hoxe → data/datos.json

Fontes (en data/):
  firespain025.nc     FIRESPAIN-025 (Zenodo 14644902): EGIF diaria en grella de 0,25°, 1983-2021
  effis_galicia.gml   EFFIS modis.ba.poly (WFS), área queimada por satélite, 2016-. Descarga:
      curl -o data/effis_galicia.gml "https://maps.effis.emergency.copernicus.eu/effis?service=WFS&request=GetFeature&typename=ms:modis.ba.poly&version=1.1.0&srsName=EPSG:4326&BBOX=41.8,-9.35,43.8,-6.7,EPSG:4326&propertyName=FIREDATE,FINALDATE,COUNTRY,PROVINCE,COMMUNE,AREA_HA"
  galicia.geojson     contorno de Galicia (xérase a primeira vez desde os concellos)

Cada cela da grella pondérase pola fracción da súa área que cae dentro de Galicia.
Necesita netCDF4, numpy e shapely.
"""
import json
import re
from datetime import date, timedelta
from pathlib import Path

import netCDF4
import numpy as np
from shapely.geometry import box, shape, mapping
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
CONCELLOS = Path("/Users/perezgulin/Proxectos/galicia-agora/data-out/concellos-parroquias/data.geojson")
PROVS = {"A Coruña", "Lugo", "Ourense", "Pontevedra"}
EGIF_ATA = 2016  # FIRESPAIN chega a 2021, pero en Galicia só é completo ata 2016 (EGIF definitiva);
                 # dende 2017 úsase EFFIS (satélite, lumes de ≳30 ha)

# Contorno de Galicia
gpath = DATA / "galicia.geojson"
if not gpath.exists():
    fs = json.loads(CONCELLOS.read_text(encoding="utf-8"))["features"]
    gal = unary_union([shape(f["geometry"]).buffer(0) for f in fs if f["properties"]["nivel"] == "concello"])
    gal = gal.simplify(0.002)
    gpath.write_text(json.dumps({"type": "Feature", "properties": {}, "geometry": mapping(gal)}))
gal = shape(json.loads(gpath.read_text())["geometry"])

# EGIF (FIRESPAIN-025)
nc = netCDF4.Dataset(DATA / "firespain025.nc")
lon, lat = nc["longitude"][:], nc["latitude"][:]
h = 0.125  # coordenadas = centro da cela
w = np.zeros((len(lat), len(lon)))
for i, la in enumerate(lat):
    for j, lo in enumerate(lon):
        c = box(lo - h, la - h, lo + h, la + h)
        if c.intersects(gal):
            w[i, j] = c.intersection(gal).area / c.area
ii, jj = np.nonzero(w)
ba = nc["ba"][:, ii.min():ii.max() + 1, jj.min():jj.max() + 1].filled(0)
diario = (ba * w[ii.min():ii.max() + 1, jj.min():jj.max() + 1]).sum(axis=(1, 2))
t0 = date(1983, 1, 1)
egif = {}
for k, v in zip(nc["time"][:], diario):
    if v > 0:
        egif[(t0 + timedelta(days=int(k))).isoformat()] = float(v)
print("celas con peso:", len(ii), " días:", len(nc["time"]), "→", (t0 + timedelta(days=int(nc["time"][-1]))).isoformat())

# EFFIS
gml = (DATA / "effis_galicia.gml").read_text(encoding="utf-8")
effis, lumes = {}, []
for m in re.finditer(r"<ms:modis\.ba\.poly .*?</ms:modis\.ba\.poly>", gml, re.S):
    f = dict(re.findall(r"<ms:(\w+)>([^<]*)</ms:\1>", m.group(0)))
    if f.get("COUNTRY") != "ES" or f.get("PROVINCE") not in PROVS:
        continue
    d, ha = f["FIREDATE"][:10], float(f["AREA_HA"])
    effis[d] = effis.get(d, 0) + ha
    c = f["COMMUNE"]
    if ", " in c:  # «Rúa, A» → «A Rúa»
        n, art = c.rsplit(", ", 1)
        c = f"{art} {n}"
    lumes.append((ha, d, c, f["PROVINCE"]))


def anual(serie):
    out = {}
    for d, v in serie.items():
        out[int(d[:4])] = out.get(int(d[:4]), 0) + v
    return out


ae, af = anual(egif), anual(effis)
comp = [{"y": y, "egif": round(ae.get(y, 0)), "effis": round(af.get(y, 0))} for y in range(2016, 2022)]
for c in comp:
    print("comparación", c)

anos = []
for y in range(1983, max(af) + 1):
    src, serie = ("egif", egif) if y <= EGIF_ATA else ("effis", effis)
    dias = []
    for d, v in sorted(serie.items()):
        if int(d[:4]) == y and v >= 0.5:
            doy = (date.fromisoformat(d) - date(y, 1, 1)).days
            dias.append([doy, round(v)])
    tot = sum(v for _, v in dias)
    anos.append({"y": y, "src": src, "tot": tot, "d": dias})
    print(y, src, f"{tot:>9,} ha", len(dias), "días")

ultimo = max(effis)
out = {"anos": anos, "comp": comp, "ultimoEFFIS": ultimo,
       "maiores": [{"ha": round(a), "d": d, "c": c, "p": p} for a, d, c, p in sorted(lumes, reverse=True)[:12]]}
(DATA / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json · último EFFIS", ultimo)

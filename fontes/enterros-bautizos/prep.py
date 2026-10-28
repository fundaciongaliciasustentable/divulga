#!/usr/bin/env python3
"""Nacementos e defuncións de cada concello galego, 1975-2025 → data/datos.json

Fonte (descárgase en data/raw/ se falta):
  ige_227.csv  IGE e INE, Movemento natural da poboación: «Nacementos, defuncións, matrimonios e
               crecemento vexetativo. Galicia, provincias, comarcas e concellos. Serie 1975-2025»,
               segundo o concello de residencia. Os datos de 2025 son provisionais.
               https://www.ige.gal/igebdt/igeapi/csv/datos/227/1:0:1
Cartograma: as posicións dos hexágonos (un por concello) son as da peza vacas-persoas
(fontes/vacas-persoas/data/datos.json, asignación óptima ao centro real de cada concello).
Os concellos fusionados (Oza-Cesuras 2013, Cerdedo-Cotobade 2016) súmanse nos anos anteriores.
"""
import csv
import io
import json
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
FUSIONS = {"15902": ["15026", "15063"], "36902": ["36011", "36012"]}
VELLO = {v: k for k, vs in FUSIONS.items() for v in vs}
f = RAW / "ige_227.csv"
if not f.exists():
    f.write_bytes(urlopen(Request("https://www.ige.gal/igebdt/igeapi/csv/datos/227/1:0:1",
                                  headers={"User-Agent": "Mozilla/5.0"}), timeout=300).read())
vp = json.loads((HERE.parent / "vacas-persoas" / "data" / "datos.json").read_text(encoding="utf-8"))["concellos"]
ids = {o["id"] for o in vp}

nac, dfn = {}, {}
for x in csv.DictReader(io.StringIO(f.read_bytes().decode("latin1"))):
    c = VELLO.get(x["CodEspazo"], x["CodEspazo"])
    if not (c in ids or c == "12") or x["DatoN"] == "":
        continue
    d = nac if x["Movemento natural da poboación"] == "Nacementos" else dfn if x["Movemento natural da poboación"] == "Defuncións" else None
    if d is None:
        continue
    a = int(x["CodTempo"])
    d.setdefault(c, {})
    d[c][a] = d[c].get(a, 0) + int(float(x["DatoN"]))
anos = sorted({a for s in nac.values() for a in s})
print("anos:", anos[0], "-", anos[-1], "· columnas:", list(x.keys()))
ULT = anos[-1]
U5 = anos[-5:]

conc = []
for o in vp:
    c = o["id"]
    conc.append({"id": c, "n": o["n"], "pr": o["pr"], "h": o["h"],
                 "b": [nac[c].get(a, 0) for a in anos], "d": [dfn[c].get(a, 0) for a in anos]})
gal = {"b": [nac["12"][a] for a in anos], "d": [dfn["12"][a] for a in anos]}
i5 = [anos.index(a) for a in U5]
r5 = lambda o: sum(o["b"][i] for i in i5) / max(1, sum(o["d"][i] for i in i5))
mais = [sum(1 for o in conc if o["d"][i] > o["b"][i]) for i in range(len(anos))]
print("concellos con máis defuncións ca nacementos por ano:", dict(zip(anos, mais)))
print(ULT, "Galicia:", gal["b"][-1], "nacementos,", gal["d"][-1], "defuncións")
print("media", U5[0], "-", U5[-1], ": concellos con < 1 nacemento por defunción:", sum(1 for o in conc if r5(o) < 1))
r = sorted(conc, key=r5)
print("menos:", [(o["n"], round(r5(o), 2)) for o in r[:6]])
print("máis:", [(o["n"], round(r5(o), 2)) for o in r[-6:]])
out = {"anos": anos, "u5": [U5[0], U5[-1]], "gal": gal, "conc": sorted(conc, key=lambda o: o["n"])}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json", (HERE / "data" / "datos.json").stat().st_size // 1024, "KB")

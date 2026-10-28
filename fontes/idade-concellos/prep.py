#!/usr/bin/env python3
"""Idade media, envellecemento e pirámide de cada concello galego → data/datos.json

Fontes (IGE, API de táboas en CSV; descárganse en data/raw/ se faltan):
  ige_723.csv  IGE, Indicadores demográficos, «Indicadores de poboación» por concello, 2002-2025:
               idade media a 1 de xaneiro (0), índice de envellecemento (3), % de menores de 20 (8)
               e % de 65 e máis anos (10), ambos os sexos.
               https://www.ige.gal/igebdt/igeapi/csv/datos/723/1:0:3:8:10,2:2
  ige_142.csv  IGE a partir do INE (Censos de poboación e vivendas; dende 2021, censo anual),
               «Poboación segundo sexo e grupos quinquenais de idade» por concello, 1/1/2025.
               https://www.ige.gal/igebdt/igeapi/csv/datos/142/0:2025,1:1:2
O índice de envellecemento do IGE é a poboación de 65 e máis anos por cada 100 menores de 20.
"""
import csv
import io
import json
import time
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
CONCELLOS = Path("/Users/perezgulin/Proxectos/galicia-agora/data-out/concellos-parroquias/data.geojson")
URLS = {"ige_723.csv": "https://www.ige.gal/igebdt/igeapi/csv/datos/723/1:0:3:8:10,2:2",
        "ige_142.csv": "https://www.ige.gal/igebdt/igeapi/csv/datos/142/0:2025,1:1:2"}
for nome, url in URLS.items():
    if not (RAW / nome).exists():
        (RAW / nome).write_bytes(urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=300).read())
        time.sleep(1)
ler = lambda n: list(csv.DictReader(io.StringIO((RAW / n).read_bytes().decode("latin1"))))

fs = [f["properties"] for f in json.loads(CONCELLOS.read_text(encoding="utf-8"))["features"] if f["properties"]["nivel"] == "concello"]
ids = {p["codigo_ine"] for p in fs}
IND = {"Idade media no 1 de xaneiro": "im", "Índice de envellecemento": "ie",
       "Porcentaxe de poboación menor de 20 anos": "p20", "Porcentaxe de poboación de 65 e máis anos": "p65"}
ind, serie = {}, {}
for x in ler("ige_723.csv"):
    c, k = x["CodEspazo"], IND.get(x["Indicadores"])
    if not k or x["DatoN"] == "" or not (c in ids or c in ("12", "15", "27", "32", "36")):
        continue
    a, v = int(x["CodTempo"]), float(x["DatoN"])
    if k == "im":
        serie.setdefault(c, {})[a] = v
    if a == 2025:
        ind.setdefault(c, {})[k] = v
ANO0 = min(min(s) for s in serie.values())

# Pirámide: grupos quinquenais (0-4 … 85-89 e «90 e máis»; os subgrupos de 90+ descártanse)
pir, grupos = {}, []
for x in ler("ige_142.csv"):
    c, g = x["CodEspazo"], x["Grupos de idade"]
    if g in ("Total", "90-94", "95-99", "100 e máis") or not (c in ids or c == "12") or x["DatoN"] == "":
        continue
    if g not in grupos:
        grupos.append(g)
    s = 0 if x["Sexo"] == "Homes" else 1
    pir.setdefault(c, [[0] * 30, [0] * 30])[s][grupos.index(g)] = int(float(x["DatoN"]))
print("grupos:", grupos)

conc = []
for p in fs:
    c = p["codigo_ine"]
    i = ind[c]
    h, m = (v[:len(grupos)] for v in pir[c])
    conc.append({"id": c, "n": p["nome"], "pr": p["provincia"], **{k: round(v, 2) for k, v in i.items()},
                 "im0": serie[c].get(ANO0), "h": h, "m": m})
gal = {**ind["12"], "im0": serie["12"][ANO0], "h": pir["12"][0][:len(grupos)], "m": pir["12"][1][:len(grupos)]}
prov = {n: {**ind[c], "im0": serie[c][ANO0]} for c, n in (("15", "A Coruña"), ("27", "Lugo"), ("32", "Ourense"), ("36", "Pontevedra"))}
r = sorted(conc, key=lambda o: o["im"])
print("Galicia:", gal["im"], gal["ie"], "en", ANO0, gal["im0"])
print("máis novos:", [(o["n"], o["im"], o["ie"]) for o in r[:6]])
print("máis vellos:", [(o["n"], o["im"], o["ie"]) for o in r[-6:]])
print("ie > 300:", sum(1 for o in conc if o["ie"] > 300), "· ie<100:", sum(1 for o in conc if o["ie"] < 100))
print("idade media > 60:", sum(1 for o in conc if o["im"] >= 60))
out = {"ano": 2025, "ano0": ANO0, "grupos": grupos, "gal": gal, "prov": prov, "conc": sorted(conc, key=lambda o: o["n"])}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json", (HERE / "data" / "datos.json").stat().st_size // 1024, "KB")

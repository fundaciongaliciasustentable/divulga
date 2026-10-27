#!/usr/bin/env python3
"""Que apelidos son máis galegos: parte dos que levan cada apelido que vive en Galicia → data/datos.json

Fontes (INE, datos a 1 de xaneiro de 2025):
  · apellidos_frecuencia.xls: todos os apelidos con 100 ou máis persoas como primeiro apelido
    https://www.ine.es/daco/daco42/nombyapel/apellidos_frecuencia.xls
  · para cada apelido, a frecuencia por mil habitantes en cada provincia (o que pinta o mapa do
    buscador do INE): https://www.ine.es/apellidos/mapaWidget?apellido=OTERO&tipo=1
  · poboación das catro provincias galegas a 1/1/2025 (padrón, táboas 2868, 2880, 2885 e 2890) e a
    correspondencia dos códigos de provincia do INE (variable 115).
Pídese o mapa de todos os apelidos con polo menos MIN persoas como primeiro apelido; as respostas
gárdanse en data/raw/mapas.jsonl e a descarga retoma onde quedou.

Persoas en Galicia = suma nas catro provincias de (‰ da provincia) × poboación / 1000. A parte
galega é iso entre o total de España dese primeiro apelido (o do ficheiro nacional).
"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock
from urllib.parse import quote
from urllib.request import Request, urlopen

import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
MIN = 1000
GAL = {"15": "A Coruña", "27": "Lugo", "32": "Ourense", "36": "Pontevedra"}
UA = {"User-Agent": "Mozilla/5.0"}


def baixa(nome, url):
    f = RAW / nome
    if not f.exists():
        RAW.mkdir(parents=True, exist_ok=True)
        f.write_bytes(urlopen(Request(url, headers=UA), timeout=180).read())
    return f


xls = baixa("apellidos_frecuencia.xls", "https://www.ine.es/daco/daco42/nombyapel/apellidos_frecuencia.xls")
nac = pd.read_excel(xls, "Apellidos >=100", header=None, skiprows=5, engine="xlrd").iloc[:, :5]
nac.columns = ["orde", "ap", "f1", "f2", "f12"]
nac = nac.dropna(subset=["ap"])
nac["f1"] = nac["f1"].astype(int)
cand = nac[nac["f1"] >= MIN]

var = json.loads(baixa("ine_var115.json", "https://servicios.ine.es/wstempus/js/ES/VALORES_VARIABLE/115").read_text())
cod = {x["Id"]: (x["Codigo"], x["Nombre"]) for x in var}
TAB = {"15": 2868, "27": 2880, "32": 2885, "36": 2890}
pob = {}
for c, t in TAB.items():
    d = json.loads(baixa(f"ine_{t}.json", f"https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{t}?nult=1").read_text())
    s_ = next(x for x in d if x["Nombre"].startswith(("Coruña, A.", "Lugo.", "Ourense.", "Pontevedra.")) and ". Total." in x["Nombre"])
    pob[c] = s_["Data"][0]["Valor"]
print("poboación 2025:", pob)

# Mapas por apelido, con caché nunha liña JSON por apelido
mapas_f = RAW / "mapas.jsonl"
feitos = {}
if mapas_f.exists():
    for l in mapas_f.read_text(encoding="utf-8").splitlines():
        x = json.loads(l)
        feitos[x["ap"]] = x["r"]
lock = Lock()


def pide(ap):
    if ap in feitos:
        return
    url = f"https://www.ine.es/apellidos/mapaWidget?apellido={quote(ap)}&tipo=1"
    for intento in range(4):
        try:
            r = json.loads(urlopen(Request(url, headers=UA), timeout=60).read())["regiones"]
            break
        except Exception:
            if intento == 3:
                r = None
            time.sleep(3 * (intento + 1))
    with lock:
        feitos[ap] = r
        with mapas_f.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ap": ap, "r": r}, ensure_ascii=False) + "\n")
        if len(feitos) % 200 == 0:
            print(len(feitos), "de", len(cand), flush=True)
    time.sleep(0.15)


if "--parcial" not in sys.argv:  # --parcial: só co xa descargado, para probar a páxina
    with ThreadPoolExecutor(2) as ex:
        list(ex.map(pide, cand["ap"]))
if "--so-descarga" in sys.argv:
    sys.exit()

POB_GAL = sum(pob.values())
POB_ES = 49_128_297  # 1/1/2025, INE (Estatística continua de poboación)
nomes = {c: n for c, n in cod.values() if c.isdigit() and len(c) == 2}
out = []
for _, x in cand.iterrows():
    r = feitos.get(x["ap"])
    if not r:
        continue
    pm = {}
    for g in r:
        c, _n = cod.get(g["id"], (None, None))
        if c and c.isdigit() and len(c) == 2:
            pm[c] = g["val"]
    gal = {c: pm.get(c, 0) * pob[c] / 1000 for c in GAL}
    sg = sum(gal.values())
    out.append({"a": x["ap"], "n": int(x["f1"]), "g": round(min(1, sg / x["f1"]), 4), "ng": round(sg),
                "pm": {c: pm.get(c, 0) for c in GAL}, "pmE": next((g["val"] for g in r if g["id"] == 16473), None),
                "t": sorted(([c, v] for c, v in pm.items()), key=lambda kv: -kv[1])[:5]})
out.sort(key=lambda x: -x["g"] * x["n"])
print("apelidos:", len(out), "· parte de Galicia na poboación:", round(POB_GAL / POB_ES, 4))
for x in sorted(out, key=lambda x: -x["g"])[:25]:
    print(f"{x['a']:14} {x['n']:>7}  {x['g']:.1%}")
(HERE / "data" / "datos.json").write_text(json.dumps(
    {"ap": out, "min": MIN, "pobGal": round(POB_GAL / POB_ES, 4), "prov": nomes, "data": "2025-01-01"},
    ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json")

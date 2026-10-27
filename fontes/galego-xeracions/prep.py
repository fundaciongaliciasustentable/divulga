#!/usr/bin/env python3
"""Lingua habitual por idade, 2003-2023, e transmisión desde a nai → data/datos.json

Fonte: IGE, Enquisa de condicións de vida das familias, módulo de coñecemento e uso do galego
(poboación de 5 e máis anos), táboas descargadas da API do IGE en data/ (descárganse se faltan):
  2953  persoas segundo a lingua na que falan habitualmente, por idade (Galicia e provincias)
  7018  lingua de fala habitual dos fillos segundo a lingua de fala habitual da nai
"""
import csv
import json
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
URL = "https://www.ige.gal/igebdt/igeapi/csv/datos/{}"
L = ["En galego sempre", "Máis galego ca castelán", "Máis castelán ca galego", "En castelán sempre"]
IDADES = ["De 5 a 14 anos", "De 15 a 29 anos", "De 30 a 49 anos", "De 50 a 64 anos", "De 65 ou máis anos"]


def taboa(cod):
    f = DATA / f"ige_{cod}.csv"
    if not f.exists():
        f.write_bytes(urlopen(Request(URL.format(cod), headers={"User-Agent": "Mozilla/5.0"}), timeout=300).read())
    return [{k: (v or "").strip() for k, v in x.items()} for x in csv.DictReader(f.open(encoding="latin1"))]


r = taboa(2953)
anos = sorted({x["Tempo"] for x in r})
esp = ["12 Galicia", "15 A Coruña", "27 Lugo", "32 Ourense", "36 Pontevedra"]
pob = {}
for e in esp:
    pob[e[3:]] = {}
    for y in anos:
        pob[e[3:]][y] = []
        for a in IDADES:
            n = {x["Lingua na que fala habitualmente"]: float(x["DatoN"] or 0) for x in r
                 if x["Espazo"] == e and x["Tempo"] == y and x["Idade"] == a and x["Medidas"] == "Número"}
            pob[e[3:]][y].append([round(n.get(l, 0)) for l in L])

nai = {}
for x in taboa(7018):
    if x["Medidas"] != "Porcentaxe" or x["Lingua que fala habitualmente a súa nai"] not in L or x["Lingua na que fala habitualmente"] not in L:
        continue
    nai.setdefault(x["Tempo"], {}).setdefault(x["Lingua que fala habitualmente a súa nai"], {})[x["Lingua na que fala habitualmente"]] = float(x["DatoN"])
nai = {y: [[round(v[m].get(l, 0), 1) for l in L] for m in L] for y, v in nai.items()}

for y in (anos[0], anos[-1]):
    g = pob["Galicia"][y]
    print(y, [f"{a[:8]} {c[0] / sum(c):.0%} sempre galego" for a, c in zip(IDADES, g)])
print("nai galego sempre → fillos galego sempre:", {y: v[0][0] for y, v in nai.items()})
out = {"anos": anos, "idades": IDADES, "linguas": L, "pob": pob, "nai": nai}
(DATA / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json")

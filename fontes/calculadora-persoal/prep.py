#!/usr/bin/env python3
"""Series anuais para a calculadora «Dende que naciches» → data/datos.json

Non descarga nada: reúne as series xa preparadas noutras pezas de Divulga (o seu data/datos.json):
  · espiral-lumes: hectáreas queimadas en Galicia cada ano (EGIF ata 2016, EFFIS dende 2017), 1983-
  · raias-clima: anomalía da temperatura media anual en seis observatorios de AEMET, dende 1931
  · ondas-atlantico: temperatura media anual do mar fronte ás Rías Baixas (NOAA OISST), dende 1982
  · galicia-apagandose: poboación de cada entidade singular (aldea, lugar) do Nomenclátor do IGE,
    1999-2025; unha aldea «baleirouse» o ano en que pasa a ter 0 habitantes despois de ter algún
  · camino-compostela: peregrinos que recolleron a Compostela, dende 2004
  · nomes-galicia: os nomes máis frecuentes por década de nacemento e por ano (dende 2000)
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
F = HERE.parent
peza = lambda s: json.loads((F / s / "data" / "datos.json").read_text(encoding="utf-8"))

lu = peza("espiral-lumes")
lume = {x["y"]: x["tot"] for x in lu["anos"]}
ult_lume = max(lume)

ra = peza("raias-clima")
temp = {}
for e in ra["est"]:
    for s in e["s"]:
        if s["t"] is not None:
            temp.setdefault(s["y"], []).append(s["t"])
# media das estacións con dato; só anos con polo menos dúas estacións
temp = {a: round(sum(v) / len(v), 3) for a, v in temp.items() if len(v) >= 2}

on = peza("ondas-atlantico")
mar = {x["a"]: x["m"] for x in on["anos"]}

ap = peza("galicia-apagandose")
anos_ap = ap["anos"]
baleiras = {a: 0 for a in anos_ap}   # aldeas que pasan a 0 habitantes ese ano
for e in ap["e"]:
    cod = e[4]
    for i in range(1, len(cod)):
        if cod[i] == "0" and cod[i - 1] not in ("0", "-"):
            baleiras[anos_ap[i]] += 1
total_baleiras = {a: sum(1 for e in ap["e"] if e[4][i] == "0") for i, a in enumerate(anos_ap)}

ca = peza("camino-compostela")
pere = {a: v for a, v in ca["serie"]}

no = peza("nomes-galicia")
nomes = {"dec": {d: [no["dec"]["12"]["H"][i][0], no["dec"]["12"]["M"][i][0]] for i, d in enumerate(no["decadas"])},
         "ano": {a: [no["anos"]["H"][a][0][0], no["anos"]["M"][a][0][0]] for a in no["anos"]["H"]}}

out = {"lume": lume, "ultLume": ult_lume, "temp": temp, "mar": mar, "baleiras": baleiras, "totBal": total_baleiras,
       "pere": pere, "nomes": nomes, "anosAp": [anos_ap[0], anos_ap[-1]]}
print("lume", min(lume), "-", ult_lume, "· temp", min(temp), "-", max(temp), "· mar", min(mar), "-", max(mar),
      "· aldeas", anos_ap[0], "-", anos_ap[-1], f"({total_baleiras[anos_ap[0]]} → {total_baleiras[anos_ap[-1]]} baleiras)",
      "· peregrinos", min(pere), "-", max(pere))
print("baleiradas por ano:", {a: v for a, v in baleiras.items() if a % 5 == 0})
(HERE / "data").mkdir(exist_ok=True)
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json")

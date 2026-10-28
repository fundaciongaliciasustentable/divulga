#!/usr/bin/env python3
"""Prazas de aloxamento turístico regrado por habitante en cada concello galego → data/datos.json

Fontes (gardadas en data/raw/):
  · Turismo de Galicia, Rexistro de Empresas e Actividades Turísticas (REAT), serie mensual de
    aloxamentos turísticos por concello e tipo (establecementos, habitacións e prazas), 2017-2026:
      https://descargascdn.xunta.gal/interno/smarxa/REAT_Serie_Mensual.csv
    publicada no Sistema de Intelixencia Turística (https://aei.turismo.gal/es/rexistro-de-empresas-e-actividades-turisticas)
    e catalogada en abertos.xunta.gal (dataset 0022, «Rexistro de empresas e actividades turísticas»).
  · INE, Padrón municipal a 1 de xaneiro de 2025, por provincia (táboas 2868, 2880, 2885, 2890):
      https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/<táboa>?nult=1&tip=AM
O REAT conta prazas inscritas (capacidade autorizada), non prazas ocupadas nin abertas todo o ano.
"""
import csv
import json
from collections import defaultdict
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
URLS = {"REAT_Serie_Mensual.csv": "https://descargascdn.xunta.gal/interno/smarxa/REAT_Serie_Mensual.csv",
        **{f"ine_{t}.json": f"https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{t}?nult=1&tip=AM" for t in (2868, 2880, 2885, 2890)}}
RAW.mkdir(parents=True, exist_ok=True)
for nome, url in URLS.items():
    if not (RAW / nome).exists():
        (RAW / nome).write_bytes(urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=600).read())
# Tipos do REAT agrupados en seis
TIPO = {"Hoteis": "h", "Pensións": "h", "Apartamentos turísticos": "a", "Turismo rural": "r", "Campamentos turísticos": "c",
        "Albergues turísticos": "b", "Vivendas de uso turístico": "v", "Vivendas turísticas": "v"}

filas = list(csv.DictReader((RAW / "REAT_Serie_Mensual.csv").open(encoding="latin1"), delimiter=";"))
assert {x["TIPO"] for x in filas} <= set(TIPO), {x["TIPO"] for x in filas} - set(TIPO)
mes = max(x["TEMPO"] for x in filas)
pr = defaultdict(lambda: defaultdict(int))     # concello → tipo → prazas (último mes)
es = defaultdict(int)                          # concello → establecementos
hist = defaultdict(lambda: defaultdict(int))   # concello → ano → prazas no mes de outubro (ou o último)
for x in filas:
    c = x["CODCON"]
    if x["TEMPO"] == mes:
        pr[c][TIPO[x["TIPO"]]] += int(x["PRAZAS"])
        es[c] += int(x["ESTABLECEMENTOS"])
    if x["TEMPO"][4:] == mes[4:]:
        hist[c][int(x["TEMPO"][:4])] += int(x["PRAZAS"])
anos = sorted({a for h in hist.values() for a in h})
print("último mes:", mes, "· anos da serie (mes", mes[4:] + "):", anos)

pob = {}
for t in (2868, 2880, 2885, 2890):
    for s in json.loads((RAW / f"ine_{t}.json").read_text()):
        md = {m["T3_Variable"]: m for m in s["MetaData"]}
        if md.get("Sexo", {}).get("Codigo") != "0" or "Municipios" not in md:
            continue
        v = [d for d in s["Data"] if d["Anyo"] == 2025 and d["Valor"] is not None]
        if v:  # os concellos desaparecidos por fusión veñen sen datos
            pob[md["Municipios"]["Codigo"]] = round(v[0]["Valor"])

mc = json.loads((HERE.parent / "monte-concellos" / "data" / "datos.json").read_text(encoding="utf-8"))
conc = []
for c in mc["concellos"]:
    i = c["id"]
    t = sum(pr[i].values())
    conc.append({"id": i, "n": c["n"], "pr": c["pr"], "hab": pob[i], "t": t, "e": es[i], "ti": dict(pr[i]),
                 "h": [hist[i].get(a, 0) for a in anos]})
assert len(conc) == 313 and not (set(pr) - {c["id"] for c in conc}), set(pr) - {c["id"] for c in conc}
T, P = sum(c["t"] for c in conc), sum(c["hab"] for c in conc)
gti = defaultdict(int)
for c in conc:
    for k, v in c["ti"].items():
        gti[k] += v
gal = {"t": T, "hab": P, "e": sum(es.values()), "ti": dict(gti), "h": [sum(c["h"][j] for c in conc) for j in range(len(anos))]}
print(f"Galicia: {T} prazas, {P} hab → {T / P * 100:.2f} por 100 hab · por tipo {dict(gti)}")
print("concellos sen ningunha praza:", [c["n"] for c in conc if c["t"] == 0])
print("máis prazas ca habitantes:", sum(c["t"] > c["hab"] for c in conc))
for c in sorted(conc, key=lambda c: -c["t"] / c["hab"])[:12]:
    print(f"  {c['n']:24} {c['t'] / c['hab'] * 100:7.1f} por 100 hab  ({c['t']} prazas, {c['hab']} hab) {c['ti']}")
(HERE / "data" / "datos.json").write_text(json.dumps({"mes": mes, "anos": anos, "pob_ano": 2025, "gal": gal, "conc": conc},
                                                     ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json", (HERE / "data" / "datos.json").stat().st_size // 1024, "KB")

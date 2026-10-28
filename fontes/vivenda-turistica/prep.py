#!/usr/bin/env python3
"""Vivendas de uso turístico por cada 100 vivendas en cada concello galego → data/datos.json

Fontes (CSV gardados en data/raw/):
  · INE, estatística experimental «Medición do número de vivendas turísticas en España e a súa
    capacidade» (https://www.ine.es/experimental/viv_turistica/experimental_viv_turistica.htm):
      táboa 39363, vivendas turísticas, prazas e prazas por vivenda, por municipio:
        https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/39363.csv
      táboa 39366, porcentaxe de vivendas turísticas sobre o total de vivendas, por municipio:
        https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/39366.csv
    O INE localiza os anuncios de Airbnb, Booking e Vrbo, quita duplicados e filtra segundo as
    normas de cada comunidade. Último dato: maio de 2026. Ata 2024 os cortes eran en febreiro e
    agosto; dende novembro de 2024, en maio e novembro.
  · INE, Censos de Poboación e Vivendas 2021, vivendas totais por municipio (táboa 59525):
        https://www.ine.es/jaxi/files/tpx/csv_bdsc/59525.csv
    É o denominador que usa o propio INE para a porcentaxe; aquí recalcúlase para comprobalo.
  · Para comparar: Turismo de Galicia, Rexistro de Empresas e Actividades Turísticas (REAT), serie
    mensual por concello (vivendas de uso turístico + vivendas turísticas rexistradas):
        https://descargascdn.xunta.gal/interno/smarxa/REAT_Serie_Mensual.csv
  · Polígonos dos concellos: os xa proxectados de monte-concellos (como en casas-baleiras).
Os dous concellos fusionados (Oza-Cesuras, Cerdedo-Cotobade) só teñen dato co código novo.
"""
import csv
import json
from collections import defaultdict
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
URLS = {"ine_39363.csv": "https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/39363.csv",
        "ine_39366.csv": "https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/39366.csv",
        "ine_59525.csv": "https://www.ine.es/jaxi/files/tpx/csv_bdsc/59525.csv",
        "REAT_Serie_Mensual.csv": "https://descargascdn.xunta.gal/interno/smarxa/REAT_Serie_Mensual.csv"}
RAW.mkdir(parents=True, exist_ok=True)
for nome, url in URLS.items():
    if not (RAW / nome).exists():
        (RAW / nome).write_bytes(urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=600).read())
num = lambda s: float(s.replace(".", "").replace(",", ".")) if s not in ("", '""', ".", "..") else None

# INE: vivendas e prazas turísticas por concello e corte
vt = defaultdict(dict)    # código → corte → {v, p}
gal_vt = {}
for r in csv.reader((RAW / "ine_39363.csv").open(encoding="utf-8-sig"), delimiter=";"):
    if len(r) < 7 or r[1] != "12 Galicia":
        continue
    k = {"Viviendas turísticas": "v", "Plazas": "p"}.get(r[4])
    if not k:
        continue
    if r[3]:
        vt[r[3][:5]].setdefault(r[5], {})[k] = num(r[6])
    elif not r[2]:
        gal_vt.setdefault(r[5], {})[k] = num(r[6])
pc, gal_pc = defaultdict(dict), {}
for r in csv.reader((RAW / "ine_39366.csv").open(encoding="utf-8-sig"), delimiter=";"):
    if len(r) < 6 or r[1] != "12 Galicia":
        continue
    if r[3]:
        pc[r[3][:5]][r[4]] = num(r[5])
    elif not r[2]:
        gal_pc[r[4]] = num(r[5])
cortes = sorted(gal_pc)
ult = cortes[-1]
print("cortes:", cortes, "· Galicia", ult, gal_vt[ult], gal_pc[ult], "%")

# Censo 2021: vivendas totais
viv = {}
for r in csv.reader((RAW / "ine_59525.csv").open(encoding="utf-8-sig"), delimiter=";"):
    if len(r) > 3 and r[1][:2] in ("15", "27", "32", "36") and len(r[1]) > 6 and r[2] == "Total":
        viv[r[1][:5]] = int(r[3].replace(".", ""))

# REAT: último mes
reat, mes = defaultdict(int), None
filas = list(csv.DictReader((RAW / "REAT_Serie_Mensual.csv").open(encoding="latin1"), delimiter=";"))
mes = max(x["TEMPO"] for x in filas)
for x in filas:
    if x["TEMPO"] == mes and x["TIPO"] in ("Vivendas de uso turístico", "Vivendas turísticas"):
        reat[x["CODCON"]] += int(x["ESTABLECEMENTOS"])
print("REAT", mes, "vivendas rexistradas:", sum(reat.values()))

mc = json.loads((HERE.parent / "monte-concellos" / "data" / "datos.json").read_text(encoding="utf-8"))
conc, dif = [], []
for c in mc["concellos"]:
    i = c["id"]
    s = vt.get(i, {})
    v = (s.get(ult) or {}).get("v")
    o = {"id": i, "n": c["n"], "pr": c["pr"], "pol": c["pol"], "viv": viv[i], "reat": reat.get(i, 0),
         "v": v, "pl": (s.get(ult) or {}).get("p"), "pc": pc[i].get(ult),
         "se": [pc[i].get(t) for t in cortes]}
    if v is not None and o["pc"] is not None:
        dif.append(abs(v / viv[i] * 100 - o["pc"]))
    conc.append(o)
print("concellos con dato no último corte:", sum(c["pc"] is not None for c in conc), "de", len(conc),
      f"· diferenza máx. entre a % do INE e a recalculada co censo: {max(dif):.3f} p.p.")
gviv = sum(viv[c["id"]] for c in conc)
print(f"Galicia recalculada: {gal_vt[ult]['v'] / gviv * 100:.2f} % ({gviv} vivendas no censo 2021)")
for c in sorted([c for c in conc if c["pc"] is not None], key=lambda c: -c["pc"])[:12]:
    print(f"  {c['n']:24} {c['pc']:5.2f} %  {c['v']:6.0f} VUT INE · {c['reat']:5} REAT · {c['viv']} vivendas")
out = {"cortes": cortes, "ult": ult, "mes_reat": mes, "conc": conc,
       "gal": {"v": gal_vt[ult]["v"], "pl": gal_vt[ult]["p"], "pc": gal_pc[ult], "viv": gviv, "reat": sum(reat.values()),
               "se": [gal_pc[t] for t in cortes]}}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json", (HERE / "data" / "datos.json").stat().st_size // 1024, "KB")

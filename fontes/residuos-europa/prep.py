#!/usr/bin/env python3
"""Residuos municipais por habitante: países da UE (Eurostat) e comunidades autónomas (INE) → data/datos.json

Fontes:
  · Eurostat, «Municipal waste by waste management operations» (env_wasmun), residuos xerados
    (wst_oper=GEN) en kg por habitante:
    https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/env_wasmun?unit=KG_HAB&wst_oper=GEN&lang=EN
  · Eurostat, «Recycling rate of municipal waste» (cei_wm011), % reciclado (material + compostaxe e dixestión):
    https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/cei_wm011?lang=EN
  · INE, Estatística sobre a recollida e tratamento de residuos, «Recogida de residuos municipales.
    Resultados por comunidades autónomas»:
      táboa 32999, indicadores per cápita (kg/hab) por clase de residuo, 2010-2023
        https://www.ine.es/jaxi/Tabla.htm?tpx=32999  (CSV: https://www.ine.es/jaxi/files/tpx/es/csv_bdsc/32999.csv)
      táboa 32998, cantidade recollida (t) por tipo de residuo, 2010-2023
        https://www.ine.es/jaxi/Tabla.htm?tpx=32998  (CSV: https://www.ine.es/jaxi/files/tpx/es/csv_bdsc/32998.csv)
Colle o último ano común ás dúas fontes. Para as comunidades non hai taxa de reciclaxe: dáse a
porcentaxe de recollida separada (papel, vidro, envases, biorresiduos, etc.) sobre o total recollido,
ambos sen residuos de construción nin «outros», que é como o INE calcula o per cápita. Ficheiros en data/raw/.
"""
import csv
import io
import json
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
B = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
URLS = {"gen.json": B + "env_wasmun?unit=KG_HAB&wst_oper=GEN&lang=EN",
        "rcy.json": B + "cei_wm011?lang=EN",
        "ine32999.csv": "https://www.ine.es/jaxi/files/tpx/es/csv_bdsc/32999.csv",
        "ine32998.csv": "https://www.ine.es/jaxi/files/tpx/es/csv_bdsc/32998.csv"}
EU = {"AT": "Austria", "BE": "Bélxica", "BG": "Bulgaria", "CY": "Chipre", "CZ": "Chequia", "DE": "Alemaña",
      "DK": "Dinamarca", "EE": "Estonia", "EL": "Grecia", "ES": "España", "FI": "Finlandia", "FR": "Francia",
      "HR": "Croacia", "HU": "Hungría", "IE": "Irlanda", "IT": "Italia", "LT": "Lituania", "LU": "Luxemburgo",
      "LV": "Letonia", "MT": "Malta", "NL": "Países Baixos", "PL": "Polonia", "PT": "Portugal", "RO": "Romanía",
      "SE": "Suecia", "SI": "Eslovenia", "SK": "Eslovaquia"}
CCAA = {"01": "Andalucía", "02": "Aragón", "03": "Asturias", "04": "Illes Balears", "05": "Canarias", "06": "Cantabria",
        "07": "Castela e León", "08": "Castela-A Mancha", "09": "Cataluña", "10": "C. Valenciana", "11": "Estremadura",
        "12": "Galicia", "13": "Madrid", "14": "Murcia", "15": "Navarra", "16": "País Vasco", "17": "A Rioxa"}

RAW.mkdir(parents=True, exist_ok=True)
for n, u in URLS.items():
    if not (RAW / n).exists():
        (RAW / n).write_bytes(urlopen(Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=180).read())


def es_val(d, geo, t):
    ids, sz, dims = d["id"], d["size"], d["dimension"]
    ix = 0
    for k, s in zip(ids, sz):
        c = dims[k]["category"]["index"]
        ix = ix * s + (c[geo] if k == "geo" else c[t] if k == "time" else 0)
        if k == "geo" and geo not in c or k == "time" and t not in c:
            return None, ""
    return d["value"].get(str(ix)), d.get("status", {}).get(str(ix), "")


gen = json.loads((RAW / "gen.json").read_text(encoding="utf-8"))
rcy = json.loads((RAW / "rcy.json").read_text(encoding="utf-8"))
num = lambda s: None if s.strip() in ("", "..", ".") else float(s.replace(".", "").replace(",", "."))
lee = lambda n: list(csv.reader(io.StringIO((RAW / n).read_bytes().decode("iso-8859-15").lstrip("﻿")), delimiter=";"))
pc = lee("ine32999.csv")[1:]
qt = lee("ine32998.csv")[1:]
ccaa = lambda s: (s[:2], CCAA[s[:2]]) if s[:2] in CCAA else ("ES", "España") if s == "" else (None, None)

ine_anos = {int(r[3]) for r in pc if num(r[4]) is not None}
ano = max(a for a in ine_anos if es_val(gen, "EU27_2020", str(a))[0] is not None)
A = str(ano)

paises = []
for c, n in EU.items():
    g, fg = es_val(gen, c, A)
    r, fr = es_val(rcy, c, A)
    if g is None:
        continue
    paises.append({"c": c, "n": n, "kg": g, "rc": r, "f": "".join(sorted(set(fg + fr)))})
ue = {"kg": es_val(gen, "EU27_2020", A)[0], "rc": es_val(rcy, "EU27_2020", A)[0]}

com = {}
for nac, ca, clase, a, v in pc:
    if a != A or nac != "Total Nacional":
        continue
    c, n = ccaa(ca)
    if c and clase == "Total":
        com.setdefault(c, {"c": c, "n": n})["kg"] = num(v)
    if c and clase == "Residuos mezclados":
        com.setdefault(c, {"c": c, "n": n})["mez"] = num(v)
tons = {}
for tipo, nac, ca, a, v in qt:
    c, _ = ccaa(ca)
    if a == A and c and tipo in ("TOTAL RESIDUOS (sin RCD ni otros)", "TOTAL RESIDUOS DE RECOGIDA SEPARADA (sin RCD ni Otros)"):
        tons.setdefault(c, {})["tot" if tipo.startswith("TOTAL RESIDUOS (") else "sep"] = num(v)
for c, x in com.items():
    x["sep"] = round(100 * tons[c]["sep"] / tons[c]["tot"], 1)
esp = com.pop("ES")
out = {"ano": ano, "paises": sorted(paises, key=lambda p: -p["kg"]), "ue": ue,
       "ccaa": sorted(com.values(), key=lambda p: -p["kg"]), "es_ine": esp,
       "es_eurostat": next(p for p in paises if p["c"] == "ES")}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ano", ano, "países", len(paises), "CCAA", len(com))
print("UE", ue, "España INE", esp, "España Eurostat", out["es_eurostat"])
print("Galicia", com["12"])

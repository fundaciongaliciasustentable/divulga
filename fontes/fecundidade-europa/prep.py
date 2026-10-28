#!/usr/bin/env python3
"""Fillos por muller (indicador conxuntural de fecundidade) nas rexións NUTS 2 da UE → data/datos.json

Fontes (Eurostat, API de difusión JSON, gardadas en data/raw/):
  - demo_r_frate2, «Fertility rates by age and NUTS 2 region», idade TOTAL (= indicador conxuntural):
    https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_r_frate2?format=JSON&lang=EN&age=TOTAL&unit=NR
  - demo_frate, «Fertility rates by age», para a media da UE-27 (EU27_2020) e España:
    https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_frate?format=JSON&lang=EN&age=TOTAL&unit=NR&geo=EU27_2020&geo=ES

Só se colle a UE-27 (rexións NUTS 2 dos 27 estados), sen as rexións «ZZ» (non asignadas).
O último ano é o máis recente con datos para todas as rexións da UE.
"""
import json
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
API = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
URLS = {
    "demo_r_frate2.json": API + "demo_r_frate2?format=JSON&lang=EN&age=TOTAL&unit=NR",
    "demo_frate.json": API + "demo_frate?format=JSON&lang=EN&age=TOTAL&unit=NR&geo=EU27_2020&geo=ES",
}
EU = "AT BE BG CY CZ DE DK EE EL ES FI FR HR HU IE IT LT LU LV MT NL PL PT RO SE SI SK".split()
# Nomes en galego dos estados (para as etiquetas)
PAIS = {"AT": "Austria", "BE": "Bélxica", "BG": "Bulgaria", "CY": "Chipre", "CZ": "Chequia", "DE": "Alemaña", "DK": "Dinamarca",
        "EE": "Estonia", "EL": "Grecia", "ES": "España", "FI": "Finlandia", "FR": "Francia", "HR": "Croacia", "HU": "Hungría",
        "IE": "Irlanda", "IT": "Italia", "LT": "Lituania", "LU": "Luxemburgo", "LV": "Letonia", "MT": "Malta", "NL": "Países Baixos",
        "PL": "Polonia", "PT": "Portugal", "RO": "Romanía", "SE": "Suecia", "SI": "Eslovenia", "SK": "Eslovaquia"}

RAW.mkdir(parents=True, exist_ok=True)
for f, u in URLS.items():
    if not (RAW / f).exists():
        (RAW / f).write_bytes(urlopen(Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=180).read())
        print("descargado", f)


def cubo(f):
    """Devolve (etiquetas xeo, anos, val(xeo, ano)) dun JSON-stat de Eurostat con dimensións únicas agás geo e time."""
    d = json.loads((RAW / f).read_text(encoding="utf-8"))
    g = d["dimension"]["geo"]["category"]
    t = d["dimension"]["time"]["category"]["index"]
    nT, v = len(t), d["value"]
    return g["label"], sorted(t), lambda geo, y: v.get(str(g["index"][geo] * nT + t[y])) if geo in g["index"] else None


lab, anos, val = cubo("demo_r_frate2.json")
n2 = [x for x in lab if len(x) == 4 and x[:2] in EU and not x.endswith("ZZ")]
# Último ano con dato en todos os estados
ult = max(y for y in anos if {x[:2] for x in n2 if val(x, y) is not None} == set(EU))
reg = sorted(([x, lab[x], round(val(x, ult), 3)] for x in n2 if val(x, ult) is not None), key=lambda r: r[2])
labn, anosn, valn = cubo("demo_frate.json")
serie = {"ES11": {}, "ES": {}, "EU": {}}
for y in anos:
    if int(y) >= 2000:
        serie["ES11"][y] = val("ES11", y)
for y in anosn:
    if int(y) >= 2000:
        serie["ES"][y] = valn("ES", y)
        serie["EU"][y] = valn("EU27_2020", y)
serie = {k: [[int(y), round(v, 3)] for y, v in s.items() if v is not None] for k, s in serie.items()}
# Mínimo e máximo de Galicia na serie e ano en que España e a UE estaban por riba de 1,5
out = {"ano": int(ult), "reg": reg, "pais": PAIS, "serie": serie}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
pos = [r[0] for r in reg].index("ES11") + 1
print(f"ok: {len(reg)} rexións en {ult}; Galicia {val('ES11', ult):.3f}, posto {pos} pola cola (de {len(reg)})")
print("serie UE:", serie["EU"][0], "…", serie["EU"][-1], "| ES:", serie["ES"][-1], "| Galicia:", serie["ES11"][0], serie["ES11"][-1])

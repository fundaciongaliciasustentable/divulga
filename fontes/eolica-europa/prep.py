#!/usr/bin/env python3
"""Potencia eólica por habitante e por km²: Galicia fronte aos países da UE, 2015-2024 → data/datos.json

Fontes (descárganse en data/raw/ se faltan):
  · Eurostat nrg_inf_epcrw, capacidade eléctrica neta máxima das renovables, eólica (siec RA300), MW:
      https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nrg_inf_epcrw?format=JSON&lang=en&siec=RA300&plant_tec=CAP_NET_ELC&unit=MW&sinceTimePeriod=2015
    e a mesma táboa para a eólica mariña (siec RA320), para calcular a de terra:
      https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nrg_inf_epcrw?format=JSON&lang=en&siec=RA320&plant_tec=CAP_NET_ELC&unit=MW&sinceTimePeriod=2015
  · Eurostat demo_r_d2jan, poboación a 1 de xaneiro (países e Galicia, NUTS ES11):
      https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_r_d2jan?format=JSON&sex=T&age=TOTAL&unit=NR&sinceTimePeriod=2016
  · Eurostat reg_area3, superficie terrestre (landuse L0008) en km²:
      https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/reg_area3?format=JSON&landuse=L0008&unit=KM2&time=2024
  · Galicia: Inega, «Potencia eléctrica e térmica instalada en Galicia» (táboa «Potencia centrais
    eléctricas en Galicia (MW)», fila Eólica, 2015-2024; fonte orixinal: Inega e Rexistro de
    Instalacións de Produción de Enerxía Eléctrica), PDF do 31/03/2026:
      https://www.inega.gal/sites/default/files/publicacions/20260331_evolucion_potencia.pdf
  · Nomes dos países en galego: Unicode CLDR 46.

Pensábase comparar tamén coas comunidades autónomas co REData de Red Eléctrica
(/es/datos/generacion/potencia-instalada), pero ese punto da HTTP 500 para calquera consulta
(probado o 28/10/2026), e non se atopou outra táboa oficial descargable por comunidade.
A potencia de fin de ano divídese pola poboación do 1 de xaneiro seguinte.
"""
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

import pypdf

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
UA = {"User-Agent": "Mozilla/5.0"}
ES = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
URLS = {
    "cap": ES + "nrg_inf_epcrw?format=JSON&lang=en&siec=RA300&plant_tec=CAP_NET_ELC&unit=MW&sinceTimePeriod=2015",
    "mar": ES + "nrg_inf_epcrw?format=JSON&lang=en&siec=RA320&plant_tec=CAP_NET_ELC&unit=MW&sinceTimePeriod=2015",
    "pop": ES + "demo_r_d2jan?format=JSON&sex=T&age=TOTAL&unit=NR&sinceTimePeriod=2016",
    "area": ES + "reg_area3?format=JSON&landuse=L0008&unit=KM2&time=2024",
}
INEGA = "https://www.inega.gal/sites/default/files/publicacions/20260331_evolucion_potencia.pdf"
CLDR = "https://cdn.jsdelivr.net/npm/cldr-localenames-full@46.0.0/main/gl/territories.json"
UE = ["BE", "BG", "CZ", "DK", "DE", "EE", "IE", "EL", "ES", "FR", "HR", "IT", "CY", "LV", "LT", "LU", "HU", "MT", "NL",
      "AT", "PL", "PT", "RO", "SI", "SK", "FI", "SE"]


def baixa(url, f):
    if not f.exists():
        f.write_bytes(urlopen(Request(url, headers=UA), timeout=300).read())
    return f


def jsonstat(f):
    """{(geo, ano): valor} dun JSON-stat de Eurostat filtrado a unha soa combinación nas outras dimensións."""
    d = json.loads(f.read_text(encoding="utf-8"))
    ids, size = d["id"], d["size"]
    inv = {k: {i: c for c, i in d["dimension"][k]["category"]["index"].items()} for k in ids}
    out = {}
    for pos, v in d["value"].items():
        pos, coord = int(pos), {}
        for k, s in zip(reversed(ids), reversed(size)):
            coord[k] = inv[k][pos % s]
            pos //= s
        out[(coord["geo"], int(coord["time"]))] = v
    return out


RAW.mkdir(parents=True, exist_ok=True)
cap = jsonstat(baixa(URLS["cap"], RAW / "nrg_inf_epcrw.json"))
mar = jsonstat(baixa(URLS["mar"], RAW / "nrg_inf_epcrw_mar.json"))
pop = jsonstat(baixa(URLS["pop"], RAW / "demo_r_d2jan.json"))
area = jsonstat(baixa(URLS["area"], RAW / "reg_area3.json"))
gl = json.loads(baixa(CLDR, RAW / "cldr_gl_territories.json").read_text(encoding="utf-8"))
gl = gl["main"]["gl"]["localeDisplayNames"]["territories"]

# Galicia, Inega
txt = "\n".join(p.extract_text() for p in pypdf.PdfReader(baixa(INEGA, RAW / "inega_evolucion_potencia.pdf")).pages)
cab = re.search(r"Potencia centrales eléctricas en Galicia \(MW\)\s*\n((?:\d{4} ?)+)", txt)
anos_g = [int(a) for a in cab.group(1).split()]
fila = re.search(r"\nEólica ((?:[\d.]+ ?)+)\n", txt[cab.end():])
mw_g = [int(v.replace(".", "")) for v in fila.group(1).split()]
assert len(mw_g) == len(anos_g), (anos_g, mw_g)
GAL = dict(zip(anos_g, mw_g))

ANOS = [y for y in range(2015, 2100) if (("DE", y) in cap and y in GAL)]
U = ANOS[-1]
nome = lambda g: {"EL": gl["GR"], "EU27_2020": "UE-27"}.get(g) or gl.get(g, g)
paises = []
for g in UE + ["EU27_2020"]:
    a = area.get((g, 2024)) or sum(area.get((c, 2024), 0) for c in UE)
    paises.append({"id": g, "n": nome(g), "mw": [round(cap.get((g, y), 0)) for y in ANOS],
                     "mar": [round(mar.get((g, y)) or 0) for y in ANOS],
                   "pob": [pop.get((g if g != "EU27_2020" else "EU27_2020", y + 1)) for y in ANOS], "km2": round(a)})
for p in paises:
    if p["id"] == "EU27_2020" and not all(p["pob"]):
        p["pob"] = [sum(pop[(c, y + 1)] for c in UE) for y in ANOS]
paises.append({"id": "GZ", "n": "Galicia", "mw": [GAL[y] for y in ANOS], "mar": [0 for y in ANOS], "pob": [pop[("ES11", y + 1)] for y in ANOS],
               "km2": round(area[("ES11", 2024)])})
for p in paises:
    assert all(p["pob"]), p
d = {"anos": ANOS, "paises": paises}
(HERE / "data" / "datos.json").write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
for p in sorted(paises, key=lambda p: -p["mw"][-1] / p["pob"][-1]):
    print(f"{p['n']:<18} {p['mw'][-1]:>7} MW (mar {p['mar'][-1]:>6}) {p['mw'][-1] * 1e6 / p['pob'][-1]:6.0f} W/hab  "
          f"{(p['mw'][-1] - p['mar'][-1]) * 1000 / p['km2']:6.0f} kW/km² en terra")
print("ok: data/datos.json", (HERE / "data" / "datos.json").stat().st_size // 1024, "KB")

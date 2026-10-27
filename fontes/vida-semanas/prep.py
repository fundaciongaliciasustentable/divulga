#!/usr/bin/env python3
"""Táboas de mortalidade de Galicia e das catro provincias, por sexo e idade → data/datos.json

Fontes (INE, Táboas de mortalidade, último ano publicado):
  · 27154: comunidades autónomas, por grupos de idade (collemos Galicia)
    https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/27154?nult=1
  · 27155: provincias, por grupos de idade
    https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/27155?nult=1
O INE dá as provincias en grupos (0, 1-4, 5-9 … 95 e máis). Para ter cada idade, os
superviventes interpólanse en escala logarítmica dentro de cada grupo e a esperanza de vida, en
liña recta; despois dos 95, os superviventes caen de xeito exponencial coa esperanza aos 95.
Tamén a idade media á maternidade de Galicia (IGE, da peza fenda-rural) para un dos fitos.
"""
import json
import math
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
AREAS = {"Galicia": "Galicia", "Coruña, A": "A Coruña", "Lugo": "Lugo", "Ourense": "Ourense", "Pontevedra": "Pontevedra"}
SEXOS = {"Hombres": "H", "Mujeres": "M", "Total": "T"}
TOPE = 110


def baixa(t):
    f = RAW / f"ine_{t}.json"
    if not f.exists():
        RAW.mkdir(parents=True, exist_ok=True)
        f.write_bytes(urlopen(Request(f"https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{t}?nult=1",
                                      headers={"User-Agent": "Mozilla/5.0"}), timeout=300).read())
    return json.loads(f.read_text(encoding="utf-8"))


def inicio(etq):
    """«0 años» → 0, «De 1 a 4 años» → 1, «95 y más años» → 95."""
    p = etq.replace("De ", "").split()
    return int(p[0])


bruto, ano = {}, None
for t in (27154, 27155):
    for s in baixa(t):
        partes = [p.strip() for p in s["Nombre"].split(".")]
        area, sexo, idade, func = partes[:4]
        if area not in AREAS or sexo not in SEXOS or func not in ("Supervivientes", "Esperanza de vida"):
            continue
        if idade == "90 y más años":  # na táboa de comunidades vai xunto co desglose 90-94 / 95+
            continue
        ano = s["Data"][0]["Anyo"]
        bruto.setdefault((AREAS[area], SEXOS[sexo]), {}).setdefault(func, {})[inicio(idade)] = s["Data"][0]["Valor"]

out = {"ano": ano, "areas": list(AREAS.values()), "t": {}}
for (area, sx), f in bruto.items():
    lxg, exg = f["Supervivientes"], f["Esperanza de vida"]
    xs = sorted(lxg)
    assert xs[0] == 0 and xs[-1] == 95, (area, sx, xs)
    lx, ex = [], []
    for x in range(TOPE + 1):
        if x >= 95:
            e95 = exg[95]
            lx.append(lxg[95] * math.exp(-(x - 95) / e95))
            ex.append(max(0.5, e95 * math.exp(-(x - 95) / 12)))  # a esperanza segue baixando pouco a pouco
            continue
        a = max(v for v in xs if v <= x)
        b = min(v for v in xs if v > x)
        w = (x - a) / (b - a)
        lx.append(math.exp(math.log(lxg[a]) * (1 - w) + math.log(lxg[b]) * w))
        ex.append(exg[a] * (1 - w) + exg[b] * w)
    out["t"][f"{area}|{sx}"] = {"lx": [round(v, 1) for v in lx], "ex": [round(v, 2) for v in ex]}
    print(f"{area:10} {sx}  e0 {ex[0]:.2f}  e40 {ex[40]:.2f}  l90/l0 {lx[90] / lx[0]:.1%}")

# Idade media á maternidade en Galicia (IGE), da peza fenda-rural
fr = json.loads((HERE.parent / "fenda-rural" / "data" / "datos.json").read_text(encoding="utf-8"))
mat = fr["ind"]["mat"]["d"]
ult = max(mat)
out["mat"] = [int(ult), mat[ult]["T"]]
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ano", ano, "· idade media á maternidade", out["mat"], "· ok: data/datos.json")

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

Uso do tempo: Eurostat, HETUS (tus_00age), España 2010, que é a Enquisa de emprego do tempo
2009-2010 do INE harmonizada; tempo medio ao día de toda a poboación de cada grupo de idade (15-19,
20-24, 25-44, 45-64, 65 e máis). Non hai datos galegos por idade nin unha edición máis nova
publicada (a 2024-2025 do INE está en curso).
  https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/tus_00age?geo=ES&sex=T
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

# Uso do tempo por idade (minutos ao día)
TUS = RAW / "eurostat_tus_00age.json"
if not TUS.exists():
    TUS.write_bytes(urlopen("https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/tus_00age?geo=ES&sex=T&lang=EN",
                            timeout=120).read())
tus = json.loads(TUS.read_text(encoding="utf-8"))
ids, size, dim = tus["id"], tus["size"], tus["dimension"]


def tus_min(idade, act):
    pos = 0
    for k, n in zip(ids, size):
        v = {"freq": "A", "unit": "TIME_SP", "sex": "T", "age": idade, "acl00": act, "geo": "ES", "time": "2010"}[k]
        pos = pos * n + dim[k]["category"]["index"][v]
    h, m = tus["value"][str(pos)].split(":")
    return int(h) * 60 + int(m)


CATS = [("durmir", "Durmir", ["AC01"]), ("traballar", "Traballar (co camiño ao traballo)", ["AC1A", "AC1B"]),
        ("casa", "Casa e familia (cociñar, limpar, coidar…)", ["AC3"]), ("tele", "Ver a tele e vídeos", ["AC82"]),
        ("comer", "Comer", ["AC02"]), ("viaxar", "Desprazarse (agás ao traballo)", ["AC9A"]),
        ("social", "Vida social, festas e espectáculos", ["AC51A", "AC51B", "AC52"]), ("estudar", "Estudar", ["AC2"]),
        ("coidarse", "Asearse e vestirse", ["AC03"]), ("deporte", "Deporte e paseos", ["AC6A", "AC611"]),
        ("ordenador", "Ordenador e videoxogos", ["AC7A", "AC733"]), ("ler", "Ler", ["AC811", "AC812"])]
GRUPOS = [(15, 20, "Y15-20"), (20, 25, "Y20-24"), (25, 45, "Y25-44"), (45, 65, "Y45-64"), (65, 200, "Y_GE65")]
uso = []
for a0, a1, g in GRUPOS:
    m = {k: sum(tus_min(g, c) for c in cs) for k, _, cs in CATS}
    m["resto"] = 1440 - sum(m.values())
    uso.append([a0, a1, m])
    print(g, m)
# Internet hoxe: só unha estimación comercial (enquisa de GWI recollida por DataReportal) e en boa
# parte á vez que outras cousas, así que non entra na suma do día
out["net"] = {"min": 5 * 60 + 40, "f": "DataReportal / GWI, 3.º trimestre de 2024, usuarios de 16 a 64 anos",
              "url": "https://datareportal.com/reports/digital-2025-spain"}
out["uso"] = {"grupos": uso, "cats": [[k, n] for k, n, _ in CATS] + [["resto", "Descansar, música, afeccións e o resto"]]}

# Idade media á maternidade en Galicia (IGE), da peza fenda-rural
fr = json.loads((HERE.parent / "fenda-rural" / "data" / "datos.json").read_text(encoding="utf-8"))
mat = fr["ind"]["mat"]["d"]
ult = max(mat)
out["mat"] = [int(ult), mat[ult]["T"]]
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ano", ano, "· idade media á maternidade", out["mat"], "· ok: data/datos.json")

#!/usr/bin/env python3
"""Temperatura da auga do mar fronte ás Rías Baixas, 1982-2025 → data/datos.json

Fonte: NOAA OISST v2.1 (Optimum Interpolation SST, satélite + boias + barcos, 0,25° e diaria),
servida polo ERDDAP de NOAA CoastWatch:
  https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21Agg_LonPM180.html
Recadro: 42,0-43,75 °N e 10,0-9,0 °O, a plataforma fronte ás rías (as celas de terra veñen en NaN).
Un CSV por ano en data/raw/ (descárgase se falta). Para cada día, media das celas de mar.
O agregado de ERDDAP ten ocos nalgúns anos (en 1993 falta media serie), así que os días que faltan
cóllense do mesmo produto no servidor THREDDS de NOAA PSL, mes a mes (data/raw/psl_AAAA-MM.txt):
  https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.oisst.v2.highres/sst.day.mean.AAAA.nc

Para cada ano: a distribución dos 365 días (densidade suavizada, para o ridgeline), a media
e a anomalía fronte a 1991-2020. Tamén a curva diaria media (para a outra vista).
"""
import csv
import json
import math
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
URL = ("https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21Agg_LonPM180.csv?"
       "sst%5B({a}-01-01T12:00:00Z):1:({a}-12-31T12:00:00Z)%5D%5B(0.0)%5D%5B(42.0):1:(43.75)%5D%5B(-10.0):1:(-9.0)%5D")
A0, A1 = 1982, 2025
NORMAL = (1991, 2020)
PSL = ("https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.oisst.v2.highres/sst.day.mean.{a}.nc.ascii?"
       "sst%5B{i0}:{i1}%5D%5B528:535%5D%5B1400:1404%5D")  # 42,125-43,875 °N e 350,125-351,125 °E: as mesmas 40 celas


def psl_mes(a, m):
    """Medias diarias dun mes desde PSL (OPeNDAP en texto). O servidor corta as peticións longas: un mes por vez."""
    f = RAW / f"psl_{a}-{m:02d}.txt"
    if not f.exists():
        i0 = (date(a, m, 1) - date(a, 1, 1)).days
        i1 = (date(a + (m == 12), m % 12 + 1, 1) - date(a, 1, 1)).days - 1
        req = Request(PSL.format(a=a, i0=i0, i1=i1), headers={"User-Agent": "Mozilla/5.0"})
        f.write_bytes(urlopen(req, timeout=120).read())
        print("PSL", a, m, flush=True)
    filas, tempo = defaultdict(list), []
    linhas = f.read_text().splitlines()
    for i, l in enumerate(linhas):
        if l.startswith("[") and "][" in l:
            t = int(l[1:l.index("]")])
            filas[t] += [float(x) for x in l.split(",")[1:] if float(x) > -100]
        if l.startswith("sst.time["):
            tempo = [float(x) for x in linhas[i + 1].split(",")]
    return {date(1800, 1, 1) + timedelta(days=int(tempo[t])): sum(v) / len(v) for t, v in filas.items() if v}

RAW.mkdir(parents=True, exist_ok=True)
dias = {}
for a in range(A0, A1 + 1):
    f = RAW / f"oisst_{a}.csv"
    if not f.exists():
        f.write_bytes(urlopen(URL.format(a=a), timeout=300).read())
        print("descargado", a, flush=True)
    acc = defaultdict(list)
    with f.open() as fh:
        r = csv.reader(fh)
        next(r), next(r)
        for t, _, _, _, v in r:
            if v != "NaN":
                acc[t[:10]].append(float(v))
    dias[a] = {date.fromisoformat(t): sum(v) / len(v) for t, v in sorted(acc.items())}
    todos = [date(a, 1, 1) + timedelta(days=i) for i in range((date(a + 1, 1, 1) - date(a, 1, 1)).days)]
    for m in sorted({d.month for d in todos if d not in dias[a]}):
        for d, v in psl_mes(a, m).items():
            dias[a].setdefault(d, v)
    falta = [d for d in todos if d not in dias[a]]
    assert len(falta) <= 3, (a, len(falta), falta[:5])
    dias[a] = dict(sorted(dias[a].items()))

media = {a: sum(v.values()) / len(v) for a, v in dias.items()}
norm = sum(media[a] for a in range(NORMAL[0], NORMAL[1] + 1)) / (NORMAL[1] - NORMAL[0] + 1)

# Densidade de cada ano por núcleo gaussiano sobre unha reixa común de temperaturas
lo = math.floor(min(min(v.values()) for v in dias.values())) - 0.5
hi = math.ceil(max(max(v.values()) for v in dias.values())) + 0.5
PASO = 0.1
X = [round(lo + i * PASO, 2) for i in range(int(round((hi - lo) / PASO)) + 1)]
BW = 0.35  # ancho de banda en °C
def kde(v):
    k = 1 / (len(v) * BW * math.sqrt(2 * math.pi))
    return [round(k * sum(math.exp(-0.5 * ((x - y) / BW) ** 2) for y in v), 4) for x in X]

# Curva do ano: medias de 7 días para que se lea a estación sen o ruído diario
def semanal(dv):
    sem = defaultdict(list)
    for d, x in dv.items():
        sem[min(51, (d.timetuple().tm_yday - 1) // 7)].append(x)
    return [round(sum(sem[i]) / len(sem[i]), 2) if sem[i] else None for i in range(52)]

anos = []
for a in range(A0, A1 + 1):
    v = list(dias[a].values())
    anos.append({"a": a, "m": round(media[a], 2), "an": round(media[a] - norm, 2), "min": round(min(v), 2),
                 "max": round(max(v), 2), "d": kde(v), "s": semanal(dias[a]), "n": len(v),
                 "q20": sum(x >= 20 for x in v), "q18": sum(x >= 18 for x in v)})
# Tendencia lineal (mínimos cadrados) en °C por década
n = len(anos)
xm = sum(x["a"] for x in anos) / n
ym = sum(x["m"] for x in anos) / n
b = sum((x["a"] - xm) * (x["m"] - ym) for x in anos) / sum((x["a"] - xm) ** 2 for x in anos)
out = {"anos": anos, "x": [X[0], PASO, len(X)], "norm": round(norm, 2), "normal": NORMAL, "tend": round(b * 10, 3),
       "caixa": [42.0, 43.75, -10.0, -9.0], "actualizado": date.today().isoformat()}
for x in anos:
    print(x["a"], x["m"], f"{x['an']:+.2f}", x["min"], x["max"], "días ≥18:", x["q18"])
print(f"normal {NORMAL}: {norm:.2f} °C · tendencia {b * 10:+.2f} °C/década")
(HERE / "data" / "datos.json").write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json")

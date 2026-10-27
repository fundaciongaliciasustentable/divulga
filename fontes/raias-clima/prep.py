#!/usr/bin/env python3
"""Temperatura media e choiva anuais de seis observatorios galegos → data/datos.json

Fonte: NOAA GHCN-Daily (series diarias das estacións de AEMET, vía ECA&D), un CSV por estación
en data/ (descárgase se falta):
  https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/<ID>.csv

Temperatura media diaria = (máxima + mínima) / 2. Un mes vale se ten polo menos 25 días con
dato (sen marca de calidade) de temperatura, ou 20 de choiva; un ano vale se ten os 12 meses. A temperatura anual é a media dos
12 meses; a choiva anual, a suma dos meses, cada un estimado coa súa media diaria polos días do mes. Anomalías respecto da normal 1991-2020.
"""
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
URL = "https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/{}.csv"
EST = [("SPE00119711", "A Coruña"), ("SPE00119729", "Santiago (Lavacolla)"), ("SPE00120413", "Vigo (Peinador)"),
       ("SPE00120395", "Pontevedra"), ("SPE00120368", "Ourense"), ("SPE00120260", "Lugo (Rozas)")]
NORMAL = range(1991, 2021)
MIN_DIAS = 25    # temperatura
MIN_DIAS_P = 20  # choiva: os días sen dato están espallados, e o mes estímase coa media diaria


def val(x, k):
    v, a = x.get(k, "").strip(), x.get(k + "_ATTRIBUTES", "")
    if not v:
        return None
    q = a.split(",")[1] if a.count(",") >= 1 else ""
    return None if q.strip() else int(v) / 10  # décimas de °C ou de mm


out = []
for sid, nome in EST:
    f = DATA / f"{sid}.csv"
    if not f.exists():
        f.write_bytes(urlopen(URL.format(sid), timeout=300).read())
    t = defaultdict(list)   # (ano, mes) → medias diarias
    p = defaultdict(list)   # (ano, mes) → choiva diaria
    for x in csv.DictReader(f.open()):
        y, m = int(x["DATE"][:4]), int(x["DATE"][5:7])
        tx, tn, pr = val(x, "TMAX"), val(x, "TMIN"), val(x, "PRCP")
        if tx is not None and tn is not None:
            t[(y, m)].append((tx + tn) / 2)
        if pr is not None:
            p[(y, m)].append(pr)
    anos = sorted({k[0] for k in list(t) + list(p)})
    T, P = {}, {}
    for y in anos:
        tm = [mean(t[(y, m)]) for m in range(1, 13) if len(t[(y, m)]) >= MIN_DIAS]
        pm = [m for m in range(1, 13) if len(p[(y, m)]) >= MIN_DIAS_P]
        if len(tm) == 12:
            T[y] = mean(tm)
        if len(pm) == 12:
            # cada mes escálase aos seus días para non contar menos choiva nos meses con ocos
            P[y] = sum(sum(p[(y, m)]) / len(p[(y, m)]) * (31 if m in (1, 3, 5, 7, 8, 10, 12) else 30 if m != 2 else 28.25)
                       for m in range(1, 13))
    nT = mean(T[y] for y in NORMAL if y in T)
    nP = mean(P[y] for y in NORMAL if y in P)
    faltaT = [y for y in NORMAL if y not in T]
    faltaP = [y for y in NORMAL if y not in P]
    tt = [y for y in T]
    a0, a1 = min(tt), max(tt)
    serie = [{"y": y, "t": round(T[y] - nT, 2) if y in T else None,
              "p": round(P[y] / nP * 100 - 100, 1) if y in P else None}
             for y in range(min(min(T), min(P)), max(max(T), max(P)) + 1)]
    quentes = sorted(T, key=lambda y: -T[y])[:5]
    print(f"{nome:22} T {a0}-{a1} ({len(T)} anos)  P {min(P)}-{max(P)} ({len(P)})  normal {nT:.2f} °C {nP:.0f} mm"
          f"  faltan na normal T:{faltaT} P:{faltaP}  máis quentes {quentes}")
    out.append({"id": sid, "n": nome, "nT": round(nT, 2), "nP": round(nP), "s": serie,
                "T": {y: round(v, 2) for y, v in T.items()}, "P": {y: round(v) for y, v in P.items()}})

(DATA / "datos.json").write_text(json.dumps({"normal": [1991, 2020], "est": out}, ensure_ascii=False,
                                            separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json", (DATA / "datos.json").stat().st_size // 1024, "KB")

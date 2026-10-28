#!/usr/bin/env python3
"""Canto se tarda en transporte público dende as sete cidades a cada concello → data/datos.json

Fontes (GTFS, gardados en data/raw/):
  · Autobuses da Xunta de Galicia (transporte público de Galicia), publicado no Punto de Acceso
    Nacional e copiado por MobilityDatabase (feed mdb-2821):
    https://mobilitydatabase.org/feeds/gtfs/mdb-2821
  · Renfe, Alta Velocidade, Longa e Media Distancia: https://ssl.renfe.com/gtransit/Fichero_AV_LD/google_transit.zip
Cálculo: un martes normal (DIA). Para cada cidade de orixe, saídas cada 20 minutos entre as 7:00 e
as 10:00 dende as paradas a menos de 1,5 km do centro; para cada saída, algoritmo de escaneo de
conexións (CSA: chegada máis temperá) sobre todas as conexións de bus e tren dese día, con
transbordos a pé entre paradas a menos de 400 m (4 km/h en liña recta × 1,3) e 2 minutos de marxe
ao cambiar de vehículo. O tempo dun concello é a viaxe máis curta (chegada − saída) a calquera
parada do concello. Máis de 8 horas ou sen conexión na mañá: sen dato.
Concellos: o xeojson de galicia-agora (como en monte-concellos) e os polígonos xa proxectados de
monte-concellos para o mapa.
"""
import json
import math
import sys
import zipfile
from collections import defaultdict
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from shapely.geometry import Point, shape
from shapely.prepared import prep

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
CONCELLOS = Path("/Users/perezgulin/Proxectos/galicia-agora/data-out/concellos-parroquias/data.geojson")
FEEDS = {"bus": "https://files.mobilitydatabase.org/mdb-2821/mdb-2821-202610240121/mdb-2821-202610240121.zip",
         "renfe": "https://ssl.renfe.com/gtransit/Fichero_AV_LD/google_transit.zip"}
DIA = "20261103"  # martes
ORIXES = {"A Coruña": (43.3623, -8.4115), "Santiago": (42.8782, -8.5448), "Vigo": (42.2328, -8.7226), "Lugo": (43.0097, -7.5560),
          "Ourense": (42.3358, -7.8639), "Pontevedra": (42.4310, -8.6446), "Ferrol": (43.4840, -8.2330)}
SAIDAS = range(7 * 60, 10 * 60 + 1, 20)
MAX = 8 * 60
LAT0 = 42.8
mxy = lambda lat, lon: (lon * 111_320 * math.cos(math.radians(LAT0)), lat * 110_574)

RAW.mkdir(parents=True, exist_ok=True)
for k, u in FEEDS.items():
    f = RAW / f"{k}.zip"
    if not f.exists():
        f.write_bytes(urlopen(Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=600).read())

gal = [shape(ft["geometry"]) for ft in json.loads(CONCELLOS.read_text(encoding="utf-8"))["features"] if ft["properties"]["nivel"] == "concello"]
conc = [(ft["properties"]["codigo_ine"], prep(shape(ft["geometry"]))) for ft in json.loads(CONCELLOS.read_text(encoding="utf-8"))["features"]
        if ft["properties"]["nivel"] == "concello"]


def lee(z, nome, **kw):
    """CSV dun GTFS sen os espazos que mete Renfe arredor dos nomes e dos valores."""
    df = pd.read_csv(z.open(nome), dtype=str, skipinitialspace=True, **kw)
    df.columns = df.columns.str.strip()
    return df.apply(lambda c: c.str.strip())


def activos(z):
    """Servizos que circulan o DIA (calendar + calendar_dates)."""
    names = z.namelist()
    act = set()
    if "calendar.txt" in names:
        cal = lee(z, "calendar.txt")
        wd = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][pd.Timestamp(DIA).weekday()]
        cal = cal[(cal.start_date <= DIA) & (cal.end_date >= DIA) & (cal[wd] == "1")]
        act |= set(cal.service_id)
    if "calendar_dates.txt" in names:
        cd = lee(z, "calendar_dates.txt")
        cd = cd[cd.date == DIA]
        act |= set(cd[cd.exception_type == "1"].service_id)
        act -= set(cd[cd.exception_type == "2"].service_id)
    return act


def minutos(s):
    h, m, *_ = s.split(":")
    return int(h) * 60 + int(m)


paradas, conex = {}, []
for k in FEEDS:
    z = zipfile.ZipFile(RAW / f"{k}.zip")
    st = lee(z, "stops.txt")[["stop_id", "stop_name", "stop_lat", "stop_lon"]]
    st[["stop_lat", "stop_lon"]] = st[["stop_lat", "stop_lon"]].astype(float)
    act = activos(z)
    tr = lee(z, "trips.txt")[["trip_id", "service_id", "route_id"]]
    tr = tr[tr.service_id.isin(act)]
    tids = set(tr.trip_id)
    print(k, "servizos activos:", len(act), "viaxes:", len(tids), flush=True)
    sts = []
    for ch in pd.read_csv(z.open("stop_times.txt"), dtype=str, chunksize=2_000_000, skipinitialspace=True):
        ch.columns = ch.columns.str.strip()
        ch = ch[["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"]].apply(lambda c: c.str.strip())
        sts.append(ch[ch.trip_id.isin(tids)])
    sts = pd.concat(sts)
    sts["stop_sequence"] = sts.stop_sequence.astype(int)
    st = st[st.stop_id.isin(set(sts.stop_id))]
    # paradas dentro de Galicia (Renfe trae toda España)
    dentro = {}
    for r in st.itertuples():
        p = Point(r.stop_lon, r.stop_lat)
        c = next((c for c, g in conc if g.contains(p)), None)
        if c or k == "bus":
            dentro[r.stop_id] = c
            paradas[f"{k}:{r.stop_id}"] = {"n": r.stop_name, "lat": r.stop_lat, "lon": r.stop_lon, "c": c}
    sts = sts[sts.stop_id.isin(dentro)].sort_values(["trip_id", "stop_sequence"])
    sts["d"] = sts.departure_time.map(minutos)
    sts["a"] = sts.arrival_time.map(minutos)
    for tid, g in sts.groupby("trip_id", sort=False):
        s, a, d = list(g.stop_id), list(g.a), list(g.d)
        for i in range(len(s) - 1):
            if a[i + 1] >= d[i]:
                conex.append((d[i], a[i + 1], f"{k}:{s[i]}", f"{k}:{s[i + 1]}", f"{k}:{tid}"))
    print(k, "paradas:", len(dentro), "conexións:", len(conex), flush=True)

# Índices numéricos e camiñadas entre paradas próximas
ids = list(paradas)
idx = {s: i for i, s in enumerate(ids)}
XY = np.array([mxy(paradas[s]["lat"], paradas[s]["lon"]) for s in ids])
arb = cKDTree(XY)
camina = defaultdict(list)
for i, j in arb.query_pairs(400):
    t = math.ceil(np.linalg.norm(XY[i] - XY[j]) * 1.3 / (4000 / 60))
    camina[i].append((j, t))
    camina[j].append((i, t))
conex.sort()
C_d = np.array([c[0] for c in conex])
C_dl = C_d.tolist()
C_a = [c[1] for c in conex]
C_f = [idx[c[2]] for c in conex]
C_t = [idx[c[3]] for c in conex]
trips = {t: i for i, t in enumerate({c[4] for c in conex})}
C_v = [trips[c[4]] for c in conex]
print("conexións do día:", len(conex), "paradas:", len(ids), "pares a pé:", sum(len(v) for v in camina.values()) // 2, flush=True)
INF = 10 ** 9


def csa(orixes, t0):
    """Chegada máis temperá a cada parada saíndo das paradas orixe ás t0 (minutos dende medianoite).
    Súbese a un vehículo se xa se vai nel ou se se chega á parada 2 minutos antes de que saia."""
    T = [INF] * len(ids)
    en = [False] * len(trips)
    for o, tw in orixes:
        T[o] = min(T[o], t0 + tw - 2)  # na orixe non fai falta marxe de transbordo
        for j, tc in camina[o]:
            T[j] = min(T[j], t0 + tw + tc - 2)
    for k in range(int(np.searchsorted(C_d, t0)), int(np.searchsorted(C_d, t0 + MAX))):
        v = C_v[k]
        if en[v] or T[C_f[k]] + 2 <= C_dl[k]:
            en[v] = True
            a, t = C_a[k], C_t[k]
            if a < T[t]:
                T[t] = a
                for j, tc in camina[t]:
                    if a + tc < T[j]:
                        T[j] = a + tc
    return T


out = {"orixes": {}, "dia": DIA}
for nome, (lat, lon) in ORIXES.items():
    p = np.array(mxy(lat, lon))
    oo = [(i, math.ceil(np.linalg.norm(XY[i] - p) * 1.3 / (4000 / 60))) for i in arb.query_ball_point(p, 1500)]
    mellor = defaultdict(lambda: INF)
    for t0 in SAIDAS:
        T = csa(oo, t0)
        for i, t in enumerate(T):
            c = paradas[ids[i]]["c"]
            if c and t < INF:
                mellor[c] = min(mellor[c], t - t0)
    out["orixes"][nome] = {c: v for c, v in mellor.items() if v <= MAX}
    v = sorted(out["orixes"][nome].values())
    print(f"{nome:10} paradas orixe {len(oo):3} · concellos alcanzados {len(v)} · mediana {v[len(v) // 2]} min", flush=True)

# Paradas por concello (para dicir onde non hai ningunha)
out["conParada"] = sorted({p["c"] for p in paradas.values() if p["c"]})
mc = json.loads((HERE.parent / "monte-concellos" / "data" / "datos.json").read_text(encoding="utf-8"))
out["conc"] = [{"id": c["id"], "n": c["n"], "pr": c["pr"], "pol": c["pol"]} for c in mc["concellos"]]
xs = [p[0] for c in out["conc"] for r in c["pol"] for p in r]
ys = [p[1] for c in out["conc"] for r in c["pol"] for p in r]
out["bbox"] = [min(xs), min(ys), max(xs), max(ys)]
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json")

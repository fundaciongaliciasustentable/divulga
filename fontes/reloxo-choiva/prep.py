#!/usr/bin/env python3
"""Choiva horaria de seis estacións de MeteoGalicia, 2016-2025 → data/datos.json

Fonte: MeteoGalicia, servizo JSON de datos horarios históricos das estacións
  https://servizos.meteogalicia.gal/mgrss/observacion/datosHorariosEstacions.action
  (doc.: https://meteo-estaticos.xunta.gal/datosred/infoweb/meteo/docs/rss/JSON_EstacionHorariosHistoricos_gl.pdf)
O servizo dá como moito 12 horas e 6 estacións por petición, así que a descarga é longa
(uns 7.300 pedidos). Vaise gardando un ficheiro por mes en data/raw/ e retoma onde quedou.

Parámetro: PP_SUM_1.5m, choiva acumulada na hora (L/m² = mm). Só se usan os datos con código
de validación 1 (válido orixinal) ou 5 (válido interpolado). As horas pásanse de UTC á hora
oficial de Galicia (Europe/Madrid), que é a que vive a xente.
"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import urlopen
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
URL = ("https://servizos.meteogalicia.gal/mgrss/observacion/datosHorariosEstacions.action"
       "?dataIni={}&numHoras=12&idEst={}&idParam=PP_SUM_1.5m")
EST = {10157: "A Coruña", 10124: "Santiago", 10053: "Lugo", 10156: "Pontevedra", 10142: "Vigo", 10148: "Ourense"}
A0, A1 = 2016, 2025
TZ = ZoneInfo("Europe/Madrid")


def baixa_mes(ano, mes):
    f = RAW / f"{ano}-{mes:02d}.json"
    if f.exists():
        return
    ini = datetime(ano, mes, 1, tzinfo=timezone.utc)
    fin = datetime(ano + (mes == 12), mes % 12 + 1, 1, tzinfo=timezone.utc)
    out = {str(k): {} for k in EST}
    t = ini
    while t < fin:
        for intento in range(5):
            try:
                d = json.load(urlopen(URL.format(t.strftime("%d/%m/%Y%%20%H:%M"), ",".join(map(str, EST))), timeout=60))
                break
            except Exception as e:  # o servizo falla de cando en vez: espera e volve
                if intento == 4:
                    raise
                time.sleep(5 * (intento + 1))
        for e in d["listHorarios"]:
            for i in e["listaInstantes"]:
                for m in i["listaMedidas"]:
                    if m["codigoParametro"] == "PP_SUM_1.5m" and m["lnCodigoValidacion"] in (1, 5) and m["valor"] >= 0:
                        out[str(e["idEstacion"])][i["instanteLecturaUTC"]] = m["valor"]
        t += timedelta(hours=12)
        time.sleep(0.2)
    RAW.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(out, separators=(",", ":")))
    print(f"{ano}-{mes:02d}", {EST[int(k)]: len(v) for k, v in out.items()}, flush=True)


meses = [(a, m) for a in range(A0, A1 + 1) for m in range(1, 13)]
if "--parcial" in sys.argv:  # para probar a páxina mentres descarga: só os meses xa gardados
    meses = [am for am in meses if (RAW / f"{am[0]}-{am[1]:02d}.json").exists()]
else:
    with ThreadPoolExecutor(2) as ex:  # dous fíos: abondo rápido sen cargar o servizo
        list(ex.map(lambda am: baixa_mes(*am), meses))
if "--so-descarga" in sys.argv:
    sys.exit()

# Agregado: para cada estación, mes (1-12) e hora local (0-23), choiva media por hora (mm)
# e frecuencia de horas con choiva (≥ 0,2 mm, a resolución habitual do pluviómetro é 0,1-0,2).
ac = {k: [[[0.0, 0, 0] for _ in range(24)] for _ in range(12)] for k in EST}
for a, m in meses:
    for k, serie in json.loads((RAW / f"{a}-{m:02d}.json").read_text()).items():
        for ts, v in serie.items():
            loc = datetime.fromisoformat(ts).replace(tzinfo=timezone.utc).astimezone(TZ)
            c = ac[int(k)][loc.month - 1][loc.hour]
            c[0] += v
            c[1] += 1
            c[2] += v >= 0.2
out = {"anos": [A0, A1], "est": []}
for k, nome in EST.items():
    g = ac[k]
    n = sum(c[1] for mes in g for c in mes)
    mm = [[round(c[0] / c[1], 4) if c[1] else None for c in mes] for mes in g]
    fr = [[round(c[2] / c[1], 4) if c[1] else None for c in mes] for mes in g]
    anual = sum(c[0] / c[1] for mes in g for c in mes if c[1]) * 365.25 / 12  # mm/ano a partir das medias
    out["est"].append({"id": k, "n": nome, "horas": n, "cob": round(n / (365.25 * 24 * (A1 - A0 + 1)), 3),
                       "mm": mm, "fr": fr, "anual": round(anual)})
    print(f"{nome:10} {n:6} horas ({n / (365.25 * 24 * (A1 - A0 + 1)):.0%}), {anual:.0f} mm/ano")
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json")

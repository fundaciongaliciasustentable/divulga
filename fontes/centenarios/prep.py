#!/usr/bin/env python3
"""Persoas de 100 anos ou máis por cada 10.000 habitantes: provincias de España e rexións NUTS 2 da UE → data/datos.json

Fontes (gardadas en data/raw/):
  - INE, Estatística Continua de Poboación (ECP), táboa 69792 «Población residente por fecha, sexo y edad
    (desde 1971)», por provincia; series de «100 y más años» e «Todas las edades», ambos sexos (API Tempus JSON):
    https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/69792?tv=357:15071&tv=18:451&nult=120
    https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/69792?tv=356:15668&tv=18:451&nult=120
    (táboa web: https://www.ine.es/jaxiT3/Tabla.htm?t=69792). Úsase a poboación a 1 de xaneiro de cada ano.
  - Eurostat, demo_r_d2jan «Population on 1 January by age, sex and NUTS 2 region», idades TOTAL, Y99 e
    Y_OPEN (clase aberta = 100 anos ou máis cando a idade 99 vén desagregada), ambos sexos:
    https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_r_d2jan?format=JSON&lang=EN&sex=T&age=Y_OPEN&age=Y99&age=TOTAL&time=<ano>
    Alemaña non publica idade simple por rexión e queda fóra.
"""
import datetime as dt
import json
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
INE = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/69792?tv={}&tv=18:451&nult=120"
EST = ("https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_r_d2jan?format=JSON&lang=EN&sex=T"
       "&age=Y_OPEN&age=Y99&age=TOTAL&time={}")
A0 = 2006  # ano de partida da comparación provincial
EU = "AT BE BG CY CZ DE DK EE EL ES FI FR HR HU IE IT LT LU LV MT NL PL PT RO SE SI SK".split()
PAIS = {"AT": "Austria", "BE": "Bélxica", "BG": "Bulgaria", "CY": "Chipre", "CZ": "Chequia", "DE": "Alemaña", "DK": "Dinamarca",
        "EE": "Estonia", "EL": "Grecia", "ES": "España", "FI": "Finlandia", "FR": "Francia", "HR": "Croacia", "HU": "Hungría",
        "IE": "Irlanda", "IT": "Italia", "LT": "Lituania", "LU": "Luxemburgo", "LV": "Letonia", "MT": "Malta", "NL": "Países Baixos",
        "PL": "Polonia", "PT": "Portugal", "RO": "Romanía", "SE": "Suecia", "SI": "Eslovenia", "SK": "Eslovaquia"}


def get(url, f):
    f = RAW / f
    if not f.exists():
        f.write_bytes(urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=180).read())
        print("descargado", f.name)
    return json.loads(f.read_text(encoding="utf-8"))


RAW.mkdir(parents=True, exist_ok=True)
c100 = get(INE.format("357:15071"), "ine_69792_100.json")
ctot = get(INE.format("356:15668"), "ine_69792_total.json")
dia = lambda x: dt.datetime.fromtimestamp(x["Fecha"] / 1000 + 7200, dt.UTC).strftime("%Y-%m-%d")
FORA = {"Todas las edades", "100 y más años", "Total", "Población", "Número", ""}
nom = lambda s: [q.strip() for q in s["Nombre"].split(".") if q.strip() not in FORA][0]


def series(js):
    """{provincia: {ano: (valor, provisional)}} só co 1 de xaneiro."""
    return {nom(s): {int(dia(x)[:4]): (x["Valor"], x["FK_TipoDato"] == 2) for x in s["Data"] if dia(x).endswith("-01-01")} for s in js}


S100, STOT = series(c100), series(ctot)
ult = max(a for a in S100["Total Nacional"])
prov_ult = S100["Total Nacional"][ult][1]


def bonito(n):
    """«Coruña, A» → «A Coruña»; «Alicante/Alacant» queda igual."""
    if ", " in n:
        a, b = n.split(", ")
        return f"{b} {a}"
    return n


GAL = {"Coruña, A", "Lugo", "Ourense", "Pontevedra"}
prov = []
for p in S100:
    anos = sorted(a for a in S100[p] if a >= A0 - 4 and a in STOT[p])
    serie = [[a, int(S100[p][a][0]), int(STOT[p][a][0])] for a in anos]
    prov.append({"n": bonito(p), "g": p in GAL, "t": p == "Total Nacional", "s": serie})
# Europa
eur = {}
for ano in range(ult, ult - 3, -1):
    d = get(EST.format(ano), f"demo_r_d2jan_{ano}.json")
    if "value" not in d:
        continue
    g = d["dimension"]["geo"]["category"]
    gi, n, a, v = g["index"], len(g["index"]), d["dimension"]["age"]["category"]["index"], d["value"]
    x = lambda geo, k: v.get(str(a[k] * n + gi[geo]))
    filas = [[geo, g["label"][geo], int(x(geo, "Y_OPEN")), int(x(geo, "TOTAL"))] for geo in gi
             if len(geo) == 4 and geo[:2] in EU and not geo.endswith("ZZ")
             and x(geo, "Y_OPEN") is not None and x(geo, "Y99") is not None and x(geo, "TOTAL")]
    if len(filas) > 150:
        eur = {"ano": ano, "reg": filas}
        break
out = {"ult": ult, "prov_ult": prov_ult, "a0": A0, "prov": prov, "eur": eur, "pais": PAIS}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
tasa = lambda s: s[1] / s[2] * 1e4
rk = sorted((p for p in prov if not p["t"]), key=lambda p: -tasa(p["s"][-1]))
print(f"ok: {len(prov)} series provinciais, último 1 de xaneiro {ult} (provisional: {prov_ult})")
for i, p in enumerate(rk):
    if i < 6 or p["g"]:
        print(f"  {i + 1:2} {p['n']:12} {tasa(p['s'][-1]):5.2f} por 10.000 · {p['s'][-1][1]} centenarios")
er = sorted(eur["reg"], key=lambda r: -r[2] / r[3])
print(f"Europa {eur['ano']}: {len(er)} rexións; Galicia posto {[r[0] for r in er].index('ES11') + 1}")

#!/usr/bin/env python3
"""Anos de salario medio para pagar unha vivenda de 90 m², provincia a provincia → data/datos.json

Fontes:
  · Ministerio de Vivenda e Axenda Urbana (MIVAU), «Valor tasado medio de vivienda libre»,
    táboa 1 por comunidades autónomas e provincias, trimestral (euros/m²):
    https://apps.fomento.gob.es/BoletinOnline2/sedal/35101000.XLS
    (índice: https://www.mivau.gob.es/el-ministerio/informacion-estadistica/vivienda-y-actuaciones-urbanas/estadisticas/valor-tasado-de-la-vivienda)
    Úsase a media dos catro trimestres de 2024.
  · Axencia Tributaria, «Mercado de trabajo y pensiones en las fuentes tributarias» 2024,
    «Asalariados, percepciones salariales y salarios por provincia, edad y sexo» (salario medio
    anual por asalariado, total):
    https://sede.agenciatributaria.gob.es/AEAT/Contenidos_Comunes/La_Agencia_Tributaria/Estadisticas/Publicaciones/sites/mercado/2024/jrubik3b8d66844e89628e7ab18a9fbf657c4c36b75a82.html
    Non inclúe País Vasco nin Navarra (teñen facenda propia).
Método: anos = (valor tasado medio do m² × 90 m²) ÷ salario medio anual bruto. Sen gastos,
impostos, xuros nin entrada: é unha medida de esforzo, non o custo real dunha hipoteca.
Precisa xlrd (pip install xlrd). Ficheiros gardados en data/raw/.
"""
import html
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

import xlrd

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0"}
F = {"mivau_35101000.xls": "https://apps.fomento.gob.es/BoletinOnline2/sedal/35101000.XLS",
     "aeat_2024_provincia.html": "https://sede.agenciatributaria.gob.es/AEAT/Contenidos_Comunes/La_Agencia_Tributaria/Estadisticas/"
                                 "Publicaciones/sites/mercado/2024/jrubik3b8d66844e89628e7ab18a9fbf657c4c36b75a82.html"}
for n, u in F.items():
    if not (RAW / n).exists():
        (RAW / n).write_bytes(urlopen(Request(u, headers=UA), timeout=180).read())
ANO, M2 = 2024, 90

# Nome do MIVAU → nome curto común
MIV = {"Asturias (Principado de )": "Asturias", "Balears (Illes)": "Illes Balears", "Palmas (Las)": "Las Palmas",
       "Santa Cruz de Tenerife": "S. C. de Tenerife", "Coruña (A)": "A Coruña", "Madrid (Comunidad de)": "Madrid",
       "Murcia (Región de)": "Murcia", "Rioja (La)": "La Rioja", "Alicante/Alacant": "Alicante", "Castellón/Castelló": "Castellón",
       "Valencia/València": "Valencia", "Cantabria": "Cantabria", "Galicia": "Galicia"}
AE = {"Asturias, Principado de": "Asturias", "Balears,Illes": "Illes Balears", "S. C. Tenerife": "S. C. de Tenerife",
      "Madrid, Comunidad de": "Madrid", "Murcia, Región de": "Murcia", "Rioja, La": "La Rioja"}
CCAA_MIV = {"Andalucía", "Aragón", "Canarias", "Castilla y León", "Castilla-La Mancha", "Cataluña", "Comunidad Valenciana",
            "Extremadura", "País Vasco", "Ceuta y Melilla", "Navarra (Comunidad Foral de)", "TOTAL NACIONAL"}
s = xlrd.open_workbook(RAW / "mivau_35101000.xls").sheet_by_name(next(n for n in xlrd.open_workbook(RAW / "mivau_35101000.xls").sheet_names()
                                                                        if str(ANO) in n))
cab = s.row_values(11)
c0 = next(i for i, v in enumerate(cab) if str(ANO) in str(v))
prezo = {}
for i in range(14, s.nrows):
    r = s.row_values(i)
    n = str(r[1]).strip()
    if not n or n in CCAA_MIV or not isinstance(r[c0], float):
        continue
    prezo[MIV.get(n, n)] = sum(r[c0:c0 + 4]) / 4

t = (RAW / "aeat_2024_provincia.html").read_text(encoding="utf-8")
filas = re.findall(r'<div class="depth_div_(\d)">([^<]+)</div>\s*</th>((?:<td[^>]*>[^<]*</td>)+)', t)
sal, ccaa, actual = {}, {}, None
for k, (dep, n, tds) in enumerate(filas):
    n = html.unescape(n).strip()
    v = int(re.findall(r">([^<]*)</td>", tds)[-1].replace(".", ""))
    if dep == "1":
        actual = n
        fillos = k + 1 < len(filas) and filas[k + 1][0] == "2"
        if not fillos:  # comunidade uniprovincial
            sal[AE.get(n, n)] = (v, AE.get(n, n))
        if n == "Galicia":
            sal["Galicia"] = (v, "Galicia")
    elif dep == "2":
        sal[AE.get(n, n)] = (v, actual)
CC = {"Asturias, Principado de": "Asturias", "Balears,Illes": "Illes Balears", "Madrid, Comunidad de": "Madrid",
      "Murcia, Región de": "Murcia", "Rioja, La": "La Rioja", "Castilla - La Mancha": "Castilla-La Mancha"}
prov = []
for n, (v, cc) in sal.items():
    if n == "Galicia":
        continue
    p = prezo[n]
    prov.append({"n": n, "cc": CC.get(cc, cc), "m2": round(p), "s": v, "a": round(p * M2 / v, 2)})
sem = sorted(set(prezo) - set(sal))
print("só no MIVAU (sen salario da AEAT):", sem)
prov.sort(key=lambda x: -x["a"])
g = {"m2": round(prezo["Galicia"]), "s": sal["Galicia"][0]}
g["a"] = round(g["m2"] * M2 / g["s"], 2)
print(len(prov), "provincias; Galicia", g)
for i, x in enumerate(prov):
    print(f"{i + 1:3} {x['n']:20} {x['a']:5.2f} anos  ({x['m2']} €/m² · {x['s']} €)")
out = {"ano": ANO, "m2": M2, "prov": prov, "gal": g}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json")

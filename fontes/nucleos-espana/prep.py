#!/usr/bin/env python3
"""Entidades singulares de poboación por comunidade autónoma → data/datos.json

Fontes:
  INE, Nomenclátor. Población del Padrón Continuo por unidad poblacional a 1 de enero de 2025,
    fichero nacional (ZIP), na páxina de resultados da operación:
    https://www.ine.es/dyngs/INEbase/operacion.htm?c=Estadistica_C&cid=1254736177010&menu=resultados&idp=1254735572981
    O ZIP descárgase cun POST a https://www.ine.es/nomen2/Descarga con anioNacional=2025.
    Úsase Nomdef2025_sex.txt: rexistros de ancho fixo, código de 11 díxitos
    PP MMM CC SS NN (provincia, municipio, entidade colectiva, entidade singular, núcleo/diseminado),
    nome e poboación total, homes e mulleres. Unha entidade singular é o rexistro con SS ≠ 00 e NN = 00.
    Deseño do rexistro: https://www.ine.es/nomen_files/DisenioRegistro.xls
  Superficie por comunidade autónoma (km²): Dirección General del Instituto Geográfico Nacional,
    recollida no Anuario de Estadística 2023 do MAPA, táboa 1.1 «Distribución por provincias y
    comunidades autónomas de la extensión superficial total»:
    https://mapa.gob.es/estadistica/pags/anuario/2023/FORMATO%20PDF/AE23-C01/1.1.pdf

Precisa pypdf (python3 -m pip install pypdf).
"""
import io
import json
import re
import statistics
import zipfile
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pypdf

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
ANO = 2025
UA = {"User-Agent": "Mozilla/5.0"}

CCAA = [  # nome en galego, código curto, provincias INE
    ("Andalucía", "AN", [4, 11, 14, 18, 21, 23, 29, 41]),
    ("Aragón", "AR", [22, 44, 50]),
    ("Asturias", "AS", [33]),
    ("Illes Balears", "IB", [7]),
    ("Canarias", "CN", [35, 38]),
    ("Cantabria", "CB", [39]),
    ("Castela e León", "CL", [5, 9, 24, 34, 37, 40, 42, 47, 49]),
    ("Castela-A Mancha", "CM", [2, 13, 16, 19, 45]),
    ("Cataluña", "CT", [8, 17, 25, 43]),
    ("C. Valenciana", "VC", [3, 12, 46]),
    ("Estremadura", "EX", [6, 10]),
    ("Galicia", "GA", [15, 27, 32, 36]),
    ("Madrid", "MD", [28]),
    ("Murcia", "MC", [30]),
    ("Navarra", "NC", [31]),
    ("País Vasco", "PV", [1, 20, 48]),
    ("A Rioxa", "RI", [26]),
    ("Ceuta", "CE", [51]),
    ("Melilla", "ML", [52]),
]
MAPA = {"GALICIA": "GA", "P. DE ASTURIAS": "AS", "CANTABRIA": "CB", "PAÍS VASCO": "PV", "NAVARRA": "NC",
        "LA RIOJA": "RI", "ARAGÓN": "AR", "CATALUÑA": "CT", "BALEARES": "IB", "CASTILLA Y LEÓN": "CL",
        "MADRID": "MD", "CASTILLA – LA MANCHA": "CM", "C. VALENCIANA": "VC", "R. DE MURCIA": "MC",
        "EXTREMADURA": "EX", "ANDALUCÍA": "AN", "CANARIAS": "CN", "Ceuta": "CE", "Melilla": "ML", "ESPAÑA": "ES"}


def get(url, data=None):
    return urlopen(Request(url, data=data, headers=UA), timeout=600).read()


# 1. Nomenclátor nacional
zf = RAW / f"nomen_nacional_{ANO}.zip"
if not zf.exists():
    zf.write_bytes(get("https://www.ine.es/nomen2/Descarga", urlencode({"anioNacional": ANO}).encode()))
txt = zipfile.ZipFile(zf).read(f"Nomdef{ANO}_sex.txt").decode("utf-8")
ent = {}  # provincia → lista de poboacións das entidades singulares
munis = {}
for l in txt.splitlines():
    c = l[:11]
    if not c.isdigit():
        continue
    pob = int(l.rstrip("\r")[-21:-14])  # tres campos de 7 caracteres: total, homes, mulleres
    p = int(c[:2])
    if c[5:] == "000000":
        munis[p] = munis.get(p, 0) + 1
    if c[7:9] != "00" and c[9:11] == "00":
        ent.setdefault(p, []).append(pob)

# 2. Superficies
pdf = RAW / "mapa_1.1.pdf"
if not pdf.exists():
    pdf.write_bytes(get("https://mapa.gob.es/estadistica/pags/anuario/2023/FORMATO%20PDF/AE23-C01/1.1.pdf"))
sup = {}
for l in pypdf.PdfReader(pdf).pages[0].extract_text().splitlines():
    m = re.match(r"^\s*(.+?)\s+(\d{1,3}(?:\.\d{3})*)\s", l)
    if m and m.group(1).strip() in MAPA:
        sup[MAPA[m.group(1).strip()]] = int(m.group(2).replace(".", ""))
assert len(sup) == 20, sup

out = []
for nome, cod, provs in CCAA:
    pobs = [x for p in provs for x in ent[p]]
    con = [x for x in pobs if x > 0]
    out.append({"c": cod, "n": nome, "es": len(pobs), "hab": len(con), "pob": sum(pobs), "km2": sup[cod],
                "mun": sum(munis[p] for p in provs), "med": statistics.median(con), "lt50": sum(1 for x in con if x < 50),
                "prov": {f"{p:02d}": len(ent[p]) for p in provs}})
    print(f"{nome:18s} {len(pobs):6d} entidades  {sup[cod]:6d} km²  {len(pobs) / sup[cod] * 100:6.1f} /100 km²")
tot = sum(o["es"] for o in out)
ga = next(o for o in out if o["c"] == "GA")
print(f"España: {tot} · Galicia: {ga['es']} ({ga['es'] / tot:.1%})")
(HERE / "data" / "datos.json").write_text(json.dumps({"ano": ANO, "km2_es": sup["ES"], "ccaa": out},
                                                     ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

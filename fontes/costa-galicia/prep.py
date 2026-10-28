#!/usr/bin/env python3
"""Quilómetros de costa: Galicia fronte ás outras comunidades e fronte a Europa → data/datos.json

Fontes:
  IGN (Dirección General del Instituto Geográfico Nacional), «Longitud de la costa por provincias.
    Sin islas e islotes las provincias peninsulares», recollida polo INE no Anuario Estadístico de
    España 2008, táboa 1.1.3 (e 1.1.2, lonxitude das costas e fronteiras):
    https://ine.es/prodyser/pubweb/anuario08/anu08_01entor.pdf
  MITECO, Dirección General de la Costa y el Mar: lonxitude do dominio público marítimo-terrestre
    (DPM-T) por provincia, no Anuario de Estadística 2017 do MAPA, táboa 9.3:
    https://servicio.mapa.gob.es/estadistica/pags/anuario/2017/CAPITULOSPDF/CAPITULO09/pdfc09_3.pdf
  CIA, The World Factbook, campo «Coastline» (última edición, xa retirada da web da CIA), copia
    arquivada en Internet Archive o 3/2/2026:
    http://web.archive.org/web/20260203220455/https://www.cia.gov/the-world-factbook/page-data/field/coastline/page-data.json

Precisa pypdf (python3 -m pip install pypdf).
"""
import gzip
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

import pypdf

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "gzip"}
URLS = {
    "ine_anu08_01entor.pdf": "https://ine.es/prodyser/pubweb/anuario08/anu08_01entor.pdf",
    "pdfc09_3.pdf": "https://servicio.mapa.gob.es/estadistica/pags/anuario/2017/CAPITULOSPDF/CAPITULO09/pdfc09_3.pdf",
    "factbook_coastline.json": "http://web.archive.org/web/20260203220455/https://www.cia.gov/the-world-factbook/page-data/field/coastline/page-data.json",
}
for f, u in URLS.items():
    if not (RAW / f).exists():
        r = urlopen(Request(u, headers=UA), timeout=180)
        b = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            b = gzip.decompress(b)
        (RAW / f).write_bytes(b)
        print("descargado", f)

num = lambda s: float(s.replace(".", "").replace(",", ".")) if "," in s else float(s.replace(".", ""))
# Provincia → comunidade (nomes como aparecen nas táboas)
PROV = {"Guipúzcoa": "PV", "Gipuzkoa": "PV", "Vizcaya": "PV", "Cantabria": "CB", "Asturias": "AS", "Lugo": "GA",
        "Coruña ( A)": "GA", "A Coruña": "GA", "Pontevedra": "GA", "Huelva": "AN", "Cádiz": "AN", "Málaga": "AN",
        "Granada": "AN", "Almería": "AN", "Sevilla": "AN", "Murcia": "MC", "Alicante/Alacant": "VC", "Alicante": "VC",
        "Valencia/València": "VC", "Valencia": "VC", "Castellón/Castelló": "VC", "Castellón": "VC", "Tarragona": "CT",
        "Barcelona": "CT", "Girona": "CT", "Balears (Illes)": "IB", "Palmas (Las)": "CN", "Las Palmas": "CN",
        "Santa Cruz de Tenerife": "CN", "S.C. de Tenerife": "CN", "Ceuta": "CE", "Melilla": "ML",
        # comunidades uniprovinciais na táboa do MITECO
        "BALEARES": "IB", "P. DE ASTURIAS": "AS", "CANTABRIA": "CB", "R. DE MURCIA": "MC"}
NOME = {"GA": "Galicia", "AS": "Asturias", "CB": "Cantabria", "PV": "País Vasco", "CT": "Cataluña", "IB": "Illes Balears",
        "VC": "C. Valenciana", "MC": "Murcia", "AN": "Andalucía", "CN": "Canarias", "CE": "Ceuta", "ML": "Melilla"}

# 1. IGN, táboa 1.1.3 (dúas columnas de «provincia número»)
t = pypdf.PdfReader(RAW / "ine_anu08_01entor.pdf").pages[7].extract_text()
bloque = t[t.index("1.1.3. Longitud de la costa por provincias"):]
ign_prov = {}
for l in bloque.splitlines():
    for nom, v in re.findall(r"([A-ZÁÉÍÓÚ][^\d]+?)\s+(\d{1,3}(?:\.\d{3})?)(?=\s|$)", l):
        if nom.strip() in PROV:
            ign_prov[nom.strip()] = num(v)
ign_extra = {k: num(v) for k, v in re.findall(r"Ciudad de (Ceuta|Melilla) (\d+)", t)[:2]}
ign_prov.update(ign_extra)
assert len(ign_prov) == 24, ign_prov
peninsula = num(re.search(r"Total de las costas (\d\.\d{3})", t).group(1))

# 2. MITECO DPM-T, táboa 9.3
t2 = pypdf.PdfReader(RAW / "pdfc09_3.pdf").pages[0].extract_text()
dpm_prov = {}
for l in t2.splitlines():
    m = re.match(r"^\s*([A-Za-zÁÉÍÓÚáéíóúñ./ ]+?)\s+(\d{1,3}(?:\.\d{3})*,\d)\s", l)
    if m and m.group(1).strip() in PROV:
        dpm_prov[m.group(1).strip()] = num(m.group(2))
m = re.search(r"ESPAÑA\s+(\d+)[.,](\d{3}),(\d)", t2)
dpm_es = float(f"{m.group(1)}{m.group(2)}.{m.group(3)}")

ccaa = {}
for src, d in (("ign", ign_prov), ("dpm", dpm_prov)):
    for p, v in d.items():
        c = ccaa.setdefault(PROV[p], {"c": PROV[p], "n": NOME[PROV[p]], "ign": 0, "dpm": 0, "pi": {}, "pd": {}})
        c[src] += v
        c["pi" if src == "ign" else "pd"][p] = v
for c in ccaa.values():
    c["ign"], c["dpm"] = round(c["ign"], 1), round(c["dpm"], 1)
ign_es = sum(ign_prov.values())

# 3. World Factbook
fb = json.loads((RAW / "factbook_coastline.json").read_text(encoding="utf-8"))
PAIS = {"Albania": "Albania", "Belgium": "Bélxica", "Bulgaria": "Bulgaria", "Croatia": "Croacia", "Cyprus": "Chipre",
        "Denmark": "Dinamarca", "Estonia": "Estonia", "Finland": "Finlandia", "France": "Francia", "Germany": "Alemaña",
        "Greece": "Grecia", "Iceland": "Islandia", "Ireland": "Irlanda", "Italy": "Italia", "Latvia": "Letonia",
        "Lithuania": "Lituania", "Malta": "Malta", "Montenegro": "Montenegro", "Netherlands": "Países Baixos",
        "Norway": "Noruega", "Poland": "Polonia", "Portugal": "Portugal", "Romania": "Romanía", "Slovenia": "Eslovenia",
        "Spain": "España", "Sweden": "Suecia", "Ukraine": "Ucraína", "United Kingdom": "Reino Unido"}
paises = []
for n in fb["result"]["data"]["fields"]["nodes"]:
    if n["placeName"] in PAIS:
        f = n["formatted"]
        v = re.search(r"metropolitan France:(?:&nbsp;|\s|</strong>)*([\d,.]+) km", f) if n["placeName"] == "France" else None
        v = v or re.match(r"([\d,.]+) km", f)
        paises.append({"n": PAIS[n["placeName"]], "en": n["placeName"], "km": float(v.group(1).replace(",", "")),
                       "nota": re.sub(r"<[^>]+>|&nbsp;", " ", f).strip()})
assert len(paises) == len(PAIS), [p["en"] for p in paises]
nor = next(p for p in paises if p["en"] == "Norway")["nota"]
extra = {"noruega_continente": float(re.search(r"mainland at ([\d,]+)", nor).group(1).replace(",", "")),
         "noruega_illas": float(re.search(r"island coastlines is ([\d,]+)", nor).group(1).replace(",", ""))}
out = {"ccaa": sorted(ccaa.values(), key=lambda c: -c["ign"]), "paises": sorted(paises, key=lambda p: -p["km"]),
       "es": {"ign": ign_es, "ign_peninsula": peninsula, "dpm": dpm_es,
              "fb": next(p["km"] for p in paises if p["en"] == "Spain")}, **extra}
for c in out["ccaa"]:
    print(f"{c['n']:15s} IGN {c['ign']:7.1f}  DPM-T {c['dpm']:7.1f}")
print("España IGN", ign_es, "DPM-T", dpm_es, "Factbook", out["es"]["fb"])
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

#!/usr/bin/env python3
"""Os nomes máis frecuentes en Galicia por década de nacemento e ano a ano → data/datos.json

Fontes (IGE):
  · Nomes máis frecuentes da poboación segundo a década de nacemento (os 30 primeiros por sexo,
    para Galicia e cada provincia), a partir do padrón:
    https://www.ige.gal/igebdt/onomast/nomdecadas.jsp?idioma=gl&codigo=12&sexo=1&cind=1;2;…;11
    (sexo 1 = homes, 6 = mulleres; codigo 12 = Galicia, 15/27/32/36 = provincias)
  · Estatística de nomes dos neonatos galegos, táboa 2245 (os 50 primeiros de cada ano, 2000-2024,
    con frecuencia): https://www.ige.gal/igebdt/igeapi/csv/datos/2245
As páxinas e o CSV gárdanse en data/raw/ (descárganse se faltan).
"""
import csv
import html
import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
UA = {"User-Agent": "Mozilla/5.0"}
DEC = "https://www.ige.gal/igebdt/onomast/nomdecadas.jsp?idioma=gl&codigo={c}&sexo={s}&cind=1;2;3;4;5;6;7;8;9;10;11"
AREAS = {"12": "Galicia", "15": "A Coruña", "27": "Lugo", "32": "Ourense", "36": "Pontevedra"}
SEXO = {"H": 1, "M": 6}
DECADAS = ["antes de 1930", "1930", "1940", "1950", "1960", "1970", "1980", "1990", "2000", "2010", "2020"]
# Formas propias do galego (non as que comparte co castelán), para marcalas no gráfico
GALEGOS = {"XOAN", "XAN", "XOSE", "XURXO", "XABIER", "IAGO", "BRAIS", "ANXO", "ROI", "LOIS", "MARTIÑO", "BREIXO",
           "UXIO", "ANTON", "UXIA", "ANTIA", "XIANA", "SABELA", "IRIA", "EREA", "NOELA", "ALDARA", "LUA", "ICIA",
           "TAREIXA", "XULIA", "XOANA", "BIEITO"}


def norm(n):
    """O IGE escribe uns nomes con til e outros sen (ANTIA, ANTÍA): unifícanse sen til, gardando o Ñ."""
    import unicodedata
    n = n.replace("Ñ", "\0")
    n = "".join(c for c in unicodedata.normalize("NFD", n) if unicodedata.category(c) != "Mn")
    return n.replace("\0", "Ñ").strip()


def baixa(nome, url):
    f = RAW / nome
    if not f.exists():
        RAW.mkdir(parents=True, exist_ok=True)
        f.write_bytes(urlopen(Request(url, headers=UA), timeout=120).read())
    return f


def decadas(area, sexo):
    s = baixa(f"dec_{area}_{sexo}.html", DEC.format(c=area, s=SEXO[sexo])).read_text(encoding="utf-8", errors="replace")
    t = re.findall(r"<table.*?</table>", s[s.find("</form>", s.find("fselec")):], re.S)[0]
    filas = [[html.unescape(re.sub(r"<[^>]+>|\s+", " ", c)).strip() for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", r, re.S)]
             for r in re.findall(r"<tr.*?</tr>", t, re.S)]
    assert len(filas[0]) == 12 and len(filas) == 31, (area, sexo, len(filas), filas[0])
    return [[norm(f[1 + j]) for f in filas[1:]] for j in range(11)]  # por década, os 30 nomes en orde


dec = {a: {s: decadas(a, s) for s in SEXO} for a in AREAS}

ano = {"H": defaultdict(dict), "M": defaultdict(dict)}
f = baixa("ige_2245.csv", "https://www.ige.gal/igebdt/igeapi/csv/datos/2245")
for x in csv.DictReader(f.open(encoding="latin1")):
    if x["CodEspazo"] != "12":
        continue
    s = "H" if x["Sexo"] == "Nenos" else "M"
    k = (int(x["Tempo"]), int(x["Orde"]))
    if x["Datos"] == "Nome":
        ano[s][k[0]].setdefault(k[1], {})["n"] = norm(x["DatoT"])
    elif x["Datos"] == "Frecuencia":
        ano[s][k[0]].setdefault(k[1], {})["f"] = int(x["DatoN"])
anos = sorted(ano["H"])
serie = {s: {str(a): [[ano[s][a][o]["n"], ano[s][a][o]["f"]] for o in sorted(ano[s][a])] for a in anos} for s in SEXO}

for s in SEXO:
    print(s, "décadas:", [d[0] for d in dec["12"][s]])
    print(s, "anos:", {a: serie[s][str(a)][0] for a in (anos[0], anos[-1])})
gal = sorted({n for a in dec for s in SEXO for d in dec[a][s] for n in d} | {n for s in SEXO for v in serie[s].values() for n, _ in v})
print("nomes en galego presentes:", sorted(set(gal) & GALEGOS))
out = {"dec": dec, "decadas": DECADAS, "areas": AREAS, "anos": serie, "galegos": sorted(set(gal) & GALEGOS)}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json")

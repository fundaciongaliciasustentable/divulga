#!/usr/bin/env python3
"""Eleccións autonómicas, municipais e xerais por concello, 2000-2024, nun mapa de hexágonos → data/datos.json

Fontes:
  · Parlamento de Galicia (2001-2024): Xunta de Galicia, Abert@s, «Eleccións ao Parlamento de
    Galicia - resultados AAAA» (CSV por concello): https://abertos.xunta.gal/catalogo/administracion-publica/
    As de 1981 a 1997 non están publicadas por concello como datos abertos.
  · Municipais (2003-2023) e xerais ao Congreso (2000-2023): Ministerio do Interior, Infoelectoral,
    ficheiros por municipio (tipo 04 e 02):
    https://infoelectoral.interior.gob.es/estaticos/docxl/apliextr/TTAAAAMM_MUNI.zip
    De largo fixo: o 03 trae as candidaturas, o 05 os datos de cada municipio (votos en branco e a
    candidaturas) e o 06 os votos de cada candidatura en cada municipio (distrito 99 = total).
    Nas municipais cóntanse os votos ás listas ao concello, non quen acabou de alcalde.
Os CSV cambian de formato dun ano a outro (codificación, separador de miles, columnas), así que
se len de xeito flexible. Os partidos agrúpanse en familias: PP, PSdeG, BNG, esquerda alternativa
(AGE 2012, En Marea 2016, Galicia en Común 2020, Sumar e Podemos 2024), DO, VOX e o resto.
Concellos fusionados: Cesuras + Oza → Oza-Cesuras (15902) e Cerdedo + Cotobade → Cerdedo-Cotobade
(36902), sumados nos anos anteriores á fusión.

Hexágonos: unha reixa hexagonal recortada co contorno de Galicia e cada concello levado a unha cela
pola asignación óptima (algoritmo húngaro) que minimiza a distancia ao seu centro real.
"""
import csv
import io
import json
import math
import re
from pathlib import Path
from urllib.request import Request, urlopen
import time

import numpy as np
from scipy.optimize import linear_sum_assignment
from shapely.geometry import Point, shape

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
CONCELLOS = Path("/Users/perezgulin/Proxectos/galicia-agora/data-out/concellos-parroquias/data.geojson")
B = "https://abertos.xunta.gal/catalogo/administracion-publica/-/dataset/"
U = {2001: ["0263/eleccions-parlamento-galicia-resultados-2001/001"], 2005: ["0261/eleccions-parlamento-galicia-resultados-2005/001"],
     2009: ["0260/eleccions-parlamento-galicia-resultados-2009/001"], 2012: ["0048/eleccions-parlamento-galicia-resultados-2012/001"],
     2016: ["0371/eleccions-parlamento-galicia-resultados-2016/001"],
     2020: [f"0426/eleccions-parlamento-galicia-resultados-2020/{n}" for n in ("001", "005", "009", "013")],
     2024: [f"0656/eleccions-parlamento-galicia-resultados-2024/{n}" for n in ("001", "005", "009", "013")]}
FUSION = {"15026": "15902", "15063": "15902", "36011": "36902", "36012": "36902"}
FAMILIAS = [("PP", r"^\s*P\.?P\.?\b|PARTIDO POPULAR"), ("PSdeG", r"PSdeG|PS ?de ?G|PSOE|SOCIALISTA"),
            ("BNG", r"\bB\.?N\.?G\b|BLOQUE NACIONALISTA"),
            ("Esq", r"\bAGE\b|ALTERNATIVA GALEGA DE ESQUERDA|^EN MAREA$|^EN MAREA\b(?!-COMPROMISO)|PODEMOS|GALICIA EN COM|SUMAR"
                    r"|MAREA ATL|COMPOSTELA ABERTA|FERROL EN COM|MAREA DE |EN COM[UÚ]N|^ANOVA"),
            ("DO", r"\bD\.?O\b|DEMOCRACIA OURENSANA"), ("VOX", r"^VOX\b")]
NOMES = {"PP": "PP", "PSdeG": "PSdeG-PSOE", "BNG": "BNG", "Esq": "Esquerda alternativa (AGE, En Marea, GeC, Sumar)",
         "DO": "Democracia Ourensana", "VOX": "VOX", "Outros": "Outros"}


def le(b):
    t = b.decode("latin1")
    if "¢" in t[:400] or "¤" in t[:2000]:
        t = b.decode("cp850")  # o de 2020 vén en codificación de MS-DOS
    return list(csv.reader(io.StringIO(t), delimiter=";"))


def num(s):
    s = (s or "").strip().replace(".", "")
    return int(s) if s.isdigit() else 0


def familia(nome):
    for k, rx in FAMILIAS:
        if re.search(rx, nome.strip(), re.I):
            return k
    return "Outros"


RAW.mkdir(parents=True, exist_ok=True)
elec, partidos = {}, {}
LISTA = []
for ano, us in U.items():
    res = {}
    for i, u in enumerate(us):
        f = RAW / f"parlamento_{ano}_{i}.csv"
        if not f.exists():
            f.write_bytes(urlopen(B + u + "/descarga-directa-ficheiro.csv", timeout=60).read())
        filas = le(f.read_bytes())
        h = [x.strip() for x in filas[0]]
        hu = [x.upper() for x in h]
        cp = next(j for j, x in enumerate(hu) if "PROV" in x or "CIR" in x)
        cc = next(j for j, x in enumerate(hu) if ("MUNICIPIO" in x or "CON." in x or x == "CÓD CON") and "CÓD" in x.replace("C¢D", "CÓD"))
        iv = max(j for j, x in enumerate(hu) if "VÁLIDOS" in x or "VALIDOS" in x or "V LIDOS" in x or "CANDIDATURAS" in x)
        ivv = next(j for j, x in enumerate(hu) if "VÁLIDOS" in x or "VALIDOS" in x or "V LIDOS" in x)
        pcols = [(j, h[j]) for j in range(iv + 1, len(h)) if h[j]]
        for r in filas[1:]:
            if len(r) <= iv or not r[cp].strip().isdigit() or not r[cc].strip().isdigit():
                continue
            cod = f"{int(r[cp]):02d}{int(r[cc]):03d}"
            if int(r[cc]) == 999 or cod in res and ano != 2001:
                continue  # 999: CERA (residentes no estranxeiro); duplicados en 2016
            cod = FUSION.get(cod, cod)
            e = res.setdefault(cod, {"v": 0, "p": {}})
            e["v"] += num(r[ivv])
            for j, n in pcols:
                if j < len(r) and num(r[j]):
                    k = familia(n)
                    e["p"][k] = e["p"].get(k, 0) + num(r[j])
                    partidos.setdefault(ano, {}).setdefault(n, k)
    elec[f"parl-{ano}"] = res
    LISTA.append({"id": f"parl-{ano}", "t": "parl", "a": str(ano), "e": f"Parlamento {ano}"})
    tot = {}
    for e in res.values():
        for k, v in e["p"].items():
            tot[k] = tot.get(k, 0) + v
    vv = sum(e["v"] for e in res.values())
    print(ano, len(res), "concellos ·", {k: f"{v / vv:.1%}" for k, v in sorted(tot.items(), key=lambda kv: -kv[1])})

# Municipais e xerais, do Ministerio do Interior
MIR = {"mun": ["200305", "200705", "201105", "201505", "201905", "202305"],
       "xer": ["200003", "200403", "200803", "201111", "201512", "201606", "201904", "201911", "202307"]}
TIPO = {"mun": "04", "xer": "02"}
MES = {"03": "marzo", "04": "abril", "05": "maio", "06": "xuño", "07": "xullo", "11": "novembro", "12": "decembro"}
import zipfile
for t, datas in MIR.items():
    for am in datas:
        f = RAW / f"{TIPO[t]}{am}_MUNI.zip"
        for intento in range(4):
            if f.exists():
                break
            try:
                f.write_bytes(urlopen(Request(f"https://infoelectoral.interior.gob.es/estaticos/docxl/apliextr/{TIPO[t]}{am}_MUNI.zip",
                                              headers={"User-Agent": "Mozilla/5.0"}), timeout=180).read())
            except Exception as ex:
                print("reintento", t, am, ex)
                time.sleep(10 * (intento + 1))
        z = zipfile.ZipFile(f)
        le_dat = lambda pre: next(z.read(n).decode("latin1").splitlines() for n in z.namelist() if n.startswith(pre))
        cand = {l[8:14]: (l[14:64].strip() + " " + l[64:214].strip()) for l in le_dat("03")}
        res = {}
        for l in le_dat("05"):
            if l[11:13] in ("15", "27", "32", "36") and l[16:18] == "99":
                cod = FUSION.get(l[11:16], l[11:16])
                e = res.setdefault(cod, {"v": 0, "p": {}})
                e["v"] += int(l[189:197]) + int(l[205:213])  # válidos = en branco + a candidaturas
        for l in le_dat("06"):
            if l[9:11] in ("15", "27", "32", "36") and l[14:16] == "99":
                cod = FUSION.get(l[9:14], l[9:14])
                v = int(l[22:30])
                if v and cod in res:
                    k = familia(cand.get(l[16:22], ""))
                    res[cod]["p"][k] = res[cod]["p"].get(k, 0) + v
        idn = f"{t}-{am[:4]}" + ("-" + am[4:] if am[:4] == "2019" and t == "xer" else "")
        elec[idn] = res
        etq = ("Municipais " if t == "mun" else "Xerais ") + am[:4] + (f" ({MES[am[4:]]})" if t == "xer" and am[:4] == "2019" else "")
        LISTA.append({"id": idn, "t": t, "a": am[:4], "e": etq})
        tot, vv = {}, sum(e["v"] for e in res.values())
        for e in res.values():
            for k, v in e["p"].items():
                tot[k] = tot.get(k, 0) + v
        print(etq, len(res), "concellos ·", {k: f"{v / vv:.1%}" for k, v in sorted(tot.items(), key=lambda kv: -kv[1])})

# Reixa hexagonal
gj = json.loads(CONCELLOS.read_text(encoding="utf-8"))
conc = [(ft["properties"]["codigo_ine"], ft["properties"]["nome"], ft["properties"]["provincia"], shape(ft["geometry"]))
        for ft in gj["features"] if ft["properties"]["nivel"] == "concello"]
LAT0 = 42.8
pxy = lambda x, y: (x * math.cos(math.radians(LAT0)), y)
cen = np.array([pxy(*g.representative_point().coords[0]) for _, _, _, g in conc])
galicia = shape({"type": "MultiPolygon", "coordinates": [p for _, _, _, g in conc for p in
                 ([g.__geo_interface__["coordinates"]] if g.geom_type == "Polygon" else g.__geo_interface__["coordinates"])]}).buffer(0.02)
gp = shape(galicia.__geo_interface__)


def reixa(s):
    pts = []
    minx, miny, maxx, maxy = galicia.bounds
    dy = s * math.sqrt(3) / 2
    j = 0
    y = miny
    while y <= maxy:
        x = minx + (s / 2 if j % 2 else 0)
        while x <= maxx * 1:
            if gp.contains(Point(x / math.cos(math.radians(LAT0)) if False else x, y)):
                pts.append((x, y, j))
            x += s
        y += dy
        j += 1
    return pts


# O tamaño de cela que dá o menor número de celas que aínda chega para todos os concellos
# (cantas menos sobren, menos buratos quedan no mapa)
mellor = None
for s in np.linspace(0.06, 0.14, 400):
    n = len(reixa(s))
    if n >= len(conc) and (mellor is None or n < mellor[1]):
        mellor = (s, n)
lo = mellor[0]
celas = reixa(lo)
P = np.array([pxy(x, y) for x, y, _ in celas])
coste = ((cen[:, None, :] - P[None, :, :]) ** 2).sum(-1)
fil, col = linear_sum_assignment(coste)
dmed = np.sqrt(coste[fil, col]).mean() / (lo * math.cos(math.radians(LAT0)))
print(f"celas {len(celas)} para {len(conc)} concellos · desprazamento medio {dmed:.2f} celas")
# Coordenadas de debuxo: fila e columna enteiras da reixa (cara arriba = norte)
ys = sorted({y for _, y, _ in celas})
hex_ = {}
for i, j in zip(fil, col):
    x, y, fila = celas[j]
    c = conc[i]
    hex_[c[0]] = {"n": c[1], "pr": c[2], "q": round((x - galicia.bounds[0]) / lo, 2), "r": len(ys) - 1 - ys.index(y)}
falta = {a: [c for c in hex_ if c not in elec[a]] for a in elec}
print("concellos sen resultado:", {a: v for a, v in falta.items() if v})
out = {"hex": hex_, "lista": LISTA, "elec": {a: {c: {"v": e["v"], "p": e["p"]} for c, e in r.items() if c in hex_} for a, r in elec.items()},
       "fam": NOMES}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json")

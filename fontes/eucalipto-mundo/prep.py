#!/usr/bin/env python3
"""Monte e eucalipto: Galicia fronte aos países do mundo, e os 313 concellos → data/datos.json

Fontes (descárganse en data/raw/ se faltan):
  · FAO, Global Forest Resources Assessment 2025 (FRA 2025), descarga completa (táboa 1a: superficie
    forestal e superficie terrestre, miles de ha, ano 2025):
      https://fra-data.fao.org/api/file/bulk-download?assessmentName=fra&cycleName=2025&countryIso=WO
  · Galicia e concellos: Inventario Forestal Continuo de Galicia (INVEGA), xa descargado e agregado en
    ../monte-concellos/data/datos.json (lese, non se modifica; ver ../monte-concellos/prep.py).
    Eucalipto = cobertura arborada de eucalipto + as súas cortas, rexeneración e áreas queimadas,
    como fai o propio Inventario; arborado = eucalipto + coníferas + frondosas; superficie = «sutil».
  · Portugal continental: ICNF, 6.º Inventário Florestal Nacional (IFN6, 2015), relatório final,
    táboas 101.PT (usos do solo) e 106.PTC (áreas por especie):
      https://www.icnf.pt/api/file/doc/c8cc40b3b7ec8541
  · Brasil: IBGE, Produção da Extração Vegetal e da Silvicultura (PEVS), táboa SIDRA 5930, área
    existente a 31/12 dos efectivos da silvicultura por especie:
      https://apisidra.ibge.gov.br/values/t/5930/n1/all/v/6549/p/all/c734/39326,0
  · Nomes dos países en galego: Unicode CLDR 46.

Non hai unha cifra mundial de superficie de eucalipto por país nas estatísticas oficiais (a FRA só
dá o volume das especies principais), así que a comparación do eucalipto limítase aos países con
inventario propio verificable. Australia (ABARES) non se puido descargar e queda fóra.
Necesita pypdf e shapely (para simplificar os contornos dos concellos).
"""
import csv
import io
import json
import re
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

import pypdf
from shapely.geometry import Polygon

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
MONTE = HERE.parent / "monte-concellos" / "data" / "datos.json"
UA = {"User-Agent": "Mozilla/5.0"}
FRA = "https://fra-data.fao.org/api/file/bulk-download?assessmentName=fra&cycleName=2025&countryIso=WO"
ICNF = "https://www.icnf.pt/api/file/doc/c8cc40b3b7ec8541"
SIDRA = "https://apisidra.ibge.gov.br/values/t/5930/n1/all/v/6549/p/all/c734/39326,0"
CLDR = "https://cdn.jsdelivr.net/npm/cldr-localenames-full@46.0.0/main/gl/territories.json"
REX = {"Africa": "África", "Asia": "Asia", "Europe": "Europa", "North and Central America": "América do Norte e Central",
       "Oceania": "Oceanía", "South America": "América do Sur"}


def baixa(url, f):
    if not f.exists():
        f.write_bytes(urlopen(Request(url, headers=UA), timeout=300).read())
    return f


RAW.mkdir(parents=True, exist_ok=True)
gl = json.loads(baixa(CLDR, RAW / "cldr_gl_territories.json").read_text(encoding="utf-8"))
gl = gl["main"]["gl"]["localeDisplayNames"]["territories"]

# FRA 2025
z = zipfile.ZipFile(baixa(FRA, RAW / "fra2025.zip"))
nome = next(n for n in z.namelist() if re.match(r"FRA_Years_.*\.csv$", n))
paises = []
for r in csv.DictReader(io.TextIOWrapper(z.open(nome), encoding="utf-8-sig")):
    if r["year"] != "2025" or not r["1a_forestArea"] or not r["1a_landArea"] or float(r["1a_landArea"]) < 100:
        continue  # fóra os territorios de menos de 1.000 km²
    f, t = float(r["1a_forestArea"]), float(r["1a_landArea"])
    paises.append({"id": r["iso3"], "n": gl.get(r["iso2"]) or r["name"], "r": REX.get(r["regions"], r["regions"]),
                   "f": round(f), "t": round(t)})  # miles de ha

# Galicia e concellos (INVEGA, vía monte-concellos)
M = json.loads(MONTE.read_text(encoding="utf-8"))
U = str(M["anos"][-1])
T = M["total"][U]
gal = {"e": T["e"], "c": T["c"], "f": T["f"], "sup": T["sutil"], "ano": int(U)}
conc = []
for c in M["concellos"]:
    h = c["ha"][U]
    pol = []
    for anel in c["pol"]:
        p = Polygon(anel).simplify(2.5, preserve_topology=True)
        if p.area > 4:
            pol.append([[int(x), int(y)] for x, y in p.exterior.coords][:-1])
    conc.append({"id": c["id"], "n": c["n"], "pr": c["pr"], "e": h["e"], "c": h["c"], "f": h["f"], "s": c["sup"], "p": pol})

# Portugal continental, IFN6
txt = "\n".join(p.extract_text() for p in pypdf.PdfReader(baixa(ICNF, RAW / "icnf_ifn6_relatorio.pdf")).pages[15:30])
cont = re.search(r"101\.PT ÁREAS DOS USOS DO SOLO.*?Portugal continental ([\d ]+,\d) ([\d ]+,\d) ([\d ]+,\d) ([\d ]+,\d)", txt, re.S)
eu = re.search(r"106\.PTC ÁREAS TOTAIS POR ESPÉCIE.*?Portugal continental ([\d ]+,\d) ([\d ]+,\d) ([\d ]+,\d) ([\d ]+,\d).*?"
               r"Eucaliptos ([\d ]+,\d) ([\d ]+,\d) ([\d ]+,\d) ([\d ]+,\d)", txt, re.S)
n = lambda s: round(float(s.replace(" ", "").replace(",", ".")) * 1000)
pt = {"e": n(eu.group(8)), "bosque": n(eu.group(4)), "sup": n(cont.group(4)), "ano": 2015}

# Brasil, IBGE PEVS
sid = json.loads(baixa(SIDRA, RAW / "ibge_sidra_5930.json").read_text(encoding="utf-8"))[1:]
ub = max(int(r["D3C"]) for r in sid if r["V"] not in ("...", "-", ""))
bre = next(int(r["V"]) for r in sid if int(r["D3C"]) == ub and r["D4N"] == "Eucalipto")
bra = next(p for p in paises if p["id"] == "BRA")
br = {"e": bre, "bosque": bra["f"] * 1000, "sup": bra["t"] * 1000, "ano": ub, "ano_bosque": 2025}

d = {"paises": paises, "galicia": gal, "pt": pt, "br": br, "concellos": conc}
(HERE / "data" / "datos.json").write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
arb = gal["e"] + gal["c"] + gal["f"]
print("Galicia arborado", arb, f"{arb / gal['sup']:.1%}", "eucalipto", gal["e"], f"{gal['e'] / gal['sup']:.1%}", f"{gal['e'] / arb:.1%} do arborado")
print("Portugal", pt, f"{pt['e'] / pt['sup']:.1%}", f"{pt['e'] / pt['bosque']:.1%}")
print("Brasil", br, f"{br['e'] / br['sup']:.2%}", f"{br['e'] / br['bosque']:.2%}")
print("países", len(paises), "concellos", len(conc))
print("ok: data/datos.json", (HERE / "data" / "datos.json").stat().st_size // 1024, "KB")

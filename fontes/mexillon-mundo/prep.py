#!/usr/bin/env python3
"""Mexillón de acuicultura: Galicia fronte aos países do mundo, 2003-2023 → data/datos.json

Fontes (descárganse en data/raw/ se faltan):
  · FAO, FishStat «Global aquaculture production» (Aquaculture_Quantity.csv), versión 2025.1.0,
    cantidade en toneladas de peso vivo por país, especie e ano (1950-2023):
      https://www.fao.org/fishery/static/Data/Aquaculture_2025.1.0.zip
    Mexillóns = todas as especies do grupo ISSCAAP «Mussels» (Mytilus galloprovincialis, M. edulis,
    M. chilensis, Perna canaliculus, Perna viridis, Mytilus NEI…).
  · Pesca de Galicia (Consellería do Mar), «Produción de acuicultura 2003-2025» (CSV, kg e €):
      https://www.pescadegalicia.gal/descargas/acuicultura/acuicultura.csv
    Mexillón (código MSM, bateas) + «Mexillón (parques de cultivo)» (MSM.).
  · Nomes dos países en galego: Unicode CLDR 46 (cldr-localenames-full, gl/territories.json):
      https://cdn.jsdelivr.net/npm/cldr-localenames-full@46.0.0/main/gl/territories.json

Galicia ponse como se fose un país máis. España (FAO) gárdase á parte: inclúe Galicia, e as dúas
estatísticas non coinciden (a FAO recibe a cifra estatal do MAPA; a Xunta conta as vendas
declaradas de mexillón das bateas), así que non se resta.
"""
import csv
import io
import json
import zipfile
from collections import defaultdict
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
UA = {"User-Agent": "Mozilla/5.0"}
FAO = "https://www.fao.org/fishery/static/Data/Aquaculture_2025.1.0.zip"
XUNTA = "https://www.pescadegalicia.gal/descargas/acuicultura/acuicultura.csv"
CLDR = "https://cdn.jsdelivr.net/npm/cldr-localenames-full@46.0.0/main/gl/territories.json"
Y0 = 2003


def baixa(url, f):
    if not f.exists():
        f.write_bytes(urlopen(Request(url, headers=UA), timeout=300).read())
    return f


RAW.mkdir(parents=True, exist_ok=True)
z = zipfile.ZipFile(baixa(FAO, RAW / "Aquaculture_2025.1.0.zip"))
le = lambda n: csv.DictReader(io.TextIOWrapper(z.open(n), encoding="utf-8-sig"))
mus = {r["3A_Code"] for r in le("CL_FI_SPECIES_GROUPS.csv") if r["ISSCAAP_Group_En"] == "Mussels"}
paises = {r["UN_Code"]: r for r in le("CL_FI_COUNTRY_GROUPS.csv")}
gl = json.loads(baixa(CLDR, RAW / "cldr_gl_territories.json").read_text(encoding="utf-8"))
gl = gl["main"]["gl"]["localeDisplayNames"]["territories"]
NOMES = {"KR": "Corea do Sur", "US": "Estados Unidos", "GB": "Reino Unido", "NL": "Países Baixos", "RU": "Rusia",
         "TR": "Turquía", "CN": "China"}

t = defaultdict(lambda: defaultdict(float))  # país → ano → t
sp = defaultdict(lambda: defaultdict(float))  # país → especie (último ano)
ymax = 0
for r in le("Aquaculture_Quantity.csv"):
    if r["SPECIES.ALPHA_3_CODE"] in mus and r["MEASURE"] == "Q_tlw":
        y = int(r["PERIOD"])
        ymax = max(ymax, y)
        if y >= Y0:
            t[r["COUNTRY.UN_CODE"]][y] += float(r["VALUE"])
for r in le("Aquaculture_Quantity.csv"):
    if r["SPECIES.ALPHA_3_CODE"] in mus and r["MEASURE"] == "Q_tlw" and int(r["PERIOD"]) == ymax:
        sp[r["COUNTRY.UN_CODE"]][r["SPECIES.ALPHA_3_CODE"]] += float(r["VALUE"])
ANOS = list(range(Y0, ymax + 1))

# Galicia (kg → t)
gal = defaultdict(float)
NUM = lambda s: float(s.replace(".", "").replace(",", "."))
for r in csv.reader(baixa(XUNTA, RAW / "acuicultura_galicia.csv").open(encoding="utf-8-sig"), delimiter=";"):
    if len(r) >= 5 and r[2].strip() in ("MSM", "MSM."):
        gal[int(r[0])] += NUM(r[4]) / 1000

out = []
for un, s in t.items():
    p = paises[un]
    iso = p["ISO2_Code"]
    serie = [round(s.get(y, 0)) for y in ANOS]
    if max(serie) < 500:  # fóra os produtores moi pequenos
        continue
    out.append({"id": iso, "n": NOMES.get(iso) or gl.get(iso) or p["Name_Es"], "c": p["Continent_Group_En"], "s": serie,
                "sp": {k: round(v) for k, v in sorted(sp[un].items(), key=lambda x: -x[1]) if v >= 1}})
esp = next(p for p in out if p["id"] == "ES")
out.remove(esp)
gserie = [round(gal[y]) for y in ANOS]
out.append({"id": "GZ", "n": "Galicia", "c": "Europe", "s": gserie, "sp": {"MSM": gserie[-1]}})
out.sort(key=lambda p: -p["s"][-1])
mundo = [round(sum(s.get(y, 0) for s in t.values())) for y in ANOS]
SPN = {"MSX": "Mexillón (sen especificar)", "MYC": "Mexillón chileno (M. chilensis)", "MUS": "Mexillón común (M. edulis)",
       "MSV": "Mexillón verde (Perna viridis)", "MUZ": "Mexillón de Nova Zelandia (P. canaliculus)",
       "MSM": "Mexillón mediterráneo (M. galloprovincialis)", "MUK": "Mexillón coreano (M. coruscus)",
       "MSL": "Mexillón de rocha suramericano (Perna perna)", "MYA": "Mexillón australiano (M. planulatus)",
       "MSC": "Cholga (Aulacomya atra)", "CHC": "Choro (Choromytilus chorus)"}
d = {"anos": ANOS, "paises": out, "mundo": mundo, "espana": esp["s"], "galicia_ultimo": round(gal[max(gal)]),
     "galicia_ultimo_ano": max(gal), "sp": SPN}
(HERE / "data" / "datos.json").write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
for i, p in enumerate(out[:8]):
    print(i + 1, p["n"], p["s"][-1])
print("mundo", mundo[-1], "España FAO", esp["s"][-1], "Galicia", gserie[-1], "países", len(out))
print("ok: data/datos.json", (HERE / "data" / "datos.json").stat().st_size // 1024, "KB")

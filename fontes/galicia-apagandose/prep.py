#!/usr/bin/env python3
"""Poboación de cada entidade singular (aldea, lugar) de Galicia, 1999-2025 → data/datos.json

Fontes:
  data/ige/AAAA.csv  Nomenclátor do IGE, unha descarga por ano (non se suben ao repositorio):
      https://www.ige.gal/igebdt/igeapi/csv/nomenc/AAAA/0/0/0/1/0/0
  ENTIDADES          puntos das entidades de poboación do IET (Xunta), capa PBA
  CONCELLOS          concellos e parroquias (nomes e centroides de reserva)

As entidades identifícanse por provincia + concello + entidade colectiva + entidade singular.
Os dous concellos fusionados (Oza-Cesuras 2013, Cerdedo-Cotobade 2016) cambiaron de código:
nos anos anteriores búscase cada entidade polo nome dentro dos concellos de orixe.
Necesita shapely.
"""
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from urllib.request import Request, urlopen

from shapely.geometry import shape

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
GA = Path("/Users/perezgulin/Proxectos/galicia-agora/data-out")
ENTIDADES = GA / "entidades-poboacion/data.geojson"
CONCELLOS = GA / "concellos-parroquias/data.geojson"
ANOS = list(range(1999, 2026))
FUSIONS = {"15902": ["15026", "15063"], "36902": ["36011", "36012"]}  # novo: antigos
URL = "https://www.ige.gal/igebdt/igeapi/csv/nomenc/{}/0/0/0/1/0/0"


def norm(s):
    s = unicodedata.normalize("NFD", s.upper())
    s = "".join(c for c in s if not unicodedata.combining(c))
    m = re.match(r"^(.*), (O|A|OS|AS)$", s)
    if m:
        s = f"{m.group(2)} {m.group(1)}"
    return re.sub(r"[^A-Z0-9]+", " ", s).strip()


def bonito(s):
    """«ADRO, O» → «O Adro»"""
    m = re.match(r"^(.*), (O|A|OS|AS)$", s)
    if m:
        s = f"{m.group(2)} {m.group(1)}"
    pal = s.lower().split(" ")
    return " ".join(p if (p in {"de", "do", "da", "dos", "das", "e"} and i) else p[:1].upper() + p[1:]
                    for i, p in enumerate(pal))


# 1. Series do IGE
serie = defaultdict(dict)   # clave → {ano: poboación}
nome = {}
for y in ANOS:
    f = DATA / "ige" / f"{y}.csv"
    if not f.exists() or f.stat().st_size < 100_000:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(urlopen(Request(URL.format(y), headers={"User-Agent": "Mozilla/5.0"}), timeout=200).read())
    for x in csv.DictReader(f.open(encoding="latin1")):
        k = x["codprov"] + x["codmun"] + x["ec"] + x["es"]
        serie[k][y] = int(x["pobtotal"])
        nome[k] = x["nome"]

modo_f = Counter()
# fusións: copia os anos antigos ás claves novas, casando polo nome
for novo, vellos in FUSIONS.items():
    vk = defaultdict(list)
    for k in serie:
        if k[:5] in vellos:
            vk[norm(nome[k])].append(k)
    for k in [k for k in serie if k[:5] == novo]:
        c = vk.get(norm(nome[k]), [])
        if len(c) == 1:
            for y, v in serie[c[0]].items():
                serie[k].setdefault(y, v)
            modo_f[novo] += 1
    for ks in vk.values():
        for k in ks:
            del serie[k]

print("fusións casadas polo nome:", dict(modo_f))
ult = ANOS[-1]
ents = {k: s for k, s in serie.items() if ult in s}
print("entidades en", ult, len(ents))

# 2. Coordenadas
fs = json.loads(ENTIDADES.read_text(encoding="utf-8"))["features"]
porcod, pornome = defaultdict(list), defaultdict(list)
for f in fs:
    p = f["properties"]
    if not f["geometry"]:
        continue
    if p["codigo"]:
        porcod[p["codigo"][:9]].append(f)
    if p["codigo_ine"]:
        pornome[(p["codigo_ine"], norm(p["nome"]))].append(f)
PRI = {"PU": 0, "EN": 1, "NU": 2, "END": 3, "EH": 4, "ED": 5, "LU": 6}
cg = json.loads(CONCELLOS.read_text(encoding="utf-8"))["features"]
nconc = {f["properties"]["codigo_ine"]: f["properties"]["nome"] for f in cg if f["properties"]["nivel"] == "concello"}
cparr = {f["properties"]["codigo_parroquia"]: shape(f["geometry"]).representative_point()
         for f in cg if f["properties"]["nivel"] == "parroquia"}

modo = Counter()
saida = []
concs = sorted(nconc, key=lambda c: nconc[c])
ci = {c: i for i, c in enumerate(concs)}
for k, s in ents.items():
    cand = porcod.get(k) or pornome.get((k[:5], norm(nome[k])))
    if cand:
        f = min(cand, key=lambda f: (PRI.get(f["properties"]["tipo"], 9), -(f["properties"]["poboacion"] or 0)))
        lon, lat = f["geometry"]["coordinates"]
        nm = f["properties"]["nome"] if norm(f["properties"]["nome"]) == norm(nome[k]) else bonito(nome[k])
        modo["punto" if porcod.get(k) else "nome"] += 1
    elif k[:7] in cparr:
        pt = cparr[k[:7]]
        lon, lat, nm = pt.x, pt.y, bonito(nome[k])
        modo["parroquia"] += 1
    else:
        modo["sen"] += 1
        continue
    if k[:5] not in ci:
        modo["sen concello"] += 1
        continue
    saida.append({"k": k, "x": round(lon, 4), "y": round(lat, 4), "n": nm, "c": ci[k[:5]],
                  "p": [s.get(y, -1) for y in ANOS]})
print("coordenadas:", dict(modo))
(DATA / "coord.json").write_text(json.dumps(dict(modo)))

# 3. Resumo
for y in ANOS:
    i = ANOS.index(y)
    z = sum(1 for e in saida if e["p"][i] == 0)
    print(y, "baleiras:", z, " 1-4 hab:", sum(1 for e in saida if 1 <= e["p"][i] <= 4))
i0 = 0
apag = [e for e in saida if e["p"][i0] > 0 and e["p"][-1] == 0]
print("tiñan xente en", ANOS[0], "e en", ult, "non:", len(apag))

# Formato compacto para a web: x, y en milésimas de grao dende (-9,4 ; 41,8); clase de poboación
# por ano nun díxito (- sen dato, 0 baleira, 1: 1-4, 2: 5-9, 3: 10-24, 4: 25-49, 5: 50-99,
# 6: 100-249, 7: 250-999, 8: 1.000-9.999, 9: 10.000+); poboación no primeiro e no último ano.
LIM = [0, 4, 9, 24, 49, 99, 249, 999, 9999]
cl = lambda v: "-" if v < 0 else str(next((i for i, t in enumerate(LIM) if v <= t), 9))
gal = shape(json.loads((DATA / "galicia.geojson").read_text())["geometry"]).simplify(0.004)
contorno = [[[round((x + 9.4) * 1000), round((y - 41.8) * 1000)] for x, y in pol.exterior.coords]
            for pol in getattr(gal, "geoms", [gal]) if pol.area > 0.0005]
out = {"anos": ANOS, "concellos": [nconc[c] for c in concs], "contorno": contorno,
       "e": [[round((e["x"] + 9.4) * 1000), round((e["y"] - 41.8) * 1000), e["n"], e["c"],
              "".join(cl(v) for v in e["p"]), e["p"][0], e["p"][-1]] for e in saida]}
(DATA / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json", (DATA / "datos.json").stat().st_size // 1024, "KB")

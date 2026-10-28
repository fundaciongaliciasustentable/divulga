#!/usr/bin/env python3
"""Vidro recollido no contedor verde en cada concello galego, 2015-2025 → data/datos.json

Reformulación: non hai datos públicos e completos de residuos municipais por concello en Galicia
(nin en abertos.xunta.gal, nin no SIRGA —«Información sobre a produción e xestión: novo contido en
construción»—, nin nas memorias de Sogama, que só dan totais). O único fluxo con datos oficiais
publicados para os 313 concellos é o vidro, así que a peza vai sobre el.

Fontes (gárdanse en data/raw/ se faltan):
  ecovidrio_<ano>_<prov>.xlsx  Ecovidrio, «Datos de reciclaje por región, provincia y municipio»
        https://www.ecovidrio.es/reciclaje/datos-reciclaje  (descarga Excel:
        https://www.ecovidrio.es/download-excel?anho=<ano>&ccaa=12&provincia=<15|27|32|36>&mancomunidad_isla=0)
        Quilos de envases de vidro recollidos no contedor verde e número de contedores, por concello.
  ecovidrio_<ano>_gal.xlsx     o mesmo para toda Galicia por provincia (inclúe a recollida
        «complementaria» —hostalaría porta a porta— e o vidro recuperado do «residuo urbano»,
        que non se asignan a ningún concello).
  ine_<táboa>.json  INE, Padrón municipal a 1 de xaneiro por provincia (2868, 2880, 2885, 2890)
        https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/<táboa>?nult=12&tip=AM
Xeometría: concellos de galicia-agora (data-out/concellos-parroquias/data.geojson), simplificada.
Fusións: Oza-Cesuras (15902 = 15026 + 15063) e Cerdedo-Cotobade (36902 = 36011 + 36012) súmanse.
Necesita openpyxl e shapely.
"""
import json
import subprocess
import unicodedata
from pathlib import Path

import openpyxl
from shapely.geometry import shape

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
CONCELLOS = Path("/Users/perezgulin/Proxectos/galicia-agora/data-out/concellos-parroquias/data.geojson")
FUSIONS = {"15902": ["15026", "15063"], "36902": ["36011", "36012"]}
VELLO = {v: k for k, vs in FUSIONS.items() for v in vs}
ANOS = list(range(2015, 2026))
PROV = {"15": "A Coruña", "27": "Lugo", "32": "Ourense", "36": "Pontevedra"}
UA = {"User-Agent": "Mozilla/5.0"}
RAW.mkdir(parents=True, exist_ok=True)


def baixa(nome, url):
    f = RAW / nome
    if not f.exists():
        # curl e non urllib: o servidor de Ecovidrio non envía a cadea de certificados completa
        subprocess.run(["curl", "-sf", "-m", "300", "-A", UA["User-Agent"], "-o", str(f), url], check=True)
        print("descargado", nome)
    return f


def filas(f):
    ws = openpyxl.load_workbook(f, read_only=True).active
    return list(ws.iter_rows(values_only=True))


def norm(s):
    """«Baña, A» → «a bana»; sen tiles nin artigos pospostos."""
    s = s.strip()
    if ", " in s:
        a, b = s.rsplit(", ", 1)
        if b.lower() in ("a", "o", "as", "os"):
            s = f"{b} {a}"
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn").replace("-", " ").replace("  ", " ")


# Xeometría
X0, Y1, KX = -9.4, 43.9, 0.7325  # KX = cos(42,9°); unidades: 1/1000 de grao de latitude
pr = lambda lon, lat: [round((lon - X0) * KX * 1000), round((Y1 - lat) * 1000)]
fs = [f for f in json.loads(CONCELLOS.read_text(encoding="utf-8"))["features"] if f["properties"]["nivel"] == "concello"]
conc, por_nome = {}, {}
for f in fs:
    p = f["properties"]
    g = shape(f["geometry"]).buffer(0).simplify(0.003)
    pol = [[pr(x, y) for x, y in q.exterior.coords] for q in getattr(g, "geoms", [g]) if q.area > 2e-6]
    conc[p["codigo_ine"]] = {"id": p["codigo_ine"], "n": p["nome"], "pr": p["provincia"], "pol": pol,
                             "kg": [None] * len(ANOS), "ct": [None] * len(ANOS), "pob": [None] * len(ANOS)}
    por_nome[norm(p["nome"])] = p["codigo_ine"]
# nomes que Ecovidrio escribe doutro xeito
ALIAS = {"oza cesuras": "15902", "cerdedo cotobade": "36902", "oza dos rios": "15026", "cesuras": "15063",
         "cerdedo": "36011", "cotobade": "36012"}

# Padrón
for t in (2868, 2880, 2885, 2890):
    f = baixa(f"ine_{t}.json", f"https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{t}?nult=12&tip=AM")
    for s in json.loads(f.read_text(encoding="utf-8")):
        md = {m["T3_Variable"]: m for m in s["MetaData"]}
        if md.get("Sexo", {}).get("Codigo") != "0" or "Municipios" not in md:
            continue
        c = md["Municipios"]["Codigo"]
        c = VELLO.get(c, c)
        if c not in conc:
            continue
        if md["Municipios"]["Codigo"] == c:  # o nome oficial do INE («Pastoriza, A» → «A Pastoriza»)
            n = md["Municipios"]["Nombre"].split(", ")
            conc[c]["n"] = f"{n[1]} {n[0]}" if len(n) == 2 and n[1] in ("A", "O", "As", "Os") else ", ".join(n)
            por_nome[norm(conc[c]["n"])] = c
        for v in s["Data"]:
            if v["Anyo"] in ANOS and v["Valor"] is not None:
                i = ANOS.index(v["Anyo"])
                conc[c]["pob"][i] = (conc[c]["pob"][i] or 0) + int(v["Valor"])

# Ecovidrio por concello
faltan, gal = set(), {}
for i, a in enumerate(ANOS):
    for pv in PROV:
        f = baixa(f"ecovidrio_{a}_{pv}.xlsx",
                  f"https://www.ecovidrio.es/download-excel?anho={a}&ccaa=12&provincia={pv}&mancomunidad_isla=0")
        for r in filas(f)[1:]:
            if not r or r[1] in (None, "TOTAL") or r[0] is None:
                continue
            k = norm(r[1])
            c = ALIAS.get(k) or por_nome.get(k)
            if c is None:
                faltan.add((pv, r[1]))
                continue
            c = VELLO.get(c, c)
            x = conc[c]
            x["kg"][i] = (x["kg"][i] or 0) + (r[3] or 0)
            x["ct"][i] = (x["ct"][i] or 0) + (r[2] or 0)
    tot = {}
    for r in filas(baixa(f"ecovidrio_{a}_gal.xlsx",
                         f"https://www.ecovidrio.es/download-excel?anho={a}&ccaa=12&provincia=0&mancomunidad_isla=0"))[1:]:
        if r[1]:
            tot[r[1]] = r[3]
    gal[a] = {"contedor": sum(v for k, v in tot.items() if k in ("Coruña, A", "Lugo", "Ourense", "Pontevedra")),
              "complementaria": tot.get("Complementaria", 0), "residuo": tot.get("Residuo urbano", 0)}
if faltan:
    print("AVISO: sen casar", sorted(faltan))

C = sorted(conc.values(), key=lambda c: c["n"])
for c in C:
    for k in ("kg", "ct"):
        c[k] = [round(v) if v is not None else None for v in c[k]]
sen = [c["n"] for c in C if c["kg"][-1] is None]
print("concellos sen dato no último ano:", sen)
pob = [sum(c["pob"][i] or 0 for c in C) for i in range(len(ANOS))]
for i, a in enumerate(ANOS):
    g = gal[a]
    print(a, f"contedor {g['contedor'] / pob[i]:.1f} kg/hab · total {sum(g.values()) / pob[i]:.1f} kg/hab · "
             f"suma concellos {sum(c['kg'][i] or 0 for c in C):,} kg (contedor {g['contedor']:,})")
kh = lambda c: c["kg"][-1] / c["pob"][-1]
for c in sorted(C, key=lambda c: -kh(c))[:6] + sorted(C, key=kh)[:6]:
    print(f"  {c['n']:28} {kh(c):5.1f} kg/hab · {c['pob'][-1] / c['ct'][-1]:.0f} hab/contedor")
out = {"anos": ANOS, "gal": gal, "pob": pob, "conc": C}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json", (HERE / "data" / "datos.json").stat().st_size // 1024, "KB")

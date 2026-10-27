#!/usr/bin/env python3
"""Monte arborado por concello e especie, 2022-2024 → data/datos.json

Entrada: data/raw/<concello>.json (de descargar.py) e os polígonos dos concellos.
Cada grupo suma a cobertura arborada e as transicións que proveñen del, como fai o
Inventario Forestal Continuo de Galicia nas súas cifras: cortas (S4x), rexeneración (S5x),
incendios (S11x) e áreas queimadas (S12x). x = 1 eucalipto, 2 coníferas, 3 frondosas.
A rexeneración sen especie identificada (S05) queda fóra.

Para o mapa, cada concello énchese de árbores (1 árbore = UNIDADE ha) en puntos ao chou
dentro do seu polígono, sempre os mesmos nos tres anos. Necesita shapely.
"""
import json
import random
from datetime import datetime, timezone
from pathlib import Path

from shapely.geometry import Point, shape
from shapely.prepared import prep

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
CONCELLOS = Path("/Users/perezgulin/Proxectos/galicia-agora/data-out/concellos-parroquias/data.geojson")
UNIDADE = 100  # ha por árbore
GRUPOS = {"e": ["s01", "s41", "s51", "s111", "s121"],
          "c": ["s02", "s42", "s52", "s112", "s122"],
          "f": ["s03", "s43", "s53", "s113", "s123"]}

fs = [f for f in json.loads(CONCELLOS.read_text(encoding="utf-8"))["features"] if f["properties"]["nivel"] == "concello"]
fs.sort(key=lambda f: f["properties"]["nome"])
X0, Y1 = -9.4, 43.9
KX = 0.7325  # cos(42,9°)
# coordenadas do mapa: unidades de 1/1000 de grao de latitude, x xa corrixido
pr = lambda lon, lat: (round((lon - X0) * KX * 1000), round((Y1 - lat) * 1000))

anos, conc, total, faltan = None, [], {}, []
rnd = random.Random(1983)
for f in fs:
    p = f["properties"]
    fr = DATA / "raw" / f"{p['codigo_ine']}.json"
    if not fr.exists():
        faltan.append(p["codigo_ine"])
        continue
    raw = json.loads(fr.read_text())
    por_ano = {}
    for r in raw:
        # ADM_FECINI é o 1 de xaneiro á medianoite peninsular (31 de decembro ás 23:00 UTC)
        y = datetime.fromtimestamp(r["ADM_FECINI"] / 1000 + 86400, timezone.utc).year
        por_ano[y] = {g: sum(r[k] or 0 for k in ks) / 1e4 for g, ks in GRUPOS.items()}
        por_ano[y]["sutil"] = (r["sutil"] or 0) / 1e4
        por_ano[y]["s05"] = (r["s05"] or 0) / 1e4
        por_ano[y]["s04"] = (r["s04"] or 0) / 1e4
    anos = anos or sorted(por_ano)
    assert sorted(por_ano) == anos, (p["codigo_ine"], sorted(por_ano))
    for y in anos:
        t = total.setdefault(y, {})
        for k, v in por_ano[y].items():
            t[k] = t.get(k, 0) + v
    g = shape(f["geometry"]).buffer(0)
    gp = prep(g)
    n = max(round(sum(por_ano[y][k] for k in "ecf") / UNIDADE) for y in anos)
    pts, (a, b, c, d) = [], g.bounds
    while len(pts) < n:
        q = Point(rnd.uniform(a, c), rnd.uniform(b, d))
        if gp.contains(q):
            pts.append(pr(q.x, q.y))
    simp = g.simplify(0.003)
    aneis = [[pr(x, y) for x, y in pol.exterior.coords] for pol in getattr(simp, "geoms", [simp])]
    conc.append({"id": p["codigo_ine"], "n": p["nome"], "pr": p["provincia"],
                 "ha": {y: {k: round(por_ano[y][k]) for k in "ecf"} for y in anos},
                 "sup": round(por_ano[anos[-1]]["sutil"]), "pt": pts, "pol": aneis})

if faltan:
    print("AVISO: faltan", len(faltan), "concellos")
for y in anos:
    t = total[y]
    print(y, {k: f"{round(v):,}" for k, v in t.items()})
ult = anos[-1]
arb = lambda c, y: sum(c["ha"][y].values())
maior = sum(1 for c in conc if arb(c, ult) and c["ha"][ult]["e"] > arb(c, ult) / 2)
print("concellos co eucalipto como máis da metade do arborado:", maior)
print("árbores no mapa:", sum(len(c["pt"]) for c in conc))
out = {"anos": anos, "unidade": UNIDADE, "total": {y: {k: round(v) for k, v in total[y].items()} for y in anos},
       "concellos": conc}
(DATA / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json", (DATA / "datos.json").stat().st_size // 1024, "KB")

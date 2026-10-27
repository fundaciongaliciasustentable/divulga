#!/usr/bin/env python3
"""Vendas en lonxa por especie e mes, 2015-2025 → data/datos.json

Fonte: Pesca de Galicia (Consellería do Mar), notas de primeira venda de pesca fresca, un CSV por
ano en data/csv/ (descárgase se falta):
  https://www.pescadegalicia.gal/descargas/pescafresca/pescafresca<ANO>.csv
Campos: data;grupo biolóxico;código FAO;especie;provincia;zona;lonxa;kg;€;€/kg (coma decimal).
"""
import csv
import json
from collections import defaultdict
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
CSV = HERE / "data" / "csv"
URL = "https://www.pescadegalicia.gal/descargas/pescafresca/pescafresca{}.csv"
ANOS = range(2015, 2026)
NUM = lambda s: float(s.replace(".", "").replace(",", ".")) if s.count(",") else float(s or 0)

kg = defaultdict(lambda: defaultdict(float))    # especie → (ano, mes) → kg
# agrúpase polo nome galego: algunhas especies teñen máis dun código FAO (p. ex. xarda pintada)
eur = defaultdict(lambda: defaultdict(float))
info, tot = {}, defaultdict(lambda: [0.0, 0.0])
CSV.mkdir(parents=True, exist_ok=True)
for y in ANOS:
    f = CSV / f"pescafresca{y}.csv"
    if not f.exists() or f.stat().st_size < 100_000:
        f.write_bytes(urlopen(Request(URL.format(y), headers={"User-Agent": "Mozilla/5.0"}), timeout=300).read())
    filas = list(csv.reader(f.open(encoding="utf-8-sig"), delimiter=";"))
    # a orde da data cambia segundo o ficheiro: se o primeiro campo pasa de 12, é día/mes
    dm = max(int(r[0].split("/")[0]) for r in filas if r) > 12
    for r in filas:
        if len(r) < 10:
            continue
        p = r[0].split("/")
        mes = int(p[1] if dm else p[0])
        assert int(p[2]) == y, (f, r)
        fao = r[3].strip()
        k, e = NUM(r[7]), NUM(r[8])
        kg[fao][(y, mes)] += k
        eur[fao][(y, mes)] += e
        info.setdefault(fao, (r[3].strip(), r[1]))
        tot[y][0] += k
        tot[y][1] += e
    print(y, "orde", "día/mes" if dm else "mes/día", f"{tot[y][0] / 1e6:,.1f} mill. kg", f"{tot[y][1] / 1e6:,.1f} mill. €")

# especies co seu total no período
esp = []
for fao, d in kg.items():
    nome, grupo = info[fao]
    ke, ee = sum(d.values()), sum(eur[fao].values())
    esp.append({"n": nome, "g": grupo, "kg": round(ke), "eur": round(ee),
                "m": [[round(kg[fao].get((y, m), 0)), round(eur[fao].get((y, m), 0))] for y in ANOS for m in range(1, 13)]})
esp.sort(key=lambda e: -e["eur"])
print("especies:", len(esp))
for e in esp[:25]:
    print(f"  {e['n']:28} {e['g']:14} {e['eur'] / 1e6:7.1f} M€ {e['kg'] / 1e6:7.1f} Mkg  {e['eur'] / max(e['kg'], 1):6.2f} €/kg")
# só as especies que suman o 1 ‰ do valor, para que o ficheiro sexa lixeiro
total = sum(e["eur"] for e in esp)
out = {"anos": list(ANOS), "total": {y: [round(v[0]), round(v[1])] for y, v in tot.items()},
       "esp": [e for e in esp if e["eur"] >= total * 0.001]}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json", len(out["esp"]), "especies", (HERE / "data" / "datos.json").stat().st_size // 1024, "KB")

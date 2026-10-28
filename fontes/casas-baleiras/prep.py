#!/usr/bin/env python3
"""Vivendas baleiras e de uso esporádico de cada concello galego → data/datos.json

Fontes: INE, Censos de Poboación e Vivendas 2021 (a 1 de xaneiro de 2021):
  · táboa 59525, vivendas principais (con alguén empadroado) e non principais, en todos os
    concellos: https://www.ine.es/jaxi/Tabla.htm?tpx=59525 — é a medida principal da peza.
  · táboa 59531, «Vivendas por intensidade de uso a partir do consumo eléctrico»:
    https://www.ine.es/jaxi/Tabla.htm?tpx=59531
  CSV: https://www.ine.es/jaxi/files/tpx/csv_bdsc/59531.csv (gárdase en data/raw/)
O INE clasifica cada vivenda polo seu consumo de luz ao longo de 2020: baleira (case nada),
de uso esporádico (entre 251 e 750 kWh ao ano) e o resto. Só publica os concellos con datos
suficientes, e nalgúns concellos o dato eléctrico non cadra co padrón (Cuntis: 77 % «baleiras» pola
luz e só 29 % sen empadroados), así que vai só como detalle e márcase cando supera ás non principais.
Polígonos dos concellos: os da peza monte-concellos (xa proxectados para SVG).
"""
import csv
import json
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
f = RAW / "ine_59531.csv"
if not f.exists():
    RAW.mkdir(parents=True, exist_ok=True)
    f.write_bytes(urlopen(Request("https://www.ine.es/jaxi/files/tpx/csv_bdsc/59531.csv", headers={"User-Agent": "Mozilla/5.0"}),
                          timeout=300).read())
num = lambda s: int(s.replace(".", "")) if s and s not in ("..", "-") else None
dat, prov, gal = {}, {}, {}
for r in csv.reader(f.open(encoding="utf-8-sig"), delimiter=";"):
    if len(r) < 6 or r[1] != "12 Galicia":
        continue
    clave = {"Viviendas totales": "t", "Viviendas vacías": "b", "Viviendas de uso esporádico": "e"}.get(r[4])
    if not clave:
        continue
    if r[3]:
        dat.setdefault(r[3][:5], {"n": r[3][6:]})[clave] = num(r[5])
    elif r[2]:
        prov.setdefault(r[2][3:], {})[clave] = num(r[5])
    else:
        gal[clave] = num(r[5])

f2 = RAW / "ine_59525.csv"
if not f2.exists():
    f2.write_bytes(urlopen(Request("https://www.ine.es/jaxi/files/tpx/csv_bdsc/59525.csv", headers={"User-Agent": "Mozilla/5.0"}),
                           timeout=300).read())
pad = {}
for r in csv.reader(f2.open(encoding="utf-8-sig"), delimiter=";"):
    if len(r) > 3 and r[1][:2] in ("15", "27", "32", "36") and len(r[1]) > 6:
        pad.setdefault(r[1][:5], {})[{"Total": "t", "Vivienda principal": "p", "Vivienda no principal": "np"}[r[2]]] = num(r[3])

mc = json.loads((HERE.parent / "monte-concellos" / "data" / "datos.json").read_text(encoding="utf-8"))
conc = []
for c in mc["concellos"]:
    x = dat.get(c["id"])
    p = pad[c["id"]]
    conc.append({"id": c["id"], "n": c["n"], "pr": c["pr"], "pol": c["pol"], "t": p["t"], "np": p["np"],
                 **({"b": x["b"], "e": x["e"], "tl": x["t"]} if x and x.get("t") else {})})
xs = [p[0] for c in conc for r in c["pol"] for p in r]
ys = [p[1] for c in conc for r in c["pol"] for p in r]
gal.update(t=sum(c["t"] for c in conc), np=sum(c["np"] for c in conc))
print("Galicia:", gal, f"{gal['np'] / gal['t']:.1%} sen ninguén empadroado")
for c in sorted(conc, key=lambda c: -c["np"] / c["t"])[:8]:
    print(f"  {c['n']:24} {c['np'] / c['t']:.0%} non principais ({c['t']} vivendas)", f"· luz: {c['b'] / c['tl']:.0%} baleiras" if "b" in c else "")
for c in sorted(conc, key=lambda c: c["np"] / c["t"])[:5]:
    print(f"  {c['n']:24} {c['np'] / c['t']:.0%}")
out = {"conc": conc, "gal": gal, "prov": prov, "bbox": [min(xs), min(ys), max(xs), max(ys)]}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json")

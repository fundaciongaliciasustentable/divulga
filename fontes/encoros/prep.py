#!/usr/bin/env python3
"""Reserva semanal de cada encoro das concas Miño-Sil e Galicia-Costa, 1988-hoxe → data/datos.json

Fonte: MITECO, Boletín Hidrolóxico, base de datos histórica de encoros (BD-Embalses.zip, un
ficheiro de Access cun rexistro por encoro e semana):
  https://www.miteco.gob.es/content/dam/miteco/es/agua/temas/evaluacion-de-los-recursos-hidricos/boletin-hidrologico/Historico-de-embalses/BD-Embalses.zip
Gárdase en data/raw/ e lese con access-parser. Collemos os ámbitos «Miño - Sil» e «Galicia Costa»:
na conca do Miño-Sil hai uns poucos encoros río arriba, en León e Zamora, que van incluídos.
Saída: unha lista común de semanas e, para cada encoro, capacidade (hm³), uso hidroeléctrico
e a porcentaxe de enchido de cada semana.
"""
import json
import zipfile
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen

from access_parser import AccessParser

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
URL = ("https://www.miteco.gob.es/content/dam/miteco/es/agua/temas/evaluacion-de-los-recursos-hidricos/"
       "boletin-hidrologico/Historico-de-embalses/BD-Embalses.zip")
AMB = {"Miño - Sil": "Miño-Sil", "Galicia Costa": "Galicia-Costa"}

z = RAW / "BD-Embalses.zip"
if not z.exists():
    RAW.mkdir(parents=True, exist_ok=True)
    z.write_bytes(urlopen(Request(URL, headers={"User-Agent": "Mozilla/5.0"}), timeout=300).read())
mdb = RAW / "BD-Embalses.mdb"
if not mdb.exists():
    with zipfile.ZipFile(z) as zf:
        zf.extract("BD-Embalses.mdb", RAW)

t = AccessParser(str(mdb)).parse_table("T_Datos Embalses 1988-2026")
num = lambda s: float(str(s).replace(",", "."))
reg = {}
for f, a, n, tot, act, el in zip(t["FECHA"], t["AMBITO_NOMBRE"], t["EMBALSE_NOMBRE"], t["AGUA_TOTAL"], t["AGUA_ACTUAL"], t["ELECTRICO_FLAG"]):
    if a not in AMB:
        continue
    d = str(f)[:10]
    e = reg.setdefault(n, {"c": num(tot), "a": AMB[a], "el": str(el).startswith("1"), "s": {}})
    e["c"] = num(tot)  # a capacidade dalgún encoro cambiou: quédase a última
    e["s"][d] = num(act)

semanas = sorted({d for e in reg.values() for d in e["s"]})
NOMES = {"Portas, Las": "As Portas", "Conchas, Las": "As Conchas", "Rozas, Las": "Las Rozas", "Ribeira, A": "A Ribeira",
         "Forcadas, As": "As Forcadas", "Peares, Os": "Os Peares", "Campañana, La": "La Campañana", "San. Estevo": "Santo Estevo",
         "Sta Uxia": "Santa Uxía", "Barrie de la Maza": "Barrié de la Maza", "Villagudín": "Vilagudín"}
enc = []
for n, e in sorted(reg.items(), key=lambda kv: -kv[1]["c"]):
    pc = [round(min(100, e["s"][d] / e["c"] * 100)) if d in e["s"] and e["c"] else None for d in semanas]
    enc.append({"n": NOMES.get(n, n), "c": e["c"], "a": e["a"], "el": e["el"], "p": pc})

# Total das dúas concas e media de cada semana do ano en 1991-2020 (para a raia de «o normal»)
tot = []
for i, d in enumerate(semanas):
    c = sum(e["c"] for e in enc if e["p"][i] is not None)
    v = sum(e["c"] * e["p"][i] / 100 for e in enc if e["p"][i] is not None)
    tot.append(round(v / c * 100, 1) if c else None)
normal = {}
for i, d in enumerate(semanas):
    if 1991 <= int(d[:4]) <= 2020:
        for e in enc:
            if e["p"][i] is not None:
                normal.setdefault((e["n"], date.fromisoformat(d).isocalendar()[1]), []).append(e["p"][i])
for e in enc:
    e["nor"] = [round(sum(normal.get((e["n"], w), [0])) / max(1, len(normal.get((e["n"], w), [])))) for w in range(1, 54)]
ult = len(semanas) - 1
print(f"{len(enc)} encoros · {len(semanas)} semanas, {semanas[0]} a {semanas[-1]} · capacidade {sum(e['c'] for e in enc):.0f} hm³")
print("total hoxe:", tot[-1], "% · mínimo:", min((v, semanas[i]) for i, v in enumerate(tot) if v), "· máximo:", max((v, semanas[i]) for i, v in enumerate(tot) if v))
out = {"sem": semanas, "enc": enc, "tot": tot}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json")

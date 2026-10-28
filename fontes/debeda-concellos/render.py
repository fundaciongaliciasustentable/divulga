#!/usr/bin/env python3
"""Xera v/debeda-concellos/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "debeda-concellos"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
C = d["conc"]
mil = lambda v: f"{v:,.0f}".replace(",", ".")
meur = lambda v: f"{v / 1e6:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
pc = lambda c: c["d"] / c["p"]
cero, cero15 = sum(1 for c in C if c["d"] == 0), sum(1 for c in C if c["d15"] == 0)
tot, tot15 = sum(c["d"] for c in C), sum(c["d15"] for c in C)
pob = sum(c["p"] for c in C)
ord_ = sorted(C, key=pc, reverse=True)
mais1000 = [c for c in ord_ if pc(c) > 1000]
nomes = lambda xs: ", ".join(c["n"] for c in xs[:-1]) + " e " + xs[-1]["n"] if len(xs) > 1 else xs[0]["n"]
dek = (f"A 31 de decembro de {d['ano']}, <b>{cero} dos {len(C)} concellos galegos</b> non tiñan ningún crédito pendente "
       f"({cero15} en {d['ano0']}). Entre todos debían {meur(tot)} millóns de euros, <b>{mil(tot / pob)} € por habitante</b>, "
       f"{round((1 - tot / tot15) * 100)} % menos ca dez anos antes. A débeda concéntrase nuns poucos: só {len(mais1000)} pasan dos "
       f"1.000 € por veciño ({nomes(mais1000)}). Cada cadrado é un concello; busca o teu.")
ogd = f"{cero} dos {len(C)} concellos galegos non teñen débeda financeira. Cada cadrado é un concello no seu tramo de débeda por habitante."
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__ANO__", str(d["ano"])).replace("__ANO0__", str(d["ano0"])).replace("__OGD__", ogd))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: o histograma de unidades
TR = [0, 50, 100, 200, 300, 500, 1000, 1e12]
PAL = ['none', '#f3e3c3', '#ecc98f', '#e0a861', '#cf8442', '#b4612f', '#8e4325', '#5e2a1b']
tramo = lambda c: 0 if c["d"] == 0 else next(i for i in range(1, 8) if pc(c) <= TR[i])
el, per, s = [], 5, 13
for i in range(8):
    col = sorted((c for c in C if tramo(c) == i), key=pc)
    x0 = 22 + i * 72
    for j, c in enumerate(col):
        x, y = x0 + (j % per) * s, 560 - (j // per + 1) * s
        el.append(f'<rect x="{x}" y="{y}" width="{s - 2}" height="{s - 2}" rx="2" '
                  + ('fill="#fbfaf7" stroke="#a7a29a" stroke-width="1.4"/>' if i == 0 else f'fill="{PAL[i]}"/>'))
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT, (OUT / "index.html").stat().st_size // 1000, "KB")
print(dek)

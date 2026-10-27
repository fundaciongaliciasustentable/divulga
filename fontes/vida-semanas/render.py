#!/usr/bin/env python3
"""Xera v/vida-semanas/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "vida-semanas"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
c = lambda v: f"{v:.1f}".replace(".", ",")
mil = lambda v: f"{v:,.0f}".replace(",", ".")
gH, gM = d["t"]["Galicia|H"], d["t"]["Galicia|M"]
sem = lambda e: e * 365.2425 / 7
dek = (f"Unha vida galega cabe en arredor de <b>{mil(sem(gM['ex'][0]))} semanas</b> se es muller e {mil(sem(gH['ex'][0]))} se es home. "
       f"Pon a túa data de nacemento e verás as que levas vividas e as que, en media, che quedan segundo as táboas de "
       f"mortalidade do INE para Galicia e a túa provincia. Das galegas, {round(gM['lx'][90] / 1000)} de cada 100 chegan aos 90; "
       f"dos galegos, {round(gH['lx'][90] / 1000)}.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__ANO__", str(d["ano"])).replace("__MATY__", str(d["mat"][0])).replace("__MAT__", c(d["mat"][1])))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: grella de 90 anos × 52 semanas, cos primeiros 40 vividos
RAMPA = ["#eef4fa", "#d3e3f2", "#adcbe6", "#7fadd6", "#5089c2", "#2c65a6"]
LIM = [.1, .25, .5, .75, .9]
t = d["t"]["Galicia|T"]
el = []
for a in range(90):
    p = t["lx"][a] / t["lx"][40]
    i = sum(p >= l for l in LIM)
    for w in range(52):
        fill = "#1f2328" if a < 40 else RAMPA[i]
        el.append(f'<rect x="{40 + w * 10}" y="{30 + a * 6}" width="8.6" height="5" fill="{fill}"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT)

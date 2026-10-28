#!/usr/bin/env python3
"""Xera v/nados-fora/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "nados-fora"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
mil = lambda v: f"{v:,.0f}".replace(",", ".")
f1 = lambda v: f"{v:.1f}".replace(".", ",")
C, PA = d["conc"], d["paises"]
T, F = sum(o["t"] for o in C), sum(o["f"] for o in C)
gp = sorted(((p, sum(o["p"][i] for o in C)) for i, p in enumerate(PA) if not p.startswith("Resto") and p != "Oceanía"), key=lambda x: -x[1])
r = sorted(C, key=lambda o: -o["f"] / o["t"])
a = r[0]
ia = max(range(len(PA)), key=lambda i: a["p"][i])
n20 = sum(1 for o in C if o["f"] / o["t"] >= .2)
sh = a["p"][ia] / a["f"]
orixe = (f"{'tres de cada catro' if sh >= .72 else 'a maioría' if sh > .5 else 'o grupo maior'} nados en países de América que o INE non detalla un a un"
         if PA[ia] == "Resto de América" else f"{'a maioría' if sh > .5 else 'o grupo maior'} nados en {PA[ia]}")
dek = (f"A 1 de xaneiro de {d['ano']}, <b>{mil(F)} veciños de Galicia</b> ({f1(F / T * 100)}\u00a0%) naceran fóra de España; o primeiro país é "
       f"{gp[0][0]} ({mil(gp[0][1])}), seguido de {gp[1][0]} e {gp[2][0]}. En <b>{a['n']}</b> son o {f1(a['f'] / a['t'] * 100)}\u00a0% da poboación, "
       f"{orixe}; en {n20} concellos pasan do 20\u00a0%.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__ANO__", str(d["ano"])))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: os círculos proporcionais sobre o contorno
COL = ["#dfe6ea", "#a9c0cc", "#6f97ab", "#3f6d86", "#1f4458"]
col = lambda v: COL[sum(v >= c for c in (5, 10, 15, 20))]
xs = [p[0] for o in C for q in o["pol"] for p in q]
ys = [p[1] for o in C for q in o["pol"] for p in q]
x0, y0 = min(xs), min(ys)
k = 540 / max(max(xs) - x0, max(ys) - y0)
ox, oy = (600 - (max(xs) - x0) * k) / 2, (600 - (max(ys) - y0) * k) / 2
FM = max(o["f"] for o in C)
el = [f'<path d="{"".join("M" + "L".join(f"{(p[0] - x0) * k + ox:.0f},{(p[1] - y0) * k + oy:.0f}" for p in q[::3] + [q[-1]]) + "Z" for q in o["pol"])}" fill="#ebe8e0" stroke="#fbfaf7" stroke-width="1"/>' for o in C]
el += [f'<circle cx="{(o["c"][0] - x0) * k + ox:.0f}" cy="{(o["c"][1] - y0) * k + oy:.0f}" r="{max(2, 26 * math.sqrt(o["f"] / FM)):.1f}" fill="{col(o["f"] / o["t"] * 100)}" stroke="#fff" stroke-width=".8"/>'
       for o in sorted(C, key=lambda o: -o["f"])]
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT, (OUT / "index.html").stat().st_size // 1024, "KB ·", (OUT / "thumb.svg").stat().st_size // 1024, "KB thumb")
print(dek)

#!/usr/bin/env python3
"""Xera v/mar-prato/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "mar-prato"
COL = {"Peixes": "#1f5fae", "Bivalvos": "#c98500", "Cefalópodos": "#6250d6", "Crustáceos": "#e0602d", "Equinodermos": "#1baf7a"}

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
A = d["anos"]
NA = len(A)
per = next(e for e in d["esp"] if e["n"] == "Percebe")
kg = [sum(per["m"][i * 12 + m][0] for i in range(NA)) for m in range(12)]
eu = [sum(per["m"][i * 12 + m][1] for i in range(NA)) for m in range(12)]
pr = [e / k for e, k in zip(eu, kg) if k]
ratio = max(pr) / min(pr)
T = d["total"]
kmax = max(T, key=lambda y: T[y][0])
u = str(A[-1])
h1 = "O percebe vale case o <em>dobre</em> no Nadal: o calendario do mar galego"
dek = (f"Cada especie ten a súa tempada nas lonxas: vedas, mareas e festas mandan no que se vende e no seu prezo. "
       f"Este é o ano medio de {A[0]} a {A[-1]}. Ademais, as lonxas venden cada vez menos: "
       f"<b>{T[u][0] / 1e6:.0f} millóns de quilos</b> en {u}, a metade ca en {kmax}.".replace(".", ",", 0))
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
for k, v in {"DATA": json.dumps(d, ensure_ascii=False, separators=(",", ":")), "H1": h1, "DEK": dek,
             "TITULO": "O percebe vale case o dobre no Nadal: o calendario do mar galego",
             "A0": A[0], "A1": A[-1], "NA": NA}.items():
    page = page.replace(f"__{k}__", str(v))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: a marea das 12 especies de máis valor
top = sorted(d["esp"], key=lambda e: -e["eur"])[:12]
ORD = list(COL)
top.sort(key=lambda e: ORD.index(e["g"]) if e["g"] in ORD else 9)
prof = [[sum(e["m"][i * 12 + m][1] for i in range(NA)) for m in range(12)] for e in top]
tot = [sum(p[m] for p in prof) for m in range(12)]
MX = max(tot)
W, H = 600, 600
xs = [m * W / 11 for m in range(12)]
sy = lambda v: v / MX * H * .8
base = [H / 2 - sy(t) / 2 for t in tot]
polys = []
for k, (e, p) in enumerate(zip(top, prof)):
    y1 = [b + sy(v) for b, v in zip(base, p)]
    pts = [f"{x:.1f},{y:.1f}" for x, y in zip(xs, base)] + [f"{x:.1f},{y:.1f}" for x, y in reversed(list(zip(xs, y1)))]
    polys.append(f'<polygon points="{" ".join(pts)}" fill="{COL.get(e["g"], "#8a8f98")}" fill-opacity="{.72 if k % 2 else .95}"/>')
    base = y1
(OUT / "thumb.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="600" height="600">'
                               f'<rect width="{W}" height="{H}" fill="#f4f8f8"/>{"".join(polys)}</svg>', encoding="utf-8")
print("ok:", OUT, f"percebe ×{ratio:.2f}")

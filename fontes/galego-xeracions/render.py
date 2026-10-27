#!/usr/bin/env python3
"""Xera v/galego-xeracions/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "galego-xeracions"
COL = ["#1d4f91", "#5f97dc", "#ec8a5f", "#b8422a"]

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
A = d["anos"]
G = d["pob"]["Galicia"]
s = lambda y, i: G[y][i][0] / sum(G[y][i]) * 100
h1 = (f'Só <span class="g">{round(s(A[-1], 0))} de cada 100 nenos</span> falan sempre en galego. '
      f'Entre os seus avós, <span class="g">{round(s(A[-1], 4))}</span>')
dek = (f"A pirámide da lingua: cada barra é unha idade, co galego á esquerda e o castelán á dereita. "
       f"En {A[0]} falaban sempre en galego {round(s(A[0], 0))} de cada 100 nenos e nenas; en {A[-1]}, {round(s(A[-1], 0))}. "
       f"Cada xeración fala menos galego ca a anterior, e en vinte anos o galego baixou en todas as idades.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
for k, v in {"DATA": json.dumps(d, ensure_ascii=False, separators=(",", ":")), "H1": h1, "DEK": dek,
             "TITULO": f"Só {round(s(A[-1], 0))} de cada 100 nenos falan sempre en galego; entre os seus avós, {round(s(A[-1], 4))}",
             "A1": A[-1]}.items():
    page = page.replace(f"__{k}__", str(v))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: a pirámide do último ano
rows = [G[A[-1]][i] for i in (4, 3, 2, 1, 0)]
mL, mR = max(r[0] + r[1] for r in rows), max(r[2] + r[3] for r in rows)
k = 540 / (mL + mR)
cx = 30 + mL * k
rects = []
for j, r in enumerate(rows):
    y = 60 + j * 100
    x = cx - (r[0] + r[1]) * k
    for c, n in zip(COL, r):
        rects.append(f'<rect x="{x:.1f}" y="{y}" width="{n * k:.1f}" height="84" fill="{c}"/>')
        x += n * k
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf6"/>{"".join(rects)}'
                               f'<line x1="{cx:.1f}" x2="{cx:.1f}" y1="40" y2="560" stroke="#1d2330" stroke-width="3"/></svg>',
                               encoding="utf-8")
print("ok:", OUT)

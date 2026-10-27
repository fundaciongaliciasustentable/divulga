#!/usr/bin/env python3
"""Xera v/luz-galicia/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "luz-galicia"
COL = {"hid": "#2a78d6", "eol": "#1baf7a", "ren": "#c98500", "cog": "#6250d6", "cc": "#eb6834", "car": "#8a4a1c"}
twh = lambda v: f"{v / 1000:.1f}".replace(".", ",")

D = json.loads((HERE / "data" / "datos.json").read_text())
u = D[-1]
mx = max(D, key=lambda d: d["car"])
ren = lambda d: round((d["hid"] + d["eol"] + d["ren"]) / d["tot"] * 100)
sobra = round((u["tot"] - u["dem"]) / u["tot"] * 100)
titulo = "Galicia xa non queima carbón para ter luz, e aínda lle sobra un terzo"
dek = (f"En {u['y']} Galicia xerou <b>{twh(u['tot'])} TWh</b> de electricidade e consumiu <b>{twh(u['dem'])}</b>. "
       f"O {sobra} % saíu cara a outras comunidades. O {ren(u)} % veu da auga e do vento. "
       f"En {mx['y']} o carbón das Pontes e Meirama era o {round(mx['car'] / mx['tot'] * 100)} % de todo; hoxe é cero.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
dek = dek.replace(" %", "&nbsp;%")
for k, v in {"DATA": json.dumps(D, separators=(",", ":")), "TITULO": titulo, "DEK": dek, "A1": u["y"]}.items():
    page = page.replace(f"__{k}__", str(v))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: as áreas apiladas, sen texto
W, H, M = 600, 600, 40
top = max(d["tot"] for d in D) * 1.05
sx = lambda i: M + i * (W - 2 * M) / (len(D) - 1)
sy = lambda v: H - M - v / top * (H - 2 * M)
base, paths = [0] * len(D), []
for k in COL:
    t = [b + d[k] for b, d in zip(base, D)]
    pts = [f"{sx(i):.1f},{sy(v):.1f}" for i, v in enumerate(t)] + [f"{sx(i):.1f},{sy(base[i]):.1f}" for i in reversed(range(len(D)))]
    paths.append(f'<polygon points="{" ".join(pts)}" fill="{COL[k]}"/>')
    base = t
dem = " ".join(f"{sx(i):.1f},{sy(d['dem']):.1f}" for i, d in enumerate(D))
(OUT / "thumb.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="600" height="600">'
                               f'<rect width="{W}" height="{H}" fill="#fbfaf7"/>{"".join(paths)}'
                               f'<polyline points="{dem}" fill="none" stroke="#1f2328" stroke-width="6" stroke-dasharray="14 9"/></svg>',
                               encoding="utf-8")
print("ok:", OUT, f"sobra {sobra} % · renovable {ren(u)} %")

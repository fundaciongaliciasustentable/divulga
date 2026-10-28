#!/usr/bin/env python3
"""Xera v/renda-concellos/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "renda-concellos"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
C, G = d["conc"], d["agr"]
mil = lambda v: f"{v:,.0f}".replace(",", ".")
ord_ = sorted(C, key=lambda c: -c["p"])
top, baixo = ord_[0], ord_[-1]
baixo_gal = sum(1 for c in C if c["p"] < G["Galicia"]["p"])
dek = (f"En {d['ano']}, a renda neta media en Galicia foi de <b>{mil(G['Galicia']['p'])} euros por persoa</b> "
       f"({mil(G['España']['p'])} en España). Entre concellos, a distancia é de {str(round(top['p'] / baixo['p'], 1)).replace('.', ',')} a 1: "
       f"<b>{mil(top['p'])} €</b> en {top['n']} fronte a {mil(baixo['p'])} € en {baixo['n']}. {baixo_gal} dos {len(C)} concellos quedan por debaixo da media "
       f"galega, que soben as cidades e as súas coroas. Busca o teu.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__ANO__", str(d["ano"])))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: o mapa de Galicia en sete clases de renda
PAL = ['#f1ece0', '#dfe3d3', '#bfd3c4', '#93bab2', '#64999b', '#3d7681', '#1f5262']
v = sorted(c["p"] for c in C)
cut = [v[int(i * len(v) / 7)] for i in range(1, 7)]
s = 520 / max(d["W"], d["H"])
tx, ty = (600 - d["W"] * s) / 2, (600 - d["H"] * s) / 2
el = [f'<path d="{c["d"]}" fill="{PAL[sum(1 for k in cut if c["p"] >= k)]}" stroke="#fbfaf7" stroke-width="1.4"/>' for c in C]
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/><g transform="translate({tx:.1f},{ty:.1f}) scale({s:.4f})">'
                               f'{"".join(el)}</g></svg>', encoding="utf-8")
print("ok:", OUT, (OUT / "index.html").stat().st_size // 1000, "KB")

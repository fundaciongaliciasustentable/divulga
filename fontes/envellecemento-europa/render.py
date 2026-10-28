#!/usr/bin/env python3
"""Xera v/envellecemento-europa/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "envellecemento-europa"
TOPN = 15

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
f1 = lambda v: f"{v:.1f}".replace(".", ",")
mil = lambda v: f"{v:,.0f}".replace(",", ".")
n3, n2 = d["n3"], d["n2"]
posto = lambda c, t: 1 + sum(1 for x in t if t[x][1] > t[c][1])
gal = sorted(("ES111", "ES112", "ES113", "ES114"), key=lambda c: -n3[c][1])
a, b = gal[0], gal[1]
ou = n3[a]
top = max(n3, key=lambda c: n3[c][1])
dek = (f"A metade da poboación de {ou[0]} ten máis de <b>{f1(ou[1])} anos</b>: é a {posto(a, n3)}.ª rexión máis envellecida de "
       f"<b>{mil(len(n3))}</b> da Unión Europea ({d['ult']}), e {n3[b][0]} a {posto(b, n3)}.ª ({f1(n3[b][1])}). "
       f"A idade mediana da UE é de {f1(d['ue'])} anos; a de Galicia, {f1(n2['ES11'][1])}, a {posto('ES11', n2)}.ª de {len(n2)} rexións NUTS 2. "
       f"En {d['a0']} {ou[0]} estaba en {f1(ou[2])}.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__ULT__", str(d["ult"])).replace("__A0__", str(d["a0"])).replace("__N__", mil(len(n3))).replace("__TOPN__", str(TOPN)))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: o mapa en si, coas galegas en maxenta
CORTES = [40, 42.5, 45, 47.5, 50, 52.5]
COR = ['#f1ede2', '#dcdccc', '#b9c4bb', '#8ea6a5', '#64868f', '#406377', '#24415a']
tramo = lambda v: sum(1 for c in CORTES if v >= c)
s = 560 / max(d["w"], d["h"])
tx, ty = (600 - d["w"] * s) / 2, (600 - d["h"] * s) / 2
el = [f'<path d="{d["fondo"]}" fill="#e9e6de"/>']
el += [f'<path d="{p}" fill="{COR[tramo(n3[c][1])]}"/>' for c, p in d["shp"].items()]
el += [f'<path d="{d["shp"][c]}" fill="none" stroke="#c2185b" stroke-width="{2.5 / s:.1f}"/>' for c in gal]
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/><g transform="translate({tx:.1f} {ty:.1f}) scale({s:.4f})">'
                               f'{"".join(el)}</g></svg>', encoding="utf-8")
print("ok:", OUT, "|", dek)
print(f"index.html {(OUT / 'index.html').stat().st_size / 1024:.0f} KB · thumb.svg {(OUT / 'thumb.svg').stat().st_size / 1024:.0f} KB")

#!/usr/bin/env python3
"""Xera v/costa-galicia/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "costa-galicia"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
mil = lambda v: f"{v:,.0f}".replace(",", ".")
C = d["ccaa"]
G = next(c for c in C if c["c"] == "GA")
rI = sorted(C, key=lambda c: -c["ign"])
rD = sorted(C, key=lambda c: -c["dpm"])
pI, pD = rI.index(G) + 1, rD.index(G) + 1
antesI = rI[0] if pI > 1 else rI[1]
antesD = rD[0] if pD > 1 else rD[1]
P = sorted(d["paises"], key=lambda p: p["km"])
menor = [p for p in P if p["km"] < G["ign"]][-1]
maior = [p for p in P if p["km"] > G["ign"]][0]
ord_ = {1: "a máis longa", 2: "a segunda máis longa", 3: "a terceira máis longa"}
pen = sorted([c for c in C if c["c"] not in ("IB", "CN")], key=lambda c: -c["ign"])
xpen = " e a máis longa da Península" if pen[0] is G else ""
dek = (f"Estirada en liña recta, a costa galega mide <b>{mil(G['ign'])} km</b> segundo o IGN, sen contar as illas: "
       f"{ord_[pI]} de España{' despois da de ' + antesI['n'] if pI > 1 else ''}{xpen}. Se se segue o deslinde legal polas rías e "
       f"se suman as illas, son <b>{mil(G['dpm'])} km</b> ({ord_[pD]}{', tras ' + antesD['n'] if pD > 1 else ''}). "
       f"É unha costa de país: entre a de {maior['n']} ({mil(maior['km'])} km) e a de {menor['n']} ({mil(menor['km'])} km) "
       f"no World Factbook, aínda que cada fonte mide cunha vara distinta.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: os fíos das comunidades, cunha marca cada 100 km
el = []
R = [c for c in rI if c["ign"] >= 200]
vmax = max(max(c["ign"], c["dpm"]) for c in R)
sx = lambda v: 50 + v / vmax * 500
for i, c in enumerate(R):
    y = 90 + i * 50
    col = "#c2185b" if c["c"] == "GA" else "#8c9199"
    el.append(f'<line x1="50" x2="{sx(c["ign"]):.0f}" y1="{y}" y2="{y}" stroke="{col}" stroke-width="9" stroke-linecap="round"/>')
    el.append(f'<line x1="50" x2="{sx(c["dpm"]):.0f}" y1="{y + 14}" y2="{y + 14}" stroke="{col if c["c"] == "GA" else "#b9bdc3"}" stroke-width="3" stroke-linecap="round"/>')
    for k in range(100, int(c["ign"]), 100):
        el.append(f'<line x1="{sx(k):.1f}" x2="{sx(k):.1f}" y1="{y - 8}" y2="{y + 8}" stroke="{col}" stroke-width="1.5"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT, f"({(OUT / 'index.html').stat().st_size / 1024:.0f} KB)")
print(dek)

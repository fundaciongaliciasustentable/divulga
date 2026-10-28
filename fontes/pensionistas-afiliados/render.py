#!/usr/bin/env python3
"""Xera v/pensionistas-afiliados/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "pensionistas-afiliados"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
C, G = d["conc"], d["agr"]["Galicia"]
mil = lambda v: f"{v:,.0f}".replace(",", ".")
dec = lambda v, n=2: f"{v:.{n}f}".replace(".", ",")
ra = lambda c: c["af"] / c["pe"]
ord_ = sorted(C, key=ra, reverse=True)
menos1 = sum(1 for c in C if ra(c) < 1)
dek = (f"A fin de {d['ano']} vivían en Galicia <b>{mil(G['af'])} persoas afiliadas á Seguridade Social</b> e {mil(G['pe'])} "
       f"pensionistas: {dec(G['af'] / G['pe'])} traballadores por cada pensionista. Pero en <b>{menos1} dos {len(C)} concellos</b> "
       f"hai máis pensionistas ca afiliados, e en {ord_[-1]['n']} só {dec(ra(ord_[-1]))} por cada un. No outro extremo, {ord_[0]['n']} "
       f"chega a {dec(ra(ord_[0]))}. Cada círculo é un concello; busca o teu.")
ogd = f"Traballadores por cada pensionista, concello a concello: en {menos1} concellos galegos hai máis pensionistas ca afiliados."
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__ANO__", str(d["ano"])).replace("__OGD__", ogd))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: a nube de puntos en log-log coa diagonal do 1
l0, l1 = math.log10(30), math.log10(150000)
sx = lambda v: 40 + (math.log10(v) - l0) / (l1 - l0) * 520
sy = lambda v: 560 - (math.log10(v) - l0) / (l1 - l0) * 520
el = [f'<line x1="{sx(30):.0f}" y1="{sy(30):.0f}" x2="{sx(150000):.0f}" y2="{sy(150000):.0f}" stroke="#1f2328" stroke-width="2"/>']
for c in sorted(C, key=lambda c: -(c["af"] + c["pe"])):
    el.append(f'<circle cx="{sx(c["pe"]):.1f}" cy="{sy(c["af"]):.1f}" r="{max(3, math.sqrt(c["af"] + c["pe"]) / 14):.1f}" '
              f'fill="{"#c98a3d" if ra(c) < 1 else "#2f6f7e"}" fill-opacity=".85" stroke="#fff"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT, (OUT / "index.html").stat().st_size // 1000, "KB")
print(dek)

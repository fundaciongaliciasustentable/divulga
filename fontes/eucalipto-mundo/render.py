#!/usr/bin/env python3
"""Xera v/eucalipto-mundo/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "eucalipto-mundo"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
miles = lambda v: f"{v:,.0f}".replace(",", ".")
pc = lambda v, n=0: f"{v:.{n}f}".replace(".", ",")
G = d["galicia"]
arb = G["e"] + G["c"] + G["f"]
gv = arb / G["sup"] * 100
P = [dict(p, v=p["f"] / p["t"] * 100) for p in d["paises"]] + [{"id": "GZ", "n": "Galicia", "v": gv}]
rk = sorted(P, key=lambda p: -p["v"])
pos = next(i for i, p in enumerate(rk) if p["id"] == "GZ") + 1
pais = {p["id"]: p for p in P}
viz = [pais[k] for k in ("ESP", "PRT", "FRA") if pais[k]["v"] < gv]
ge, pte = G["e"] / G["sup"] * 100, d["pt"]["e"] / d["pt"]["sup"] * 100
C = d["concellos"]
pe = lambda c: c["e"] / c["s"] * 100
top = max(C, key=pe)
n30 = sum(1 for c in C if pe(c) >= 30)
dek = (f"O <b>{pc(gv)} %</b> de Galicia é bosque: o posto {pos} de {len(P)} se fose un país, por riba de "
       f"{', '.join(p['n'] for p in viz[:-1])} e {viz[-1]['n']}. O eucalipto cobre o <b>{pc(ge, 1)} % do territorio</b> "
       f"({miles(G['e'])} ha en {G['ano']}), {'máis' if ge > pte else 'menos'} ca en Portugal continental ({pc(pte, 1)} %). "
       f"En {n30} concellos pasa do 30 %; en {top['n']}, do {pc(pe(top))} %.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__ANOF__", "2025").replace("__ANOG__", str(G["ano"])).replace("__ANOPT__", str(d["pt"]["ano"]))
        .replace("__ANOBR__", str(d["br"]["ano"])))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: o perfil dos 313 concellos
vs = sorted((pe(c) for c in C), reverse=True)
vm = vs[0]
bw = 520 / len(vs)
el = []
for i, v in enumerate(vs):
    h = v / vm * 460
    t = (min(1, v / 50)) ** .5
    col = "#%02x%02x%02x" % tuple(round(a + (b - a) * t) for a, b in zip((236, 234, 226), (22, 92, 99)))
    el.append(f'<rect x="{40 + i * bw:.2f}" y="{530 - h:.1f}" width="{bw + .3:.2f}" height="{h:.1f}" fill="{col}"/>')
gy = 530 - ge / vm * 460
el.append(f'<line x1="40" x2="560" y1="{gy:.0f}" y2="{gy:.0f}" stroke="#c2185b" stroke-width="4"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("dek:", dek)
print("ok:", OUT, (OUT / "index.html").stat().st_size // 1024, "KB")

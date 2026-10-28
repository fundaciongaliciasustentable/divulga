#!/usr/bin/env python3
"""Xera v/paro-concellos/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "paro-concellos"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
C, G, A = d["conc"], d["gal"], d["anos"]
i25 = A.index(2025)
mil = lambda v: f"{v:,.0f}".replace(",", ".")
pc = lambda v: f"{v * 100:.1f}".replace(".", ",") + " %"
t0, t1 = G["s"][0] / G["p11"], G["s"][i25] / G["p25"]
baixa = sum(1 for c in C if c["s"][i25] / c["p25"] < c["s"][0] / c["p11"])
ord_ = sorted((c for c in C if c["p25"] >= 1000), key=lambda c: -c["s"][i25] / c["p25"])  # sen os máis pequenos, moi variables
dek = (f"En setembro de 2012 había en Galicia {mil(G['s'][0])} persoas no paro rexistrado, o {pc(t0)} da poboación de 15 a 64 anos. "
       f"En setembro de 2025 eran <b>{mil(G['s'][i25])}</b>, o <b>{pc(t1)}</b>, e en {A[-1]}, {mil(G['s'][-1])}. A taxa baixou en "
       f"{baixa} dos {len(C)} concellos. Entre os de máis de mil veciños de 15 a 64 anos, onde máis pesa o paro en 2025 é en {ord_[0]['n']} ({pc(ord_[0]['s'][i25] / ord_[0]['p25'])}); "
       f"onde menos, en {ord_[-1]['n']} ({pc(ord_[-1]['s'][i25] / ord_[-1]['p25'])}). Busca o teu concello.")
ogd = f"O paro rexistrado en Galicia pasou do {pc(t0)} da poboación de 15 a 64 anos en 2012 ao {pc(t1)} en 2025. Concello a concello."
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__ULT__", str(A[-1])).replace("__OGD__", ogd))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: as pendentes de todos os concellos e a de Galicia
ymax = 0.25
sy = lambda v: 60 + (1 - min(v, ymax) / ymax) * 480
el = [f'<path d="M110,{sy(c["s"][0] / c["p11"]):.1f}L490,{sy(c["s"][i25] / c["p25"]):.1f}" stroke="#c9c5bb" stroke-width="1.2" fill="none"/>' for c in C]
el.append(f'<path d="M110,{sy(t0):.1f}L490,{sy(t1):.1f}" stroke="#1f2328" stroke-width="7" fill="none" stroke-linecap="round"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT, (OUT / "index.html").stat().st_size // 1000, "KB")
print(dek)

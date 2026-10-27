#!/usr/bin/env python3
"""Xera v/fenda-rural/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "fenda-rural"
COL = {"ZDP": "#6a3d9a", "ZIP": "#1f78b4", "ZPP": "#33a02c"}

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
I = d["ind"]
u = lambda k: I[k]["d"][max(I[k]["d"])]
irpf, pobr, ev, env = u("irpf"), u("pobr"), u("evida"), u("envel")
pc = lambda a, b: round((a - b) / b * 100)
d1 = lambda v: f"{v:.1f}".replace(".", ",")
dek = (f"Nas zonas pouco poboadas declárase un <b>{-pc(irpf['ZPP'], irpf['ZDP'])} % menos de renda</b> no IRPF ca nas cidades, "
       f"pero o risco de pobreza é o máis baixo ({d1(pobr['ZPP'])} % fronte a {d1(pobr['ZDP'])} %) "
       f"e a esperanza de vida, case a mesma. {len(I)} indicadores do IGE para as tres Galicias: cada marca é unha zona e "
       f"a súa distancia á liña central, canto se afasta do total de Galicia.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: dez filas de pesas
ks = sorted(I, key=lambda k: -abs(math.log(u(k)["ZPP"] / u(k)["ZDP"])))[:10]
sx = lambda v: 60 + (math.log(max(18, min(280, v))) - math.log(18)) / (math.log(280) - math.log(18)) * 480
el = [f'<line x1="{sx(100):.1f}" y1="40" x2="{sx(100):.1f}" y2="560" stroke="#1f2328" stroke-width="3"/>']
for i, k in enumerate(ks):
    y = 70 + i * 50
    v = u(k)
    xs = {z: sx(v[z] / v["T"] * 100) for z in COL}
    el.append(f'<line x1="{min(xs.values()):.1f}" y1="{y}" x2="{max(xs.values()):.1f}" y2="{y}" stroke="#b8b4aa" stroke-width="5"/>')
    for z, x in xs.items():
        if z == "ZDP":
            el.append(f'<rect x="{x - 11:.1f}" y="{y - 11}" width="22" height="22" fill="{COL[z]}"/>')
        elif z == "ZIP":
            el.append(f'<path d="M{x:.1f},{y - 14}L{x + 14:.1f},{y}L{x:.1f},{y + 14}L{x - 14:.1f},{y}Z" fill="{COL[z]}"/>')
        else:
            el.append(f'<circle cx="{x:.1f}" cy="{y}" r="12" fill="{COL[z]}"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT)

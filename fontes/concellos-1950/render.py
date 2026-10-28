#!/usr/bin/env python3
"""Xera v/concellos-1950/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "concellos-1950"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
mil = lambda v: f"{v:,.0f}".replace(",", ".")
C = d["conc"]
for o in C:
    a = o["g"]["h50"] if "g" in o else o["h"]["1950"]
    b = o["g"]["p25"] if "g" in o else o["p25"]
    o["r"] = b / a
GA, GB = sum(o["h"].get("1950", 0) for o in C), sum(o["p25"] for o in C)
r = sorted(C, key=lambda o: o["r"])
gan = sum(1 for o in C if o["r"] > 1)
media = sum(1 for o in C if o["r"] < 0.5)
top, fondo = r[-1], r[0]
pc = lambda x: f"{abs(round((x - 1) * 100))}\u00a0%"
dek = (f"Galicia ten {mil(GB)} habitantes ({d['ano']}), un {pc(GB / GA)} máis ca no censo de 1950. Pero só "
       f"<b>{gan} dos {len(C)} concellos</b> teñen hoxe máis xente, e <b>{media}</b> perderon máis da metade: "
       f"{top['n']} multiplicou a súa poboación por {f'{top['r']:.1f}'.replace('.', ',')}, e {fondo['n']} quedou co "
       f"{round(fondo['r'] * 100)}\u00a0% da que tiña. Busca o teu concello.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__ANO__", str(d["ano"])))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: o mapa coroplético
COL = ["#7a4419", "#ad6c34", "#d3a26b", "#efd9b8", "#cfe4df", "#7fb5ab", "#2e7b70"]
col = lambda v: COL[sum(v - 1 >= c for c in (-.75, -.5, -.25, 0, .5, 1))]
xs = [p[0] for o in C for q in o["pol"] for p in q]
ys = [p[1] for o in C for q in o["pol"] for p in q]
x0, y0, s = min(xs), min(ys), 540 / max(max(xs) - min(xs), max(ys) - min(ys))
dx = (600 - (max(xs) - x0) * s) / 2
dy = (600 - (max(ys) - y0) * s) / 2
el = [f'<path d="{"".join("M" + "L".join(f"{(p[0] - x0) * s + dx:.0f},{(p[1] - y0) * s + dy:.0f}" for p in q[::2] + [q[-1]]) + "Z" for q in o["pol"])}" '
      f'fill="{col(o["r"])}" stroke="#fbfaf7" stroke-width=".8"/>' for o in C]
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT, (OUT / "index.html").stat().st_size // 1024, "KB ·", (OUT / "thumb.svg").stat().st_size // 1024, "KB thumb")
print(dek)

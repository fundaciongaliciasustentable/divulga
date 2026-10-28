#!/usr/bin/env python3
"""Xera v/mexillon-mundo/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "mexillon-mundo"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
miles = lambda v: f"{v:,.0f}".replace(",", ".")
pc = lambda v: f"{v:.1f}".replace(".", ",")
A, P = d["anos"], d["paises"]
L = len(A) - 1
rk = sorted([p for p in P if p["s"][L]], key=lambda p: -p["s"][L])
g = next(p for p in P if p["id"] == "GZ")
pos = rk.index(g) + 1
mundo = d["mundo"][L] - d["espana"][L] + g["s"][L]
ord_ = {1: "primeiro", 2: "segundo", 3: "terceiro", 4: "cuarto", 5: "quinto"}
ante = [p["n"] for p in rk[:pos - 1]]
detras = rk[pos]
anos_top2 = [A[i] for i in range(len(A)) if sorted(P, key=lambda p: -p["s"][i]).index(g) == 1]
dek = (f"Coas súas bateas, Galicia sería o <b>{ord_[pos]} produtor de mexillón de acuicultura do mundo</b>: "
       f"<b>{miles(g['s'][L])} toneladas</b> en {A[L]}, o {pc(g['s'][L] / mundo * 100)} % do total"
       f"{', só por detrás de ' + ' e '.join(ante) if ante else ''}"
       f" e por diante de {detras['n']} ({miles(detras['s'][L])} t). "
       f"{f'Foi segunda en {len(anos_top2)} dos {len(A)} anos dende {A[0]}. ' if anos_top2 else ''}"
       f"Cada círculo é un país; move o ano.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__ANOS__", f"{A[0]}-{A[L]}").replace("__UANO__", str(A[L])).replace("__ESP__", miles(d["espana"][L]))
        .replace("__GAL__", miles(g["s"][L])))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: os círculos empaquetados do último ano
cs, R = [], 150
mx = max(p["s"][L] for p in rk)
for p in rk:
    r = max(3, R * math.sqrt(p["s"][L] / mx))
    if not cs:
        cs.append((0, 0, r, p["id"]))
        continue
    best = None
    for (x0, y0, r0, _) in cs:
        for a in range(0, 360, 8):
            t = math.radians(a)
            x, y = x0 + (r0 + r + 3) * math.cos(t), y0 + (r0 + r + 3) * math.sin(t)
            if all(math.hypot(x - q[0], y - q[1]) >= q[2] + r + 2.5 for q in cs):
                dd = x * x + y * y
                if best is None or dd < best[0]:
                    best = (dd, x, y)
    cs.append((best[1], best[2], r, p["id"]))
x0 = min(c[0] - c[2] for c in cs); x1 = max(c[0] + c[2] for c in cs)
y0 = min(c[1] - c[2] for c in cs); y1 = max(c[1] + c[2] for c in cs)
s = min(540 / (x1 - x0), 540 / (y1 - y0))
el = [f'<circle cx="{300 + (c[0] - (x0 + x1) / 2) * s:.0f}" cy="{300 + (c[1] - (y0 + y1) / 2) * s:.0f}" r="{c[2] * s:.1f}" '
      f'fill="{"#c2185b" if c[3] == "GZ" else "#a3a9ad"}" stroke="#fbfaf7" stroke-width="2"/>' for c in cs]
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("dek:", dek)
print("ok:", OUT, (OUT / "index.html").stat().st_size // 1024, "KB")

#!/usr/bin/env python3
"""Xera v/vivenda-turistica/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "vivenda-turistica"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
C, G = d["conc"], d["gal"]
f2 = lambda v: f"{v:.2f}".replace(".", ",")
f1 = lambda v: f"{v:.1f}".replace(".", ",")
mil = lambda v: f"{v:,.0f}".replace(",", ".")
MES = {"M02": "febreiro", "M05": "maio", "M08": "agosto", "M11": "novembro"}
MESR = ["xaneiro", "febreiro", "marzo", "abril", "maio", "xuño", "xullo", "agosto", "setembro", "outubro", "novembro", "decembro"]
corte = lambda s: f"{MES[s[4:]]} de {s[:4]}"
o = sorted(C, key=lambda c: -c["pc"])
a, b = o[0], o[1]
mais2 = sum(c["pc"] >= 2 for c in C)
baixo = sum(c["pc"] < 0.5 for c in C)
dek = (f"En {corte(d['ult'])}, o INE contaba <b>{mil(G['v'])} vivendas turísticas</b> anunciadas en Galicia: "
       f"<b>{f2(G['pc'])} de cada 100</b> vivendas. Pero o reparto é moi desigual: en <b>{a['n']} e {b['n']}</b> son "
       + (f"{f1(a['pc'])} de cada 100" if f1(a['pc']) == f1(b['pc']) else f"{f1(a['pc'])} e {f1(b['pc'])} de cada 100") +
       f"; en {mais2} concellos pasan de 2, e en {baixo} non chegan a 0,5.")
mr = d["mes_reat"]
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__ULT__", corte(d["ult"])).replace("__REAT__", f"{MESR[int(mr[5:]) - 1]} de {mr[:4]}")
        .replace("__REATN__", mil(G["reat"])))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: o mapa coroplético sen bordos
CORT, COR = [.25, .5, 1, 2, 4], ["#f4eee3", "#ead6b8", "#dfb486", "#c98a55", "#a0582b", "#5f2f12"]
xs = [p[0] for c in C for r in c["pol"] for p in r]
ys = [p[1] for c in C for r in c["pol"] for p in r]
x0, y0, s = min(xs), min(ys), 520 / max(max(xs) - min(xs), max(ys) - min(ys))
dx = (600 - (max(xs) - x0) * s) / 2
dy = (600 - (max(ys) - y0) * s) / 2
el = []
for c in C:
    dd = "".join("M" + "L".join(f"{(x - x0) * s + dx:.0f},{(y - y0) * s + dy:.0f}" for x, y in r[::3] + [r[0]]) + "Z" for r in c["pol"])
    el.append(f'<path d="{dd}" fill="{COR[sum(c["pc"] >= t for t in CORT)]}"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/><g stroke="#fbfaf7" stroke-width=".8">{"".join(el)}</g></svg>', encoding="utf-8")
print("ok:", OUT, (OUT / "index.html").stat().st_size // 1024, "KB", "thumb", (OUT / "thumb.svg").stat().st_size // 1024, "KB")
print(dek)

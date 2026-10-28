#!/usr/bin/env python3
"""Xera v/calculadora-persoal/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "calculadora-persoal"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
mil = lambda v: f"{v:,.0f}".replace(",", ".")
L = {int(k): v for k, v in d["lume"].items()}
ha85 = sum(v for a, v in L.items() if a >= 1985)
B = {int(k): v for k, v in d["totBal"].items()}
dek = (f"Escribe o ano no que naciches. Se foi en 1985, dende entón arderon en Galicia {mil(ha85)} hectáreas e hai "
       f"{mil(B[max(B)] - B[min(B)])} aldeas máis sen ninguén que en {min(B)}. Seis contas sobre o que cambiou na túa vida, "
       f"feitas cos datos doutras pezas de Divulga.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__AP0__", str(d["anosAp"][0])).replace("__AP1__", str(d["anosAp"][1])))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: «1985 →» e as barras dos lumes dende entón
anos = sorted(L)
mx = max(L.values())
el = ['<text x="300" y="170" text-anchor="middle" font-family="Barlow Condensed,Arial Narrow,sans-serif" font-weight="700" '
      'font-size="140" fill="#1f2328">1985 →</text>']
bw = 520 / len(anos)
for i, a in enumerate(anos):
    h = L[a] / mx * 300
    el.append(f'<rect x="{40 + i * bw:.1f}" y="{540 - h:.1f}" width="{bw - 2:.1f}" height="{h:.1f}" fill="{"#d95f02" if a >= 1985 else "#d9d5cc"}"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT)

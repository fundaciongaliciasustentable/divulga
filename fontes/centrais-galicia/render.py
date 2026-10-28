#!/usr/bin/env python3
"""Xera v/centrais-galicia/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "centrais-galicia"
COR = {"hidraulica": "#2166ac", "eolica": "#1b9e77", "ciclo": "#e08214", "solar": "#c2185b"}

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
C = d["c"]
mil = lambda v: f"{v:,.0f}".replace(",", ".")
maior = max(C, key=lambda c: c["mw"])
eol = [c for c in C if c["t"] == "eolica"]
hid = [c for c in C if c["t"] == "hidraulica"]
pech = sum(p["mw"] for p in d["pech"])
nb = lambda n: n.replace("Central de Ciclo Combinado Endesa - ", "o ciclo combinado de ").replace("de As Pontes", "das Pontes")
dek = (f"Galicia ten {mil(d['reeTotal'])} MW de potencia eléctrica. Aquí están, unha a unha, as {len(C)} centrais que se poden "
       f"identificar: <b>{len(eol)} parques eólicos</b>, ningún de máis de 50 MW, que xuntos suman {mil(sum(c['mw'] for c in eol))} MW; "
       f"<b>{len(hid)} centrais hidráulicas</b>, con Santo Estevo e Belesar á cabeza; e {nb(maior['n'])}, a maior de todas, con "
       f"{mil(maior['mw'])} MW. En trazo discontinuo, as térmicas de carbón das Pontes e Meirama: {mil(pech)} MW que xa non producen.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: unha fila de círculos coas vinte maiores centrais
top = sorted(C, key=lambda c: -c["mw"])[:20]
k = 300 / math.sqrt(top[0]["mw"])
el, x, y, fila = [], 20, 0, []
for c in top:
    r = math.sqrt(c["mw"]) * k / 2.2
    if x + 2 * r > 580:
        x, y = 20, y + 1
    cy = 170 + y * 230
    el.append(f'<circle cx="{x + r:.0f}" cy="{cy:.0f}" r="{r:.0f}" fill="{COR.get(c["t"], "#9aa3ad")}" stroke="#fff" stroke-width="2"/>')
    x += 2 * r + 6
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT)

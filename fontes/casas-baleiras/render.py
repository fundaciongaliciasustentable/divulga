#!/usr/bin/env python3
"""Xera v/casas-baleiras/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "casas-baleiras"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
C, G = d["conc"], d["gal"]
pc = lambda v: f"{v * 100:.0f}"
mil = lambda v: f"{v:,.0f}".replace(",", ".")
ord_ = sorted(C, key=lambda c: -c["np"] / c["t"])
mais50 = sum(1 for c in C if c["np"] / c["t"] >= 0.5)
top = ord_[0]
def en(n):
    """«en» + nome con artigo: en A Teixeira → na Teixeira."""
    for art, c in (("As ", "nas "), ("Os ", "nos "), ("A ", "na "), ("O ", "no ")):
        if n.startswith(art):
            return c + n[len(art):]
    return "en " + n


bar = next((c for c in C if c["n"] == "Barreiros"), None)
dek = (f"<b>{mil(G['np'])}</b> vivendas galegas, catro de cada dez, non teñen ninguén empadroado. En {mais50} concellos son "
       f"máis da metade, e {en(top['n'])} chegan ao {pc(top['np'] / top['t'])} %. Non todas están igual de soas: no interior "
       f"tampouco teñen luz, están abandonadas; na costa moitas son segundas residencias"
       + (f", como en Barreiros, co {pc(bar['np'] / bar['t'])} % sen empadroados pero só o {pc(bar['b'] / bar['tl'])} % sen consumo" if bar and "b" in bar else "")
       + ". Toca un concello para ver as súas dez casas.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__NL__", str(sum(1 for c in C if "b" in c))))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: cinco fiadas de dez casas (dos concellos máis baleiros aos menos)
CASA = "M3 11.5L12 4l9 7.5V21H3z"
el = []
for f, c in enumerate([ord_[0], ord_[40], ord_[150], ord_[250], ord_[-1]]):
    n = round(c["np"] / c["t"] * 10)
    for i in range(10):
        a = i >= n
        el.append(f'<g transform="translate({30 + i * 54},{60 + f * 105}) scale(2.1)"><path d="{CASA}" fill="{"#e08214" if a else "none"}" '
                  f'stroke="{"#e08214" if a else "#c9c5bb"}" stroke-width="1.8" stroke-linejoin="round"/></g>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT)

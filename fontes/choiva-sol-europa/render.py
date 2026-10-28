#!/usr/bin/env python3
"""Xera v/choiva-sol-europa/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "choiva-sol-europa"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
mil = lambda v: f"{v:,.0f}".replace(",", ".")
pc = lambda v: f"{v:.1f}".replace(".", ",")
C = d["cidades"]
by = {c["n"]: c for c in C}
GA = [c for c in C if c["g"] == "g"]
mxG = max(GA, key=lambda c: c["mm"])
minsol = min(GA, key=lambda c: c["sol"])
lon = by["Londres"]
# capitais e grandes cidades do norte con menos sol ca a cidade galega menos soleada
ref = [n for n in ("Londres", "París", "Bruxelas", "Ámsterdam", "Dublín", "Berlín") if by[n]["sol"] < minsol["sol"]]
lista = ", ".join(ref[:-1]) + " ou " + ref[-1] if len(ref) > 1 else ref[0]
dek = (f"{mxG['n']} recolle <b>{mil(mxG['mm'])} litros por m²</b> ao ano, {pc(mxG['mm'] / lon['mm'])} veces o que cae en Londres. "
       f"Pero as seis cidades galegas teñen entre <b>{mil(minsol['sol'])} e {mil(max(c['sol'] for c in GA))} horas de sol</b>, "
       f"máis ca {lista}. Os días de choiva non son moitos máis ({mil(mxG['dias'])} en {mxG['n']}, {mil(lon['dias'])} en Londres); "
       f"o que cambia é canta auga cae cada un: {pc(mxG['mm'] / mxG['dias'])} l/m² fronte a {pc(lon['mm'] / lon['dias'])}. "
       f"Normais climatolóxicas {d['periodo']}.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: a dispersión choiva × sol
S = [c for c in C if c["sol"]]
xmax = max(c["mm"] for c in C)
y0, y1 = min(c["sol"] for c in S), max(c["sol"] for c in S)
el = ['<line x1="50" x2="560" y1="550" y2="550" stroke="#e5e2da" stroke-width="2"/>',
      '<line x1="50" x2="50" y1="40" y2="550" stroke="#e5e2da" stroke-width="2"/>']
COR = {"g": "#c2185b", "e": "#5f636b", "u": "#a9aeb5"}
for c in sorted(S, key=lambda c: c["g"] == "g"):
    x = 60 + c["mm"] / xmax * 490
    y = 530 - (c["sol"] - y0) / (y1 - y0) * 470
    el.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{13 if c["g"] == "g" else 10}" fill="{COR[c["g"]]}" stroke="#fff" stroke-width="2"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT, f"({(OUT / 'index.html').stat().st_size / 1024:.0f} KB)")
print(dek)

#!/usr/bin/env python3
"""Xera v/apelidos-galegos/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "apelidos-galegos"
COR = {"15": "#2166ac", "27": "#1b9e77", "32": "#c2185b", "36": "#e08214"}

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
A = d["ap"]
tit = lambda s: " ".join(w.capitalize() for w in s.lower().split())
mil = lambda v: f"{v:,.0f}".replace(",", ".")
pc = lambda v: f"{v * 100:.0f}"
by = {a["a"]: a for a in A}
galegos = [a for a in A if a["g"] >= 0.75]
top = max(galegos, key=lambda a: a["n"])
mais = max((a for a in A if a["n"] >= 10000), key=lambda a: a["g"])
garcia = by.get("GARCIA")
dek = (f"Galicia ten o {d['pobGal'] * 100:.1f}".replace(".", ",") + f" % da poboación de España, pero hai apelidos que case non saen dela. "
       f"{len(galegos)} primeiros apelidos teñen tres de cada catro portadores vivindo en Galicia. O máis común deles é "
       f"<b>{tit(top['a'])}</b> ({mil(top['n'])} persoas, o {pc(top['g'])} % en Galicia); entre os de máis de 10.000, "
       f"o máis galego é {tit(mais['a'])}, co {pc(mais['g'])} %."
       + (f" E García, o máis común de España, só ten aquí o {pc(garcia['g'])} %." if garcia else "")
       + " Busca o teu.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__MIN__", mil(d["min"])).replace("__N__", mil(len(A))).replace("__PG__", f"{d['pobGal'] * 100:.1f}".replace(".", ",")))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: unha nube cos quince apelidos galegos máis comúns
nube = sorted(galegos, key=lambda a: -a["n"])[:15]
nmax, nmin = nube[0]["n"], nube[-1]["n"]
el, y, x = [], 110, 40
for a in nube:
    s = 26 + 46 * ((a["n"] - nmin) / (nmax - nmin or 1)) ** 0.5
    w = len(a["a"]) * s * 0.6
    if x + w > 570:
        x, y = 40, y + 74
    c = COR[max(a["pm"], key=a["pm"].get)]
    el.append(f'<text x="{x:.0f}" y="{y}" font-family="Raleway,Arial,sans-serif" font-weight="800" font-size="{s:.0f}" fill="{c}">{tit(a["a"])}</text>')
    x += w + 18
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT)

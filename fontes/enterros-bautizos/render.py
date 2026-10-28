#!/usr/bin/env python3
"""Xera v/enterros-bautizos/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py   (precisa fontes/vacas-persoas xerada)
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "enterros-bautizos"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
mil = lambda v: f"{v:,.0f}".replace(",", ".")
A, C, G = d["anos"], d["conc"], d["gal"]
ult = A[-1]
i5 = [A.index(a) for a in range(ult - 4, ult + 1)]
i75 = [A.index(a) for a in range(1975, 1980)]
s = lambda arr, ii: sum(arr[i] for i in ii)
mais5 = [o for o in C if s(o["d"], i5) > s(o["b"], i5)]
menos5 = [o for o in C if o not in mais5]
mais75 = sum(1 for o in C if s(o["d"], i75) > s(o["b"], i75))
mais_ult = sum(1 for o in C if o["d"][-1] > o["b"][-1])
lista = lambda os: " e ".join(o["n"] for o in os)
dek = (f"Entre {ult - 4} e {ult}, <b>{len(mais5)} dos {len(C)} concellos</b> galegos tiveron máis defuncións ca nacementos; "
       f"a excepción foi {lista(menos5)}. Entre 1975 e 1979 pasaba en {mais75}. En {ult} (datos provisionais) naceron en Galicia "
       f"{mil(G['b'][-1])} persoas e morreron {mil(G['d'][-1])}: <b>{G['b'][-1] / G['d'][-1] * 10:.0f} berces por cada 10 cruces</b>.")
if len(menos5) == 0:
    dek = dek.replace(f"; a excepción foi .", ".")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__ULT__", str(ult)))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: o cartograma de hexágonos no último quinquenio
COL = ["#2b2d33", "#55585f", "#80838a", "#a9abb0", "#cfd0d2", "#e6e6e4", "#8cc1a4", "#3f8f6a"]
col = lambda v: COL[sum(v >= c for c in (1, 2, 4, 6, 8, 10, 15))]
R = 20
DX, DY = math.sqrt(3) * R, 1.5 * R
pts = [((o["h"][0] * DX + (DX / 2 if o["h"][1] % 2 else 0)), -o["h"][1] * DY, o) for o in C]
x0, x1 = min(p[0] for p in pts) - R, max(p[0] for p in pts) + R
y0, y1 = min(p[1] for p in pts) - R, max(p[1] for p in pts) + R
k = 560 / max(x1 - x0, y1 - y0)
ox, oy = (600 - (x1 - x0) * k) / 2, (600 - (y1 - y0) * k) / 2
hexd = lambda x, y: "M" + "L".join(f"{x + R * .95 * k * math.cos(math.radians(60 * j - 30)):.1f},{y + R * .95 * k * math.sin(math.radians(60 * j - 30)):.1f}" for j in range(6)) + "Z"
el = [f'<path d="{hexd((x - x0) * k + ox, (y - y0) * k + oy)}" fill="{col(s(o["b"], i5) / max(1, s(o["d"], i5)) * 10)}"/>' for x, y, o in pts]
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT, (OUT / "index.html").stat().st_size // 1024, "KB")
print(dek)
print("último ano, concellos con máis defuncións:", mais_ult)

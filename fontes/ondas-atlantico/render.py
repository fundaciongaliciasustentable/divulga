#!/usr/bin/env python3
"""Xera v/ondas-atlantico/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "ondas-atlantico"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
A = d["anos"]
c = lambda v, n=1: f"{v:.{n}f}".replace(".", ",")
dec = lambda xs: sum(x["m"] for x in xs) / len(xs)
pri, ult = A[:10], A[-10:]
quente = max(A, key=lambda x: x["m"])
mn = lambda xs: sum(x["min"] for x in xs) / len(xs)
dek = (f"Unha onda por ano, dende {A[0]['a']} (arriba) ata {A[-1]['a']} (abaixo): a temperatura da auga fronte ás Rías Baixas "
       f"cada día do ano. As ondas van fuxindo cara á dereita: a última década está <b>{c(dec(ult) - dec(pri))} °C máis quente</b> "
       f"ca a primeira, e o día máis frío do ano xa non baixa de {c(mn(ult))} °C de media (eran {c(mn(pri))}). "
       f"O ano máis quente foi {quente['a']}, con {c(quente['m'], 2)} °C de media, e a tendencia é de "
       f"{c(d['tend'], 2)} °C por década.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__N0__", str(d["normal"][0])).replace("__N1__", str(d["normal"][1])).replace("__NORM__", c(d["norm"], 2)))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: as ondas en branco sobre negro, como a portada
X0, PX, NX = d["x"]
xmin = min(x["min"] for x in A) - 0.6
xmax = max(x["max"] for x in A) + 0.6
sx = lambda t: 70 + (t - xmin) / (xmax - xmin) * 460
ymax = max(v for x in A for v in x["d"])
el = []
for i, x in enumerate(A):
    y0 = 120 + i * 9.5
    pts = [f"{sx(X0 + j * PX):.1f},{y0 - v / ymax * 70:.1f}" for j, v in enumerate(x["d"]) if xmin <= X0 + j * PX <= xmax]
    el.append(f'<path d="M{pts[0].split(",")[0]},{y0}L{"L".join(pts)}L{pts[-1].split(",")[0]},{y0}Z" fill="#0d0f12" '
              f'stroke="#e9e6df" stroke-width="1.6"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#0d0f12"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT)

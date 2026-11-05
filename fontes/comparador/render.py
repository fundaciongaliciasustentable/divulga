#!/usr/bin/env python3
"""Xera v/comparador/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "comparador"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
CONC, IND, GRUPOS = d["concellos"], d["indicadores"], d["grupos"]
n_val = sum(len(v["valores"]) for v in IND.values())

dek = (f"Escolle dous indicadores calquera entre os <b>{len(IND)}</b> dispoñibles —idade, renda, paro, "
       f"vidro reciclado, vacas, débeda, galego, turismo e máis— e mira como se moven xuntos nos "
       f"<b>{len(CONC)} concellos</b> galegos. Cando ambos teñen serie temporal, dálle a reproducir.")

page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: a propia bólla-tipo, renda (x) vs idade media (y), tamaño pola
# poboación, cor pola provincia — a mesma lóxica có comparador en si.
COR = {"A Coruña": "#2E6B8A", "Lugo": "#8B5E3C", "Ourense": "#7A7A2E", "Pontevedra": "#6B4C8A"}
renda = {k: v for k, v in IND["renda"]["valores"].items()}
idade = {k: v for k, v in IND["idade_media"]["valores"].items()}
pob = {k: v for k, v in IND["poboacion"]["valores"].items()}


def ult(serie):
    return serie[max(serie, key=int)] if serie else None


pts = []
for c in CONC:
    rv, iv, pv = ult(renda.get(c["id"], {})), ult(idade.get(c["id"], {})), ult(pob.get(c["id"], {}))
    if rv is None or iv is None or pv is None:
        continue
    pts.append((c, rv, iv, pv))

xs, ys = [p[1] for p in pts], [p[2] for p in pts]
x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
smax = max(p[3] for p in pts)
sx = lambda v: 40 + (v - x0) / (x1 - x0) * 520
sy = lambda v: 560 - ((v - y0) / (y1 - y0) * 520)
rr = lambda v: max(3, min(16, (v / smax) ** .5 * 42))

circ = "".join(
    f'<circle cx="{sx(r):.0f}" cy="{sy(i):.0f}" r="{rr(p):.1f}" fill="{COR.get(c["pr"], "#999")}" '
    f'fill-opacity=".82" stroke="#fff" stroke-width="1"/>'
    for c, r, i, p in sorted(pts, key=lambda t: -t[3])
)
(OUT / "thumb.svg").write_text(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
    f'<rect width="600" height="600" fill="#fbfaf7"/>{circ}</svg>', encoding="utf-8")

print("ok:", OUT, (OUT / "index.html").stat().st_size // 1024, "KB")
print(f"{len(IND)} indicadores, {n_val} series, {len(CONC)} concellos")
print(dek)

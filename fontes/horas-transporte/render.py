#!/usr/bin/env python3
"""Xera v/horas-transporte/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "horas-transporte"
RAMPA = ["#fff4e6", "#fdd49e", "#fdbb84", "#fc8d59", "#e34a33", "#b30000", "#6b0000"]
LIM = [30, 60, 90, 120, 180, 240]

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
C = d["conc"]
nome = {c["id"]: c["n"] for c in C}
T = d["orixes"]["Santiago"]
hm = lambda v: f"{v} minutos" if v < 60 else f"{v // 60} h {v % 60:02d} min"
dentro2 = sum(1 for c in C if T.get(c["id"], 10 ** 9) <= 120)
lonx = max(T, key=T.get)
sen = len(C) - len(T)
mais_lonx_cid = {o: max(v.values()) for o, v in d["orixes"].items()}
dia = f"{d['dia'][6:]}/{d['dia'][4:6]}/{d['dia'][:4]}"
dek = (f"Un martes pola mañá, saíndo de Santiago en autobús ou en tren, chégase en menos de dúas horas a <b>{dentro2} dos {len(C)}</b> "
       f"concellos. O máis afastado é {nome[lonx]}, a <b>{hm(T[lonx])}</b>, e {sen} concellos non teñen ningunha chegada en toda a "
       f"mañá. Escolle a cidade de saída e cambia ao «mapa do tempo» para ver Galicia deformada polas horas de viaxe.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek).replace("__DIA__", dia)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: o mapa dende Santiago
x0, y0, x1, y1 = d["bbox"]
k = 560 / max(x1 - x0, y1 - y0)
ox, oy = (600 - (x1 - x0) * k) / 2, (600 - (y1 - y0) * k) / 2
el = []
for c in C:
    v = T.get(c["id"])
    i = sum(v >= l for l in LIM) if v is not None else None
    col = RAMPA[i] if i is not None else "#e4e1da"
    dd = "".join("M" + "L".join(f"{ox + (p[0] - x0) * k:.1f},{oy + (p[1] - y0) * k:.1f}" for p in r) + "Z" for r in c["pol"])
    el.append(f'<path d="{dd}" fill="{col}" stroke="#fff" stroke-width=".6"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT)

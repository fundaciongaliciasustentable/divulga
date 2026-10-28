#!/usr/bin/env python3
"""Xera v/encoros/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "encoros"
MESES = ["xaneiro", "febreiro", "marzo", "abril", "maio", "xuño", "xullo", "agosto", "setembro", "outubro", "novembro", "decembro"]

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
S, T, E = d["sem"], d["tot"], d["enc"]
fe = lambda s: f"{int(s[8:])} de {MESES[int(s[5:7]) - 1]} de {s[:4]}"
i_min = min((i for i, v in enumerate(T) if v is not None), key=lambda i: T[i])
w = date.fromisoformat(S[-1]).isocalendar()[1] - 1
nor = sum(e["c"] * e["nor"][w] for e in E) / sum(e["c"] for e in E)
cap = sum(e["c"] for e in E)
mil = lambda v: f"{v:,.0f}".replace(",", ".")
dek = (f"Corenta encoros das concas galegas, {mil(cap)} hm³ entre todos, debuxados coma vasos. "
       f"O {fe(S[-1])} estaban ao <b>{T[-1]:.0f} %</b>, cando o normal desa semana é o {nor:.0f} %. "
       f"O mínimo dende 1988 foi o {fe(S[i_min])}, co {T[i_min]:.0f} %. Move a data ou dálle ao play para ver como se "
       f"enchen no inverno e se baleiran no verán.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: seis vasos cos maiores encoros hoxe
el, x = [], 30
for e in E[:6]:
    wv, h = 70, 300
    p = e["p"][-1] or 0
    el.append(f'<rect x="{x}" y="{150 + h * (1 - p / 100):.0f}" width="{wv}" height="{h * p / 100:.0f}" fill="#2c7fb8" opacity=".85"/>'
              f'<path d="M{x},150 L{x + 5},{150 + h} L{x + wv - 5},{150 + h} L{x + wv},150" fill="none" stroke="#9aa3ad" stroke-width="5"/>')
    x += 92
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT)

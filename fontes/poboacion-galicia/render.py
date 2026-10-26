#!/usr/bin/env python3
"""Xera v/poboacion-galicia/index.html e thumb.svg desde data/layout.json.

Pasos completos:  python3 prep.py  →  node layout.js s51  →  python3 render.py
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "poboacion-galicia"
COL = {"A Coruña": "#a8c3df", "Pontevedra": "#e9b39e", "Ourense": "#f1d98f",
       "Lugo": "#b7d3a8", "Exterior": "#cdbfe0"}

d = json.loads((HERE / "data" / "layout.json").read_text(encoding="utf-8"))
simbolo = re.search(r"<g[^>]*>(.*)</g>", (ROOT / "assets/logos/favicon.svg").read_text(), re.S).group(1)

page = ((HERE / "viz.tpl.html").read_text(encoding="utf-8")
        .replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":")))
        .replace("__ANOP__", str(d["anoPadron"]))
        .replace("__ANOE__", str(d["anoPERE"]))
        .replace("__SIMBOLO__", simbolo))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")


def rnd(poly):
    return " ".join(",".join(str(round(float(v))) for v in p.split(",")) for p in poly.split())


cells = "".join(f'<polygon points="{rnd(c["poly"])}" fill="{COL[c["p"]]}"/>' for c in d["cells"])
groups = "".join(f'<polygon points="{rnd(g["poly"])}"/>' for g in d["groups"])
thumb = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-560 -560 1120 1120" width="600" height="600">'
         f'<rect x="-560" y="-560" width="1120" height="1120" fill="#242228"/>'
         f'<g stroke="#242228" stroke-width="2">{cells}</g>'
         f'<g fill="none" stroke="#242228" stroke-width="7" stroke-linejoin="round">{groups}</g>'
         f'<circle r="{d["R"] + 1}" fill="none" stroke="#242228" stroke-width="8"/></svg>')
(OUT / "thumb.svg").write_text(thumb, encoding="utf-8")
print("ok:", OUT / "index.html", f"({len(page) // 1024} KB)", "+ thumb.svg", f"({len(thumb) // 1024} KB)")

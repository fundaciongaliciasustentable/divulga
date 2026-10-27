#!/usr/bin/env python3
"""Xera v/raias-clima/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "raias-clima"
RDBU = ["#053061", "#2166ac", "#4393c3", "#92c5de", "#d1e5f0", "#f7f7f7",
        "#fddbc7", "#f4a582", "#d6604d", "#b2182b", "#67001f"]

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8").replace(
    "__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":")))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: as raias de calor da Coruña, a serie máis longa
e = d["est"][0]
s = [x for x in e["s"] if x["t"] is not None]
a, b = s[0]["y"], s[-1]["y"]
w = 600 / (b - a + 1)
col = lambda v: RDBU[round(max(-2, min(2, v)) / 2 * 5) + 5]
rects = "".join(f'<rect x="{(x["y"] - a) * w:.2f}" width="{w + .5:.2f}" height="600" fill="{col(x["t"])}"/>'
                for x in e["s"] if x["t"] is not None and x["y"] >= a)
(OUT / "thumb.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#2c2f36"/>{rects}</svg>', encoding="utf-8")
print("ok:", OUT, f"({len(page) // 1024} KB)")

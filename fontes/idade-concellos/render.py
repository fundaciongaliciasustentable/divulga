#!/usr/bin/env python3
"""Xera v/idade-concellos/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "idade-concellos"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
f1 = lambda v: f"{v:.1f}".replace(".", ",")
C, G = d["conc"], d["gal"]
r = sorted(C, key=lambda o: o["im"])
novo, vello = r[0], r[-1]
n300 = sum(1 for o in C if o["ie"] >= 300)
dek = (f"A idade media en Galicia é de <b>{f1(G['im'])} anos</b> ({d['ano']}), {f1(G['im'] - G['im0'])} máis ca en {d['ano0']}. "
       f"Pero vai dos {f1(novo['im'])} anos de {novo['n']} aos {f1(vello['im'])} de {vello['n']}, e en <b>{n300} dos {len(C)} concellos</b> "
       f"hai tres ou máis maiores de 65 anos por cada menor de 20. Cada punto é un concello; busca o teu.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__ANO0__", str(d["ano0"])).replace("__ANO__", str(d["ano"])))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: catro filas dun enxame coloreado polo envellecemento
random.seed(4)
COL = ["#e3ddd0", "#c9b99a", "#a88f68", "#7a6446", "#4a3b29"]
col = lambda v: COL[sum(v >= c for c in (100, 200, 300, 500))]
x0, x1 = min(o["im"] for o in C), max(o["im"] for o in C)
el = []
for i, p in enumerate(["A Coruña", "Lugo", "Ourense", "Pontevedra"]):
    for o in sorted((o for o in C if o["pr"] == p), key=lambda o: o["ie"]):
        x = 50 + (o["im"] - x0) / (x1 - x0) * 500
        el.append(f'<circle cx="{x:.0f}" cy="{110 + i * 125 + random.gauss(0, 18):.0f}" r="7" fill="{col(o["ie"])}" stroke="#fbfaf7" stroke-width="1.5"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT, (OUT / "index.html").stat().st_size // 1024, "KB")
print(dek)

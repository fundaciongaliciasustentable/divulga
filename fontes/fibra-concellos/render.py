#!/usr/bin/env python3
"""Xera v/fibra-concellos/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "fibra-concellos"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
C, G = d["conc"], d["gal"]
f1 = lambda v: f"{v:.1f}".replace(".", ",")
mil = lambda v: f"{v:,.0f}".replace(",", ".")
def en(n):
    for art, c in (("As ", "nas "), ("Os ", "nos "), ("A ", "na "), ("O ", "no ")):
        if n.startswith(art):
            return c + n[len(art):]
    return "en " + n


C.sort(key=lambda c: -c["g100"])
peor = C[-1]
menos50 = sum(c["g100"] < 50 for c in C)
sen = sum((100 - c["g100"]) / 100 * c["fog"] for c in C)
peq = [c for c in C if c["hab"] < 5000]
sen_peq = sum((100 - c["g100"]) / 100 * c["fog"] for c in peq)
fog_peq = sum(c["fog"] for c in peq) / sum(c["fog"] for c in C)
dek = (f"A 30 de xuño de 2025, o <b>{f1(G['g100'])} %</b> dos fogares galegos podía contratar internet fixa a 100 Mbps e o "
       f"<b>{f1(G['g1'])} %</b> a 1 Gbps. Quedan fóra uns {mil(round(sen, -3))} fogares, e o {sen_peq / sen * 100:.0f} % deles "
       f"está nos {len(peq)} concellos de menos de 5.000 habitantes, que só teñen o {fog_peq * 100:.0f} % dos fogares. En "
       f"<b>{menos50} concellos</b> os 100 Mbps non chegan nin á metade das casas; {en(peor['n'])}, só ao {f1(peor['g100'])} %.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: a liña de horizonte
el, n = [], len(C)
w = 520 / n
for i, c in enumerate(C):
    x = 40 + i * w
    for v, col in ((100, "#efede7"), (c["g100"], "#8cbfc3"), (c["g1"], "#1d5e6a")):
        el.append(f'<rect x="{x:.2f}" y="{500 - v * 3.6:.1f}" width="{w + .3:.2f}" height="{v * 3.6:.1f}" fill="{col}"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}'
                               '<line x1="40" x2="560" y1="500" y2="500" stroke="#1f2328" stroke-width="2"/></svg>', encoding="utf-8")
print("ok:", OUT, (OUT / "index.html").stat().st_size // 1024, "KB")
print(dek)

#!/usr/bin/env python3
"""Xera v/bibliotecas-concellos/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "bibliotecas-concellos"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
mil = lambda v: f"{v:,.0f}".replace(",", ".")
dec = lambda v, n=2: f"{v:.{n}f}".replace(".", ",")
C, g, ano = d["conc"], d["gal"], d["ano"]
sen = [c for c in C if not c["b"]]
nd = [c for c in C if c["b"] and "p" not in c]
grandes = sorted([c for c in C if "p" in c and c["h"] >= 10000], key=lambda c: -c["p"] / c["h"])
top, ult = grandes[0], grandes[-1]
dek = (f"En {ano}, as {g['b']} bibliotecas públicas galegas fixeron <b>{dec(g['pr'] / 1e6)} millóns de préstamos</b>, "
       f"{dec(g['pr'] / g['h'])} por habitante. Entre os concellos de máis de 10.000 habitantes con datos, vai de {dec(top['p'] / top['h'])} en "
       f"{top['n']} a {dec(ult['p'] / ult['h'])} en {ult['n']}. E <b>{len(sen)} concellos</b>, onde viven {mil(sum(c['h'] for c in sen))} "
       f"persoas, non tiñan ningunha biblioteca pública. Cada lombo deste andel é un concello.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
for k, v in {"__DATA__": json.dumps(d, ensure_ascii=False, separators=(",", ":")), "__DEK__": dek, "__ANO__": str(ano),
             "__ND__": str(len(nd))}.items():
    page = page.replace(k, v)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: catro andeis de lombos ordenados
TONS = ["#b7aa92", "#a3967e", "#c5baa5", "#978a73", "#bdb09a"]
el = []
for j, p in enumerate(["A Coruña", "Lugo", "Ourense", "Pontevedra"]):
    cs = [c for c in C if c["pr"] == p]
    ok = sorted([c for c in cs if "p" in c], key=lambda c: -c["p"] / c["h"])
    base, x, bw = 150 + j * 135, 40, 520 / 93
    for i, c in enumerate(ok):
        h = min(c["p"] / c["h"], 2.4) / 2.4 * 105 + 2
        col = "#c2185b" if c["n"] == "Lugo" else TONS[(i * 7 + len(c["n"])) % 5]
        el.append(f'<rect x="{x:.1f}" y="{base - h:.1f}" width="{bw - 1:.1f}" height="{h:.1f}" fill="{col}"/>')
        x += bw
    for c in cs:
        if "p" not in c:
            el.append(f'<rect x="{x + .5:.1f}" y="{base - 10}" width="{bw - 2:.1f}" height="10" fill="none" stroke="#b9b2a3" stroke-dasharray="2 2"/>')
            x += bw
    el.append(f'<rect x="36" y="{base}" width="528" height="7" fill="#8a7a62"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT, (OUT / "index.html").stat().st_size // 1024, "KB")
print(dek)

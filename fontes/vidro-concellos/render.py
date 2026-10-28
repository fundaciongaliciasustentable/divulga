#!/usr/bin/env python3
"""Xera v/vidro-concellos/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "vidro-concellos"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
A, C, G = d["anos"], d["conc"], d["gal"]
U = len(A) - 1
d1 = lambda v: f"{v:.1f}".replace(".", ",")
kh = lambda c, i=U: c["kg"][i] / c["pob"][i] if c["kg"][i] and c["pob"][i] else None
gk = lambda i: G[str(A[i])]["contedor"] / d["pob"][i]
pico = max(range(len(A)), key=gk)
cidades = sorted((c for c in C if c["pob"][U] >= 60000 and kh(c)), key=kh)
alta, baixa = cidades[-1], cidades[0]
con = [c for c in C if kh(c)]
sobre = sum(1 for c in con if kh(c) >= gk(U))
sen = [c["n"] for c in C if not kh(c)]

NUM = {7: "sete", 6: "seis", 8: "oito"}
dek = (f"En {A[U]} cada galego levou ao contedor verde <b>{d1(gk(U))} kg de vidro</b>, "
       + (f"menos que os {d1(gk(pico))} de {A[pico]}. " if pico != U else "o máximo da serie. ")
       + f"Entre as {NUM.get(len(cidades), len(cidades))} cidades, {alta['n']} chega a <b>{d1(kh(alta))} kg</b> por habitante e {baixa['n']} queda en "
       f"{d1(kh(baixa))}. {sobre} dos {len(con)} concellos con dato están por riba da media galega. Busca o teu.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__ULT__", str(A[U])).replace("__ANOS__", f"{A[0]}-{A[U]}")
        .replace("__SENDATO__", " e ".join(sen) if sen else "ningún"))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: catro enxames de puntos verdes (un por provincia), cun punto magenta
CORTES, CORES = [8, 12, 16, 20, 25], ["#e4efe3", "#bcdcb9", "#8cc28c", "#5a9f68", "#2f7a4c", "#164f31"]
cor = lambda v: CORES[sum(1 for t in CORTES if v >= t)]
el = []
for f, pv in enumerate(["A Coruña", "Lugo", "Ourense", "Pontevedra"]):
    pts = []
    for c in sorted((c for c in con if c["pr"] == pv), key=lambda c: -c["pob"][U]):
        x, r = 40 + min(kh(c), 40) / 40 * 520, max(3, min(15, c["pob"][U] ** .5 * .06))
        y = 0
        for k in range(80):
            cand = (1 if k % 2 else -1) * ((k + 1) // 2) * 2
            if all(((x - a) ** 2 + (cand - b) ** 2) ** .5 >= r + s + .8 for a, b, s in pts):
                y = cand
                break
        pts.append((x, y, r))
        hl = c is alta
        el.append(f'<circle cx="{x:.0f}" cy="{95 + f * 135 + y:.0f}" r="{r:.1f}" fill="{"#c2185b" if hl else cor(kh(c))}" '
                  f'stroke="#fff" stroke-width="1"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT, (OUT / "index.html").stat().st_size // 1024, "KB")
print(dek)

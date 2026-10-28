#!/usr/bin/env python3
"""Xera v/pib-rexions/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "pib-rexions"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
A, R, N = d["anos"], d["rex"], d["n"]
G = next(r for r in R if r["c"] == "ES11")
ES = [r for r in R if r["p"] == "España"]
posto_es = lambda i: 1 + sum(1 for r in ES if r["v"][i] > G["v"][i])
mellor = min(range(len(A)), key=lambda i: (G["r"][i], -A[i]))
ant_mellor = min(G["r"][:-1])
xunta = lambda xs: ", ".join(xs[:-1]) + " e " + xs[-1] if len(xs) > 1 else xs[0]

subiu = G["r"][0] - G["r"][-1]
dek = (f"En {A[0]} Galicia era a rexión <b>{G['r'][0]}</b> de {N} da UE en PIB por habitante, medido en poder de compra; "
       f"en {A[-1]} é a <b>{G['r'][-1]}</b>, co {G['v'][-1]} % da media europea (dende o {G['v'][0]} %). "
       f"{'Sobe' if subiu > 0 else 'Baixa'} {abs(subiu)} postos e, entre as {len(ES)} rexións españolas, pasa da {posto_es(0)}ª á {posto_es(-1)}ª. "
       + (f"É o seu mellor posto da serie: antes da crise de 2008 chegara ao {ant_mellor}."
          if G["r"][-1] < ant_mellor else f"O seu mellor posto foi o {G['r'][mellor]}, en {A[mellor]}."))
prov = xunta([str(a) for a in d["prov"]]) if d["prov"] else ""
prov = (prov + (" son provisionais" if len(d["prov"]) > 1 else " é provisional")) if prov else "ningún ano é provisional"
paises = [p for p in d["fora"] if p != "Mayotte"]
fora = "as rexións de " + xunta(paises) + (", e Mayotte" if "Mayotte" in d["fora"] else "")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__A0__", str(A[0])).replace("__A1__", str(A[-1])).replace("__N__", str(N)).replace("__FORA__", fora)
        .replace("__ACT__", "/".join(reversed(d["actualizado"].split("-")))).replace("__PROV__", prov))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: o feixe de liñas, coas españolas e Galicia por riba
W, H, M = 600, 600, 50
sx = lambda i: M + i / (len(A) - 1) * (W - 2 * M)
sy = lambda r: M + (r - 1) / (N - 1) * (H - 2 * M)
pth = lambda r: "M" + "L".join(f"{sx(i):.0f},{sy(v):.0f}" for i, v in enumerate(r["r"]))
el = [f'<path d="{pth(r)}" fill="none" stroke="#d8d5cc" stroke-width="1.2"/>' for r in R[::2] if r["p"] != "España"]
el += [f'<path d="{pth(r)}" fill="none" stroke="#8a8e96" stroke-width="2"/>' for r in ES if r["c"] != "ES11"]
el.append(f'<path d="{pth(G)}" fill="none" stroke="#fbfaf7" stroke-width="12"/><path d="{pth(G)}" fill="none" stroke="#c2185b" stroke-width="7" stroke-linejoin="round"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT)
print(dek)

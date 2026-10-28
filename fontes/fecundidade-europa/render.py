#!/usr/bin/env python3
"""Xera v/fecundidade-europa/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "fecundidade-europa"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
f2 = lambda v: f"{v:.2f}".replace(".", ",")
ORD = {1: "a cifra máis baixa", 2: "a segunda cifra máis baixa", 3: "a terceira cifra máis baixa", 4: "a cuarta cifra máis baixa",
       5: "a quinta cifra máis baixa"}
reg = d["reg"]  # de menos a máis
n = len(reg)
ids = [r[0] for r in reg]
cola = ids.index("ES11") + 1
g = reg[cola - 1][2]
posto = n - cola + 1
eu = d["serie"]["EU"][-1][1]
es = d["serie"]["ES"][-1][1]
ano = d["ano"]
baixo1 = sum(1 for r in reg if r[2] < 1)
dek = (f"En {ano} Galicia tivo <b>{f2(g)} fillos por muller</b>, {ORD.get(cola, f"a {cola}.ª cifra máis baixa")} das {n} rexións da Unión Europea "
       f"(posto {posto} de {n}). A media da UE foi de {f2(eu)} e a de España, de {f2(es)}; o relevo xeracional pide 2,1. "
       f"Só {baixo1} rexións quedan por baixo de un fillo{', e Galicia é unha delas' if g < 1 else ''}.")
gs = d["serie"]["ES11"]
gm = max(gs, key=lambda p: p[1])
h2 = f"Galicia tocou teito en {gm[0]}, con {f2(gm[1])}, e volveu baixar"
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek).replace("__H2__", h2)
        .replace("__ANO__", str(ano)).replace("__N__", str(n)).replace("__A0__", str(min(s[0][0] for s in d["serie"].values()))))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: o perfil de barras, con Galicia en maxenta
el = []
R = list(reversed(reg))
bw = 520 / n
for i, r in enumerate(R):
    v = min(r[2], 2.4)
    h = v / 2.4 * 420
    el.append(f'<rect x="{40 + i * bw:.2f}" y="{510 - h:.1f}" width="{bw:.2f}" height="{h:.1f}" fill="{"#c2185b" if r[0] == "ES11" else "#c9c5bb"}"/>')
gi = [r[0] for r in R].index("ES11")
el.append(f'<rect x="{40 + gi * bw - 1.5:.1f}" y="{510 - g / 2.4 * 420:.1f}" width="{bw + 3:.1f}" height="{g / 2.4 * 420:.1f}" fill="#c2185b"/>')
el.append(f'<line x1="40" x2="560" y1="{510 - 2.1 / 2.4 * 420:.1f}" y2="{510 - 2.1 / 2.4 * 420:.1f}" stroke="#1f2328" stroke-width="2" stroke-dasharray="8 6"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT, "|", dek)
print(h2)

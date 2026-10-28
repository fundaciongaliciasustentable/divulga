#!/usr/bin/env python3
"""Xera v/centenarios/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "centenarios"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
f1 = lambda v: f"{v:.1f}".replace(".", ",")
mil = lambda v: f"{v:,.0f}".replace(",", ".")
tx = lambda s: s[1] / s[2] * 1e4
ORD = {1: "primeira", 2: "segunda", 3: "terceira", 4: "cuarta", 5: "quinta", 6: "sexta", 7: "sétima", 8: "oitava", 9: "novena", 10: "décima"}
pr = sorted((p for p in d["prov"] if not p["t"]), key=lambda p: -tx(p["s"][-1]))
es = next(p for p in d["prov"] if p["t"])
n = len(pr)
gal = [(i + 1, p) for i, p in enumerate(pr) if p["g"]]
g1i, g1 = gal[0]
g2i, g2 = gal[1]
diante = [p["n"] for p in pr[:g1i - 1]]
lista = ", ".join(diante[:-1]) + " e " + diante[-1] if len(diante) > 1 else (diante[0] if diante else "")
ult = d["ult"]
gtot = sum(p["s"][-1][1] for _, p in gal)
er = sorted(d["eur"]["reg"], key=lambda r: -r[2] / r[3])
ge = [r[0] for r in er].index("ES11") + 1
gev = next(r for r in er if r[0] == "ES11")
dek = (f"A 1 de xaneiro de {ult} vivían en {g1['n']} <b>{mil(g1['s'][-1][1])} persoas de 100 anos ou máis</b>: "
       f"<b>{f1(tx(g1['s'][-1]))} por cada 10.000 habitantes</b>, a {ORD.get(g1i, str(g1i) + '.ª')} provincia de España"
       + (f", despois de {lista}" if lista else "") + f". {g2['n']} é a {ORD.get(g2i, str(g2i) + '.ª')} ({f1(tx(g2['s'][-1]))}); "
       f"a media española é {f1(tx(es['s'][-1]))}. En toda Galicia hai {mil(gtot)} centenarios, e entre as {len(er)} rexións da UE "
       f"con datos Galicia é a {ge}.ª ({d['eur']['ano']}).")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__ULT__", str(ult)).replace("__A0__", str(d["a0"])).replace("__EANO__", str(d["eur"]["ano"]))
        .replace("__EN__", str(len(er))).replace("__PROV__", " (datos provisionais)" if d["prov_ult"] else ""))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: unhas cantas pesas
el = []
top = pr[:12]
xm = max(max(tx(p["s"][-1]), tx(next(s for s in p["s"] if s[0] == d["a0"]))) for p in top)
for i, p in enumerate(top):
    y = 70 + i * 40
    a = tx(next(s for s in p["s"] if s[0] == d["a0"]))
    u = tx(p["s"][-1])
    xa, xu = 60 + a / xm * 480, 60 + u / xm * 480
    c, c2 = ("#c2185b", "#f3c6d8") if p["g"] else ("#4b4f57", "#e5e2da")
    el.append(f'<line x1="{xa:.0f}" x2="{xu:.0f}" y1="{y}" y2="{y}" stroke="{c2}" stroke-width="10" stroke-linecap="round"/>'
              f'<circle cx="{xa:.0f}" cy="{y}" r="7" fill="#fbfaf7" stroke="{c}" stroke-width="3"/><circle cx="{xu:.0f}" cy="{y}" r="10" fill="{c}"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT, "|", dek)

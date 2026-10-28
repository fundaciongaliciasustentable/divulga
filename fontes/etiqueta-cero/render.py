#!/usr/bin/env python3
"""Xera v/etiqueta-cero/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "etiqueta-cero"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
A, C, G, E = d["anos"], d["conc"], d["ccaa"]["Galicia"], d["esp"]
U = len(A) - 1
d1 = lambda v: f"{v:.1f}".replace(".", ",")
mil = lambda v: f"{v:,.0f}".replace(",", ".")
tx = lambda x, i=U: x["z"][i] / x["pob"][i] * 1000
cc = sorted(d["ccaa"], key=lambda n: -tx(d["ccaa"][n]))
posto = cc.index("Galicia") + 1
veces = G["z"][U] / G["z"][0]
cidades = sorted((c for c in C if c["pob"][U] >= 60000), key=tx)
mais = max((c for c in C if c["pob"][U] >= 10000), key=tx)

dek = (f"En Galicia había a finais de {A[U]} <b>{mil(G['z'][U])} vehículos con etiqueta CERO</b>, eléctricos e híbridos "
       f"enchufables: {d1(veces).replace(',0', '')} veces máis que en {A[0]}. Aínda así son {d1(tx(G))} por cada mil habitantes, "
       f"fronte a <b>{d1(tx(E))} en España</b>: Galicia é a {posto}ª de {len(cc)} comunidades. Entre os concellos de máis de "
       f"10.000 habitantes vai diante {mais['n']} ({d1(tx(mais))}); entre as cidades, {cidades[-1]['n']} ({d1(tx(cidades[-1]))}) "
       f"e {cidades[0]['n']} ({d1(tx(cidades[0]))}) nos extremos.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__ULT__", str(A[U])).replace("__A0__", str(A[0])))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: o feixe de liñas, coa de Galicia en negro e unha en magenta
YM = 40
sx = lambda i: 50 + i / U * 500
sy = lambda v: 550 - min(v, YM) / YM * 480
path = lambda ys: "M" + "L".join(f"{sx(i):.0f},{sy(v):.0f}" for i, v in enumerate(ys))
el = [f'<path d="{path([tx(c, i) for i in range(len(A))])}" fill="none" stroke="#c9c5bb" stroke-width="1.6" opacity=".6"/>' for c in C]
el.append(f'<path d="{path([tx(mais, i) for i in range(len(A))])}" fill="none" stroke="#c2185b" stroke-width="7"/>')
el.append(f'<path d="{path([tx(G, i) for i in range(len(A))])}" fill="none" stroke="#1f2328" stroke-width="8"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT, (OUT / "index.html").stat().st_size // 1024, "KB")
print(dek)

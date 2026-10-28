#!/usr/bin/env python3
"""Xera v/minutos-hospital/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "minutos-hospital"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
C, G = d["conc"], d["gal"]
mil = lambda v: f"{v:,.0f}".replace(",", ".")
pc = lambda v: f"{v * 100:.0f}"
def en(n):
    for art, c in (("As ", "nas "), ("Os ", "nos "), ("A ", "na "), ("O ", "no ")):
        if n.startswith(art):
            return c + n[len(art):]
    return "en " + n


o = sorted(C, key=lambda c: -c["m"])
mais45 = sum(c["m"] > 45 for c in C)
dek = (f"Para máis da metade dos galegos (<b>{pc(G['p15'])} %</b>) o hospital público máis próximo está a 15 minutos en coche ou menos. "
       f"Pero <b>{mil(round(G['h30'], -3))} persoas</b>, o {pc(G['p30'])} %, viven a máis de media hora, e en {mais45} concellos "
       f"a viaxe media pasa dos 45 minutos; {en(o[0]['n'])} chega a {o[0]['m']:.0f} minutos.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__NE__", mil(G["ne"])))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: a grella de isócronas
BAN, COR = [10, 20, 30, 45, 60], ["#f2efe6", "#cfe0d6", "#93bfae", "#5a9384", "#2f6467", "#173a49"]
S, cel = d["cel"], d["grella"]
i0, j0 = min(c[0] for c in cel), min(c[1] for c in cel)
ni, nj = max(c[0] for c in cel) - i0 + 1, max(c[1] for c in cel) - j0 + 1
k = 540 / max(ni, nj)
ox, oy = (600 - ni * k) / 2, (600 - nj * k) / 2
paths = ["" for _ in COR]
for i, j, m, _ in cel:
    paths[sum(m > t for t in BAN)] += f"M{ox + (i - i0) * k:.1f},{oy + (j - j0) * k:.1f}h{k:.1f}v{k:.1f}h-{k:.1f}Z"
el = [f'<path d="{p}" fill="{c}"/>' for p, c in zip(paths, COR) if p]
for h in d["hosp"]:
    x, y = ox + (h["xy"][0] / S - i0) * k, oy + (h["xy"][1] / S - j0) * k
    el.append(f'<path d="M{x - 7:.0f},{y:.0f}h14M{x:.0f},{y - 7:.0f}v14" stroke="#c2185b" stroke-width="5"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT, (OUT / "index.html").stat().st_size // 1024, "KB", "thumb", (OUT / "thumb.svg").stat().st_size // 1024, "KB")
print(dek)

#!/usr/bin/env python3
"""Xera v/nomes-galicia/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "nomes-galicia"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
G = set(d["galegos"])
H, M = d["dec"]["12"]["H"], d["dec"]["12"]["M"]
anos = sorted(d["anos"]["H"], key=int)
ult = anos[-1]
tit = lambda n: n.capitalize().replace("Maria", "María").replace("Sofia", "Sofía").replace("Lucia", "Lucía")
TIL = {"UXIA": "Uxía", "ANTIA": "Antía", "ANTON": "Antón", "LUA": "Lúa", "ICIA": "Icía", "MARTIÑO": "Martiño"}
tg = lambda n: TIL.get(n, n.capitalize())
galx = [[n for n in H[i] + M[i] if n in G] for i in range(len(H))]
pri = next(i for i, g in enumerate(galx) if g)
dek = (f"Os galegos nados nos anos corenta, cincuenta e sesenta chámanse sobre todo <b>Manuel</b>, e as galegas, Carmen e "
       f"María del Carmen. Os bebés de hoxe, <b>{tit(d['anos']['H'][ult][0][0])}</b> e <b>{tit(d['anos']['M'][ult][0][0])}</b>. "
       f"Entre medias, os nomes compostos desaparecen e chegan as formas propias do galego: ningunha entra entre os 30 máis comúns "
       f"ata os anos {d['decadas'][pri][2:]}, con {tg(galx[pri][0])}, e na década de 2020 xa son {len(galx[-1])} "
       f"({', '.join(map(tg, galx[-1][:5]))}…). Un río de rankings década a década, dende antes de 1930, e ano a ano dende 2000.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek).replace("__A1__", ult)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: o río dos 8 primeiros nomes de home por década
L = [c[:8] for c in H]
cx = lambda i: 40 + i * 52
cy = lambda r: 80 + r * 60
el = []
for n in {x for c in L for x in c}:
    pts = [(cx(i), cy(c.index(n))) for i, c in enumerate(L) if n in c]
    if len(pts) < 2:
        continue
    dd = f"M{pts[0][0]},{pts[0][1]}" + "".join(f"L{x},{y}" for x, y in pts[1:])
    col = "#1b9e77" if n in G else ("#c2185b" if n == "MANUEL" else "#c9c5bb")
    el.append(f'<path d="{dd}" fill="none" stroke="{col}" stroke-width="{7 if n == "MANUEL" else 4}" stroke-linecap="round" stroke-linejoin="round"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(sorted(el, key=lambda s: "c2185b" in s))}</svg>', encoding="utf-8")
print("ok:", OUT)

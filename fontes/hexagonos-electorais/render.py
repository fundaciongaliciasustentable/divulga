#!/usr/bin/env python3
"""Xera v/hexagonos-electorais/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "hexagonos-electorais"
HEX = {"PP": "#1f5fa8", "PSdeG": "#d7191c", "BNG": "#41b6c4", "Esq": "#e08214"}

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
E = d["elec"]
gana = lambda i: {c: max(e["p"], key=e["p"].get) for c, e in E[i].items() if e["p"]}
segundo = lambda i: {c: sorted(e["p"], key=e["p"].get)[-2] for c, e in E[i].items() if len(e["p"]) > 1}
pp = lambda i: sum(1 for v in gana(i).values() if v == "PP")
igual = lambda a, b: sum(1 for c, v in gana(a).items() if gana(b).get(c) == v)
s24 = sum(1 for v in segundo("parl-2024").values() if v == "BNG")
dek = (f"Para a Xunta e para o Congreso, o PP gaña en case todos os concellos: en <b>{pp('parl-2024')} dos 313</b> nas autonómicas "
       f"de 2024 e en {pp('xer-2023')} nas xerais de 2023. Nos concellos é outra cousa: nas municipais de 2023 gañou en {pp('mun-2023')}, "
       f"e no resto mandan o PSdeG, o BNG e as listas locais. Só en {igual('parl-2024', 'mun-2023')} concellos gañou o mesmo partido "
       f"nas autonómicas e nas municipais. Detrás, o BNG é segundo en {s24} concellos en 2024. Cada concello pesa igual, sexa Vigo ou "
       f"Negueira de Muñiz; usa «Comparar» para cruzar dúas eleccións.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: o mapa de quen queda segundo en 2024
H = d["hex"]
qs, rs = [h["q"] for h in H.values()], [h["r"] for h in H.values()]
k = 560 / max((max(qs) - min(qs)) * math.sqrt(3) * 10, max(rs) * 15)
S = 10 * k
seg = segundo("parl-2024")
el = []
for c, h in H.items():
    cx = 20 + (h["q"] - min(qs)) * S * math.sqrt(3)
    cy = 20 + h["r"] * S * 1.5
    pts = " ".join(f"{cx + S * math.cos(math.radians(60 * i - 90)):.1f},{cy + S * math.sin(math.radians(60 * i - 90)):.1f}" for i in range(6))
    el.append(f'<polygon points="{pts}" fill="{HEX.get(seg.get(c), "#ccc")}" stroke="#fbfaf7" stroke-width="1.5"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT)

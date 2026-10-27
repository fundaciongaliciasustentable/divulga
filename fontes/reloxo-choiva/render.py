#!/usr/bin/env python3
"""Xera v/reloxo-choiva/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "reloxo-choiva"
RAMPA = ["#eef4fa", "#d3e3f2", "#adcbe6", "#7fadd6", "#5089c2", "#2c65a6", "#163f7a"]
LIM = [0.03, 0.07, 0.12, 0.18, 0.25, 0.33]

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
E = {e["n"]: e for e in d["est"]}


def perfil(e, k="mm"):
    return [sum(m[h] for m in e[k] if m[h] is not None) / sum(m[h] is not None for m in e[k]) for h in range(24)]


mil = lambda v: f"{v:,.0f}".replace(",", ".")
mollada = max(E.values(), key=lambda e: e["anual"])
seca = min(E.values(), key=lambda e: e["anual"])
# Noite e madrugada (0-8 h) fronte a tarde (15-21 h): canto máis chove nunha que noutra, en %
franxa = lambda e, hs: sum(perfil(e)[h] for h in hs) / len(hs)
noite = lambda e: round((franxa(e, range(0, 9)) / franxa(e, range(15, 22)) - 1) * 100)
mes = lambda e, ms: sum(sum(e["mm"][m]) for m in ms) / len(ms)
inv = mes(E["Santiago"], (0, 1, 10, 11)) / mes(E["Santiago"], (5, 6, 7))
dek = (f"Dez anos de choiva, hora a hora, en seis cidades. O que manda é o mes: en Santiago chove {inv:.0f} veces máis "
       f"en inverno ca no verán. Pero a hora tamén conta: en Pontevedra chove un {noite(E['Pontevedra'])}\u00a0% máis de noite "
       f"e de madrugada ca pola tarde, e en Lugo e Ourense, ao revés, as tardes son as máis mollas. Cada reloxo ten as 24 horas "
       f"en círculo, coa medianoite arriba, e un anel por mes: <b>canto máis escuro, máis chove</b>.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__A0__", str(d["anos"][0])).replace("__A1__", str(d["anos"][1])))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: o reloxo de Santiago
e = E["Santiago"]
cx = cy = 300
R0, R1 = 80, 280
dr = (R1 - R0) / 12
el = []
for m in range(12):
    for h in range(24):
        v = e["mm"][m][h]
        i = 0
        while v is not None and i < len(LIM) and v >= LIM[i]:
            i += 1
        r0, r1 = R0 + m * dr, R0 + (m + 1) * dr
        a0, a1 = h / 24 * 2 * math.pi - math.pi / 2, (h + 1) / 24 * 2 * math.pi - math.pi / 2
        P = lambda r, a: f"{cx + r * math.cos(a):.1f},{cy + r * math.sin(a):.1f}"
        el.append(f'<path d="M{P(r0, a0)}L{P(r1, a0)}A{r1},{r1} 0 0 1 {P(r1, a1)}L{P(r0, a1)}A{r0},{r0} 0 0 0 {P(r0, a0)}Z" '
                  f'fill="{RAMPA[i] if v is not None else "#f3f1ec"}" stroke="#fff" stroke-width="1"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT)

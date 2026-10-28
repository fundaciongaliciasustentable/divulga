#!/usr/bin/env python3
"""Xera v/residuos-europa/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "residuos-europa"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
f1 = lambda v: f"{v:.1f}".replace(".", ",")
P, C, ue = d["paises"], d["ccaa"], d["ue"]
G = next(c for c in C if c["c"] == "12")
menos_p = [p["n"] for p in sorted(P, key=lambda p: p["kg"]) if p["kg"] < G["kg"]]
posto_c = 1 + sum(1 for c in C if c["kg"] < G["kg"])
posto_sep = 1 + sum(1 for c in C if c["sep"] > G["sep"])
xunta = lambda xs: ", ".join(xs[:-1]) + " e " + xs[-1] if len(xs) > 1 else xs[0]
dek = (f"En {d['ano']} recolléronse en Galicia <b>{f1(G['kg'])} kg</b> de residuos municipais por habitante, {round(ue['kg'] - G['kg'])} menos ca media da UE ({ue['kg']} kg): "
       f"na escala europea só {xunta(menos_p)} quedan por debaixo, e entre as comunidades é a {posto_c}ª que menos recolle de {len(C)}. "
       f"Onde queda atrás é na separación: só o <b>{f1(G['sep'])} %</b> chega por recollida separada, "
       f"{'a porcentaxe máis baixa' if posto_sep == len(C) else f'a {posto_sep}ª de {len(C)}'}, fronte ao {f1(d['es_ine']['sep'])} % de España.")
fl = {"p": "dato provisional", "e": "dato estimado", "b": "rotura de serie"}
marcas = {}
for p in P:
    for ch in p["f"]:
        if ch in fl:
            marcas.setdefault(fl[ch], []).append(p["n"])
flags = "; ".join(f"{k}: {xunta(v)}" for k, v in marcas.items()) or "sen marcas"
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__ANO__", str(d["ano"])).replace("__FLAGS__", flags)
        .replace("__ESINE__", f1(d["es_ine"]["kg"])).replace("__ESEU__", str(d["es_eurostat"]["kg"])))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: barras ordenadas con tramo escuro, Galicia intercalada
filas = sorted([(p["kg"], p["rc"], False) for p in P] + [(G["kg"], None, True)], key=lambda x: -x[0])
kmax = max(f[0] for f in filas)
el = []
rh = 520 / len(filas)
for i, (kg, rc, g) in enumerate(filas):
    y, w = 40 + i * rh, kg / kmax * 520
    el.append(f'<rect x="40" y="{y:.1f}" width="{w:.0f}" height="{rh - 4:.1f}" fill="{"#f1c7d7" if g else "#dcd8ce"}"/>')
    if rc is not None:
        el.append(f'<rect x="40" y="{y:.1f}" width="{w * rc / 100:.0f}" height="{rh - 4:.1f}" fill="#4f6f5c"/>')
    if g:
        el.append(f'<rect x="40" y="{y:.1f}" width="{w:.0f}" height="{rh - 4:.1f}" fill="#c2185b"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT)
print(dek)
print(flags)

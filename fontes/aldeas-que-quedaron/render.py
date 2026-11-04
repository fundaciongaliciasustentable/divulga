#!/usr/bin/env python3
"""Xera v/aldeas-que-quedaron/index.html a partir de peza.tpl.html e datos.json coas paradas.

Copia a barra .dv-bar e o pé .dv-foot de v/galicia-cero-neto/ para que coincidan co
resto de Divulga, e cambia a licenza do pé a CC BY-SA 4.0 (a peza usa capas CC BY-SA
de Mapas Galicia Sustentable). Uso: python3 render.py
"""
import html
import json
import re
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
modelo = (RAIZ / "v" / "galicia-cero-neto" / "index.html").read_text(encoding="utf-8")
bar = re.search(r'<header class="dv-bar">.*?</header>', modelo, re.S).group(0)
foot = re.search(r'<footer class="dv-foot">.*?</footer>', modelo, re.S).group(0)
assert "CC BY-NC-SA 4.0" in foot
foot = foot.replace(
    "CC BY-NC-SA 4.0",
    "CC BY-SA 4.0 · Datos: INE, IGE, © IET Xunta de Galicia (CC BY-SA 4.0) · "
    "Relevo: © Instituto Geográfico Nacional, MDT (PNOA-LiDAR), CC BY 4.0")
tpl = (AQUI / "peza.tpl.html").read_text(encoding="utf-8")
out = tpl.replace("{{BAR}}", bar).replace("{{FOOT}}", foot)
dest = RAIZ / "v" / "aldeas-que-quedaron" / "index.html"
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(out, encoding="utf-8")
print(dest)


def texto(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


paradas = []
for n, m in enumerate(re.finditer(r'<section class="paso"([^>]*)>(.*?)</section>', tpl, re.S)):
    at = dict(re.findall(r'data-([a-z]+)="([^"]*)"', m.group(1)))
    corpo = m.group(2)
    g = lambda pat: (re.search(pat, corpo, re.S) or [None, None])[1]  # noqa: E731
    paradas.append({
        "paso": n,
        "onde": texto(g(r'<p class="onde">(.*?)</p>')),
        "titulo": texto(g(r"<h[12]>(.*?)</h[12]>")),
        "camara": {"centro": [float(x) for x in at["centro"].split(",")], "zoom": float(at["zoom"]),
                   "inclinacion": float(at.get("inclinacion", 55)), "rumbo": float(at.get("rumbo", 0))},
        "capas": [c for c in at.get("capa", "").split(",") if c],
        "marcas": [s.split("|")[1] for s in at.get("marca", "").split(";") if "|" in s],
        "dato": texto(g(r'<p class="dato">(.*?)</p>')),
        "dato_l": texto(g(r'<p class="dato-l">(.*?)</p>')),
        "fonte": texto(g(r'<p class="fonte">(.*?)</p>')),
    })
palabras = len(texto(re.search(r'<div class="voo-pasos">(.*?)</main>', tpl, re.S).group(1)).split())
(AQUI / "datos.json").write_text(json.dumps(
    {"slug": "aldeas-que-quedaron", "palabras_pasos": palabras,
     "cifras_calculadas": "cifras.json (prep.py)", "paradas": paradas},
    ensure_ascii=False, indent=1), encoding="utf-8")
print(f"datos.json: {len(paradas)} paradas, {palabras} palabras nos pasos")

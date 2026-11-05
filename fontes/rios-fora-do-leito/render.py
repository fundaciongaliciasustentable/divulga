#!/usr/bin/env python3
"""Xera v/rios-fora-do-leito/index.html a partir de peza.tpl.html.

Copia a barra .dv-bar e o pé .dv-foot de v/galicia-cero-neto/ para que coincidan co resto
de Divulga, e cambia a licenza do pé (CC BY-SA 4.0: a peza usa capas CC BY-SA de Mapas
Galicia Sustentable) coas atribucións principais. Uso: python3 render.py
"""
import re
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
modelo = (RAIZ / "v" / "galicia-cero-neto" / "index.html").read_text(encoding="utf-8")
bar = re.search(r'<header class="dv-bar">.*?</header>', modelo, re.S).group(0)
foot = re.search(r'<footer class="dv-foot">.*?</footer>', modelo, re.S).group(0)
foot = foot.replace(
    "CC BY-NC-SA 4.0",
    "CC BY-SA 4.0 · Datos: Augas de Galicia e MeteoGalicia (Xunta de Galicia); "
    "SNCZI, MITECO (CC BY 4.0); ríos © colaboradores de OpenStreetMap (ODbL); "
    "relevo © Instituto Geográfico Nacional (CC BY 4.0)")
out = (AQUI / "peza.tpl.html").read_text(encoding="utf-8").replace("{{BAR}}", bar).replace("{{FOOT}}", foot)
dest = RAIZ / "v" / "rios-fora-do-leito" / "index.html"
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(out, encoding="utf-8")
print(dest)

# datos.json: as paradas (cámara, capas, cifras e fonte) tal e como están no HTML
import html
import json

pasos = []
for i, m in enumerate(re.finditer(r'<section class="paso"(.*?)>(.*?)</section>', out, re.S)):
    attrs = dict(re.findall(r'data-([a-z]+)="([^"]*)"', m.group(1)))
    corpo = m.group(2)

    def g(pat):
        x = re.search(pat, corpo, re.S)
        return html.unescape(re.sub(r"<[^>]+>", "", x.group(1))).strip() if x else None

    pasos.append({
        "n": i, "onde": g(r'<p class="onde">(.*?)</p>'), "titulo": g(r"<h[12]>(.*?)</h[12]>"),
        "camara": {"centro": [float(v) for v in attrs["centro"].split(",")], "zoom": float(attrs["zoom"]),
                   "inclinacion": float(attrs["inclinacion"]), "rumbo": float(attrs["rumbo"])},
        "capas": [c for c in attrs.get("capa", "").split(",") if c], "marcas": attrs.get("marca"),
        "dato": g(r'<p class="dato">(.*?)</p>'), "dato_l": g(r'<p class="dato-l">(.*?)</p>'),
        "fonte": g(r'<p class="fonte">(.*?)</p>'),
    })
(AQUI / "datos.json").write_text(json.dumps(
    {"slug": "rios-fora-do-leito", "titulo": "Cando os ríos saen do leito", "data": "2026-11-04",
     "cifras_calculadas": "data/cifras.json (saída de prep.py)", "paradas": pasos},
    ensure_ascii=False, indent=1), encoding="utf-8")
print(AQUI / "datos.json")

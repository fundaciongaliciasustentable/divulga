#!/usr/bin/env python3
"""Xera v/rias-que-traballan/index.html a partir de peza.tpl.html.

Copia a barra .dv-bar e o pé .dv-foot de v/galicia-cero-neto/ para que coincidan
co resto de Divulga e cambia a licenza do pé a CC BY-SA 4.0 (a peza usa capas
CC BY-SA de Mapas Galicia Sustentable). Uso: python3 fontes/rias-que-traballan/render.py
"""
import re
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
modelo = (RAIZ / "v" / "galicia-cero-neto" / "index.html").read_text(encoding="utf-8")
bar = re.search(r'<header class="dv-bar">.*?</header>', modelo, re.S).group(0)
foot = re.search(r'<footer class="dv-foot">.*?</footer>', modelo, re.S).group(0)
assert "CC BY-NC-SA 4.0" in foot
foot = foot.replace("CC BY-NC-SA 4.0",
                    "CC BY-SA 4.0 · Datos: Augas de Galicia e Consellería do Mar (Xunta de Galicia), "
                    "Mapas Galicia Sustentable · Relevo: © Instituto Geográfico Nacional, MDT (PNOA-LiDAR), CC BY 4.0")
out = (AQUI / "peza.tpl.html").read_text(encoding="utf-8").replace("{{BAR}}", bar).replace("{{FOOT}}", foot)
dest = RAIZ / "v" / "rias-que-traballan" / "index.html"
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(out, encoding="utf-8")
print(dest)

# datos.json: as paradas tal como están no HTML (lugar, cámara, capas, cifra, fonte)
import html
import json


def limpa(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


paradas = []
for m in re.finditer(r'<section class="paso[^"]*"(.*?)>(.*?)</section>', out, re.S):
    attrs = dict(re.findall(r'data-([a-z]+)="([^"]*)"', m.group(1)))
    corpo = m.group(2)
    g = lambda pat: (re.search(pat, corpo, re.S) or [None, None])[1]
    paradas.append({
        "onde": limpa(g(r'<p class="onde">(.*?)</p>')),
        "titulo": limpa(g(r"<h[12]>(.*?)</h[12]>")),
        "camara": {k: attrs.get(k) for k in ("centro", "zoom", "inclinacion", "rumbo")},
        "capas": attrs.get("capa"),
        "marcas": attrs.get("marca"),
        "cifra": limpa(g(r'<p class="dato">(.*?)</p>')),
        "cifra_texto": limpa(g(r'<p class="dato-l">(.*?)</p>')),
        "fonte": limpa(g(r'<p class="fonte">(.*?)</p>')),
    })
(AQUI / "datos.json").write_text(json.dumps({"slug": "rias-que-traballan", "paradas": paradas},
                                            ensure_ascii=False, indent=1), encoding="utf-8")
print(AQUI / "datos.json", len(paradas), "paradas")

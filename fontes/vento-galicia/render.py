#!/usr/bin/env python3
"""Xera v/vento-galicia/index.html a partir de peza.tpl.html.

Copia a barra .dv-bar e o pé .dv-foot de v/galicia-cero-neto/ para que coincidan
co resto de Divulga e engade ao pé as atribucións dos datos. Uso: python3 render.py
"""
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
    "CC BY-NC-SA 4.0 · Aeroxeradores: © colaboradores de OpenStreetMap, ODbL · "
    "Vento: Global Wind Atlas 3 (DTU), CC BY 4.0 · Rede Natura: MITECO · "
    "ZAPER: MITECO/EMODnet, CC BY 4.0 · Relevo: © Instituto Geográfico Nacional, MDT (PNOA-LiDAR), CC BY 4.0",
    1)
out = (AQUI / "peza.tpl.html").read_text(encoding="utf-8").replace("{{BAR}}", bar).replace("{{FOOT}}", foot)
dest = RAIZ / "v" / "vento-galicia" / "index.html"
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(out, encoding="utf-8")
print(dest)

# datos.json: as paradas tal como van no HTML (sincronizado en cada render)
import html as _h
import json


def _txt(s):
    return _h.unescape(re.sub(r"<[^>]+>", "", s)).strip() if s else None


paradas = []
for m in re.finditer(r'<section class="paso"(.*?)>(.*?)</section>', out, re.S):
    at = dict(re.findall(r'data-([a-z]+)="([^"]*)"', m.group(1)))
    corpo = m.group(2)
    g = lambda pat: (re.search(pat, corpo, re.S) or [None, None])[1]
    paradas.append({
        "nome": _txt(g(r"<h[12][^>]*>(.*?)</h[12]>")),
        "onde": _txt(g(r'<p class="onde">(.*?)</p>')),
        "camara": {"centro": [float(x) for x in at["centro"].split(",")], "zoom": float(at["zoom"]),
                   "inclinacion": float(at.get("inclinacion", 55)), "rumbo": float(at.get("rumbo", 0))},
        "capas": [c for c in at.get("capa", "").split(",") if c],
        "marcas": [x.split("|")[1] for x in at.get("marca", "").split(";") if "|" in x],
        "dato": _txt(g(r'<p class="dato">(.*?)</p>')),
        "dato_l": _txt(g(r'<p class="dato-l">(.*?)</p>')),
        "fonte": _txt(g(r'<p class="fonte">(.*?)</p>')),
    })
(AQUI / "datos.json").write_text(json.dumps({"slug": "vento-galicia", "paradas": paradas,
                                             "cifras_calculadas": json.loads((AQUI / "data" / "cifras.json").read_text())},
                                            ensure_ascii=False, indent=1), encoding="utf-8")
print(AQUI / "datos.json", len(paradas), "paradas")

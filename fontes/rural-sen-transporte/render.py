#!/usr/bin/env python3
"""Xera v/rural-sen-transporte/index.html a partir de peza.tpl.html.

Copia a barra .dv-bar e o pé .dv-foot de v/galicia-cero-neto/ para que
coincidan co resto de Divulga e cambia a licenza do pé a CC BY-SA 4.0 (a peza
usa capas CC BY-SA de Mapas Galicia Sustentable). Uso: python3 render.py
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
    "CC BY-SA 4.0 · Buses: Xunta de Galicia vía NAP (MITRAMS), Powered by MITRAMS · "
    "Trens: Renfe Operadora, CC BY 4.0 · Lugares, límites e distancias: IET e SERGAS, "
    "cálculo FGS (CC BY-SA 4.0) · Relevo: © Instituto Geográfico Nacional, MDT (PNOA-LiDAR), CC BY 4.0")
out = (AQUI / "peza.tpl.html").read_text(encoding="utf-8").replace("{{BAR}}", bar).replace("{{FOOT}}", foot)
dest = RAIZ / "v" / "rural-sen-transporte" / "index.html"
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(out, encoding="utf-8")
print(dest)


# datos.json: as paradas tal como están no HTML (sincronizado en cada render)
def texto(x):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", x))).strip() if x else None


paradas = []
for attrs, corpo in re.findall(r'<section class="paso"([^>]*)>(.*?)</section>', out, re.S):
    a = dict(re.findall(r'data-([a-z]+)="([^"]*)"', attrs))
    campo = lambda pat: (m.group(1) if (m := re.search(pat, corpo, re.S)) else None)
    paradas.append({
        "onde": texto(campo(r'<p class="onde">(.*?)</p>')),
        "titulo": texto(campo(r"<h[12]>(.*?)</h[12]>")),
        "camara": {"centro": [float(v) for v in a["centro"].split(",")], "zoom": float(a["zoom"]),
                   "inclinacion": float(a.get("inclinacion", 55)), "rumbo": float(a.get("rumbo", 0))},
        "capas": a.get("capa", "").split(",") if a.get("capa") else [],
        "marcas": [m.split("|")[1] for m in a.get("marca", "").split(";") if "|" in m],
        "dato": texto(campo(r'<p class="dato">(.*?)</p>')),
        "dato_l": texto(campo(r'<p class="dato-l">(.*?)</p>')),
        "texto": [texto(t) for t in re.findall(r"<p>(.*?)</p>", corpo, re.S)],
        "fonte": texto(campo(r'<p class="fonte">(.*?)</p>')),
    })
(AQUI / "datos.json").write_text(json.dumps({"slug": "rural-sen-transporte", "dia_laborable": "2026-11-04",
                                             "dia_domingo": "2026-11-08", "paradas": paradas},
                                            ensure_ascii=False, indent=1), encoding="utf-8")
print(AQUI / "datos.json", len(paradas), "paradas")

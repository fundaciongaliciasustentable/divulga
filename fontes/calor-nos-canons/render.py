#!/usr/bin/env python3
"""Xera v/calor-nos-canons/index.html a partir de peza.tpl.html.

Copia a barra .dv-bar e o pé .dv-foot de v/galicia-cero-neto/ para que
coincidan co resto de Divulga, e cambia a licenza a CC BY-SA 4.0 (a capa
tmax-ano de Mapas Galicia Sustentable é da colección CC BY-SA 4.0).
Tamén escribe datos.json coas paradas (cámara, capas, cifras e fonte),
sacadas do propio modelo para que estean sempre sincronizadas co HTML.
Uso: python3 render.py
"""
import json
import re
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
modelo = (RAIZ / "v" / "galicia-cero-neto" / "index.html").read_text(encoding="utf-8")
bar = re.search(r'<header class="dv-bar">.*?</header>', modelo, re.S).group(0)
foot = re.search(r'<footer class="dv-foot">.*?</footer>', modelo, re.S).group(0)
foot = foot.replace(
    "CC BY-NC-SA 4.0",
    "CC BY-SA 4.0 · Temperaturas: MeteoGalicia e Consellería de Medio Ambiente e Cambio Climático"
    " · Lumes: Copernicus EFFIS, CC BY 4.0"
    " · Relevo: © Instituto Geográfico Nacional, MDT (PNOA-LiDAR), CC BY 4.0")
out = (AQUI / "peza.tpl.html").read_text(encoding="utf-8").replace("{{BAR}}", bar).replace("{{FOOT}}", foot)
dest = RAIZ / "v" / "calor-nos-canons" / "index.html"
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(out, encoding="utf-8")
print(dest)


def texto(m):
    return re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else None


tpl = (AQUI / "peza.tpl.html").read_text(encoding="utf-8")
paradas = []
for i, (attrs, corpo) in enumerate(re.findall(r'<section class="paso[^"]*"(.*?)>(.*?)</section>', tpl, re.S)):
    a = dict(re.findall(r'data-([a-z]+)="([^"]*)"', attrs))
    paradas.append({
        "paso": i,
        "nome": texto(re.search(r"<h[12]>(.*?)</h[12]>", corpo, re.S)),
        "onde": texto(re.search(r'<p class="onde">(.*?)</p>', corpo, re.S)),
        "camara": {"centro": [float(x) for x in a["centro"].split(",")], "zoom": float(a["zoom"]),
                   "inclinacion": float(a["inclinacion"]), "rumbo": float(a["rumbo"])},
        "capas": [c for c in a.get("capa", "").split(",") if c]
                 + (["superficie (calor-xja.png)"] if a.get("superficie") == "1" else []),
        "marcas": [m.split("|")[1] for m in a.get("marca", "").split(";") if m],
        "dato": texto(re.search(r'<p class="dato">(.*?)</p>', corpo, re.S)),
        "dato_l": texto(re.search(r'<p class="dato-l">(.*?)</p>', corpo, re.S)),
        "fonte": texto(re.search(r'<p class="fonte">(.*?)</p>', corpo, re.S)),
    })
(AQUI / "datos.json").write_text(json.dumps({"slug": "calor-nos-canons", "consulta": "2026-11-04",
                                             "paradas": paradas}, ensure_ascii=False, indent=1), encoding="utf-8")

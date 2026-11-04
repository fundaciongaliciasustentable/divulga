#!/usr/bin/env python3
"""Xera v/veran-que-ardeu/index.html a partir de peza.tpl.html.

Copia a barra .dv-bar e o pé .dv-foot de v/galicia-cero-neto/ e enche a serie
anual coas cifras de data/calculos.json (saen de prep.py). Uso: python3 render.py
"""
import json
import re
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
modelo = (RAIZ / "v" / "galicia-cero-neto" / "index.html").read_text(encoding="utf-8")
bar = re.search(r'<header class="dv-bar">.*?</header>', modelo, re.S).group(0)
foot = re.search(r'<footer class="dv-foot">.*?</footer>', modelo, re.S).group(0)
# Usa a capa focos-tempada-2025 de Mapas Galicia Sustentable, CC BY-SA 4.0: a peza herda a licenza
foot = foot.replace("CC BY-NC-SA 4.0",
                    "CC BY-SA 4.0 · Focos: NASA FIRMS vía Mapas Galicia Sustentable · "
                    "Áreas queimadas: © UE, Copernicus EFFIS, CC BY 4.0 · "
                    "Relevo: © Instituto Geográfico Nacional, MDT (PNOA-LiDAR), CC BY 4.0")


def miles(n):
    return f"{n:,}".replace(",", ".")


calc = json.loads((AQUI / "data" / "calculos.json").read_text(encoding="utf-8"))
anos = calc["effis_ha_en_galicia_por_ano"]
maximo = max(anos.values())
serie = "".join(
    f'<span>{a}</span><span{" class=\"m\"" if a == "2025" else ""} style="width:{100 * v / maximo:.1f}%"></span>'
    f'<span>{"<b>" + miles(v) + "</b>" if a == "2025" else miles(v)}</span>'
    for a, v in anos.items())

out = ((AQUI / "peza.tpl.html").read_text(encoding="utf-8")
       .replace("{{BAR}}", bar).replace("{{FOOT}}", foot).replace("{{SERIE}}", serie))
dest = RAIZ / "v" / "veran-que-ardeu" / "index.html"
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(out, encoding="utf-8")
print(dest)

#!/usr/bin/env python3
"""Xera v/costa-morte-courel/index.html a partir de peza.tpl.html.

Copia a barra .dv-bar e o pé .dv-foot dunha peza existente para que
coincidan co resto de Divulga. Uso: python3 render.py
"""
import re
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
modelo = (RAIZ / "v" / "galicia-cero-neto" / "index.html").read_text(encoding="utf-8")
bar = re.search(r'<header class="dv-bar">.*?</header>', modelo, re.S).group(0)
foot = re.search(r'<footer class="dv-foot">.*?</footer>', modelo, re.S).group(0)
foot = foot.replace("CC BY-NC-SA 4.0",
                    "CC BY-NC-SA 4.0 · Relevo: © Instituto Geográfico Nacional, MDT (PNOA-LiDAR), CC BY 4.0")
out = (AQUI / "peza.tpl.html").read_text(encoding="utf-8").replace("{{BAR}}", bar).replace("{{FOOT}}", foot)
dest = RAIZ / "v" / "costa-morte-courel" / "index.html"
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(out, encoding="utf-8")
print(dest)

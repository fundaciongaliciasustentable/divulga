#!/usr/bin/env python3
"""Escribe datos.json: as paradas (nome, cámara, capas, cifras e fonte) lidas do
propio peza.tpl.html, para ter unha copia lexible e sincronizada. Uso: python3 datos.py"""
import html
import json
import re
from pathlib import Path

AQUI = Path(__file__).resolve().parent
tpl = (AQUI / "peza.tpl.html").read_text(encoding="utf-8")
txt = lambda s: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()
paradas = []
for i, m in enumerate(re.finditer(r'<section class="paso"([^>]*)>(.*?)</section>', tpl, re.S)):
    at = dict(re.findall(r'data-([a-z]+)="([^"]*)"', m.group(1)))
    corpo = m.group(2)
    g = lambda pat: (re.search(pat, corpo, re.S) or [None, None])[1]
    paradas.append({
        "paso": i,
        "onde": txt(g(r'<p class="onde">(.*?)</p>')),
        "titulo": txt(g(r"<h[12]>(.*?)</h[12]>")),
        "camara": {"centro": [float(v) for v in at["centro"].split(",")], "zoom": float(at["zoom"]),
                   "inclinacion": float(at.get("inclinacion", 55)), "rumbo": float(at.get("rumbo", 0))},
        "capas": [c for c in at.get("capa", "").split(",") if c],
        "marcas": [s.split("|")[1] for s in at.get("marca", "").split(";") if "|" in s],
        "dato": txt(g(r'<p class="dato">(.*?)</p>')) or None,
        "dato_l": txt(g(r'<p class="dato-l">(.*?)</p>')) or None,
        "fonte": txt(g(r'<p class="fonte">(.*?)</p>')),
    })
calc = json.loads((AQUI / "data" / "calculos.json").read_text(encoding="utf-8"))
(AQUI / "datos.json").write_text(json.dumps({"paradas": paradas, "calculos_fgs": calc}, ensure_ascii=False, indent=1),
                                 encoding="utf-8")
print(len(paradas), "paradas")

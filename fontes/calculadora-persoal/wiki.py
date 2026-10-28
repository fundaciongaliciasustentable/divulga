#!/usr/bin/env python3
"""Acontecementos de cada ano, 1930-2025, da Galipedia e da Wikipedia en castelán → data/raw/wiki_*.json

Galipedia, artigo «AAAA»: os puntos de «Acontecementos» (Galicia e mundo) e quen foi homenaxeado
no Día das Letras Galegas (do artigo «Día das Letras Galegas»). Wikipedia en castelán, artigo «AAAA»: os acontecementos de España (a
Galipedia case non os trae). Cada páxina gárdase en data/raw/ e só se descarga se falta; prep.py
le estes ficheiros. As frases quedan tal como están na Wikipedia, coa ligazón ao artigo.
"""
import json
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

RAW = Path(__file__).resolve().parent / "data" / "raw"
UA = {"User-Agent": "DivulgaFGS/1.0 (https://divulga.galiciasustentable.org)"}
RAW.mkdir(parents=True, exist_ok=True)
# a táboa de homenaxeados do Día das Letras Galegas, nun só artigo
f = RAW / "wiki_gl_letras.json"
if not f.exists():
    f.write_bytes(urlopen(Request("https://gl.wikipedia.org/w/api.php?" + urlencode({"action": "parse", "page": "Día das Letras Galegas", "prop": "text",
                                                                                    "format": "json"}), headers=UA), timeout=60).read())
for ano in range(1930, 2026):
    for w in ("gl", "es"):
        f = RAW / f"wiki_{w}_{ano}.json"
        if f.exists():
            continue
        url = f"https://{w}.wikipedia.org/w/api.php?" + urlencode({"action": "parse", "page": str(ano), "prop": "text|revid", "format": "json",
                                                                 "redirects": 1})
        for intento in range(4):
            try:
                f.write_bytes(urlopen(Request(url, headers=UA), timeout=60).read())
                break
            except Exception as e:
                print("reintento", w, ano, e, flush=True)
                time.sleep(5 * (intento + 1))
        time.sleep(0.3)
    if ano % 10 == 0:
        print(ano, flush=True)
print("ok")

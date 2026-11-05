#!/usr/bin/env python3
"""Xera v/costa-morte-courel/index.html a partir de peza.tpl.html, e fontes/costa-morte-courel/datos.json.

Copia a barra .dv-bar e o pé .dv-foot dunha peza existente para que coincidan co resto de
Divulga, cambia a licenza do pé a CC BY-SA 4.0 (a peza usa capas CC BY-SA de Mapas Galicia
Sustentable: aldeas-baleiras, concellos-parroquias e espazos-naturais-galicia, do IET) e
extrae as paradas do HTML a datos.json para que estean sempre sincronizadas.
Uso: python3 render.py
"""
import html
import json
import re
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
SLUG = "costa-morte-courel"
modelo = (RAIZ / "v" / "galicia-cero-neto" / "index.html").read_text(encoding="utf-8")
bar = re.search(r'<header class="dv-bar">.*?</header>', modelo, re.S).group(0)
foot = re.search(r'<footer class="dv-foot">.*?</footer>', modelo, re.S).group(0)
foot = foot.replace(
    "CC BY-NC-SA 4.0",
    "CC BY-SA 4.0 · Relevo: © IGN, MDT (PNOA-LiDAR), CC BY 4.0 · Datos: MeteoGalicia, Augas de Galicia, "
    "INE, IGE, © IET (Xunta de Galicia), © UE Copernicus EFFIS")
tpl = (AQUI / "peza.tpl.html").read_text(encoding="utf-8")
out = tpl.replace("{{BAR}}", bar).replace("{{FOOT}}", foot)
dest = RAIZ / "v" / SLUG / "index.html"
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(out, encoding="utf-8")
print(dest)


# ── datos.json: as paradas tal como están no HTML ───────────────────────────
def texto(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def campo(cls, corpo):
    m = re.search(rf'<p class="{cls}">(.*?)</p>', corpo, re.S)
    return texto(m.group(1)) if m else None


paradas = []
for attrs, corpo in re.findall(r'<section class="paso[^"]*"(.*?)>(.*?)</section>', tpl, re.S):
    d = dict(re.findall(r'data-([a-z]+)="([^"]*)"', attrs))
    tit = re.search(r"<h[12]>(.*?)</h[12]>", corpo, re.S)
    paradas.append({
        "nome": texto(tit.group(1)) if tit else None,
        "onde": campo("onde", corpo),
        "camara": {"centro": [float(x) for x in d["centro"].split(",")], "zoom": float(d["zoom"]),
                   "inclinacion": float(d.get("inclinacion", 55)), "rumbo": float(d.get("rumbo", 0))},
        "capa": d.get("capa"),
        "marcas": [m.split("|")[1] for m in d.get("marca", "").split(";") if "|" in m],
        "dato": campo("dato", corpo),
        "dato_l": campo("dato-l", corpo),
        "fonte": campo("fonte", corpo),
    })
cifras = json.loads((AQUI / "cifras.json").read_text(encoding="utf-8")) if (AQUI / "cifras.json").exists() else {}
(AQUI / "datos.json").write_text(json.dumps({"slug": SLUG, "consulta": cifras.get("consulta"), "paradas": paradas},
                                            ensure_ascii=False, indent=1), encoding="utf-8")
pasos = tpl.split('<div class="voo-pasos">')[1].split('<section class="voo-fontes">')[0]
PAL = re.compile(r'[^\W\d_]+')
print(f"{len(paradas)} pasos, {len(PAL.findall(texto(pasos)))} palabras nos pasos")

# capa da ruta (as once paradas unidas) para o título e o peche
pts = [p["camara"]["centro"] for p in paradas[1:-1]]
ruta = {"type": "FeatureCollection", "features": [
    {"type": "Feature", "geometry": {"type": "LineString", "coordinates": pts}, "properties": {}},
    *({"type": "Feature", "geometry": {"type": "Point", "coordinates": c}, "properties": {"n": i + 1}}
      for i, c in enumerate(pts))]}
(RAIZ / "v" / SLUG / "capas" / "ruta.geojson").write_text(json.dumps(ruta, separators=(",", ":")), encoding="utf-8")

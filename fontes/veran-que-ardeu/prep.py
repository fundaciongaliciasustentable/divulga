#!/usr/bin/env python3
"""Prepara as capas e as cifras calculadas de «O verán que ardeu».

Entradas (copias do día de Mapas Galicia Sustentable, en data/raw/; se faltan,
cópianse de ~/Proxectos/mapasgs/site/public/data/ ou descárganse de
https://mapas.galiciasustentable.org/data/<capa>/data.geojson):
  - focos-tempada-2025  focos de calor de satélite (NASA FIRMS), CC BY-SA 4.0
  - historial-queimados áreas queimadas por ano desde 2016 (Copernicus EFFIS), CC BY 4.0
Tamén usa o contorno de Galicia (assets/terreo/galicia-contorno.geojson) e o MDT
de 25 m (fontes/terreo/data/raw/*.tif) para as alturas.

Saídas:
  ../../v/veran-que-ardeu/capas/focos.geojson   focos de agosto en celas de ~500 m, un MultiPoint por día
  ../../v/veran-que-ardeu/capas/lumes.geojson   perímetros EFFIS de 2025 (≥ 100 ha)
  ../../v/veran-que-ardeu/capas/anos.geojson    perímetros EFFIS 2016-2024 (≥ 50 ha)
  data/calculos.json                            cifras calculadas (cálculo FGS)

Uso (precisa shapely, numpy e tifffile):
    python3 -I prep.py
"""
import json
import math
import shutil
import urllib.request
from collections import Counter
from pathlib import Path

import numpy as np
import tifffile
from shapely.geometry import mapping, shape, Point
from shapely.ops import polygonize, unary_union

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
RAW = AQUI / "data" / "raw"
SAIDA = RAIZ / "v" / "veran-que-ardeu" / "capas"
MAPAS_LOCAL = Path.home() / "Proxectos" / "mapasgs" / "site" / "public" / "data"
MAPAS_URL = "https://mapas.galiciasustentable.org/data/{}/data.geojson"
MDT = RAIZ / "fontes" / "terreo" / "data" / "raw"
CELA = 0.005   # grao (~ 400 × 550 m)


def capa(nome):
    dest = RAW / f"{nome}.geojson"
    if not dest.exists():
        RAW.mkdir(parents=True, exist_ok=True)
        local = MAPAS_LOCAL / nome / "data.geojson"
        if local.exists():
            shutil.copy(local, dest)
            shutil.copy(local.parent / "meta.json", RAW / f"{nome}.meta.json")
        else:
            urllib.request.urlretrieve(MAPAS_URL.format(nome), dest)
    return json.loads(dest.read_text(encoding="utf-8"))


def redondear(g, n=4):
    if isinstance(g, (list, tuple)):
        if g and isinstance(g[0], (int, float)):
            return [round(g[0], n), round(g[1], n)]
        return [redondear(x, n) for x in g]
    return g


def geo(geom, n=4):
    m = mapping(geom)
    return {"type": m["type"], "coordinates": redondear(m["coordinates"], n)}


def ha(geom):
    """Área en hectáreas cunha proxección equirrectangular local (erro < 0,5 % en Galicia)."""
    if geom.is_empty:
        return 0.0
    lat0 = geom.centroid.y
    kx = 111320 * math.cos(math.radians(lat0))
    ky = 110574
    from shapely.affinity import scale
    return scale(geom, kx, ky, origin=(0, 0)).area / 1e4


def gardar(nome, feats):
    SAIDA.mkdir(parents=True, exist_ok=True)
    txt = json.dumps({"type": "FeatureCollection", "features": feats},
                     ensure_ascii=False, separators=(",", ":"))
    (SAIDA / nome).write_text(txt, encoding="utf-8")
    print(f"{nome}: {len(feats)} entidades, {len(txt) / 1024:.0f} KB")


def mosaico_mdt():
    pezas = []
    for f in sorted(MDT.glob("mdt25_*.tif")):
        with tifffile.TiffFile(f) as t:
            p = t.pages[0]
            sx, sy, _ = p.tags["ModelPixelScaleTag"].value
            _, _, _, x0, y0, _ = p.tags["ModelTiepointTag"].value
            pezas.append((x0, y0, sx, p.asarray()))
    paso = pezas[0][2]
    oeste = min(p[0] for p in pezas)
    norte = max(p[1] for p in pezas)
    ancho = max(round((p[0] - oeste) / paso) + p[3].shape[1] for p in pezas)
    alto = max(round((norte - p[1]) / paso) + p[3].shape[0] for p in pezas)
    m = np.zeros((alto, ancho), dtype=np.int16)
    for x0, y0, _, a in pezas:
        c, f = round((x0 - oeste) / paso), round((norte - y0) / paso)
        m[f:f + a.shape[0], c:c + a.shape[1]] = a
    return m, oeste, norte, paso


def alturas(geom, mdt):
    """Altura mínima e máxima do MDT dentro dun polígono (mostra cada 4 píxeles, ~100 m)."""
    m, oeste, norte, paso = mdt
    x0, y0, x1, y1 = geom.bounds
    c0, c1 = int((x0 - oeste) / paso), int((x1 - oeste) / paso)
    f0, f1 = int((norte - y1) / paso), int((norte - y0) / paso)
    from shapely import contains_xy
    cols = np.arange(c0, c1, 4)
    filas = np.arange(f0, f1, 4)
    cc, ff = np.meshgrid(cols, filas)
    lon = oeste + (cc + 0.5) * paso
    lat = norte - (ff + 0.5) * paso
    dentro = contains_xy(geom, lon, lat)
    v = m[ff[dentro], cc[dentro]]
    lo, la = lon[dentro], lat[dentro]
    ok = v > 0
    v, lo, la = v[ok], lo[ok], la[ok]
    i, j = int(v.argmin()), int(v.argmax())
    return (int(v[i]), [round(float(lo[i]), 4), round(float(la[i]), 4)],
            int(v[j]), [round(float(lo[j]), 4), round(float(la[j]), 4)])


def main():
    contorno = json.loads((RAIZ / "assets" / "terreo" / "galicia-contorno.geojson").read_text())
    linas = unary_union([shape(f["geometry"]) for f in contorno["features"]])
    galicia = unary_union(list(polygonize(linas)))
    print(f"Galicia: {ha(galicia) / 100:.0f} km² (contorno IGN)")
    calc = {}

    # 1. Focos de calor de agosto (FIRMS) -----------------------------------
    focos = capa("focos-tempada-2025")["features"]
    tempada = len(focos)
    ago = [f for f in focos if f["properties"]["instante"].startswith("2025-08")]
    our = sum(1 for f in ago if str(f["properties"]["codigo_ine"]).startswith("32"))
    dias = Counter(int(f["properties"]["instante"][8:10]) for f in ago)
    pico = sum(dias[d] for d in range(13, 18))
    calc["focos"] = {
        "tempada_xuno_outubro": tempada, "agosto": len(ago), "agosto_ourense": our,
        "pct_agosto_tempada": round(100 * len(ago) / tempada, 1),
        "pct_ourense_agosto": round(100 * our / len(ago), 1),
        "dias_13_17": pico, "pct_dias_13_17": round(100 * pico / len(ago), 1),
        "dia_maximo": max(dias, key=dias.get), "focos_dia_maximo": max(dias.values()),
        "por_dia": {str(d): dias[d] for d in sorted(dias)},
        "por_produto": dict(Counter(f["properties"]["produto"] for f in ago)),
    }
    celas = {}
    for f in ago:
        lon, lat = f["geometry"]["coordinates"]
        k = (math.floor(lon / CELA), math.floor(lat / CELA))
        d = int(f["properties"]["instante"][8:10])
        c = celas.setdefault(k, {"d": d, "n": 0})
        c["d"] = min(c["d"], d)
        c["n"] += 1
    # un MultiPoint por día: cada cela de ~500 m co día no que o satélite a viu arder por primeira vez
    por_dia = {}
    for k, c in sorted(celas.items()):
        por_dia.setdefault(c["d"], []).append([round((k[0] + .5) * CELA, 3), round((k[1] + .5) * CELA, 3)])
    feats = [{"type": "Feature", "properties": {"d": d},
              "geometry": {"type": "MultiPoint", "coordinates": pts}} for d, pts in sorted(por_dia.items())]
    calc["focos"]["celas_500m"] = len(celas)
    gardar("focos.geojson", feats)

    # 2. Perímetros EFFIS ----------------------------------------------------
    hist = capa("historial-queimados")["features"]
    por_ano = Counter()
    lumes, anos = [], []
    mdt = mosaico_mdt()
    grandes = {}
    for f in hist:
        p = f["properties"]
        g = shape(f["geometry"]).buffer(0)
        dentro = g.intersection(galicia)
        por_ano[p["ano"]] += ha(dentro)
        if p["ano"] == 2025 and p["area_ha"] >= 100:
            s = g.simplify(0.0006, preserve_topology=True)
            lumes.append({"type": "Feature", "properties": {"id": p["id"], "data": p["data_lume"], "ha": p["area_ha"]},
                          "geometry": geo(s)})
            if p["area_ha"] >= 10000:
                mn, pmn, mx, pmx = alturas(dentro, mdt)
                c = dentro.representative_point()
                grandes[p["id"]] = {"data": p["data_lume"], "concello_effis": p["concello"],
                                    "ha_effis": p["area_ha"], "ha_effis_en_galicia": round(ha(dentro)),
                                    "altura_min": mn, "punto_min": pmn, "altura_max": mx, "punto_max": pmx,
                                    "punto": [round(c.x, 4), round(c.y, 4)]}
        elif p["ano"] < 2025 and p["area_ha"] >= 50:
            s = g.simplify(0.0012, preserve_topology=True)
            anos.append({"type": "Feature", "properties": {"ano": p["ano"]}, "geometry": geo(s, 3)})
    gardar("lumes.geojson", lumes)
    gardar("anos.geojson", anos)
    calc["effis_ha_en_galicia_por_ano"] = {str(a): round(por_ano[a]) for a in sorted(por_ano)}
    previos = [por_ano[a] for a in range(2016, 2025)]
    calc["effis_2016_2024_suma"] = round(sum(previos))
    calc["effis_2025_vs_suma_previa"] = round(por_ano[2025] / sum(previos), 2)
    calc["grandes_effis_2025"] = grandes
    (AQUI / "data").mkdir(exist_ok=True)
    (AQUI / "data" / "calculos.json").write_text(json.dumps(calc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(calc, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""O vento que move Galicia → v/vento-galicia/capas/*.geojson e data/cifras.json

Fontes (todo en data/raw/, descárgase se falta, agás o MDT, que é de fontes/terreo/):
  · OpenStreetMap (Overpass), aeroxeradores (generator:source=wind) e parques
    (power=plant + plant:source=wind) en Galicia. ODbL.
  · Global Wind Atlas 3 (DTU / Banco Mundial), velocidade media do vento a 100 m,
    GeoTIFF de España (country_tifs_v4). CC BY 4.0.
  · Rede Natura 2000 (MITECO, Banco de Datos de la Naturaleza), copia publicada en
    mapas.galiciasustentable.org/data/rede-natura/ (edición 2024).
  · Zonas de alto potencial para a eólica mariña (ZAPER) do POEM (RD 150/2023), vía
    EMODnet Human Activities (capa mspzoningpoly), CC BY 4.0.
  · MDT de 25 m do IGN (fontes/terreo/data/raw/*.tif) para as alturas.
  · Contorno de Galicia: assets/terreo/galicia-contorno.geojson (IGN).

Uso: python -I prep.py  (con numpy, tifffile, imagecodecs e shapely)
"""
import json
import math
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import tifffile
from shapely import contains_xy, make_valid
from shapely.geometry import MultiPolygon, Point, mapping, shape
from shapely.ops import polygonize, unary_union
from shapely.prepared import prep

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
RAW = AQUI / "data" / "raw"
CAPAS = RAIZ / "v" / "vento-galicia" / "capas"
MDT = RAIZ / "fontes" / "terreo" / "data" / "raw"
UA = {"User-Agent": "DivulgaFGS/1.0 (https://divulga.galiciasustentable.org)"}
RAW.mkdir(parents=True, exist_ok=True)
CAPAS.mkdir(parents=True, exist_ok=True)

OVERPASS = "https://overpass-api.de/api/interpreter"
Q_AERO = ('[out:json][timeout:240];area["ISO3166-2"="ES-GA"]->.g;'
          'node["generator:source"="wind"](area.g);out body;')
Q_PARQUES = ('[out:json][timeout:240];area["ISO3166-2"="ES-GA"]->.g;'
             'nwr["power"="plant"]["plant:source"="wind"](area.g);out center tags;')
GWA = "https://gwa.cdn.nazkamapps.com/country_tifs_v4/ESP_wind-speed_100m.tif"
RN = "https://mapas.galiciasustentable.org/data/rede-natura/data.geojson"
EMODNET = ("https://ows.emodnet-humanactivities.eu/wfs?service=WFS&version=2.0.0&request=GetFeature"
           "&typeNames=emodnet:mspzoningpoly&outputFormat=application/json&srsName=EPSG:4326"
           "&bbox=41.5,-10.5,44.5,-5.5,urn:ogc:def:crs:EPSG::4326")

# Recadros das paradas (lon_min, lat_min, lon_max, lat_max): contan os aeroxeradores e
# a altura máxima. Decláranse tal cal no README.
ZONAS = {
    "costa_morte": (-9.25, 43.03, -8.80, 43.33),   # Camariñas, Vimianzo, Zas, Laxe, Ponteceso, Malpica
    "paxareiras": (-9.20, 42.80, -8.80, 43.02),    # Mazaricos, Dumbría, Cee, Carnota, Outes, Muros
    "xistral": (-7.80, 43.40, -7.38, 43.58),       # Abadín, Muras, Xermade, Ourol, Alfoz, Valadouro
    "faladoira": (-8.00, 43.56, -7.73, 43.73),     # A Capelada, Faladoira, Coto Teixido (Cedeira a Mañón)
    "testeiro": (-8.30, 42.48, -8.00, 42.62),      # Montes do Testeiro (Lalín, Silleda, Dozón, Rodeiro)
    "suido": (-8.40, 42.24, -8.20, 42.40),         # Serra do Suído (Avión, Covelo, A Lama, Fornelos)
    "somozas": (-7.95, 43.50, -7.84, 43.56),       # As Somozas
}


def baixa(nome, url, data=None, binario=False):
    f = RAW / nome
    if not f.exists():
        print("descargando", nome)
        req = Request(url, data=urlencode(data).encode() if data else None, headers=UA)
        f.write_bytes(urlopen(req, timeout=600).read())
    return f if binario else json.loads(f.read_text(encoding="utf-8"))


def r(x, n=4):
    return round(x, n)


def geo(feats):
    return {"type": "FeatureCollection", "features": feats}


def garda(nome, fc):
    f = CAPAS / nome
    f.write_text(json.dumps(fc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{nome}: {len(fc['features'])} elementos, {f.stat().st_size / 1024:.0f} KB")


def redondea(g, n=4):
    if isinstance(g, (list, tuple)):
        if g and isinstance(g[0], (int, float)):
            return [round(g[0], n), round(g[1], n)]
        return [redondea(x, n) for x in g]
    return g


# --- contorno de Galicia (liñas → polígono)
cont = json.loads((RAIZ / "assets/terreo/galicia-contorno.geojson").read_text())
liñas = unary_union([shape(f["geometry"]) for f in cont["features"]])
galicia = unary_union(list(polygonize(liñas)))
gal_p = prep(galicia)
print(f"Galicia (contorno): {galicia.area:.3f} grao²")

# --- MDT 25 m (teselas de 0,5° desde lat x,25/x,75; nome = esquina SO; píxel 0,5/2220)
_mdt = {}


def tesela(lat0, lon0):
    k = (lat0, lon0)
    if k not in _mdt:
        f = MDT / f"mdt25_{lat0:+.2f}_{lon0:+.2f}.tif"
        _mdt[k] = tifffile.imread(f) if f.exists() else None
    return _mdt[k]


def altura(lon, lat):
    lat0 = math.floor((lat - 0.25) * 2) / 2 + 0.25   # as teselas empezan en x,25 / x,75
    lon0 = math.floor(lon * 2) / 2
    a = tesela(lat0, lon0)
    if a is None:
        return None
    n = a.shape[0]
    fil = min(n - 1, int((lat0 + 0.5 - lat) / 0.5 * n))
    col = min(n - 1, int((lon - lon0) / 0.5 * n))
    return int(a[fil, col])


def altura_max(caixa):
    x0, y0, x1, y1 = caixa
    mx, onde = -1, None
    for lat0 in np.arange(math.floor((y0 - 0.25) * 2) / 2 + 0.25, y1, 0.5):
        for lon0 in np.arange(math.floor(x0 * 2) / 2, x1, 0.5):
            a = tesela(float(lat0), float(lon0))
            if a is None:
                continue
            n = a.shape[0]
            f0 = max(0, int((lat0 + 0.5 - y1) / 0.5 * n)); f1 = min(n, int((lat0 + 0.5 - y0) / 0.5 * n))
            c0 = max(0, int((x0 - lon0) / 0.5 * n)); c1 = min(n, int((x1 - lon0) / 0.5 * n))
            if f1 <= f0 or c1 <= c0:
                continue
            sub = a[f0:f1, c0:c1]
            i = int(sub.argmax())
            if sub.flat[i] > mx:
                ff, cc = divmod(i, sub.shape[1])
                mx = int(sub.flat[i])
                onde = (r(lon0 + (c0 + cc + .5) / n * 0.5), r(lat0 + 0.5 - (f0 + ff + .5) / n * 0.5))
    return mx, onde


# altura media de Galicia: mostraxe cada 8 píxeles (200 m) dentro do contorno
mostras = []
for f in sorted(MDT.glob("mdt25_*.tif")):
    _, la, lo = f.stem.split("_")
    la, lo = float(la), float(lo)
    a = tifffile.imread(f)[::8, ::8].astype(float)
    n = a.shape[0]
    ys = la + 0.5 - (np.arange(n) + .5) / n * 0.5
    xs = lo + (np.arange(a.shape[1]) + .5) / a.shape[1] * 0.5
    X, Y = np.meshgrid(xs, ys)
    dentro = contains_xy(galicia, X.ravel(), Y.ravel())
    mostras.append(a.ravel()[dentro])
alt_gal = np.concatenate(mostras)
print(f"altura media de Galicia: {alt_gal.mean():.0f} m (n={alt_gal.size})")

# --- Global Wind Atlas, 100 m
gwa = tifffile.TiffFile(baixa("gwa_ESP_wind-speed_100m.tif", GWA, binario=True))
pg = gwa.pages[0]
esc = pg.tags["ModelPixelScaleTag"].value
tie = pg.tags["ModelTiepointTag"].value
GX0, GY0, GD = tie[3], tie[4], esc[0]
V = pg.asarray()
V = np.where(V > 0, V, np.nan)


def vento(lon, lat):
    fil = int((GY0 - lat) / GD); col = int((lon - GX0) / GD)
    v = V[fil, col]
    return None if np.isnan(v) else float(v)


# media do vento en terra galega (todas as celas de 250 m dentro do contorno)
f0, f1 = int((GY0 - 43.85) / GD), int((GY0 - 41.75) / GD)
c0, c1 = int((-9.35 - GX0) / GD), int((-6.70 - GX0) / GD)
sub = V[f0:f1, c0:c1]
ys = GY0 - (np.arange(f0, f1) + .5) * GD
xs = GX0 + (np.arange(c0, c1) + .5) * GD
X, Y = np.meshgrid(xs, ys)
dentro = contains_xy(galicia, X.ravel(), Y.ravel())
v_gal = sub.ravel()[dentro]
v_gal = v_gal[~np.isnan(v_gal)]
print(f"vento medio a 100 m en Galicia (GWA): {v_gal.mean():.2f} m/s")

# grella de puntos de vento (0,04°), media dos píxeles de cada cela, só en terra
PASO = 0.04
grella = []
for lat in np.arange(41.82, 43.80, PASO):
    for lon in np.arange(-9.30, -6.72, PASO):
        if not gal_p.contains(Point(lon, lat)):
            continue
        ff = int((GY0 - lat - PASO / 2) / GD); cc = int((lon - PASO / 2 - GX0) / GD)
        k = int(PASO / GD)
        bloque = V[ff:ff + k, cc:cc + k]
        if np.isnan(bloque).all():
            continue
        grella.append((round(float(np.nanmean(bloque)) * 4) / 4, [r(lon, 3), r(lat, 3)]))
# agrupados por clase de 0,25 m/s nun MultiPoint por clase (a capa pesa moito menos)
clases = {}
for v, c in grella:
    clases.setdefault(v, []).append(c)
garda("vento.geojson", geo([{"type": "Feature", "properties": {"v": v},
                             "geometry": {"type": "MultiPoint", "coordinates": cs}} for v, cs in sorted(clases.items())]))

# --- aeroxeradores (OSM)
aero = baixa("osm_aeroxeradores.json", OVERPASS, {"data": Q_AERO})["elements"]
aero = [e for e in aero if e.get("tags", {}).get("power") == "generator"
        and gal_p.contains(Point(e["lon"], e["lat"]))]
alt_a = np.array([altura(e["lon"], e["lat"]) for e in aero], dtype=float)
v_a = np.array([vento(e["lon"], e["lat"]) or np.nan for e in aero])
print(f"aeroxeradores en Galicia (OSM): {len(aero)}; altura media {np.nanmean(alt_a):.0f} m; "
      f"vento medio {np.nanmean(v_a):.2f} m/s")

# --- Rede Natura 2000
rn = baixa("mgs_rede-natura.geojson", RN)
rn_g = []
for f in rn["features"]:
    g = make_valid(shape(f["geometry"]))
    if not g.intersects(galicia):
        continue
    rn_g.append((f["properties"], g))
rn_terra = unary_union([g for _, g in rn_g]).intersection(galicia)
rn_p = prep(rn_terra)
en_rn = sum(rn_p.contains(Point(e["lon"], e["lat"])) for e in aero)
print(f"Rede Natura en terra: {rn_terra.area / galicia.area * 100:.1f} % de Galicia; aeroxeradores dentro: {en_rn}")
galicia_s = galicia.simplify(0.01).buffer(0.01)
rn_out = []
for p, g in rn_g:
    s = g.simplify(0.006).intersection(galicia_s).simplify(0.003)
    if s.is_empty or s.area < 1e-4:
        continue
    rn_out.append({"type": "Feature", "properties": {"n": p["nome"]},
                   "geometry": redondea(mapping(s))})
garda("rede-natura.geojson", geo(rn_out))
# aeroxeradores por espazo da Rede Natura (un aeroxerador pode estar en ZEC e ZEPA á vez)
por_espazo = {}
for p, g in rn_g:
    gp = prep(g)
    n = sum(gp.contains(Point(e["lon"], e["lat"])) for e in aero)
    if n:
        por_espazo[f"{p['nome']} ({p['figura']})"] = n

# aeroxeradores: dous MultiPoint (dentro / fóra da Rede Natura) para que a capa pese pouco
dentro_rn = [[r(e["lon"]), r(e["lat"])] for e in aero if rn_p.contains(Point(e["lon"], e["lat"]))]
fora_rn = [[r(e["lon"]), r(e["lat"])] for e in aero if not rn_p.contains(Point(e["lon"], e["lat"]))]
garda("aeroxeradores.geojson", geo([
    {"type": "Feature", "properties": {"rn": 1}, "geometry": {"type": "MultiPoint", "coordinates": dentro_rn}},
    {"type": "Feature", "properties": {"rn": 0}, "geometry": {"type": "MultiPoint", "coordinates": fora_rn}}]))

# --- ZAPER (POEM) fronte a Galicia: NOR-1 a NOR-5 (NOR-6 a NOR-8 están fronte a Asturias)
emod = baixa("zaper/emodnet_msp_zoning.json", EMODNET)
zaper = []
for f in emod["features"]:
    p = f["properties"]
    if "ZAPER" not in p["localid"]:
        continue
    cod = "NOR-" + p["localid"].rsplit("_", 1)[1]
    if cod not in {"NOR-1", "NOR-2", "NOR-3", "NOR-4", "NOR-5"}:
        continue
    g = shape(f["geometry"]).simplify(0.002)
    zaper.append({"type": "Feature", "properties": {"c": cod, "km2": round(p["areakm2"], 1)},
                  "geometry": redondea(mapping(g))})
garda("zaper.geojson", geo(zaper))

# --- parques (OSM): só para o README e as comprobacións
parq = baixa("osm_parques.json", OVERPASS, {"data": Q_PARQUES})["elements"]

# --- cifras por zona
cifras = {
    "n_aeroxeradores": len(aero),
    "n_parques_osm": len(parq),
    "altura_media_aero_m": round(float(np.nanmean(alt_a))),
    "altura_mediana_aero_m": round(float(np.nanmedian(alt_a))),
    "pc_aero_sobre_500m": round(float((alt_a > 500).mean() * 100), 1),
    "altura_media_galicia_m": round(float(alt_gal.mean())),
    "pc_galicia_sobre_500m": round(float((alt_gal > 500).mean() * 100), 1),
    "vento_medio_aero_ms": round(float(np.nanmean(v_a)), 1),
    "vento_medio_galicia_ms": round(float(v_gal.mean()), 1),
    "pc_galicia_vento_ge_7": round(float((v_gal >= 7).mean() * 100), 1),
    "pc_aero_vento_ge_7": round(float((v_a[~np.isnan(v_a)] >= 7).mean() * 100), 1),
    "aero_en_rede_natura": int(en_rn),
    "pc_aero_en_rede_natura": round(en_rn / len(aero) * 100, 1),
    "pc_galicia_rede_natura": round(rn_terra.area / galicia.area * 100, 1),
    "zaper_galicia_km2_emodnet": round(sum(z["properties"]["km2"] for z in zaper), 1),
    "zonas": {},
    "aero_por_espazo_rn": dict(sorted(por_espazo.items(), key=lambda x: -x[1])),
}
for k, (x0, y0, x1, y1) in ZONAS.items():
    sel = [e for e in aero if x0 <= e["lon"] <= x1 and y0 <= e["lat"] <= y1]
    sa = np.array([altura(e["lon"], e["lat"]) for e in sel], dtype=float)
    sv = np.array([vento(e["lon"], e["lat"]) or np.nan for e in sel])
    mx, onde = altura_max((x0, y0, x1, y1))
    cifras["zonas"][k] = {"caixa": [x0, y0, x1, y1], "aeroxeradores": len(sel),
                          "altura_media_aero_m": round(float(np.nanmean(sa))) if len(sel) else None,
                          "vento_medio_aero_ms": round(float(np.nanmean(sv)), 1) if len(sel) else None,
                          "en_rede_natura": int(sum(rn_p.contains(Point(e["lon"], e["lat"])) for e in sel)),
                          "altura_max_m": mx, "altura_max_onde": onde}
(AQUI / "data" / "cifras.json").write_text(json.dumps(cifras, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(cifras, ensure_ascii=False, indent=1))

#!/usr/bin/env python3
"""Cando os ríos saen do leito — prepara as capas de v/rios-fora-do-leito/capas/.

Fontes (detalle en README.md):
  1. Mapas Galicia Sustentable (foto do día en local, ~/Proxectos/mapasgs/site/public/data):
     crecida-episodios (episodio do 5–11/10/2026), estacions-meteo (nomes das estacións),
     inundacion-perigo-t10/-t100/-t500 (teselas PNG do SNCZI, para Miño e Sil).
  2. Augas de Galicia, IDEG ArcGIS REST, D2007_60_MapasInundFluv_21_27: láminas T10/T100/T500
     (vector) e risco para a poboación das ARPSI de Galicia-Costa.
  3. Mapa base de mapasgs (build/galicia.pmtiles, Protomaps/OpenStreetMap): ríos (capa water).
  4. MDT 25 m do IGN (fontes/terreo/data/raw/*.tif): alturas.

Precisa: numpy, pillow, tifffile, shapely; e os binarios `pmtiles` e `tippecanoe-decode`.
Uso: python3 prep.py   (descarga o que falte en data/raw/ e escribe capas/ e data/cifras.json)
"""
import hashlib
import io
import json
import math
import shutil
import subprocess
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

import numpy as np
import shapely
import tifffile
from PIL import Image
from shapely import box, simplify, unary_union
from shapely.geometry import mapping, shape

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
RAW = AQUI / "data" / "raw"
CAPAS = RAIZ / "v" / "rios-fora-do-leito" / "capas"
MAPASGS = Path.home() / "Proxectos" / "mapasgs"
DATA_MGS = MAPASGS / "site" / "public" / "data"
PUB_MGS = "https://mapas.galiciasustentable.org/data"
BASEMAP = MAPASGS / "build" / "galicia.pmtiles"
MDT = RAIZ / "fontes" / "terreo" / "data" / "raw"
IDEG = ("https://ideg.xunta.gal/servizos/rest/services/IDE_DHGC/"
        "D2007_60_MapasInundFluv_21_27/MapServer")
UA = {"User-Agent": "FGS-divulga/1.0"}

RAW.mkdir(parents=True, exist_ok=True)
CAPAS.mkdir(parents=True, exist_ok=True)

# ARPSI de Galicia-Costa que se usan (código da ARPSI no plan 2021–2027)
ARPSI = {
    "betanzos": "CO-12-01-01",   # Río Mandeo - Betanzos
    "padron": "CP-05-02-11",     # Río Ulla y Río Sar - Padrón
    "pontevea": "CP-05-03-12",   # Río Ulla - Pontevea
}
# Miño e Sil (Miño-Sil, sen vector público accesible): recadros para vectorizar as teselas
RECADROS = {
    "ourense": (-7.93, 42.29, -7.80, 42.39),
    "obarco": (-7.10, 42.37, -6.885, 42.46),
}


def rnd(g, n=5):
    return shapely.transform(g, lambda c: np.round(c, n))


def gardar(nome, feats):
    fc = {"type": "FeatureCollection", "features": feats}
    p = CAPAS / f"{nome}.geojson"
    p.write_text(json.dumps(fc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    kb = p.stat().st_size / 1024
    print(f"  {p.name}: {len(feats)} elementos, {kb:.0f} KB")
    assert kb < 200, f"{p.name} pasa de 200 KB"


def feat(geom, **props):
    return {"type": "Feature", "properties": props, "geometry": mapping(geom)}


# ---------------------------------------------------------------- 1. capas de mapasgs
def capa_mgs(capa):
    dest = RAW / f"{capa}.geojson"
    if not dest.exists():
        local = DATA_MGS / capa / "data.geojson"
        if local.exists():
            shutil.copy(local, dest)
            shutil.copy(DATA_MGS / capa / "meta.json", RAW / f"{capa}.meta.json")
        else:
            for f in ("data.geojson", "meta.json"):
                req = urllib.request.Request(f"{PUB_MGS}/{capa}/{f}", headers=UA)
                out = dest if f == "data.geojson" else RAW / f"{capa}.meta.json"
                out.write_bytes(urllib.request.urlopen(req, timeout=120).read())
    return json.loads(dest.read_text(encoding="utf-8"))


print("1. Episodio de crecida (crecida-episodios) e estacións (estacions-meteo)")
crec = capa_mgs("crecida-episodios")
meteo = capa_mgs("estacions-meteo")
nomes_meteo = {f["properties"]["id"]: f["properties"] for f in meteo["features"]}
cifras = {}

est = [f for f in crec["features"] if f["properties"]["tipo"] == "estacion"]
estac_feats = []
info_est = {}
for f in est:
    p = f["properties"]
    base, pico = p["caudal_base"], p["caudal_pico"]
    r = pico / base if base else None
    info_est[p["id"]] = (p["nome"].strip(), base, pico, r, p["hora_pico"], p["marea"])
    # razón só para estacións con caudal base apreciable (≥ 0,1 m³/s): cos regos case secos
    # a razón dispárase (0,009 → 21 m³/s en Baltar) e non describe a crecida
    estac_feats.append(feat(shape(f["geometry"]), nome=p["nome"].strip(),
                            base=round(base, 2), pico=round(pico, 1),
                            r=round(r, 1) if (r and base >= 0.1) else None,
                            marea=p["marea"]))
gardar("estacions", estac_feats)

# ríos de Galicia-Costa (masas de auga) acesos pola razón da estación que lles corresponde
id_por_nome = {}
for f in est:
    id_por_nome[f["properties"]["nome"].strip()] = f["properties"]["id"]
rios = []
for f in crec["features"]:
    p = f["properties"]
    if p["tipo"] != "rio":
        continue
    g = shape(f["geometry"])
    st = p.get("estacion")
    r = None
    if st is not None:
        sid = st if isinstance(st, int) else id_por_nome.get(str(st).strip())
        if sid in info_est:
            _, b, _, rr, _, mar = info_est[sid]
            if rr and b >= 0.1 and not mar:
                r = round(rr, 1)
    rios.append((r, g))
# agrupa por razón (truncada a 0,5: ×1,95 queda en 1,5, por baixo do dobre) para ter poucos elementos
grupos = defaultdict(list)
for r, g in rios:
    grupos[None if r is None else math.floor(r * 2) / 2].append(g)
gardar("rios-crecida", [feat(rnd(simplify(unary_union(gs), 0.001), 4), r=r) for r, gs in grupos.items()])

# choiva diaria: total do 5 ao 10/10/2026 (seis días) por estación
ch = []
tot = []
for f in crec["features"]:
    p = f["properties"]
    if p["tipo"] != "choiva":
        continue
    dias = p["choiva_dia"]
    if any(v is None for v in dias):
        continue
    t = round(sum(dias), 1)
    tot.append((t, p["id"], dias))
    ch.append(feat(rnd(shape(f["geometry"]), 4), mm=t))
gardar("choiva", ch)
tot.sort(reverse=True)
cifras["choiva"] = {
    "estacions": len(tot),
    "mediana_mm": float(np.median([t for t, _, _ in tot])),
    "maximas": [{"mm": t, "id": i, "nome": nomes_meteo.get(i, {}).get("nome"),
                 "concello": nomes_meteo.get(i, {}).get("concello"), "dias": d}
                for t, i, d in tot[:6]],
}
cifras["estacions"] = {n: {"base": b, "pico": pc, "razon": round(r, 2) if r else None,
                           "hora_pico_utc": h, "marea": m}
                       for (n, b, pc, r, h, m) in info_est.values()}

# ---------------------------------------------------------------- 2. rede fluvial (OSM)
print("2. Rede fluvial (mapa base de mapasgs, OpenStreetMap)")
rede_raw = RAW / "basemap-water-z9.geojson"
if not rede_raw.exists():
    out = subprocess.run(["tippecanoe-decode", "-z9", "-Z9", "-l", "water", str(BASEMAP)],
                         capture_output=True, check=True).stdout
    rede_raw.write_bytes(out)
dec = json.loads(rede_raw.read_text(encoding="utf-8"))
lin = defaultdict(list)
for tile in dec["features"]:
    for L in tile["features"]:
        for f in L.get("features", []):
            pr = f.get("properties", {})
            if pr.get("kind") != "river":
                continue
            lin[pr.get("name") or ""].append(shape(f["geometry"]))
fora = unary_union([shape(f["geometry"]) for f in json.loads(
    (RAIZ / "assets" / "terreo" / "galicia-fora.geojson").read_text(encoding="utf-8"))["features"]]).buffer(0)
PRINCIPAIS = ("Miño", "Sil", "Ulla", "Tambre", "Xallas", "Eume", "Mandeo", "Lérez", "Umia", "Mero",
              "Masma", "Navia", "Limia", "Avia", "Arnoia", "Neira", "Cabe", "Bibei", "Sar", "Mendo",
              "Anllóns", "Landro", "Sor", "Deza", "Ladra", "Támega", "Tea", "Arenteiro", "Xares")
xr = {0: [], 1: []}
for nome, gs in lin.items():
    g = unary_union(gs).difference(fora)
    if g.length < 0.1:  # só ríos de máis de ~8 km dentro de Galicia
        continue
    xr[1 if any(k in nome for k in PRINCIPAIS) else 0].append(g)
rede = [feat(rnd(simplify(unary_union(gs), 0.0022 if k == 0 else 0.0012), 4), p=k) for k, gs in xr.items()]
gardar("rede", rede)

# ---------------------------------------------------------------- 3. láminas de Galicia-Costa (IDEG)
print("3. Zonas inundables de Galicia-Costa (Augas de Galicia, IDEG)")


def ideg(capa, where, campos, xeo=True):
    q = urllib.parse.urlencode({"where": where, "outFields": campos, "returnGeometry": str(xeo).lower(),
                                "outSR": 4326, "f": "geojson" if xeo else "json"})
    nome = RAW / f"ideg-{capa}-{hashlib.md5(where.encode()).hexdigest()[:10]}-{int(xeo)}.json"
    if not nome.exists():
        req = urllib.request.Request(f"{IDEG}/{capa}/query?{q}", headers=UA)
        nome.write_bytes(urllib.request.urlopen(req, timeout=180).read())
    return json.loads(nome.read_text(encoding="utf-8"))


LAMINA = {"t10": 2, "t100": 3, "t500": 4}
RISCO = {"t10": 5, "t100": 6, "t500": 7}
zi = {t: [] for t in LAMINA}
cifras["zi"] = {}
for lugar, cod in ARPSI.items():
    cifras["zi"][lugar] = {}
    for t, capa in LAMINA.items():
        d = ideg(capa, f"ID_ZONA LIKE 'ES014-{ {'t10': 'T010'}.get(t, t.upper()) }-{cod}-%'", "ID_ZONA,RIO,Q_M3_S")
        gs = [shape(f["geometry"]) for f in d["features"]]
        g = unary_union(gs)
        # área en ha (proxección local equirectangular, abonda para unha cifra en ha)
        lat0 = g.centroid.y
        kx, ky = 111320 * math.cos(math.radians(lat0)), 110574
        ha = shapely.transform(g, lambda c: c * [kx, ky]).area / 1e4
        qs = sorted({f["properties"]["RIO"] + ": " + (f["properties"]["Q_M3_S"] or "")
                     for f in d["features"]})
        cifras["zi"][lugar][t] = {"ha": round(ha, 1), "caudais_m3s": qs}
        zi[t].append(feat(rnd(simplify(g, 0.00006), 5), lugar=lugar))
        r = ideg(RISCO[t], f"COD_ARPSI = 'ES014-{cod}'", "COD_ARPSI,NOM_MUNICI,NUM_AFE_MU,NUM_AFE_ZI,FECHA", xeo=False)
        hab = defaultdict(int)
        for a in (x["attributes"] for x in r["features"]):
            # NUM_AFE_ZI: habitantes do polígono de poboación dentro da lámina; súmase na ARPSI
            # (NUM_AFE_MU repite o total do concello en todas as súas ARPSI: non se usa)
            hab[a["NOM_MUNICI"]] += a["NUM_AFE_ZI"] or 0
        cifras["zi"][lugar][t]["habitantes_por_concello"] = dict(hab)
        cifras["zi"][lugar][t]["ano_poboacion"] = sorted({x["attributes"]["FECHA"] for x in r["features"]})

# ---------------------------------------------------------------- 4. Miño e Sil: teselas do SNCZI
print("4. Zonas inundables do Miño e do Sil (teselas PNG do SNCZI en mapasgs, vectorizadas)")
Z = 13


def lonlat2tile(lon, lat, z):
    n = 2 ** z
    return ((lon + 180) / 360 * n, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)


def px2lonlat(px, py, z):
    n = 2 ** z * 256
    lon = px / n * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * py / n))))
    return lon, lat


for lugar, (w, s, e, n_) in RECADROS.items():
    cifras["zi"][lugar] = {}
    fx0, fy0 = lonlat2tile(w, n_, Z)
    fx1, fy1 = lonlat2tile(e, s, Z)
    x0, y0, x1, y1 = int(fx0), int(fy0), int(fx1), int(fy1)
    for t in LAMINA:
        pm = DATA_MGS / f"inundacion-perigo-{t}" / "data.pmtiles"
        W, H = (x1 - x0 + 1) * 256, (y1 - y0 + 1) * 256
        mask = np.zeros((H, W), bool)
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                cache = RAW / "snczi" / t / f"{Z}-{x}-{y}.png"
                if not cache.exists():
                    cache.parent.mkdir(parents=True, exist_ok=True)
                    b = subprocess.run(["pmtiles", "tile", str(pm), str(Z), str(x), str(y)],
                                       capture_output=True).stdout
                    cache.write_bytes(b)
                b = cache.read_bytes()
                if b:
                    a = np.array(Image.open(io.BytesIO(b)).convert("RGBA"))[:, :, 3] > 127
                    mask[(y - y0) * 256:(y - y0 + 1) * 256, (x - x0) * 256:(x - x0 + 1) * 256] = a
        # recorta ao recadro
        cx0, cy0 = int((fx0 - x0) * 256), int((fy0 - y0) * 256)
        cx1, cy1 = int((fx1 - x0) * 256), int((fy1 - y0) * 256)
        m = np.zeros_like(mask)
        m[cy0:cy1, cx0:cx1] = mask[cy0:cy1, cx0:cx1]
        # área: píxeles × área do píxel no chan á latitude de cada fila
        lat_fila = np.array([px2lonlat(0, (y0 * 256 + j + 0.5), Z)[1] for j in range(H)])
        lado = 40075016.686 * np.cos(np.radians(lat_fila)) / (2 ** Z * 256)
        ha = float((m.sum(axis=1) * lado ** 2).sum() / 1e4)
        # polígonos: tramos de cada fila → caixas → unión
        caixas = []
        for j in range(H):
            fila = m[j]
            if not fila.any():
                continue
            d = np.diff(np.concatenate([[0], fila.astype(np.int8), [0]]))
            for a0, a1 in zip(np.where(d == 1)[0], np.where(d == -1)[0]):
                caixas.append(box(a0, j, a1, j + 1))
        g = unary_union(caixas).simplify(1.3)
        g = shapely.transform(g, lambda c: np.array([px2lonlat(a + x0 * 256, b + y0 * 256, Z) for a, b in c]))
        cifras["zi"][lugar][t] = {"ha": round(ha, 1), "metodo": "teselas z13 do SNCZI vectorizadas"}
        zi[t].append(feat(rnd(g, 5), lugar=lugar))

for t, fs in zi.items():
    gardar(f"zi-{t}", fs)

# ---------------------------------------------------------------- 5. alturas do MDT
print("5. Alturas (MDT 25 m do IGN)")


def altura(lon, lat):
    for tif in MDT.glob("mdt25_*.tif"):
        la, lo = (float(v) for v in tif.stem.split("_")[1:3])
        if la <= lat < la + 0.5 and lo <= lon < lo + 0.5:
            with tifffile.TiffFile(tif) as tf:
                a = tf.pages[0].asarray()
            h, w = a.shape
            i = int((la + 0.5 - lat) / 0.5 * h)
            j = int((lon - lo) / 0.5 * w)
            return int(a[min(i, h - 1), min(j, w - 1)])
    return None


cifras["alturas"] = {
    "ourense_ponte_romana_rio": altura(-7.8706, 42.3433),
    "obarco_rio": altura(-6.9826, 42.4142),
}

(AQUI / "data").mkdir(exist_ok=True)
(AQUI / "data" / "cifras.json").write_text(json.dumps(cifras, ensure_ascii=False, indent=1), encoding="utf-8")
print("cifras → data/cifras.json")

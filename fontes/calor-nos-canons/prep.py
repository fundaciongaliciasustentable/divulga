#!/usr/bin/env python3
"""Datos de «A calor que baixa aos vales» (v/calor-nos-canons/).

Entradas (foto do día, 04/11/2026):
  - capa tmax-ano de Mapas Galicia Sustentable: máximas diarias de 2025 das
    estacións de MeteoGalicia (copia en data/raw/tmax-ano.geojson);
  - capa historial-queimados (Copernicus EFFIS) para os perímetros de 2025;
  - MDT de 25 m do IGN en ../terreo/data/raw/*.tif;
  - máscara de Galicia en ../../assets/terreo/galicia-fora.geojson.

Saídas:
  - ../../v/calor-nos-canons/capas/estacions.geojson  puntos coas cifras de cada estación
  - ../../v/calor-nos-canons/capas/lumes2025.geojson  perímetros EFFIS de agosto de 2025 (> 1.000 ha)
  - ../../v/calor-nos-canons/capas/perfil.geojson     liña do perfil San Clodio–Conchada
  - ../../v/calor-nos-canons/capas/calor-xja.png      superficie interpolada (media das máximas xuño–agosto)
  - data/cifras.json                                  todas as cifras que cita a peza
  - ../../v/calor-nos-canons/thumb.svg

Uso (numpy, tifffile, Pillow):
    python3 prep.py
"""
import datetime as dt
import io
import json
import math
import shutil
from pathlib import Path

import numpy as np
import tifffile
from PIL import Image, ImageDraw

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
RAW = AQUI / "data" / "raw"
MDT = RAIZ / "fontes" / "terreo" / "data" / "raw"
SAIDA = RAIZ / "v" / "calor-nos-canons"
CAPAS = SAIDA / "capas"
MAPASGS = Path.home() / "Proxectos" / "mapasgs" / "site" / "public" / "data"

ANO = 2025
D0 = dt.date(ANO, 1, 1)
XJA = (dt.date(ANO, 6, 1) - D0).days, (dt.date(ANO, 8, 31) - D0).days   # índices incluídos
DIA_10A = (dt.date(ANO, 8, 10) - D0).days
DIA_29X = (dt.date(ANO, 6, 29) - D0).days
GRADIENTE = 6.5 / 1000          # °C por metro (atmosfera estándar), como en Mapas GS

# grella da superficie (graos): ~330 × 330 m
G_LON0, G_LON1, G_LAT0, G_LAT1 = -9.36, -6.70, 41.80, 43.80
G_DLON, G_DLAT = 0.004, 0.003


def copia(capa):
    dest = RAW / f"{capa}.geojson"
    if not dest.exists():
        shutil.copy(MAPASGS / capa / "data.geojson", dest)
        shutil.copy(MAPASGS / capa / "meta.json", RAW / f"{capa}.meta.json")
    return json.loads(dest.read_text(encoding="utf-8"))


# --- MDT -------------------------------------------------------------------
class Mdt:
    """Mosaico do MDT de 25 m cargado por anacos de 0,5° baixo demanda."""

    def __init__(self):
        self.cache = {}

    def anaco(self, lon, lat):
        lo = math.floor(lon * 2) / 2
        la = math.floor((lat - 0.25) * 2) / 2 + 0.25
        k = (la, lo)
        if k not in self.cache:
            f = MDT / f"mdt25_+{la:.2f}_{lo:.2f}.tif"
            with tifffile.TiffFile(f) as t:
                p = t.pages[0]
                sx, sy, _ = p.tags["ModelPixelScaleTag"].value
                _, _, _, x0, y0, _ = p.tags["ModelTiepointTag"].value
                self.cache[k] = (x0, y0, sx, sy, p.asarray().astype(np.float32))
        return self.cache[k]

    def altura(self, lon, lat):
        x0, y0, sx, sy, a = self.anaco(lon, lat)
        c = int((lon - x0) / sx)
        f = int((y0 - lat) / sy)
        return float(a[min(f, a.shape[0] - 1), min(c, a.shape[1] - 1)])

    def ventá(self, lon, lat, rlon, rlat):
        """Mínimo e máximo (con posición) nun rectángulo arredor do punto."""
        lons = np.arange(lon - rlon, lon + rlon, 0.000225)
        lats = np.arange(lat - rlat, lat + rlat, 0.000225)
        mn, mx = (1e9, None), (-1e9, None)
        for la in lats[::2]:
            for lo in lons[::2]:
                h = self.altura(lo, la)
                if h <= 0:
                    continue
                if h < mn[0]:
                    mn = (h, (round(lo, 4), round(la, 4)))
                if h > mx[0]:
                    mx = (h, (round(lo, 4), round(la, 4)))
        return mn, mx

    def grella_media(self, lon0, lat1, dlon, dlat, nx, ny):
        """Altura media de cada cela (fila 0 = norte)."""
        out = np.zeros((ny, nx), dtype=np.float32)
        for j in range(ny):
            la = lat1 - (j + 0.5) * dlat
            for i in range(nx):
                lo = lon0 + (i + 0.5) * dlon
                x0, y0, sx, sy, a = self.anaco(lo, la)
                c = int((lo - x0) / sx)
                f = int((la - y0) / -sy)
                h = max(1, int(dlon / sx / 2))
                v = max(1, int(dlat / sy / 2))
                blq = a[max(0, f - v):f + v, max(0, c - h):c + h]
                out[j, i] = blq.mean() if blq.size else 0
        return out


def perfil(mdt, a, b, n=200):
    pts = []
    for k in range(n + 1):
        t = k / n
        lo = a[0] + (b[0] - a[0]) * t
        la = a[1] + (b[1] - a[1]) * t
        pts.append((round(lo, 5), round(la, 5), mdt.altura(lo, la)))
    return pts


def km(a, b):
    dx = (b[0] - a[0]) * 111.32 * math.cos(math.radians((a[1] + b[1]) / 2))
    dy = (b[1] - a[1]) * 110.57
    return math.hypot(dx, dy)


# --- simplificación ----------------------------------------------------------
def dp(pts, tol):
    if len(pts) < 3:
        return pts
    a, b = np.array(pts[0]), np.array(pts[-1])
    ab = b - a
    n = np.hypot(*ab) or 1e-12
    p = np.array(pts)
    d = np.abs(ab[0] * (p[:, 1] - a[1]) - ab[1] * (p[:, 0] - a[0])) / n
    i = int(d.argmax())
    if d[i] > tol:
        return dp(pts[:i + 1], tol)[:-1] + dp(pts[i:], tol)
    return [pts[0], pts[-1]]


def anel(r, tol):
    """Simplifica un anel pechado partíndoo en dúas metades (DP non vale con extremos iguais)."""
    m = len(r) // 2
    return dp(r[:m + 1], tol)[:-1] + dp(r[m:], tol)


def rnd(pts, nd=4):
    out = []
    for x, y in pts:
        q = [round(x, nd), round(y, nd)]
        if not out or q != out[-1]:
            out.append(q)
    return out


# --- cores ----------------------------------------------------------------------
ESCALA = [  # media das máximas xuño–agosto (°C) → cor, opacidade
    (18, (40, 60, 90), 0.00),
    (22, (60, 95, 120), 0.20),
    (25, (150, 150, 110), 0.35),
    (27, (233, 196, 106), 0.55),
    (29, (240, 140, 60), 0.72),
    (31, (220, 70, 45), 0.85),
    (33, (165, 20, 50), 0.92),
]


def cor(v):
    if v <= ESCALA[0][0]:
        return (*ESCALA[0][1], 0)
    for (v0, c0, a0), (v1, c1, a1) in zip(ESCALA, ESCALA[1:]):
        if v <= v1:
            t = (v - v0) / (v1 - v0)
            return tuple(round(c0[k] + (c1[k] - c0[k]) * t) for k in range(3)) + (round(255 * (a0 + (a1 - a0) * t)),)
    return (*ESCALA[-1][1], round(255 * ESCALA[-1][2]))


def main():
    CAPAS.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    tmax = copia("tmax-ano")
    lumes = copia("historial-queimados")
    mdt = Mdt()
    cifras = {"ano": ANO, "consulta": "2026-11-04"}

    # --- 1. cifras por estación ------------------------------------------------
    est = []
    for f in tmax["features"]:
        p = f["properties"]
        v = p["tmax"]
        ok = [(x, i) for i, x in enumerate(v) if x is not None]
        if not ok:
            continue
        mx, imx = max(ok)
        xja = [x for i, x in enumerate(v) if XJA[0] <= i <= XJA[1] and x is not None]
        e = {
            "n": p["nome"].strip(), "c": p["concello"], "alt": p["altitude"],
            "lon": f["geometry"]["coordinates"][0], "lat": f["geometry"]["coordinates"][1],
            "max": mx, "data_max": str(D0 + dt.timedelta(imx)),
            "d30": sum(1 for x, _ in ok if x >= 30), "d35": sum(1 for x, _ in ok if x >= 35),
            "xja": round(sum(xja) / len(xja), 1) if len(xja) >= 85 else None,
            "dias_xja": len(xja), "dias": p.get("dias_con_dato", len(ok)),
            "t10a": v[DIA_10A], "t29x": v[DIA_29X],
        }
        est.append(e)
    est.sort(key=lambda e: -e["max"])
    cifras["estacions"] = len(est)
    cifras["top_max"] = [{k: e[k] for k in ("n", "c", "alt", "max", "data_max")} for e in est[:10]]
    cifras["top_d35"] = [{k: e[k] for k in ("n", "c", "alt", "d30", "d35")}
                         for e in sorted(est, key=lambda e: -e["d35"])[:10]]
    conxs = [e for e in est if e["xja"] is not None]
    cifras["top_xja"] = [{k: e[k] for k in ("n", "c", "alt", "xja")}
                         for e in sorted(conxs, key=lambda e: -e["xja"])[:10]]
    cifras["baixo_xja"] = [{k: e[k] for k in ("n", "c", "alt", "xja")}
                           for e in sorted(conxs, key=lambda e: e["xja"])[:8]]
    por = {e["n"]: e for e in est}
    nomes = ["Ourense", "Ourense-Estacións", "EVEGA Leiro", "Remuíño", "Prado", "San Clodio", "Conchada",
             "Xabrega", "Míllara", "Monforte", "Monforte-CFEA", "A Portela", "As Petarelas", "Larouco",
             "Lardeira", "Verín-Vilela", "Verín-Vilamaior", "Cabeza de Manzaneda", "Xares", "Camariñas",
             "Coruña-Torre de Hércules", "Vigo-Navia", "Corrubedo"]
    cifras["sel"] = {n: por[n] for n in nomes if n in por}
    d10 = sorted([e for e in est if e["t10a"] is not None], key=lambda e: -e["t10a"])
    cifras["dia_10a"] = {"estacions": len(d10), "max": [(e["n"], e["t10a"]) for e in d10[:5]],
                         "min": [(e["n"], e["alt"], e["t10a"]) for e in d10[-5:]],
                         "ge40": sum(1 for e in d10 if e["t10a"] >= 40)}
    d29 = sorted([e for e in est if e["t29x"] is not None], key=lambda e: -e["t29x"])
    cifras["dia_29x"] = {"max": [(e["n"], e["t29x"]) for e in d29[:5]],
                         "ge40": sum(1 for e in d29 if e["t29x"] >= 40)}
    cifras["rede_ge35_algun_dia"] = sum(1 for e in est if e["d35"] > 0)
    cifras["rede_ge40_algun_dia"] = sum(1 for e in est if e["max"] >= 40)

    feats = []
    for e in est:
        feats.append({"type": "Feature",
                      "geometry": {"type": "Point", "coordinates": [round(e["lon"], 4), round(e["lat"], 4)]},
                      "properties": {"n": e["n"], "alt": e["alt"], "max": e["max"], "d35": e["d35"],
                                     "xja": e["xja"], "t10": e["t10a"]}})
    (CAPAS / "estacions.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats},
                                                        ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # --- 2. relevo: alturas citadas -------------------------------------------
    rel = {}
    sc, co = (por["San Clodio"]["lon"], por["San Clodio"]["lat"]), (por["Conchada"]["lon"], por["Conchada"]["lat"])
    rel["san_clodio_mdt"] = mdt.altura(*sc)
    rel["conchada_mdt"] = mdt.altura(*co)
    rel["san_clodio_conchada_km"] = round(km(sc, co), 1)
    pf = perfil(mdt, sc, co)
    rel["perfil_min"] = min(h for *_, h in pf)
    rel["perfil_max"] = max(h for *_, h in pf)
    # río Sil ao pé de San Clodio e bordo do val (ventá de ~3 × 4 km)
    rel["sil_san_clodio"] = mdt.ventá(-7.287, 42.455, 0.02, 0.012)
    # canón do Sil (Parada de Sil – Nogueira de Ramuín): fondo e bordo
    rel["canon_sil"] = mdt.ventá(-7.56, 42.39, 0.03, 0.015)
    # Ourense: fondo do val do Miño e cumios a menos de 10 km
    rel["ourense"] = mdt.ventá(-7.86, 42.34, 0.12, 0.09)
    # depresión de Lemos
    rel["lemos"] = mdt.ventá(-7.52, 42.51, 0.10, 0.07)
    # Valdeorras: Sil no Barco e Pena Trevinca
    rel["valdeorras"] = mdt.ventá(-6.90, 42.36, 0.20, 0.12)
    # Verín: veiga do Támega
    rel["verin"] = mdt.ventá(-7.43, 41.95, 0.08, 0.06)
    # O Ribeiro: Miño e Avia arredor de Ribadavia
    rel["ribeiro"] = mdt.ventá(-8.12, 42.29, 0.08, 0.07)
    for n in ("Cabeza de Manzaneda", "Lardeira", "Xares", "A Portela", "Ourense", "EVEGA Leiro", "Monforte-CFEA",
              "Verín-Vilela", "Camariñas"):
        rel[f"mdt_{n}"] = mdt.altura(por[n]["lon"], por[n]["lat"])
    rel["sc_manzaneda_km"] = round(km(sc, (por["Cabeza de Manzaneda"]["lon"], por["Cabeza de Manzaneda"]["lat"])), 1)
    rel["sc_camarinas_km"] = round(km(sc, (por["Camariñas"]["lon"], por["Camariñas"]["lat"])), 1)
    rel["portela_lardeira_km"] = round(km((por["A Portela"]["lon"], por["A Portela"]["lat"]),
                                          (por["Lardeira"]["lon"], por["Lardeira"]["lat"])), 1)
    cifras["relevo"] = rel
    (CAPAS / "perfil.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {}, "geometry": {"type": "LineString",
                                                           "coordinates": [[x, y] for x, y, _ in pf[::10]]}}]},
        separators=(",", ":")), encoding="utf-8")
    cifras["perfil"] = [h for *_, h in pf[::10]]

    # --- 3. lumes de agosto de 2025 (EFFIS) -------------------------------------
    lf, tot_ou = [], 0
    for f in lumes["features"]:
        p = f["properties"]
        if p["ano"] != 2025 or not p["data_lume"].startswith("2025-08"):
            continue
        if p["provincia"] == "Ourense":
            tot_ou += p["area_ha"]
        if p["area_ha"] < 1000:
            continue
        aneis = [rnd(anel(r, 0.0015)) for r in f["geometry"]["coordinates"]]
        aneis = [r for r in aneis if len(r) >= 4]
        lf.append({"type": "Feature", "properties": {"c": p["concello"], "ha": p["area_ha"], "d": p["data_lume"]},
                   "geometry": {"type": "Polygon", "coordinates": aneis}})
    cifras["effis_ourense_agosto_2025_ha"] = tot_ou
    cifras["effis_lumes_maiores"] = sorted([(f["properties"]["c"], f["properties"]["ha"], f["properties"]["d"])
                                            for f in lf], key=lambda x: -x[1])[:8]
    (CAPAS / "lumes2025.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": lf},
                                                        ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # --- 4. superficie: media das máximas de xuño a agosto -----------------------
    nx = round((G_LON1 - G_LON0) / G_DLON)
    ny = round((G_LAT1 - G_LAT0) / G_DLAT)
    cache = AQUI / "data" / "alturas_grella.npy"
    if cache.exists():
        z = np.load(cache)
    else:
        z = mdt.grella_media(G_LON0, G_LAT1, G_DLON, G_DLAT, nx, ny)
        np.save(cache, z)
    sx = np.array([e["lon"] for e in conxs])
    sy = np.array([e["lat"] for e in conxs])
    sa = np.array([e["alt"] for e in conxs], dtype=float)
    sv = np.array([e["xja"] for e in conxs])
    s0 = sv + GRADIENTE * sa                     # levadas ao nivel do mar
    lon = G_LON0 + (np.arange(nx) + 0.5) * G_DLON
    lat = G_LAT1 - (np.arange(ny) + 0.5) * G_DLAT
    kx = 111.32 * np.cos(np.radians(42.8))
    k = 8
    t0 = np.zeros((ny, nx))
    for j0 in range(0, ny, 40):          # por bloques de filas, para non encher a memoria
        LON, LAT = np.meshgrid(lon, lat[j0:j0 + 40])
        d2 = ((LON[..., None] - sx) * kx) ** 2 + ((LAT[..., None] - sy) * 110.57) ** 2
        idx = np.argpartition(d2, k, axis=-1)[..., :k]
        dk = np.take_along_axis(d2, idx, -1)
        w = 1 / np.maximum(dk, 0.25)     # inverso do cadrado da distancia (km), k = 8 veciñas
        t0[j0:j0 + 40] = (w * s0[idx]).sum(-1) / w.sum(-1)
    t = t0 - GRADIENTE * np.maximum(z, 0)
    # máscara: só Galicia
    fora = json.loads((RAIZ / "assets" / "terreo" / "galicia-fora.geojson").read_text())
    mask = Image.new("L", (nx, ny), 0)
    dr = ImageDraw.Draw(mask)
    aneis = fora["features"][0]["geometry"]["coordinates"]
    px = lambda r: [((x - G_LON0) / G_DLON, (G_LAT1 - y) / G_DLAT) for x, y in r]
    dr.polygon(px(aneis[0]), fill=0)
    for r in aneis[1:]:
        dr.polygon(px(r), fill=255)
    m = np.array(mask) > 0
    rgba = np.zeros((ny, nx, 4), dtype=np.uint8)
    paleta = {}
    for j in range(ny):
        for i in range(nx):
            if m[j, i]:
                v = round(float(t[j, i]) * 4) / 4
                if v not in paleta:
                    paleta[v] = cor(v)
                rgba[j, i] = paleta[v]
    img = Image.fromarray(rgba, "RGBA")
    buf = io.BytesIO()
    img.quantize(colors=128, method=Image.Quantize.FASTOCTREE).save(buf, "PNG", optimize=True)
    (CAPAS / "calor-xja.png").write_bytes(buf.getvalue())
    cifras["superficie"] = {"nx": nx, "ny": ny, "bbox": [G_LON0, G_LAT0, G_LON1, G_LAT1],
                            "min": round(float(t[m].min()), 1), "max": round(float(t[m].max()), 1),
                            "kb": round(len(buf.getvalue()) / 1024)}

    # --- 5. miniatura -------------------------------------------------------------
    miniatura(t, m, z, est, nx, ny)

    (AQUI / "data" / "cifras.json").write_text(json.dumps(cifras, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: cifras[k] for k in ("top_max", "top_xja", "dia_10a", "relevo", "superficie",
                                             "effis_ourense_agosto_2025_ha")}, ensure_ascii=False, indent=1))


def miniatura(t, m, z, est, nx, ny):
    """Cadrado 600×600: a superficie como trama de puntos (máis grandes e vermellos canto máis
    quente) sobre fondo escuro, sen texto. Agrupados por cor para que pese pouco."""
    lon0, lon1, lat0, lat1 = -9.30, -6.75, 41.82, 43.80
    cl = math.cos(math.radians(42.8))
    esc = 560 / max((lon1 - lon0) * cl, lat1 - lat0)
    w, h = (lon1 - lon0) * cl * esc, (lat1 - lat0) * esc
    ox, oy = (600 - w) / 2, (600 - h) / 2
    grupos = {}
    paso_i, paso_j = 15, 20          # ~ 0,06° × 0,06°
    for j in range(paso_j // 2, ny, paso_j):
        for i in range(paso_i // 2, nx, paso_i):
            if not m[j, i]:
                continue
            lo = G_LON0 + (i + 0.5) * G_DLON
            la = G_LAT1 - (j + 0.5) * G_DLAT
            if not (lon0 <= lo <= lon1 and lat0 <= la <= lat1):
                continue
            v = float(t[j, i])
            r, g, b, _ = cor(max(v, 22.5))
            rad = round(1.6 + 4.6 * max(0, min(1, (v - 21) / 12)), 1)
            x = ox + (lo - lon0) * cl * esc
            y = oy + (lat1 - la) * esc
            grupos.setdefault(f"#{r:02x}{g:02x}{b:02x}", []).append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rad}"/>')
    partes = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">',
              '<rect width="600" height="600" fill="#0e1012"/>']
    for c, l in grupos.items():
        partes.append(f'<g fill="{c}">' + "".join(l) + "</g>")
    partes.append("</svg>")
    s = "".join(partes)
    (SAIDA / "thumb.svg").write_text(s, encoding="utf-8")
    print("thumb", round(len(s) / 1024), "KB")


if __name__ == "__main__":
    main()

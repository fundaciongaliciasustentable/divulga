#!/usr/bin/env python3
"""Converte o MDT de 25 m (data/raw/*.tif) en relevo terrain-RGB para MapLibre.

Fai o mesmo ca gdalwarp + rio-rgbify, sen GDAL: mosaico en EPSG:4258,
mostraxe bilineal para cada píxel das teselas Web Mercator e codificación
«mapbox» (altura = -10000 + (R·65536 + G·256 + B) · 0,1). Os zooms baixos
saen dunha pirámide de medias 2×2 para non facer aliasing.

Saída: data/galicia-terreo.mbtiles e, con `pmtiles convert`,
../../assets/terreo/galicia-terreo.pmtiles.

Uso (precisa numpy, tifffile e Pillow):
    python3 xerar.py [--max-zoom 12]
"""
import argparse
import io
import math
import sqlite3
import subprocess
from pathlib import Path

import numpy as np
import tifffile
from PIL import Image

AQUI = Path(__file__).resolve().parent
RAW = AQUI / "data" / "raw"
MBTILES = AQUI / "data" / "galicia-terreo.mbtiles"
PMTILES = AQUI.parent.parent / "assets" / "terreo" / "galicia-terreo.pmtiles"
BBOX = (-9.40, 41.75, -6.20, 43.85)   # oeste, sur, leste, norte (o visible nas pezas)
MIN_Z = 6


def mosaico():
    """Une os GeoTIFF nun só array int16 e devolve (array, oeste, norte, paso)."""
    pezas = []
    for f in sorted(RAW.glob("mdt25_*.tif")):
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
    m = np.zeros((alto, ancho), dtype=np.float32)
    for x0, y0, _, a in pezas:
        c, f = round((x0 - oeste) / paso), round((norte - y0) / paso)
        m[f:f + a.shape[0], c:c + a.shape[1]] = a
    print(f"mosaico {ancho}×{alto}, {len(pezas)} anacos, paso {paso:.7f}°")
    return m, oeste, norte, paso


def media2(a):
    h, w = a.shape[0] // 2 * 2, a.shape[1] // 2 * 2
    a = a[:h, :w]
    return (a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2]) / 4


def tile_xy(lon, lat, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def mostrar(niv, oeste, norte, paso, lons, lats):
    """Bilineal separable: lons (256,) e lats (256,) → alturas (256, 256).

    Fóra do mosaico a altura é 0, como o mar (sen estirar o bordo)."""
    cols_r = (lons - oeste) / paso - 0.5
    filas_r = (norte - lats) / paso - 0.5
    fora = ((filas_r < 0) | (filas_r > niv.shape[0] - 1))[:, None] | \
           ((cols_r < 0) | (cols_r > niv.shape[1] - 1))[None, :]
    cols = np.clip(cols_r, 0, niv.shape[1] - 1.001)
    filas = np.clip(filas_r, 0, niv.shape[0] - 1.001)
    c0, f0 = cols.astype(int), filas.astype(int)
    dc, df = (cols - c0)[None, :], (filas - f0)[:, None]
    a = niv[np.ix_(f0, c0)]
    b = niv[np.ix_(f0, c0 + 1)]
    c = niv[np.ix_(f0 + 1, c0)]
    d = niv[np.ix_(f0 + 1, c0 + 1)]
    h = (a * (1 - dc) + b * dc) * (1 - df) + (c * (1 - dc) + d * dc) * df
    h[fora] = 0
    return h


def codificar(h):
    v = np.round((h + 10000) * 10).astype(np.uint32)
    rgb = np.stack([(v >> 16) & 255, (v >> 8) & 255, v & 255], axis=-1).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(rgb, "RGB").save(buf, "WEBP", lossless=True, quality=100, method=4)
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-zoom", type=int, default=12)
    args = ap.parse_args()
    base, oeste, norte, paso = mosaico()

    # Pirámide: o nivel k ten paso·2^k. Para cada zoom úsase o nivel máis fino
    # que non sexa máis fino ca o píxel da tesela (≈ 28 m en z12 a 43° N).
    niveis = [(base, paso)]
    while len(niveis) < 8:
        a, p = niveis[-1]
        niveis.append((media2(a), p * 2))

    MBTILES.parent.mkdir(parents=True, exist_ok=True)
    MBTILES.unlink(missing_ok=True)
    db = sqlite3.connect(MBTILES)
    db.execute("CREATE TABLE metadata (name text, value text)")
    db.execute("CREATE TABLE tiles (zoom_level integer, tile_column integer, tile_row integer, tile_data blob)")
    meta = {"name": "galicia-terreo", "format": "webp", "type": "baselayer",
            "minzoom": MIN_Z, "maxzoom": args.max_zoom,
            "bounds": ",".join(map(str, BBOX)), "center": "-8.0,42.8,8",
            "attribution": "© Instituto Geográfico Nacional, MDT (PNOA-LiDAR), CC BY 4.0",
            "description": "terrain-RGB (codificación mapbox) do MDT25 do IGN"}
    db.executemany("INSERT INTO metadata VALUES (?, ?)", [(k, str(v)) for k, v in meta.items()])

    total = 0
    for z in range(MIN_Z, args.max_zoom + 1):
        x0, y0 = tile_xy(BBOX[0], BBOX[3], z)
        x1, y1 = tile_xy(BBOX[2], BBOX[1], z)
        px_m = 40075016.686 * math.cos(math.radians(42.8)) / (256 * 2 ** z)
        k = 0
        while k + 1 < len(niveis) and niveis[k + 1][1] * 111320 * math.cos(math.radians(42.8)) <= px_m:
            k += 1
        niv, p = niveis[k]
        n = 2 ** z
        for tx in range(int(x0), int(x1) + 1):
            lons = (tx * 256 + np.arange(256) + 0.5) / (256 * n) * 360 - 180
            for ty in range(int(y0), int(y1) + 1):
                yy = (ty * 256 + np.arange(256) + 0.5) / (256 * n)
                lats = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * yy))))
                h = mostrar(niv, oeste, norte, p, lons, lats)
                db.execute("INSERT INTO tiles VALUES (?, ?, ?, ?)",
                           (z, tx, n - 1 - ty, codificar(h)))
                total += 1
        print(f"z{z}: nivel {k} ({p * 111320 * math.cos(math.radians(42.8)):.0f} m), total {total}", flush=True)
    db.execute("CREATE UNIQUE INDEX tile_index ON tiles (zoom_level, tile_column, tile_row)")
    db.commit()
    db.close()

    PMTILES.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["pmtiles", "convert", str(MBTILES), str(PMTILES)], check=True)
    print(PMTILES, PMTILES.stat().st_size // 1024 // 1024, "MB")


if __name__ == "__main__":
    main()

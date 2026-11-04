#!/usr/bin/env python3
"""Descarga o MDT de 25 m do IGN (PNOA-LiDAR, CC BY 4.0 scne.es) para Galicia.

Pídese ao WCS INSPIRE en anacos de 0,5° (o servizo corta pedidos grandes) e
gárdanse como GeoTIFF en data/raw/. Cada anaco son ~2.222 × 2.222 celas de
int16 en EPSG:4258. Uso: python3 descargar.py
"""
import time
import urllib.request
from pathlib import Path

RAW = Path(__file__).resolve().parent / "data" / "raw"
WCS = ("https://servicios.idee.es/wcs-inspire/mdt?SERVICE=WCS&VERSION=2.0.1"
       "&REQUEST=GetCoverage&COVERAGEID=Elevacion4258_25"
       "&SUBSET=Lat({s},{n})&SUBSET=Long({w},{e})&FORMAT=image/tiff")
# Galicia con marxe: lon -9.40…-6.65, lat 41.75…43.85, e ata -6.0 para que
# Asturias e León (que o IGN tamén cobre) se vexan detrás do Courel e dos Ancares
LONS = [-9.5, -9.0, -8.5, -8.0, -7.5, -7.0, -6.5, -6.0]
LATS = [41.75, 42.25, 42.75, 43.25, 43.75, 43.85]


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    for i in range(len(LATS) - 1):
        for j in range(len(LONS) - 1):
            s, n, w, e = LATS[i], LATS[i + 1], LONS[j], LONS[j + 1]
            out = RAW / f"mdt25_{s:+.2f}_{w:+.2f}.tif"
            if out.exists() and out.stat().st_size > 10_000:
                continue
            url = WCS.format(s=s, n=n, w=w, e=e)
            for intento in range(3):
                try:
                    with urllib.request.urlopen(url, timeout=300) as r:
                        data = r.read()
                    if not data.startswith(b"II*"):
                        raise ValueError(data[:200])
                    out.write_bytes(data)
                    print(out.name, len(data) // 1024, "KB", flush=True)
                    break
                except Exception as err:  # noqa: BLE001 — reintenta e segue
                    print("erro", out.name, intento, err, flush=True)
                    time.sleep(5)
    (RAW / "DESCARGA.txt").write_text(
        f"MDT25 IGN (WCS INSPIRE Elevacion4258_25) descargado o {time.strftime('%Y-%m-%d')}\n",
        encoding="utf-8")


if __name__ == "__main__":
    main()

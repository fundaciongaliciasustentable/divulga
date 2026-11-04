# Relevo para os voos de cámara

`assets/terreo/galicia-terreo.pmtiles`: relevo terrain-RGB (codificación
«mapbox») para MapLibre, compartido por todas as pezas 3D de Divulga.

- Fonte: MDT de 25 m do IGN (PNOA-LiDAR), WCS INSPIRE `Elevacion4258_25`,
  licenza CC BY 4.0 (scne.es). Descargado o 4 de novembro de 2026.
- Cobertura: lon −9,5…−6,0, lat 41,75…43,85. Asturias e León entran porque o
  IGN cobre toda España; o mar e Portugal veñen a 0.
- Zooms 6–12 (en z12 o píxel mide ~28 m, a resolución do MDT); por riba,
  MapLibre amplía. 1.744 teselas WebP sen perdas, ~66 MB.

## Rexenerar

O `.pmtiles` non vai ao git (está no `.gitignore`) para non engordar o
historial. Nun clon novo hai que xeralo antes de `./scripts/empaquetar.sh`;
se non, o paquete sae sen relevo e os voos quedan en negro.

```bash
python3 descargar.py                 # 35 GeoTIFF en data/raw/ (~290 MB, non van ao git)
python3 xerar.py                     # precisa numpy, tifffile e Pillow, e o CLI pmtiles
```

`xerar.py` fai o traballo de `gdalwarp` + `rio rgbify` sen GDAL: mosaico,
pirámide de medias 2×2 para os zooms baixos, mostraxe bilineal en Web
Mercator e `pmtiles convert`.

## Pendente

- Portugal a 0 deixa un cantil no Miño. Para pezas no sur, recortar co
  contorno de Galicia ou encher con outro MDT.
- O servidor de proba precisa atender peticións Range (PMTiles);
  `python3 -m http.server` non o fai. Apache en Dinahosting si.

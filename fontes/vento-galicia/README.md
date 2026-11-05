# O vento que move Galicia (`vento-galicia`)

Voo de cámara sobre o relevo (motor común `assets/js/voo.js`) polas serras dos
parques eólicos: onde están, por que alí, o conflito coa Rede Natura, a
repotenciación e as zonas de eólica mariña do POEM.

## Rexenerar

```bash
# python con numpy, tifffile, imagecodecs e shapely (o venv das pezas de voo vale)
python -I fontes/vento-galicia/prep.py    # capas/*.geojson e data/cifras.json (descarga o que falte en data/raw/)
python -I fontes/vento-galicia/thumb.py   # v/vento-galicia/thumb.svg
python3 fontes/vento-galicia/render.py    # v/vento-galicia/index.html e fontes/vento-galicia/datos.json
```

`data/raw/` (descargas en bruto, ~110 MB) non vai ao git. O MDT de 25 m lese de
`fontes/terreo/data/raw/`.

## Capas (`v/vento-galicia/capas/`)

| capa | contido | peso |
|---|---|---|
| `aeroxeradores.geojson` | 4.077 aeroxeradores de OSM en dous MultiPoint (`rn`=1 dentro da Rede Natura, 0 fóra) | ~71 KB |
| `vento.geojson` | grella de 0,04° en terra galega, media do Global Wind Atlas a 100 m, agrupada en clases de 0,25 m/s | ~29 KB |
| `rede-natura.geojson` | espazos Rede Natura que tocan Galicia, simplificados (0,006°) e recortados á costa | ~178 KB |
| `zaper.geojson` | polígonos NOR-1 a NOR-5 do POEM | ~1 KB |

## Fontes (consultadas o 4 de novembro de 2026)

- **OpenStreetMap**, Overpass API (`overpass-api.de`), ODbL 1.0.
  `node["generator:source"="wind"](area ES-GA)` → `data/raw/osm_aeroxeradores.json`;
  de 4.095 nodos, 4.081 son `power=generator` (12 `power=proposed`, 2 sen `power`) e 4.077
  deles están dentro do contorno de Galicia. Parques: `nwr["power"="plant"]["plant:source"="wind"]`
  → `data/raw/osm_parques.json` (174; só para consulta). Base do timestamp: 2026-11-04T08:33Z.
  OSM non é un rexistro oficial: pode haber aeroxeradores sen cartografar ou xa desmontados
  (p. ex. os retirados nas repotenciacións recentes).
- **Global Wind Atlas 3** (DTU Wind Energy e Banco Mundial), CC BY 4.0:
  `https://gwa.cdn.nazkamapps.com/country_tifs_v4/ESP_wind-speed_100m.tif` (velocidade media
  a 100 m, celas de 0,0025°).
- **Rede Natura 2000**: MITECO, Banco de Datos de la Naturaleza, edición 2024, copia de Mapas
  Galicia Sustentable `https://mapas.galiciasustentable.org/data/rede-natura/data.geojson`
  (76 espazos; a capa local de mapasgs estaba en erro). Reutilización co aviso legal do MITECO.
- **ZAPER (POEM)**: polígonos `Alto_Potencial_Energia_Eolica_ZAPER_20230215_NOR_*` da capa
  `emodnet:mspzoningpoly` de EMODnet Human Activities (WFS, CC BY 4.0), orixe MITECO. A descarga
  directa do MITECO (`gis.miteco.gob.es/descargas/...zaper.zip`) cortaba a conexión.
  Superficies da **táboa 27 do RD 150/2023** (BOE-A-2023-5704, `data/raw/boe_rd150_2023.pdf`, p. 132-133):
  NOR-1 117,63 · NOR-2 1.806,41 · NOR-3 112,97 · NOR-4 77,70 · NOR-5 236,29 km² → **2.351,00 km²**.
  NOR-6 a NOR-8 quedan fronte a Asturias (centroides a leste de 7,03° O). Criterio de vento
  > 7,5 m/s a 100 m: mesma norma, apartado 4.5.1. Vixencia ata o 31/12/2027: campo `validto` de EMODnet.
- **INEGA**, *Potencia instalada en Galicia* (xuño 2026),
  `https://www.inega.gal/sites/default/files/publicacions/evolucion_potencia-202606.pdf`:
  eólica 4.027 MW en 2025 (2.364 en 2005 → +70,3 %); eólica = 48,4 % da potencia renovable;
  C. T. das Pontes 1.403 MW ata 2023 e 0 en 2024.
- **INEGA**, memoria da *Modificación del Plan Sectorial Eólico de Galicia*
  (`https://www.inega.gal/sites/default/files/2023-12/242-d-memoria.pdf`, p. 11-14): Estaca de
  Bares 1987, 12 máquinas de 30 kW; Cabo Vilán finais de 1989, 100 e 200 kW; Decreto 205/1995;
  Plan Eólico de Galicia aprobado o 1/10/1997; 660 MW a finais de 2000.
- **Cabo Vilán 2016**: Ecoticias, 15/9/2016 (22 aeroxeradores substituídos por 2 de 3 MW).
- **Repotenciación**: Xunta de Galicia, nota do 6/6/2025
  (`xunta.gal/gl/notas-de-prensa/-/nova/013596/...`): nove proxectos, 361 → 75 aeroxeradores,
  615.000 → 828.000 MWh/ano (+35 %), «practicamente a mesma potencia». Nota do 19/5/2026
  (`xunta.gal/notas-de-prensa/-/nova/024633/...`): unha vintena en trámite, 626 aeroxeradores
  retirados; As Somozas 81 → 9 e 168 GWh/ano; Monte Redondo 66 → 11.
- **TJUE**, sentenza do 1/8/2025, asunto C-461/24 (ECLI:EU:C:2025:620), cuestión prexudicial do
  TSXG sobre os informes sectoriais na tramitación ambiental.
- **Xeración 2025**: Red Eléctrica, REData, sistema eléctrico de Galicia (datos de
  `fontes/luz-galicia/data/datos.json`): eólica 8.609 GWh de 21.292 → 40,4 %.
- **Relevo e contorno**: IGN, MDT 25 m (PNOA-LiDAR) e contorno de `assets/terreo/`, CC BY 4.0.

## Cálculos FGS (`prep.py` → `data/cifras.json`)

- Altura de cada aeroxerador: MDT de 25 m. Media 691 m (mediana 676); 78,5 % por riba de 500 m.
- Altura media de Galicia: MDT mostraxeado cada 200 m dentro do contorno → 501 m; 45,0 % por riba de 500 m.
- Vento: GWA no punto de cada aeroxerador → media 8,8 m/s; 98,6 % en celas ≥ 7 m/s.
  En toda a terra galega (celas de 250 m dentro do contorno): media 6,0 m/s; 22,4 % ≥ 7 m/s.
- Rede Natura: unión dos espazos (xeometría completa) intersecada co contorno → 12,0 % da
  superficie; 1.210 aeroxeradores dentro (29,7 %). Por espazo: Serra do Xistral 650, Serra do
  Candán 150, Serra do Cando 87, Costa Ártabra 83, Carnota-Monte Pindo 58…
- Recadros das paradas (lon/lat, conta de aeroxeradores, altura media, vento medio, altura máxima do MDT):
  - Costa da Morte −9,25…−8,80 / 43,03…43,33: 211 (non se usa no texto).
  - Paxareiras −9,20…−8,80 / 42,80…43,02 (33 × 24 km): 419; 472 m; 9,0 m/s.
  - Xistral −7,80…−7,38 / 43,40…43,58 (34 × 20 km): 1.068 (26,2 % do total); 749 m; 9,5 m/s;
    máximo 1.055 m en −7,5488 43,4704 (Cadramón).
  - Faladoira −8,00…−7,73 / 43,56…43,73: 288; 9,5 m/s; máximo 613 m en −7,7983 43,5740.
  - Testeiro −8,30…−8,00 / 42,48…42,62: 165; 874 m; 8,6 m/s.
  - Suído −8,40…−8,20 / 42,24…42,40: 158; 1.001 m; 8,6 m/s.
- ZAPER: 2.351 km² é a suma da táboa 27 do BOE (EMODnet dá 2.352,7 km² cos seus polígonos).

## Advertencias

- As contas de aeroxeradores dependen da completitude de OSM e dos recadros escollidos.
- O Global Wind Atlas é un modelo de vento medio de longo prazo; non se usou a capa
  `vento-wrf` (predición dun día).
- `datos.json` xérase en `render.py` lendo as paradas do HTML: está sempre sincronizado.

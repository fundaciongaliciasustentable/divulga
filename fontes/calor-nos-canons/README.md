# A calor que baixa aos vales (`v/calor-nos-canons/`)

Voo 3D sobre o relevo: por que os vales encaixados do interior (Miño, Sil, Támega,
depresión de Lemos) foron os lugares máis quentes de Galicia en 2025.

## Rexenerar

```bash
python3 prep.py      # precisa numpy, tifffile e Pillow; le o MDT de ../terreo/data/raw/
python3 render.py    # v/calor-nos-canons/index.html e datos.json
```

`prep.py` copia en `data/raw/` as capas `tmax-ano` e `historial-queimados` de
`~/Proxectos/mapasgs/site/public/data/` se aínda non están (foto do 04/11/2026) e
escribe `data/cifras.json` con todas as cifras calculadas. `data/` non vai ao git.

Saídas en `v/calor-nos-canons/`: `capas/estacions.geojson` (27 KB),
`capas/lumes2025.geojson` (45 KB), `capas/perfil.geojson` (1 KB),
`capas/calor-xja.png` (78 KB, superficie que se pinta como capa `image` en `aoCargar`)
e `thumb.svg` (39 KB).

## Fontes

| Dato | Fonte | Consulta |
|---|---|---|
| Máximas diarias de 2025 de 169 estacións | MeteoGalicia e Consellería de Medio Ambiente e Cambio Climático, `datosDiariosEstacionsMeteo` (`TA_MAX_1.5m`, só validadas, código 1), vía capa `tmax-ano` de Mapas Galicia Sustentable (colección CC BY-SA 4.0; meta en `data/raw/tmax-ano.meta.json`) | 04/11/2026 |
| Contraste das cifras clave | O mesmo servizo pedido directamente para xuño e agosto de 2025: `https://servizos.meteogalicia.gal/mgrss/observacion/datosDiariosEstacionsMeteo.action?dataIni=2025-08-01&dataFin=2025-08-31&idParam=TA_MAX_1.5m` (e xuño). Gardado en `data/raw/meteogalicia_tamax_2025-0{6,8}.json`. Coincide coa capa (a capa redondea a 0,1) | 04/11/2026 |
| Observatorio de Ourense (41,3 e 41,6 °C o 29 e 30/06/2025; récord de xuño anterior 40,9 °C, 2011) | AEMET, avance climatolóxico mensual de Galicia, xuño de 2025 (4/7/2025): `https://www.aemet.es/documentos/es/serviciosclimaticos/vigilancia_clima/resumenes_climat/ccaa/galicia/avance_climat_gal_jun_2025.pdf` | 04/11/2026 |
| Ribadavia 42,8 °C o 4/8/2025, máxima absoluta do mes en Galicia | AEMET, avance climatolóxico de Galicia, agosto de 2025 (3/9/2025, datos provisionais): `.../avance_climat_gal_ago_2025.pdf` | 04/11/2026 |
| Perímetros de lumes de agosto de 2025 | Copernicus EFFIS (JRC), CC BY 4.0, vía capa `historial-queimados` de Mapas Galicia Sustentable | 04/11/2026 |
| Alturas e desniveis | MDT de 25 m do IGN (PNOA-LiDAR), CC BY 4.0, `../terreo/data/raw/` | descarga 04/11/2026 |

## Cada cifra da peza

Todas saen de `data/cifras.json` (cálculo FGS sobre os datos anteriores) salvo as de AEMET.

- **Paso 1.** 33,6 °C: media das 92 máximas diarias de xuño a agosto de 2025 da estación
  Ourense (143 m), a maior entre as 162 estacións con ≥ 85 días de dato no verán. O Xistral
  (Muras) 18,9 °C e Camariñas 20,7 °C, mesmo cálculo. 169 estacións na capa.
- **Paso 2.** Ourense: 42,9 °C (42,88) o 29/06/2025; 93 días ≥ 30 °C e 48 días ≥ 35 °C en
  2025 (365 días con dato). «Serras que pasan dos 700»: máximo do MDT 728 m nun rectángulo de
  ±0,12° lon × ±0,09° lat arredor de (−7,86; 42,34). AEMET: ver táboa.
- **Paso 3.** EVEGA Leiro (105 m): 50 días ≥ 35 °C, o máximo da rede (Ourense 48);
  41,8 °C (41,75) o 30/06. Remuíño (A Arnoia): 41,8 °C (41,75) o 04/08. Miño a uns 65 m: mínimo
  do MDT (65 m) en ±0,08° × ±0,07° arredor de (−8,12; 42,29). AEMET Ribadavia: ver táboa.
- **Paso 4.** Canón do Sil: mínimo 226 m e máximo 812 m do MDT nun rectángulo de ±0,03° lon ×
  ±0,015° lat (~5 × 3 km) arredor de (−7,56; 42,39); 812 − 226 = 586 m.
- **Paso 5.** San Clodio (Ribas de Sil, 257 m): 42,95 °C o 10/08/2025, a máxima do ano en
  toda a rede (a capa dá 43,0).
- **Paso 6.** Conchada (Quiroga, 697 m): 38,95 °C o 10/08/2025; diferenza 4,0 °C;
  440 m de desnivel entre estacións (altitudes de MeteoGalicia; MDT: 257 e 693 m);
  3,4 km en liña recta; 0,44 km × 6,5 °C/km = 2,9 °C.
- **Paso 7.** Monforte-CFEA (320 m): 41,0 °C (41,04) o 29/06, 72 días ≥ 30 °C. Míllara
  (Pantón, 340 m): 41,0 °C o 10/08, 73 días ≥ 30 °C. Monforte (286 m).
- **Paso 8.** A Portela (Vilamartín de Valdeorras, 408 m): 41,3 °C (41,27) o 09/08, 41,2
  (41,21) o 10/08, 41 días ≥ 35 °C. Lardeira (Carballeda de Valdeorras, 1.620 m): 30,3 °C o
  10/08; 20,6 km entre estacións.
- **Paso 9.** Verín-Vilela (392 m): 73 días ≥ 30 °C; 40,2 °C (40,18) o 09/08. Verín-Vilamaior
  (546 m): 38,9 °C o 09/08.
- **Paso 10.** 10/08/2025, 168 estacións con dato: 10 con ≥ 40 °C (San Clodio, A Portela,
  Míllara, As Petarelas, EVEGA Leiro, Monforte, Larouco, Monforte-CFEA, Ourense, Laza).
  Cabeza de Manzaneda (1.758 m) 29,1 °C (29,14), a 22,5 km de San Clodio; 43,0 − 29,1 = 13,9.
  Camariñas 27,0 °C (26,99). Foz 21,9 °C, a máis baixa dese día.
- **Paso 11.** 139.735 ha: suma de `area_ha` dos perímetros EFFIS con `ano` 2025,
  `data_lume` en agosto e `provincia` Ourense. Datas de inicio dos lumes > 1.000 ha: do 08/08
  (Manzaneda) ao 15/08 (A Veiga, Carballeda de Avia). Denominacións de orixe de viño de
  Galicia: Rías Baixas, Ribeiro, Ribeira Sacra, Valdeorras e Monterrei (Consellería do
  Medio Rural); as catro últimas están nos vales do percorrido.

## Superficie (`calor-xja.png`)

Media das máximas de xuño a agosto de 2025 en cada estación con ≥ 85 días de dato, levada ao
nivel do mar con 6,5 °C/km (altitude da estación segundo MeteoGalicia), interpolada polo
inverso do cadrado da distancia coas 8 estacións máis próximas e devolta á altura media do MDT
de cada cela (0,004° × 0,003°, ~330 m). Recortada coa máscara de Galicia do IGN. É o mesmo
método ca a páxina `/pulso/calor/` de Mapas Galicia Sustentable. Non recolle inversións
térmicas nin efectos de abrigo, así que no fondo dos vales pode quedar curta (no paso 6, San
Clodio e Conchada separáronse 4,0 °C cando o gradiente estándar daría 2,9).

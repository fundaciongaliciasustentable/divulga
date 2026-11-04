# Da Costa da Morte ao Courel

Voo 3D (motor común `assets/js/voo.js`) de oeste a leste sobre o relevo de Galicia: título,
once paradas e peche. Datos consultados o **4 de novembro de 2026**.

## Rexenerar

```bash
cd fontes/costa-morte-courel
PY=python3                                   # con numpy, tifffile e shapely
$PY prep.py      # capas → v/costa-morte-courel/capas/*.geojson e cifras.json
python3 render.py   # peza.tpl.html → v/costa-morte-courel/index.html e datos.json
$PY thumb.py     # v/costa-morte-courel/thumb.svg (usa datos.json e o MDT)
```

`prep.py` copia as capas de Mapas Galicia Sustentable desde `~/Proxectos/mapasgs/site/public/data/`
(ou as descarga de `https://mapas.galiciasustentable.org/data/<capa>/`) a `data/raw/<capa>/`, e
descarga a táboa 62 do IGE a `data/raw/ige_62.csv`. **`data/raw/` non vai ao git.** As alturas
saen do MDT de `../terreo/data/raw/` (ver `../terreo/README.md`).

As cifras do texto escríbense a man no modelo; `prep.py` deixa en `cifras.json` todos os valores
calculados para comprobalas. `render.py` extrae as paradas do HTML a `datos.json` (nome, cámara,
capa, dato e fonte), así que sempre están sincronizadas.

## De onde sae cada cifra

| Parada | Cifra | Fonte e cálculo |
|---|---|---|
| 1 Fisterra | 237 m | Máximo do MDT 25 m do IGN (WCS `Elevacion4258_25`, CC BY 4.0, descargado o 4/11/2026) no recadro −9,29…−9,26 / 42,87…42,90 (Monte Facho). `cifras.json` → `mdt.monte_facho` |
| 2 Costa da Morte | 4,3 m/s (Touriñán), 2,4 m/s (Santiago) | Capa `vento-wrf`: MeteoGalicia, WRF 4 km, ficheiro `wrf_2d_04km/fmrc/files/20261104/wrf_arw_det_history_d03_20261104_0000.nc4` (execución 4/11/2026 00 UTC), remostrado a grella 0,03° por Mapas GS. Media da velocidade √(u²+v²) dos 25 pasos de 3 h (4/11 00 UTC – 7/11 00 UTC) na celda máis próxima a −9,297, 43,05 e −8,545, 42,88. Cálculo FGS. É unha predición, non clima |
| 3 Pindo e Xallas | ×5,3 (3,049 → 16,127 m³/s) | Capa `crecida-episodios` (Augas de Galicia e MeteoGalicia, caudais de 10 min non validados, `servizos.meteogalicia.gal/mgafos/json/datos10min.action`), episodio 5–11/10/2026, estación 140760 «Xallas - Mazaricos»: `caudal_base` e `caudal_pico` (pico o 6/10/2026 20:00 UTC). A Moa 627 m: máximo do MDT en −9,16…−9,09 / 42,86…42,92. Encoros: nomes das masas de auga ES-014-MR-184-000-03-* da capa `estado-masas-auga` (Augas de Galicia, Plan hidrolóxico Galicia-Costa 2021–2027, CC BY-SA 4.0) |
| 4 Soneira e Xallas | 426 de 463; 38.906 → 29.185; 4 baleiras | Capa `aldeas-baleiras` (INE, Nomenclátor `Nacional_2025.zip`, 2000–2025; posicións IET; CC BY-SA 4.0). Concellos 15016 Camariñas, 15092 Vimianzo, 15093 Zas, 15077 Santa Comba e 15045 Mazaricos. Conta de unidades con `pob` < `pob_2000`, sumas de `pob_2000` e `pob`, e unidades con `pob` = 0. 48 sen posición (contan, non se debuxan) |
| 5 Santiago | Ames 10.011 (1991) → 32.062 (2021), ×3,2; Santiago 87.807 → 97.798 (+11 %); Teo 12.607 → 18.846 (+49 %) | Capa `poboacion-seculo` (INE, «Alteraciones de los municipios en los Censos de Población desde 1842», harmonizada aos concellos actuais por Mapas GS). Mapa: variación 1991–2021 de 18 concellos da área sobre os límites de `concellos-parroquias` (IET, CC BY-SA 4.0) |
| 6 Pico Sacro e Ulla | 1.633 ha; Pico Sacro 527 m | Capa `espazos-naturais-galicia` (IET, IDEG `LugaresProtexidos/EN_EspazosProtexidos`, CC BY-SA 4.0): `superficie_ha` da ZEPVN «Sistema Fluvial Ulla-Deza». Altura: máximo do MDT en −8,48…−8,42 / 42,78…42,83 |
| 7 Deza | Lalín 45,3 vacas/km² (14.794 / 326,8 km²); Galicia 17,3 (511.138 / 29.540,9 km²); Frades 122,1, Pastoriza 87,0, Mesía 70,8 | IGE táboa 62 (`https://www.ige.gal/igebdt/igeapi/csv/datos/62`, «Número de vacas», 2025, consultada o 4/11/2026) entre `superficie_km2` da capa `perfil-concellos` (superficie do IGE). Cálculo FGS |
| 8 Ribeira Sacra | 460 m (207 → 669 m) | Mínimo e máximo do MDT en −7,76…−7,66 / 42,58…42,66 (cadrado de ~8 × 9 km arredor de Belesar) |
| 9 Monforte | 27 días ≥ 35 °C; 40,5 °C o 10/8/2025; Camariñas 0 días, máx. 27 °C o 10/8/2025 | Capa `tmax-ano` (MeteoGalicia, datos diarios das estacións, ano 2025): estacións «Monforte» (286 m, 365 días con dato) e «Camariñas» (365 días). Días con `tmax` ≥ 35,0. O mapa amosa as 165 estacións con 330 días ou máis |
| 10 Courel | 1.639 m; 13.612 ha, 73 % Natura 2000, 14/7/2022 | Altura: máximo do MDT en −7,12…−7,08 / 42,59…42,62. Lume: capa `historial-queimados` (Copernicus EFFIS `modis.ba.poly`, CC BY 4.0), perímetro id 206702: `area_ha`, `pct_natura2000`, `data_lume`. Mapa: perímetros 2016–2025 con centroide en −7,45…−6,85 / 42,35…42,85 |
| 11 Folgoso do Courel | 45 % (45,02) de 65+ en 2025, Galicia 26,88; censos 1950 5.659 e 2021 988; Seoane 149 → 87; 39 de 47 lugares perderon xente, 2 baleiros | Idade: capa `indicadores-concellos` (IGE, `maiores_65_pct`, 2025). Censos: `poboacion-seculo` (INE). Lugares: `aldeas-baleiras` (concello 27017) |
| Peche | 180 km | Distancia en liña recta Fisterra–Formigueiros (−9,27, 42,88 → −7,10, 42,61), cálculo FGS |

## Capas (`v/costa-morte-courel/capas/`)

| Ficheiro | Contido | Propiedades |
|---|---|---|
| `vento.geojson` | grella 0,03° do WRF, −9,75…−8,2 / 42,6…43,55 | `v` vento medio (m/s) |
| `xallas.geojson` | curso principal e encoros do Xallas, estacións de aforo | `t` (rio/encoro/estacion), `x` |
| `aldeas-soneira.geojson`, `aldeas-courel.geojson` | lugares con posición | `p` poboación 2025, `e` 0 baleira · 1 perdeu · 2 igual ou gañou |
| `santiago.geojson` | 18 concellos da área de Santiago | `v` variación 1991–2021 (%) |
| `ulla.geojson` | ZEPVN Sistema Fluvial Ulla-Deza | — |
| `vacas.geojson` | os 313 concellos, simplificados (0,016°) | `v` vacas/km² 2025 |
| `tmax.geojson` | estacións de MeteoGalicia | `d` días ≥ 35 °C en 2025 |
| `lume.geojson` | perímetros EFFIS 2016–2025 do leste de Lugo | `a` ano |

## Licenza

CC BY-SA 4.0: a peza usa capas con esa licenza (`aldeas-baleiras`, `concellos-parroquias`,
`espazos-naturais-galicia`, `estado-masas-auga`).

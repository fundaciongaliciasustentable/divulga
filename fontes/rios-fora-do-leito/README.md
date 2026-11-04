# Cando os ríos saen do leito (`rios-fora-do-leito`)

Voo de cámara (Divulga, motor `assets/js/voo.js`) sobre a crecida do 5–11 de outubro de 2026 e as
zonas inundables de 10, 100 e 500 anos. 11 paradas.

## Rexenerar

```bash
cd fontes/rios-fora-do-leito
pip install numpy pillow tifffile shapely      # e os binarios pmtiles e tippecanoe-decode
python3 prep.py      # data/raw/ (descargas, non van ao git) → ../../v/rios-fora-do-leito/capas/*.geojson e data/cifras.json
python3 render.py    # peza.tpl.html → ../../v/rios-fora-do-leito/index.html e datos.json
python3 thumb.py     # ../../v/rios-fora-do-leito/thumb.svg
```

`prep.py` le as capas de Mapas Galicia Sustentable da copia local (`~/Proxectos/mapasgs/site/public/data/`)
ou, se non existe, de `https://mapas.galiciasustentable.org/data/<capa>/`, e garda unha copia en
`data/raw/`. Tamén precisa `~/Proxectos/mapasgs/build/galicia.pmtiles` (mapa base) e o MDT de
`fontes/terreo/data/raw/`. Todo o que descarga queda en `data/raw/` (con caché).

## Capas (`v/rios-fora-do-leito/capas/`)

| capa | contido | orixe |
|---|---|---|
| `rede.geojson` | ríos de máis de ~8 km dentro de Galicia, `p=1` os principais | mapa base de mapasgs (`galicia.pmtiles`, capa `water`, `kind=river`, zoom 9), © OpenStreetMap (ODbL); recortado con `assets/terreo/galicia-fora.geojson` |
| `rios-crecida.geojson` | masas de auga fluviais de Galicia-Costa agrupadas pola razón `r` (pico/base, truncada a 0,5) da súa estación | `crecida-episodios` (tipo `rio`) |
| `estacions.geojson` | 67 estacións de aforo: `base`, `pico`, `r` (só se base ≥ 0,1 m³/s), `marea` | `crecida-episodios` (tipo `estacion`) |
| `choiva.geojson` | 150 estacións con choiva diaria completa: `mm` total 5–10/10/2026 | `crecida-episodios` (tipo `choiva`) |
| `zi-t10/-t100/-t500.geojson` | zonas inundables por lugar (`betanzos`, `padron`, `pontevea`, `ourense`, `obarco`) | Galicia-Costa: IDEG (vector); Miño e Sil: teselas PNG do SNCZI vectorizadas |

## De onde sae cada cifra

Consultas do 04/11/2026. As horas pasáronse de UTC á hora oficial (UTC+2 en outubro de 2026).

**Crecida** — capa `crecida-episodios` de Mapas Galicia Sustentable (publicada o 11/10/2026, gardada
o 04/11/2026), que recolle os caudais de 10 min *non validados* de Augas de Galicia e MeteoGalicia
(`servizos.meteogalicia.gal/mgafos/json/datos10min.action`, parámetro `CAMed_AVG_0m`), en medias
horarias, e a choiva diaria das estacións de MeteoGalicia (`datosDiariosEstacionsMeteo.action`).
`caudal_base` = mediana das primeiras 24 h do episodio (5/10); `caudal_pico` = máxima media horaria.
Nomes das estacións de choiva: capa `estacions-meteo` (CC BY-SA 4.0).

| parada | cifra | cálculo |
|---|---|---|
| 1 | 65,6 mm en Santa Cruz (O Valadouro), a máis alta de 150 | suma dos seis valores de `choiva_dia` (5–10/10), estación 10167; as estacións cun día sen dato quedan fóra (1 de 151) |
| 1 | Baiona 61,3 mm o 6/10; Foz 61 mm (45 + 16) | `choiva_dia` das estacións 10169 e 10103 |
| 1 | a metade non pasou de 13 mm | mediana dos totais (13,0 mm), cálculo FGS |
| 1 | case toda a auga o 6 e o 7 | o 99,4 % da choiva sumada das 150 estacións caeu eses dous días, cálculo FGS |
| 2 | 18 de 45 estacións dobraron o caudal | estacións con `caudal_base` ≥ 0,1 m³/s e sen marea (45 de 67); 18 con pico/base ≥ 2. Cálculo FGS |
| 2 | Tambre en Trazo: 1,9 → 2,0 m³/s | `caudal_base` 1,931, `caudal_pico` 2,003 |
| 3 | Eume en Monfero: 2,0 → 16,6 m³/s (×8,3), 7/10 ás 8 h | estación 141380; pico 06:00 UTC. É a razón máis alta entre as 45 estacións do paso 2 |
| 4 | Ulla en Teo: 16,7 m³/s o 7/10 | estación 140540, `caudal_pico` 16,741 (12:00 UTC) |
| 4 | 1.622,2 m³/s, crecida de 100 anos | campo `Q_M3_S` da lámina T100 `ES014-T100-CP-05-03-12-01` (Río Ulla, estudo Ulla-Pontevea) |
| 4 | «case cen veces menor» | 1.622,2 / 16,741 = 96,9 |
| 4 | 83 ha | área da unión das láminas T100 da ARPSI ES014-CP-05-03-12 (proxección local), cálculo FGS |
| 5 | 2.417 persoas (T100) e 202 (T10) en Padrón | capa «Risco poboación T100/T10» do IDEG (6 e 5), ARPSI ES014-CP-05-02-11, suma de `NUM_AFE_ZI` dos polígonos do concello de Padrón (poboación de 2019). Non se usa `NUM_AFE_MU`, que repite o total do concello en todas as súas ARPSI |
| 5 | «multiplícase por doce» | 2.417 / 202 = 12,0 |
| 5 | Sar en Brión ×6 | estación 140560: 0,535 → 3,191 m³/s (×5,96) |
| 6 | Xallas en Mazaricos: 3,0 → 16,1 m³/s, 6/10 ás 22 h | estación 140760: 3,049 → 16,127 (20:00 UTC) |
| 7 | Ourense: 183 / 259 / 321 ha (T10/T100/T500) | teselas z13 de `inundacion-perigo-t10/-t100/-t500` (SNCZI, MITECO) no recadro lon −7,93…−7,80, lat 42,29…42,39; píxeles con alfa > 127 × área do píxel no chan. Aproximado (píxel ~14 m) |
| 8 | O Barco: 306 / 427 / 525 ha | igual, recadro lon −7,10…−6,885, lat 42,37…42,46 (o tramo inundable do Sil vai de −7,097 a −6,889: uns 17 km en liña recta) |
| 9 | Betanzos: 1.327 / 1.600 / 1.752 persoas | risco poboación T10/T100/T500, ARPSI ES014-CO-12-01-01, suma de `NUM_AFE_ZI` do concello de Betanzos (poboación de 2019) |
| 9 | 99 ha (T10), +20 ha (T500: 119) | área das láminas IDEG (98,6 e 118,6 ha), cálculo FGS |

Todas as cifras calculadas están en `data/cifras.json` (saída de `prep.py`).

**Zonas inundables de Galicia-Costa** — Augas de Galicia, servizo ArcGIS
`https://ideg.xunta.gal/servizos/rest/services/IDE_DHGC/D2007_60_MapasInundFluv_21_27/MapServer`
(capas 2–4 láminas T10/T100/T500, 5–7 risco para a poboación), ciclo 2021–2027, `FECHA_APRO`
05/03/2021. Consultas `query` por `ID_ZONA LIKE 'ES014-T010|T100|T500-<ARPSI>-%'` e
`COD_ARPSI = 'ES014-<ARPSI>'`, `outSR=4326`. Licenza: aviso legal de Augas de Galicia (reutilización
citando a fonte).

**Zonas inundables do Miño e do Sil** — SNCZI (MITECO), CC BY 4.0. Non hai servizo vectorial
accesible (a descarga `laminasPB-q100.zip` de MITECO e o WFS non responderon o 04/11/2026), así que
se vectorizan as teselas PNG que Mapas Galicia Sustentable xa aloxa (`inundacion-perigo-*/data.pmtiles`,
teselas do 11/03/2026), lidas con `pmtiles tile`.

**Relevo** — MDT 25 m do IGN (CC BY 4.0), a través do motor común.

## Notas e límites

- Os caudais son datos en tempo real *non validados*. As estacións de Padrón (Ulla e Sar) seguen a
  marea e quedan fóra das comparacións; tamén as de caudal base < 0,1 m³/s, onde a razón dispárase
  (Baltar, en Sanxenxo, 0,009 → 21 m³/s).
- A rede de aforos da capa é a de Galicia-Costa; os ríos do Miño-Sil (Confederación Hidrográfica do
  Miño-Sil) non teñen datos no episodio.
- Os mapas de perigo só cobren as ARPSI (áreas con risco potencial significativo), non todos os ríos.

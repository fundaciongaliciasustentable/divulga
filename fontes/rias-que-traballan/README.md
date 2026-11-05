# As rías que traballan

Voo de cámara (Divulga, `v/rias-que-traballan/`) polas rías galegas: zonas de produción de
moluscos, polígonos de bateas, lonxas e marisqueo, estado das augas e costa inundable.

## Rexenerar

```bash
python3 fontes/rias-que-traballan/prep.py     # precisa shapely; descarga en data/raw/ o que falte
python3 fontes/rias-que-traballan/render.py   # escribe v/rias-que-traballan/index.html e datos.json
```

- `prep.py` → `v/rias-que-traballan/capas/*.geojson` (zonas, bateas, lonxas, augas, inundacion;
  todas < 200 KB), `v/rias-que-traballan/thumb.svg` e `data/cifras.json` (todas as cifras calculadas).
- `render.py` → a peza desde `peza.tpl.html` (barra e pé de `v/galicia-cero-neto/`, licenza
  CC BY-SA 4.0) e `datos.json` (as paradas extraídas do propio HTML, sempre sincronizadas).
- `data/raw/` non vai ao git.

## Fontes (descargadas o 4/11/2026)

| Ficheiro en `data/raw/` | Orixe | Licenza |
|---|---|---|
| `mgs/zonas-producion-moluscos/` | https://mapas.galiciasustentable.org/data/zonas-producion-moluscos/data.geojson (de Augas de Galicia, IDEG `PHGC2021_2027_ZProtex_NEuropeo/MapServer`, subcapas 1 e 2; colleita de MGS do 1/11/2026) | CC BY-SA 4.0 (MGS) |
| `mgs/inundacion-costeira/` | https://mapas.galiciasustentable.org/data/inundacion-costeira/data.geojson (IDEG `D2007_60_MapasInundablesCosteiros`, subcapas 3 e 4; estudo SNCZI do 22/3/2014) | CC BY-SA 4.0 (MGS) |
| `mgs/lonxas-2025/` | copia local de `mapasgs/site/public/data/lonxas-2025/` (colleita do 1/11/2026) | CC BY-SA 4.0 (MGS) |
| `mgs/estado-masas-auga/` | copia local de `mapasgs/site/public/data/estado-masas-auga/` (IDEG `PHGC2021_2027_Estado`, 1/11/2026) | CC BY-SA 4.0 (MGS) |
| `pescadegalicia/pescafresca2025.csv` | https://www.pescadegalicia.gal/descargas/pescafresca/pescafresca2025.csv (notas de primeira venda, 1/1–31/12/2025, 60 lonxas, 327 días con vendas) | Consellería do Mar |
| `pescadegalicia/acuicultura.csv` | https://www.pescadegalicia.gal/descargas/acuicultura/acuicultura.csv (produción de acuicultura 2003–2025) | Consellería do Mar |

Columnas de `pescafresca2025.csv` (sen cabeceira, `;`, decimais con coma): data; grupo; código FAO;
especie; provincia; zona; lonxa; kg; importe (€); prezo medio (€/kg).

## De onde sae cada cifra

Todas as cifras calculadas están en `data/cifras.json` (clave entre parénteses).

| Parada | Cifra | Orixe e cálculo |
|---|---|---|
| 1 | 84 zonas de produción (9 A, 64 B, 11 C) | Elementos `tipo = zona` da capa de moluscos; reconto por `clase` (`zonas_producion`, `zonas_por_clase`). Definición das clases: Regulamento de execución (UE) 2019/627. |
| 2 | 69 % (43,1 de 62,7 km²) da superficie de polígonos de bateas en Arousa; 26 de 71 polígonos | Suma de `superficie_km2` dos `tipo = poligono_bateas` por `ria` (`bateas_km2_por_ria`, `poligonos_por_ria`). 43,10 / 62,7 = 68,7 %. |
| 2 | 177.639 t e 124,1 M€ de mexillón en 2025 | `acuicultura.csv`, fila 2025 / MSM / «Mexillón»: 177.638.577,49 kg e 124.126.072,81 € (`mexillon_2025_kg`, `mexillon_2025_eur`). Non inclúe «Mexillón (parques de cultivo)» (4 t). |
| 2 | o mexillón case non pasa pola lonxa | En `pescafresca2025.csv` só hai unha nota de mexillón (6 kg en Pontedeume). |
| 3 | 6,16 M€ de ameixa xaponesa en Carril, a primeira lonxa nesa especie | Suma do importe por lonxa e especie (`especie_Ameixa xaponesa`: Carril 6.160.961 €). |
| 3 | 25,6 M€ de bivalvos na zona de Arousa, 54 % de Galicia | Grupo «Bivalvos», zona «Zona III - Arousa» 25.589.731 € / total Galicia 47.754.165 € (`zona_bivalvos_eur`, `grupos_galicia_eur`). |
| 4 | Vigo 82,1 M€, primeira das 60 lonxas | `lonxas.Vigo.total_eur` = 82.134.526 €; 60 lonxas distintas no CSV (`lonxas_con_vendas`). |
| 4 | peixe sapo 23,0 M€ en Vigo; 12 polígonos de bateas na ría | `lonxas.Vigo.especies_top` (22.960.065 €); `poligonos_por_ria.Vigo`. |
| 5 | polbo en Bueu 1,39 M€, 44 % da lonxa | 1.387.962 € / 3.180.397 € (`lonxas.Bueu`). 8 polígonos e 5,24 km² na ría de Pontevedra; ameixa xaponesa en Campelo 1.974.047 €. |
| 6 | 58 % do berberecho en Noia (1,74 M€) | 1.740.062 € / 3.023.134 € (`especie_Berberecho`). Noia: bivalvos 5.581.524 € de 5.621.893 € (99 %). |
| 6 | Tambre (Noia) en estado peor que bo | `estado-masas-auga`, ES01431, `estado_global = peor que bo`. |
| 7 | 87 % de peixe en Camariñas, 3,94 M€ | Peixes 3.446.070 € / total 3.942.464 € (`lonxas.Camariñas`). Catro polígonos: Corme A e B, Camariñas A e B. |
| 8 | Neda 5,26 km² inundables (T100); Neda + Betanzos 9,2 km², 46 % | `superficie_km2` dos tramos de período de retorno 100 (`inundacion_t100_km2_por_zona`): 5,259 + 3,892 = 9,151 / 19,8. |
| 8 | 4 augas costeiras naturais peor que bo: A Coruña, Ares, Moaña, Rande | `augas_peor_que_bo` e `augas_naturais` (exclúense as masas moi modificadas dos portos). |
| 9 | 75 % da pescada en Celeiro e Burela (73,9 M€); 104,8 M€ entre as dúas | Pescada: 37.819.908 + 36.056.270 = 73.876.178 € / 99.016.256 € (`especie_Pescada`); totais: 47.025.987 + 57.790.232 € sobre 407.783.173 € (25,7 %). |
| 10 | 14 de 22 augas de transición e 4 de 22 costeiras naturais peor que bo; estado químico bo en todas | `augas_naturais`; campo `estado_quimico` = «bo» nas 44. |
| 11 | 19,8 km² inundables en 28 tramos (T100) | Suma de `superficie_km2` dos tramos de 100 anos (`inundacion_t100_km2`, `inundacion_t100_tramos`). |

## Cifras que se quitaron

- **Número de bateas.** Non hai unha cifra oficial con data verificable: a prensa e notas da Xunta
  falan de «case 3.400», «unhas 3.600» ou «máis de 3.300» con alcances distintos. A peza fala de
  polígonos (71) e da súa superficie, que si saen dunha capa oficial.
- **Cota da lámina de inundación** (`cota_max_m` 2,66–2,88 m): non se pode confirmar a referencia
  altimétrica no servizo, así que non se cita.

## Advertencias

- As zonas de produción, os polígonos e o estado das augas son os do plan hidrolóxico Galicia-Costa
  2021–2027: non cobren a demarcación Miño-Sil (a beira galega do Miño) e son avaliacións do
  plan, non medicións recentes. A clasificación sanitaria vixente día a día publícaa o Intecmar.
- As zonas inundables son do ciclo 2015–2021 (estudo de 2014) e só cobren as 28 áreas de risco
  potencial significativo (ARPSI) costeiras; fóra delas tamén pode haber inundación.
- Dúas lonxas do CSV non teñen posición (Coop. Ría de Arosa e Baldaio): contan nos totais, non
  no mapa. «A Coruña (Lonja Coruña, S.A.)» e «A Coruña (Confraría)» comparten punto.

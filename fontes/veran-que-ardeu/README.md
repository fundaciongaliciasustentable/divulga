# O verán que ardeu

Voo de cámara sobre os grandes lumes de agosto de 2025 (Ourense e resto de
Galicia). Peza: `v/veran-que-ardeu/index.html` (xerada), capas en
`v/veran-que-ardeu/capas/`, miniatura `v/veran-que-ardeu/thumb.svg`.

## Rexenerar

```bash
cd fontes/veran-que-ardeu
python3 -I prep.py     # capas + data/calculos.json (precisa shapely, numpy, tifffile; MDT en fontes/terreo/data/raw/)
python3 thumb.py       # miniatura (precisa shapely)
python3 render.py      # v/veran-que-ardeu/index.html (barra e pé de v/galicia-cero-neto/)
python3 datos.py       # datos.json: paradas e cifras, extraídas do modelo
```

`prep.py` copia as capas de Mapas Galicia Sustentable a `data/raw/` desde
`~/Proxectos/mapasgs/site/public/data/` (ou descárgaas de
`https://mapas.galiciasustentable.org/data/<capa>/data.geojson`). Foto do día:
4 de novembro de 2026. `data/raw/` non vai ao git.

Descargas manuais en `data/raw/` (consultadas o 04/11/2026):

- `miteco_avance_2025.pdf`: <https://www.miteco.gob.es/content/dam/miteco/es/biodiversidad/temas/incendios-forestales/Avance_IIFF_2025_.pdf>
  (texto extraído con pypdf en `miteco_avance_2025.txt`).
- `xunta/Lumes-2025-por-Distrito.xlsx` e `xunta/Lumes-2024-por-Distrito.xlsx`:
  `https://mediorural.xunta.gal/sites/default/files/estatisticas/<ano>/Lumes-<ano>-por-Distrito.xlsx`
  (os anos 2016–2023 dan 404 nese enderezo). As cifras lense directamente nas filas Galicia, provincia e distrito (columna «Superficie total (ha)»).

## De onde sae cada cifra

| Parada | Cifra | Fonte |
|---|---|---|
| 1 | 10.427 focos en agosto; 96,8 % da tempada (10.767, xuño–outubro); 7.345 entre o 13 e o 17 (70,4 %); 1.613 o día 15; 8.845 en concellos de Ourense (84,8 %) | Cálculo FGS (`prep.py`) sobre a capa `focos-tempada-2025` (NASA FIRMS, VIIRS S-NPP + MODIS; concello do IET). Unha detección = un píxel visto arder nunha pasada. |
| 2 | 23.036,6 ha (Chandrexa de Queixa + Vilariño de Conso) | Xunta, Medio Rural, nota do 31/08/2025 ás 14.00: <https://www.xunta.gal/notas-de-prensa/-/nova/016163/medio-rural-informa-situacion-dos-lumes-forestais-con-datos-recollidos-ata-14> |
| 2 | 19.172 ha = 6.320,29 (Requeixo, 8-ago) + 12.851,81 (Parafita, 12-ago) | MITECO, Avance informativo 2025, táboa 3 (GIF) |
| 3 | 1.778 m (máximo) e 591 m (mínimo) dentro do perímetro EFFIS 278504 | Cálculo FGS: MDT 25 m do IGN, mostra cada 4 píxeles, dentro do perímetro recortado a Galicia |
| 3 | 5.490 ha Vilariño de Conso–Mormentelos; reactivación o xoves 14; concellos afectados | MITECO táboa 3; Xunta, nota do 25/08/2025: <https://www.xunta.gal/notas-de-prensa/-/nova/016023/medio-rural-informa-situacion-dos-lumes-forestais-con-datos-recollidos-ata-14> |
| 4 | 37.765 ha (Larouco–Quiroga–Oencia), o maior GIF de España en 2025 | MITECO táboa 3 (o maior valor da táboa) |
| 4 | 31.778,18 ha no lado galego; inicio mércores 13 ás 18.55 en Seadur | Xunta, nota do 31/08/2025 |
| 4 | 269 m e 1.605 m dentro do perímetro EFFIS 278475 | Cálculo FGS co MDT do IGN |
| 5 | 49.532,21 ha no distrito Valdeorras-Trives en 2025; 57,93 en 2024 | Xunta, `Lumes-2025-por-Distrito.xlsx` e `Lumes-2024-por-Distrito.xlsx` |
| 5 | Concellos do lume de Larouco | Xunta, nota do 25/08/2025 |
| 5 | 21.373 ha (Porto–Encinedo–Carballeda de Valdeorras, 14-ago) | MITECO táboa 3 |
| 5 | Por riba de 2.100 m (2.109 m) no perímetro EFFIS 278477, preto de Pena Trevinca | Cálculo FGS co MDT do IGN. Atribuímos ese perímetro ao lume de Porto pola data (15-ago), a localización e a superficie (25.953 ha EFFIS, 6.285 en Galicia); non hai unha correspondencia oficial EFFIS–EGIF. |
| 6 | 23.763,65 ha (Oímbra–A Granxa + Xinzo de Limia–Gudín); datas; concellos | Xunta, notas do 25 e 31/08/2025. MITECO táboa 3: 22.414 + 1.023,35 ha |
| 7 | 10.743 ha A Mezquita; martes 12 ás 21.20; Zamora, A Gudiña, Viana do Bolo | MITECO táboa 3; Xunta, nota do 25/08/2025 |
| 7 | 3.478 ha = 563,62 + 1.106,12 + 1.807,94 (Vilardevós: Terroso, Moialde, Vilar de Cervos) | MITECO táboa 3 |
| 8 | 16 GIF de agosto que afectan a Galicia (inclúe os compartidos con León/Zamora); Maceda 4.506 = 1.856,18 + 2.649,50; Carballeda de Avia 3.017,90; A Pobra do Brollón 1.015,36; Agolada 522,32 | MITECO táboa 3 (filas con Ourense, Lugo ou Pontevedra e data de agosto) |
| 9 | 101.584,08 ha en Ourense de 118.763,65 en Galicia (85,5 %); Valdeorras-Trives + Verín-Viana = 92.067,28 ha (77,5 %); 1.475 lumes | Xunta, `Lumes-2025-por-Distrito.xlsx` |
| 10 | 122.685 ha en 2025 e 150.235 en 2016–2024 (serie anual) | Cálculo FGS: perímetros EFFIS (`historial-queimados`) recortados ao contorno de Galicia (`assets/terreo/galicia-contorno.geojson`), área en proxección local. Ver `data/calculos.json`. |
| 10 | 2.644,7 ha (2024) e 118.763,65 ha (2025) | Xunta, ficheiros por distrito |
| 11 | ≈9,6 Mt de GEI dos lumes do verán de 2025; equivale a un ano de absorcións | Copernicus, subliñado polo Ogacli, en Ecoticias (18/08/2026): <https://www.ecoticias.com/co2/galicia-reduce-sus-emisiones-pero-el-transporte-frena-la-transicion-climatica>. Absorción 2024 ≈ 9,58 Mt = brutas 16,59 − netas 7,02 (Ogacli), como en `fontes/galicia-cero-neto/README.md`. |

## Capas (`v/veran-que-ardeu/capas/`)

- `focos.geojson` (~82 KB): focos de agosto agrupados en celas de 0,005° (~500 m),
  un MultiPoint por día (`d` = primeiro día no que a cela ardeu). A parada 1 anímaa
  día a día con `setFilter` (co movemento reducido mostra o mes enteiro).
- `lumes.geojson` (~109 KB): perímetros EFFIS de 2025 de 100 ha ou máis,
  simplificados (0,0006°), con `id`, `data` e `ha` (EFFIS).
- `anos.geojson` (~99 KB): perímetros EFFIS de 2016–2024 de 50 ha ou máis,
  simplificados (0,0012°), con `ano`.

## Licenzas

A capa `focos-tempada-2025` é CC BY-SA 4.0 (Mapas Galicia Sustentable), polo
que a peza vai baixo CC BY-SA 4.0. EFFIS: CC BY 4.0 (© UE). MDT do IGN: CC BY
4.0. Estatística da Xunta: aviso legal de Medio Rural (reutilización con cita).

## Advertencias

- Xunta, MITECO e EFFIS dan superficies distintas: superficie forestal declarada
  (EGIF), balances provisionais en prensa institucional e perímetros de satélite
  (que inclúen terreo agrícola e só os lumes medianos e grandes). Non se mesturan
  nun mesmo cálculo; cada cifra leva a súa fonte.
- A cifra de prensa de 118.966 ha (nov. 2025) non se usa: o ficheiro oficial da
  Xunta di 118.763,65 ha.

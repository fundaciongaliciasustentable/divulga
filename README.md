# Divulga

Sitio estático de visualizacións de datos da Fundación Galicia Sustentable,
pensado para `divulga.galiciasustentable.org`. Sen build de framework: o que
hai na raíz é o que se publica.

```
index.html               portada (XERADA por build.py, non editar a man)
visualizacions.json      manifesto: unha entrada por visualización
templates/index.tpl.html modelo da portada
assets/css/divulga.css   tokens FGS, barra superior e pé comúns
assets/logos/            logos FGS (de fundaciongaliciasustentable.gal)
v/<slug>/index.html      cada visualización, páxina autónoma
v/<slug>/thumb.svg|png   miniatura cadrada para a portada
fontes/<slug>/           datos e scripts que xeran v/<slug>/ (non se suben)
```

## Engadir unha visualización

1. Crea `v/<slug>/index.html`. Enlaza `../../assets/css/divulga.css` e usa a
   barra `.dv-bar` (símbolo + «Divulga» + «← Todas as visualizacións») e o pé
   `.dv-foot`, como en `v/poboacion-galicia/`.
2. Engade unha miniatura cadrada `v/<slug>/thumb.svg` (ou `.png`, 600×600).
3. Engade a entrada en `visualizacions.json` (`slug`, `titulo`, `entradilla`,
   `data` AAAA-MM-DD, `temas`, `formato`, `fontes`).
4. `python3 build.py` rexenera a portada: unha grella de tarxetas da máis
   recente á máis antiga, ao xeito de informationisbeautiful.net. Os `temas`
   do manifesto convértense en botóns de filtro.
5. Garda os datos e scripts en `fontes/<slug>/` para poder reproducila.

## Vista previa local

```bash
python3 -m http.server 8780
```

## Publicar

```bash
./scripts/empaquetar.sh
```

Rexenera a portada e deixa en `dist/` (e en `divulga-web.zip`) só os ficheiros
públicos. Sube o contido de `dist/` á raíz do subdominio en Dinahosting, ou
sube o zip e descomprímeo alí.

Non borres `api/datos/` no servidor ao subir: aí viven os votos de
`habelos-hainos`, que non van no paquete.

## Votación (api/)

`api/votos.php` garda os votos «Críaste este mito?» de `v/habelos-hainos/`
nun JSON dentro de `api/datos/` (bloqueado por `.htaccess`). Precisa PHP 7.4
ou superior e permiso de escritura en `api/datos/`. Os identificadores dos
mitos de `votos.php` teñen que coincidir cos `IDS` da páxina. Sen PHP (por
exemplo, coa vista previa local) a páxina funciona e oculta a votación.

## Imaxe de marca

A cabeceira usa a mesma foto (Unsplash) e o mesmo degradado que a portada de
fundaciongaliciasustentable.gal. `assets/img/og-divulga.jpg` é a imaxe para
compartir en redes; xérase con `fontes/_marca/og.py` (Pillow + Playfair
Display e Lato).

## Visualizacións

| slug | fontes | rexenerar |
|---|---|---|
| poboacion-galicia | INE Padrón municipal 2025 (táboas 2868, 2880, 2885, 2890) e PERE 2026 (táboa 71117) | `cd fontes/poboacion-galicia && npm i && python3 prep.py && node layout.js s51 && python3 render.py` |

| biblioteca-sustentable | `fontes/biblioteca-sustentable/libros.json` (selección FGS) e portadas de Open Library | `python3 fontes/biblioteca-sustentable/render.py` |
| espiral-lumes | FIRESPAIN-025 (EGIF diaria en grella, 1983-2016, Zenodo 14644902) e Copernicus EFFIS `modis.ba.poly` (WFS, 2017-) | `cd fontes/espiral-lumes && pip install netCDF4 numpy shapely && python3 prep.py && python3 render.py` (para actualizar, descarga de novo `data/effis_galicia.gml` co URL de `prep.py`) |
| galicia-apagandose | IGE, Nomenclátor 1999-2025 (API `igeapi/csv/nomenc`), puntos de entidades de poboación do IET e concellos/parroquias de `galicia-agora` | `cd fontes/galicia-apagandose && pip install shapely pillow && python3 prep.py && python3 render.py` (prep.py descarga os CSV do IGE en `data/ige/` se faltan) |
| raias-clima | Observatorios de AEMET (A Coruña, Santiago, Vigo, Pontevedra, Ourense, Lugo) vía NOAA GHCN-Daily | `cd fontes/raias-clima && python3 prep.py && python3 render.py` (prep.py descarga os CSV das estacións se faltan) |
| vacas-persoas | IGE táboa 62 (gando bovino por concello, Medio Rural), INE Padrón (2868, 2880, 2885, 2890), IGE táboa 10332 (Censo agrario 2020, UG por especie) | `cd fontes/vacas-persoas && pip install shapely scipy && python3 prep.py && python3 render.py` (prep.py descarga os datos se faltan) |
| luz-galicia | Red Eléctrica, API REData: estrutura da xeración e demanda de Galicia (geo_id 17), 2011-2025 | `cd fontes/luz-galicia && python3 prep.py && python3 render.py` (prep.py descarga as respostas da API se faltan) |
| monte-concellos | Inventario Forestal Continuo de Galicia (INVEGA): capa de recintos con coberturas, servizo ArcGIS do IDEG, 2022-2024 | `cd fontes/monte-concellos && python3 descargar.py && pip install shapely pillow && python3 prep.py && python3 render.py` (descargar.py tarda ~2 h: unha consulta por concello) |
| mar-prato | Pesca de Galicia, notas de primeira venda de pesca fresca (CSV por ano, 2015-2025) | `cd fontes/mar-prato && python3 prep.py && python3 render.py` (prep.py descarga os CSV se faltan) |
| galego-xeracions | IGE táboas 2953 (lingua habitual por idade, Galicia e provincias) e 7018 (lingua dos fillos segundo a da nai), 2003-2023 | `cd fontes/galego-xeracions && python3 prep.py && python3 render.py` |
| camino-compostela | Oficina do Peregrino: informe público de Power BI (2021-2025, transcrito en `data/oficina.json`) e informes anuais en PDF (2004-2018); contorno de Natural Earth (world-atlas) | `cd fontes/camino-compostela && pip install pypdf shapely && python3 prep.py && python3 render.py` (para actualizar, transcribir as cifras novas en `data/oficina.json`) |
| calculadora-persoal | INE IPC (xeral IPC251856; alimentos IPC251862 e transporte IPC251892), valor tasado medio da vivenda libre do MIVAU (35101000.XLS), SMI do Ministerio de Traballo (smi1.xls), Our World in Data (poboación, CO₂, esperanza de vida, internet, móbil), artigos «AAAA» da Galipedia e da Wikipedia en castelán (os de España, traducidos ao galego en data/esp_gl.json), e os datos.json de espiral-lumes, raias-clima, ondas-atlantico, galicia-apagandose, camino-compostela e nomes-galicia | `cd fontes/calculadora-persoal && python3 wiki.py && python3 prep.py && python3 render.py` (descarga en data/raw/; precisa pandas e xlrd, e esas pezas xeradas) |
| hexagonos-electorais | Xunta, Abert@s: Parlamento de Galicia por concello (2001-2024); Ministerio do Interior, Infoelectoral: municipais (2003-2023) e xerais ao Congreso (2000-2023) por municipio; concellos de galicia-agora para a reixa | `cd fontes/hexagonos-electorais && pip install numpy scipy shapely && python3 prep.py && python3 render.py` |
| centrais-galicia | OpenStreetMap (power=plant), Wikidata (P2109), Galipedia «Parques eólicos en Galicia»; totais da nota de prensa de REE do Informe do Sistema Eléctrico 2025 | `cd fontes/centrais-galicia && pip install shapely && python3 prep.py && python3 render.py` |
| horas-transporte | GTFS dos autobuses da Xunta (NAP, copia de MobilityDatabase mdb-2821) e de Renfe AV/LD/MD; concellos de galicia-agora e polígonos de monte-concellos | `cd fontes/horas-transporte && pip install pandas numpy scipy shapely && python3 prep.py && python3 render.py` (o cálculo leva uns minutos) |
| encoros | MITECO, Boletín Hidrolóxico, BD-Embalses.zip (Access, semanal 1988-hoxe), concas Miño-Sil e Galicia-Costa | `cd fontes/encoros && pip install access-parser && python3 prep.py && python3 render.py` |
| espera-sergas | Sergas, PDFs da lista de espera cirúrxica (cortes semestrais dende 2014; o último por hospitais e servizos) | `cd fontes/espera-sergas && pip install pypdf && python3 prep.py && python3 render.py` |
| casas-baleiras | INE, Censo 2021: vivendas principais e non principais (59525) e vivendas por consumo eléctrico (59531); polígonos de monte-concellos | `cd fontes/casas-baleiras && python3 prep.py && python3 render.py` (precisa monte-concellos xerado) |
| castros | OpenStreetMap (Overpass: historic=archaeological_site en ES-GA), filtrado a castros; concellos de galicia-agora e contorno de galicia-apagandose | `cd fontes/castros && pip install numpy scipy shapely && python3 prep.py && python3 render.py` |
| ondas-atlantico | NOAA OISST v2.1 diaria (ERDDAP de CoastWatch, ncdcOisst21Agg_LonPM180; os ocos, do THREDDS de PSL), recadro 42-43,9 °N e 9,9-8,9 °O, 1982-2025 | `cd fontes/ondas-atlantico && python3 prep.py && python3 render.py` (a primeira descarga leva un bo anaco: PSL vai mes a mes) |
| apelidos-galegos | INE: apellidos_frecuencia.xls (1/1/2025), mapa por provincia do buscador de apelidos (mapaWidget) e padrón 2025 das catro provincias (2868, 2880, 2885, 2890) | `cd fontes/apelidos-galegos && pip install pandas xlrd && python3 prep.py && python3 render.py` (a descarga son ~4.400 pedidos, retoma onde quedou) |
| vida-semanas | INE, táboas de mortalidade por comunidade (27154) e provincia (27155), interpoladas a cada idade; Eurostat HETUS tus_00age (uso do tempo por idade, España 2010); DataReportal/GWI 2024 (horas en internet); idade media á maternidade do IGE (datos de fenda-rural) | `cd fontes/vida-semanas && python3 prep.py && python3 render.py` (precisa fenda-rural xerada) |
| nomes-galicia | IGE: nomes máis frecuentes segundo a década de nacemento (Galicia e provincias) e táboa 2245 (nomes dos neonatos, 2000-2024) | `cd fontes/nomes-galicia && python3 prep.py && python3 render.py` (prep.py descarga o que falte) |
| reloxo-choiva | MeteoGalicia, datos horarios históricos das estacións (PP_SUM_1.5m), 2016-2025: Coruña-Torre de Hércules, Santiago-EOAS, Campus Lugo, Pontevedra-Campolongo, Vigo e Ourense | `cd fontes/reloxo-choiva && python3 prep.py && python3 render.py` (a primeira descarga son ~7.300 pedidos, unha hora longa; retoma onde quedou) |
| galicia-minuto | IGE 11070 (PIB) e INE 2074 (hoteis), descargados; cifras pechadas de Sanidade, 112, Aena, FEGA, Consellería do Mar, Xunta (madeira), INE (auga) e Sogama, con ligazón en prep.py; e os datos.json de luz-galicia, camino-compostela, mar-prato e raias-clima | `cd fontes/galicia-minuto && python3 prep.py && python3 render.py` (prep.py descarga o que falte; precisa as outras pezas xeradas) |
| fenda-rural | IGE, Panorama rural-urbano (28 táboas por grao de urbanización GU 2016); IGE 8444 (grao de cada concello) | `cd fontes/fenda-rural && python3 prep.py && python3 render.py` (prep.py descarga as táboas que falten) |
| migracions | INE táboas 69695 e 69710 (estranxeiro por país, 2021-2024); IGE 10614, 10613, 568 e 567 (por comunidade e serie dende 1992); Natural Earth (world-atlas) | `cd fontes/migracions && pip install shapely && python3 prep.py && python3 render.py` (prep.py descarga o que falte) |
| habelos-hainos | AEMET, MeteoGalicia, IGE, INEGA, Xunta, ICCT e outras (fonte enlazada en cada mito) | editar o array `MITOS` de `v/habelos-hainos/index.html` a man; votos en `api/votos.php` |
| galicia-cero-neto | Ogacli/MITECO (emisións 2024), INEGA, REE, DGT, Lei 1/2026 do clima; método en `fontes/galicia-cero-neto/README.md` | editar `SECTORS`, `SINK` e `ROADMAP` en `v/galicia-cero-neto/index.html` a man |

### Engadir libros á Biblioteca Sustentable

```bash
python3 fontes/biblioteca-sustentable/engadir.py --titulo "Overshoot" \
  --autoria "William R. Catton" --ano 1980 --eixo fund --descricion "..." [--comezar] [--isbn ...]
```

Engade o libro a `libros.json`, busca e descarga a portada en
`v/biblioteca-sustentable/capas/`, e rexenera a páxina, a miniatura e a
portada de Divulga. Eixos: `fund`, `eco`, `clima`, `bio`, `rural`, `etica`.
Revisa a portada descargada: se é outra edición ou unha tapa de biblioteca,
cámbiaa con `--so-capa --titulo "..." --isbn ...` (ou `--capa-id`).

`prep.py` toma os nomes galegos dos concellos de
`~/Proxectos/galicia-agora/data-out/perfil-concellos/data.geojson`.

Contidos baixo licenza CC BY-NC-SA 4.0.
| pib-rexions | Eurostat nama_10r_2gdp (PPS_HAB_EU27_2020, NUTS 2, 2000-2024), API JSON-stat | `cd fontes/pib-rexions && python3 prep.py && python3 render.py` (prep.py descarga a resposta da API se falta) |
| estudos-rexions | Eurostat edat_lfse_16 (abandono temperán 18-24) e edat_lfse_04 (25-34 con ISCED 5-8) por NUTS 2, 2008-2025 | `cd fontes/estudos-rexions && python3 prep.py && python3 render.py` |
| residuos-europa | Eurostat env_wasmun (GEN, kg/hab) e cei_wm011 (taxa de reciclaxe); INE táboas 32999 (per cápita por CCAA) e 32998 (toneladas por tipo e CCAA), 2023 | `cd fontes/residuos-europa && python3 prep.py && python3 render.py` |
| fecundidade-europa | Eurostat demo_r_frate2 (NUTS 2, 2024) e demo_frate (UE-27, España), 2000-2024 | `cd fontes/fecundidade-europa && python3 prep.py && python3 render.py` |
| centenarios | INE ECP táboa 69792 (poboación por idade simple e provincia, 1 de xaneiro de 2006 e 2026) e Eurostat demo_r_d2jan (NUTS 2, 2025) | `cd fontes/centenarios && python3 prep.py && python3 render.py` |
| envellecemento-europa | Eurostat demo_r_pjanind3 (idade mediana NUTS 3/NUTS 2, 2014-2025), demo_pjanind (UE-27) e GISCO NUTS 2024 1:20M | `cd fontes/envellecemento-europa && python3 prep.py && python3 render.py` |
| galego-concellos | IGE, Censo 2001 e 2011: uso do galego por concello (táboas 1845 e 6856, igeapi CSV); límites IET (galicia-agora) | `cd fontes/galego-concellos && python3 prep.py && python3 render.py` (prep.py descarga os CSV do IGE se faltan) |
| toponimos | IGE, Nomenclátor 2025 (igeapi `csv/nomenc/2025/0/0/0/1/0/0`); puntos de entidades de poboación (PBA) e límites do IET vía galicia-agora | `cd fontes/toponimos && python3 prep.py && python3 render.py` (prep.py descarga o nomenclátor se falta) |
| bibliotecas-concellos | Ministerio de Cultura, Bibliotecas Públicas Españolas en cifras: informe anual por municipio (alziraweb `GetAnexo&id=51&origen=PR`, provincias 15/27/32/36), 2024 | `cd fontes/bibliotecas-concellos && python3 prep.py && python3 render.py` (necesita pandas; prep.py descarga as táboas se faltan) |
| mexillon-mundo | FAO FishStat Global aquaculture production (zip 2025.1.0, grupo ISSCAAP «Mussels») e Pesca de Galicia, CSV de produción de acuicultura (mexillón MSM e MSM.) | `cd fontes/mexillon-mundo && python3 prep.py && python3 render.py` (prep.py descarga os datos se faltan) |
| eolica-europa | Eurostat nrg_inf_epcrw (eólica RA300 e mariña RA320), demo_r_d2jan, reg_area3; Inega, «Potencia eléctrica e térmica instalada en Galicia» (PDF 31/03/2026) | `cd fontes/eolica-europa && pip install pypdf && python3 prep.py && python3 render.py` (prep.py descarga os datos se faltan) |
| eucalipto-mundo | FAO FRA 2025 (descarga completa, táboa 1a), INVEGA vía `fontes/monte-concellos/data/datos.json`, ICNF IFN6 relatório final (táboas 101.PT e 106.PTC), IBGE SIDRA 5930 | `cd fontes/eucalipto-mundo && pip install pypdf shapely && python3 prep.py && python3 render.py` (precisa antes `fontes/monte-concellos/data/datos.json`) |
| minutos-hospital | Ministerio de Sanidade, Catálogo Nacional de Hospitais 2025 (14 hospitais xerais do Sergas); IGE Nomenclátor 2025; puntos de entidades do IET (galicia-agora); coordenadas de hospitais de OSM/Nominatim; tempos OSRM (router.project-osrm.org) | `cd fontes/minutos-hospital && python3 prep.py && python3 render.py` (a primeira vez prep.py fai ~333 peticións a OSRM, unha por segundo, ~10 min; despois usa a caché de data/raw/osrm/) |
| fibra-concellos | Ministerio para a Transformación Dixital, Informe de cobertura de banda ancha en España 2025 (datos a 30/06/2025): capas municipais dos mapas de cobertura agregada (servizos ArcGIS do Ministerio, % de fogares a 100 Mbps, 1 Gbps e FTTH) | `cd fontes/fibra-concellos && python3 prep.py && python3 render.py` |
| vivenda-turistica | INE, estatística experimental de vivendas turísticas (táboas 39363 e 39366, maio 2026); INE Censo 2021 (táboa 59525); Turismo de Galicia, REAT serie mensual (para comparar) | `cd fontes/vivenda-turistica && python3 prep.py && python3 render.py` |
| prazas-turisticas | Turismo de Galicia, REAT serie mensual de aloxamentos por concello e tipo (descargascdn.xunta.gal/interno/smarxa/REAT_Serie_Mensual.csv, outubro 2026); INE Padrón 1/1/2025 (2868, 2880, 2885, 2890) | `cd fontes/prazas-turisticas && python3 prep.py && python3 render.py` |
| nucleos-espana | INE, Nomenclátor: poboación por unidade poboacional a 1/1/2025 (ficheiro nacional ZIP); IGN, superficie por CCAA (Anuario de Estadística MAPA 2023, táboa 1.1) | `cd fontes/nucleos-espana && pip install pypdf && python3 prep.py && python3 render.py` (prep.py descarga o ZIP do INE, ~21 MB, se falta) |
| costa-galicia | IGN, lonxitude da costa por provincias (INE, AEE 2008, táboa 1.1.3); MITECO, lonxitude do DPM-T por provincia (Anuario MAPA 2017, táboa 9.3); CIA World Factbook «Coastline» (Internet Archive, 3/2/2026) | `cd fontes/costa-galicia && pip install pypdf && python3 prep.py && python3 render.py` |
| choiva-sol-europa | OMM, WMO Climate Normals 1991-2020 (NOAA NCEI 0253808, ficheiros compostos PRCP, DP01, TSUN); IPMA, normais 1991-2020 de Lisboa e Porto | `cd fontes/choiva-sol-europa && pip install pypdf && python3 prep.py && python3 render.py` |
| coches-ccaa | DGT, Parque de vehículos. Táboas estatísticas 2025 (táboa 82) e Matriculacións. Táboas estatísticas 2025 (táboas 41 e 42); INE, ECP (poboación a 1/1/2026) | `cd fontes/coches-ccaa && pip install openpyxl && python3 prep.py && python3 render.py` |
| vidro-concellos | Ecovidrio, datos de recollida de envases de vidro por municipio (Excel `download-excel`, 2015-2025) e INE Padrón (2868, 2880, 2885, 2890) | `cd fontes/vidro-concellos && pip install openpyxl shapely && python3 prep.py && python3 render.py` (prep.py descarga os datos en `data/raw/` se faltan) |
| etiqueta-cero | DGT, «DGT en cifras» → Datos municipales – información general, Excel 2020-2025 (parque por distintivo ambiental e poboación) | `cd fontes/etiqueta-cero && pip install openpyxl shapely && python3 prep.py && python3 render.py` (prep.py descarga os Excel en `data/raw/` se faltan) |
| bandeiras-azuis | Xunta, Datos Abertos «Praias galegas con bandeira azul» (CSV 2013-2026); ADEAC, relación e nota de prensa 2026 (banderaazul.org); INE, Anuario 2008, táboa 1.1.3 (lonxitude da costa, IGN) | `cd fontes/bandeiras-azuis && pip install pypdf shapely && python3 prep.py && python3 render.py` (prep.py descarga os datos en `data/raw/` se faltan) |
| concellos-1950 | INE, «Alteraciones de los municipios en los Censos de Población desde 1842» (intercensal, poboación de feito 1900-1991 e de dereito 2001-2021) e Padrón 2025 (2868, 2880, 2885, 2890); concellos de galicia-agora | `cd fontes/concellos-1950 && python3 prep.py && python3 render.py` (a primeira vez descarga ~325 páxinas do INE, uns minutos) |
| idade-concellos | IGE táboa 723 (indicadores de poboación: idade media, índice de envellecemento, 2002-2025) e táboa 142 (poboación por sexo e grupos quinquenais, censo anual 2025) | `cd fontes/idade-concellos && python3 prep.py && python3 render.py` |
| enterros-bautizos | IGE/INE, Movemento natural da poboación: nacementos e defuncións por concello, 1975-2025 (táboa 227); hexágonos de vacas-persoas | `cd fontes/enterros-bautizos && python3 prep.py && python3 render.py` (precisa `fontes/vacas-persoas/data/datos.json`) |
| nados-fora | INE, Censo anual de poboación 1/1/2025, «Población por sexo y país de nacimiento (principales países)» por municipio (66404, 66426, 66436, 66442); concellos de galicia-agora | `cd fontes/nados-fora && python3 prep.py && python3 render.py` (descarga ~60 MB do INE a primeira vez) |
| renda-concellos | INE, ADRH 2024: táboas 30989, 31088, 31133, 31160 (concellos e seccións) e 53689 (agregados); polígonos de galicia-agora | `cd fontes/renda-concellos && python3 prep.py && python3 render.py` (prep.py descarga os CSV se faltan) |
| pensionistas-afiliados | IGE táboas 6560 (pensionistas por concello, 31/12/2024) e 11311 (persoas afiliadas por concello de residencia, decembro 2024) | `cd fontes/pensionistas-afiliados && python3 prep.py && python3 render.py` (prep.py descarga os CSV se faltan) |
| debeda-concellos | Facenda, débeda viva dos concellos a 31/12/2025 e 31/12/2015 (Excel); INE Padrón 2025 e 2016 (2868, 2880, 2885, 2890) | `cd fontes/debeda-concellos && pip install openpyxl xlrd && python3 prep.py && python3 render.py` (prep.py descarga os ficheiros se faltan) |
| paro-concellos | SEPE, MUNI_<provincia>_09AA.xls (setembro 2012-2026); IGE táboa 142 (poboación 15-64, Censo 2011 e 1/1/2025) | `cd fontes/paro-concellos && pip install xlrd && python3 prep.py && python3 render.py` (prep.py descarga os 60 Excel do SEPE se faltan) |
| vivenda-salario | MIVAU 35101000.XLS (valor tasado por provincia, media dos 4 trimestres de 2024); AEAT Mercado de traballo e pensións 2024, salario medio por provincia | `cd fontes/vivenda-salario && pip install xlrd && python3 prep.py && python3 render.py` (prep.py descarga os ficheiros se faltan) |

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

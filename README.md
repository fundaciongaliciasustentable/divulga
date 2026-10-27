# Divulga

Sitio estático de visualizacións de datos da Fundación Galicia Sustentable,
pensado para `divulga.galiciasustentable.org`. Sen build de framework: o que
hai na raíz é o que se publica.

A portada (`index.html`) é deliberadamente **allea á estética institucional**
da web da FGS na grella de pezas: lenzo crema, tipografía editorial, sen
barra verde nin botóns de cor — deixa falar as propias pezas. A banda de
enriba (`assets/img/heroe-1200/2400.jpg` con degradado, logo branco, «Divulga»
e subtítulo) si segue o tratamento institucional, igual ca na vella portada e
ca `og-divulga.jpg`. A marca FGS queda tamén ben visible no pé, co logotipo
estendido. A portada non amosa datas de publicación: a
`data` do manifesto só ordena as tarxetas, para non confundir esa data coa
temporalidade propia de cada peza (que pode cubrir anos ou décadas distintos).
Cada peza en `v/<slug>/`
segue si os criterios FGS (cabeceira `.dv-bar`, pé `.dv-foot`) por tratarse de
documentos propios da fundación — pero `.dv-bar`/`.dv-foot` van **transparentes
e integrados no tema de cada peza** (len o fondo/cor que a propia peza xa
resolveu, só cun símbolo «gs» pequeno e unha liña fina), non un bloque de cor
fixo que rompa coa estética de cada visualización. O pé inclúe sempre o
mínimo legal: nome, CIF, licenza e ligazóns a Aviso legal/Privacidade/Cookies
da web institucional (non hai páxinas propias en Divulga para iso).

```
index.html                 portada (XERADA por build.py, non editar a man)
visualizacions.json        manifesto: unha entrada por visualización
templates/index.tpl.html   modelo da portada
build.py                   xera index.html desde o manifesto e o modelo
assets/css/divulga.css     tokens FGS, barra superior e pé comúns (.dv-bar/.dv-foot)
assets/css/viz-base.css    tipografía de gráfica compartida (--gs-font-chart-*) e
                            compoñentes para pezas novas (.dv-stat/.dv-badge/.dv-tooltip/.dv-legend)
assets/logos/               logos FGS (de fundaciongaliciasustentable.gal)
assets/img/                 foto da banda (heroe-1200/2400.jpg) e og-divulga.jpg
v/<slug>/index.html         cada visualización, páxina autónoma
v/<slug>/thumb.svg|png      miniatura cadrada para a portada
fontes/<slug>/               datos e scripts que xeran v/<slug>/ (non se suben)
scripts/                     empaquetado (`empaquetar.sh`) e xeración do OG (`og.py`)
```

## Engadir unha visualización

1. Crea `v/<slug>/index.html`. Enlaza `../../assets/css/divulga.css` e usa a
   barra `.dv-bar` (símbolo + «Divulga» + «← Todas as visualizacións») e o pé
   `.dv-foot`, como en `v/poboacion-galicia/`. Define `--ink`/`--paper`/
   `--muted` (e `--line` se queres unha liña separadora precisa) no `:root`
   propio da peza: `.dv-bar`/`.dv-foot` adáptanse sós a eses valores, claros
   ou escuros. Para o chrome denso (eixos,
   cifras, controis) enlaza tamén `../../assets/css/viz-base.css` e define os
   `--display`/`--num` locais como `var(--gs-font-chart-display)` /
   `var(--gs-font-chart-num)` en vez de repetir o stack de fontes — e usa
   `.dv-stat`/`.dv-badge`/`.dv-tooltip`/`.dv-legend` en vez de reinventar eses
   compoñentes.
2. Engade unha miniatura cadrada `v/<slug>/thumb.svg` (ou `.png`, 600×600).
   Que pese pouco (idealmente <50 KB): é a imaxe que carga a portada das 13
   pezas á vez. Se a peza ten moitos elementos (puntos, portadas...), simplifica
   para o thumb (menos detalle, máis compresión) — ver `fontes/espiral-lumes/`
   e `fontes/biblioteca-sustentable/` como exemplo.
3. Engade a entrada en `visualizacions.json` (`slug`, `titulo`, `entradilla`,
   `data` AAAA-MM-DD, `temas`, `formato`, `fontes`).
4. `python3 build.py` rexenera a portada: unha grella de pezas da máis
   recente á máis antiga, numeradas, cunha liña de filtro por tema.
5. Garda os datos e scripts en `fontes/<slug>/` para poder reproducila. Se a
   peza se edita a man (sen `prep.py`/`render.py`), garda igualmente un
   `datos.json` sincronizado en `fontes/<slug>/` — ver `fontes/habelos-hainos/`
   ou `fontes/galicia-cero-neto/`.

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

`assets/img/heroe-1200.jpg`/`heroe-2400.jpg` son a foto da banda da portada
(srcset responsive). `assets/img/og-divulga.jpg` é a imaxe para compartir en
redes, xerada con `scripts/og.py` (Pillow + Playfair Display e Lato) a partir
de `heroe-2400.jpg`, co mesmo tratamento que a portada de
fundaciongaliciasustentable.gal:

```bash
python3 scripts/og.py <PlayfairDisplay[wght].ttf> <Lato-Regular.ttf>
```

> **Pendente**: `heroe-2400.jpg` é unha foto de stock de Quiraing (Illa de
> Skye, Escocia), non de Galicia. Mentres non se substitúa por unha foto real
> de Galicia con licenza, tanto a banda da portada como `og-divulga.jpg`
> seguen usándoa.

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

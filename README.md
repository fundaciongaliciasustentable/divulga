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
4. `python3 build.py` rexenera a portada. A máis recente sae destacada; o resto
   pasa a «Arquivo».
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

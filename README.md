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

Sube por FTP todo menos `fontes/`, `templates/`, `build.py`, `README.md` e
`.claude/` ao cartafol do subdominio en Dinahosting.

## Visualizacións

| slug | fontes | rexenerar |
|---|---|---|
| poboacion-galicia | INE Padrón municipal 2025 (táboas 2868, 2880, 2885, 2890) e PERE 2026 (táboa 71117) | `cd fontes/poboacion-galicia && npm i && python3 prep.py && node layout.js s51 && python3 render.py` |

`prep.py` toma os nomes galegos dos concellos de
`~/Proxectos/galicia-agora/data-out/perfil-concellos/data.geojson`.

Contidos baixo licenza CC BY-NC-SA 4.0.

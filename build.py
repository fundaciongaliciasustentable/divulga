#!/usr/bin/env python3
"""Xera index.html (portada de Divulga) a partir de visualizacions.json.

A portada é un repositorio ao xeito dunha app de streaming (Apple TV):
unha peza destacada grande arriba e, debaixo, filas horizontais por
categoría («Novidades» + as categorías de CATEGORIAS). O HTML xerado
aquí é sempre determinista (a mesma entrada, a mesma saída, para que os
diffs de git teñan sentido); a variedade do día a día — cal peza sae
destacada, en que orde van as pezas dentro de cada fila — faina o propio
navegador en JS (templates/index.tpl.html), cunha semente baseada na
data de hoxe, así a portada cambia sen ter que reempaquetar nin subir
nada cada día.

Cada visualización vive en v/<slug>/index.html e ten unha miniatura en
v/<slug>/thumb.svg (ou thumb.png), que tamén se usa como ilustración da
destacada. Os temas do manifesto agrúpanse en poucas categorías amplas
(ver CATEGORIAS) para as filas e os saltos rápidos, e tamén alimentan a
busca de texto libre xunto co título e a entradilla. Uso: python3 build.py
"""
import html
import json
import re
import unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Agrupa os ~26 temas soltos do manifesto en categorías amplas para o filtro
# da portada (á escala do menú de «Causas» da web institucional: un puñado de
# opcións, non unha ringleira de etiquetas). O detalle de `temas` consérvase
# igual no manifesto e na busca de texto libre, só o filtro por botóns usa
# estas categorías.
CATEGORIAS = {
    "Poboación": "Poboación e sociedade", "Sociedade": "Poboación e sociedade",
    "Emigración": "Poboación e sociedade", "Lingua": "Poboación e sociedade",
    "Saúde": "Poboación e sociedade", "Mitos e datos": "Poboación e sociedade",
    "Política": "Poboación e sociedade",
    "Territorio": "Territorio e clima", "Clima": "Territorio e clima",
    "Choiva": "Territorio e clima", "Auga": "Territorio e clima",
    "Monte": "Territorio e clima", "Lumes": "Territorio e clima",
    "Mar": "Territorio e clima",
    "Rural": "Rural e alimentación", "Gandería": "Rural e alimentación",
    "Alimentación": "Rural e alimentación",
    "Economía": "Economía e vivenda", "Vivenda": "Economía e vivenda",
    "Turismo": "Economía e vivenda", "Mobilidade": "Economía e vivenda",
    "Enerxía": "Enerxía e sustentabilidade", "Sustentabilidade": "Enerxía e sustentabilidade",
    "Patrimonio": "Patrimonio e cultura", "Camiño de Santiago": "Patrimonio e cultura",
    "Lecturas": "Patrimonio e cultura",
}


def miniatura(slug):
    for ext in ("svg", "png", "jpg", "webp"):
        if (ROOT / "v" / slug / f"thumb.{ext}").exists():
            return f"v/{slug}/thumb.{ext}"
    return None


def categorias_de(v):
    return sorted({CATEGORIAS[t] for t in v.get("temas", []) if t in CATEGORIAS}, key=str.casefold)


def ancora(texto):
    """id de HTML lexible a partir dun nome de categoría: 'Economía e vivenda' -> 'economia-e-vivenda'."""
    sen_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", sen_acentos.lower()).strip("-")


def tarxeta(v):
    """Tarxeta cadrada: úsase tanto nas filas coma na grella de resultados da
    busca (unha soa compoñente, un só sitio para o seu CSS). Os data-* levan
    tamén o que precisa a destacada para redebuxarse en JS sen ter que
    volver ao servidor."""
    e = html.escape
    href = f"v/{v['slug']}/"
    thumb = miniatura(v["slug"])
    img = f'<img src="{thumb}" alt="" loading="lazy" width="600" height="600">' if thumb else ""
    cats = "|".join(categorias_de(v))
    busca = " ".join([v["titulo"], v["entradilla"], *v.get("temas", [])]).lower()
    formato = v.get("formato", "")
    return (f'<a class="tarxeta" href="{href}" data-temas="{e(cats)}" data-busca="{e(busca)}" '
            f'data-titulo="{e(v["titulo"])}" data-entradilla="{e(v["entradilla"])}" data-formato="{e(formato)}">'
            f'<span class="tarxeta__marco">{img}</span>'
            f'<span class="tarxeta__cap">'
            f'<span class="tarxeta__formato">{e(formato)}</span>'
            f'<span class="tarxeta__titulo">{e(v["titulo"])}</span>'
            f'</span></a>')


def fila(titulo_fila, vs_fila, id_ancora):
    e = html.escape
    tarxetas = "\n".join(f"          {tarxeta(v)}" for v in vs_fila)
    return f"""  <section class="fila" id="fila-{id_ancora}" aria-labelledby="fila-{id_ancora}-tit">
    <div class="inner">
      <div class="fila__cabeceira"><h2 id="fila-{id_ancora}-tit">{e(titulo_fila)}</h2></div>
      <div class="fila__envoltura">
        <button type="button" class="fila__frecha fila__frecha--esq" data-scroll="-1" aria-label="Desprazar {e(titulo_fila)} cara a atrás">‹</button>
        <div class="fila__pista">
{tarxetas}
        </div>
        <button type="button" class="fila__frecha fila__frecha--dta" data-scroll="1" aria-label="Desprazar {e(titulo_fila)} cara a adiante">›</button>
      </div>
    </div>
  </section>"""


def destacada(v):
    """Panel grande do inicio, sen JS: amosa a peza máis recente. En canto
    carga JS, templates/index.tpl.html elixe outra ao chou (semente do día)
    entre TODAS as pezas, non só as recentes, para que a portada tamén
    saque á luz traballo máis antigo — un repositorio, non só un titular."""
    e = html.escape
    thumb = miniatura(v["slug"]) or ""
    return f"""    <a class="destacada__panel" href="v/{v['slug']}/" id="destacada-link">
      <div class="destacada__texto">
        <p class="destacada__kicker"><span class="barra" aria-hidden="true"></span><span id="destacada-formato">{e(v.get('formato', ''))}</span></p>
        <h2 id="destacada-titulo">{e(v['titulo'])}</h2>
        <p class="destacada__sub" id="destacada-entradilla">{e(v['entradilla'])}</p>
        <span class="destacada__cta">Ver a visualización <span aria-hidden="true">→</span></span>
      </div>
      <div class="destacada__arte">
        <img id="destacada-img" src="{thumb}" alt="" width="600" height="600" loading="eager">
      </div>
    </a>"""


def catalogo(vs):
    e = html.escape
    filas = sorted(vs, key=lambda v: v["titulo"].casefold())
    return "\n".join(
        f'      <li><a href="v/{v["slug"]}/">{e(v["titulo"])}</a><span>{e(v.get("formato", ""))}</span></li>'
        for v in filas
    )


def main():
    vs = json.loads((ROOT / "visualizacions.json").read_text(encoding="utf-8"))
    vs.sort(key=lambda v: v["data"], reverse=True)
    for v in vs:
        if not (ROOT / "v" / v["slug"] / "index.html").exists():
            raise SystemExit(f"Falta v/{v['slug']}/index.html")
        descoñecidos = [t for t in v.get("temas", []) if t not in CATEGORIAS]
        if descoñecidos:
            raise SystemExit(f"{v['slug']}: temas sen categoría en CATEGORIAS: {descoñecidos}")

    categorias = sorted(set(CATEGORIAS.values()), key=str.casefold)

    chips = '<a class="chip" href="#fila-novidades">Novidades</a>' + "".join(
        f'<a class="chip" href="#fila-{ancora(c)}">{html.escape(c)}</a>' for c in categorias
    )

    filas = [fila("Novidades", vs[:14], "novidades")]
    for c in categorias:
        pezas_cat = [v for v in vs if c in categorias_de(v)]
        filas.append(fila(c, pezas_cat, ancora(c)))

    n = len(vs)
    tpl = (ROOT / "templates" / "index.tpl.html").read_text(encoding="utf-8")
    out = (tpl.replace("{{DESTACADA}}", destacada(vs[0]))
              .replace("{{CHIPS}}", chips)
              .replace("{{FILAS}}", "\n".join(filas))
              .replace("{{RESULTADOS}}", "\n".join(f"    {tarxeta(v)}" for v in vs))
              .replace("{{CATALOGO}}", catalogo(vs))
              .replace("{{CONTA}}", f"{n} {'visualización' if n == 1 else 'visualizacións'}")
              .replace("{{ANO}}", str(date.today().year)))
    (ROOT / "index.html").write_text(out, encoding="utf-8")
    print(f"index.html xerado con {n} visualización(s)")


if __name__ == "__main__":
    main()

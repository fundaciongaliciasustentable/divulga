#!/usr/bin/env python3
"""Xera index.html (portada de Divulga) a partir de visualizacions.json.

Cada visualización vive en v/<slug>/index.html e ten unha miniatura en
v/<slug>/thumb.svg (ou thumb.png). As pezas van da máis recente á máis
antiga (a `data` do manifesto só ordena: a portada non amosa datas de
publicación, para non confundilas coa temporalidade propia dos datos de
cada peza). Os temas do manifesto agrúpanse en poucas categorías amplas
(ver CATEGORIAS) para o filtro de botóns, e tamén alimentan a busca de
texto libre xunto co título e a entradilla. Uso: python3 build.py
"""
import html
import json
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


def peza(v, i):
    e = html.escape
    href = f"v/{v['slug']}/"
    thumb = miniatura(v["slug"])
    img = (f'<img src="{thumb}" alt="" loading="lazy" width="600" height="750">'
           if thumb else "")
    cats = "|".join(categorias_de(v))
    busca = " ".join([v["titulo"], v["entradilla"], *v.get("temas", [])]).lower()
    return f"""    <a class="peza" href="{href}" data-temas="{e(cats)}" data-busca="{e(busca)}">
      <span class="linea-sup"><span class="num">{i:02d}</span><span>{e(v.get('formato', ''))}</span></span>
      <div class="marco">{img}</div>
      <div class="cap">
        <h2>{e(v['titulo'])}</h2>
        <p class="entradilla">{e(v['entradilla'])}</p>
      </div>
    </a>"""


def main():
    vs = json.loads((ROOT / "visualizacions.json").read_text(encoding="utf-8"))
    vs.sort(key=lambda v: v["data"], reverse=True)
    for v in vs:
        if not (ROOT / "v" / v["slug"] / "index.html").exists():
            raise SystemExit(f"Falta v/{v['slug']}/index.html")
        descoñecidos = [t for t in v.get("temas", []) if t not in CATEGORIAS]
        if descoñecidos:
            raise SystemExit(f"{v['slug']}: temas sen categoría en CATEGORIAS: {descoñecidos}")
    temas = sorted(set(CATEGORIAS.values()), key=str.casefold)
    filtros = "".join(f'<button type="button" class="tema" data-tema="{html.escape(t)}" aria-pressed="false">'
                      f'{html.escape(t)}</button>' for t in temas)
    n = len(vs)
    tpl = (ROOT / "templates" / "index.tpl.html").read_text(encoding="utf-8")
    out = (tpl.replace("{{PEZAS}}", "\n".join(peza(v, i + 1) for i, v in enumerate(vs)))
              .replace("{{FILTROS}}", filtros)
              .replace("{{CONTA}}", f"{n} {'visualización' if n == 1 else 'visualizacións'}")
              .replace("{{ANO}}", str(date.today().year)))
    (ROOT / "index.html").write_text(out, encoding="utf-8")
    print(f"index.html xerado con {n} visualización(s)")


if __name__ == "__main__":
    main()

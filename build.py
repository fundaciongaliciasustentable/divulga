#!/usr/bin/env python3
"""Xera index.html (portada de Divulga) a partir de visualizacions.json.

Cada visualización vive en v/<slug>/index.html e ten unha miniatura en
v/<slug>/thumb.svg (ou thumb.png). As tarxetas van da máis recente á máis
antiga e os temas do manifesto fan de filtro. Uso: python3 build.py
"""
import html
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MESES = ["xaneiro", "febreiro", "marzo", "abril", "maio", "xuño", "xullo",
         "agosto", "setembro", "outubro", "novembro", "decembro"]


def data_longa(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def miniatura(slug):
    for ext in ("svg", "png", "jpg", "webp"):
        if (ROOT / "v" / slug / f"thumb.{ext}").exists():
            return f"v/{slug}/thumb.{ext}"
    return None


def tarxeta(v):
    e = html.escape
    href = f"v/{v['slug']}/"
    thumb = miniatura(v["slug"])
    img = (f'<img src="{thumb}" alt="" loading="lazy" width="600" height="600">'
           if thumb else '<div class="sen-img" aria-hidden="true"></div>')
    temas = "|".join(v.get("temas", []))
    return f"""
    <article class="tarxeta" data-temas="{e(temas)}">
      <a href="{href}">
        <span class="img">{img}</span>
        <span class="txt">
          <span class="titulo">{e(v['titulo'])}</span>
          <span class="sub">{e(v.get('formato', ''))} · <time datetime="{v['data']}">{data_longa(v['data'])}</time></span>
        </span>
      </a>
    </article>"""


def main():
    vs = json.loads((ROOT / "visualizacions.json").read_text(encoding="utf-8"))
    vs.sort(key=lambda v: v["data"], reverse=True)
    for v in vs:
        if not (ROOT / "v" / v["slug"] / "index.html").exists():
            raise SystemExit(f"Falta v/{v['slug']}/index.html")
    temas = sorted({t for v in vs for t in v.get("temas", [])}, key=str.casefold)
    filtros = "".join(f'<button type="button" class="tema" data-tema="{html.escape(t)}" aria-pressed="false">'
                      f'{html.escape(t.lower())}</button>' for t in temas)
    n = len(vs)
    tpl = (ROOT / "templates" / "index.tpl.html").read_text(encoding="utf-8")
    out = (tpl.replace("{{TARXETAS}}", "".join(tarxeta(v) for v in vs))
              .replace("{{FILTROS}}", filtros)
              .replace("{{CONTA}}", f"{n} {'visualización' if n == 1 else 'visualizacións'}")
              .replace("{{ANO}}", str(date.today().year)))
    (ROOT / "index.html").write_text(out, encoding="utf-8")
    print(f"index.html xerado con {n} visualización(s)")


if __name__ == "__main__":
    main()

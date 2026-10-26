#!/usr/bin/env python3
"""Xera index.html (portada de Divulga) a partir de visualizacions.json.

Cada visualización vive en v/<slug>/index.html e ten unha miniatura en
v/<slug>/thumb.svg (ou thumb.png). A máis recente vai destacada; o resto,
no arquivo. Uso: python3 build.py
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


def ficha(v, destacada=False):
    e = html.escape
    href = f"v/{v['slug']}/"
    thumb = miniatura(v["slug"])
    img = (f'<img src="{thumb}" alt="" loading="lazy" width="600" height="600">'
           if thumb else '<div class="sen-img" aria-hidden="true"></div>')
    temas = "".join(f'<li>{e(t)}</li>' for t in v.get("temas", []))
    return f"""
    <article class="ficha{' destacada' if destacada else ''}">
      <a class="img" href="{href}" tabindex="-1" aria-hidden="true">{img}</a>
      <div class="txt">
        <p class="meta"><time datetime="{v['data']}">{data_longa(v['data'])}</time> · {e(v.get('formato', ''))}</p>
        <h{2 if destacada else 3}><a href="{href}">{e(v['titulo'])}</a></h{2 if destacada else 3}>
        <p class="entradilla">{e(v['entradilla'])}</p>
        <ul class="temas">{temas}</ul>
        <p class="fontes">Fontes: {e(v.get('fontes', ''))}</p>
        {f'<a class="ver" href="{href}">Ver a visualización →</a>' if destacada else ''}
      </div>
    </article>"""


def main():
    vs = json.loads((ROOT / "visualizacions.json").read_text(encoding="utf-8"))
    vs.sort(key=lambda v: v["data"], reverse=True)
    for v in vs:
        if not (ROOT / "v" / v["slug"] / "index.html").exists():
            raise SystemExit(f"Falta v/{v['slug']}/index.html")
    destacada = ficha(vs[0], True) if vs else ""
    resto = "".join(ficha(v) for v in vs[1:])
    arquivo = (f'<section class="arquivo" aria-labelledby="h-arq"><h2 id="h-arq">Arquivo</h2>'
               f'<div class="grella">{resto}</div></section>') if resto else ""
    n = len(vs)
    tpl = (ROOT / "templates" / "index.tpl.html").read_text(encoding="utf-8")
    out = (tpl.replace("{{DESTACADA}}", destacada)
              .replace("{{ARQUIVO}}", arquivo)
              .replace("{{CONTA}}", f"{n} {'visualización' if n == 1 else 'visualizacións'}")
              .replace("{{ANO}}", str(date.today().year)))
    (ROOT / "index.html").write_text(out, encoding="utf-8")
    print(f"index.html xerado con {n} visualización(s)")


if __name__ == "__main__":
    main()

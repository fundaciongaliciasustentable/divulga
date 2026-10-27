#!/usr/bin/env python3
"""Xera index.html (portada de Divulga) a partir de visualizacions.json.

Cada visualización vive en v/<slug>/index.html e ten unha miniatura en
v/<slug>/thumb.svg (ou thumb.png). As pezas van da máis recente á máis
antiga (a `data` do manifesto só ordena: a portada non amosa datas de
publicación, para non confundilas coa temporalidade propia dos datos de
cada peza) e os temas do manifesto fan de filtro. Uso: python3 build.py
"""
import html
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def miniatura(slug):
    for ext in ("svg", "png", "jpg", "webp"):
        if (ROOT / "v" / slug / f"thumb.{ext}").exists():
            return f"v/{slug}/thumb.{ext}"
    return None


def peza(v, i):
    e = html.escape
    href = f"v/{v['slug']}/"
    thumb = miniatura(v["slug"])
    img = (f'<img src="{thumb}" alt="" loading="lazy" width="600" height="750">'
           if thumb else "")
    temas = "|".join(v.get("temas", []))
    return f"""    <a class="peza" href="{href}" data-temas="{e(temas)}">
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
    temas = sorted({t for v in vs for t in v.get("temas", [])}, key=str.casefold)
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

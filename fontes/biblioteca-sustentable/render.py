#!/usr/bin/env python3
"""Xera v/biblioteca-sustentable/index.html e thumb.svg desde libros.json,
actualiza a entrada en visualizacions.json e rexenera a portada.

Uso: python3 render.py   (engadir.py chámao ao rematar)
"""
import base64
import json
import re
import subprocess
import tempfile
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SLUG = "biblioteca-sustentable"
OUT = ROOT / "v" / SLUG
EIXOS = ("fund", "eco", "clima", "bio", "rural", "etica")
MESES = ["xaneiro", "febreiro", "marzo", "abril", "maio", "xuño", "xullo",
         "agosto", "setembro", "outubro", "novembro", "decembro"]


def validar(libros):
    for b in libros:
        if b["eixo"] not in EIXOS:
            raise SystemExit(f"Eixo descoñecido «{b['eixo']}» en {b['titulo']}")
        if b.get("capa") and not (OUT / "capas" / b["capa"]).exists():
            raise SystemExit(f"Falta capas/{b['capa']}")


def miniatura(libros):
    """Mosaico 3×3 coas portadas «Comezar aquí» (as nove máis recentes por ano)."""
    sel = [b for b in libros if b.get("capa") and b.get("comezar")]
    sel = sorted(sel, key=lambda b: b["ano"])[-9:]
    w, h, gap = 184, 276, 24
    x0 = (600 - 3 * w - 2 * gap) // 2
    cells = []
    with tempfile.TemporaryDirectory() as tmp:
        for k, b in enumerate(sel):
            small = Path(tmp) / f"{k}.jpg"
            subprocess.run(["sips", "-Z", "300", str(OUT / "capas" / b["capa"]), "--out", str(small)],
                           check=True, capture_output=True)
            data = base64.b64encode(small.read_bytes()).decode()
            x, y = x0 + (k % 3) * (w + gap), -60 + (k // 3) * (h + gap)
            cells.append(f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice" '
                         f'href="data:image/jpeg;base64,{data}"/>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
            '<rect width="600" height="600" fill="#E8EFE3"/>' + "".join(cells) + "</svg>")


def main():
    libros = json.loads((HERE / "libros.json").read_text(encoding="utf-8"))
    validar(libros)
    n = len(libros)
    ultima = max(b["engadido"] for b in libros)
    d = date.fromisoformat(ultima)
    simbolo = re.search(r"<g[^>]*>(.*)</g>", (ROOT / "assets/logos/favicon.svg").read_text(), re.S)
    simbolo = re.sub(r'\s*class="st0"', "", simbolo.group(1)) if simbolo else ""
    tpl = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
    html = (tpl.replace("{{LIBROS}}", json.dumps(libros, ensure_ascii=False, indent=0).replace("</", "<\\/"))
               .replace("{{N}}", str(n))
               .replace("{{SIMBOLO}}", simbolo)
               .replace("{{ACTUALIZADA}}", f"{d.day} de {MESES[d.month - 1]} de {d.year}"))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "index.html").write_text(html, encoding="utf-8")
    (OUT / "thumb.svg").write_text(miniatura(libros), encoding="utf-8")

    man_path = ROOT / "visualizacions.json"
    man = json.loads(man_path.read_text(encoding="utf-8"))
    entrada = {
        "slug": SLUG,
        "titulo": "Biblioteca Sustentable",
        "entradilla": f"{n} libros para entender a crise ecosocial e pensar saídas, dos clásicos de Carson e Meadows ao postcrecemento, o clima e o mundo rural. Unha lista viva que medra co tempo.",
        "data": "2026-10-26",
        "temas": ["Lecturas", "Sustentabilidade"],
        "formato": "Biblioteca",
        "fontes": "Selección FGS · portadas de Open Library",
    }
    man = [v for v in man if v["slug"] != SLUG] + [entrada]
    man_path.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    subprocess.run(["python3", str(ROOT / "build.py")], check=True)
    print(f"v/{SLUG}/ xerado con {n} libros ({sum(1 for b in libros if b.get('capa'))} con portada)")


if __name__ == "__main__":
    main()

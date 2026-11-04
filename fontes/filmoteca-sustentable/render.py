#!/usr/bin/env python3
"""Xera v/filmoteca-sustentable/index.html e thumb.svg desde documentais.json,
actualiza a entrada en visualizacions.json e rexenera a portada.

Uso: python3 render.py   (engadir.py chámao ao rematar)
"""
import base64
import json
import subprocess
import tempfile
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SLUG = "filmoteca-sustentable"
OUT = ROOT / "v" / SLUG
EIXOS = ("fund", "eco", "clima", "bio", "rural", "etica")
MESES = ["xaneiro", "febreiro", "marzo", "abril", "maio", "xuño", "xullo",
         "agosto", "setembro", "outubro", "novembro", "decembro"]


def validar(docs):
    for d in docs:
        if d["eixo"] not in EIXOS:
            raise SystemExit(f"Eixo descoñecido «{d['eixo']}» en {d['titulo']}")
        if d.get("cartel") and not (OUT / "carteis" / d["cartel"]).exists():
            raise SystemExit(f"Falta carteis/{d['cartel']}")


def miniatura(docs):
    """Mosaico 3×3 cos carteis «Comezar aquí» verticais (os nove máis recentes por ano)."""
    sel = []
    with tempfile.TemporaryDirectory() as tmp:
        for d in sorted((d for d in docs if d.get("cartel") and d.get("comezar")), key=lambda d: d["ano"]):
            small = Path(tmp) / f"{len(sel)}.jpg"
            # JPEG pequeno e comprimido: o thumb carga na portada con decenas de pezas
            subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "55", "-Z", "200",
                            str(OUT / "carteis" / d["cartel"]), "--out", str(small)],
                           check=True, capture_output=True)
            dims = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(small)],
                                  check=True, capture_output=True, text=True).stdout.split()
            if int(dims[-3]) < int(dims[-1]):  # só carteis verticais
                sel.append(base64.b64encode(small.read_bytes()).decode())
    sel = sel[-9:]
    w, h, gap = 184, 276, 24
    x0 = (600 - 3 * w - 2 * gap) // 2
    cells = [f'<image x="{x0 + (k % 3) * (w + gap)}" y="{-60 + (k // 3) * (h + gap)}" width="{w}" height="{h}" '
             f'preserveAspectRatio="xMidYMid slice" href="data:image/jpeg;base64,{data}"/>'
             for k, data in enumerate(sel)]
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
            '<rect width="600" height="600" fill="#1A1A17"/>' + "".join(cells) + "</svg>")


def main():
    docs = json.loads((HERE / "documentais.json").read_text(encoding="utf-8"))
    validar(docs)
    n = len(docs)
    d = date.fromisoformat(max(x["engadido"] for x in docs))
    tpl = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
    html = (tpl.replace("{{DOCS}}", json.dumps(docs, ensure_ascii=False, indent=0).replace("</", "<\\/"))
               .replace("{{N}}", str(n))
               .replace("{{ACTUALIZADA}}", f"{d.day} de {MESES[d.month - 1]} de {d.year}"))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "index.html").write_text(html, encoding="utf-8")
    (OUT / "thumb.svg").write_text(miniatura(docs), encoding="utf-8")

    man_path = ROOT / "visualizacions.json"
    man = json.loads(man_path.read_text(encoding="utf-8"))
    entrada = {
        "slug": SLUG,
        "titulo": "Filmoteca Sustentable",
        "entradilla": f"{n} documentais para entender a crise ecosocial e ver saídas, de Koyaanisqatsi e Home a Demain e Honeyland. Fai parella coa Biblioteca Sustentable e medra co tempo.",
        "data": "2026-11-04",
        "temas": ["Documentais", "Sustentabilidade"],
        "formato": "Filmoteca",
        "fontes": "Selección FGS · carteis da Wikipedia",
    }
    man = [v for v in man if v["slug"] != SLUG] + [entrada]
    man_path.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    subprocess.run(["python3", str(ROOT / "build.py")], check=True)
    print(f"v/{SLUG}/ xerado con {n} documentais ({sum(1 for x in docs if x.get('cartel'))} con cartel)")


if __name__ == "__main__":
    main()

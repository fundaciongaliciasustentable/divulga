#!/usr/bin/env python3
"""Engade un libro a libros.json, descarga a portada de Open Library e rexenera.

  python3 engadir.py --titulo "Overshoot" --autoria "William R. Catton" --ano 1980 \
      --eixo fund --descricion "..." [--comezar] [--isbn 9780252009884] [--capa-id 123]

Eixos: fund, eco, clima, bio, rural, etica. Sen --isbn nin --capa-id busca por
título e apelido. Comproba sempre a portada descargada: Open Library ás veces
devolve outra edición, unha tapa de biblioteca ou unha páxina interior.
Para cambiar só a portada dun libro xa engadido: --so-capa --titulo "..." --isbn/--capa-id.
"""
import argparse
import json
import re
import subprocess
import sys
import unicodedata
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAPAS = HERE.parents[1] / "v" / "biblioteca-sustentable" / "capas"
UA = {"User-Agent": "FGS-Divulga/1.0 (divulga.galiciasustentable.org)"}


def slug(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:60]


def busca_capa(titulo, autoria):
    apelido = autoria.split(",")[0].split(" e ")[0].split()[-1]
    for q in ({"title": titulo, "author": apelido}, {"q": f"{titulo} {apelido}"}):
        url = "https://openlibrary.org/search.json?" + urllib.parse.urlencode(
            {**q, "limit": 5, "fields": "title,author_name,cover_i"})
        docs = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))["docs"]
        for d in docs:
            if d.get("cover_i"):
                print(f"  atopado: {d.get('title')} · {', '.join(d.get('author_name', []))} · capa {d['cover_i']}")
                return f"https://covers.openlibrary.org/b/id/{d['cover_i']}-M.jpg"
    return None


def descarga(url, dest):
    try:
        data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
    except Exception as e:
        print(f"  sen portada ({e})")
        return False
    if len(data) < 2000:
        print("  sen portada (imaxe baleira)")
        return False
    dest.write_bytes(data)
    return True


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--titulo", required=True)
    p.add_argument("--autoria")
    p.add_argument("--ano", type=int)
    p.add_argument("--eixo", choices=["fund", "eco", "clima", "bio", "rural", "etica"])
    p.add_argument("--descricion")
    p.add_argument("--comezar", action="store_true")
    p.add_argument("--isbn")
    p.add_argument("--capa-id", type=int)
    p.add_argument("--so-capa", action="store_true")
    a = p.parse_args()

    path = HERE / "libros.json"
    libros = json.loads(path.read_text(encoding="utf-8"))
    existente = next((b for b in libros if b["titulo"].lower() == a.titulo.lower()), None)
    if a.so_capa:
        if not existente:
            sys.exit(f"Non está «{a.titulo}»")
        libro = existente
    else:
        if existente:
            sys.exit(f"«{a.titulo}» xa está na biblioteca")
        falta = [k for k in ("autoria", "ano", "eixo", "descricion") if not getattr(a, k)]
        if falta:
            sys.exit("Faltan: " + ", ".join("--" + k for k in falta))
        libro = {"titulo": a.titulo, "autoria": a.autoria, "ano": a.ano, "eixo": a.eixo,
                 "comezar": a.comezar, "descricion": a.descricion, "capa": None,
                 "engadido": date.today().isoformat()}
        libros.append(libro)

    if a.capa_id:
        url = f"https://covers.openlibrary.org/b/id/{a.capa_id}-M.jpg"
    elif a.isbn:
        url = f"https://covers.openlibrary.org/b/isbn/{a.isbn.replace('-', '')}-M.jpg?default=false"
    else:
        url = busca_capa(libro["titulo"], libro["autoria"])
    nome = slug(libro["titulo"]) + ".jpg"
    if url and descarga(url, CAPAS / nome):
        libro["capa"] = nome
        print(f"  portada: v/biblioteca-sustentable/capas/{nome}")

    path.write_text(json.dumps(libros, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    subprocess.run([sys.executable, str(HERE / "render.py")], check=True)


if __name__ == "__main__":
    main()

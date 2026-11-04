#!/usr/bin/env python3
"""Engade un documental a documentais.json, descarga o cartel da Wikipedia e rexenera.

  python3 engadir.py --titulo "Honeyland" --direccion "Ljubomir Stefanov e Tamara Kotevska" \
      --ano 2019 --eixo rural --descricion "..." [--comezar] [--wiki "Honeyland"] [--lingua en]

Eixos: fund, eco, clima, bio, rural, etica. --wiki é o título do artigo da
Wikipedia (por defecto, o título do filme); --lingua, a edición (en, es, gl...).
Comproba sempre o cartel descargado: ás veces o artigo leva unha foto do
director ou dun fotograma en vez do cartel.

  python3 engadir.py --so-cartel --titulo "..." [--wiki ... | --cartel-url https://upload.wikimedia.org/...]
      cambia só o cartel dun documental xa engadido.
  python3 engadir.py --pendentes
      busca o cartel de todos os que aínda non teñen.
"""
import argparse
import json
import re
import subprocess
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
CARTEIS = HERE.parents[1] / "v" / "filmoteca-sustentable" / "carteis"
UA = {"User-Agent": "FGS-Divulga/1.0 (https://divulga.galiciasustentable.org)"}


def slug(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:60]


def url_cartel(artigo, lingua="en"):
    """Imaxe principal do artigo da Wikipedia (nos filmes, case sempre o cartel)."""
    q = urllib.parse.urlencode({"action": "query", "format": "json", "redirects": 1, "titles": artigo,
                                "prop": "pageimages", "piprop": "thumbnail|name", "pithumbsize": 500,
                                # os carteis non son imaxes libres: sen «any» a API non os devolve
                                "pilicense": "any"})
    d = json.load(urllib.request.urlopen(urllib.request.Request(
        f"https://{lingua}.wikipedia.org/w/api.php?{q}", headers=UA), timeout=30))
    for p in d.get("query", {}).get("pages", {}).values():
        if "thumbnail" in p:
            print(f"  {lingua}.wikipedia «{p['title']}» → {p.get('pageimage')}")
            return p["thumbnail"]["source"]
    print(f"  {lingua}.wikipedia «{artigo}»: sen imaxe")
    return None


def descarga(url, dest):
    for intento in range(4):
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
            break
        except urllib.error.HTTPError as e:
            # Wikimedia corta (429) se se piden moitas imaxes seguidas
            if e.code != 429 or intento == 3:
                print(f"  sen cartel ({e})")
                return False
            time.sleep(10 * (intento + 1))
        except Exception as e:
            print(f"  sen cartel ({e})")
            return False
    if len(data) < 2000:
        print("  sen cartel (imaxe baleira)")
        return False
    dest.write_bytes(data)
    return True


def pon_cartel(doc, url=None, artigo=None, lingua="en"):
    artigo = artigo or doc.get("wiki") or doc["titulo"]
    m = re.match(r"([a-z]{2,3}):(.+)", artigo)  # «fr:Tout peut changer» → outra Wikipedia
    if m:
        lingua, artigo = m.groups()
    url = url or url_cartel(artigo, lingua)
    ext = (Path(urllib.parse.urlparse(url).path).suffix.lower() if url else "") or ".jpg"
    ext = ext if ext in (".jpg", ".jpeg", ".png", ".webp") else ".jpg"
    nome = slug(doc["titulo"]) + ext
    if url and descarga(url, CARTEIS / nome):
        doc["cartel"] = nome
        print(f"  cartel: v/filmoteca-sustentable/carteis/{nome}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--titulo")
    p.add_argument("--direccion")
    p.add_argument("--ano", type=int)
    p.add_argument("--eixo", choices=["fund", "eco", "clima", "bio", "rural", "etica"])
    p.add_argument("--descricion")
    p.add_argument("--comezar", action="store_true")
    p.add_argument("--wiki")
    p.add_argument("--lingua", default="en")
    p.add_argument("--cartel-url")
    p.add_argument("--so-cartel", action="store_true")
    p.add_argument("--pendentes", action="store_true")
    a = p.parse_args()

    path = HERE / "documentais.json"
    docs = json.loads(path.read_text(encoding="utf-8"))
    CARTEIS.mkdir(parents=True, exist_ok=True)

    if a.pendentes:
        for d in docs:
            if not d.get("cartel"):
                print(d["titulo"])
                pon_cartel(d)
                time.sleep(3)
    else:
        if not a.titulo:
            sys.exit("Falta --titulo")
        existente = next((d for d in docs if d["titulo"].lower() == a.titulo.lower()), None)
        if a.so_cartel:
            if not existente:
                sys.exit(f"Non está «{a.titulo}»")
            doc = existente
            if a.wiki:
                doc["wiki"] = a.wiki
        else:
            if existente:
                sys.exit(f"«{a.titulo}» xa está nos documentais")
            falta = [k for k in ("direccion", "ano", "eixo", "descricion") if not getattr(a, k)]
            if falta:
                sys.exit("Faltan: " + ", ".join("--" + k for k in falta))
            doc = {"titulo": a.titulo, "direccion": a.direccion, "ano": a.ano, "eixo": a.eixo,
                   "comezar": a.comezar, "descricion": a.descricion, "wiki": a.wiki or a.titulo,
                   "cartel": None, "engadido": date.today().isoformat()}
            docs.append(doc)
        pon_cartel(doc, a.cartel_url, a.wiki, a.lingua)

    path.write_text(json.dumps(docs, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    subprocess.run([sys.executable, str(HERE / "render.py")], check=True)


if __name__ == "__main__":
    main()

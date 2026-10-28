#!/usr/bin/env python3
"""Xera unha imaxe para compartir (v/<slug>/og.jpg, 1200×630) para CADA
visualización de visualizacions.json, co mesmo tratamento que
assets/img/og-divulga.jpg (foto + degradado + logo), pero co título e a
entradilla de cada peza — así cada unha ten algo propio que amosar ao
compartila en redes, non a mesma imaxe xenérica.

Precisa Pillow e as fontes Playfair Display e Lato (Google Fonts, OFL):
  python3 scripts/og_pezas.py <PlayfairDisplay[wght].ttf> <Lato-Regular.ttf> [slug...]

Sen slugs, rexenera as imaxes de todas as pezas do manifesto.
"""
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
playfair, lato = sys.argv[1], sys.argv[2]
so_slugs = set(sys.argv[3:])
W, H = 1200, 630
MARXE = 64


def fondo():
    foto = Image.open(ROOT / "assets/img/heroe-2400.jpg").convert("RGB")
    s = max(W / foto.width, H / foto.height)
    foto = foto.resize((round(foto.width * s), round(foto.height * s)), Image.LANCZOS)
    x0 = (foto.width - W) // 2
    y0 = int((foto.height - H) * 0.55)
    img = foto.crop((x0, y0, x0 + W, y0 + H))
    neg = (26, 26, 23)
    capa = Image.new("RGBA", (W, H))
    px = capa.load()
    for y in range(H):
        for x in range(W):
            a = 0.2 + 0.64 * (y / H) ** 1.3 + 0.32 * max(0, 1 - x / (W * 0.8))
            px[x, y] = (*neg, int(255 * min(a, 0.9)))
    return Image.alpha_composite(img.convert("RGBA"), capa)


def envolver(draw, texto, font, largo_max):
    liñas, actual = [], ""
    for palabra in texto.split():
        proba = f"{actual} {palabra}".strip()
        if draw.textlength(proba, font=font) <= largo_max:
            actual = proba
        else:
            if actual:
                liñas.append(actual)
            actual = palabra
    if actual:
        liñas.append(actual)
    return liñas


def axustar_titulo(draw, texto, largo_max, alto_max):
    for tam in range(72, 31, -4):
        font = ImageFont.truetype(playfair, tam)
        font.set_variation_by_axes([700])
        liñas = envolver(draw, texto, font, largo_max)
        alto_liña = int(tam * 1.12)
        if len(liñas) <= 3 and alto_liña * len(liñas) <= alto_max:
            return font, liñas, alto_liña
    return font, liñas[:3], alto_liña


OG_RE = {
    "titulo": re.compile(r'<meta property="og:title" content="([^"]*)">'),
    "entradilla": re.compile(r'<meta property="og:description" content="([^"]*)">'),
}


def copia_social(v):
    """A imaxe usa o og:title/og:description propios da peza (o gancho
    social que vai citar calquera rede), non o titulo/entradilla do
    manifesto (ese é o da tarxeta na grella da portada) — adoitan diferir."""
    txt = (ROOT / "v" / v["slug"] / "index.html").read_text(encoding="utf-8")
    copia = dict(v)
    for campo, regex in OG_RE.items():
        m = regex.search(txt)
        if m:
            copia[campo] = m.group(1)
    return copia


def xerar(v, etiqueta, corpo):
    v = copia_social(v)
    img = fondo()
    d = ImageDraw.Draw(img)
    branco, verde_mc = (255, 255, 255), (232, 239, 227)
    largo_max = W - MARXE * 2

    logo = Image.open(ROOT / "assets/logos/logo-fgs-horizontal-branco.png").convert("RGBA")
    lh = 60
    logo = logo.resize((round(logo.width * lh / logo.height), lh), Image.LANCZOS)
    img.alpha_composite(logo, (MARXE, 46))

    kicker = (v.get("formato") or "Visualización de datos").upper()
    ky = 128
    d.line([(MARXE + 2, ky), (MARXE + 2, ky + 24)], fill=verde_mc, width=2)
    d.text((MARXE + 18, ky), kicker, font=etiqueta, fill=verde_mc)

    font_tit, liñas_tit, alto_liña = axustar_titulo(d, v["titulo"], largo_max, 230)
    y = 190
    for liña in liñas_tit:
        d.text((MARXE, y), liña, font=font_tit, fill=branco)
        y += alto_liña

    y += 14
    liñas_dek = envolver(d, v["entradilla"], corpo, largo_max)
    if len(liñas_dek) > 2:
        liñas_dek = liñas_dek[:2]
        ultima = liñas_dek[1]
        while ultima and d.textlength(ultima + "…", font=corpo) > largo_max:
            ultima = ultima.rsplit(" ", 1)[0] if " " in ultima else ultima[:-1]
        liñas_dek[1] = ultima + "…"
    for liña in liñas_dek:
        d.text((MARXE, y), liña, font=corpo, fill=(255, 255, 255, 235))
        y += 34

    d.text((MARXE, H - 56), f"divulga.galiciasustentable.org/v/{v['slug']}/", font=etiqueta, fill=verde_mc)

    out = ROOT / "v" / v["slug"] / "og.jpg"
    img.convert("RGB").save(out, quality=86, optimize=True, progressive=True)
    return out


def main():
    vs = json.loads((ROOT / "visualizacions.json").read_text(encoding="utf-8"))
    if so_slugs:
        vs = [v for v in vs if v["slug"] in so_slugs]
    etiqueta = ImageFont.truetype(lato, 22)
    corpo = ImageFont.truetype(lato, 27)
    for v in vs:
        out = xerar(v, etiqueta, corpo)
        print("ok:", out.relative_to(ROOT))
    print(f"xeradas {len(vs)} imaxe(s)")


if __name__ == "__main__":
    main()

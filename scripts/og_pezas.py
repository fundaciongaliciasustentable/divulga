#!/usr/bin/env python3
"""Xera as imaxes para compartir de CADA visualización de
visualizacions.json, co mesmo tratamento que assets/img/og-divulga.jpg
(foto + degradado + logo) pero co título e a entradilla de cada peza:

  v/<slug>/og.jpg       1200×630  — redes con "link preview" (X, FB, WhatsApp...)
  v/<slug>/historia.jpg 1080×1920 — para descargar e subir a man a Instagram
                                    Stories ou TikTok (eses non len a ligazón)

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
BRANCO, VERDE_MC, NEGRO = (255, 255, 255), (232, 239, 227), (26, 26, 23)

# Un deseño para cada formato: tamaño, recorte da foto (fracción do que
# sobra de ancho/alto tras escalar, 0=esquerda/arriba, 1=dereita/abaixo) e
# posición de cada elemento. Mesma foto e tratamento, só cambian as
# proporcións porque un vai en horizontal e outro en vertical.
FORMATOS = {
    "og": dict(
        ficheiro="og.jpg", W=1200, H=630, marxe=64, recorte=(0.5, 0.55),
        logo_alto=60, logo_pos=(64, 46), kicker_y=128,
        titulo_y=190, titulo_alto_max=230, titulo_tam=range(72, 31, -4),
        dek_gap=14, dek_liña=34, dek_max_liñas=2, url_y=630 - 56,
        kicker_tam=22, dek_tam=27,
    ),
    "historia": dict(
        ficheiro="historia.jpg", W=1080, H=1920, marxe=76, recorte=(0.63, 0.38),
        logo_alto=70, logo_pos=(76, 96), kicker_y=840,
        titulo_y=900, titulo_alto_max=520, titulo_tam=range(100, 47, -6),
        dek_gap=22, dek_liña=46, dek_max_liñas=3, url_y=1920 - 110,
        kicker_tam=30, dek_tam=36,
    ),
}


def fondo(w, h, recorte):
    foto = Image.open(ROOT / "assets/img/heroe-2400.jpg").convert("RGB")
    s = max(w / foto.width, h / foto.height)
    foto = foto.resize((round(foto.width * s), round(foto.height * s)), Image.LANCZOS)
    x0 = round((foto.width - w) * recorte[0])
    y0 = round((foto.height - h) * recorte[1])
    img = foto.crop((x0, y0, x0 + w, y0 + h))
    capa = Image.new("RGBA", (w, h))
    px = capa.load()
    for y in range(h):
        for x in range(w):
            a = 0.2 + 0.64 * (y / h) ** 1.3 + 0.32 * max(0, 1 - x / (w * 0.8))
            px[x, y] = (*NEGRO, int(255 * min(a, 0.9)))
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


def recortar_con_elipsis(draw, liñas, max_liñas, font, largo_max):
    if len(liñas) <= max_liñas:
        return liñas
    liñas = liñas[:max_liñas]
    ultima = liñas[-1]
    while ultima and draw.textlength(ultima + "…", font=font) > largo_max:
        ultima = ultima.rsplit(" ", 1)[0] if " " in ultima else ultima[:-1]
    liñas[-1] = ultima + "…"
    return liñas


def axustar_titulo(draw, texto, largo_max, alto_max, gama_tam):
    font = liñas = alto_liña = None
    for tam in gama_tam:
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


def xerar(v, formato, l):
    img = fondo(l["W"], l["H"], l["recorte"])
    d = ImageDraw.Draw(img)
    marxe, largo_max = l["marxe"], l["W"] - l["marxe"] * 2
    etiqueta = ImageFont.truetype(lato, l["kicker_tam"])
    corpo = ImageFont.truetype(lato, l["dek_tam"])

    logo = Image.open(ROOT / "assets/logos/logo-fgs-horizontal-branco.png").convert("RGBA")
    lh = l["logo_alto"]
    logo = logo.resize((round(logo.width * lh / logo.height), lh), Image.LANCZOS)
    img.alpha_composite(logo, l["logo_pos"])

    kicker = (v.get("formato") or "Visualización de datos").upper()
    ky = l["kicker_y"]
    d.line([(marxe + 2, ky), (marxe + 2, ky + round(l["kicker_tam"] * 1.1))], fill=VERDE_MC, width=2)
    d.text((marxe + 18, ky), kicker, font=etiqueta, fill=VERDE_MC)

    font_tit, liñas_tit, alto_liña = axustar_titulo(d, v["titulo"], largo_max, l["titulo_alto_max"], l["titulo_tam"])
    y = l["titulo_y"]
    for liña in liñas_tit:
        d.text((marxe, y), liña, font=font_tit, fill=BRANCO)
        y += alto_liña

    y += l["dek_gap"]
    liñas_dek = recortar_con_elipsis(d, envolver(d, v["entradilla"], corpo, largo_max), l["dek_max_liñas"], corpo, largo_max)
    for liña in liñas_dek:
        d.text((marxe, y), liña, font=corpo, fill=(255, 255, 255, 235))
        y += l["dek_liña"]

    d.text((marxe, l["url_y"]), f"divulga.galiciasustentable.org/v/{v['slug']}/", font=etiqueta, fill=VERDE_MC)

    out = ROOT / "v" / v["slug"] / l["ficheiro"]
    img.convert("RGB").save(out, quality=86, optimize=True, progressive=True)
    return out


def main():
    vs = json.loads((ROOT / "visualizacions.json").read_text(encoding="utf-8"))
    if so_slugs:
        vs = [v for v in vs if v["slug"] in so_slugs]
    for v in vs:
        v = copia_social(v)
        for formato, l in FORMATOS.items():
            out = xerar(v, formato, l)
            print("ok:", out.relative_to(ROOT))
    print(f"xeradas {len(vs)} peza(s) × {len(FORMATOS)} formato(s)")


if __name__ == "__main__":
    main()

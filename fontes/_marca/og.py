#!/usr/bin/env python3
"""Xera assets/img/og-divulga.jpg (1200×630), a imaxe para compartir en redes.

Mesma foto e mesmo tratamento que a portada de fundaciongaliciasustentable.gal.
Precisa Pillow e as fontes Playfair Display e Lato (Google Fonts, OFL):
  python3 og.py <PlayfairDisplay[wght].ttf> <Lato-Regular.ttf>
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
playfair, lato = sys.argv[1], sys.argv[2]
W, H = 1200, 630

foto = Image.open(ROOT / "assets/img/heroe-2400.jpg").convert("RGB")
s = max(W / foto.width, H / foto.height)
foto = foto.resize((round(foto.width * s), round(foto.height * s)), Image.LANCZOS)
x0 = (foto.width - W) // 2
y0 = int((foto.height - H) * 0.55)
img = foto.crop((x0, y0, x0 + W, y0 + H))

# Degradado escuro (--gs-negro) cara abaixo e á esquerda, como o heroe da web
neg = (26, 26, 23)
capa = Image.new("RGBA", (W, H))
px = capa.load()
for y in range(H):
    for x in range(W):
        a = 0.15 + 0.62 * (y / H) ** 1.4 + 0.30 * max(0, 1 - x / (W * 0.75))
        px[x, y] = (*neg, int(255 * min(a, 0.88)))
img = Image.alpha_composite(img.convert("RGBA"), capa)

logo = Image.open(ROOT / "assets/logos/logo-fgs-horizontal-branco.png").convert("RGBA")
lh = 78
logo = logo.resize((round(logo.width * lh / logo.height), lh), Image.LANCZOS)
img.alpha_composite(logo, (64, 52))

d = ImageDraw.Draw(img)
titulo = ImageFont.truetype(playfair, 150)
titulo.set_variation_by_axes([400])
etiqueta = ImageFont.truetype(lato, 24)
corpo = ImageFont.truetype(lato, 30)
branco, verde_mc = (255, 255, 255), (232, 239, 227)

d.line([(66, 306), (66, 334)], fill=verde_mc, width=2)
d.text((82, 306), "Visualizacións de datos", font=etiqueta, fill=verde_mc)
d.text((60, 328), "Divulga", font=titulo, fill=branco)
d.text((66, 532), "Datos públicos para entender Galicia", font=corpo, fill=branco)
d.text((66, 574), "divulga.galiciasustentable.org", font=etiqueta, fill=verde_mc)

out = ROOT / "assets/img/og-divulga.jpg"
img.convert("RGB").save(out, quality=86, optimize=True, progressive=True)
print("ok:", out)

#!/usr/bin/env python3
"""
«O solo galego en detalle»: adapta o cartograma deseñado para o sitio vello de AGADER
(orixinal.html, copia de AGADER/web_v1/cartograma-solo.html) ao formato de Divulga.

Primeiro corrixe as cifras cos datos oficiais (corrixir.py, datos_oficiais.json; precisa shapely).
Despois, cambios de formato (o deseño queda igual):
- cabeceira: título, descrición e etiquetas og; favicon, divulga.css e o botón «Compartir»;
- fóra o gs.css, a comporta de contrasinal e o site.js do sitio vello;
- fóra o logo PNG da cabeceira (356 KB): a marca xa vai na barra .dv-bar;
- o pé antigo substitúese polo .dv-foot común; --ink/--paper/--muted para a barra e o pé.

Uso: python3 fontes/solo-galicia/adaptar.py   (desde a raíz de divulga)
"""
import re
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
SAIDA = RAIZ / 'v' / 'solo-galicia' / 'index.html'
URL = 'https://divulga.galiciasustentable.org/v/solo-galicia/'

TITULO = 'O solo galego en detalle'
DESCRICION = ('A silueta de Galicia partida en zonas proporcionais ao que hai sobre o solo: forestal, '
              'agrario, artificial e auga. E dentro do agrario, canto está sen aproveitamento.')
OG_TITULO = 'Galicia non é verde porque prospere'
OG_DESCRICION = 'A silueta de Galicia partida segundo o que hai no seu solo, e provincia a provincia.'


def substituir(txt, patron, novo, flags=re.S, contar=1):
    res, n = re.subn(patron, novo, txt, count=contar, flags=flags)
    assert n == contar, f'Non se atopou: {patron[:60]}'
    return res


def main():
    import sys
    sys.path.insert(0, str(AQUI))
    import corrixir   # datos oficiais: precisa shapely
    h = corrixir.aplicar((AQUI / 'orixinal.html').read_text(encoding='utf-8'))
    barra = (AQUI / '_chrome_bar.html').read_text(encoding='utf-8')
    pe = (AQUI / '_chrome_foot.html').read_text(encoding='utf-8')

    cab = (f'<title>{TITULO} — Divulga · Fundación Galicia Sustentable</title>\n'
           f'<meta name="description" content="{DESCRICION}">\n'
           f'<meta property="og:title" content="{OG_TITULO}">\n'
           f'<meta property="og:description" content="{OG_DESCRICION}">\n'
           f'<meta property="og:image" content="{URL}og.jpg">\n'
           '<meta property="og:image:width" content="1200">\n'
           '<meta property="og:image:height" content="630">\n'
           f'<meta property="og:url" content="{URL}">\n'
           '<meta name="twitter:card" content="summary_large_image">\n'
           '<link rel="icon" href="../../assets/logos/favicon.svg" type="image/svg+xml">')
    h = substituir(h, r'<title>.*?</title>', lambda m: cab)
    h = h.replace('initial-scale=1.0">', 'initial-scale=1, viewport-fit=cover">', 1)
    h = substituir(h, r'<link rel="stylesheet" href="assets/gs\.css">\n',
                   '<link rel="stylesheet" href="../../assets/css/divulga.css">\n'
                   '<script defer src="../../assets/js/compartir.js"></script>\n')
    h = substituir(h, r'<script src="assets/gate\.js"></script>', '')
    h = substituir(h, r'<script src="assets/site\.js" defer></script>\n?', '')
    # cores que len a barra e o pé de Divulga
    h = substituir(h, r':root\{\n', ':root{\n  --ink:#1A1A17; --paper:#F5F5F0; --muted:#6C6C64; --line:#E8E8E2;\n')
    # logo PNG da cabeceira: a marca xa está na barra
    h = substituir(h, r'\s*<img src="data:image/png;base64,[A-Za-z0-9+/=]+" alt="Fundación Galicia Sustentable">', '')
    # pé antigo → pé común
    h = substituir(h, r'<footer>\s*<div class="gs-container">.*?</footer>', lambda m: pe)
    h = substituir(h, r'<body>\n', lambda m: '<body>\n' + barra + '\n')
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(h, encoding='utf-8')
    print(f'{SAIDA.relative_to(RAIZ)}: {len(h.encode()) / 1024:.0f} KB')
    miniatura(h)
    datos(h)


def datos(h):
    """datos.json: as cifras que mostra a peza (lendas de Galicia e das provincias), para reproducila."""
    import json
    gal = [{'uso': n, 'valor': v} for n, v in re.findall(r'<div class="li(?: sub)?"><i style="[^"]*"></i><span class="nm">([^<]+)</span><span class="v">([^<]+)</span>', h)]
    prov = {}
    for nome, bloque in re.findall(r'<h3>(A Coruña|Lugo|Ourense|Pontevedra)</h3>(.*?)</div>\s*</div>', h, re.S):
        prov[nome] = {'resumo': re.search(r'<p class="sub">([^<]+)</p>', bloque).group(1),
                      'usos': re.findall(r'</i>([^<]+)</span>', bloque)}
    fontes = re.findall(r'<p class="fonte">([^<]+)</p>', h)
    out = {'galicia': gal, 'provincias': prov, 'fontes_das_graficas': fontes,
           'nota': 'Cifras tal como as mostra a peza (deseño orixinal de AGADER/web_v1, maio de 2026). Ver README.md: varias están pendentes de verificar.'}
    (AQUI / 'datos.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'datos.json: {len(gal)} usos de Galicia, {len(prov)} provincias')


def miniatura(h):
    """thumb.svg 600×600: o cartograma de Galicia da propia peza, sen rótulos e coas cores resoltas."""
    cores = dict(re.findall(r'--(c-[a-z-]+):(#[0-9A-Fa-f]{6})', h))
    svg = re.search(r'<svg viewBox="([^"]+)"[^>]*aria-label="Cartograma do solo de Galicia">(.*?)</svg>', h, re.S)
    vb, corpo = svg.group(1), svg.group(2)
    corpo = re.sub(r'<text.*?</text>', '', corpo, flags=re.S)
    corpo = re.sub(r'var\(--(c-[a-z-]+)\)', lambda m: cores[m.group(1)], corpo)
    corpo = re.sub(r'class="contorno"', 'fill="none" stroke="#1A1A17" stroke-width="2"', corpo)  # o contorno é só liña
    corpo = re.sub(r'\s+class="[^"]*"', '', corpo)
    corpo = re.sub(r'(\d+\.\d)\d+', r'\1', corpo)          # unha cifra decimal abonda nunha miniatura
    corpo = re.sub(r'>\s+<', '><', corpo).strip()
    t = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
         '<rect width="600" height="600" fill="#F5F5F0"/>'
         f'<svg x="60" y="45" width="480" height="510" viewBox="{vb}" preserveAspectRatio="xMidYMid meet">'
         f'<g stroke="#F5F5F0" stroke-width="3" stroke-linejoin="round">{corpo}</g></svg></svg>\n')
    (SAIDA.parent / 'thumb.svg').write_text(t, encoding='utf-8')
    print(f'thumb.svg: {len(t.encode()) / 1024:.0f} KB')


if __name__ == '__main__':
    main()

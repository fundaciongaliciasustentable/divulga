"""
Corrixe a peza orixinal cos datos oficiais de datos_oficiais.json (6 de novembro de 2026):
- usos do solo de Galicia e das provincias: MAPA, Anuario 2025, táboa 3.3 (2024);
- artificial e arborado: IFN4 e IFCG 2024 (memoria do PLADIGA 2026);
- cortas de madeira 2025 e peso do sector: Xunta (cadea forestal-madeira 2025);
- terra abandonada: AGADER (presentación da Lei 11/2021).
Rexenera as zonas dos mapas (xeometria.py) e substitúe lendas, textos, gráficas e nota metodolóxica.
Cada substitución comproba que o texto orixinal existe: se o orixinal cambia, o script para.
"""
import json
import re
from pathlib import Path

import xeometria as X

AQUI = Path(__file__).resolve().parent
D = json.loads((AQUI / 'datos_oficiais.json').read_text(encoding='utf-8'))
U = D['usos']
PROV = ['A Coruña', 'Lugo', 'Ourense', 'Pontevedra']
ROTULO_SVG = {'A Coruña': 'coruna', 'Lugo': 'lugo', 'Ourense': 'ourense', 'Pontevedra': 'pontevedra'}
DESCR = {'A Coruña': 'costeira', 'Lugo': 'a maior, interior', 'Ourense': 'interior, a máis forestal', 'Pontevedra': 'a menor, costeira'}
CORTAS = D['cortas_2025']


def pc(v, d=1):
    return f'{v:.{d}f}'.replace('.', ',')


def mil(v):
    return f'{round(v):,}'.replace(',', '.')


def cotas(z):
    u = U[z]
    return {k: u[k] / u['total'] for k in ('forestal', 'pastos', 'cultivo', 'non_utilizada', 'outras')}


def pct(z, k):
    u = U[z]
    if k == 'agrario':
        return (u['cultivo'] + u['pastos'] + u['non_utilizada']) / u['total'] * 100
    return u[k] / u['total'] * 100


def m3ha(p):
    return CORTAS[p] / U[p]['forestal']


def cota_cortas(p):
    return CORTAS[p] / CORTAS['Galicia'] * 100


def rx(texto):
    """Patrón que acepta calquera espazado onde o texto ten espazos."""
    return r'\s*'.join(re.escape(p) for p in texto.split(' '))


def subst(h, patron, novo, n=1, literal=True):
    pat = rx(patron) if literal else patron
    res, k = re.subn(pat, lambda m: novo, h, flags=re.S)
    assert k == n, f'{k} coincidencias (esperaba {n}): {patron[:70]}'
    return res


# ---------- Mapas ----------
def _g(x, y, contido):
    return f'<g transform="translate({x:.1f},{y:.1f})" text-anchor="middle">{contido}</g>'


def mapa(svg, zona, rotulos_dentro):
    contorno = re.search(r'<path class="contorno" d="([^"]+)"/>', svg).group(1)
    z = X.repartir(X.anel(contorno), cotas(zona))
    cor = {'forestal': ('regiao', 'c-forestal'), 'pastos': ('subregiao', 'c-ag-gan'),
           'non_utilizada': ('subregiao', 'c-ag-sen'), 'cultivo': ('subregiao', 'c-ag-ali'),
           'outras': ('regiao', 'c-artificial')}
    rutas = ''.join(f'<path class="{c}" d="{X.ruta(z[k])}" fill="var(--{v})"/>' for k, (c, v) in cor.items())
    fx, fy = X.centro(z['forestal'])
    rot = _g(fx, fy, f'<text class="etq etq-pct" y="0">{round(pct(zona, "forestal"))}%</text>'
                     '<text class="etq etq-nom" y="22">FORESTAL</text>')
    if rotulos_dentro:
        for k, t in (('pastos', 'Pastos e prados'), ('cultivo', 'Cultivos'), ('outras', 'Artificial e auga')):
            x, y = X.centro(z[k])
            rot += _g(x, y, f'<text class="etq-d" y="0">{t}</text>')
    cab = re.match(r'<svg[^>]*>', svg).group(0)
    return f'{cab}{rutas}<path class="contorno" d="{contorno}"/>{rot}</svg>'


def mapas(h):
    def galicia(m):
        return mapa(m.group(0), 'Galicia', True)
    h, k = re.subn(r'<svg viewBox="[^"]+"[^>]*aria-label="Cartograma do solo de Galicia">.*?</svg>', galicia, h, flags=re.S)
    assert k == 1
    for p, r in ROTULO_SVG.items():
        h, k = re.subn(r'<svg viewBox="[^"]+"[^>]*aria-label="' + r + r'">.*?</svg>', lambda m, p=p: mapa(m.group(0), p, False), h, flags=re.S)
        assert k == 1, p
    return h


# ---------- Lendas ----------
def li(cor, nome, valor, sub=False):
    return (f'<div class="li{" sub" if sub else ""}"><i style="background:var(--{cor})"></i>'
            f'<span class="nm">{nome}</span><span class="v">{valor}</span></div>')


def lendas(h):
    g = 'Galicia'
    lenda = ('<div class="leyenda">\n'
             '          <div class="lg-grupo">Grandes usos</div>\n'
             f'          {li("c-forestal", "Forestal", pc(pct(g, "forestal")) + "%")}\n'
             f'          {li("c-artificial", "Artificial e auga", pc(pct(g, "outras")) + "%")}\n'
             f'          <div class="lg-grupo">Agrario · {pc(pct(g, "agrario"))}%</div>\n'
             f'          {li("c-ag-gan", "Pastos e prados", pc(pct(g, "pastos")) + "%", True)}\n'
             f'          {li("c-ag-ali", "Terras de cultivo", pc(pct(g, "cultivo")) + "%", True)}\n'
             f'          {li("c-ag-sen", "Agraria non utilizada", pc(pct(g, "non_utilizada")) + "%", True)}\n'
             '        </div>')
    h = subst(h, r'<div class="leyenda">.*?</div>\s*</div>', lenda + '\n      </div>', literal=False)
    h = subst(h, 'Catro grandes usos. A zona agraria, subdividida en tres compoñentes: pastos e forraxes, produción de alimentos e terra sen aproveitamento.',
              'Tres grandes usos. A zona agraria, subdividida en tres: pastos e prados, terras de cultivo e superficie agraria que xa non se utiliza.')
    for p in PROV:
        u = U[p]
        cab = f'<h3>{p}</h3><p class="sub">{mil(u["total"] / 100)} km² · {DESCR[p]} · forestal {round(pct(p, "forestal"))}%</p>'
        h = subst(h, r'<h3>' + re.escape(p) + r'</h3><p class="sub">[^<]*</p>', cab, literal=False)
        sp = lambda cor, t, sub=False: f'<span{" class=\"ml-sub\"" if sub else ""}><i style="background:var(--{cor})"></i>{t}</span>'
        ml = ('<div class="minileg">' + sp('c-forestal', f'Forestal {round(pct(p, "forestal"))}%')
              + sp('c-ag-sen', f'Agraria {round(pct(p, "agrario"))}%')
              + sp('c-ag-gan', f'Pastos e prados {pc(pct(p, "pastos"))}%', True)
              + sp('c-ag-ali', f'Cultivos {pc(pct(p, "cultivo"))}%', True)
              + sp('c-ag-sen', f'Non utilizada {pc(pct(p, "non_utilizada"))}%', True)
              + sp('c-artificial', f'Artificial e auga {pc(pct(p, "outras"))}%') + '</div>')
        i = h.index(cab)
        j = h.index('<div class="minileg">', i)
        k = h.index('</div>', j) + len('</div>')
        h = h[:j] + ml + h[k:]
    return h


# ---------- Textos ----------
def textos(h):
    g = 'Galicia'
    ag_gal = U[g]['cultivo'] + U[g]['pastos'] + U[g]['non_utilizada']
    E = D['espana_agrario']
    nu_es = E['non_utilizada'] / (E['cultivo'] + E['pastos'] + E['non_utilizada']) * 100
    nu_gal = U[g]['non_utilizada'] / ag_gal * 100
    ifn = D['ifn4']
    art_ifn = ifn['artificial'] / ifn['total'] * 100
    arb = ifn['arborado_ifcg_2024'] / ifn['forestal'] * 100
    S = D['sector_forestal_madeira']
    co, lu, ou, po = (m3ha(p) for p in PROV)
    ccl = cota_cortas('A Coruña') + cota_cortas('Lugo')
    T = [
        # cabeceira
        ('A silueta real de Galicia partida en zonas proporcionais aos principais usos do solo: artificial, auga continental, forestal e agrario.',
         'A silueta real de Galicia partida en zonas proporcionais aos grandes usos do solo: forestal, agrario, e artificial e auga.'),
        # lente
        ('O 35,7% do agrario parado, o monte que rende oito veces menos do que podería, non son usos do solo: son a ausencia deles.',
         'A terra agraria que deixou de traballarse e o monte que medrou enriba dela non son usos do solo: son a ausencia deles.'),
        # provincias
        ('Galicia non se divide por provincias: divídese pola distancia ao mar. Unha Galicia atlántica (A Coruña, Pontevedra), máis construída e co agrario máis vivo. Unha Galicia interior (Lugo, Ourense), abrumadoramente forestal.',
         f'Galicia non se divide por provincias. A costa (A Coruña, Pontevedra) concentra o construído: arredor do {round(pct("A Coruña", "outras"))}% do seu solo é artificial ou auga, o dobre ca no interior. E o interior non é un bloque: Lugo é a provincia máis agraria ({round(pct("Lugo", "agrario"))}% do solo, sobre todo pastos) e Ourense, a máis forestal ({round(pct("Ourense", "forestal"))}%).'),
        ('As catro provincias non son catro realidades. Son dúas.', 'As catro provincias non contan a historia do territorio.'),
        ('non falan de catro provincias: falan de <b>costa e interior</b>, unha fronteira real —ecolóxica e económica— que ningún decreto debuxou.',
         'non falan de catro provincias: falan de <b>costa e interior</b> e, dentro do interior, de dous modelos opostos, unha fronteira real —ecolóxica e económica— que ningún decreto debuxou.'),
        ('Ourense ten o maior monte de Galicia (~78%) e é a que menos produce: só o 5,1% das cortas. O seu verde non é riqueza forestal, é despoboamento convertido en matogueira.',
         f'Ourense ten a maior proporción de monte de Galicia ({round(pct("Ourense", "forestal"))}%) e é a que menos madeira corta por hectárea: {pc(ou)} m³, fronte a {pc(co)} na Coruña. O seu verde non é riqueza forestal: é, en boa parte, terra que deixou de traballarse.'),
    ]
    for a, b in T:
        h = subst(h, a, b)
    h = subst(h, r'<p>O contraste Lugo–Ourense é a proba:.*?</p>', (
        f'<p>O contraste Lugo–Ourense é a proba: as dúas son interiores, pero <b>Lugo mantén vivo o agrario</b> ({round(pct("Lugo", "agrario"))}% do solo) '
        f'e corta o {pc(cota_cortas("Lugo"))}% da madeira de Galicia, mentres <b>Ourense ten o agrario máis pequeno</b> ({round(pct("Ourense", "agrario"))}%) '
        f'e a maior proporción del sen utilizar ({pc(U["Ourense"]["non_utilizada"] / (U["Ourense"]["cultivo"] + U["Ourense"]["pastos"] + U["Ourense"]["non_utilizada"]) * 100)}% do agrario, fronte ao {pc(U["Lugo"]["non_utilizada"] / (U["Lugo"]["cultivo"] + U["Lugo"]["pastos"] + U["Lugo"]["non_utilizada"]) * 100)}% de Lugo). '
        'Interior non é destino; a diferenza non é a xeografía, é a xestión. '
        f'A Coruña demóstrao polo outro lado: costeira, cun {round(pct("A Coruña", "forestal"))}% de monte, corta o {pc(cota_cortas("A Coruña"))}% de toda a madeira de Galicia ({pc(co)} m³ por hectárea de monte). Verde e actividade si é posible. '
        f'Pontevedra, a máis pequena e densa, ten un {round(pct("Pontevedra", "outras"))}% de solo artificial ou auga, como A Coruña, e aínda así un {round(pct("Pontevedra", "forestal"))}% forestal.</p>'), literal=False)
    h = subst(h, 'O dato que o pecha: <b>A Coruña e Lugo concentran o 81,5%</b> das cortas de Galicia; Ourense e Pontevedra, menos do 19%.',
              f'O dato que o pecha: <b>A Coruña e Lugo concentran o {pc(ccl)}%</b> das cortas de Galicia; Ourense e Pontevedra, o {pc(100 - ccl)}%.')
    h = subst(h, 'Á primeira ollada parécense; o que cambia é o tipo de monte e canto agrario está sen uso.',
              'Á primeira ollada parécense; o que cambia é canto monte, canto agrario e canto construído ten cada unha.')

    # tira de catro cifras
    datos = [
        (r'<span class="cifra">3%</span>', '&lt;3%', 'O cemento que non vemos',
         f'Todo o artificial —cidades, polígonos, estradas, portos— non chega ao 3% de Galicia ({pc(art_ifn, 2)}%, IFN4). Vemos ladrillo, pisamos matogueira.'),
        (r'<span class="cifra">32,4%</span>', '1 de 3', 'Monte sen árbores',
         'Case un terzo do monte galego non está arborado: é matogueira ou terreo raso. Só pouco máis do 67% ten árbores (IFCG 2024).'),
        (r'<span class="cifra">35,7%</span>', '+500.000 ha', 'A terra que xa non se ve',
         f'De terra agraria abandonada ou infrautilizada, segundo AGADER. A estatística só rexistra {mil(U[g]["non_utilizada"])} ha como agraria non utilizada: o resto xa conta como monte.'),
        (r'<span class="cifra">1 / 8</span>', f'{pc(ou)} / {pc(co)}', 'Verde non é madeira',
         'Metros cúbicos cortados en 2025 por hectárea de monte en Ourense e na Coruña. O mesmo verde, case catro veces menos actividade.'),
    ]
    for ant, cifra, tit, desc in datos:
        h = subst(h, r'<div class="dato">\s*' + ant + r'.*?</div>',
                  f'<div class="dato">\n          <span class="cifra">{cifra}</span>\n          <span class="tit">{tit}</span>\n'
                  f'          <span class="desc">{desc}</span>\n        </div>', literal=False)

    # análise xeral
    h = subst(h, 'O 73% forestal soa a riqueza natural.', f'O {round(pct(g, "forestal"))}% forestal soa a riqueza natural.')
    h = subst(h, 'é só o <b>3% do territorio</b>. O que de verdade ocupa Galicia',
              f'non chega ao <b>3% do territorio</b> ({pc(art_ifn, 2)}% segundo o IFN4). O que de verdade ocupa Galicia')
    h = subst(h, r'<p>O 22% agrario tampouco é o que a palabra suxire\..*?</p>', (
        f'<p>O {round(pct(g, "agrario"))}% agrario tampouco é o que a palabra suxire. A metade son pastos e prados para o gando '
        f'({pc(pct(g, "pastos"))}% do territorio); as terras de cultivo ocupan o <b>{pc(pct(g, "cultivo"))}% do territorio</b> '
        f'({mil(U[g]["cultivo"])} ha).</p>'), literal=False)
    h = subst(h, r'<p class="frase">Dentro do agrario, a terra sen aproveitamento.*?</p>', (
        f'<p class="frase">A estatística agraria só ve {mil(U[g]["non_utilizada"])} hectáreas de terra agraria sen utilizar. AGADER calcula máis de 500.000. '
        'A diferenza non desapareceu: cubriuna o monte.</p>'), literal=False)
    h = subst(h, r'<p>É a maior bolsa de terra agraria infrautilizada do Estado:.*?</p>', (
        f'<p>Na estatística, o {pc(nu_gal)}% do agrario galego figura como non utilizado, fronte ao {pc(nu_es)}% de España. '
        'Pero a terra que se abandona non queda moito tempo como «agraria sen uso»: en poucos anos cóbrese de matogueira e pasa a contar como forestal. '
        'Por iso o abandono real é moito maior do que mide a estatística, e por iso o verde engana. '
        f'E co monte pasa o mesmo: non rende igual en todas partes. A Coruña corta {pc(co)} m³ de madeira por hectárea de monte; Ourense, {pc(ou)}. '
        f'Aínda así, a cadea forestal-madeira xa achega o {pc(S["pib_pct"])}% do PIB galego e máis de {mil(S["afiliados"])} afiliados á Seguridade Social ({S["ano"]}): '
        'o que se deixa de xerar co monte sen xestión é enorme.</p>'), literal=False)
    h = subst(h, 'Galicia ten terra de sobra: ten case un terzo do seu agrario parado e un monte que rende oito veces menos do que podería.',
              'Galicia ten terra de sobra: centos de miles de hectáreas de agrario abandonado e un monte que, en boa parte, ninguén xestiona.')

    # nota metodolóxica
    h = subst(h, r'<b>Nota metodolóxica\.</b>.*?localización\.', (
        '<b>Nota metodolóxica.</b> Os usos do solo de Galicia e das provincias son os do <b>MAPA, Anuario de Estatística 2025, táboa 3.3</b> (datos de 2024), '
        'a única fonte oficial que dá as mesmas categorías para Galicia e as catro provincias: superficie de cultivo, uso principal pastos, superficie agraria non utilizada, '
        'forestal (arborado, arbustivo e matogueira) e outras superficies (usos urbanos e artificiais, augas e humidais), que aquí se mostra como «artificial e auga». '
        'A comparación con España usa a táboa 3.2 do mesmo anuario. '
        f'O artificial por si só ({pc(art_ifn, 2)}%) e o arborado (máis do 67% do forestal) proceden do 4º Inventario Forestal Nacional e do IFCG 2024, segundo a memoria do PLADIGA 2026 (Xunta). '
        'As cortas de madeira de 2025 son da Xunta (A cadea forestal-madeira de Galicia 2025); os metros cúbicos por hectárea de monte son cálculo da FGS con esas cortas e a superficie forestal do MAPA. '
        'A cifra de terra abandonada (máis de 500.000 ha) é de AGADER. As fontes non miden igual: o IFN4 dá máis forestal (68,66%) e menos agrario (27,82%) ca o MAPA. '
        'As fronteiras das zonas son ondas decorativas: o exacto é a <b>área</b> de cada zona, non a súa forma nin a súa localización.'), literal=False)
    return h


# ---------- Gráficas ----------
def graficas(h):
    g = 'Galicia'
    P = ['A Coruña', 'Lugo', 'Ourense', 'Pontevedra']
    E = D['espana_agrario']
    nu_es = E['non_utilizada'] / (E['cultivo'] + E['pastos'] + E['non_utilizada']) * 100
    nu_gal = U[g]['non_utilizada'] / (U[g]['cultivo'] + U[g]['pastos'] + U[g]['non_utilizada']) * 100
    r1 = lambda v: round(v, 1)
    h = subst(h, r"\{label:'Forestal 73%'.*?\{label:'Auga 1,5%',data:\[1\.5\],backgroundColor:C\.agua\}\]\}", (
        f"{{label:'Forestal {pc(pct(g, 'forestal'))}%',data:[{r1(pct(g, 'forestal'))}],backgroundColor:C.verde}},"
        f"{{label:'Agrario {pc(pct(g, 'agrario'))}%',data:[{r1(pct(g, 'agrario'))}],backgroundColor:C.sen}},"
        f"{{label:'Artificial e auga {pc(pct(g, 'outras'))}%',data:[{r1(pct(g, 'outras'))}],backgroundColor:C.art}}]}}"), literal=False)
    h = subst(h, r"labels:\['Pastos e forraxes','Sen aproveitamento','Produción de alimentos'\],\s*datasets:\[\{data:\[11,8,3\],backgroundColor:\[C\.gan,C\.sen,C\.aviso\]\}\]\}",
              f"labels:['Pastos e prados','Terras de cultivo','Agraria non utilizada'], datasets:[{{data:[{r1(pct(g, 'pastos'))},{r1(pct(g, 'cultivo'))},{r1(pct(g, 'non_utilizada'))}],backgroundColor:[C.gan,C.ali,C.aviso]}}]}}", literal=False)
    h = subst(h, r"x:\{max:13,", "x:{max:16,", literal=False)
    h = subst(h, r"data:\[35\.7,7\.9\]", f"data:[{r1(nu_gal)},{r1(nu_es)}]", literal=False)
    h = subst(h, r"y:\{max:40,ticks", "y:{max:10,ticks", literal=False)
    h = subst(h, r"'% do agrario sen aproveitar'", "'% do agrario non utilizado'", literal=False)
    prov = ','.join(f"{{n:'{p}',x:{r1(pct(p, 'forestal'))},y:{r1(m3ha(p))}}}" for p in P)
    h = subst(h, r"const prov=\[.*?\];", f"const prov=[{prov}];", literal=False)
    h = subst(h, r"text:'% das cortas de Galicia'\},min:0,max:50", "text:'m³ cortados por ha de monte (2025)'},min:0,max:12", literal=False)
    h = subst(h, r"min:55,max:82", "min:50,max:80", literal=False)
    h = subst(h, r"c\.raw\.n\+': '\+c\.raw\.x\+'% forestal · '\+c\.raw\.y\+'% cortas'", "c.raw.n+': '+c.raw.x+'% forestal · '+c.raw.y+' m³/ha'", literal=False)
    orde6 = ['A Coruña', 'Lugo', 'Pontevedra', 'Ourense']
    h = subst(h, r"data:\[44\.1,37\.4,13\.4,5\.1\]", 'data:[' + ','.join(str(r1(cota_cortas(p))) for p in orde6) + ']', literal=False)
    serie = lambda k: ','.join(str(r1(pct(p, k))) for p in P)
    h = subst(h, r"\{label:'Forestal',data:\[64,72,78,62\].*?\{label:'Artificial',data:\[6,2,2,9\],backgroundColor:C\.art\}\]\}", (
        f"{{label:'Forestal',data:[{serie('forestal')}],backgroundColor:C.verde}},"
        f"{{label:'Agrario',data:[{serie('agrario')}],backgroundColor:C.sen}},"
        f"{{label:'Artificial e auga',data:[{serie('outras')}],backgroundColor:C.art}}]}}"), literal=False)
    # textos das tarxetas
    cl = cota_cortas('A Coruña') + cota_cortas('Lugo')
    T = [
        ('Distribución do territorio galego. Un só uso ocupa case tres cuartas partes; o construído é marxinal.',
         'Distribución do territorio galego. O monte ocupa seis de cada dez hectáreas.'),
        ('Inventario Forestal Nacional / Plan Forestal de Galicia · ESYRCE-MAPA 2025 · SIOSE. Auga separada do residuo metodolóxico.',
         'MAPA, Anuario de Estatística 2025, táboa 3.3 (datos de 2024).'),
        (f'Os tres compoñentes do 22% agrario, en % do territorio. O que de verdade alimenta é o máis pequeno.',
         f'Os tres compoñentes do {pc(pct(g, "agrario"))}% agrario, en % do territorio.'),
        ('ESYRCE (pastos e forraxes ~80% do agrario) · terra sen aproveitamento: Cocampo 2025 con datos MAPA.',
         'MAPA, Anuario de Estatística 2025, táboa 3.3 (datos de 2024).'),
        ('Porcentaxe do agrario sen aproveitamento. Galicia cuadriplica a media estatal.',
         'Superficie agraria non utilizada, en % do agrario. A estatística só ve unha parte do abandono: o resto xa conta como monte.'),
        ('Informe Cocampo 2025 a partir de datos do MAPA.', 'MAPA, Anuario de Estatística 2025, táboas 3.2 e 3.3 (datos de 2024).'),
        ('Cada provincia segundo a súa superficie forestal (eixo horizontal) e a súa cota de cortas de madeira (eixo vertical).',
         'Cada provincia segundo a súa superficie forestal (eixo horizontal) e a madeira cortada por hectárea de monte (eixo vertical).'),
        ('Forestal: estimación FGS sobre IFN. Cortas 2025: Anuario de Estatística Forestal.',
         'Forestal: MAPA, Anuario 2025 (datos de 2024). Cortas 2025: Xunta, A cadea forestal-madeira de Galicia 2025. Cálculo da FGS.'),
        ('Reparto das cortas de madeira de Galicia (2025). Dúas provincias concentran o 81,5%.',
         f'Reparto das cortas de madeira de Galicia (2025). Dúas provincias concentran o {pc(cl)}%.'),
        ('Anuario de Estatística Forestal · cota de cortas 2025.', 'Xunta, A cadea forestal-madeira de Galicia 2025 (volume total por provincia).'),
        ('Cada provincia ao 100%. As do interior, case todo verde; as da costa, máis agrario e construído.',
         'Cada provincia ao 100%. A costa ten o dobre de solo construído; Ourense, o máis monte e o menos agrario.'),
        ('Estimación propia FGS cruzando superficie total (INE), forestal (IFN) e cortas.', 'MAPA, Anuario de Estatística 2025, táboa 3.3 (datos de 2024).'),
    ]
    for a, b in T:
        h = subst(h, a, b)
    return h


def aplicar(h):
    for paso in (mapas, lendas, textos, graficas):
        h = paso(h)
    return h

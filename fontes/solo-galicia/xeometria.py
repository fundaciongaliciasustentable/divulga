"""
Reparte a silueta de cada mapa (Galicia e as catro provincias) en zonas de área exacta,
con fronteiras en onda (decorativas, como no deseño orixinal): o exacto é a área, non a forma.

Disposición, igual que no orixinal: o monte arriba; debaixo, unha franxa partida de esquerda a
dereita en pastos | cultivos (enriba) e agraria non utilizada (debaixo) | artificial e auga.
Precisa shapely (pip install shapely).
"""
import math
import re

from shapely.geometry import Polygon, MultiPolygon
from shapely.geometry.polygon import orient
from shapely.ops import polylabel


def anel(d):
    nums = [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?', d)]
    return Polygon(list(zip(nums[0::2], nums[1::2]))).buffer(0)


def _arriba(caixa, y0, amp, onda):
    x0, y_min, x1, y_max = caixa
    n = 240
    pts = [(x0 - 5 + (x1 - x0 + 10) * i / n, 0) for i in range(n + 1)]
    pts = [(x, y0 + amp * math.sin(2 * math.pi * (x - x0) / onda)) for x, _ in pts]
    return Polygon(pts + [(x1 + 5, y_min - amp - 5), (x0 - 5, y_min - amp - 5)])


def _esquerda(caixa, xc, amp, onda):
    x0, y_min, x1, y_max = caixa
    n = 240
    ys = [y_min - 5 + (y_max - y_min + 10) * i / n for i in range(n + 1)]
    pts = [(xc + amp * math.sin(2 * math.pi * (y - y_min) / onda + 1.3), y) for y in ys]
    return Polygon(pts + [(x0 - amp - 5, y_max + 5), (x0 - amp - 5, y_min - 5)])


def _cortar(forma, area_obxectivo, construir, lo, hi):
    """Busca por bisección a posición do corte que deixa area_obxectivo no lado construído."""
    for _ in range(60):
        m = (lo + hi) / 2
        if forma.intersection(construir(m)).area < area_obxectivo:
            lo = m
        else:
            hi = m
    parte = forma.intersection(construir((lo + hi) / 2))
    return parte, forma.difference(parte)


def repartir(silueta, cotas):
    """cotas: fraccións (suman 1) para forestal, pastos, cultivo, non_utilizada, outras."""
    caixa = silueta.bounds
    an, al = caixa[2] - caixa[0], caixa[3] - caixa[1]
    amp, onda = 0.012 * max(an, al), an / 2.4
    A = silueta.area
    forestal, abaixo = _cortar(silueta, cotas['forestal'] * A,
                               lambda y: _arriba(caixa, y, amp, onda), caixa[1] - amp - 2, caixa[3] + amp + 2)
    ondav = al / 2.2
    esq = lambda x: _esquerda(caixa, x, amp, ondav)
    pastos, resto = _cortar(abaixo, cotas['pastos'] * A, esq, caixa[0] - amp - 2, caixa[2] + amp + 2)
    medio, outras = _cortar(resto, (cotas['cultivo'] + cotas['non_utilizada']) * A, esq, caixa[0] - amp - 2, caixa[2] + amp + 2)
    cultivo, non_util = _cortar(medio, cotas['cultivo'] * A,
                                lambda y: _arriba(caixa, y, amp * .6, onda * .6), caixa[1] - amp - 2, caixa[3] + amp + 2)
    zonas = {'forestal': forestal, 'pastos': pastos, 'cultivo': cultivo, 'non_utilizada': non_util, 'outras': outras}
    for k, z in zonas.items():   # comprobación: cada zona ten a área que lle toca (±0,1 % do total)
        assert abs(z.area / A - cotas[k]) < 0.001, (k, z.area / A, cotas[k])
    return zonas


def ruta(xeo):
    """Xeometría shapely → atributo d dun <path> (aneis exteriores en sentido antihorario, ocos ao revés)."""
    pols = [xeo] if isinstance(xeo, Polygon) else [g for g in getattr(xeo, 'geoms', []) if isinstance(g, Polygon)]
    partes = []
    for p in pols:
        if p.area < 1:
            continue
        p = orient(p, 1.0)
        for r in [p.exterior] + list(p.interiors):
            c = list(r.coords)[:-1]
            partes.append('M' + ' L'.join(f'{x:.2f},{y:.2f}' for x, y in c) + ' Z')
    return ' '.join(partes)


def centro(xeo):
    """Punto interior máis afastado do bordo (para os rótulos), na parte maior da zona."""
    pols = [xeo] if isinstance(xeo, Polygon) else list(xeo.geoms)
    p = max(pols, key=lambda g: g.area)
    c = polylabel(p, tolerance=1.0)
    return c.x, c.y

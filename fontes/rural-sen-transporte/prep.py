#!/usr/bin/env python3
"""Prepara as capas e as cifras de «Ata onde chega o bus» (v/rural-sen-transporte/).

Entradas (foto do día, nunca chamadas en vivo desde a peza):
  - Mapas Galicia Sustentable, copia local en ~/Proxectos/mapasgs/site/public/data/:
      pulso-tren, estacions-tren, buses-xunta, distancia-servizos, concellos-parroquias
  - pulso-bus: en local non hai data.geojson; descárgase da web pública a data/raw/
      https://mapas.galiciasustentable.org/data/pulso-bus/data.geojson (e meta.json)
  - Poboación por concello: INE, Padrón a 1/1/2025, tal como a garda
      fontes/poboacion-galicia/data/datos.json (táboas 2868, 2880, 2885, 2890)
  - Alturas: MDT 25 m do IGN en fontes/terreo/data/raw/*.tif

Saídas: v/rural-sen-transporte/capas/*.geojson e fontes/rural-sen-transporte/cifras.json

Uso (precisa shapely, numpy e tifffile):
  python3 fontes/rural-sen-transporte/prep.py
"""
import json
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import tifffile
from shapely import STRtree
from shapely.geometry import MultiLineString, MultiPolygon, Point, mapping, shape
from shapely.ops import linemerge

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
RAW = AQUI / "data" / "raw"
CAPAS = RAIZ / "v" / "rural-sen-transporte" / "capas"
MAPAS = Path.home() / "Proxectos" / "mapasgs" / "site" / "public" / "data"
WEB = "https://mapas.galiciasustentable.org/data/"
LAB, DOM = "2026-11-04", "2026-11-08"   # mércores laborable e domingo de referencia

RAW.mkdir(parents=True, exist_ok=True)
CAPAS.mkdir(parents=True, exist_ok=True)


def le(nome):
    return json.load(open(MAPAS / nome / "data.geojson", encoding="utf-8"))["features"]


def pulso_bus():
    f = RAW / "pulso-bus.geojson"
    if not f.exists():
        urllib.request.urlretrieve(WEB + "pulso-bus/data.geojson", f)
        urllib.request.urlretrieve(WEB + "pulso-bus/meta.json", RAW / "pulso-bus.meta.json")
    return json.load(open(f, encoding="utf-8"))["features"]


def gardar(nome, feats, dec=4):
    def r(c):
        if isinstance(c[0], (int, float)):
            return [round(c[0], dec), round(c[1], dec)]
        return [r(x) for x in c]
    for f in feats:
        f["geometry"]["coordinates"] = r(f["geometry"]["coordinates"])
    p = CAPAS / f"{nome}.geojson"
    p.write_text(json.dumps({"type": "FeatureCollection", "features": feats},
                            ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    kb = p.stat().st_size / 1024
    print(f"{p.name}: {len(feats)} elementos, {kb:.0f} KB")
    assert kb < 200, p


# ---------------------------------------------------------------- concellos
conc = [f for f in le("concellos-parroquias") if f["properties"]["nivel"] == "concello"]
xeo = [shape(f["geometry"]) for f in conc]
cod = [f["properties"]["codigo_ine"] for f in conc]
nome = {f["properties"]["codigo_ine"]: f["properties"]["nome"] for f in conc}
arbore = STRtree(xeo)
_cache = {}


def concello(lon, lat):
    k = (round(lon, 5), round(lat, 5))
    if k not in _cache:
        p = Point(lon, lat)
        _cache[k] = next((cod[i] for i in arbore.query(p) if xeo[i].contains(p)), None)
    return _cache[k]


pob = {c["id"]: c["v"] for c in json.load(open(
    RAIZ / "fontes" / "poboacion-galicia" / "data" / "datos.json", encoding="utf-8"))["concellos"]}
assert len(pob) == 313

# ---------------------------------------------------------------- viaxes
bus = pulso_bus()
tren = le("pulso-tren")
paradas = le("buses-xunta")


def tramos(viaxes, dia):
    """Tramos entre paradas consecutivas e cantas viaxes distintas os percorren ese día.
    Dúas viaxes coa mesma hora nas dúas paradas (trens acoplados que o GTFS publica como
    dous produtos, p. ex. Alvia + MD) contan unha vez."""
    vistos = defaultdict(set)
    for f in viaxes:
        if f["properties"]["data"] != dia:
            continue
        cs, t = f["geometry"]["coordinates"], f["properties"]["t"]
        for i in range(len(cs) - 1):
            a, b = tuple(round(x, 4) for x in cs[i]), tuple(round(x, 4) for x in cs[i + 1])
            if a == b:
                continue
            k = (a, b) if a < b else (b, a)
            vistos[k].add((t[i], t[i + 1]) if a < b else (t[i + 1], t[i]))
    return {k: len(v) for k, v in vistos.items()}


def por_concello(viaxes, dia):
    n = Counter()
    for f in viaxes:
        if f["properties"]["data"] == dia:
            for c in {concello(*p) for p in f["geometry"]["coordinates"]} - {None}:
                n[c] += 1
    return n


bus_lab, bus_dom = por_concello(bus, LAB), por_concello(bus, DOM)
tren_lab = por_concello(tren, LAB)
n_paradas = Counter(concello(*p["geometry"]["coordinates"]) for p in paradas)

cifras = {
    "dia_laborable": LAB, "dia_domingo": DOM,
    "viaxes_bus_laborable": sum(f["properties"]["data"] == LAB for f in bus),
    "viaxes_bus_domingo": sum(f["properties"]["data"] == DOM for f in bus),
    "viaxes_tren_laborable": sum(f["properties"]["data"] == LAB for f in tren),
    "viaxes_tren_domingo": sum(f["properties"]["data"] == DOM for f in tren),
    "paradas_bus": len(paradas),
    "poboacion_galicia_2025": sum(pob.values()),
}
cifras["concellos_sen_bus_domingo"] = sorted(nome[c] for c in cod if bus_dom[c] == 0)
cifras["n_concellos_sen_bus_domingo"] = len(cifras["concellos_sen_bus_domingo"])
cifras["concellos_sen_bus_laborable"] = sorted(nome[c] for c in cod if bus_lab[c] == 0)
cifras["pob_concellos_sen_bus_domingo"] = sum(pob[c] for c in cod if bus_dom[c] == 0)
cifras["concellos_sen_tren"] = sum(1 for c in cod if tren_lab[c] == 0)
cifras["pob_concellos_con_tren"] = sum(pob[c] for c in cod if tren_lab[c] > 0)

# ---------------------------------------------------------------- tren: corredores
est = le("estacions-tren")
pos = {f["properties"]["nome"]: f["geometry"]["coordinates"] for f in est}


def preto(c, p):
    return abs(c[0] - p[0]) < 0.003 and abs(c[1] - p[1]) < 0.003


def corredor(a, b, dia=LAB):
    """Trens distintos que paran en a e en b ese día (mesma hora nas dúas = un tren)."""
    s = set()
    for f in tren:
        if f["properties"]["data"] != dia:
            continue
        cs, t = f["geometry"]["coordinates"], f["properties"]["t"]
        ia = [i for i, c in enumerate(cs) if preto(c, pos[a])]
        ib = [i for i, c in enumerate(cs) if preto(c, pos[b])]
        if ia and ib:
            s.add((t[ia[0]], t[ib[0]]))
    return len(s)


SCQ = "Santiago de Compostela-Daniel Castelao"
cifras["corredores_laborable"] = {
    "A Coruña–Santiago": corredor("A Coruña", SCQ),
    "Santiago–Vigo Urzaiz": corredor(SCQ, "Vigo Urzaiz"),
    "Santiago–Pontevedra": corredor(SCQ, "Pontevedra"),
    "Santiago–Ourense": corredor(SCQ, "Ourense"),
    "Lugo–Monforte": corredor("Lugo", "Monforte de Lemos"),
    "Monforte–Ourense": corredor("Monforte de Lemos", "Ourense"),
    "Lugo–Ourense": corredor("Lugo", "Ourense"),
    "A Coruña–Lugo": corredor("A Coruña", "Lugo"),
}
cifras["corredores_domingo"] = {
    "A Coruña–Santiago": corredor("A Coruña", SCQ, DOM),
    "Lugo–Monforte": corredor("Lugo", "Monforte de Lemos", DOM),
}
cifras["estacions_servizos_dia"] = {n: next(f["properties"]["servizos_dia"] for f in est if f["properties"]["nome"] == n)
                                    for n in ("A Coruña", SCQ, "Vigo Urzaiz", "Pontevedra", "Ourense", "Lugo",
                                              "Monforte de Lemos", "Sarria")}

# ---------------------------------------------------------------- comarcas e concellos citados
# Comarcas oficiais (Decreto 65/1997), comprobadas contra a táboa IGE 2246
# («Relación de provincias, concellos e comarcas galegas») o 2026-11-05.
# CORRIXIDO ese día: A Fonsagrada tiña A Ribeira de Piquín, que é da comarca
# de Meira, e faltáballe Baleira. As cifras de cifras.json e o texto da peza
# son anteriores á corrección e NON se rexeneraron. Reexecutar este guión
# cambia, na comarca da Fonsagrada: poboación de 3.858 a 4.402 (fonte da
# propia peza, INE padrón 2025), superficie de 582,7 a 678,2 km²
# (perfil-concellos) e tamén viaxes de bus, paradas e tren, que dependen das
# capas de mapas. A frase do paso da Fonsagrada en peza.tpl.html leva as
# cifras escritas a man e hai que actualizala no mesmo paso.
COMARCAS = {
    "A Fonsagrada": ["A Fonsagrada", "Baleira", "Negueira de Muñiz"],
    "Os Ancares": ["Baralla", "Becerreá", "Cervantes", "Navia de Suarna", "As Nogais", "Pedrafita do Cebreiro"],
    "Quiroga": ["Folgoso do Courel", "Quiroga", "Ribas de Sil"],
}
por_nome = {v: k for k, v in nome.items()}
sup = {f["properties"]["codigo_ine"]: f["properties"]["superficie_km2"] for f in le("perfil-concellos")}
comarcas = {}
for com, ns in COMARCAS.items():
    cs = [por_nome[n] for n in ns]
    trips = sum(1 for f in bus if f["properties"]["data"] == LAB
                and {concello(*p) for p in f["geometry"]["coordinates"]} & set(cs))
    trips_d = sum(1 for f in bus if f["properties"]["data"] == DOM
                  and {concello(*p) for p in f["geometry"]["coordinates"]} & set(cs))
    comarcas[com] = {
        "poboacion": sum(pob[c] for c in cs), "viaxes_bus_laborable": trips, "viaxes_bus_domingo": trips_d,
        "paradas": sum(n_paradas[c] for c in cs), "tren": sum(tren_lab[c] for c in cs),
        "superficie_km2": round(sum(sup[c] for c in cs), 1),
        "concellos": {nome[c]: {"poboacion": pob[c], "bus_laborable": bus_lab[c], "bus_domingo": bus_dom[c],
                                "paradas": n_paradas[c]} for c in cs},
    }
cifras["comarcas"] = comarcas
CITADOS = ["Santiago de Compostela", "A Coruña", "Vigo", "Lugo", "Monforte de Lemos", "Ourense", "Ames",
           "Folgoso do Courel", "Negueira de Muñiz", "Navia de Suarna", "Cervantes", "A Fonsagrada", "Ramirás"]
cifras["concellos"] = {n: {"poboacion": pob[por_nome[n]], "bus_laborable": bus_lab[por_nome[n]],
                           "bus_domingo": bus_dom[por_nome[n]], "tren_laborable": tren_lab[por_nome[n]],
                           "paradas": n_paradas[por_nome[n]],
                           "paradas_1000hab": round(n_paradas[por_nome[n]] / pob[por_nome[n]] * 1000, 1),
                           "bus_1000hab": round(bus_lab[por_nome[n]] / pob[por_nome[n]] * 1000, 1)}
                       for n in CITADOS}

# paradas por habitante e viaxes por parada, rural (<2.000 hab.) fronte a urbano (>50.000)
peq = [c for c in cod if pob[c] < 2000]
gra = [c for c in cod if pob[c] > 50000]
for k, g in (("concellos_menos_2000", peq), ("concellos_mais_50000", gra)):
    P = sum(pob[c] for c in g)
    cifras[k] = {"n": len(g), "poboacion": P, "paradas": sum(n_paradas[c] for c in g),
                 "paradas_1000hab": round(sum(n_paradas[c] for c in g) / P * 1000, 1)}

# horario dos buses en Navia de Suarna e Negueira/A Fonsagrada o mércores
def horario(n):
    c = por_nome[n]
    out = []
    for f in bus:
        if f["properties"]["data"] != LAB:
            continue
        cs, t = f["geometry"]["coordinates"], f["properties"]["t"]
        idx = [i for i, p in enumerate(cs) if concello(*p) == c]
        if idx:
            h = t[idx[0]]
            out.append((f"{h // 3600:02d}:{h % 3600 // 60:02d}", f["properties"]["lina"]))
    return sorted(out)


cifras["horario_laborable"] = {n: horario(n) for n in ("Navia de Suarna", "A Ribeira de Piquín", "Cervantes")}
cifras["liñas_paradas_courel"] = sorted({p["properties"]["linas_nomes"] for p in paradas
                                         if concello(*p["geometry"]["coordinates"]) == por_nome["Folgoso do Courel"]})

# ---------------------------------------------------------------- distancias
ds = le("distancia-servizos")
dh = [f["properties"]["dist_hospital"] for f in ds if f["properties"]["dist_hospital"] is not None]
cifras["lugares"] = len(ds)
cifras["lugares_hospital_mediana_km"] = float(np.median(dh))
cifras["lugares_hospital_mais_30km"] = sum(x > 30 for x in dh)
cifras["lugares_hospital_mais_40km"] = sum(x > 40 for x in dh)
lonxe = sorted(ds, key=lambda f: -(f["properties"]["dist_hospital"] or 0))[:12]
cifras["lugares_mais_lonxe_hospital"] = [
    {"nome": f["properties"]["nome"], "concello": nome[f["properties"]["codigo_ine"]],
     "poboacion_2024": f["properties"]["poboacion"], "dist_hospital_km": f["properties"]["dist_hospital"],
     "dist_centro_saude_km": f["properties"]["dist_centro_saude"], "lonlat": f["geometry"]["coordinates"]}
    for f in lonxe]
for n in ("Folgoso do Courel", "Navia de Suarna", "Negueira de Muñiz"):
    L = [f["properties"] for f in ds if f["properties"]["codigo_ine"] == por_nome[n]]
    h = [p["dist_hospital"] for p in L]
    cifras.setdefault("distancias_concello", {})[n] = {
        "lugares": len(L), "hospital_mediana_km": float(np.median(h)), "hospital_max_km": max(h),
        "centro_saude_max_km": max(p["dist_centro_saude"] for p in L),
        "instituto_mediana_km": float(np.median([p["dist_instituto"] for p in L if p["dist_instituto"] is not None])),
    }


# ---------------------------------------------------------------- alturas (MDT 25 m)
def altura(lon, lat):
    for f in (RAIZ / "fontes" / "terreo" / "data" / "raw").glob("mdt25_*.tif"):
        with tifffile.TiffFile(f) as t:
            p = t.pages[0]
            sx, sy, _ = p.tags["ModelPixelScaleTag"].value
            _, _, _, x0, y0, _ = p.tags["ModelTiepointTag"].value
            w, h = p.imagewidth, p.imagelength
            c, r = int((lon - x0) / sx), int((y0 - lat) / sy)
            if 0 <= c < w and 0 <= r < h:
                return int(p.asarray()[r, c])
    return None


cifras["alturas_m"] = {
    "Escanlar (Negueira de Muñiz)": altura(-6.83221, 43.14888),
    "Peliceira (Navia de Suarna)": altura(-6.8352, 42.94202),
    "Teixeira (Folgoso do Courel)": altura(-7.16725, 42.69642),
    "A Fonsagrada (vila)": altura(-7.0675, 43.1235),
    "Murias de Rao (Navia de Suarna)": altura(-6.87171, 42.92511),
    "Entralgo (Negueira de Muñiz)": altura(-6.86486, 43.16322),
    "A Pobra de Navia (parada do bus)": altura(-7.0056, 42.9636),
    "Seoane do Courel": altura(-7.0985, 42.6612),
}

# parada de bus máis próxima (en liña recta) a algúns lugares de montaña e as súas viaxes do mércores
def km(a, b):
    dx = (a[0] - b[0]) * 111.32 * np.cos(np.radians((a[1] + b[1]) / 2))
    return float(np.hypot(dx, (a[1] - b[1]) * 110.95))


viaxes_parada = Counter()
for f in bus:
    if f["properties"]["data"] == LAB:
        for p in {tuple(round(x, 4) for x in q) for q in f["geometry"]["coordinates"]}:
            viaxes_parada[p] += 1
LUG = {"Murias de Rao": (-6.87171, 42.92511), "Escanlar": (-6.83221, 43.14888),
       "Entralgo": (-6.86486, 43.16322), "Teixeira": (-7.16725, 42.69642)}
cifras["parada_mais_proxima"] = {}
for n, ll in LUG.items():
    p = min(paradas, key=lambda q: km(ll, q["geometry"]["coordinates"]))
    pc = p["geometry"]["coordinates"]
    cifras["parada_mais_proxima"][n] = {"parada": p["properties"]["nome"], "km_linea_recta": round(km(ll, pc), 1),
                                        "viaxes_mercores": viaxes_parada[tuple(round(x, 4) for x in pc)],
                                        "concello": nome.get(concello(*pc))}
cifras["km_murias_rao_pobra_navia"] = round(km(LUG["Murias de Rao"], (-7.0056, 42.9636)), 1)

(AQUI / "cifras.json").write_text(json.dumps(cifras, ensure_ascii=False, indent=1), encoding="utf-8")

# ---------------------------------------------------------------- capas
def capa_tramos(nome_capa, viaxes, dia, minimo=1, dec=4):
    t = tramos(viaxes, dia)
    feats = [{"type": "Feature", "properties": {"n": n},
              "geometry": {"type": "LineString", "coordinates": [list(a), list(b)]}}
             for (a, b), n in sorted(t.items(), key=lambda x: x[1]) if n >= minimo]
    gardar(nome_capa, feats, dec)


CLASES = [1, 4, 11, 31, 101]   # viaxes ao día por tramo: 1–3, 4–10, 11–30, 31–100, >100


def capa_bus(nome_capa, dia, g=0.025):
    """Rede de bus xeneralizada para que pese < 200 KB: as paradas axústanse a unha grella de
    g graos (~2–3 km), cóntanse as viaxes distintas que unen cada par de celas veciñas e os
    tramos fúndense en liñas por clase de frecuencia."""
    E = defaultdict(set)
    for i, f in enumerate(bus):
        if f["properties"]["data"] != dia:
            continue
        cs = [(round(c[0] / g), round(c[1] / g)) for c in f["geometry"]["coordinates"]]
        for a, b in zip(cs, cs[1:]):
            if a != b:
                E[(min(a, b), max(a, b))].add(i)
    feats = []
    for k, lo in enumerate(CLASES):
        hi = CLASES[k + 1] if k + 1 < len(CLASES) else 10 ** 9
        segs = [[(a[0] * g, a[1] * g), (b[0] * g, b[1] * g)] for (a, b), v in E.items() if lo <= len(v) < hi]
        if segs:
            feats.append({"type": "Feature", "properties": {"c": k},
                          "geometry": mapping(linemerge(MultiLineString(segs)))})
    gardar(nome_capa, feats, 3)


capa_tramos("tren", tren, LAB)
capa_bus("bus", LAB)
capa_bus("bus-domingo", DOM)

gardar("estacions", [{"type": "Feature", "properties": {"s": f["properties"]["servizos_dia"]},
                      "geometry": f["geometry"]} for f in est
                     if -9.5 < f["geometry"]["coordinates"][0] < -6.7 and 41.8 < f["geometry"]["coordinates"][1] < 43.8])

# concellos: viaxes de bus por día (mércores e domingo) e paradas por 1.000 hab.
cf = []
for f, g in zip(conc, xeo):
    c = f["properties"]["codigo_ine"]
    if g.geom_type == "MultiPolygon":   # sen illotes de menos de ~0,2 km²
        g = MultiPolygon([q for q in g.geoms if q.area > 2e-5]) if any(q.area > 2e-5 for q in g.geoms) else g
    s = g.simplify(0.008, preserve_topology=True)
    cf.append({"type": "Feature", "properties": {"b": bus_lab[c], "d": bus_dom[c],
                                                 "p": round(n_paradas[c] / pob[c] * 1000, 1)},
               "geometry": mapping(s)})
gardar("concellos", cf, 3)

# lugares a máis de 30 km en liña recta do hospital máis próximo
lx = []
for k, (lo, hi) in enumerate(((30, 40), (40, 50), (50, 999))):   # MultiPoint por clase: pesa moito menos
    pts = [f["geometry"]["coordinates"] for f in ds if lo < (f["properties"]["dist_hospital"] or 0) <= hi]
    lx.append({"type": "Feature", "properties": {"c": k, "n": len(pts)},
               "geometry": {"type": "MultiPoint", "coordinates": pts}})
gardar("lonxe", lx, 3)

# paradas de bus da montaña oriental de Lugo (A Fonsagrada, Os Ancares, Quiroga), coas viaxes do mércores
zona = {por_nome[n] for ns in COMARCAS.values() for n in ns}
gardar("paradas-montana", [{"type": "Feature", "properties": {
    "v": viaxes_parada[tuple(round(x, 4) for x in p["geometry"]["coordinates"])]},
    "geometry": p["geometry"]} for p in paradas if concello(*p["geometry"]["coordinates"]) in zona])

print(json.dumps({k: v for k, v in cifras.items() if k not in ("comarcas", "concellos", "lugares_mais_lonxe_hospital",
                                                              "concellos_sen_bus_domingo", "liñas_paradas_courel")},
                 ensure_ascii=False, indent=1))

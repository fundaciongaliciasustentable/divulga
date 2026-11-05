#!/usr/bin/env python3
"""Prepara os datos de «As aldeas que quedaron sen ninguén» (v/aldeas-que-quedaron/).

1. Volve contar as entidades singulares de Galicia desde os ficheiros do INE
   (Nomenclátor 2000 e 2025) para verificar as cifras da capa aldeas-baleiras.
2. Le as capas de Mapas Galicia Sustentable (copia local en mapasgs, foto do día):
   aldeas-baleiras, distancia-servizos, poboacion-seculo e concellos-parroquias.
3. Descarga do IGE os nacementos (táboa 57) e as defuncións (táboa 30) por concello.
4. Mide a altitude de cada aldea destacada no MDT de 25 m do IGN (fontes/terreo).
5. Escribe as capas da peza en v/aldeas-que-quedaron/capas/, a miniatura thumb.svg
   e as cifras calculadas en cifras.json.

Uso (precisa numpy e tifffile):
    python3 prep.py
Os ficheiros en bruto quedan en data/raw/ (non van ao git).
"""
import csv
import glob
import io
import json
import math
import re
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
import tifffile

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
RAW = AQUI / "data" / "raw"
SAIDA = RAIZ / "v" / "aldeas-que-quedaron"
CAPAS = SAIDA / "capas"
MAPAS = Path.home() / "Proxectos" / "mapasgs" / "site" / "public" / "data"
MDT = RAIZ / "fontes" / "terreo" / "data" / "raw"
INE = "https://www.ine.es/nomen_files/nacional/es/Nacional_{ano}.zip"
IGE = "https://www.ige.gal/igebdt/igeapi/csv/datos/{taboa}"
PROV = {"15": "A Coruña", "27": "Lugo", "32": "Ourense", "36": "Pontevedra"}

# Aldeas destacadas en cada parada (código INE de 11 cifras)
ALDEAS = {
    "15061110700": "Os Campos",        # Ortigueira
    "27033052700": "Debodas",          # Muras
    "27018250800": "Trasouturo",       # A Fonsagrada
    "27034140900": "Peliceira",        # Navia de Suarna (Ancares)
    "27012080500": "O Mazo",           # Cervantes (Ancares)
    "27017060200": "Lousadela",        # Folgoso do Courel
    "32044060200": "Tonxil",           # Manzaneda
    "32024120100": "Ademourán",        # Celanova
}
# Concellos das paradas (código INE): contorno e cifras
CONCELLOS = ["15061", "27033", "27038", "27063", "27018", "27034", "27012", "27017",
             "32044", "32063", "32024", "36051"]


def baixar(url, dest):
    if not dest.exists():
        print("descargando", url)
        with urllib.request.urlopen(url, timeout=300) as r:
            dest.write_bytes(r.read())
    return dest


def nomenclator(ano):
    """Entidades singulares de Galicia: código → (nome, poboación)."""
    z = zipfile.ZipFile(baixar(INE.format(ano=ano), RAW / f"Nacional_{ano}.zip"))
    nome = next(n for n in z.namelist() if not n.endswith("xlsx") and ("_sex" in n or n == f"Nomdef{ano}"))
    b = z.read(nome)
    try:
        t = b.decode("utf-8")
    except UnicodeDecodeError:
        t = b.decode("latin-1")
    out = {}
    for liña in t.splitlines():
        m = re.match(r"^(\d{11})(.*?)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s*$", liña)
        if not m or m.group(1)[:2] not in PROV:
            continue
        c = m.group(1)
        if c.endswith("00") and not c.endswith("0000"):   # singular, non colectiva
            out[c] = (m.group(2).strip(), int(m.group(3)))
    return out


def ige(taboa):
    """Táboa do IGE por concello e ano (Total): {(codigo, ano): valor}."""
    f = baixar(IGE.format(taboa=taboa), RAW / f"ige{taboa}.csv")
    out = {}
    for fila in csv.DictReader(io.StringIO(f.read_bytes().decode("latin-1"))):
        if fila["Sexo"] == "Total" and len(fila["CodEspazo"]) == 5 and fila["DatoN"]:
            out[(fila["CodEspazo"], int(fila["CodTempo"]))] = int(float(fila["DatoN"]))
    return out


class Relevo:
    """Altitude (m) no MDT de 25 m do IGN, GeoTIFF en EPSG:4258."""

    def __init__(self):
        self.anacos = []
        for f in sorted(glob.glob(str(MDT / "mdt25_*.tif"))):
            with tifffile.TiffFile(f) as t:
                p = t.pages[0]
                sx, sy, _ = p.tags["ModelPixelScaleTag"].value
                _, _, _, x0, y0, _ = p.tags["ModelTiepointTag"].value
                self.anacos.append([x0, y0, sx, sy, f, None, p.shape])

    def __call__(self, lon, lat):
        for a in self.anacos:
            x0, y0, sx, sy, f, arr, forma = a
            c, r = int((lon - x0) / sx), int((y0 - lat) / sy)
            if 0 <= r < forma[0] and 0 <= c < forma[1]:
                if arr is None:
                    arr = a[5] = tifffile.imread(f)
                return int(arr[r, c])
        return None


def dp(pts, tol):
    """Douglas-Peucker sobre unha lista de [lon, lat]."""
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    n = math.hypot(dx, dy) or 1e-12
    dmax, imax = 0, 0
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / n if (dx or dy) else math.hypot(x - x1, y - y1)
        if d > dmax:
            dmax, imax = d, i
    if dmax > tol:
        return dp(pts[: imax + 1], tol)[:-1] + dp(pts[imax:], tol)
    return [pts[0], pts[-1]]


def r4(c):
    return [round(c[0], 4), round(c[1], 4)]


def gardar(nome, obx):
    t = json.dumps(obx, ensure_ascii=False, separators=(",", ":"))
    (CAPAS / nome).write_text(t, encoding="utf-8")
    print(f"capas/{nome}: {len(t) // 1024} KB")


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    CAPAS.mkdir(parents=True, exist_ok=True)
    cifras = {}

    # 1. INE en bruto: verificación
    a, b = nomenclator(2000), nomenclator(2025)
    cifras["ine"] = {
        "entidades_2000": len(a), "a_cero_2000": sum(1 for v in a.values() if v[1] == 0),
        "entidades_2025": len(b), "a_cero_2025": sum(1 for v in b.values() if v[1] == 0),
        "con_xente_2000_a_cero_2025_mesmo_codigo": sum(
            1 for c, v in b.items() if v[1] == 0 and c in a and a[c][1] > 0),
        "de_1_a_5_hab_2025": sum(1 for v in b.values() if 1 <= v[1] <= 5),
        "provincias_2025": {
            PROV[p]: {
                "entidades": sum(1 for c in b if c[:2] == p),
                "a_cero": sum(1 for c, v in b.items() if c[:2] == p and v[1] == 0),
                "de_1_a_5": sum(1 for c, v in b.items() if c[:2] == p and 1 <= v[1] <= 5),
                "mediana_hab": float(np.median([v[1] for c, v in b.items() if c[:2] == p])),
            } for p in PROV},
        "aldeas": {c: {"2000": a.get(c), "2025": b.get(c)} for c in ALDEAS},
    }

    # 2. Capas de Mapas Galicia Sustentable
    F = json.loads((MAPAS / "aldeas-baleiras" / "data.geojson").read_text())["features"]
    dist = {f["properties"]["codigo"]: f["properties"]
            for f in json.loads((MAPAS / "distancia-servizos" / "data.geojson").read_text())["features"]}
    seculo = {f["properties"]["codigo_ine"]: f["properties"]
              for f in json.loads((MAPAS / "poboacion-seculo" / "data.geojson").read_text())["features"]}
    lim = [f for f in json.loads((MAPAS / "concellos-parroquias" / "data.geojson").read_text())["features"]
           if f["properties"]["nivel"] == "concello"]

    P = [f["properties"] for f in F]
    baleirada = lambda p: p["pob"] == 0 and (p["pob_2000"] or 0) > 0   # noqa: E731
    cifras["capa"] = {
        "entidades": len(P),
        "a_cero_2025": sum(1 for p in P if p["pob"] == 0),
        "baleiradas_desde_2000": sum(1 for p in P if baleirada(p)),
        "baleiradas_con_posicion": sum(1 for f in F if baleirada(f["properties"]) and f["geometry"]),
        "a_cero_con_posicion": sum(1 for f in F if f["properties"]["pob"] == 0 and f["geometry"]),
        "baleiradas_por_provincia": {PROV[k]: v for k, v in
                                     Counter(p["codigo"][:2] for p in P if baleirada(p)).items()},
        "concellos_mais_baleiradas": [
            [seculo[k]["nome"], v] for k, v in
            Counter(p["codigo"][:5] for p in P if baleirada(p)).most_common(10)],
    }

    # 3. IGE: nacementos (57) e defuncións (30)
    nac, mor = ige(57), ige(30)
    rel = Relevo()

    conc = {}
    for k in CONCELLOS:
        ents = [p for p in P if p["codigo"][:5] == k]
        s = seculo[k]
        conc[k] = {
            "nome": s["nome"],
            "entidades_2025": len(ents),
            "a_cero_2025": sum(1 for p in ents if p["pob"] == 0),
            "baleiradas_desde_2000": sum(1 for p in ents if baleirada(p)),
            "de_1_a_5_hab_2025": sum(1 for p in ents if 1 <= p["pob"] <= 5),
            "hab_nomenclator_2000": sum((p["pob_2000"] or 0) for p in ents),
            "hab_nomenclator_2025": sum(p["pob"] for p in ents),
            "censo": dict(zip(map(str, s["censos"]), s["poboacion"])),
            "nacementos_2015_2024": sum(nac.get((k, y), 0) for y in range(2015, 2025)),
            "defuncions_2015_2024": sum(mor.get((k, y), 0) for y in range(2015, 2025)),
        }
    cifras["concellos"] = conc

    al = {}
    for f in F:
        c = f["properties"]["codigo"]
        if c in ALDEAS:
            p, (lon, lat) = f["properties"], f["geometry"]["coordinates"]
            d = dist.get(c, {})
            al[c] = {"nome": p["nome"], "parroquia_ine": p["parroquia_ine"],
                     "concello": seculo[c[:5]]["nome"], "lon": round(lon, 4), "lat": round(lat, 4),
                     "hab_2000": p["pob_2000"], "hab_2025": p["pob"],
                     "baleira_desde": p["baleira_desde"], "rexurdiu": p["rexurdiu"],
                     "altitude_m": rel(lon, lat),
                     "km_centro_saude": d.get("dist_centro_saude"),
                     "centro_saude": d.get("centro_saude_nome")}
    cifras["aldeas"] = al

    # 4. Capas da peza
    def multipunto(cond):
        return {"type": "MultiPoint",
                "coordinates": [r4(f["geometry"]["coordinates"]) for f in F
                                if f["geometry"] and cond(f["properties"])]}
    gardar("baleiras.geojson", {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"t": "despois"}, "geometry": multipunto(baleirada)},
        {"type": "Feature", "properties": {"t": "antes"},
         "geometry": multipunto(lambda p: p["pob"] == 0 and p["baleira_antes_2000"])},
    ]})
    gardar("quedan.geojson", {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {}, "geometry": multipunto(lambda p: 1 <= p["pob"] <= 5)}]})
    gardar("aldeas.geojson", {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"nome": v["nome"]},
         "geometry": {"type": "Point", "coordinates": [v["lon"], v["lat"]]}} for v in al.values()]})

    liñas = []
    for f in lim:
        if f["properties"]["codigo_ine"] not in CONCELLOS:
            continue
        g = f["geometry"]
        polis = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for pol in polis:
            aneis = [dp(pol[0], 0.0006)]
            liñas.append([r4(c) for c in aneis[0]])
    gardar("concellos.geojson", {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {}, "geometry": {"type": "MultiLineString", "coordinates": liñas}}]})

    # 5. Miniatura: contorno de Galicia e as entidades baleiras
    contorno = json.loads((RAIZ / "assets" / "terreo" / "galicia-contorno.geojson").read_text())
    O, L, S, N = -9.35, -6.7, 41.8, 43.82
    k = 520 / max((L - O) * math.cos(math.radians(42.8)), N - S)
    def xy(lon, lat):
        return (40 + (lon - O) * math.cos(math.radians(42.8)) * k, 560 - (lat - S) * k - 10)
    trazos = []
    for g in [ft["geometry"] for ft in contorno["features"]]:
        aneis = []
        if g["type"] in ("Polygon", "MultiPolygon"):
            for pol in ([g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]):
                aneis.append(pol[0])
        elif g["type"] in ("LineString", "MultiLineString"):
            aneis = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
        for an in aneis:
            an = dp(an, 0.005)
            if len(an) > 2:
                trazos.append("M" + "L".join(f"{x:.0f},{y:.0f}" for x, y in map(lambda c: xy(*c), an)))
    puntos = lambda cond: "".join(  # noqa: E731
        f"M{x:.0f} {y:.0f}h0"
        for x, y in sorted({tuple(round(v / 3) * 3 for v in xy(*f["geometry"]["coordinates"]))
                            for f in F if f["geometry"] and cond(f["properties"])}))
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
           '<rect width="600" height="600" fill="#0e1012"/>'
           f'<path d="{"".join(trazos)}" fill="#1b211d" stroke="#f2f0e8" stroke-opacity=".35" stroke-width="1.2"/>'
           f'<g fill="none" stroke-width="6" stroke-linecap="round">'
           f'<path stroke="#5d6a73" d="{puntos(lambda p: p["pob"] == 0 and p["baleira_antes_2000"])}"/>'
           f'<path stroke="#f0a03c" d="{puntos(baleirada)}"/></g></svg>')
    (SAIDA / "thumb.svg").write_text(svg, encoding="utf-8")
    print(f"thumb.svg: {len(svg) // 1024} KB")

    (AQUI / "cifras.json").write_text(json.dumps(cifras, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: cifras[k] for k in ("ine", "capa")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

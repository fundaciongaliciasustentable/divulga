#!/usr/bin/env python3
"""Poboación de cada concello galego en 1950 e en 2025 → data/datos.json

Fontes (descárganse en data/raw/ se faltan):
  ic_<código>.html  INE, «Alteraciones de los municipios en los Censos de Población desde 1842»:
                    poboación de feito (1842-1991) e de dereito (1842-2021) de cada municipio, cos
                    cambios de territorio entre censos. Unha páxina por municipio:
                    https://www.ine.es/intercensal/intercensal.do?search=3&codigoProvincia=<pp>&codigoMunicipio=<mmm>
                    Metodoloxía: https://www.ine.es/alteraciones/alteraciones_municipios_metodologia.pdf
  ine_<táboa>.json  INE, Padrón municipal, cifras oficiais a 1 de xaneiro de 2025, táboas
                    2868 (A Coruña), 2880 (Lugo), 2885 (Ourense) e 2890 (Pontevedra):
                    https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/<táboa>?nult=1&tip=AM
Xeometría dos concellos: galicia-agora (concellos-parroquias/data.geojson), simplificada aquí.

Comparación a territorio actual:
  · Oza-Cesuras (15902) = Oza dos Ríos (15063) + Cesuras (15026); Cerdedo-Cotobade (36902) =
    Cerdedo (36011) + Cotobade (36012): en 1950 súmanse os dous concellos.
  · Concellos desaparecidos despois de 1950 súmanse ao actual que os absorbeu (EXTRA): Enfesta
    (Santiago), Neira de Xusá (Baralla), Puente Nuevo e Villaodrid (A Pontenova), Acevedo do Río
    (Celanova) e Ponte Sampaio (Pontevedra).
  · Cando un concello actual se segregou doutro despois de 1950 (Cariño de Ortigueira, Burela de
    Cervo, A Illa de Vilanova de Arousa) ou cambiou termo con outro (Ribadavia e Carballeda de
    Avia), a variación calcúlase para os dous xuntos e márcase («g»).
  · As notas de alteracións do INE posteriores a 1950 gárdanse en «alt».
En 1950 cóntase a poboación de feito (a presente o día do censo) e en 2025 a empadroada.
"""
import json
import math
import re
import time
from html import unescape
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
CONCELLOS = Path("/Users/perezgulin/Proxectos/galicia-agora/data-out/concellos-parroquias/data.geojson")
UA = {"User-Agent": "Mozilla/5.0"}
FUSIONS = {"15902": ["15026", "15063"], "36902": ["36011", "36012"]}
VELLO = {v: k for k, vs in FUSIONS.items() for v in vs}
# Municipios desaparecidos despois de 1950 que hoxe son parte dun concello: súmanse en toda a serie
EXTRA = {"15078": ["15501"],           # Santiago incorpora Enfesta (1960-1970)
         "27901": ["27036"],           # Baralla é a antiga Neira de Xusá (cambio de nome)
         "27048": ["27500", "27501"],  # A Pontenova = Puente Nuevo + Villaodrid (1963)
         "32024": ["32500"],           # Celanova incorpora Acevedo do Río (1960-1970)
         "36038": ["36506"]}           # Pontevedra incorpora Ponte Sampaio (1950-1960)
# Segregacións e cambios de termo entre concellos actuais despois de 1950: compáranse xuntos
GRUPOS = [("15061", "15901", "Ortigueira e Cariño"), ("27013", "27902", "Cervo e Burela"),
          ("36061", "36901", "Vilanova de Arousa e A Illa de Arousa"), ("32069", "32018", "Ribadavia e Carballeda de Avia")]


def get(url, f, timeout=120):
    if not f.exists():
        for intento in range(4):
            try:
                f.write_bytes(urlopen(Request(url, headers=UA), timeout=timeout).read())
                break
            except Exception as e:  # o servidor do INE ás veces corta
                print("reintento", f.name, e)
                time.sleep(5)
        time.sleep(0.4)
    return f


# ---------- Xeometría: proxección plana e Douglas-Peucker ----------
fs = [f for f in json.loads(CONCELLOS.read_text(encoding="utf-8"))["features"] if f["properties"]["nivel"] == "concello"]
KX = math.cos(math.radians(42.8))
allpts = [p for f in fs for pol in (f["geometry"]["coordinates"] if f["geometry"]["type"] == "MultiPolygon" else [f["geometry"]["coordinates"]])
          for r in pol for p in r]
LON0, LAT1 = min(p[0] for p in allpts), max(p[1] for p in allpts)
S = 1000 / ((max(p[0] for p in allpts) - LON0) * KX)
proj = lambda p: ((p[0] - LON0) * KX * S, (LAT1 - p[1]) * S)


def dp(pts, tol):
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1e-9
    dmax, imax = 0, 0
    for i in range(1, len(pts) - 1):
        d = abs(dy * pts[i][0] - dx * pts[i][1] + x2 * y1 - y2 * x1) / L
        if d > dmax:
            dmax, imax = d, i
    if dmax > tol:
        return dp(pts[:imax + 1], tol)[:-1] + dp(pts[imax:], tol)
    return [pts[0], pts[-1]]


def dp_anel(r, tol):
    """Douglas-Peucker nun anel pechado: pártese polo vértice máis afastado do primeiro."""
    k = max(range(len(r)), key=lambda i: (r[i][0] - r[0][0]) ** 2 + (r[i][1] - r[0][1]) ** 2)
    return dp(r[:k + 1], tol)[:-1] + dp(r[k:], tol)


def poligono(f, tol=1.1):
    g = f["geometry"]
    out = []
    for pol in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        r = [proj(p) for p in pol[0]]
        area = abs(sum(r[i][0] * r[i - 1][1] - r[i - 1][0] * r[i][1] for i in range(len(r)))) / 2
        if area < 6:
            continue
        s = dp_anel(r, tol)
        q = []
        for x, y in s:
            p = [round(x), round(y)]
            if not q or q[-1] != p:
                q.append(p)
        if len(q) >= 4:
            out.append(q)
    return out


# ---------- Padrón 2025 ----------
pob25, ano_pad = {}, None
for t in (2868, 2880, 2885, 2890):
    for s in json.loads(get(f"https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{t}?nult=1&tip=AM", RAW / f"ine_{t}.json").read_text()):
        md = {m["T3_Variable"]: m for m in s["MetaData"]}
        if md.get("Sexo", {}).get("Codigo") != "0" or "Municipios" not in md or not s["Data"]:
            continue
        v = s["Data"][0]
        ano_pad = v["Anyo"]
        pob25[md["Municipios"]["Codigo"]] = round(v["Valor"])

# ---------- Censos históricos ----------
CEL = re.compile(r'<td[^>]*headers="(pHecho|pDerecho) (\d{4})"[^>]*>(.*?)</td>', re.S)


def censos(cod):
    f = get(f"https://www.ine.es/intercensal/intercensal.do?search=3&codigoProvincia={cod[:2]}&codigoMunicipio={cod[2:]}"
            "&btnBuscarCod=Consultar+selecci%F3n", RAW / f"ic_{cod}.html")
    t = f.read_bytes().decode("utf-8", "replace")
    hecho, dereito = {}, {}
    for k, ano, v in CEL.findall(t):
        v = re.sub(r"<[^>]+>|&nbsp;|\s", "", v)
        if v.isdigit():
            (hecho if k == "pHecho" else dereito)[int(ano)] = int(v)  # se o ano se repite, queda a 2.ª columna (termo novo)
    notas = [re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", n))).strip()
             for n in re.findall(r"&nbsp;(Entre el Censo de \d{4}[^<]*)", t)]
    return hecho, dereito, notas


conc = []
for f in fs:
    p = f["properties"]
    c = p["codigo_ine"]
    partes = FUSIONS.get(c, [c]) + EXTRA.get(c, [])
    H, D, N = {}, {}, []
    for q in partes:
        h, d, n = censos(q)
        for a, v in h.items():
            H[a] = H.get(a, 0) + v
        for a, v in d.items():
            D[a] = D.get(a, 0) + v
        N += n
    conc.append({"id": c, "n": p["nome"], "pr": p["provincia"], "pol": poligono(f), "h": H, "d": D, "p25": pob25[c],
                 "notas": N})
    print(c, p["nome"], H.get(1950), pob25[c], len(N))

# Grupos de concellos que se comparan xuntos
for a, b, nome in GRUPOS:
    cb = [o for o in conc if o["id"] in (a, b)]
    h50 = sum(o["h"].get(1950, 0) for o in cb)
    p25 = sum(o["p25"] for o in cb)
    for o in cb:
        o["g"] = {"n": nome, "h50": h50, "p25": p25}

# Alteracións de termo despois de 1950 (para revisar e amosar)
for o in conc:
    alt = [n for n in o["notas"] if int(re.search(r"Censo de (\d{4})", n).group(1)) > 1950]
    if alt:
        o["alt"] = alt
        print("ALTERACIÓN despois de 1950:", o["n"], alt)
    del o["notas"]

ok = [o for o in conc if o["h"].get(1950) or "g" in o]
assert len(ok) == len(conc), [o["n"] for o in conc if o not in ok]
print("Galicia 1950 (feito, suma):", sum(o["h"].get(1950, 0) for o in conc), "2025:", sum(o["p25"] for o in conc))
var = lambda o: (o.get("g", {}).get("p25", o["p25"]) / o.get("g", {}).get("h50", o["h"].get(1950)) - 1)
r = sorted(ok, key=var)
print("máis perden:", [(o["n"], f"{var(o):.0%}") for o in r[:8]])
print("máis gañan:", [(o["n"], f"{var(o):.0%}") for o in r[-8:]])
print("gañan:", sum(1 for o in ok if var(o) > 0), "de", len(ok))
for o in conc:  # anos como texto para JSON compacto
    o["h"] = {str(a): v for a, v in sorted(o["h"].items()) if a >= 1900}
    o["d"] = {str(a): v for a, v in sorted(o["d"].items()) if a >= 2001}
out = {"ano": ano_pad, "conc": sorted(conc, key=lambda o: o["n"])}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json", (HERE / "data" / "datos.json").stat().st_size // 1024, "KB")

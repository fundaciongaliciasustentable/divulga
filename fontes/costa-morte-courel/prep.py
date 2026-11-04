#!/usr/bin/env python3
"""Da Costa da Morte ao Courel: capas e cifras do voo → v/costa-morte-courel/capas/*.geojson
e fontes/costa-morte-courel/cifras.json.

Fontes (foto do día; cópianse en data/raw/ se faltan):
  · Capas de Mapas Galicia Sustentable (https://mapas.galiciasustentable.org/data/<capa>/data.geojson):
      vento-wrf, crecida-episodios, estado-masas-auga, aldeas-baleiras, poboacion-seculo, indicadores-concellos,
      perfil-concellos, concellos-parroquias, espazos-naturais-galicia, tmax-ano, historial-queimados
    Se existe o repositorio local ~/Proxectos/mapasgs, cóllense de site/public/data/.
  · IGE, táboa 62 (efectivos de gando bovino por concello, Consellería do Medio Rural):
      https://www.ige.gal/igebdt/igeapi/csv/datos/62
  · Alturas: MDT de 25 m do IGN en ../terreo/data/raw/ (ver ../terreo/README.md).

Uso (precisa numpy, tifffile e shapely):  python3 prep.py
"""
import base64
import csv
import datetime as dt
import json
import math
import shutil
import struct
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import tifffile
from shapely.geometry import MultiPolygon, mapping, shape

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
RAW = AQUI / "data" / "raw"
CAPAS = RAIZ / "v" / "costa-morte-courel" / "capas"
MDT = AQUI.parent / "terreo" / "data" / "raw"
LOCAL = Path.home() / "Proxectos" / "mapasgs" / "site" / "public" / "data"
WEB = "https://mapas.galiciasustentable.org/data"
UA = {"User-Agent": "DivulgaFGS/1.0 (https://divulga.galiciasustentable.org)"}
RAW.mkdir(parents=True, exist_ok=True)
CAPAS.mkdir(parents=True, exist_ok=True)
cifras = {}


def baixa(url, dest):
    if not dest.exists():
        dest.write_bytes(urlopen(Request(url, headers=UA), timeout=300).read())
    return dest


def capa(cid):
    """GeoJSON e meta.json dunha capa de Mapas GS, copiados en data/raw/<capa>/."""
    d = RAW / cid
    d.mkdir(exist_ok=True)
    for f in ("data.geojson", "meta.json"):
        if not (d / f).exists():
            if (LOCAL / cid / f).exists():
                shutil.copy(LOCAL / cid / f, d / f)
            else:
                baixa(f"{WEB}/{cid}/{f}", d / f)
    return json.loads((d / "data.geojson").read_text())["features"], json.loads((d / "meta.json").read_text())


def garda(nome, feats, nd=4):
    def r(c):
        return [r(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], nd), round(c[1], nd)]
    for f in feats:
        f["geometry"]["coordinates"] = r(f["geometry"]["coordinates"])
    txt = json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False, separators=(",", ":"))
    (CAPAS / f"{nome}.geojson").write_text(txt, encoding="utf-8")
    kb = len(txt.encode()) / 1024
    print(f"capas/{nome}.geojson  {len(feats)} elementos  {kb:.0f} KB")
    assert kb < 200, nome


def pt(lon, lat, **p):
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]}, "properties": p}


def xeom(g, tol, **p):
    s = shape(g).simplify(tol, preserve_topology=True)
    if s.geom_type == "MultiPolygon":   # sen illotes minúsculos
        partes = [x for x in s.geoms if x.area > tol * tol * 20] or [max(s.geoms, key=lambda x: x.area)]
        s = partes[0] if len(partes) == 1 else MultiPolygon(partes)
    return {"type": "Feature", "geometry": mapping(s), "properties": p}


# ── MDT: altura máxima nun recadro ───────────────────────────────────────────
def maxbox(lon1, lat1, lon2, lat2, minimo=False):
    best = None
    for lo in np.arange(math.floor(lon1 * 2) / 2, lon2, 0.5):
        for la in np.arange(math.floor((lat1 - 0.25) * 2) / 2 + 0.25, lat2, 0.5):
            f = MDT / f"mdt25_+{la:.2f}_{lo:.2f}.tif"
            if not f.exists():
                continue
            a = tifffile.imread(f)
            n = a.shape[0]
            d = 0.5 / n
            c1, c2 = max(0, int((lon1 - lo) / d)), min(n, math.ceil((lon2 - lo) / d))
            r1, r2 = max(0, int((la + 0.5 - lat2) / d)), min(n, math.ceil((la + 0.5 - lat1) / d))
            if c2 <= c1 or r2 <= r1:
                continue
            s = a[r1:r2, c1:c2]
            k = np.unravel_index(np.argmin(s) if minimo else np.argmax(s), s.shape)
            v = int(s[k])
            if best is None or (v < best[0] if minimo else v > best[0]):
                best = (v, round(lo + (c1 + k[1] + .5) * d, 4), round(la + .5 - (r1 + k[0] + .5) * d, 4))
    return best


cifras["mdt"] = {
    "monte_facho": maxbox(-9.29, 42.87, -9.26, 42.90),
    "pindo_a_moa": maxbox(-9.16, 42.86, -9.09, 42.92),
    "pico_sacro": maxbox(-8.48, 42.78, -8.42, 42.83),
    # canón do Miño arredor de Belesar: cadrado de 8 × 9 km (fondo do río e bordo)
    "belesar_rio": maxbox(-7.76, 42.58, -7.66, 42.66, minimo=True),
    "belesar_bordo": maxbox(-7.76, 42.58, -7.66, 42.66),
    "formigueiros": maxbox(-7.12, 42.59, -7.08, 42.62),
}

# ── 2 · Vento: predición WRF de MeteoGalicia (unha execución) ────────────────
(fv,), mv = capa("vento-wrf")
p = fv["properties"]
g = p["grella"]
q = p["cuantizacion_ms"]
pasos = [struct.unpack(f"{len(b)}b", b) for b in (base64.b64decode(s) for s in p["uv"])]


def vmedio(k):
    return sum(math.hypot(s[2 * k], s[2 * k + 1]) * q for s in pasos) / len(pasos)


def celda(lon, lat):
    return round((lat - g["lat0"]) / g["dlat"]) * g["nx"] + round((lon - g["lon0"]) / g["dlon"])


vento = []
for j in range(g["ny"]):
    for i in range(g["nx"]):
        lon, lat = g["lon0"] + i * g["dlon"], g["lat0"] + j * g["dlat"]
        if -9.75 <= lon <= -8.2 and 42.6 <= lat <= 43.55:
            vento.append(pt(lon, lat, v=round(vmedio(j * g["nx"] + i), 1)))
garda("vento", vento, 3)
cifras["vento"] = {"execucion": p["execucion"], "desde": p["horas"][0], "ata": p["horas"][-1],
                   "pasos": len(pasos), "ficheiro": p["ficheiro"],
                   "tourinan_ms": round(vmedio(celda(-9.297, 43.05)), 1),
                   "vilan_ms": round(vmedio(celda(-9.2235, 43.1606)), 1),
                   "santiago_ms": round(vmedio(celda(-8.545, 42.88)), 1)}

# ── 3 · Xallas: crecida de outubro de 2026 ───────────────────────────────────
fc, _ = capa("crecida-episodios")
# curso principal do Xallas (masas de auga ES-014-*-184-000-*): tramos de río e encoros
fm, _ = capa("estado-masas-auga")
xallas = [xeom(f["geometry"], 0.0004, t="rio" if f["properties"]["categoria"] == "rio" else "encoro")
          for f in fm if "-184-000-" in f["properties"]["codigo"]]
cifras["xallas_masas"] = [(f["properties"]["codigo"], f["properties"]["nome"]) for f in fm
                          if "-184-000-" in f["properties"]["codigo"]]
for f in fc:
    pr = f["properties"]
    if pr["tipo"] == "estacion" and pr["nome"].startswith("Xallas"):
        xallas.append(pt(*f["geometry"]["coordinates"], t="estacion", x=round(pr["caudal_pico"] / pr["caudal_base"], 1)))
        cifras.setdefault("xallas", {})[pr["nome"]] = {
            "episodio": pr["episodio"], "caudal_base": pr["caudal_base"], "caudal_pico": pr["caudal_pico"],
            "hora_pico": pr["hora_pico"], "veces": round(pr["caudal_pico"] / pr["caudal_base"], 1)}
garda("xallas", xallas)

# ── 4 e 11 · Aldeas: Nomenclátor 2000–2025 ──────────────────────────────────
fa, _ = capa("aldeas-baleiras")


def aldeas(codigos, nome):
    sel = [f for f in fa if f["properties"]["codigo_ine"] in codigos]
    out = []
    for f in sel:
        pr = f["properties"]
        if not f["geometry"]:
            continue
        p0, p1 = pr["pob_2000"] or 0, pr["pob"] or 0
        estado = 0 if p1 == 0 else (1 if p1 < p0 else 2)   # 0 baleira, 1 perdeu, 2 igual ou gañou
        out.append(pt(*f["geometry"]["coordinates"], p=p1, e=estado))
    garda(nome, out)
    return {"codigos": codigos, "entidades": len(sel), "sen_posicion": sum(1 for f in sel if not f["geometry"]),
            "pob_2000": sum(f["properties"]["pob_2000"] or 0 for f in sel),
            "pob_2025": sum(f["properties"]["pob"] or 0 for f in sel),
            "perderon": sum(1 for f in sel if (f["properties"]["pob_2000"] or 0) > (f["properties"]["pob"] or 0)),
            "baleiras_2025": sum(1 for f in sel if (f["properties"]["pob"] or 0) == 0)}


# Soneira (Camariñas, Vimianzo, Zas) e Xallas (Santa Comba, Mazaricos)
cifras["aldeas_soneira_xallas"] = aldeas(["15016", "15092", "15093", "15077", "15045"], "aldeas-soneira")
cifras["aldeas_courel"] = aldeas(["27017"], "aldeas-courel")
cifras["seoane"] = [(f["properties"]["nome"], f["properties"]["pob_2000"], f["properties"]["pob"])
                    for f in fa if f["properties"]["codigo_ine"] == "27017" and "Seoane" in f["properties"]["nome"]]

# ── 5 · Santiago e a súa área: censos 1991 e 2021 ───────────────────────────
fs_, _ = capa("poboacion-seculo")
fcp, _ = capa("concellos-parroquias")
censos = {f["properties"]["codigo_ine"]: f["properties"] for f in fs_}
AREA = ["15078", "15002", "15082", "15013", "15060", "15012", "15089", "15066", "15085", "15086",
        "15088", "15056", "15074", "15065", "15033", "15038", "15059", "15007"]
santiago = []
for f in fcp:
    pr = f["properties"]
    if pr["nivel"] != "concello" or pr["codigo_ine"] not in AREA:
        continue
    c = censos[pr["codigo_ine"]]
    a = dict(zip(c["censos"], c["poboacion"]))
    santiago.append(xeom(f["geometry"], 0.002, v=round((a[2021] / a[1991] - 1) * 100)))
garda("santiago", santiago)
cifras["censos"] = {censos[c]["nome"]: {a: v for a, v in zip(censos[c]["censos"], censos[c]["poboacion"]) if a in (1950, 1991, 2021)}
                    for c in ("15078", "15002", "15082")}

# ── 6 · Ulla: Sistema Fluvial Ulla-Deza (espazo protexido) ───────────────────
fe, _ = capa("espazos-naturais-galicia")
ulla = [xeom(f["geometry"], 0.0003) for f in fe if f["properties"]["nome"] == "Sistema Fluvial Ulla-Deza"]
cifras["ulla_deza"] = [f["properties"] for f in fe if f["properties"]["nome"] in ("Sistema Fluvial Ulla-Deza", "Os Ancares-O Courel")]
garda("ulla", ulla, 5)

# ── 7 · Vacas por km² (IGE táboa 62, 2025) ───────────────────────────────────
ige = baixa("https://www.ige.gal/igebdt/igeapi/csv/datos/62", RAW / "ige_62.csv")
vacas = {}
for cols in list(csv.reader(ige.read_text(encoding="latin-1").splitlines()))[1:]:
    if cols[0] == "Número de vacas" and cols[2] == "2025" and cols[5]:
        vacas[cols[3]] = float(cols[5])
fpc, _ = capa("perfil-concellos")
sup = {f["properties"]["codigo_ine"]: f["properties"]["superficie_km2"] for f in fpc}
nomes = {f["properties"]["codigo_ine"]: f["properties"]["nome"] for f in fpc}
den = {c: vacas.get(c, 0) / s for c, s in sup.items()}
vac = [xeom(f["geometry"], 0.008, v=round(den[f["properties"]["codigo_ine"]], 1)) for f in fcp
       if f["properties"]["nivel"] == "concello"]
garda("vacas", vac, 3)
DEZA = ["36024", "36052", "36059", "36020", "36047", "36016"]
cifras["vacas_2025"] = {
    "galicia": vacas["12"], "galicia_km2": round(sum(sup.values()), 1),
    "galicia_por_km2": round(vacas["12"] / sum(sup.values()), 1),
    "lalin": vacas["36024"], "lalin_km2": sup["36024"], "lalin_por_km2": round(den["36024"], 1),
    "deza": sum(vacas[c] for c in DEZA), "deza_km2": round(sum(sup[c] for c in DEZA), 1),
    "deza_por_km2": round(sum(vacas[c] for c in DEZA) / sum(sup[c] for c in DEZA), 1),
    "top5": sorted(((round(v, 1), nomes[c]) for c, v in den.items()), reverse=True)[:5]}

# ── 9 · Calor: días de 35 °C ou máis en 2025 por estación ────────────────────
ft, _ = capa("tmax-ano")
tmax = []
for f in ft:
    pr = f["properties"]
    vals = [v for v in pr["tmax"] if v is not None]
    if len(vals) < 330:
        continue
    d35 = sum(1 for v in vals if v >= 35)
    tmax.append(pt(*f["geometry"]["coordinates"], d=d35))
    if pr["nome"] in ("Monforte", "Camariñas", "Santiago-EOAS", "Ourense", "Courel", "Lalín", "San Clodio"):
        i = max(range(len(pr["tmax"])), key=lambda k: pr["tmax"][k] if pr["tmax"][k] is not None else -99)
        cifras.setdefault("tmax_2025", {})[pr["nome"]] = {
            "altitude": pr["altitude"], "dias_con_dato": len(vals), "dias_35": d35, "maxima": max(vals),
            "data_maxima": (dt.date(pr["ano"], 1, 1) + dt.timedelta(i)).isoformat()}
garda("tmax", tmax)

# ── 10 · Lume: perímetros EFFIS 2016–2025 no leste de Lugo ──────────────────
fq, _ = capa("historial-queimados")
lume = []
for f in fq:
    pr = f["properties"]
    s = shape(f["geometry"])
    c = s.centroid
    if -7.45 <= c.x <= -6.85 and 42.35 <= c.y <= 42.85:
        lume.append(xeom(f["geometry"], 0.0008, a=pr["ano"]))
garda("lume", lume)
cifras["lume_courel_2022"] = [f["properties"] for f in fq
                              if f["properties"]["concello"] == "Folgoso do Courel" and f["properties"]["ano"] == 2022]

# ── 11 · Folgoso do Courel: idade e censos ───────────────────────────────────
fi, mi = capa("indicadores-concellos")
fol = next(f["properties"] for f in fi if f["properties"]["codigo_ine"] == "27017")
cifras["folgoso"] = {"maiores_65_pct": fol["maiores_65_pct"], "periodo": fol["maiores_65_pct_periodo"],
                     "galicia": fol["maiores_65_pct_galicia"],
                     "censos": {a: v for a, v in zip(censos["27017"]["censos"], censos["27017"]["poboacion"])}}

cifras["consulta"] = dt.date.today().isoformat()
(AQUI / "cifras.json").write_text(json.dumps(cifras, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
print(json.dumps(cifras, ensure_ascii=False, indent=1, default=str))

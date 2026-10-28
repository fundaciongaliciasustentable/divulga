#!/usr/bin/env python3
"""Minutos en coche dende cada núcleo de poboación ao hospital público máis próximo → data/datos.json

Fontes (gardadas en data/raw/, que non se sobe):
  · Ministerio de Sanidade, Catálogo Nacional de Hospitais 2025 (hospitais a 31/12/2024), Excel:
    https://www.sanidad.gob.es/estadEstudios/estadisticas/sisInfSanSNS/ofertaRecursos/hospitales/docs/CNH_2025.xlsx
    Quédanse os hospitais xerais (clase C11) de Galicia con dependencia funcional «Servizos de saúde
    das comunidades autónomas» (o Sergas): 14 centros. Os complexos (CHUAC, CHUS…) contan no seu
    edificio principal, o do enderezo do catálogo.
  · Coordenadas dos hospitais: OpenStreetMap vía Nominatim (https://nominatim.openstreetmap.org),
    unha consulta por hospital, comprobada co enderezo do catálogo.
  · IGE, Nomenclátor 2025: poboación de cada entidade singular (aldea, lugar, núcleo):
    https://www.ige.gal/igebdt/igeapi/csv/nomenc/2025/0/0/0/1/0/0
  · Puntos das entidades de poboación (IET, Xunta) e parroquias, de galicia-agora (como en
    galicia-apagandose); se unha entidade non ten punto, úsase o centro da súa parroquia.
  · Tempos e distancias por estrada: OSRM (http://project-osrm.org), servidor público
    https://router.project-osrm.org/table/v1/driving/ con datos de OpenStreetMap, perfil de coche,
    sen tráfico. Unha petición por cada 86 entidades (máx. 1 por segundo), gardadas en data/raw/osrm/.
  · Polígonos dos concellos: os xa proxectados de monte-concellos (como en casas-baleiras).
Agregación por concello: media dos minutos de cada entidade ponderada pola súa poboación.
"""
import csv
import json
import math
import re
import time
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
GA = Path("/Users/perezgulin/Proxectos/galicia-agora/data-out")
UA = {"User-Agent": "divulga-fgs-prep/1.0"}
CNH = "https://www.sanidad.gob.es/estadEstudios/estadisticas/sisInfSanSNS/ofertaRecursos/hospitales/docs/CNH_2025.xlsx"
NOMENC = "https://www.ige.gal/igebdt/igeapi/csv/nomenc/2025/0/0/0/1/0/0"
OSRM = "https://router.project-osrm.org/table/v1/driving/"
FUSIONS = {"15026": "15902", "15063": "15902", "36011": "36902", "36012": "36902"}
# Consulta a Nominatim para cada hospital do catálogo (CODCNH) e nome curto para a peza
HOSP = {"150011": ("Complexo Hospitalario Universitario da Coruña", "CHU da Coruña"),
        "150130": ("Hospital Arquitecto Marcide Ferrol", "CHU de Ferrol"),
        "150200": ("Hospital Clínico Universitario de Santiago de Compostela Choupana", "CHU de Santiago"),
        "150336": ("Hospital da Barbanza", "Hospital da Barbanza (Ribeira)"),
        "150341": ("Hospital Virxe da Xunqueira", "Hospital Virxe da Xunqueira (Cee)"),
        "270018": ("Hospital Universitario Lucus Augusti", "CHU de Lugo"),
        "270095": ("Hospital da Mariña Burela", "Hospital da Mariña (Burela)"),
        "270109": ("Hospital de Monforte", "Hospital de Monforte"),
        "320013": ("Complexo Hospitalario Universitario de Ourense", "CHU de Ourense"),
        "320126": ("Hospital de Valdeorras", "Hospital de Valdeorras (O Barco)"),
        "320150": ("Hospital Público de Verín", "Hospital de Verín"),
        "360340": ("Hospital Montecelo", "CHU de Pontevedra"),
        "360353": ("Hospital Público do Salnés", "Hospital do Salnés (Vilagarcía)"),
        "360368": ("Hospital Álvaro Cunqueiro Vigo", "CHU de Vigo")}


def get(url, timeout=300):
    for i in range(5):
        try:
            return urlopen(Request(url, headers=UA), timeout=timeout).read()
        except Exception as e:  # o servidor público de OSRM ás veces corta
            print("  reintento", i + 1, e)
            time.sleep(5 * (i + 1))
    raise SystemExit("non se puido descargar " + url)


def xlsx(path, folla):
    """Le unha folla dun .xlsx só coa biblioteca estándar."""
    z = zipfile.ZipFile(path)
    m = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    ss = ["".join(t.text or "" for t in si.iter(m + "t")) for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(m + "si")]
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
    s = next(s for s in wb.iter(m + "sheet") if s.get("name") == folla)
    t = rels[s.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")].lstrip("/")
    filas = []
    for r in ET.fromstring(z.read(t if t.startswith("xl/") else "xl/" + t)).iter(m + "row"):
        fila = {}
        for c in r.iter(m + "c"):
            col = sum((ord(ch) - 64) * 26 ** i for i, ch in enumerate(reversed(re.match(r"[A-Z]+", c.get("r")).group())))
            v = c.find(m + "v")
            fila[col - 1] = ss[int(v.text)] if c.get("t") == "s" else (v.text if v is not None else None)
        filas.append([fila.get(i) for i in range(max(fila) + 1)] if fila else [])
    return filas


def norm(s):
    s = unicodedata.normalize("NFD", s.upper())
    s = "".join(c for c in s if not unicodedata.combining(c))
    m = re.match(r"^(.*), (O|A|OS|AS)$", s)
    if m:
        s = f"{m.group(2)} {m.group(1)}"
    return re.sub(r"[^A-Z0-9]+", " ", s).strip()


def bonito(s):
    m = re.match(r"^(.*), (O|A|OS|AS)$", s)
    if m:
        s = f"{m.group(2)} {m.group(1)}"
    pal = s.lower().split(" ")
    return " ".join(p if (p in {"de", "do", "da", "dos", "das", "e"} and i) else p[:1].upper() + p[1:] for i, p in enumerate(pal))


def centroide(geom):
    """Centroide de área do anel exterior máis grande (sen shapely)."""
    aneis = [geom["coordinates"][0]] if geom["type"] == "Polygon" else [p[0] for p in geom["coordinates"]]
    def ac(r):
        a = cx = cy = 0
        for (x0, y0), (x1, y1) in zip(r, r[1:]):
            k = x0 * y1 - x1 * y0
            a += k; cx += (x0 + x1) * k; cy += (y0 + y1) * k
        return a / 2, cx / (3 * a) if a else r[0][0], cy / (3 * a) if a else r[0][1]
    a, x, y = max((ac(r) for r in aneis), key=lambda t: abs(t[0]))
    return x, y


hav = lambda a, b, c, d: 6371 * 2 * math.asin(math.sqrt(math.sin(math.radians(c - a) / 2) ** 2 + math.cos(math.radians(a)) *
                                                          math.cos(math.radians(c)) * math.sin(math.radians(d - b) / 2) ** 2))
RAW.mkdir(parents=True, exist_ok=True)

# 1. Hospitais do Sergas no catálogo
f = RAW / "CNH_2025.xlsx"
if not f.exists():
    f.write_bytes(get(CNH))
cab, *filas = xlsx(f, "DIRECTORIO DE HOSPITALES")
ix = {k: i for i, k in enumerate(cab)}
hosp = [r for r in filas if r and r[ix["Cód. CCAA"]] == "12" and r[ix["Cód. Clase de Centro"]] == "C11" and r[ix["Cód. Dep. Funcional"]] == "2"]
assert {r[ix["CODCNH"]] for r in hosp} == set(HOSP), sorted(r[ix["Nombre Centro"]] for r in hosp)
geo = RAW / "nominatim.json"
gc = json.loads(geo.read_text()) if geo.exists() else {}
H = []
for r in sorted(hosp, key=lambda r: r[ix["CODCNH"]]):
    cod = r[ix["CODCNH"]]
    if cod not in gc:
        res = json.loads(get("https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=es&q=" + quote(HOSP[cod][0])))
        gc[cod] = res[0]
        time.sleep(1.1)
    g = gc[cod]
    H.append({"cod": cod, "n": HOSP[cod][1], "cnh": r[ix["Nombre Centro"]], "camas": int(r[ix["CAMAS"]]), "conc": r[ix["Municipio"]],
              "lat": float(g["lat"]), "lon": float(g["lon"])})
    print(f"  {HOSP[cod][1]:34} {r[ix['CAMAS']]:>5} camas  {g['lat'][:8]}, {g['lon'][:8]}  ← {g['display_name'][:60]}")
geo.write_text(json.dumps(gc, ensure_ascii=False, indent=1))

# 2. Entidades de poboación do Nomenclátor 2025 e as súas coordenadas
f = RAW / "nomenclator_2025.csv"
if not f.exists():
    f.write_bytes(get(NOMENC))
ents = [x for x in csv.DictReader(f.open(encoding="latin1")) if int(x["pobtotal"]) > 0]
fs = json.loads((GA / "entidades-poboacion/data.geojson").read_text(encoding="utf-8"))["features"]
porcod, pornome = defaultdict(list), defaultdict(list)
for ft in fs:
    p = ft["properties"]
    if not ft["geometry"]:
        continue
    if p["codigo"]:
        porcod[p["codigo"][:9]].append(ft)
    if p["codigo_ine"]:
        pornome[(p["codigo_ine"], norm(p["nome"]))].append(ft)
PRI = {"PU": 0, "EN": 1, "NU": 2, "END": 3, "EH": 4, "ED": 5, "LU": 6}
cg = json.loads((GA / "concellos-parroquias/data.geojson").read_text(encoding="utf-8"))["features"]
cparr = {ft["properties"]["codigo_parroquia"]: centroide(ft["geometry"]) for ft in cg if ft["properties"]["nivel"] == "parroquia"}
modo, E = Counter(), []
for x in ents:
    k = x["codprov"] + x["codmun"] + x["ec"] + x["es"]
    c = FUSIONS.get(k[:5], k[:5])
    cand = porcod.get(k) or pornome.get((c, norm(x["nome"])))
    if cand:
        ft = min(cand, key=lambda ft: (PRI.get(ft["properties"]["tipo"], 9), -(ft["properties"]["poboacion"] or 0)))
        lon, lat = ft["geometry"]["coordinates"]
        modo["punto"] += 1
    elif k[:7] in cparr:
        lon, lat = cparr[k[:7]]
        modo["parroquia"] += 1
    else:
        modo["sen"] += 1
        continue
    E.append({"k": k, "c": c, "n": bonito(x["nome"]), "p": int(x["pobtotal"]), "lon": lon, "lat": lat})
print("entidades con poboación:", len(ents), dict(modo), "poboación", sum(e["p"] for e in E))

# 3. Tempos por estrada con OSRM (todas as entidades contra os 14 hospitais)
LOTE = 86
dst = ";".join(f"{h['lon']:.5f},{h['lat']:.5f}" for h in H)
(RAW / "osrm").mkdir(exist_ok=True)
for i in range(0, len(E), LOTE):
    fo = RAW / "osrm" / f"{i // LOTE:04d}.json"
    lote = E[i:i + LOTE]
    if not fo.exists():
        src = ";".join(f"{e['lon']:.5f},{e['lat']:.5f}" for e in lote)
        url = (OSRM + src + ";" + dst + "?sources=" + ";".join(map(str, range(len(lote)))) +
               "&destinations=" + ";".join(str(len(lote) + j) for j in range(len(H))) + "&annotations=duration,distance")
        d = json.loads(get(url, 120))
        assert d["code"] == "Ok", d
        fo.write_text(json.dumps({"durations": d["durations"], "distances": d["distances"],
                                  "snap": [round(s["distance"]) for s in d["sources"]]}))
        time.sleep(1.0)
        if (i // LOTE) % 25 == 0:
            print("  osrm", i, "/", len(E))
    d = json.loads(fo.read_text())
    for e, du, di, sn in zip(lote, d["durations"], d["distances"], d["snap"]):
        ok = [(t, s, j) for j, (t, s) in enumerate(zip(du, di)) if t is not None]
        if ok:
            t, s, j = min(ok)
            e.update(m=t / 60, km=s / 1000, h=j, snap=sn)
        e["lr"] = min(hav(e["lat"], e["lon"], h["lat"], h["lon"]) for h in H)
sen = [e for e in E if "m" not in e]
print("sen ruta:", len(sen), sum(e["p"] for e in sen), "hab")
E = [e for e in E if "m" in e]
lonxe = [e for e in E if e["snap"] > 2000]
print("entidades a máis de 2 km da estrada máis próxima no mapa de OSRM:", len(lonxe), [(e["n"], e["snap"]) for e in lonxe[:8]])

# 4. Agregados por concello e para Galicia
mc = json.loads((HERE.parent / "monte-concellos" / "data" / "datos.json").read_text(encoding="utf-8"))
por = defaultdict(list)
for e in E:
    por[e["c"]].append(e)
X0, Y1, KX = -9.4, 43.9, 0.7325
pr = lambda lon, lat: (round((lon - X0) * KX * 1000), round((Y1 - lat) * 1000))
pm = lambda es, k: sum(e[k] * e["p"] for e in es) / sum(e["p"] for e in es)
conc = []
for c in mc["concellos"]:
    es = por[c["id"]]
    P = sum(e["p"] for e in es)
    peor = max(es, key=lambda e: e["m"])
    hh = Counter()
    for e in es:
        hh[e["h"]] += e["p"]
    # Polígonos máis lixeiros: un de cada dous vértices (o mapa é pequeno)
    pol = [r[::2] + [r[0]] if len(r) > 12 else r for r in c["pol"]]
    conc.append({"id": c["id"], "n": c["n"], "pr": c["pr"], "pol": pol, "pob": P, "ne": len(es),
                 "m": round(pm(es, "m"), 1), "km": round(pm(es, "km"), 1), "lr": round(pm(es, "lr"), 1),
                 "p30": round(sum(e["p"] for e in es if e["m"] > 30) / P, 3), "p45": round(sum(e["p"] for e in es if e["m"] > 45) / P, 3),
                 "h": hh.most_common(1)[0][0], "pe": [peor["n"], round(peor["m"]), peor["p"]],
                 # distribución de habitantes por minuto (para a curva acumulada do concello)
                 "cu": [sum(e["p"] for e in es if b <= e["m"] < b + 5) for b in range(0, 120, 5)]})
tot = sum(e["p"] for e in E)
gal = {"pob": tot, "m": round(pm(E, "m"), 1), "km": round(pm(E, "km"), 1), "lr": round(pm(E, "lr"), 1),
       "p30": round(sum(e["p"] for e in E if e["m"] > 30) / tot, 3), "p45": round(sum(e["p"] for e in E if e["m"] > 45) / tot, 3),
       "p15": round(sum(e["p"] for e in E if e["m"] <= 15) / tot, 3), "ne": len(E),
       "h30": sum(e["p"] for e in E if e["m"] > 30), "h45": sum(e["p"] for e in E if e["m"] > 45),
       "cu": [sum(e["p"] for e in E if b <= e["m"] < b + 1) for b in range(0, 150)]}
# Grella de 3 km × 3 km para o mapa: media ponderada dos minutos das entidades de cada cela
CEL = 27  # unidades do mapa (1/1000 de grao de latitude ≈ 111 m)
cel = defaultdict(lambda: [0, 0])
for e in E:
    x, y = pr(e["lon"], e["lat"])
    q = cel[(x // CEL, y // CEL)]
    q[0] += e["m"] * e["p"]; q[1] += e["p"]
grella = [[i, j, round(s / p), p] for (i, j), (s, p) in sorted(cel.items())]
out = {"gal": gal, "conc": conc, "cel": CEL, "grella": grella,
       "hosp": [{"n": h["n"], "cnh": h["cnh"], "camas": h["camas"], "xy": pr(h["lon"], h["lat"])} for h in H]}
for c in sorted(conc, key=lambda c: -c["m"])[:10]:
    print(f"  {c['n']:24} {c['m']:5.1f} min  {c['km']:5.1f} km estrada  {c['lr']:5.1f} km liña recta  >30 min {c['p30']:.0%}")
print("Galicia:", {k: v for k, v in gal.items() if k != "cu"})
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json", (HERE / "data" / "datos.json").stat().st_size // 1024, "KB")

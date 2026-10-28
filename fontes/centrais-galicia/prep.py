#!/usr/bin/env python3
"""As centrais eléctricas de Galicia, unha a unha, cos seus MW → data/datos.json

Non hai un rexistro aberto de centrais con potencia (o RAIPEE do MITECO non se descarga), así
que se xuntan tres fontes colaborativas e cóntase canto cobren fronte aos totais oficiais:
  · OpenStreetMap: power=plant en Galicia (Overpass), con plant:output:electricity
  · Wikidata: centrais eléctricas (Q159719 e subclases) con potencia instalada (P2109) no
    recadro de Galicia, filtradas despois polo contorno
  · Galipedia, «Parques eólicos en Galicia»: táboas con potencia en kW de cada parque
  · Totais: REE, nota de prensa «Galicia» do Informe do Sistema Eléctrico 2025 (9.892 MW a
    31/12/2025 e o reparto en % por tecnoloxía):
    https://www.ree.es/sites/default/files/07_SALA_PRENSA/Documentos/2026/np-galicia.pdf
Duplicados: a mesma central en varias fontes xúntase polo nome normalizado (sen «P. E.»,
«central», tiles…) ou, se ten coordenadas, por estar a menos de 2 km e ser da mesma tecnoloxía.
Quédase a potencia de Wikidata ou da Galipedia, que adoitan citar fonte, e se non, a de OSM.
Todo vai en data/raw/ (descárgase se falta).
"""
import json
import math
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from shapely.geometry import Point, shape

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
UA = {"User-Agent": "DivulgaFGS/1.0 (https://divulga.galiciasustentable.org)"}
CONTORNO = HERE.parent / "galicia-apagandose" / "data" / "galicia.geojson"
OVERPASS = """[out:json][timeout:180];
area["ISO3166-2"="ES-GA"]->.g;
nwr["power"="plant"](area.g);
out center tags;"""
SPARQL = """SELECT ?c ?cLabel ?pot ?un ?coord ?tipoLabel WHERE {
  SERVICE wikibase:box { ?c wdt:P625 ?coord . bd:serviceParam wikibase:cornerSouthWest "Point(-9.35 41.8)"^^geo:wktLiteral .
    bd:serviceParam wikibase:cornerNorthEast "Point(-6.7 43.85)"^^geo:wktLiteral . }
  ?c wdt:P31/wdt:P279* wd:Q159719 .
  ?c p:P2109/psv:P2109 [ wikibase:quantityAmount ?pot ; wikibase:quantityUnit ?un ] .
  OPTIONAL { ?c wdt:P31 ?tipo . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "gl,es,en". }
}"""
# REE 2025: 9.892 MW e o reparto por tecnoloxía da nota de prensa
REE_TOTAL = 9892
REE_PC = {"eolica": 40.7, "hidraulica": 37.7, "ciclo": 12.6, "coxeneracion": 5.0, "solar": 2.7}
NOMES_TEC = {"eolica": "Eólica", "hidraulica": "Hidráulica", "ciclo": "Ciclo combinado", "coxeneracion": "Coxeración",
             "solar": "Solar fotovoltaica", "outras": "Outras (residuos, biomasa, gasóleo)"}

RAW.mkdir(parents=True, exist_ok=True)


def baixa(nome, fn):
    f = RAW / nome
    if not f.exists():
        f.write_bytes(fn())
    return json.loads(f.read_text(encoding="utf-8"))


osm = baixa("osm_plants.json", lambda: urlopen(Request("https://overpass-api.de/api/interpreter",
                                                       data=urlencode({"data": OVERPASS}).encode(), headers=UA), timeout=240).read())["elements"]
wd = baixa("wikidata.json", lambda: urlopen(Request("https://query.wikidata.org/sparql?" + urlencode({"query": SPARQL}),
                                                    headers={**UA, "Accept": "application/sparql-results+json"}), timeout=200).read())
gp = baixa("galipedia_eolicos.json", lambda: urlopen(Request("https://gl.wikipedia.org/w/api.php?" + urlencode(
    {"action": "parse", "page": "Parques eólicos en Galicia", "prop": "text|revid", "format": "json"}), headers=UA), timeout=60).read())
gal = shape(json.loads(CONTORNO.read_text(encoding="utf-8"))["geometry"]).buffer(0)

PALABRAS = {"p", "e", "pe", "parque", "eolico", "central", "hidroelectrica", "hidroelectrico", "hydro", "power", "plant", "station",
            "de", "do", "da", "dos", "das", "del", "la", "el", "o", "a", "os", "as", "encoro", "presa", "embalse", "salto",
            "ciclo", "combinado", "wind", "farm", "termica", "y", "e", "i", "ii", "iii", "repotenciacion", "fase"}
# Térmicas de carbón que seguen en Wikidata con potencia pero xa non producen: van á parte
PECHADAS = {"central termica das pontes", "central termica de meirama"}
FORA = {"cornatel hydro power plant"}  # en León: Wikidata ponlle as coordenadas dentro do contorno


def norm(n):
    n = "".join(c for c in unicodedata.normalize("NFD", n.lower()) if unicodedata.category(c) != "Mn")
    return " ".join(w for w in re.findall(r"[a-z0-9ñ]+", n) if w not in PALABRAS)


def mw(s):
    m = re.match(r"\s*([\d.,]+)\s*(gw|mw|kw|w)?", (s or "").lower())
    if not m:
        return None
    v = float(m.group(1).replace(",", "."))
    return {"gw": v * 1000, "kw": v / 1000, "w": v / 1e6}.get(m.group(2) or "mw", v)


def tec_osm(t):
    s = t.get("plant:source", "")
    if s == "wind":
        return "eolica"
    if s == "hydro":
        return "hidraulica"
    if s == "solar":
        return "solar"
    if s == "gas":
        return "ciclo"
    return "outras"


def tec_wd(t):
    t = t.lower()
    if "eólic" in t or "wind" in t:
        return "eolica"
    if "hidro" in t or "presa" in t or "encoro" in t:
        return "hidraulica"
    if "ciclo" in t or "gas" in t:
        return "ciclo"
    if "solar" in t or "fotovolt" in t:
        return "solar"
    return "outras"


# 1. Candidatas de cada fonte: (fonte, nome, tecnoloxía, MW, lat, lon, concello)
cand = []
for e in osm:
    t = e.get("tags", {})
    v = mw(t.get("plant:output:electricity"))
    if not v or not t.get("name"):
        continue
    lat, lon = (e["lat"], e["lon"]) if "lat" in e else (e["center"]["lat"], e["center"]["lon"])
    cand.append({"f": "OSM", "n": t["name"], "t": tec_osm(t), "mw": v, "lat": lat, "lon": lon, "c": ""})
porc = {}
for x in wd["results"]["bindings"]:
    m = re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", x["coord"]["value"])
    lon, lat = float(m[1]), float(m[2])
    if not gal.contains(Point(lon, lat)):
        continue  # o recadro colle Portugal, Asturias e León
    q = x["c"]["value"].rsplit("/", 1)[-1]
    e = porc.setdefault(q, {"f": "Wikidata", "n": x["cLabel"]["value"], "t": "outras", "mw": 0, "lat": lat, "lon": lon, "c": ""})
    e["mw"] = max(e["mw"], float(x["pot"]["value"]))  # se hai varios valores (ampliacións), o maior
    if "tipoLabel" in x and e["t"] == "outras":
        e["t"] = tec_wd(x["tipoLabel"]["value"])
cand += [e for e in porc.values() if e["mw"]]
texto = gp["parse"]["text"]["*"]
for tb in re.findall(r"<table.*?</table>", texto, re.S):
    filas = [[re.sub(r"\s+", " ", re.sub(r"<[^>]+>|\[\s*\d+\s*\]", " ", c)).strip() for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", r, re.S)]
             for r in re.findall(r"<tr.*?</tr>", tb, re.S)]
    if not filas or "Potencia" not in " ".join(filas[0]):
        continue
    for r in filas[1:]:
        kw = re.sub(r"[^\d]", "", r[-1]) if len(r) >= len(filas[0]) else ""
        if kw:
            import html as _h
            cand.append({"f": "Galipedia", "n": _h.unescape(r[0]), "t": "eolica", "mw": int(kw) / 1000, "lat": None, "lon": None,
                         "c": _h.unescape(re.sub(r"\s*\(.*?\)", "", r[1])).replace(" ,", ",").replace("  ", " ")})

# 2. Xuntar duplicados
PRIO = {"Wikidata": 0, "Galipedia": 1, "OSM": 2}
cand.sort(key=lambda e: PRIO[e["f"]])
dist = lambda a, b: math.hypot((a["lon"] - b["lon"]) * 81.6, (a["lat"] - b["lat"]) * 111.0)
centrais = []
for e in cand:
    k = norm(e["n"])
    igual = None
    for c in centrais:
        if e["f"] in c["fontes"]:
            continue  # dúas entradas da mesma fonte son centrais distintas (fases, ampliacións)
        if c["t"] != e["t"] and not ({c["t"], e["t"]} <= {"hidraulica", "outras"}):
            continue
        ck = norm(c["n"])
        if k and ck and (k == ck or (len(k) > 4 and len(ck) > 4 and (k in ck or ck in k))
                         or (e["t"] == "eolica" and SequenceMatcher(None, k, ck).ratio() >= 0.85)):
            igual = c
            break
        if e["lat"] is not None and c["lat"] is not None and dist(e, c) < 2:
            igual = c
            break
    if igual:
        igual["fontes"].add(e["f"])
        if "repotenciac" in e["n"].lower():  # a repotenciación substitúe o parque vello: vale a potencia nova
            igual["mw"], igual["n"] = e["mw"], e["n"]
        if igual["lat"] is None and e["lat"] is not None:
            igual["lat"], igual["lon"] = e["lat"], e["lon"]
        continue
    centrais.append({**e, "fontes": {e["f"]}})

for c in centrais:
    sen = "".join(ch for ch in unicodedata.normalize("NFD", c["n"].lower()) if unicodedata.category(ch) != "Mn")
    c["pech"] = sen in PECHADAS
    c["fora"] = sen in FORA
centrais = [c for c in centrais if not c["fora"]]
pechadas = [c for c in centrais if c["pech"]]
centrais = [c for c in centrais if not c["pech"]]
tot = {}
for c in centrais:
    tot[c["t"]] = tot.get(c["t"], 0) + c["mw"]
ree = {k: round(REE_TOTAL * v / 100) for k, v in REE_PC.items()}
print(f"{len(centrais)} centrais · {sum(tot.values()):.0f} MW de {REE_TOTAL}")
for k in NOMES_TEC:
    print(f"  {NOMES_TEC[k]:38} {tot.get(k, 0):7.0f} MW de {ree.get(k, '–')}  "
          f"({sum(1 for c in centrais if c['t'] == k)} centrais)")
for c in sorted(centrais, key=lambda c: -c["mw"])[:12]:
    print(f"    {c['n']:40} {c['t']:11} {c['mw']:7.1f} {sorted(c['fontes'])}")
print("pechadas:", [(c["n"], c["mw"]) for c in pechadas])
out = {"pech": [{"n": c["n"], "mw": c["mw"]} for c in pechadas], "c": [{"n": c["n"], "t": c["t"], "mw": round(c["mw"], 2), "f": sorted(c["fontes"]), "co": c["c"]} for c in centrais],
       "ree": ree, "reeTotal": REE_TOTAL, "tec": NOMES_TEC, "rev": gp["parse"]["revid"]}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json")

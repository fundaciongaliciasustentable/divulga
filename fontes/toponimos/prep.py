#!/usr/bin/env python3
"""Os topónimos máis repetidos de Galicia: as raíces dos nomes das entidades de poboación → data/datos.json

Fontes:
  IGE, Nomenclátor 2025 (entidades singulares de poboación, con código e nome oficial):
      https://www.ige.gal/igebdt/igeapi/csv/nomenc/2025/0/0/0/1/0/0   → data/raw/nomenc_2025.csv
  Instituto de Estudos do Territorio (Xunta), capa PBA de entidades de poboación (puntos), vía
      https://ideg.xunta.gal/servizos/rest/services/PBA/EntidadesPoboacion_PBA/MapServer/0
      (copia local en galicia-agora/data-out/entidades-poboacion/data.geojson)
  IET, límites de concellos (galicia-agora/data-out/concellos-parroquias/data.geojson), servizo
      https://ideg.xunta.gal/servizos/rest/services/LimitesAdministrativos/LimitesAdministrativos/MapServer

Criterio da raíz (explicado tamén na páxina):
  1. Quítase o artigo: «VILAR, O» → «Vilar»; «A IGREXA» → «Igrexa».
  2. A raíz é a primeira palabra do nome que queda: «Vilar de Arriba», «Vilar de Cima» → Vilar.
     Excepcións: San/Santa/Santo/Santiago/Vila/Ponte/Porto/Pena/Vilar… seguen sendo a primeira
     palabra; só os hagiotopónimos (San, Santa, Santo, Santa María…) levan a palabra seguinte,
     porque «San» só non é un lugar: «San Martiño», «Santa Mariña».
  3. Os plurais xúntanse co singular cando o singular existe como raíz: Pazos → Pazo,
     Outeiros → Outeiro, Vilares → Vilar, Lamas → Lama (a ficha mostra as variantes).
  4. Non se xuntan derivados nin diminutivos: Vilariño, Outeiriño, Castrelo son raíces propias.
Cada entidade leva o punto do IET co mesmo código (provincia+concello+colectiva+singular); se non o
hai, búscase polo nome dentro do concello; as que non casan contan nas cifras pero non no mapa.
"""
import csv
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
GA = Path("/Users/perezgulin/Proxectos/galicia-agora/data-out")
URL = "https://www.ige.gal/igebdt/igeapi/csv/nomenc/2025/0/0/0/1/0/0"
FUSIONS = {"15026": "15902", "15063": "15902", "36011": "36902", "36012": "36902"}
ART = {"O", "A", "OS", "AS"}
MIN = {"de", "do", "da", "dos", "das", "e", "o", "a", "os", "as"}


def sen(s):
    s = unicodedata.normalize("NFD", s.upper())
    return re.sub(r"[^A-Z0-9 ]+", " ", "".join(c for c in s if not unicodedata.combining(c))).strip()


def bonito(s):
    """«ADRO, O» → «O Adro»; «TRAS DA IGREXA» → «Tras da Igrexa»"""
    m = re.match(r"^(.*), (O|A|OS|AS)$", s)
    if m:
        s = f"{m.group(2)} {m.group(1)}"
    pal = s.lower().split(" ")
    return " ".join(p if (p in MIN and i) else p[:1].upper() + p[1:] for i, p in enumerate(pal))


def sen_artigo(s):
    """«VILAR, O» / «O VILAR» → «VILAR»"""
    m = re.match(r"^(.*), (O|A|OS|AS)$", s)
    if m:
        return m.group(1)
    p = s.split(" ", 1)
    return p[1] if len(p) == 2 and p[0] in ART else s


SANTOS = {"SAN", "SANTA", "SANTO", "SANTOS", "SANTAS", "SAO", "SÃO"}


def raiz_crua(nome):
    w = sen_artigo(nome.strip()).replace("-", " ").split()
    if not w:
        return None
    if w[0] in SANTOS and len(w) > 1:
        seg = w[1] if w[1] not in {"DE", "DO", "DA"} else (w[2] if len(w) > 2 else "")
        if w[1] == "MARIA" or w[1] == "MARÍA":
            return f"{w[0]} {w[1]}"
        return f"{w[0]} {seg}".strip()
    return w[0]


# --- 1. Nomenclátor do IGE
RAW.mkdir(parents=True, exist_ok=True)
fn = RAW / "nomenc_2025.csv"
if not fn.exists() or fn.stat().st_size < 100_000:
    fn.write_bytes(urlopen(Request(URL, headers={"User-Agent": "Mozilla/5.0"}), timeout=300).read())
ents = []
for x in csv.DictReader(fn.open(encoding="latin1")):
    k = x["codprov"] + x["codmun"] + x["ec"] + x["es"]
    ents.append({"k": k, "c": FUSIONS.get(k[:5], k[:5]), "nome": x["nome"].strip(), "p": int(x["pobtotal"] or 0)})
print("entidades singulares:", len(ents))

# --- 2. Raíces: plurais → singular se o singular existe
crua = Counter(raiz_crua(e["nome"]) for e in ents)
def sing(r):
    if " " in r or len(r) < 4:
        return r
    if r.endswith("ES") and crua.get(r[:-2], 0) > 0 and len(r) > 5:
        return r[:-2]
    if r.endswith("S") and crua.get(r[:-1], 0) > 0:
        return r[:-1]
    return r
var = defaultdict(Counter)
for e in ents:
    rc = raiz_crua(e["nome"])
    e["r"] = sing(rc)
    var[e["r"]][rc] += 1

# --- 3. Coordenadas (IET), proxectadas a unha grella local
fs = json.loads((GA / "entidades-poboacion/data.geojson").read_text(encoding="utf-8"))["features"]
porcod, pornome = {}, defaultdict(list)
PRI = {"PU": 0, "EN": 1, "NU": 2, "END": 3, "EH": 4, "ED": 5, "LU": 6}
for f in sorted(fs, key=lambda f: PRI.get(f["properties"]["tipo"], 9)):
    p = f["properties"]
    if not f["geometry"]:
        continue
    if p["codigo"]:
        porcod.setdefault(p["codigo"][:9], f["geometry"]["coordinates"])
    if p["codigo_ine"]:
        pornome[(FUSIONS.get(p["codigo_ine"], p["codigo_ine"]), sen(sen_artigo(sen(p["nome"]))))].append(f["geometry"]["coordinates"])
LAT0 = 42.75
KX = math.cos(math.radians(LAT0))
X0, Y1 = -9.31, 43.80
ESC = 1000 / ((-6.73 - X0) * KX)          # ~1000 unidades de ancho
proj = lambda lon, lat: (round((lon - X0) * KX * ESC, 1), round((Y1 - lat) * ESC, 1))
modo = Counter()
for e in ents:
    xy = porcod.get(e["k"])
    if xy:
        modo["código"] += 1
    else:
        c = pornome.get((e["c"], sen(sen_artigo(sen(e["nome"])))))
        if c and len(c) == 1:
            xy = c[0]
            modo["nome"] += 1
        else:
            modo["sen punto"] += 1
    e["xy"] = proj(*xy) if xy else None
print("coordenadas:", dict(modo))

# --- 4. Concellos: nomes e polígonos simplificados (Douglas-Peucker, sen dependencias)
def dp(pts, tol):
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy) or 1e-9
    i, dm = 0, -1
    for j in range(1, len(pts) - 1):
        d = abs(dy * (pts[j][0] - a[0]) - dx * (pts[j][1] - a[1])) / n
        if d > dm:
            i, dm = j, d
    if dm <= tol:
        return [a, b]
    return dp(pts[:i + 1], tol)[:-1] + dp(pts[i:], tol)


def anel(r, tol):
    """Simplifica un anel pechado: pártese no punto máis afastado do primeiro."""
    m = max(range(len(r)), key=lambda j: (r[j][0] - r[0][0]) ** 2 + (r[j][1] - r[0][1]) ** 2)
    return dp(r[:m + 1], tol)[:-1] + dp(r[m:], tol)


def area(r):
    return abs(sum(r[i][0] * r[i - 1][1] - r[i - 1][0] * r[i][1] for i in range(len(r)))) / 2


cg = json.loads((GA / "concellos-parroquias/data.geojson").read_text(encoding="utf-8"))["features"]
conc = {}
for f in cg:
    p = f["properties"]
    if p["nivel"] != "concello":
        continue
    g = f["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    aneis = []
    for pol in polys:
        r = [proj(x, y) for x, y in pol[0]]
        s = anel(r, 1.2)
        if len(s) >= 4 and area(s) > 6:
            aneis.append([[round(x), round(y)] for x, y in s[:-1]])
    conc[p["codigo_ine"]] = {"n": p["nome"], "pr": p["provincia"], "pol": aneis}
B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
enc2 = lambda v: B64[v // 64] + B64[v % 64]                       # 0..4095


def cod_aneis(aneis):
    """Polígonos en texto: cada anel empeza en x,y absolutos (2+2 caracteres) e segue con saltos
    dx,dy dun carácter cada un (-32..31); «~» marca un punto absoluto; os aneis sepáranse cun espazo."""
    out = []
    for r in aneis:
        s, (px, py) = enc2(r[0][0]) + enc2(r[0][1]), r[0]
        for x, y in r[1:]:
            dx, dy = x - px, y - py
            s += B64[dx + 32] + B64[dy + 32] if -32 <= dx < 32 and -32 <= dy < 32 else "~" + enc2(x) + enc2(y)
            px, py = x, y
        out.append(s)
    return " ".join(out)


ids = sorted(conc, key=lambda c: sen(conc[c]["n"]))
ci = {c: i for i, c in enumerate(ids)}
assert len(ids) == 313, len(ids)

# --- 5. Saída compacta
# raíces con 2+ entidades; para cada unha: nome bonito, total, variantes e puntos agrupados por concello
cont = Counter(e["r"] for e in ents)
roots = [r for r, n in cont.most_common() if n >= 2]
print("raíces con 2+ entidades:", len(roots), "· únicas:", sum(1 for n in cont.values() if n == 1))
enc3 = lambda v: B64[v // 4096] + B64[v // 64 % 64] + B64[v % 64]  # 0..262143
# Cada punto en 3 caracteres: grella de 2,1 unidades (≈ 0,5 km); «___» = entidade sen punto
pt = lambda e: enc3(round(e["xy"][0] / 2.1) * 512 + round(e["xy"][1] / 2.1)) if e["xy"] else "___"
por = defaultdict(lambda: defaultdict(list))
for e in ents:
    if cont[e["r"]] >= 2:
        por[e["r"]][e["c"]].append(e)
R = []
for r in roots:
    s = ""
    for c, es in sorted(por[r].items(), key=lambda t: ci[t[0]]):
        for i in range(0, len(es), 63):      # bloque: concello (2) + n.º de entidades (1) + puntos
            b = es[i:i + 63]
            s += enc2(ci[c]) + B64[len(b)] + "".join(pt(e) for e in b)
    vs = [[bonito(v), n] for v, n in var[r].most_common() if v != r][:3]
    R.append([bonito(r), s] + ([vs] if vs else []))
# poboación por raíz (só as 200 primeiras, para a ficha)
pob = Counter()
for e in ents:
    pob[e["r"]] += e["p"]
habitadas = Counter(e["r"] for e in ents if e["p"] > 0)
top = [[bonito(r), cont[r], habitadas[r], pob[r]] for r in roots[:200]]
for t in top[:25]:
    print(f"  {t[0]:16} {t[1]:5} entidades · {t[2]:5} habitadas · {t[3]:7} hab. · variantes {var[[r for r in roots if bonito(r)==t[0]][0]].most_common(3)}")
out = {"ano": 2025, "n": len(ents), "nraices": len(cont), "unicas": sum(1 for n in cont.values() if n == 1),
       "sencoord": modo["sen punto"], "conc": [[conc[c]["n"], conc[c]["pr"][0], cod_aneis(conc[c]["pol"])] for c in ids],
       "nconc": [sum(1 for e in ents if e["c"] == c) for c in ids], "R": R, "top": top}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json", (HERE / "data" / "datos.json").stat().st_size // 1024, "KB")

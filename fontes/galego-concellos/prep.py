#!/usr/bin/env python3
"""Uso do galego en cada concello, Censos de 2001 e 2011 → data/datos.json

Fontes (IGE, «Censo de poboación e vivendas. Coñecemento e uso do galego», banco de datos
municipal, gárdanse en data/raw/):
  táboa 1845, Censo 2001: poboación en vivendas familiares de 5 e máis anos segundo o xénero e o
      uso do galego (sempre / ás veces / nunca), por concello
      https://www.ige.gal/igebdt/igeapi/csv/datos/1845
  táboa 6856, Censo 2011: poboación en vivendas familiares de 5 ou máis anos segundo o uso do
      galego, por concello  https://www.ige.gal/igebdt/igeapi/csv/datos/6856
  notas metodolóxicas: https://www.ige.gal/estatico/pdfs/s3/notasExplicativas/notas_Censo_Galego_2011.pdf
Os concellos fusionados despois (Oza-Cesuras 2013, Cerdedo-Cotobade 2016) súmanse.
O dato de 2011 vén da gran enquisa por mostraxe do censo (207.942 persoas en Galicia), non dun
reconto exhaustivo como en 2001; o IGE suprime as categorías con pouca mostra («nunca» e «ás
veces» en moitos concellos pequenos), pero publica «sempre» e o total en todos.
Polígonos: IET, límites de concellos (galicia-agora/data-out/concellos-parroquias/data.geojson).
"""
import csv
import json
import math
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
GEO = Path("/Users/perezgulin/Proxectos/galicia-agora/data-out/concellos-parroquias/data.geojson")
FUSIONS = {"15026": "15902", "15063": "15902", "36011": "36902", "36012": "36902"}
URL = "https://www.ige.gal/igebdt/igeapi/csv/datos/{}"

RAW.mkdir(parents=True, exist_ok=True)


def ige(t):
    f = RAW / f"ige_{t}.csv"
    if not f.exists():
        f.write_bytes(urlopen(Request(URL.format(t), headers={"User-Agent": "Mozilla/5.0"}), timeout=300).read())
    d = {}
    for x in csv.DictReader(f.open(encoding="latin1")):
        if x.get("Xénero", "Ambos xéneros") != "Ambos xéneros":
            continue
        k = x["CodEspazo"]
        if k in FUSIONS.values():          # a fila do concello novo vén baleira: súmanse os antigos
            continue
        k = FUSIONS.get(k, k)
        v = float(x["DatoN"]) if x["DatoN"].strip() else None
        cat = {"Total": "t", "Sempre": "s", "Ás veces": "a", "Nunca": "n"}[x["Uso do galego"]]
        c = d.setdefault(k, {})
        if x["CodEspazo"] in FUSIONS:      # fusionados: súmanse (se falta un, queda sen dato)
            c[cat] = None if v is None or c.get(cat, 0) is None else c.get(cat, 0) + v
        else:
            c[cat] = v
    return d


d01, d11 = ige(1845), ige(6856)

# --- Polígonos (proxección local, Douglas-Peucker sen dependencias, texto compacto)
LAT0 = 42.75
KX = math.cos(math.radians(LAT0))
X0, Y1 = -9.31, 43.80
ESC = 1000 / ((-6.73 - X0) * KX)
proj = lambda lon, lat: ((lon - X0) * KX * ESC, (Y1 - lat) * ESC)


def dp(pts, tol):
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy) or 1e-9
    i, dm = 0, -1
    for j in range(1, len(pts) - 1):
        dd = abs(dy * (pts[j][0] - a[0]) - dx * (pts[j][1] - a[1])) / n
        if dd > dm:
            i, dm = j, dd
    if dm <= tol:
        return [a, b]
    return dp(pts[:i + 1], tol)[:-1] + dp(pts[i:], tol)


def anel(r, tol):
    m = max(range(len(r)), key=lambda j: (r[j][0] - r[0][0]) ** 2 + (r[j][1] - r[0][1]) ** 2)
    return dp(r[:m + 1], tol)[:-1] + dp(r[m:], tol)


area = lambda r: abs(sum(r[i][0] * r[i - 1][1] - r[i - 1][0] * r[i][1] for i in range(len(r)))) / 2
B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
enc2 = lambda v: B64[v // 64] + B64[v % 64]


def cod_aneis(aneis):
    """Cada anel: x,y absolutos (2+2 caracteres) e logo saltos dx,dy dun carácter (-32..31);
    «~» marca un punto absoluto; os aneis sepáranse cun espazo."""
    out = []
    for r in aneis:
        s, (px, py) = enc2(r[0][0]) + enc2(r[0][1]), r[0]
        for x, y in r[1:]:
            dx, dy = x - px, y - py
            s += B64[dx + 32] + B64[dy + 32] if -32 <= dx < 32 and -32 <= dy < 32 else "~" + enc2(x) + enc2(y)
            px, py = x, y
        out.append(s)
    return " ".join(out)


conc = []
for f in json.loads(GEO.read_text(encoding="utf-8"))["features"]:
    p = f["properties"]
    if p["nivel"] != "concello":
        continue
    g = f["geometry"]
    aneis = []
    for pol in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        s = anel([proj(x, y) for x, y in pol[0]], 1.2)
        if len(s) >= 4 and area(s) > 6:
            aneis.append([[round(x), round(y)] for x, y in s[:-1]])
    k = p["codigo_ine"]
    a, b = d01[k], d11[k]
    conc.append({"id": k, "n": p["nome"], "pr": p["provincia"], "pol": cod_aneis(aneis),
                 "t1": round(a["t"]), "s1": round(a["s"]), "n1": round(a["n"]),
                 "t2": round(b["t"]), "s2": round(b["s"]), **({"n2": round(b["n"])} if b.get("n") is not None else {})})
assert len(conc) == 313
conc.sort(key=lambda c: c["n"])
PROV = {"15": "A Coruña", "27": "Lugo", "32": "Ourense", "36": "Pontevedra"}
agr = {k: {"t1": d01[k]["t"], "s1": d01[k]["s"], "n1": d01[k]["n"], "t2": d11[k]["t"], "s2": d11[k]["s"], "n2": d11[k]["n"]}
       for k in ["12", *PROV]}
g = agr["12"]
print(f"Galicia: sempre {g['s1'] / g['t1']:.1%} (2001) → {g['s2'] / g['t2']:.1%} (2011); nunca {g['n1'] / g['t1']:.1%} → {g['n2'] / g['t2']:.1%}")
for k, n in PROV.items():
    print(f"  {n:11} {agr[k]['s1'] / agr[k]['t1']:.1%} → {agr[k]['s2'] / agr[k]['t2']:.1%}")
o = sorted(conc, key=lambda c: -c["s2"] / c["t2"])
for c in o[:4] + o[-4:]:
    print(f"  {c['n']:24} {c['s1'] / c['t1']:.1%} → {c['s2'] / c['t2']:.1%}")
print("concellos que suben:", sum(c["s2"] / c["t2"] > c["s1"] / c["t1"] for c in conc))
out = {"conc": conc, "agr": {("gal" if k == "12" else PROV[k]): {kk: round(v) for kk, v in x.items()} for k, x in agr.items()}}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json", (HERE / "data" / "datos.json").stat().st_size // 1024, "KB")

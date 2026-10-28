#!/usr/bin/env python3
"""Paro rexistrado por concello (setembro de cada ano, 2012-2026) e taxa sobre a poboación de
15 a 64 anos → data/datos.json

Fontes:
  · SEPE, «Paro registrado y contratos por municipios», un Excel mensual por provincia
    (MUNI_<PROVINCIA>_MMAA.xls). Páxina índice:
    https://www.sepe.es/HomeSepe/que-es-el-sepe/estadisticas/datos-estadisticos/municipios.html
    Lense os de setembro (o mesmo mes todos os anos, para non mesturar a estacionalidade) das catro
    provincias galegas, de 2012 a 2026. Gárdanse en data/raw/.
  · IGE, «Poboación segundo sexo e grupos quinquenais de idade» por concello (Censos de 2011 e
    censos anuais a 1 de xaneiro de 2021-2025, INE), táboa 142:
    https://www.ige.gal/igebdt/selector.jsp?COD=142  CSV: https://www.ige.gal/igebdt/igeapi/csv/datos/142
Taxa = parados rexistrados ÷ poboación de 15 a 64 anos. O IGE non publica idades simples para os
concellos pequenos, así que o denominador é 15-64 e non 16-64 (o paro rexistrado empeza aos 16).
Taxa de 2012: paro de setembro de 2012 sobre a poboación do Censo de 2011 (1/11/2011).
Taxa de 2025: paro de setembro de 2025 sobre a poboación a 1/1/2025. Para os anos intermedios non
hai poboación por idade en todos os concellos, así que a serie móstrase en parados.
Precisa xlrd (pip install xlrd).
"""
import csv
import html
import json
import re
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

import xlrd

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
BASE = "https://www.sepe.es"
UA = {"User-Agent": "Mozilla/5.0"}
ANOS = range(2012, 2027)
PROV = {"A_CORUNA": "15", "LUGO": "27", "OURENSE": "32", "PONTEVEDRA": "36"}
FUS = {"36011": "36902", "36012": "36902", "15026": "15902", "15063": "15902"}


def get(url):
    return urlopen(Request(url, headers=UA), timeout=180).read()


idx = RAW / "sepe_municipios.html"
if not idx.exists():
    idx.write_bytes(get(BASE + "/HomeSepe/que-es-el-sepe/estadisticas/datos-estadisticos/municipios.html"))
paxs = dict(re.findall(r'href="(/HomeSepe/que-es-el-sepe/estadisticas/datos-estadisticos/municipios/(\d{4})/septiembre[^"]*\.html)"',
                       idx.read_text(encoding="utf-8", errors="replace")))
paxs = {a: h for h, a in paxs.items()}
import unicodedata

norm = lambda s: re.sub(r"[^A-Z]", "", unicodedata.normalize("NFKD", s.upper()).encode("ascii", "ignore").decode())
# Os ficheiros antigos (2012-2013) non traen código de concello, só o nome: emparéllanse polo nome
# cos ficheiros novos. Os concellos que logo se fusionaron engádense a man.
NOMES = {norm("COVELO"): "36013", norm("CESURAS"): "15026", norm("OZA DOS RIOS"): "15063", norm("CERDEDO"): "36011", norm("COTOBADE"): "36012"}


def follas(a, pr):
    f = RAW / f"MUNI_{pr}_09{a % 100:02d}.xls"
    if not f.exists():
        t = get(BASE + paxs[str(a)]).decode("utf-8", "replace")
        m = re.search(rf'href="([^"]*MUNI_{pr}_09{a % 100:02d}\.xls)"', t, re.I)
        f.write_bytes(get(BASE + quote(html.unescape(m.group(1)), safe="/:%")))
        print("descargado", f.name)
    b = f.read_bytes()
    if b[28:30] == b"\xff\xff":  # algúns ficheiros do SEPE traen mal a marca de orde de bytes
        b = b[:28] + b"\xfe\xff" + b[30:]
    wb = xlrd.open_workbook(file_contents=b)
    s = next((s for s in wb.sheets() if "PARO" in s.name.upper()), wb.sheet_by_index(0))
    return [s.row_values(i) for i in range(s.nrows)]


def valor(v):
    if isinstance(v, str):
        if not v.strip():  # fila baleira (p.ex. Oza-Cesuras en 2014, que vén nos concellos vellos)
            return None
        if "<" in v:  # «<5»: o SEPE oculta os valores pequenos; no total do concello non debería pasar
            raise ValueError(f"total oculto: {v}")
    return int(v)


leidos = {(a, pr): follas(a, pr) for a in ANOS for pr in PROV}
for rows in leidos.values():
    for r in rows:
        cod = r[0] if isinstance(r[0], float) and 1000 < r[0] < 100000 else None
        if cod is not None and isinstance(r[r.index(cod) + 1], str):
            NOMES.setdefault(norm(r[r.index(cod) + 1]), f"{int(cod):05d}")
paro, sen = {}, set()
for (a, pr), rows in leidos.items():
    cp = PROV[pr]
    con_cod = any(isinstance(r[0], float) and 1000 < r[0] < 100000 for r in rows)  # se hai códigos, só se len esas filas
    for r in rows:
        cod = r[0] if isinstance(r[0], float) and 1000 < r[0] < 100000 else None
        if cod is not None:
            k, v = f"{int(cod):05d}", valor(r[r.index(cod) + 2])
        elif not con_cod and isinstance(r[1], str) and r[1].strip() and isinstance(r[2], float) \
                and not (r[1].strip().endswith(".") and norm(r[1]) in ("ACORUNA", "LUGO", "OURENSE", "PONTEVEDRA")):  # total provincial
            k = NOMES.get(norm(r[1]))
            if not k:
                sen.add((a, r[1]))
                continue
            v = valor(r[2])
        else:
            continue
        if k[:2] != cp or v is None:
            continue
        k = FUS.get(k, k)
        dk = paro.setdefault(k, {})
        dk[a] = dk.get(a, 0) + v
print("filas sen emparellar:", sorted(sen)[:20])
print(len(paro), "concellos con paro")

f = RAW / "ige_142.csv"
if not f.exists():
    f.write_bytes(get("https://www.ige.gal/igebdt/igeapi/csv/datos/142"))
G15 = {"15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64"}
pob, nomes = {}, {}
for r in csv.DictReader(f.open(encoding="latin-1")):
    if r["Sexo"] != "Total" or r["CodTempo"] not in ("2011", "2025") or not r["DatoN"]:
        continue
    k = r["CodEspazo"]
    if len(k) == 5 or k in ("12", "15", "27", "32", "36"):
        if r["Grupos de idade"] in G15:
            kk = FUS.get(k, k)
            pob.setdefault(kk, {}).setdefault(r["CodTempo"], 0)
            pob[kk][r["CodTempo"]] += int(float(r["DatoN"]))
        if r["Grupos de idade"] == "Total":
            nomes[k] = r["Espazo"].split(" ", 1)[1]


def bonito(n):
    if ", " in n:
        a, b = n.rsplit(", ", 1)
        if b in ("A", "O", "As", "Os"):
            return f"{b} {a}"
    return n.replace("Cerdedo Cotobade", "Cerdedo-Cotobade")


PN = {"15": "A Coruña", "27": "Lugo", "32": "Ourense", "36": "Pontevedra"}
conc = []
for k in sorted(paro):
    if k not in pob:
        continue
    conc.append({"id": k, "n": bonito(nomes[k]), "pr": PN[k[:2]], "s": [paro[k].get(a) for a in ANOS],
                 "p11": pob[k]["2011"], "p25": pob[k]["2025"]})
assert len(conc) == 313, len(conc)
print("ocos:", [(c["n"], a) for c in conc for a, v in zip(ANOS, c["s"]) if v is None])
gal = {"s": [sum(c["s"][i] for c in conc) for i in range(len(ANOS))], "p11": pob["12"]["2011"], "p25": pob["12"]["2025"]}
print("Galicia parados:", dict(zip(ANOS, gal["s"])))
print(f"taxa 2012 {gal['s'][0] / gal['p11']:.1%} → 2025 {gal['s'][13] / gal['p25']:.1%}")
tx = lambda c: c["s"][13] / c["p25"]
for c in sorted(conc, key=tx)[-6:] + sorted(conc, key=tx)[:6]:
    print(f"  {c['n']:24} {c['s'][0] / c['p11']:.1%} → {tx(c):.1%}")
out = {"anos": list(ANOS), "conc": conc, "gal": gal}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json")

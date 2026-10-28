#!/usr/bin/env python3
"""Persoas afiliadas á Seguridade Social por cada pensionista, concello a concello → data/datos.json

Fontes (IGE, as dúas por concello de residencia, cruzando os ficheiros da Seguridade Social co
Padrón):
  · Pensionistas: IGE, «Pensións da Seguridade Social por concello de residencia da persoa
    pensionista», titulares de pensións contributivas do INSS e do ISM a 31 de decembro, 2011-2024
    (número, importe medio e mediana). Táboa 6560:
    https://www.ige.gal/igebdt/selector.jsp?COD=6560&paxina=001&c=0205023
    CSV: https://www.ige.gal/igebdt/igeapi/csv/datos/6560
  · Afiliados: IGE, «Afiliación á Seguridade Social segundo o concello de residencia», persoas
    afiliadas en alta laboral (unha persoa conta unha vez aínda que teña varias afiliacións), datos
    mensuais dende xaneiro de 2024. Táboa 11311:
    https://www.ige.gal/igebdt/selector.jsp?c=0204033001&COD=11311
    CSV: https://www.ige.gal/igebdt/igeapi/csv/datos/11311
Úsase decembro de 2024 dos afiliados para cadrar coa data dos pensionistas (31/12/2024).
CSV gardados en data/raw/ (codificación latin-1).
"""
import csv
import json
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
URL = "https://www.ige.gal/igebdt/igeapi/csv/datos/{}"
ANO, MES = "2024", "202412"


def le(t):
    f = RAW / f"ige_{t}.csv"
    if not f.exists():
        f.write_bytes(urlopen(Request(URL.format(t), headers={"User-Agent": "Mozilla/5.0"}), timeout=600).read())
    return csv.DictReader(f.open(encoding="latin-1"))


nome = lambda e: e.split(" ", 1)[1]
pen, imp, afi, nomes = {}, {}, {}, {}
for r in le(6560):
    if r["CodTempo"] == ANO and r["Sexo"] == "Total" and r["DatoN"]:
        k = r["CodEspazo"]
        if r["Variable"] == "Número":
            pen[k] = int(float(r["DatoN"]))
        elif r["Variable"] == "Importe medio":
            imp[k] = float(r["DatoN"])
        nomes[k] = nome(r["Espazo"])
for r in le(11311):
    if r["CodTempo"] == MES and r["Sexo"] == "Total" and r["Idade"] == "Total" and r["DatoN"]:
        afi[r["CodEspazo"]] = int(float(r["DatoN"]))


def bonito(n):
    """«Coruña, A» → «A Coruña»."""
    if ", " in n:
        a, b = n.rsplit(", ", 1)
        if b in ("A", "O", "As", "Os"):
            return f"{b} {a}"
    return n.replace("Cerdedo Cotobade", "Cerdedo-Cotobade")


PROV = {"15": "A Coruña", "27": "Lugo", "32": "Ourense", "36": "Pontevedra"}
conc = []
for k in sorted(pen):
    if len(k) != 5 or k not in afi:
        continue
    conc.append({"id": k, "n": bonito(nomes[k]), "pr": PROV[k[:2]], "pe": pen[k], "af": afi[k], "im": round(imp[k])})
agr = {("Galicia" if k == "12" else PROV[k]): {"pe": pen[k], "af": afi[k], "im": round(imp[k])} for k in ("12", "15", "27", "32", "36")}
print(len(conc), "concellos")
assert len(conc) == 313
print("Galicia", agr["Galicia"], f"{agr['Galicia']['af'] / agr['Galicia']['pe']:.2f} afiliados por pensionista")
ra = lambda c: c["af"] / c["pe"]
for c in sorted(conc, key=ra)[:6] + sorted(conc, key=ra)[-6:]:
    print(f"  {c['n']:24} {ra(c):.2f}  ({c['af']} / {c['pe']})")
print("concellos con máis pensionistas ca afiliados:", sum(1 for c in conc if ra(c) < 1))
out = {"ano": int(ANO), "conc": conc, "agr": agr}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json")

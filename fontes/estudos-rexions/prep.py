#!/usr/bin/env python3
"""Abandono escolar temperán e mocidade con estudos superiores por rexión NUTS 2 da UE → data/datos.json

Fontes: Eurostat, Enquisa de Poboación Activa da UE (LFS), API JSON-stat:
  · edat_lfse_16 «Early leavers from education and training by sex and NUTS 2 region»: % de
    persoas de 18-24 anos que como moito teñen a ESO (ISCED 0-2) e non estudan nin se forman.
    https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/edat_lfse_16?sex=T&lang=EN
  · edat_lfse_04 «Population aged 25-34 by educational attainment level, sex and NUTS 2 region»,
    nivel ED5-8 (estudos superiores: ciclos superiores de FP, grao, mestrado, doutoramento).
    https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/edat_lfse_04?sex=T&age=Y25-34&isced11=ED5-8&lang=EN
  Fichas: https://ec.europa.eu/eurostat/databrowser/view/edat_lfse_16/default/table
          https://ec.europa.eu/eurostat/databrowser/view/edat_lfse_04/default/table
Rexións NUTS 2 dos 27 estados da UE (sen «Extra-Regio»), serie dende 2008. Gárdase a marca «u»
(fiabilidade baixa pola mostra pequena) de cada valor. Respostas gardadas en data/raw/.
"""
import json
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
B = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
URLS = {"esl": B + "edat_lfse_16?sex=T&lang=EN",
        "ter": B + "edat_lfse_04?sex=T&age=Y25-34&isced11=ED5-8&lang=EN"}
A0 = 2008
EU = {"AT": "Austria", "BE": "Bélxica", "BG": "Bulgaria", "CY": "Chipre", "CZ": "Chequia", "DE": "Alemaña",
      "DK": "Dinamarca", "EE": "Estonia", "EL": "Grecia", "ES": "España", "FI": "Finlandia", "FR": "Francia",
      "HR": "Croacia", "HU": "Hungría", "IE": "Irlanda", "IT": "Italia", "LT": "Lituania", "LU": "Luxemburgo",
      "LV": "Letonia", "MT": "Malta", "NL": "Países Baixos", "PL": "Polonia", "PT": "Portugal", "RO": "Romanía",
      "SE": "Suecia", "SI": "Eslovenia", "SK": "Eslovaquia"}
ES = {"ES11": "Galicia", "ES12": "Asturias", "ES13": "Cantabria", "ES21": "País Vasco", "ES22": "Navarra",
      "ES23": "A Rioxa", "ES24": "Aragón", "ES30": "Madrid", "ES41": "Castela e León", "ES42": "Castela-A Mancha",
      "ES43": "Estremadura", "ES51": "Cataluña", "ES52": "C. Valenciana", "ES53": "Illes Balears",
      "ES61": "Andalucía", "ES62": "Murcia", "ES63": "Ceuta", "ES64": "Melilla", "ES70": "Canarias"}

RAW.mkdir(parents=True, exist_ok=True)
D = {}
for k, u in URLS.items():
    f = RAW / f"{k}.json"
    if not f.exists():
        f.write_bytes(urlopen(Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=180).read())
    D[k] = json.loads(f.read_text(encoding="utf-8"))


def serie(k, g, anos):
    d = D[k]
    gi, ti = d["dimension"]["geo"]["category"]["index"], d["dimension"]["time"]["category"]["index"]
    T, st = len(ti), d.get("status", {})
    if g not in gi:
        return [None] * len(anos), [""] * len(anos)
    ix = [str(gi[g] * T + ti[str(a)]) if str(a) in ti else None for a in anos]
    return [d["value"].get(i) if i else None for i in ix], [("u" if "u" in st.get(i, "") else "") if i else "" for i in ix]


ult = min(max(int(t) for t in D[k]["dimension"]["time"]["category"]["index"]) for k in D)
anos = list(range(A0, ult + 1))
lab = D["ter"]["dimension"]["geo"]["category"]["label"] | D["esl"]["dimension"]["geo"]["category"]["label"]
geos = set(D["esl"]["dimension"]["geo"]["category"]["index"]) | set(D["ter"]["dimension"]["geo"]["category"]["index"])
rex = []
for g in sorted(geos):
    if len(g) != 4 or g[:2] not in EU or g.endswith("ZZ"):
        continue
    e, eu = serie("esl", g, anos)
    t, tu = serie("ter", g, anos)
    if e[-1] is None or t[-1] is None:
        continue
    rex.append({"c": g, "n": ES.get(g, lab[g]), "p": EU[g[:2]], "e": e, "t": t,
                "u": ("e" if eu[-1] else "") + ("t" if tu[-1] else "")})
out = {"anos": anos, "rex": rex,
       "ue": {"e": serie("esl", "EU27_2020", anos)[0], "t": serie("ter", "EU27_2020", anos)[0]},
       "es": {"e": serie("esl", "ES", anos)[0], "t": serie("ter", "ES", anos)[0]},
       "actualizado": max(D[k].get("updated", "")[:10] for k in D)}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
g = next(r for r in rex if r["c"] == "ES11")
print(len(rex), "rexións con ambos datos en", ult)
print("Galicia", list(zip(anos, g["e"], g["t"])))
print("UE", out["ue"]["e"][-1], out["ue"]["t"][-1], "España", out["es"]["e"][-1], out["es"]["t"][-1])

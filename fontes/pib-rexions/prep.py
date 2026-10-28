#!/usr/bin/env python3
"""PIB por habitante en PPS (% da media UE-27) das rexións NUTS 2 da UE, 2000-último ano → data/datos.json

Fonte: Eurostat, «Gross domestic product (GDP) at current market prices by NUTS 2 region»
(nama_10r_2gdp), unidade PPS_HAB_EU27_2020 (PPS por habitante en % da media da UE-27), API JSON-stat:
  https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nama_10r_2gdp?unit=PPS_HAB_EU27_2020&lang=EN
  Ficha: https://ec.europa.eu/eurostat/databrowser/view/nama_10r_2gdp/default/table
Collemos as rexións NUTS 2 dos 27 estados da UE (sen as «Extra-Regio» ZZ) que teñen dato en TODOS
os anos, para que o posto se calcule sempre sobre o mesmo conxunto. Quedan fóra Bélxica (sen dato
2000-2002), Romanía (sen dato 2002-2011) e Mayotte (sen dato ata 2014). O posto 1 é o PIB por
habitante máis alto. Resposta gardada en data/raw/.
"""
import json
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
URL = ("https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nama_10r_2gdp"
       "?unit=PPS_HAB_EU27_2020&lang=EN")
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
f = RAW / "nama_10r_2gdp.json"
if not f.exists():
    f.write_bytes(urlopen(Request(URL, headers={"User-Agent": "Mozilla/5.0"}), timeout=180).read())
d = json.loads(f.read_text(encoding="utf-8"))
gi = d["dimension"]["geo"]["category"]["index"]
lab = d["dimension"]["geo"]["category"]["label"]
ti = d["dimension"]["time"]["category"]["index"]
anos = sorted(ti, key=int)
T = len(ti)
st = d.get("status", {})
val = lambda g, t: d["value"].get(str(gi[g] * T + ti[t]))
prov = [t for t in anos if st.get(str(gi["ES11"] * T + ti[t])) == "p"]

cands = [g for g in gi if len(g) == 4 and g[:2] in EU and not g.endswith("ZZ")]
rex = [g for g in cands if all(val(g, t) is not None for t in anos)]
fora = sorted({EU[g[:2]] if g[:2] != "FR" else "Mayotte" for g in cands if g not in rex})
print(f"{len(rex)} rexións con serie completa {anos[0]}-{anos[-1]}; fóra: {fora}")

# Posto de cada rexión en cada ano (1 = maior); empates co mesmo posto
postos = {g: [] for g in rex}
for t in anos:
    vs = {g: val(g, t) for g in rex}
    for g in rex:
        postos[g].append(1 + sum(1 for h in rex if vs[h] > vs[g]))

out = {
    "anos": [int(a) for a in anos],
    "prov": [int(a) for a in prov],
    "n": len(rex),
    "ue": [val("EU27_2020", t) for t in anos],
    "es": [val("ES", t) for t in anos],
    "fora": fora,
    "actualizado": d.get("updated", "")[:10],
    "rex": [{"c": g, "n": ES.get(g, lab[g]), "p": EU[g[:2]], "v": [val(g, t) for t in anos], "r": postos[g]}
            for g in sorted(rex, key=lambda g: postos[g][-1])],
}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
gal = next(r for r in out["rex"] if r["c"] == "ES11")
print("Galicia:", list(zip(out["anos"], gal["v"], gal["r"])))

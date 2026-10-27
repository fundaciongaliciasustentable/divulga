#!/usr/bin/env python3
"""Xeración eléctrica por tecnoloxía e demanda de Galicia, 2011-2025 → data/datos.json

Fonte: REData, API de Red Eléctrica (apidatos.ree.es), sistema eléctrico de Galicia (geo_id 17),
unha petición por ano e indicador, gardada en data/ree/ (descárgase se falta):
  /es/datos/generacion/estructura-generacion   xeración por tecnoloxía (MWh)
  /es/datos/demanda/evolucion                  demanda (MWh)
"""
import json
from pathlib import Path
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "ree"
ANOS = range(2011, 2026)
URL = ("https://apidatos.ree.es/es/datos/{ep}?start_date={y}-01-01T00:00&end_date={y}-12-31T23:59"
       "&time_trunc=year&geo_trunc=electric_system&geo_limit=ccaa&geo_ids=17")
EP = {"gen": "generacion/estructura-generacion", "dem": "demanda/evolucion"}
# Agrupación das tecnoloxías de REE
GRUPO = {"Hidráulica": "hid", "Eólica": "eol", "Solar fotovoltaica": "ren", "Otras renovables": "ren",
         "Residuos renovables": "ren", "Cogeneración": "cog", "Residuos no renovables": "cog",
         "Fuel + Gas": "cog", "Ciclo combinado": "cc", "Carbón": "car"}

RAW.mkdir(parents=True, exist_ok=True)
out = []
for y in ANOS:
    fila = {"y": y, "hid": 0, "eol": 0, "ren": 0, "cog": 0, "cc": 0, "car": 0}
    for k, ep in EP.items():
        f = RAW / f"{k}_{y}.json"
        if not f.exists() or "errors" in json.loads(f.read_text()):
            f.write_bytes(urlopen(URL.format(ep=ep, y=y), timeout=60).read())
        d = json.loads(f.read_text())
        assert "errors" not in d, (y, k, d)
        for x in d["included"]:
            t, v = x["attributes"]["title"], sum(z["value"] for z in x["attributes"]["values"]) / 1e3  # GWh
            if k == "dem" and t == "Demanda":
                fila["dem"] = round(v)
            elif k == "gen" and t in GRUPO:
                fila[GRUPO[t]] += v
            elif k == "gen" and t == "Generación total":
                fila["tot"] = round(v)
    for g in ("hid", "eol", "ren", "cog", "cc", "car"):
        fila[g] = round(fila[g])
    assert abs(sum(fila[g] for g in ("hid", "eol", "ren", "cog", "cc", "car")) - fila["tot"]) < 10, fila
    out.append(fila)
    r = fila["hid"] + fila["eol"] + fila["ren"]
    print(y, f"xera {fila['tot']:>6} GWh · consome {fila['dem']:>6} · sobra {fila['tot'] - fila['dem']:>6}"
             f" ({(fila['tot'] - fila['dem']) / fila['tot']:.0%}) · renovable {r / fila['tot']:.0%} · carbón {fila['car']}")
(HERE / "data" / "datos.json").write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json")

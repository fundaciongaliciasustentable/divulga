#!/usr/bin/env python3
"""Descarga do Inventario Forestal Continuo de Galicia (INVEGA, Xunta) a superficie de cada
cobertura por concello e ano → data/raw/<concello>.json

Fonte: capa de recintos SIGPAC con coberturas (InvegaRecintos), servizo ArcGIS do IDEG.
Cada recinto ten a superficie útil (SUTIL) e a de cada clase (S01, S02…) en m², cunha versión
por ano (ADM_FECINI). Pídese ao servidor a suma por ano para cada concello.
"""
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
URL = "https://ideg.xunta.gal/servizos-c05/rest/services/INVEGA/InvegaRecintos/MapServer/0/query"
CONCELLOS = Path("/Users/perezgulin/Proxectos/galicia-agora/data-out/concellos-parroquias/data.geojson")
CAMPOS = ["SUTIL", "S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09", "S10", "S11", "S12",
          "S41", "S42", "S43", "S51", "S52", "S53", "S111", "S112", "S113", "S121", "S122", "S123"]


def baixar(c):
    out = RAW / f"{c}.json"
    if out.exists():
        return c, "xa estaba"
    st = [{"statisticType": "sum", "onStatisticField": f, "outStatisticFieldName": f.lower()} for f in CAMPOS]
    st.append({"statisticType": "count", "onStatisticField": "OBJECTID", "outStatisticFieldName": "n"})
    body = urlencode({"where": f"CONCELLO='{c}'", "outStatistics": json.dumps(st),
                      "groupByFieldsForStatistics": "ADM_FECINI", "f": "json"}).encode()
    for intento in range(4):
        try:
            d = json.loads(urlopen(Request(URL, body, {"User-Agent": "Mozilla/5.0"}), timeout=400).read())
            if "features" in d:
                out.write_text(json.dumps([f["attributes"] for f in d["features"]]))
                return c, len(d["features"])
        except Exception as e:  # noqa: BLE001
            err = e
        time.sleep(10 * (intento + 1))
    return c, f"erro {err if 'err' in dir() else d}"


RAW.mkdir(parents=True, exist_ok=True)
cods = sorted({f["properties"]["codigo_ine"] for f in json.loads(CONCELLOS.read_text())["features"]
               if f["properties"]["nivel"] == "concello"})
with ThreadPoolExecutor(6) as ex:
    for i, (c, r) in enumerate(ex.map(baixar, cods), 1):
        print(i, c, r, flush=True)

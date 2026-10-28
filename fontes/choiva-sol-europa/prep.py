#!/usr/bin/env python3
"""Choiva anual, días de choiva e horas de sol: cidades galegas fronte a Europa → data/datos.json

Fontes (normais climatolóxicas oficiais 1991-2020):
  OMM, «WMO Climate Normals 1991-2020», arquivados por NOAA NCEI (accesión 0253808), ficheiros
  compostos dos parámetros principais, enviados por cada servizo meteorolóxico nacional (AEMET para
  España, Met Office, Météo-France, DWD, KNMI, MET Norway, Met Éireann…):
    https://www.ncei.noaa.gov/products/wmo-climate-normals
    https://www.ncei.noaa.gov/data/oceans/archive/arc0216/0253808/1.1/data/0-data/data-composite-primary-parameters/
      wmo_normals_9120_PRCP.csv  precipitación total (mm)
      wmo_normals_9120_DP01.csv  días con precipitación ≥ 1 mm
      wmo_normals_9120_TSUN.csv  horas de sol
  Ficha por estación de Berlín-Tempelhof, para comprobar os días de choiva do DWD:
    https://www.ncei.noaa.gov/data/oceans/archive/arc0216/0253808/1.1/data/0-data/Region-6-WMO-Normals-9120/Germany/CSV/Berlin-Tempelhof_10384.csv
  Portugal non enviou as súas normais á OMM; para Lisboa e Porto úsanse as fichas 1991-2020 do IPMA
  (que non inclúen horas de sol):
    https://www.ipma.pt/pt/oclima/normais.clima/1991-2020/normalclimate9120.jsp
    https://www.ipma.pt/opencms/bin/file.data/climate-normal/cn_91-20_LISBOA_GEOFISICO.pdf
    https://www.ipma.pt/opencms/bin/file.data/climate-normal/cn_91-20_PORTO_PEDRAS_RUBRAS.pdf

Precisa pypdf (python3 -m pip install pypdf).
"""
import csv
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

import pypdf

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0"}
WMO = "https://www.ncei.noaa.gov/data/oceans/archive/arc0216/0253808/1.1/data/0-data/data-composite-primary-parameters/"
IPMA = "https://www.ipma.pt/opencms/bin/file.data/climate-normal/"

# nome en galego, grupo (g = Galicia, e = resto de España, u = Europa), país (código), estación OMM
CIDADES = [
    ("A Coruña", "g", "ES", "ACORUNA"),
    ("Santiago", "g", "ES", "SANTIAGODECOMPOSTELALABACOLLA"),
    ("Vigo", "g", "ES", "VIGOPEINADOR"),
    ("Pontevedra", "g", "ES", "PONTEVEDRA"),
    ("Lugo", "g", "ES", "LUGOROZAS"),
    ("Ourense", "g", "ES", "OURENSE"),
    ("Oviedo", "e", "ES", "OVIEDO"),
    ("Bilbao", "e", "ES", "BILBAOAEROPUERTO"),
    ("Madrid", "e", "ES", "MADRIDBARAJAS"),
    ("Barcelona", "e", "ES", "BARCELONAAEROPUERTO"),
    ("Sevilla", "e", "ES", "SEVILLASANPABLO"),
    ("Londres", "u", "GB", "Heathrow"),
    ("Dublín", "u", "IE", "CasementAerodrome"),
    ("Cork", "u", "IE", "CorkAirport"),
    ("Bruxelas", "u", "BE", "UCCLE"),
    ("París", "u", "FR", "PARIS_MONTSOURIS"),
    ("Brest", "u", "FR", "BREST_GUIPAVAS"),
    ("Bordeos", "u", "FR", "BORDEAUX_MERIGNAC"),
    ("Ámsterdam", "u", "NL", "AmsterdamSchipholAp"),
    ("Berlín", "u", "DE", "Berlin-Tempelhof"),
    ("Hamburgo", "u", "DE", "Hamburg-Fuhlsbuettel"),
    ("Múnic", "u", "DE", "Muenchen-Stadt"),
    ("Zúric", "u", "CH", "ZuerichFluntern"),
    ("Xenebra", "u", "CH", "GeneveCointrin"),
    ("Viena", "u", "AT", "Wien_Hohe_Warte"),
    ("Praga", "u", "CZ", "PrahaRuzyne"),
    ("Milán", "u", "IT", "MilanoLinate"),
    ("Roma", "u", "IT", "RomaCiampino"),
    ("Bergen", "u", "NO", "BERGEN_FLORIDA"),
    ("Oslo", "u", "NO", "OSLO_BLINDERN"),
    ("Copenhague", "u", "DK", "LANDBOHYJSKOLEN"),
    ("Estocolmo", "u", "SE", "Stockholm_Observatoriekullen"),
    ("Helsinki", "u", "FI", "HelsinkiKaisaniemi"),
    ("Reikiavik", "u", "IS", "Reykjavik"),
    ("Varsovia", "u", "PL", "WarszawaOkecie"),
]
PT = [("Lisboa", "u", "PT", "LISBOA_GEOFISICO", "Lisboa / Instituto Geofísico"),
      ("Porto", "u", "PT", "PORTO_PEDRAS_RUBRAS", "Porto / Pedras Rubras")]


def get(url):
    return urlopen(Request(url, headers=UA), timeout=300).read()


def wmo(el):
    f = RAW / f"{el}.csv"
    if not f.exists():
        f.write_bytes(get(WMO + f"wmo_normals_9120_{el}.csv"))
    d = {}
    with f.open(encoding="utf-8", errors="replace") as fh:
        for r in csv.reader(fh):
            if len(r) < 22 or not r[0].strip().isdigit():
                continue
            v = float(r[-1])
            d[r[8].strip()] = {"v": None if v < -90 else v, "lat": float(r[4]), "lon": float(r[5]), "alt": float(r[6]),
                               "id": r[2].strip()}
    return d


P, D, S = wmo("PRCP"), wmo("DP01"), wmo("TSUN")
out = []
for nome, g, pais, est in CIDADES:
    p, d = P[est], D[est]
    s = S.get(est, {}).get("v")
    assert p["v"] and d["v"], est
    # O DWD enviou como «días con ≥ 1 mm» o reconto de días con ≥ 0,1 mm (nas fichas por estación,
    # Berlin-Tempelhof: parámetro 2 = parámetro 16 = 163,9 días), así que os días de Alemaña non se usan.
    dias = None if pais == "DE" else d["v"]
    out.append({"n": nome, "g": g, "p": pais, "est": est, "mm": p["v"], "dias": dias, "sol": s,
                "lat": p["lat"], "alt": p["alt"], "f": "OMM"})
for nome, g, pais, cod, est in PT:
    f = RAW / f"ipma_{cod}.pdf"
    if not f.exists():
        f.write_bytes(get(IPMA + f"cn_91-20_{cod}.pdf"))
    t = "\n".join(pg.extract_text() for pg in pypdf.PdfReader(f).pages)
    mm = float(re.search(r"Prec \[mm\]((?:\s+[\d.]+){13})", t).group(1).split()[-1])
    dias = float(re.search(r"P ≥ 1 mm((?:\s+[\d.]+){13})", t).group(1).split()[-1])
    lat = float(re.search(r"Latitude: ([\d.]+)N", t).group(1))
    alt = float(re.search(r"Altitude: ([\d.]+) m", t).group(1))
    out.append({"n": nome, "g": g, "p": pais, "est": est, "mm": mm, "dias": dias, "sol": None, "lat": lat, "alt": alt,
                "f": "IPMA"})
for o in sorted(out, key=lambda o: -o["mm"]):
    print(f"{o['n']:12s} {o['mm']:7.1f} mm {o['dias']} días  sol {o['sol']}")
(HERE / "data" / "datos.json").write_text(json.dumps({"periodo": "1991-2020", "cidades": out}, ensure_ascii=False,
                                                     separators=(",", ":")), encoding="utf-8")

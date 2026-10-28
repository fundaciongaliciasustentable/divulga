#!/usr/bin/env python3
"""Cobertura de banda larga fixa a ≥100 Mbps e a ≥1 Gbps en cada concello galego → data/datos.json

Fonte: Ministerio para a Transformación Dixital e da Función Pública (SETELECO), «Informe de
cobertura de banda ancha en España 2025» (datos a 30/06/2025):
  https://digital.gob.es/telecomunicaciones-infraestructuras-digitales/areas-interes/banda-ancha/informacion-cobertura/informes-cobertura/informe-cobertura-2025
Os datos por municipio son os que o Ministerio publica nos seus mapas de cobertura agregada
(https://digital.gob.es/telecomunicaciones-infraestructuras-digitales/areas-interes/banda-ancha/informacion-cobertura/mapas-cobertura-agregada),
servizos ArcGIS do propio Ministerio, unha capa por velocidade, en % de fogares cubertos:
  https://services-eu1.arcgis.com/3LqdsBPalJaUFvo1/arcgis/rest/services/cobertura_municipios_2025_hogar_100mbps/FeatureServer/0
  https://services-eu1.arcgis.com/3LqdsBPalJaUFvo1/arcgis/rest/services/cobertura_municipios_2025_hogar_1gbps/FeatureServer/0
  https://services-eu1.arcgis.com/3LqdsBPalJaUFvo1/arcgis/rest/services/cobertura_municipios_2025_hogar_ftth/FeatureServer/0
  e o total de Galicia: .../cobertura_ccaa_2025_hogares/FeatureServer/0
Para comparar, tamén a capa de 2023 a 1 Gbps (.../cobertura_municipios_2023_1gbps), que o Ministerio
mide en % de unidades inmobiliarias e non de fogares: só vai como referencia na táboa.
Respostas JSON gardadas en data/raw/.
"""
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
B = "https://services-eu1.arcgis.com/3LqdsBPalJaUFvo1/arcgis/rest/services/"
CAPAS = {"g100": "cobertura_municipios_2025_hogar_100mbps", "g1": "cobertura_municipios_2025_hogar_1gbps",
         "ftth": "cobertura_municipios_2025_hogar_ftth", "g1_23": "cobertura_municipios_2023_1gbps"}
RAW.mkdir(parents=True, exist_ok=True)


def capa(nome, where):
    f = RAW / f"{nome}.json"
    if not f.exists():
        q = urlencode({"where": where, "outFields": "*", "returnGeometry": "false", "f": "json"})
        f.write_bytes(urlopen(Request(B + nome + "/FeatureServer/0/query?" + q, headers={"User-Agent": "Mozilla/5.0"}), timeout=120).read())
    return [x["attributes"] for x in json.loads(f.read_text(encoding="utf-8"))["features"]]


dat = {}
for k, nome in CAPAS.items():
    for a in capa(nome, "cod_ccaa='12'"):
        dat.setdefault(a["cod_munici"], {})[k] = a["porcentaje"]
        if k == "g1":
            dat[a["cod_munici"]].update(fog=a["hogares_to"], hab=a["habitantes"])
gal = {a["tecnologia"]: a["porcentaje"] for a in capa("cobertura_ccaa_2025_hogares", "COD_CCAA='12'")}
gal = {"g100": gal["100 Mbps velocidad descarga"], "g1": gal["1Gbps velocidad descarga"], "ftth": gal["FTTH"],
       "fog": capa("cobertura_ccaa_2025_hogares", "COD_CCAA='12'")[0]["hogares_to"]}
print("Galicia (Ministerio):", gal)

mc = json.loads((HERE.parent / "monte-concellos" / "data" / "datos.json").read_text(encoding="utf-8"))
conc = []
for c in mc["concellos"]:
    x = dat[c["id"]]
    conc.append({"id": c["id"], "n": c["n"], "pr": c["pr"], "fog": x["fog"], "hab": x["hab"],
                 **{k: round(x[k], 1) for k in CAPAS if x.get(k) is not None}})
assert len(conc) == 313
# comprobación: a media ponderada polos fogares debe dar o total de Galicia do Ministerio
for k in ("g100", "g1"):
    m = sum(c[k] * c["fog"] for c in conc) / sum(c["fog"] for c in conc)
    print(f"  {k}: media ponderada dos concellos {m:.2f} % · Ministerio {gal[k]:.2f} %")
fog_sen100 = sum((100 - c["g100"]) / 100 * c["fog"] for c in conc)
print("fogares sen 100 Mbps:", round(fog_sen100), " concellos con menos do 50 % a 100 Mbps:", sum(c["g100"] < 50 for c in conc))
for c in sorted(conc, key=lambda c: c["g100"])[:10]:
    print(f"  {c['n']:24} 100M {c['g100']:5.1f}  1G {c['g1']:5.1f}  ({c['fog']} fogares)")
(HERE / "data" / "datos.json").write_text(json.dumps({"gal": gal, "conc": conc, "data": "2025-06-30"}, ensure_ascii=False,
                                                     separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json")

#!/usr/bin/env python3
"""Praias galegas con bandeira azul, 2013-2026, e comparación entre comunidades → data/datos.json

Fontes (gárdanse en data/raw/ se faltan):
  xunta_<ano>.csv  Xunta de Galicia, Datos Abertos, «Praias galegas con bandeira azul en <ano>»
        (concello, praia e coordenadas). Un conxunto por ano, 2013-2026:
        https://abertos.xunta.gal/catalogo/cultura-ocio-deporte/-/dataset/0697/praias-galegas-con-bandeira-azul-2026
        (os URL de cada ano están en XUNTA, máis abaixo; listados tamén en datos.gob.es)
  adeac_relacion_2026.pdf  ADEAC, «Relación de playas galardonadas con Bandera Azul 2026-2027»:
        https://www.banderaazul.org/sites/default/files/2026/Rueda-de-prensa-2026/Relaci%C3%B3n%20Playas%20Galardonadas%202026.pdf
  adeac_nota_2026.pdf  ADEAC (Asociación de Educación Ambiental e do Consumidor), nota de prensa
        do 5/5/2026 coas praias galardoadas por comunidade autónoma e a variación sobre 2025:
        https://www.banderaazul.org/sites/default/files/2026/Rueda-de-prensa-2026/ADEAC-Bandera-Azul_Nota-Prensa-2026.pdf
  ine_anuario2008_entorno.pdf  INE, Anuario Estadístico de España 2008, táboa 1.1.3 «Lonxitude da
        costa por provincias» (Instituto Geográfico Nacional; sen illas nas provincias peninsulares):
        https://ine.es/prodyser/pubweb/anuario08/anu08_01entor.pdf
Xeometría: concellos de galicia-agora (data-out/concellos-parroquias/data.geojson), simplificada.
Necesita pypdf e shapely.
"""
import csv
import json
import re
import unicodedata
from pathlib import Path
from urllib.request import Request, urlopen

import pypdf
from shapely.geometry import shape

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
CONCELLOS = Path("/Users/perezgulin/Proxectos/galicia-agora/data-out/concellos-parroquias/data.geojson")
AB = "https://abertos.xunta.gal/catalogo/cultura-ocio-deporte/-/dataset/"
XUNTA = {2013: "0281", 2014: "0316", 2015: "0356", 2016: "0364", 2017: "0380", 2018: "0392", 2019: "0401",
         2020: "0424", 2021: "0438", 2022: "0490", 2023: "0599", 2024: "0654", 2025: "0686", 2026: "0697"}
RELACION = "https://www.banderaazul.org/sites/default/files/2026/Rueda-de-prensa-2026/Relaci%C3%B3n%20Playas%20Galardonadas%202026.pdf"
NOTA = "https://www.banderaazul.org/sites/default/files/2026/Rueda-de-prensa-2026/ADEAC-Bandera-Azul_Nota-Prensa-2026.pdf"
ANUARIO = "https://ine.es/prodyser/pubweb/anuario08/anu08_01entor.pdf"
RAW.mkdir(parents=True, exist_ok=True)


def baixa(nome, url):
    f = RAW / nome
    if not f.exists():
        f.write_bytes(urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=300).read())
        print("descargado", nome)
    return f


def norm(s):
    s = s.strip()
    if ", " in s:
        a, b = s.rsplit(", ", 1)
        if b.lower() in ("a", "o", "as", "os"):
            s = f"{b} {a}"
    s = unicodedata.normalize("NFD", s.lower())
    return re.sub(r"\s+", " ", "".join(ch for ch in s if unicodedata.category(ch) != "Mn").replace("-", " ")).strip()


# Concellos e xeometría
X0, Y1, KX = -9.4, 43.9, 0.7325  # KX = cos(42,9°); unidades: 1/1000 de grao de latitude
pr = lambda lon, lat: [round((lon - X0) * KX * 1000), round((Y1 - lat) * 1000)]
fs = [f for f in json.loads(CONCELLOS.read_text(encoding="utf-8"))["features"] if f["properties"]["nivel"] == "concello"]
conc, por_nome = {}, {}
for f in fs:
    p = f["properties"]
    g = shape(f["geometry"]).buffer(0).simplify(0.0025)
    pol = [[pr(x, y) for x, y in q.exterior.coords] for q in getattr(g, "geoms", [g]) if q.area > 2e-6]
    conc[p["codigo_ine"]] = {"id": p["codigo_ine"], "n": p["nome"], "pr": p["provincia"], "pol": pol}
    por_nome[norm(p["nome"])] = p["codigo_ine"]
# nomes da Xunta (e algún erro de escritura) que non coinciden co da xeometría
ALIAS = {"porto do son": "15071", "pontes, as": "15070", "as pontes": "15070", "cangas": "36008",
         "a pobra do caraminal": "15067", "vilagarcia": "36060", "oza cesuras": "15902", "castro caldelas": "32023"}
# nomes oficiais (INE) onde a xeometría trae outra forma
NOMES = {"15071": "Porto do Son", "36008": "Cangas", "27002": "Alfoz", "27053": "Ribeira de Piquín",
         "32023": "Castro Caldelas", "36007": "Campo Lameiro", "32071": "Riós", "27044": "A Pastoriza", "15902": "Oza-Cesuras"}
for c, n in NOMES.items():
    if c in conc:
        conc[c]["n"] = n


def concello(nome, cod):
    k = norm(nome)
    c = ALIAS.get(k) or por_nome.get(k)
    if not c and cod and cod.strip()[:5] in conc:
        c = cod.strip()[:5]
    return c


# Praias por ano
anos, praias, sen = {}, [], set()
for a, ds in sorted(XUNTA.items()):
    f = baixa(f"xunta_{a}.csv", f"{AB}{ds}/praias-galegas-con-bandeira-azul-{a}/001/descarga-directa-ficheiro.csv")
    # codificación mesturada segundo o ano e ata dentro dunha mesma liña: utf-8 se vale; se non,
    # latin1 cos códigos de cp850 que aparecen nos ficheiros (0xA4 = «ñ», 0xA1 = «í»…)
    CP850 = {0xA4: "ñ", 0xA5: "Ñ", 0xA0: "á", 0x82: "é", 0xA1: "í", 0xA2: "ó", 0xA3: "ú", 0x81: "ü", 0xB5: "Á"}
    def dec(l):
        try:
            return l.decode("utf-8")
        except UnicodeDecodeError:
            return "".join(CP850.get(ch, chr(ch)) for ch in l)
    txt = "\n".join(dec(l) for l in f.read_bytes().lstrip(b"\xef\xbb\xbf").splitlines())
    sep = ";" if txt.count(";") > txt.count(",") else ","
    rows = list(csv.reader(txt.splitlines(), delimiter=sep))
    cab = [norm(h) for h in rows[0]]
    col = lambda *ks: next((i for i, h in enumerate(cab) if any(k in h for k in ks)), None)
    ic, icod, ip, ixy = col("concello"), col("codigo concello"), col("praia"), col("coordenadas")
    lista = []
    for r in rows[1:]:
        if len(r) <= max(ic, ip) or not r[ic].strip() or not r[ip].strip():
            continue
        c = concello(r[ic], r[icod] if icod is not None and len(r) > icod else "")
        if not c:
            sen.add((a, r[ic]))
            continue
        lista.append((c, r[ip].strip(), r[ixy] if ixy is not None and len(r) > ixy else ""))
    anos[a] = lista
    print(a, len(lista), "praias")
    if a == max(XUNTA):
        for c, n, xy in lista:
            m = re.findall(r"-?\d+\.\d+", xy)
            lat, lon = float(m[0]), float(m[1])
            assert 41.8 < lat < 43.9 and -9.4 < lon < -6.7, (n, xy)
            praias.append({"c": c, "n": n, "xy": pr(lon, lat)})
if sen:
    print("AVISO: concellos sen casar", sorted(sen))
ult = max(anos)
serie = [[a, len(v)] for a, v in sorted(anos.items())]
for c in conc.values():
    c["b"] = [sum(1 for x in anos[a] if x[0] == c["id"]) for a in sorted(anos)]

# ADEAC 2026 por comunidade: a relación oficial de praias galardoadas (a nota de prensa dá 151 na
# Comunidade Valenciana e a relación 152; a suma da relación cadra co total de 677)
rel = "\n".join(p.extract_text() for p in pypdf.PdfReader(baixa("adeac_relacion_2026.pdf", RELACION)).pages)
CC = {"ANDALUCÍA": "Andalucía", "PRINCIPADO DE ASTURIAS": "Asturias", "ILLES BALEARS": "Illes Balears", "CANARIAS": "Canarias",
      "CANTABRIA": "Cantabria", "CATALUÑA": "Cataluña", "COMUNITAT VALENCIANA": "Comunidade Valenciana",
      "EXTREMADURA": "Extremadura", "GALICIA": "Galicia", "COMUNIDAD DE MADRID": "Madrid", "REGIÓN DE MURCIA": "Rexión de Murcia",
      "PAÍS VASCO": "País Vasco", "CIUDAD AUTÓNOMA DE CEUTA": "Ceuta", "CIUDAD AUTÓNOMA DE MELILLA": "Melilla"}
ccaa = [{"n": CC[m.group(1).strip()], "b": int(m.group(2)), "m": int(m.group(3))}
        for m in re.finditer(r"([A-ZÁÉÍÓÚÑ ]+) \((\d+) playas? en (\d+) municipios?\)", rel)]
nota = "\n".join(p.extract_text() for p in pypdf.PdfReader(baixa("adeac_nota_2026.pdf", NOTA)).pages)
tot = int(re.search(r"(\d+)\s*para playas en", nota).group(1))
assert len(ccaa) == 14 and sum(c["b"] for c in ccaa) == tot, (ccaa, tot)

# Lonxitude da costa (IGN, vía INE): provincias → comunidades
an = pypdf.PdfReader(baixa("ine_anuario2008_entorno.pdf", ANUARIO))
t = next(p.extract_text() for p in an.pages if "1.1.3. Longitud de la costa por provincias" in p.extract_text())
t = t[t.index("1.1.3. Longitud de la costa por provincias"):]
km = {n.strip(): int(v.replace(".", "")) for n, v in re.findall(r"([A-ZÁÉÍÓÚ][^\d\n]+?)\s+(\d[\d.]*)", t.split("Kilómetros", 1)[1])}
t2 = next(p.extract_text() for p in an.pages if "1.1.2. Longitud de las costas y fronteras" in p.extract_text())
ceuta = int(re.search(r"Límites marítimos Ciudad de Ceuta (\d+)", t2).group(1))
melilla = int(re.search(r"Ciudad de Melilla (\d+)", t2).group(1))
PROVS = {"Galicia": ["Lugo", "Coruña ( A)", "Pontevedra"], "Asturias": ["Asturias"], "Cantabria": ["Cantabria"],
         "País Vasco": ["Guipúzcoa", "Vizcaya"], "Andalucía": ["Huelva", "Cádiz", "Málaga", "Granada", "Almería"],
         "Rexión de Murcia": ["Murcia"], "Comunidade Valenciana": ["Alicante/Alacant", "Valencia/València", "Castellón/Castelló"],
         "Cataluña": ["Tarragona", "Barcelona", "Girona"], "Illes Balears": ["Balears (Illes)"],
         "Canarias": ["Palmas (Las)", "Santa Cruz de Tenerife"]}
for c in ccaa:
    if c["n"] in PROVS:
        c["km"] = sum(km[p] for p in PROVS[c["n"]])
    elif c["n"] == "Ceuta":
        c["km"] = ceuta
    elif c["n"] == "Melilla":
        c["km"] = melilla
    else:
        c["km"] = None  # sen costa (praias fluviais ou de encoro)
kmprov = {"A Coruña": km["Coruña ( A)"], "Lugo": km["Lugo"], "Pontevedra": km["Pontevedra"]}
for c in ccaa:
    print(f"  {c['n']:22} {c['b']:4} · {c['km'] or '-':>5} km", f"· {c['b'] / c['km'] * 100:.1f} /100 km" if c["km"] else "")
gal = next(c for c in ccaa if c["n"] == "Galicia")
assert gal["b"] == len(anos[ult]), (gal["b"], len(anos[ult]))

C = sorted(conc.values(), key=lambda c: c["n"])
for c in sorted(C, key=lambda c: -c["b"][-1])[:8]:
    print(f"  {c['n']:24} {c['b'][-1]} bandeiras")
out = {"anos": sorted(anos), "serie": serie, "praias": praias, "ccaa": ccaa, "kmprov": kmprov, "conc": C}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json", (HERE / "data" / "datos.json").stat().st_size // 1024, "KB")

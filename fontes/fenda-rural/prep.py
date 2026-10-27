#!/usr/bin/env python3
"""Indicadores do Panorama rural-urbano do IGE por grao de urbanización → data/datos.json

Fonte: IGE, Panorama rural-urbano (https://www.ige.gal/web/mostrar_seccion.jsp?codigo=0701),
unha páxina HTML por indicador con táboas para Galicia, as provincias e os subgraos.
Gárdanse en data/pru/ (descárganse se faltan). Clasificación dos concellos: IGE, táboa 8444.

Grao de urbanización (GU 2016, estándar europeo):
  ZDP zona densamente poboada · ZIP zona intermedia · ZPP zona pouco poboada.
As táboas non teñen todas a mesma forma, así que cada indicador ten a súa regra de lectura.
"""
import csv
import html
import json
import re
from collections import Counter
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
PRU = HERE / "data" / "pru"
BASE = "https://www.ige.gal/estatico/html/gl/rural-urbano/{}.html"
Z = ["T", "ZDP", "ZIP", "ZPP"]


def num(s):
    s = s.replace(".", "").replace(",", ".").strip()
    return float(s) if s not in ("", "-", "..") else None


def taboas(nome):
    f = PRU / f"{nome}.html"
    if not f.exists():
        PRU.mkdir(parents=True, exist_ok=True)
        f.write_bytes(urlopen(Request(BASE.format(nome), headers={"User-Agent": "Mozilla/5.0"}), timeout=120).read())
    s = re.sub(r"<script.*?</script>|<style.*?</style>", "", f.read_text(encoding="utf-8", errors="replace"), flags=re.S)
    out = []
    for t in re.findall(r"<table.*?</table>", s, re.S):
        rows = []
        for tr in re.findall(r"<tr.*?</tr>", t, re.S):
            rows.append([html.unescape(re.sub(r"<[^>]+>|\s+", " ", c)).strip() for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", tr, re.S)])
        out.append(rows)
    return out


def fila(rows, etiqueta):
    return next(r for r in rows if r and r[0].strip().lstrip("• ") == etiqueta)


def bloques(rows, etiqueta, anos):
    """Fila con bloques de 4 columnas (Total, ZDP, ZIP, ZPP), un bloque por ano."""
    r = [num(x) for x in fila(rows, etiqueta)[1:]]
    return {a: dict(zip(Z, r[i * 4:i * 4 + 4])) for i, a in enumerate(anos)}


def series(rows, ano_ini, ano_fin):
    """Táboa con anos en columnas e unha fila por zona (Total, ZDP, ZIP, ZPP)."""
    cab = rows[0]
    out = {}
    for a in (ano_ini, ano_fin):
        j = cab.index(str(a))
        out[a] = {z: num(fila(rows, e)[j]) for z, e in zip(Z, ("Total", "ZDP", "ZIP", "ZPP"))}
    return out


def series_longas(rows, ano_ini, ano_fin):
    """Como series, pero coas zonas co nome longo (taxa de pobreza)."""
    cab = rows[0]
    nomes = {"T": "Total", "ZDP": "Zonas densamente poboadas (ZDP)", "ZIP": "Zonas intermedias (ZIP)", "ZPP": "Zonas pouco poboadas (ZPP)"}
    return {a: {z: num(fila(rows, nomes[z])[cab.index(str(a))]) for z in Z} for a in (ano_ini, ano_fin)}


T = {}
def ind(clave, tema, nome, unidade, datos, mellor, nota=""):
    """mellor: 'alto' ou 'baixo' (que valor se considera favorable), ou None se non procede."""
    T[clave] = {"tema": tema, "n": nome, "u": unidade, "d": {str(a): v for a, v in datos.items()}, "mellor": mellor, "nota": nota}


t = taboas("PRU_D_5_Poboacion_estranxeira")
ind("estr", "Poboación", "Poboación estranxeira", "%", bloques(t[0], "Galicia", [2001, 2024]), None)
t = taboas("PRU_D_6_Idade_media")
ind("idade", "Poboación", "Idade media", "anos", bloques(t[0], "Galicia", [2003, 2024]), None)
t = taboas("PRU_D_7_Indice_envellecemento")
ind("envel", "Poboación", "Índice de envellecemento", "maiores de 65 por cada 100 menores de 20", {2024: bloques(t[0], "Galicia", [2024])[2024]}, None)
t = taboas("PRU_D_4_Porcentaxe_poboacion_grandes_grupos_idade")
g = {}
for a, k in ((2001, 0), (2024, 1)):
    r = [num(x) for x in fila(t[k], "Galicia")[1:]]
    g[a] = r
ind("may60", "Poboación", "Poboación de 60 e máis anos", "%", {a: dict(zip(Z, r[2::3])) for a, r in g.items()}, None)
ind("men20", "Poboación", "Poboación menor de 20 anos", "%", {a: dict(zip(Z, r[0::3])) for a, r in g.items()}, None)
t = taboas("PRU_D_8_Taxa_bruta_natalidade")
ind("nat", "Poboación", "Taxa de natalidade", "nacementos por 1.000 hab.", bloques(t[0], "Galicia", [2003, 2023]), None)
t = taboas("PRU_D_9_Indice_sintetico_fecundidade")
ind("isf", "Poboación", "Fillos por muller", "índice sintético de fecundidade", bloques(t[0], "Galicia", [2003, 2023]), None)
t = taboas("PRU_D_10_Idade_media_maternidade")
ind("mat", "Poboación", "Idade media á maternidade", "anos", bloques(t[0], "Galicia", [2008, 2023]), None)
t = taboas("PRU_D_11_Taxa_de_mortalidade")
b = [num(x) for x in fila(t[0], "Galicia")[1:]]
ind("mortb", "Saúde", "Taxa bruta de mortalidade", "defuncións por 1.000 hab.", {2023: dict(zip(Z, b[:4]))}, None)
ind("morte", "Saúde", "Mortalidade estandarizada por idade", "defuncións por 1.000 hab.", {2023: dict(zip(Z, b[4:8]))}, "baixo",
    "Elimina o efecto da idade: compara como se todas as zonas tivesen a mesma estrutura de idades.")
t = taboas("PRU_D_12_Esperanza_de_vida")
ind("evida", "Saúde", "Esperanza de vida ao nacer", "anos", bloques(t[0], "Galicia", [2002, 2022]), "alto")
t = taboas("PRU_S_3_Porcentaxe_de_autonomos")
ind("auton", "Traballo", "Afiliacións por conta propia", "% das afiliacións", {2019: bloques(t[0], "Galicia", [2019])[2019], 2024: bloques(t[1], "Galicia", [2024])[2024]}, None)
t = taboas("PRU_S_2_Afiliacions_a_seguridade_social_Sector")
ind("agri", "Traballo", "Afiliacións na agricultura e pesca", "% das afiliacións",
    {2017: bloques(t[0], "Agricultura e pesca", [2017])[2017], 2024: bloques(t[1], "Agricultura e pesca", [2024])[2024]}, None)
ind("serv", "Traballo", "Afiliacións nos servizos", "% das afiliacións",
    {2017: bloques(t[0], "Servizos", [2017])[2017], 2024: bloques(t[1], "Servizos", [2024])[2024]}, None)
t = taboas("PRU_S_4_Paro_rexistrado_total")
ind("paro", "Traballo", "Paro rexistrado", "persoas en paro por 1.000 hab.", series(t[0], 2014, 2024), "baixo")
t = taboas("PRU_S_5_Paro_rexistrado_menores25")
ind("paro25", "Traballo", "Paro rexistrado de menores de 25 anos", "por 1.000 hab. menores de 25", series(t[0], 2014, 2024), "baixo")
t = taboas("PRU_S_6_Contratos_iniciais")
ind("contr", "Traballo", "Contratos iniciais", "por 1.000 hab.", bloques(t[0], "Galicia", [2014, 2024]), "alto")
t = taboas("PRU_S_8_Rendemento_medio_declarado_no_IRPF")
ind("irpf", "Diñeiro", "Rendemento medio declarado no IRPF", "€ por declaración",
    {2012: bloques(t[0], "Galicia", [2012])[2012], 2022: bloques(t[1], "Galicia", [2022])[2022]}, "alto")
t = taboas("PRU_S_12_Importe_Pensions_contributivas")
ind("pens", "Diñeiro", "Pensión contributiva media", "€ ao mes", {2022: bloques(t[0], "Galicia", [2022])[2022]}, "alto")
t = taboas("PRU_S_11_Pensions_contributivas")
ind("npens", "Diñeiro", "Pensionistas", "por 1.000 hab.", {2022: bloques(t[0], "Galicia", [2022])[2022]}, None)
t = taboas("PRU_S_7_Pensions_non_contributivas")
ind("pnc", "Diñeiro", "Pensións non contributivas", "por 1.000 hab.", bloques(t[0], "Galicia", [2017, 2023]), "baixo")
t = taboas("PRU_S_10_TaxasPob")
ind("pobr", "Diñeiro", "Risco de pobreza ou exclusión social", "% da poboación", series_longas(t[0], 2016, 2023), "baixo")
t = taboas("PRU_E_RDB")
pob, rdb = {}, {}
for r in t[0][1:]:
    if r and r[0] in ("ZDP", "ZIP", "ZPP"):
        pob[r[0]], rdb[r[0]] = num(r[1]), num(r[3])
ind("rdb", "Diñeiro", "Renda dispoñible por persoa", "Galicia = 100", {2022: {"T": 100.0, **{z: round(rdb[z] / pob[z] * 100, 1) for z in pob}}}, "alto",
    "Parte da renda dispoñible bruta de Galicia que vai a cada zona dividida pola súa parte da poboación.")
t = taboas("PRU_E_10_Establecementos_por_1000h")
ind("estab", "Servizos e vivenda", "Establecementos (empresas, comercios…)", "por 1.000 hab.", bloques(t[0], "Galicia", [2017, 2023]), "alto")
t = taboas("PRU_E_11_Establecementos_servizos_por_1000h")
ind("estabs", "Servizos e vivenda", "Establecementos de servizos", "por 1.000 hab.", bloques(t[0], "Galicia", [2017, 2023]), "alto")
t = taboas("PRU_E_13_Bens_hab")
ind("viv", "Servizos e vivenda", "Inmobles residenciais", "por 1.000 hab.", bloques(t[0], "Galicia", [2014, 2023]), None,
    "Casas e pisos do catastro: nas zonas rurais hai moitos máis por veciño, en boa parte baleiros ou de segunda residencia.")
t = taboas("PRU_D_1_Densidade_de_poboacion")
dens = bloques(t[0], "Galicia", [2024])[2024]
t = taboas("PRU_D_2_Cifras_de_poboacion")
rows = t[0]
i24 = next(i for i, r in enumerate(rows) if r and r[0] == "2024")
pob24 = {z: num(fila(rows[i24:], e)[1]) for z, e in zip(Z, ("Total", "ZDP", "ZIP", "ZPP"))}

for k, v in T.items():
    for a, d in v["d"].items():
        assert all(d[z] is not None for z in Z), (k, a, d)
    ult = max(v["d"])
    d = v["d"][ult]
    print(f"{k:7} {ult} T {d['T']:>9} ZDP {d['ZDP']:>9} ZIP {d['ZIP']:>9} ZPP {d['ZPP']:>9}  ZPP/ZDP {d['ZPP'] / d['ZDP']:.2f}")

VELLOS = {"15026", "15063", "36011", "36012"}  # concellos fusionados en Oza-Cesuras e Cerdedo-Cotobade
conc = Counter(x["DatoT"] for x in csv.DictReader((HERE / "data" / "ige_8444.csv").open(encoding="latin1"))
               if x["Valores"] == "Grao urbanización" and x["CodEspazo"] not in VELLOS)
print("concellos por grao:", conc, "poboación 2024:", pob24, "densidade:", dens)
out = {"ind": T, "orde": list(T), "concellos": conc, "pob": pob24, "dens": dens}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json")

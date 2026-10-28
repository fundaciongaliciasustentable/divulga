#!/usr/bin/env python3
"""Series anuais para a calculadora «Dende que naciches» → data/datos.json

Series doutras fontes, descargadas en data/raw/ se faltan:
  · INE, IPC, índice xeral nacional, variación anual mensual dende 1962 (serie IPC251856):
    https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/IPC251856?nult=1000 — encadéase a variación
    de decembro a decembro para ter un índice anual (decembro de cada ano).
  · Ministerio de Traballo, Boletín de Estatísticas Laborais, SMI-1 «Evolución do salario mínimo
    interprofesional» (mensual, dende 1980): https://www.mites.gob.es/estadisticas/bel/SMI/smi1.xls
  · Our World in Data (CC BY): poboación mundial (HYDE/Gapminder/ONU), esperanza de vida (HMD/ONU),
    CO₂ na atmosfera (NOAA), usuarios de internet e liñas de móbil (UIT/Banco Mundial).
  · Wikipedia (Galipedia e en castelán): acontecementos de cada ano (ver wiki.py).
E as series xa preparadas noutras pezas de Divulga (o seu data/datos.json):
  · espiral-lumes: hectáreas queimadas en Galicia cada ano (EGIF ata 2016, EFFIS dende 2017), 1983-
  · raias-clima: anomalía da temperatura media anual en seis observatorios de AEMET, dende 1931
  · ondas-atlantico: temperatura media anual do mar fronte ás Rías Baixas (NOAA OISST), dende 1982
  · galicia-apagandose: poboación de cada entidade singular (aldea, lugar) do Nomenclátor do IGE,
    1999-2025; unha aldea «baleirouse» o ano en que pasa a ter 0 habitantes despois de ter algún
  · camino-compostela: peregrinos que recolleron a Compostela, dende 2004
  · nomes-galicia: os nomes máis frecuentes por década de nacemento e por ano (dende 2000)
"""
import csv
import html
import io
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd

HERE = Path(__file__).resolve().parent
F = HERE.parent
peza = lambda s: json.loads((F / s / "data" / "datos.json").read_text(encoding="utf-8"))

lu = peza("espiral-lumes")
lume = {x["y"]: x["tot"] for x in lu["anos"]}
ult_lume = max(lume)

ra = peza("raias-clima")
temp = {}
for e in ra["est"]:
    for s in e["s"]:
        if s["t"] is not None:
            temp.setdefault(s["y"], []).append(s["t"])
# media das estacións con dato; só anos con polo menos dúas estacións
temp = {a: round(sum(v) / len(v), 3) for a, v in temp.items() if len(v) >= 2}

on = peza("ondas-atlantico")
mar = {x["a"]: x["m"] for x in on["anos"]}

ap = peza("galicia-apagandose")
anos_ap = ap["anos"]
baleiras = {a: 0 for a in anos_ap}   # aldeas que pasan a 0 habitantes ese ano
for e in ap["e"]:
    cod = e[4]
    for i in range(1, len(cod)):
        if cod[i] == "0" and cod[i - 1] not in ("0", "-"):
            baleiras[anos_ap[i]] += 1
total_baleiras = {a: sum(1 for e in ap["e"] if e[4][i] == "0") for i, a in enumerate(anos_ap)}

ca = peza("camino-compostela")
pere = {a: v for a, v in ca["serie"]}

no = peza("nomes-galicia")
nomes = {"dec": {d: [no["dec"]["12"]["H"][i][0], no["dec"]["12"]["M"][i][0]] for i, d in enumerate(no["decadas"])},
         "ano": {a: [no["anos"]["H"][a][0][0], no["anos"]["M"][a][0][0]] for a in no["anos"]["H"]}}

RAW = HERE / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "DivulgaFGS/1.0 (https://divulga.galiciasustentable.org)"}


def baixa(nome, url):
    f = RAW / nome
    if not f.exists():
        f.write_bytes(urlopen(Request(url, headers=UA), timeout=120).read())
    return f


# IPC: índice de decembro de cada ano, encadeando a variación anual (decembro 1961 = 1)
ipc_v = json.loads(baixa("ine_ipc251856.json", "https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/IPC251856?nult=1000").read_text())["Data"]
dec = {x["Anyo"]: x["Valor"] for x in ipc_v if x["FK_Periodo"] == 12}
ipc, v = {1961: 1.0}, 1.0
for a in sorted(dec):
    v *= 1 + dec[a] / 100
    ipc[a] = round(v, 5)


# Subíndices de alimentos (IPC251862) e transporte (IPC251892), con datos dende 1994: encadéanse
# dende o índice xeral de 1993, así que antes de 1994 seguen ao xeral
def subindice(serie):
    v = json.loads(baixa(f"ine_ipc{serie}.json", f"https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/IPC{serie}?nult=1000").read_text())["Data"]
    dv = {x["Anyo"]: x["Valor"] for x in v if x["FK_Periodo"] == 12}
    out, w = {1993: ipc[1993]}, ipc[1993]
    for a in sorted(dv):
        w *= 1 + dv[a] / 100
        out[a] = round(w, 5)
    return out


ipc_al, ipc_tr = subindice(251862), subindice(251892)

# Vivenda: valor tasado medio da vivenda libre en Galicia (€/m², MIVAU, trimestral dende 1995), media
# dos trimestres de cada ano. É o mesmo ficheiro que usa a peza vivenda-salario.
import xlrd
viv = {}
bk = xlrd.open_workbook(baixa("mivau_35101000.xls", "https://apps.fomento.gob.es/BoletinOnline2/sedal/35101000.XLS"))
for sh in bk.sheets():
    cab = sh.row_values(11)
    fila = next(sh.row_values(i) for i in range(12, sh.nrows) if str(sh.row_values(i)[1]).strip() == "Galicia")
    for c, h in enumerate(cab):
        m = re.match(r"Año (\d{4})", str(h))
        if m:
            fin = next((j for j in range(c + 1, c + 4) if j < len(cab) and cab[j]), c + 4)  # ata a cabeceira seguinte («Variación»)
            q = [x for x in fila[c:fin] if isinstance(x, float)]
            if q:
                viv[int(m.group(1))] = round(sum(q) / len(q), 1)

# SMI mensual (euros)
smi_df = pd.read_excel(baixa("mites_smi1.xls", "https://www.mites.gob.es/estadisticas/bel/SMI/smi1.xls"), header=None, engine="xlrd")
smi = {}
for _, r in smi_df.iterrows():
    m = re.match(r"\s*1-[IVX]+-(\d{4})", str(r[0]))
    if m and isinstance(r[5], (int, float)) and r[5] == r[5]:
        smi[int(m.group(1))] = round(float(r[5]), 2)  # se hai varios no ano, queda o último

# Our World in Data
def owid(nome, ent, col, q=""):
    f = baixa(f"owid_{nome}.csv", f"https://ourworldindata.org/grapher/{nome}.csv?v=1&csvType=full&useColumnShortNames=true{q}")
    out = {}
    for r in csv.DictReader(io.StringIO(f.read_text(encoding="utf-8"))):
        if r["entity"] == ent and r[col]:
            out[int(r["year"])] = round(float(r[col]), 3)
    return out


mundo = {"pob": {a: v for a, v in owid("population", "World", "population_historical").items() if a >= 1930},
         "co2": {a: v for a, v in owid("co2-long-term-concentration", "World", "co2_concentration").items() if a >= 1930},
         "evES": {a: v for a, v in owid("life-expectancy", "Spain", "life_expectancy_0").items() if a >= 1930},
         "net": owid("share-of-individuals-using-the-internet", "Spain", "it_net_user_zs"),
         "mob": owid("mobile-cellular-subscriptions-per-100-people", "Spain", "it_cel_sets_p2")}

# Acontecementos de cada ano (Galipedia e Wikipedia en castelán), xa descargados por wiki.py.
# Un punto é «de Galicia» se nomea un concello galego ou outra palabra clave (con límites de palabra,
# para que «vigor» non sexa Vigo)
AMBIGUOS = {"Muros", "Coles", "Curtis", "Marín", "Melón", "Sober", "Toques", "Pol", "Cangas", "Bande", "Valga", "Porto"}  # palabras ou apelidos comúns
conc = [c for c in ap["concellos"] if len(c) >= 4 and c not in AMBIGUOS]
GAL = re.compile(r"\b(" + "|".join(re.escape(c) for c in conc) + r"|Galiza|Galicia|galeg\w*|Compostela|Celta|Deportivo|Xunta|TVG|CRTVG|"
                 r"Castelao|Rosalía|Prestige|Mar Exeo|Casón|Rías Baixas|Coruñes\w*|ourensán\w*|lucense\w*|vigués\w*|Nunca Máis|BNG|"
                 r"Fraga Iribarne|Feijóo|Touriño)\b", re.I)
ESP = re.compile(r"\b(España|español\w*|Madrid|Barcelona|Franco(?!-)|franquis\w*|Cortes Generales|Congreso de los Diputados|Juan Carlos|"
                 r"Felipe González|Suárez|Aznar|Zapatero|Rajoy|Sánchez|ETA|PSOE|Partido Popular|Sevilla|Valencia|Bilbao|"
                 r"Cataluña|Euskadi|País Vasco|Andalucía|Generalitat|Real Madrid|lehendakari|BOE)\b", re.I)
# primeiro os puntos con data («12 de xullo: …»), que son os acontecementos propiamente ditos
DATA = re.compile(r"^\d{1,2} de \w+|^(xaneiro|febreiro|marzo|abril|maio|xuño|xullo|agosto|setembro|outubro|novembro|decembro|enero|febrero|mayo|junio|julio|"
                  r"septiembre|octubre|noviembre|diciembre)\b", re.I)
datados = lambda l: sorted(l, key=lambda x: not DATA.search(x))
limpa = lambda x: re.sub(r" ([.,;:])", r"\1", re.sub(r"[\s\u200b]+", " ", re.sub(r"\[(\d+|cita requerida|nota \d+)\]", "", html.unescape(re.sub(r"<[^>]+>", "", x))))).strip()


def puntos(w, ano):
    f = RAW / f"wiki_{w}_{ano}.json"
    if not f.exists():
        return []
    d = json.loads(f.read_text(encoding="utf-8"))
    if "parse" not in d:
        return []
    t = d["parse"]["text"]["*"]
    corte = re.search(r'id="(Nacementos|Nacimientos|Mortes|Falecementos|Fallecimientos)"', t)
    corpo = t[:corte.start()] if corte else t
    corpo = re.sub(r'<li class="gallerybox".*?</li>\s*</ul>|<ul class="gallery.*?</ul>', "", corpo, flags=re.S)  # pés de foto
    li = [re.sub(r"\s*V[ée]a?xase:.*$", "", limpa(re.sub(r"<ul>.*?</ul>", "", x, flags=re.S))) for x in re.findall(r"<li[^>]*>(.*?)</li>", corpo, re.S)]
    return [x for x in li if 25 <= len(x) <= 260 and not re.search(r"\((n|m|f)\. \d{4}\)| sem\. L M", x)
            and not x.lower().startswith(("véxase", "véase", "artigo principal"))]


# Día das Letras Galegas: «Nome (AAAA)» na táboa do artigo
lt = limpa(json.loads((RAW / "wiki_gl_letras.json").read_text(encoding="utf-8"))["parse"]["text"]["*"])
lt = lt[lt.index("Rosalía de Castro (1963)"):]
letras = {int(a): n.strip() for n, a in re.findall(r"(.+?) \((\d{4})\)", lt[:lt.index("(2027)") + 6])}

# Tradución ao galego dos puntos de España (feita á man a partir do texto da Wikipedia en castelán)
TRAD = json.loads((HERE / "data" / "esp_gl.json").read_text(encoding="utf-8")) if (HERE / "data" / "esp_gl.json").exists() else {}
noticias = {}
for ano in range(1930, 2026):
    gl, es = puntos("gl", ano), puntos("es", ano)
    gal = datados([x for x in gl if GAL.search(x)])[:4]
    esp = [TRAD.get(x, x) for x in datados([x for x in es if ESP.search(x) and not GAL.search(x)])[:4]]
    mun = datados([x for x in gl if not GAL.search(x) and not ESP.search(x)])[:4]
    noticias[ano] = {"gal": gal, "esp": esp, "mun": mun, "letras": letras.get(ano, "")}
cheos = sum(1 for v in noticias.values() if v["gal"] and v["esp"] and v["mun"])
print("vivenda", min(viv), "-", max(viv), viv[min(viv)], "→", viv[max(viv)], "· alimentos", ipc_al[max(ipc_al)] / ipc_al[1993], "· sen traducir",
      sum(1 for v in noticias.values() for x in v["esp"] if x not in TRAD.values()))
print("IPC", min(ipc), "-", max(ipc), f"(× {ipc[max(ipc)] / ipc[1985]:.2f} dende 1985)", "· SMI", min(smi), "-", max(smi),
      "· anos con noticias das tres partes:", cheos, "de", len(noticias))

out = {"ipc": ipc, "ipcAl": ipc_al, "ipcTr": ipc_tr, "viv": viv, "smi": smi, "mundo": mundo, "noticias": noticias, "lume": lume, "ultLume": ult_lume, "temp": temp, "mar": mar, "baleiras": baleiras, "totBal": total_baleiras,
       "pere": pere, "nomes": nomes, "anosAp": [anos_ap[0], anos_ap[-1]]}
print("lume", min(lume), "-", ult_lume, "· temp", min(temp), "-", max(temp), "· mar", min(mar), "-", max(mar),
      "· aldeas", anos_ap[0], "-", anos_ap[-1], f"({total_baleiras[anos_ap[0]]} → {total_baleiras[anos_ap[-1]]} baleiras)",
      "· peregrinos", min(pere), "-", max(pere))
print("baleiradas por ano:", {a: v for a, v in baleiras.items() if a % 5 == 0})
(HERE / "data").mkdir(exist_ok=True)
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json")

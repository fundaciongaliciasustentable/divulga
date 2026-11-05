#!/usr/bin/env python3
"""Cruza os datos.json xa procesados doutras pezas de Divulga nun único
dataset por concello, para o comparador estilo Gapminder.

Non toca ningunha fonte en bruto: reutiliza os data/datos.json que xa
xeraron os prep.py de cada peza orixe (idade-concellos, renda-concellos,
paro-concellos...). Se algunha desas pezas cambia o seu formato, hai que
axustar aquí a función de extracción correspondente.

Saída: fontes/comparador/data/datos.json
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FONTES = ROOT / "fontes"


def cargar(slug):
    return json.loads((FONTES / slug / "data" / "datos.json").read_text(encoding="utf-8"))


# --- lista mestra de concellos (313) -----------------------------------
base = cargar("idade-concellos")
CONC = [{"id": c["id"], "n": c["n"], "pr": c["pr"]} for c in base["conc"]]
IDS = {c["id"] for c in CONC}

# --- poboación por ano, fonte común para normalizar taxas ---------------
vacas = cargar("vacas-persoas")
POB = {c["id"]: {int(a): v for a, v in c["pob"].items()} for c in vacas["concellos"]}


def pob_ano(cid, ano):
    """Poboación do concello no ano pedido, ou a do ano dispoñible máis preto."""
    serie = POB.get(cid)
    if not serie:
        return None
    if ano in serie:
        return serie[ano]
    return serie[min(serie, key=lambda a: abs(a - ano))]


IND = {}


def rexistra(id_, et, cat, un, fonte, valores):
    """valores: {concello_id: {ano_int: valor}}"""
    valores = {k: v for k, v in valores.items() if v}
    IND[id_] = {"et": et, "cat": cat, "un": un, "fonte": fonte, "valores": valores}


# 1. Poboación (tamén serve de tamaño por defecto) -----------------------
rexistra("poboacion", "Poboación", "Demografía", "habitantes",
          "INE/IGE, padrón municipal",
          {cid: dict(serie) for cid, serie in POB.items()})

# 2-3. Idade -------------------------------------------------------------
idade = cargar("idade-concellos")
rexistra("idade_media", "Idade media", "Demografía", "anos",
          "IGE, táboa 62",
          {c["id"]: {idade["ano"]: c["im"]} for c in idade["conc"]})
rexistra("envellecemento", "Índice de envellecemento", "Demografía", "maiores de 64 por cada 100 menores de 20",
          "IGE, táboa 62",
          {c["id"]: {idade["ano"]: c["ie"]} for c in idade["conc"]})

# 4. Renda -----------------------------------------------------------------
renda = cargar("renda-concellos")
rexistra("renda", "Renda neta media por persoa", "Economía", "€/ano",
          "INE, Atlas de distribución de renda dos fogares",
          {c["id"]: {renda["ano"]: c["p"]} for c in renda["conc"]})

# 5. Paro (normalizado coa poboación do ano correspondente) --------------
paro = cargar("paro-concellos")
ANOS_PARO = paro["anos"]
paro_val = {}
for c in paro["conc"]:
    serie = {}
    for a, s in zip(ANOS_PARO, c["s"]):
        if s is None:
            continue
        p = pob_ano(c["id"], a)
        if p:
            serie[a] = round(s / p * 1000, 2)
    paro_val[c["id"]] = serie
rexistra("paro", "Parados rexistrados", "Economía", "por cada 1.000 habitantes",
          "SEPE / IGE", paro_val)

# 6. Débeda municipal (dous puntos: 2015 e a última) ----------------------
debeda = cargar("debeda-concellos")
deb_val = {}
for c in debeda["conc"]:
    serie = {}
    if c.get("p15"):
        serie[2015] = round(c["d15"] / c["p15"], 1)
    if c.get("p"):
        serie[debeda["ano"]] = round(c["d"] / c["p"], 1)
    deb_val[c["id"]] = serie
rexistra("debeda", "Débeda municipal", "Economía", "€ por habitante",
          "Ministerio de Facenda, débeda viva das entidades locais", deb_val)

# 7. Pensionistas por cada 100 afiliados ----------------------------------
pens = cargar("pensionistas-afiliados")
rexistra("pensionistas", "Pensionistas", "Economía", "por cada 100 afiliados á Seguridade Social",
          "Seguridade Social / IGE",
          {c["id"]: {pens["ano"]: round(c["pe"] / c["af"] * 100, 1)} for c in pens["conc"] if c.get("af")})

# 8. Vivendas non principais ------------------------------------------------
vb = cargar("casas-baleiras")
rexistra("vivendas_baleiras", "Vivendas non principais", "Vivenda", "% das vivendas totais",
          "INE, Censo de vivendas",
          {c["id"]: {2021: round(c["np"] / c["t"] * 100, 1)} for c in vb["conc"] if c.get("t")})

# 9. Vidro reciclado por habitante (normalizado por ano) ------------------
vidro = cargar("vidro-concellos")
ANOS_V = vidro["anos"]
vidro_val = {}
for c in vidro["conc"]:
    serie = {}
    for a, kg in zip(ANOS_V, c["kg"]):
        if not kg:
            continue
        p = pob_ano(c["id"], a)
        if p:
            serie[a] = round(kg / p, 1)
    vidro_val[c["id"]] = serie
rexistra("vidro", "Vidro reciclado", "Ambiente", "kg por habitante e ano",
          "Ecovidrio", vidro_val)

# 10. Superficie de eucalipto ----------------------------------------------
monte = cargar("monte-concellos")
euc_val = {}
for c in monte["concellos"]:
    serie = {}
    for a, v in c.get("ha", {}).items():
        tot = v.get("e", 0) + v.get("c", 0) + v.get("f", 0)
        if tot:
            serie[int(a)] = round(v.get("e", 0) / tot * 100, 1)
    euc_val[c["id"]] = serie
rexistra("eucalipto", "Superficie de eucalipto", "Ambiente", "% da superficie arborada",
          "Xunta de Galicia, estatística forestal", euc_val)

# 11. Coñecemento do galego (dous puntos censais) --------------------------
galego = cargar("galego-concellos")
gal_val = {}
for c in galego["conc"]:
    serie = {}
    if c.get("t1"):
        serie[2001] = round(c["s1"] / c["t1"] * 100, 1)
    if c.get("t2"):
        serie[2011] = round(c["s2"] / c["t2"] * 100, 1)
    gal_val[c["id"]] = serie
rexistra("galego", "Sabe falar galego", "Cultura", "% da poboación",
          "IGE, censos de poboación", gal_val)

# 12. Préstamos de biblioteca por habitante --------------------------------
bib = cargar("bibliotecas-concellos")
rexistra("bibliotecas", "Préstamos de biblioteca", "Cultura", "por habitante e ano",
          "Rede de bibliotecas de Galicia",
          {c["id"]: {bib["ano"]: round(c["p"] / c["h"], 2)} for c in bib["conc"] if c.get("h") and c.get("p") is not None})

# 13. Tempo medio ao hospital ------------------------------------------------
hosp = cargar("minutos-hospital")
rexistra("hospital", "Tempo medio ata o hospital", "Servizos", "minutos por estrada",
          "Elaboración propia sobre a rede viaria e os hospitais públicos",
          {c["id"]: {2025: c["m"]} for c in hosp["conc"] if c.get("m") is not None})

# 14. Prazas turísticas por 100 habitantes ---------------------------------
praz = cargar("prazas-turisticas")
ANOS_P = praz["anos"]
praz_val = {}
for c in praz["conc"]:
    hab = c.get("hab")
    if not hab:
        continue
    serie = {}
    for a, v in zip(ANOS_P, c["h"]):
        serie[int(a)] = round(v / hab * 100, 1)
    praz_val[c["id"]] = serie
rexistra("prazas_turisticas", "Prazas turísticas", "Turismo", "por cada 100 habitantes",
          "INE, Enquisa de ocupación en aloxamentos", praz_val)

# 15. Vacas por 100 habitantes (anos comúns ás dúas series) ---------------
vac_val = {}
for c in vacas["concellos"]:
    pob = {int(a): v for a, v in c["pob"].items()}
    vac = {int(a): v for a, v in c.get("vac", {}).items()}
    serie = {a: round(vac[a] / pob[a] * 100, 1) for a in sorted(set(pob) & set(vac)) if pob[a]}
    vac_val[c["id"]] = serie
rexistra("vacas", "Vacas", "Rural", "por cada 100 habitantes",
          "IGE / SITEGAL (censo gandeiro)", vac_val)

# 16. Praias con bandeira azul ---------------------------------------------
band = cargar("bandeiras-azuis")
ANOS_B = band["anos"]
rexistra("bandeiras", "Praias con bandeira azul", "Ambiente", "número de praias",
          "ADEAC",
          {c["id"]: {a: v for a, v in zip(ANOS_B, c["b"])} for c in band["conc"]})

GRUPOS = ["Demografía", "Economía", "Vivenda", "Rural", "Ambiente", "Cultura", "Servizos", "Turismo"]

saida = {"concellos": CONC, "indicadores": IND, "grupos": GRUPOS}
(HERE / "data" / "datos.json").write_text(
    json.dumps(saida, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

n_ind = len(IND)
n_val = sum(len(v["valores"]) for v in IND.values())
print(f"{n_ind} indicadores · {n_val} series de concello · {len(CONC)} concellos")
for k, v in IND.items():
    anos = sorted({a for s in v["valores"].values() for a in s})
    print(f"  {k:20} {v['et']:32} [{anos[0] if anos else '-'}–{anos[-1] if anos else '-'}]  n={len(v['valores'])}")

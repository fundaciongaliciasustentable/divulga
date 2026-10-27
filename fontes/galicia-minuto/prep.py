#!/usr/bin/env python3
"""Cifras anuais de Galicia para os contadores de «Galicia nun minuto» → data/datos.json

Cada contador é un total anual que a páxina reparte de xeito uniforme polos segundos do ano.
Saen de tres sitios:
  · outras pezas de Divulga (luz, camiño, mar, migracións, lumes, raias do clima): o seu data/datos.json;
  · descargas: IGE 11070 (PIB a prezos correntes) e INE 2074 (viaxeiros en hoteis), en data/raw/;
  · notas de prensa con cifra pechada, coa ligazón ao lado (MNP, leite, comercio exterior, aeroportos).
"""
import csv
import json
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
FONTES = HERE.parent
RAW = HERE / "data" / "raw"
URLS = {"ige_11070.csv": "https://www.ige.gal/igebdt/igeapi/csv/datos/11070",
        "ine_2074.json": "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/2074?nult=36&tip=AM"}
RAW.mkdir(parents=True, exist_ok=True)
for f, u in URLS.items():
    if not (RAW / f).exists():
        (RAW / f).write_bytes(urlopen(Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=120).read())


def peza(slug):
    return json.loads((FONTES / slug / "data" / "datos.json").read_text(encoding="utf-8"))


C = []
def cont(clave, tema, n, ano, valor, unidade, fonte, url, sub="", discreto=True):
    """valor: total do ano. discreto: cousas que se contan unha a unha (persoas, vodas)."""
    C.append({"k": clave, "tema": tema, "n": n, "y": ano, "v": valor, "u": unidade, "f": fonte, "url": url,
              "sub": sub, "d": discreto})


# Persoas: IGE, Movemento natural da poboación 2025 (provisional, 26/06/2026)
MNP = "https://www.ige.gal/estatico/html/gl/OperacionsEstruturais/PDF/Resumo_resultados_MNP_2025p.pdf"
cont("nac", "Persoas", "nacementos", 2025, 13556, "bebés", "IGE, MNP 2025 (provisional)", MNP)
cont("def", "Persoas", "defuncións", 2025, 33456, "persoas", "IGE, MNP 2025 (provisional)", MNP,
     "Máis de dous terzos, de 80 ou máis anos.")
cont("mat", "Persoas", "vodas", 2025, 9714, "matrimonios", "IGE, MNP 2025 (provisional)", MNP)
mi = peza("migracions")
cont("inm", "Persoas", "chegan a vivir dende o estranxeiro", mi["ano"], mi["total"]["ei"], "persoas",
     "INE, Estatística de migracións", "https://www.ine.es/dyngs/INEbase/operacion.htm?c=Estadistica_C&cid=1254736177000")
cont("emi", "Persoas", "marchan a vivir ao estranxeiro", mi["ano"], mi["total"]["ee"], "persoas",
     "INE, Estatística de migracións", "https://www.ine.es/dyngs/INEbase/operacion.htm?c=Estadistica_C&cid=1254736177000")

# Viaxes
ca = peza("camino-compostela")
ano_c, per = ca["serie"][-1]
cont("per", "Viaxes", "peregrinos recollen a Compostela", ano_c, per, "peregrinos", "Oficina do Peregrino",
     "https://oficinadelperegrino.com/estadisticas/", "Concéntranse entre maio e outubro: no verán, case tres por minuto.")
ine = json.loads((RAW / "ine_2074.json").read_text(encoding="utf-8"))
hot = {}
for s in ine:
    for chave, nome in (("viax", "Galicia. Viajeros. Total."), ("noit", "Galicia. Pernoctaciones. Total.")):
        if s["Nombre"].strip() == nome:
            m = [x["Valor"] for x in s["Data"] if x["Anyo"] == 2025]
            assert len(m) == 12, (nome, len(m))
            hot[chave] = round(sum(m))
cont("hot", "Viaxes", "viaxeiros entran nun hotel", 2025, hot["viax"], "viaxeiros",
     "INE, Enquisa de ocupación hoteleira", "https://www.ine.es/dynt3/inebase/index.htm?padre=238",
     f"E durmen {hot['noit']:,} noites en hoteis ao ano.".replace(",", "."))
AENA = {"Santiago": 3120759, "A Coruña": 1292166, "Vigo": 1114810}  # notas de Aena do 13/01/2026
cont("avi", "Viaxes", "pasaxeiros nos aeroportos", 2025, sum(AENA.values()), "pasaxeiros",
     "Aena, balance de tráfico 2025", "https://www.aena.es/es/prensa.html",
     "Santiago, A Coruña e Vigo xuntos.")

# Economía
pib = next(float(x["DatoN"]) for x in csv.DictReader((RAW / "ige_11070.csv").open(encoding="latin1"))
           if x["Tempo"] == "2025" and x["Prezos"] == "Prezos correntes" and x["Tratamento do dato"] == "Datos brutos"
           and x["Compoñentes"] == "PIBpm" and x["Dato"] == "Niveis")
cont("pib", "Economía", "de riqueza producida (PIB)", 2025, round(pib * 1000), "euros",
     "IGE, Contabilidade trimestral (táboa 11070)", "https://www.ige.gal/igebdt/selector.jsp?COD=11070",
     discreto=False)
cont("exp", "Economía", "en vendas ao estranxeiro", 2025, 30_939_000_000, "euros",
     "IGE, Comercio exterior (decembro 2025)",
     "https://www.ige.gal/estatico/html/gl/OperacionsConxunturais/PDF/InformeComercioExterior2025_12.pdf",
     "Exportacións de bens. A moda e o automóbil levan a maior parte.", discreto=False)

# Campo e mar
LEITE_T = 3_088_325  # entregas declaradas a compradores en 2025 (FEGA/MAPA)
cont("lei", "Campo e mar", "de leite saen das granxas", 2025, round(LEITE_T * 1000 / 1.032), "litros",
     "FEGA/MAPA, declaracións de entregas de leite 2025", "https://www.fega.gob.es/es/datos-abiertos/consulta-de-datos-sectoriales",
     "O 40 % do leite de vaca de España. (3,09 millóns de toneladas a 1,032 kg por litro.)", discreto=False)
mar = peza("mar-prato")
ano_m = str(max(map(int, mar["total"])))
kg, eur = mar["total"][ano_m]
cont("pei", "Campo e mar", "de peixe e marisco véndense en lonxa", int(ano_m), kg, "quilos",
     "Xunta, Pesca de Galicia (vendas en lonxa)", "https://www.pescadegalicia.gal/",
     f"Por {eur / 1e6:,.0f} millóns de euros ao ano. Sen contar o mexillón de batea.".replace(",", "."), discreto=False)

# Enerxía e clima
luz = peza("luz-galicia")[-1]
cont("ele", "Enerxía e clima", "de electricidade xerada", luz["y"], luz["tot"] * 1000, "MWh",
     "REE, balance eléctrico por comunidade", "https://www.ree.es/es/datos/balance",
     f"O {round(luz['eol'] / luz['tot'] * 100)} % co vento. Galicia consome só o {round(luz['dem'] / luz['tot'] * 100)} % do que xera.",
     discreto=False)
lu = peza("espiral-lumes")
dec = [x["tot"] for x in lu["anos"] if 2016 <= x["y"] <= 2025]
a25 = next(x["tot"] for x in lu["anos"] if x["y"] == 2025)
cont("lum", "Enerxía e clima", "de monte arden", "2016-2025", round(sum(dec) / len(dec)), "hectáreas",
     "EGIF (ata 2016) e EFFIS (dende 2017)", "https://effis.jrc.ec.europa.eu/",
     f"Media da última década. En 2025 arderon {a25:,} ha, cinco veces máis.".replace(",", "."), discreto=False)
ra = peza("raias-clima")
mm = sum(e["nP"] for e in ra["est"]) / len(ra["est"])
SUP_KM2 = 29_575
cont("cho", "Enerxía e clima", "de choiva caen sobre Galicia", "1991-2020", round(mm / 1000 * SUP_KM2 * 1e6 * 1000), "litros",
     "AEMET, normais 1991-2020 de seis observatorios (estimación)", "https://www.aemet.es/es/serviciosclimaticos/datosclimatologicos/valoresclimatologicos",
     f"Estimación: {mm:,.0f} mm ao ano, a media dos seis observatorios, sobre os {SUP_KM2:,} km² de Galicia.".replace(",", "."),
     discreto=False)

for c in C:
    print(f"{c['k']:4} {c['y']!s:10} {c['v']:>18,}  {c['v'] / 525_960:>14,.2f} ao minuto  {c['n']}")
(HERE / "data" / "datos.json").write_text(json.dumps({"c": C}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json")

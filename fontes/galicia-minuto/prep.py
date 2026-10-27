#!/usr/bin/env python3
"""Cifras anuais de Galicia para o panel de «Galicia nun minuto» → data/datos.json

Cada contador é un total anual que a páxina reparte polos segundos do ano. Escóllense fluxos que
se moven abondo nun minuto (de un a millóns de unidades); os sucesos raros (nacementos e
defuncións) van á parte, nunha faixa de «de cando en vez».
Saen de tres sitios:
  · outras pezas de Divulga (luz, camiño, mar, raias do clima): o seu data/datos.json;
  · descargas: IGE 11070 (PIB a prezos correntes) e INE 2074 (viaxeiros en hoteis), en data/raw/;
  · informes e notas con cifra pechada, coa ligazón ao lado.
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


mil = lambda v: f"{v:,.0f}".replace(",", ".")
POB25 = 2_720_738  # poboación a 1 de xullo de 2025 (IGE, cifras de poboación)
C = []
def cont(clave, tema, n, ano, valor, unidade, fonte, url, sub="", discreto=False, raro=False):
    """valor: total do ano. discreto: cousas que se contan unha a unha (chegan ao chou, arredor da media).
    raro: vai na faixa de abaixo, con conta atrás ata o seguinte."""
    C.append({"k": clave, "tema": tema, "n": n, "y": ano, "v": valor, "u": unidade, "f": fonte, "url": url,
              "sub": sub, "d": discreto, "r": raro})


# Saúde e emerxencias
cont("far", "Saúde e emerxencias", "medicamentos con receita do Sergas", 2025, 79_814_846, "envases",
     "Ministerio de Sanidade, facturación de receitas (decembro 2025)",
     "https://www.sanidad.gob.es/areas/farmacia/consumoMedicamentos/facturacionRecetas/totales/2025/diciembre.htm",
     f"Envases facturados ás farmacias: {mil(942_928_694 / 1e6)} millóns de euros no ano.", discreto=True)
cont("112", "Saúde e emerxencias", "chamadas ao 112", 2024, 869_424, "chamadas", "Xunta, balance do 112 Galicia 2024",
     "https://www.xunta.gal/gl/notas-de-prensa/-/nova/009818/avances-tecnoloxicos-concienciacion-poboacion-contribuen-terceira-cifra-chamadas",
     "Unha de cada catro acaba nunha actuación.", discreto=True)

# Viaxes
AENA = {"Santiago": 3120759, "A Coruña": 1292166, "Vigo": 1114810}  # notas de Aena do 13/01/2026
cont("avi", "Viaxes", "pasaxeiros nos aeroportos", 2025, sum(AENA.values()), "pasaxeiros",
     "Aena, balance de tráfico 2025", "https://www.aena.es/es/prensa.html", "Santiago, A Coruña e Vigo xuntos.", discreto=True)
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
     f"E durmen {mil(hot['noit'])} noites ao ano.", discreto=True)
ano_c, per = peza("camino-compostela")["serie"][-1]
cont("per", "Viaxes", "peregrinos recollen a Compostela", ano_c, per, "peregrinos", "Oficina do Peregrino",
     "https://oficinadelperegrino.com/estadisticas/", "No verán, case tres por minuto.", discreto=True)

# Economía
pib = next(float(x["DatoN"]) for x in csv.DictReader((RAW / "ige_11070.csv").open(encoding="latin1"))
           if x["Tempo"] == "2025" and x["Prezos"] == "Prezos correntes" and x["Tratamento do dato"] == "Datos brutos"
           and x["Compoñentes"] == "PIBpm" and x["Dato"] == "Niveis")
cont("pib", "Economía", "de riqueza producida (PIB)", 2025, round(pib * 1000), "euros",
     "IGE, Contabilidade trimestral (táboa 11070)", "https://www.ige.gal/igebdt/selector.jsp?COD=11070",
     f"Uns {mil(pib * 1000 / POB25)} euros por persoa ao ano.")
cont("exp", "Economía", "en vendas ao estranxeiro", 2025, 30_939_000_000, "euros",
     "IGE, Comercio exterior (decembro 2025)",
     "https://www.ige.gal/estatico/html/gl/OperacionsConxunturais/PDF/InformeComercioExterior2025_12.pdf",
     "Exportacións de bens.")

# Campo, monte e mar
LEITE_T = 3_088_325  # entregas declaradas a compradores en 2025 (FEGA/MAPA)
cont("lei", "Campo, monte e mar", "de leite saen das granxas", 2025, round(LEITE_T * 1000 / 1.032), "litros",
     "FEGA/MAPA, entregas de leite 2025", "https://www.fega.gob.es/es/datos-abiertos/consulta-de-datos-sectoriales",
     "O 40 % do leite de vaca de España.")
cont("mex", "Campo, monte e mar", "de mexillón saen das bateas", 2025, 177_638_000, "quilos",
     "Consellería do Mar, produción de acuicultura 2025",
     "https://www.xunta.gal/gl/notas-de-prensa/-/nova/025489/villaverde-apoia-sector-miticultor-busca-alternativas-para-garantir-subministro",
     "A maior produción do mar galego.")
mar = peza("mar-prato")
ano_m = str(max(map(int, mar["total"])))
kg, eur = mar["total"][ano_m]
cont("pei", "Campo, monte e mar", "de peixe e marisco véndense en lonxa", int(ano_m), kg, "quilos",
     "Xunta, Pesca de Galicia (vendas en lonxa)", "https://www.pescadegalicia.gal/",
     f"Por {mil(eur / 1e6)} millóns de euros ao ano.")
cont("mad", "Campo, monte e mar", "de madeira córtanse no monte", 2023, 9_799_573, "m³",
     "Xunta, Cadea forestal-madeira 2023-2024", "https://xera.xunta.gal/sites/default/files/Cadena%20Forestal%20Madera%202023%202024%20.pdf",
     "O 94 % de montes privados.")

# Auga, enerxía e lixo
AUGA_LHD = 115  # litros por habitante e día nos fogares, Galicia 2024 (INE)
cont("aug", "Auga, enerxía e lixo", "de auga gastan os fogares", 2024, round(AUGA_LHD * POB25 * 365.25), "litros",
     "INE, Estatística sobre o subministro e saneamento da auga 2024", "https://www.ine.es/dyngs/Prensa/ESSA2024.pdf",
     f"{AUGA_LHD} litros por persoa e día, dos máis baixos de España.")
luz = peza("luz-galicia")[-1]
cont("ele", "Auga, enerxía e lixo", "de electricidade xerada", luz["y"], luz["tot"] * 1_000_000, "kWh",
     "REE, balance eléctrico por comunidade", "https://www.ree.es/es/datos/balance",
     f"O {round(luz['eol'] / luz['tot'] * 100)} % co vento. Galicia consome o {round(luz['dem'] / luz['tot'] * 100)} %.")
cont("lix", "Auga, enerxía e lixo", "de lixo da bolsa negra chegan a Sogama", 2024, 780_200_000, "quilos",
     "Sogama, balance de 2024 (en Metropolitano.gal)",
     "https://metropolitano.gal/extra/pontevedra-es-la-unica-provincia-gallega-en-la-que-se-reducen-los-residuos-sin-reciclar",
     "295 concellos; sen o reciclado nin a área da Coruña.")
ra = peza("raias-clima")
mm = sum(e["nP"] for e in ra["est"]) / len(ra["est"])
SUP_KM2 = 29_575
cont("cho", "Auga, enerxía e lixo", "de choiva caen sobre Galicia", "1991-2020", round(mm / 1000 * SUP_KM2 * 1e9), "litros",
     "AEMET, normais 1991-2020 de seis observatorios (estimación)",
     "https://www.aemet.es/es/serviciosclimaticos/datosclimatologicos/valoresclimatologicos",
     f"Estimación: {mil(mm)} mm ao ano sobre {mil(SUP_KM2)} km².")

# De cando en vez: IGE, Movemento natural da poboación 2025 (provisional, 26/06/2026)
MNP = "https://www.ige.gal/estatico/html/gl/OperacionsEstruturais/PDF/Resumo_resultados_MNP_2025p.pdf"
cont("nac", "De cando en vez", "nace un bebé", 2025, 13_556, "bebés", "IGE, MNP 2025 (provisional)", MNP, discreto=True, raro=True)
cont("def", "De cando en vez", "morre unha persoa", 2025, 33_456, "persoas", "IGE, MNP 2025 (provisional)", MNP, discreto=True, raro=True)
cont("mat", "De cando en vez", "casa unha parella", 2025, 9_714, "vodas", "IGE, MNP 2025 (provisional)", MNP, discreto=True, raro=True)

for c in C:
    print(f"{c['k']:4} {c['y']!s:10} {c['v']:>20,}  {c['v'] / 525_960:>16,.2f} ao minuto  {c['n']}")
(HERE / "data" / "datos.json").write_text(json.dumps({"c": C}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json")

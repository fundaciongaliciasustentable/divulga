#!/usr/bin/env python3
"""Lista de espera cirúrxica do Sergas por hospital e servizo → data/datos.json

Fonte: Sergas, «Lista de espera cirúrxica», un PDF por corte (30/06 e 31/12 de cada ano):
  https://www.sergas.gal/Asistencia-sanitaria/Lista-de-espera-cir%C3%BArxica
Do último corte lense as páxinas «por hospitais e servizos» (pacientes por tramo de espera, total
e tempo medio de espera en días) e a de Povisa (o hospital concertado de Vigo). De todos os cortes
lese o total do Sergas para a serie. PDFs gardados en data/raw/.
"""
import html
import json
import re
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

import pypdf

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
BASE = "https://www.sergas.gal"
UA = {"User-Agent": "Mozilla/5.0"}


def get(url):
    return urlopen(Request(url, headers=UA), timeout=120).read()


RAW.mkdir(parents=True, exist_ok=True)
lista = RAW / "lista.html"
if not lista.exists():
    lista.write_bytes(get(BASE + "/Asistencia-sanitaria/Lista-de-espera-cir%C3%BArxica"))
cortes = re.findall(r'href="(/Asistencia-sanitaria/Resultados-cir[^"]+)"[^>]*>\s*Resultados cir\S+ a (\d\d)/(\d\d)/(\d{4})',
                    lista.read_text(encoding="utf-8", errors="replace"))
pdfs = {}
for href, d, m, a in cortes:
    data = f"{a}-{m}-{d}"
    f = RAW / f"cir_{data}.pdf"
    if not f.exists():
        pax = get(BASE + quote(html.unescape(href), safe="/%?=&")).decode("utf-8", "replace")
        lig = re.search(r'((?:https?://[a-z.]*sergas\.gal)?/Asistencia-sanitaria/Documents/[^"\'<>]*?\.pdf)', pax, re.I)
        if not lig:
            print("sen PDF:", data)
            continue
        url = html.unescape(lig.group(1))
        url = url if url.startswith("http") else BASE + url
        f.write_bytes(get(quote(url, safe=":/%")))
        print("descargado", data)
    pdfs[data] = f

num = lambda s: float(s.replace(".", "").replace(",", "."))
FILA = re.compile(r"^(.+?)\s+((?:[\d.]+\s+)+)([\d.]+,\d+)\s*$")


def filas(texto):
    for l in texto.splitlines():
        m = FILA.match(l.strip())
        if m:
            ns = [num(x) for x in m.group(2).split()]
            yield m.group(1).strip(), ns, num(m.group(3))


# Serie: total do Sergas (sen Povisa) en cada corte
serie = []
for data, f in sorted(pdfs.items()):
    try:
        t = pypdf.PdfReader(f).pages[0].extract_text()
    except Exception as e:
        print("non se le", data, e)
        continue
    tot = next(((ns, tme) for n, ns, tme in filas(t) if n == "TOTAL"), None)
    if tot:
        serie.append([data, int(tot[0][-1]), tot[1]])
print("serie:", serie[0], "…", serie[-1], f"({len(serie)} cortes)")

# Último corte: hospitais e servizos
ult = max(pdfs)
r = pypdf.PdfReader(pdfs[ult])
HOSP = re.compile(r"^(C\.H\. |H\. |HOSPITAL |H\.)")
hosp, actual = {}, None
paxs = [i for i, p in enumerate(r.pages) if "POR HOSPITAIS E SERVIZOS" in p.extract_text()] or [11]
for i in range(paxs[0], len(r.pages)):
    t = r.pages[i].extract_text()
    if "POR SERVIZOS" in t.splitlines()[0] and "HOSPITAIS" not in t.splitlines()[0] and "POVISA" not in t.splitlines()[0]:
        continue  # a táboa de toda Galicia por servizos
    if "POVISA" in t.splitlines()[0]:
        break  # Povisa xa vén antes, na súa propia páxina de hospital
    for l in t.splitlines():
        l = l.strip()
        if HOSP.match(l) and not re.search(r"\d", l):
            actual = l
            continue
        m = FILA.match(l)
        if m and actual:
            n, ns, tme = m.group(1).strip(), [num(x) for x in m.group(2).split()], num(m.group(3))
            if n.startswith(actual) or n == "TOTAL":
                continue
            hosp.setdefault(actual, {})[n] = {"p": int(ns[-1]), "t": tme, "m12": int(ns[3]) if len(ns) >= 5 else 0}
hosp = {("H. POVISA (concertado)" if h.upper() == "H. POVISA" else h): v for h, v in hosp.items()}
serv = sorted({s for h in hosp.values() for s in h})
print("hospitais:", len(hosp), "servizos:", len(serv))
for h, v in hosp.items():
    print(f"  {h:38} {sum(x['p'] for x in v.values()):6} pacientes · {len(v)} servizos")
out = {"data": ult, "serie": serie, "hosp": hosp, "serv": serv}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json")

#!/usr/bin/env python3
"""Bibliotecas públicas de cada concello galego: préstamos, persoas inscritas e visitas → data/datos.json

Fonte: Ministerio de Cultura, «Bibliotecas Públicas Españolas en cifras», informe anual por
municipio (id=51) de cada provincia, exercicio 2024 (o último completo):
  https://www.mcu.es/alziraweb/alziraweb.cmd?command=GetAnexo&id=51&origen=PR&codigo=<prov>&ejercicio=2024
  prov = 15 (A Coruña), 27 (Lugo), 32 (Ourense), 36 (Pontevedra). Páxina xeral:
  https://www.mcu.es/alziraweb/alziraweb.cmd?command=GetAnexos
Cada fila trae habitantes do municipio, número de bibliotecas públicas, colección, visitas,
usuarios inscritos, prestatarios activos e préstamos presenciais. Os concellos con 0
bibliotecas non teñen biblioteca pública na estatística (poden ter servizo de bibliobús ou
furgoteca, que o Ministerio non asigna a ningún municipio); os que teñen biblioteca pero
aparecen con «-» non entregaron datos ese ano. HTML gardados en data/raw/.
Necesita pandas (lxml ou html5lib) para ler as táboas HTML.
"""
import io
import json
import re
import unicodedata
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
GEO = Path("/Users/perezgulin/Proxectos/galicia-agora/data-out/concellos-parroquias/data.geojson")
ANO = 2024
URL = "https://www.mcu.es/alziraweb/alziraweb.cmd?command=GetAnexo&id=51&origen=PR&codigo={}&ejercicio={}"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0"}
PROV = {"15": "A Coruña", "27": "Lugo", "32": "Ourense", "36": "Pontevedra"}
# nomes do Ministerio que non coinciden co nome oficial do IET
ALIAS = {"porto do son": "o porto do son", "a pastoriza": "pastoriza", "alfoz": "alfoz do castrodouro",
         "castro caldelas": "castro de caldelas", "rios": "o rios",
         "cangas": "cangas de morrazo", "oza cesuras": "oza cesuras"}


def nz(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"^(.*), (o|a|os|as)$", r"\2 \1", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def num(v):
    """As táboas usan «.» de miles e «-» para sen dato."""
    if isinstance(v, (int, float)) and not pd.isna(v):
        return int(v)
    s = str(v).strip()
    return None if s in ("-", "", "nan") else int(s.replace(".", ""))

feat = [f["properties"] for f in json.loads(GEO.read_text(encoding="utf-8"))["features"] if f["properties"]["nivel"] == "concello"]
porn = {nz(p["nome"]): p for p in feat}
# variantes sen artigo do nome oficial (A Pastoriza → pastoriza, O Riós → rios…)
for p in feat:
    porn.setdefault(re.sub(r"^(o|a|os|as) ", "", nz(p["nome"])), p)
RAW.mkdir(parents=True, exist_ok=True)
conc, tot = [], {}
for cp, pn in PROV.items():
    f = RAW / f"mcu_51_{cp}_{ANO}.html"
    if not f.exists():
        f.write_bytes(urlopen(Request(URL.format(cp, ANO), headers=UA), timeout=120).read())
    t = pd.read_html(io.StringIO(f.read_text(encoding="iso-8859-15")), thousands='.', decimal=',')[0]
    for _, r in t.iterrows():
        m = str(r["Municipio"]).strip()
        if m == "TOTAL":
            tot[pn] = {"h": num(r["Habitantes"]), "b": num(r["Bibliotecas"]), "pr": num(r["Préstamos presenciales"]),
                       "u": num(r["Usuarios inscritos"]), "v": num(r["Visitas"])}
            continue
        k = nz(m)
        p = porn.get(k) or porn.get(ALIAS.get(k, k)) or porn.get(re.sub(r"^(o|a|os|as) ", "", k))
        if not p or p["codigo_ine"][:2] != cp:
            raise SystemExit(f"sen casar: {m} ({pn})")
        c = {"id": p["codigo_ine"], "n": p["nome"], "pr": pn, "h": num(r["Habitantes"]), "b": num(r["Bibliotecas"])}
        if c["b"] and num(r["Préstamos presenciales"]) is not None:
            c.update(p_=num(r["Préstamos presenciales"]), u=num(r["Usuarios inscritos"]), v=num(r["Visitas"]),
                     col=num(r["Colección"]))
        conc.append(c)
ids = [c["id"] for c in conc]
assert len(set(ids)) == 313 == len(ids), len(set(ids))
for c in conc:
    if "p_" in c:
        c["p"] = c.pop("p_")
gal = {k: sum(t[k] for t in tot.values()) for k in ("h", "b", "pr", "u", "v")}
print(f"Galicia {ANO}: {gal['b']} bibliotecas · {gal['pr']:,} préstamos · {gal['pr'] / gal['h']:.2f} por habitante · "
      f"{gal['u'] / gal['h']:.1%} inscritos")
sen = [c for c in conc if not c["b"]]
nd = [c for c in conc if c["b"] and "p" not in c]
print("sen biblioteca:", len(sen), sum(c["h"] for c in sen), "hab. · con biblioteca e sen datos:", [c["n"] for c in nd])
o = sorted([c for c in conc if "p" in c], key=lambda c: -c["p"] / c["h"])
for c in o[:6] + o[-4:]:
    print(f"  {c['n']:24} {c['p'] / c['h']:.2f} préstamos/hab · {c['u'] / c['h']:.0%} inscritos · {c['h']} hab.")
conc.sort(key=lambda c: c["n"])
out = {"ano": ANO, "conc": conc, "prov": tot, "gal": gal}
(HERE / "data" / "datos.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok: data/datos.json", (HERE / "data" / "datos.json").stat().st_size // 1024, "KB")

#!/usr/bin/env python3
"""Xera v/espera-sergas/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "espera-sergas"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
mil = lambda v: f"{v:,.0f}".replace(",", ".")
fec = lambda s: "/".join(reversed(s.split("-")))
H = d["hosp"]
pts = [(h, s, v) for h, ss in H.items() for s, v in ss.items() if v["p"] >= 20]
lento = max(pts, key=lambda x: x[2]["t"])
rapido = min(pts, key=lambda x: x[2]["t"])
ult, ant = d["serie"][-1], d["serie"][-2]
tit = lambda s: s.capitalize().replace("xia", "xía").replace("loxia", "loxía")
SERV = {"TRAUMATOLOXIA": "traumatoloxía", "CIRURXIA MAXILOFACIAL": "cirurxía maxilofacial", "OTORRINOLARINGOLOXIA": "otorrino",
        "NEUROCIRURXIA": "neurocirurxía", "OFTALMOLOXIA": "oftalmoloxía", "DERMATOLOXIA": "dermatoloxía", "XINECOLOXIA": "xinecoloxía",
        "CIRURXIA XERAL E DIXESTIVA": "cirurxía xeral", "UROLOXIA": "uroloxía"}
def hn(h):
    """«C.H. UNIVERSITARIO DE SANTIAGO» → «no CHU de Santiago»; «H. PÚBLICO DE VALDEORRAS» → «no hospital de Valdeorras»."""
    n = h.replace("C.H. UNIVERSITARIO ", "").replace("H. PÚBLICO ", "").replace(" (concertado)", "").title()
    n = n.replace("De ", "de ", 1).replace("Da ", "da ", 1).replace("Do ", "do ", 1).replace("A Coruña", "da Coruña")
    return ("no CHU " if h.startswith("C.H.") else "no hospital ") + n
dek = (f"A {fec(d['data'])}, <b>{mil(ult[1])} persoas</b> agardaban por unha operación no Sergas, cunha espera media de "
       f"<b>{ult[2]:.0f} días</b>, {ult[2] - ant[2]:+.0f} en seis meses. Pero depende moito de onde e de que: "
       f"en {SERV.get(lento[1], tit(lento[1]))}, {hn(lento[0])}, a media é de {lento[2]['t']:.0f} días; en "
       f"{SERV.get(rapido[1], tit(rapido[1]))}, {hn(rapido[0])}, de {rapido[2]['t']:.0f}. Cada punto é un hospital; escolle o teu.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__CORTE__", fec(d["data"])))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: un enxame de puntos
random.seed(2)
COR = {"chu": "#2166ac", "com": "#1b9e77", "con": "#e08214"}
tipo = lambda h: "con" if "POVISA" in h else ("chu" if h.startswith("C.H.") else "com")
el = []
servs = sorted({s for _, s, _ in pts}, key=lambda s: -max(v["t"] for _, ss, v in pts if ss == s))[:8]
for i, s in enumerate(servs):
    for h, ss, v in pts:
        if ss == s:
            el.append(f'<circle cx="{40 + v["t"] / 160 * 520:.0f}" cy="{70 + i * 62 + random.uniform(-14, 14):.0f}" r="{4 + v["p"] ** .5 * .35:.1f}" '
                      f'fill="{COR[tipo(h)]}" stroke="#fff"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT)

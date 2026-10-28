#!/usr/bin/env python3
"""Xera v/estudos-rexions/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "estudos-rexions"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
A, R = d["anos"], d["rex"]
G = next(r for r in R if r["c"] == "ES11")
ES = [r for r in R if r["p"] == "España"]
f1 = lambda v: f"{v:.1f}".replace(".", ",")
pe = lambda lista, k, mellor_baixo: 1 + sum(1 for r in lista if (r[k][-1] < G[k][-1] if mellor_baixo else r[k][-1] > G[k][-1]))
ue, es = d["ue"], d["es"]
i0 = next(i for i in range(len(A)) if G["e"][i] is not None)
cmp_ue = lambda a, b, maior: ("por riba" if a > b else "por debaixo") if a != b else "igual"
dek = (f"En {A[-1]}, o <b>{f1(G['e'][-1])} %</b> dos mozos galegos de 18 a 24 anos deixara os estudos sen pasar da ESO, "
       f"menos da metade ca en {A[i0]} ({f1(G['e'][i0])} %)" if G["e"][-1] * 2 < G["e"][i0] else
       f"En {A[-1]}, o <b>{f1(G['e'][-1])} %</b> dos mozos galegos de 18 a 24 anos deixara os estudos sen pasar da ESO, "
       f"fronte ao {f1(G['e'][i0])} % de {A[i0]}")
dek += (f": é a {pe(ES, 'e', True)}ª comunidade con menos abandono das {len(ES)} con dato, aínda {cmp_ue(G['e'][-1], ue['e'][-1], False)} da media da UE ({f1(ue['e'][-1])} %). "
        f"E o <b>{f1(G['t'][-1])} %</b> dos de 25 a 34 anos ten estudos superiores, {cmp_ue(G['t'][-1], ue['t'][-1], True)} da media europea ({f1(ue['t'][-1])} %): "
        f"posto {pe(R, 't', False)} de {len(R)} rexións.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
page = (page.replace("__DATA__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__DEK__", dek)
        .replace("__A0__", str(A[0])).replace("__A1__", str(A[-1])).replace("__N__", str(len(R)))
        .replace("__ACT__", "/".join(reversed(d["actualizado"].split("-")))))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")

# Miniatura: a nube de puntos co camiño de Galicia
W, M = 600, 50
EMAX, TMIN, TMAX = 35, 10, 80
sx = lambda v: M + min(v, EMAX) / EMAX * (W - 2 * M)
sy = lambda v: M + (TMAX - v) / (TMAX - TMIN) * (W - 2 * M)
el = [f'<rect x="{sx(0):.0f}" y="{sy(TMAX):.0f}" width="{sx(9) - sx(0):.0f}" height="{sy(45) - sy(TMAX):.0f}" fill="#e8f1ea"/>']
for r in R:
    if r is G:
        continue
    c = "#7d828a" if r["p"] == "España" else "#cfcbc1"
    el.append(f'<circle cx="{sx(r["e"][-1]):.0f}" cy="{sy(r["t"][-1]):.0f}" r="{9 if r["p"] == "España" else 7}" fill="{c}" stroke="#fff" stroke-width="1.5"/>')
pts = [(sx(e), sy(t)) for e, t in zip(G["e"], G["t"]) if e is not None and t is not None]
el.append('<path d="M' + "L".join(f"{x:.0f},{y:.0f}" for x, y in pts) + '" fill="none" stroke="#c2185b" stroke-width="4" opacity=".6" stroke-linejoin="round"/>')
el.append(f'<circle cx="{pts[-1][0]:.0f}" cy="{pts[-1][1]:.0f}" r="16" fill="#c2185b" stroke="#fff" stroke-width="3"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT)
print(dek)

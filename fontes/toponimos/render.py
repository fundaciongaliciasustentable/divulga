#!/usr/bin/env python3
"""Xera v/toponimos/index.html e thumb.svg desde data/datos.json.

Pasos completos:  python3 prep.py  →  python3 render.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "v" / "toponimos"

d = json.loads((HERE / "data" / "datos.json").read_text(encoding="utf-8"))
mil = lambda v: f"{v:,.0f}".replace(",", ".")
T = d["top"]
R = d["R"]
B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
IX = {c: i for i, c in enumerate(B64)}


def nconc(s):
    k, cs = 0, set()
    while k < len(s):
        cs.add(s[k:k + 2])
        k += 3 + 3 * IX[s[k + 2]]
    return len(cs)


a, b, c = T[0], T[1], T[2]
var0 = f" (ou {R[0][2][0][0]})" if len(R[0]) > 2 and R[0][2] else ""
dek = (f"No Nomenclátor de {d['ano']} hai {mil(d['n'])} aldeas, lugares e barrios con nome propio. "
       f"<b>{mil(a[1])}</b> chámanse {a[0]}{var0}, en {nconc(R[0][1])} concellos; "
       f"<b>{mil(b[1])}</b>, {b[0]}, e {mil(c[1])}, {c[0]}. Detrás veñen {T[3][0]}, {T[4][0]}, {T[5][0]} e {T[6][0]}: "
       f"a paisaxe, a casa e a parroquia feitas nome. Escolle un topónimo ou busca o teu concello.")
page = (HERE / "viz.tpl.html").read_text(encoding="utf-8")
rep = {"__DATA__": json.dumps(d, ensure_ascii=False, separators=(",", ":")), "__DEK__": dek, "__ANO__": str(d["ano"]),
       "__N__": mil(d["n"]), "__SEN__": mil(d["sencoord"]), "__SENP__": f"{d['sencoord'] / d['n'] * 100:.0f} %",
       "__UNICAS__": mil(d["unicas"])}
for k, v in rep.items():
    page = page.replace(k, v)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")


# Miniatura: o mosaico das raíces, coa primeira en maxenta
def squarify(vals, x, y, w, h):
    out, tot = [], sum(vals)
    rest = [v * w * h / tot for v in vals]
    while rest:
        short, row, best = min(w, h), [], float("inf")
        for a_ in rest:
            t = row + [a_]
            s = sum(t)
            r = max(short * short * max(t) / (s * s), s * s / (short * short * min(t)))
            if r <= best:
                best, row = r, t
            else:
                break
        s = sum(row)
        if w >= h:
            rw, yy = s / h, y
            for a_ in row:
                out.append((x, yy, rw, a_ / rw))
                yy += a_ / rw
            x, w = x + rw, w - rw
        else:
            rh, xx = s / w, x
            for a_ in row:
                out.append((xx, y, a_ / rh, rh))
                xx += a_ / rh
            y, h = y + rh, h - rh
        rest = rest[len(row):]
    return out


cel = squarify([t[1] for t in T[:40]], 30, 30, 540, 540)
mx, mn = T[0][1], T[39][1]
el = []
for i, (x, y, w, h) in enumerate(cel):
    t = ((T[i][1] - mn) / (mx - mn)) ** .5
    col = "#c2185b" if i == 0 else "#%02x%02x%02x" % tuple(round(a_ + (b_ - a_) * t) for a_, b_ in ((236, 214), (233, 206), (224, 190)))
    el.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{col}" stroke="#fbfaf7" stroke-width="4"/>')
(OUT / "thumb.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
                               f'<rect width="600" height="600" fill="#fbfaf7"/>{"".join(el)}</svg>', encoding="utf-8")
print("ok:", OUT, (OUT / "index.html").stat().st_size // 1024, "KB")
print(dek)

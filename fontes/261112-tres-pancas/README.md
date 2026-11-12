# As tres pancas

Os datos van no propio `v/261112-tres-pancas/index.html` (constante `D`);
para actualizalos edítanse alí a man. A miniatura `thumb.svg` é un debuxo á
parte, non xerado desde `D`.

`datos.json` nesta carpeta é unha **instantánea sincronizada** dese bloque —
para ter unha fonte lexible e versionada á parte do HTML, non para
rexenerar a páxina. Ao editar os datos na páxina, actualiza tamén este
ficheiro a man.

## Fonte

Comisión EAT-Lancet, «Dietas saudables a partir de sistemas alimentarios
sostibles» (informe resumido de 2019, táboas 3, 4 e 5), a partir de
Willett e outros, *The Lancet*, 2019.
<https://doi.org/10.1016/S0140-6736(18)31788-4>

Proxeccións dun modelo global para 2050 (~10.000 millóns de persoas), non
predicións. A edición de 2025 da Comisión (once modelos) chega á mesma
conclusión pero non publica a táboa de combinacións; por iso as cifras
seguen sendo as de 2019.

`D.limites` ten, por presión (clima, terra, auga, nitróxeno, fósforo,
biodiversidade): `lim` (límite central), `lo`/`hi` (rango de incerteza) e
`b2010` (valor de partida; a biodiversidade leva un rango, `b2010r`, en vez
dunha cifra). `D.esc` ten as 12 combinacións posibles das tres pancas
(produción × desperdicio × dieta), chave `"<produción><desperdicio><dieta>"`
(0/1/2 cada unha, agás desperdicio e dieta que son 0/1), valor = as seis
magnitudes na orde de `D.limites`. No nitróxeno úsase o rango da táboa 3
(65–130); a táboa 5 escribe 140 e ningún escenario cae entre ambas cifras.

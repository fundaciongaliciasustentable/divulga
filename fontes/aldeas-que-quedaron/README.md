# As aldeas que quedaron sen ninguén (`v/aldeas-que-quedaron/`)

Voo de cámara sobre os lugares de Galicia que pasaron a ter cero habitantes desde 2000.

## Rexenerar

```bash
cd fontes/aldeas-que-quedaron
python3 prep.py      # precisa numpy e tifffile; descarga en data/raw/ o que falte
python3 render.py    # v/aldeas-que-quedaron/index.html e datos.json
```

- `prep.py` escribe `v/aldeas-que-quedaron/capas/*.geojson`, `v/aldeas-que-quedaron/thumb.svg`
  e `cifras.json` (todas as cifras calculadas, para contrastar co texto).
- `render.py` pega `.dv-bar` e `.dv-foot` de `v/galicia-cero-neto/`, cambia a licenza do pé a
  CC BY-SA 4.0 e extrae as paradas do modelo a `datos.json` (sempre sincronizado co HTML).
- `data/raw/` (Nomenclátor do INE e táboas do IGE, ~32 MB) non vai ao git.
- Precisa a copia local de Mapas Galicia Sustentable en `~/Proxectos/mapasgs/site/public/data/`
  e o MDT de `fontes/terreo/data/raw/`.

## Fontes e cálculo de cada cifra

Consultas feitas o 4/11/2026.

| Cifra | Fonte | Cálculo |
|---|---|---|
| 1.960 lugares a 0 en 2025; 1.064 en 2000; 30.518 entidades en 2025 | INE, Nomenclátor, `https://www.ine.es/nomen_files/nacional/es/Nacional_{2000,2025}.zip` (membros `Nomdef2000`, Latin-1, e `Nomdef2025_sex.txt`, UTF-8) | Entidades singulares de Galicia (código de 11 cifras rematado en `00` pero non en `0000`, provincias 15, 27, 32, 36) con total 0. Coincide coa ficha `ine-nomenclator` de `mapasgs/pipeline/sources.yaml`. |
| 1.072 lugares con veciños en 2000 e ningún en 2025; 579 Lugo, 314 A Coruña, 93 Ourense, 86 Pontevedra; ranking de concellos (Ortigueira 60, Muras 36, As Pontes e Ourol 35, O Valadouro 31) | Capa `aldeas-baleiras` de Mapas Galicia Sustentable (cálculo FGS sobre os 26 nomenclátores 2000–2025), foto do 3/11/2026 | `pob == 0` e `pob_2000 > 0`. Cos ficheiros en bruto e o mesmo código saen 1.062; os 10 restantes son de Oza-Cesuras, que a capa segue polo nome ata Oza e Cesuras. 1.030 teñen posición (IET). |
| Ano «baleiro desde» de cada aldea | Mesma capa | Primeiro ano da serie de ceros que chega a 2025 (`baleira_desde`); todas as aldeas destacadas teñen `rexurdiu = false`. As poboacións de 2000 e 2025 comprobáronse nos ficheiros do INE (`cifras.json` → `ine.aldeas`). |
| Mediana de habitantes por entidade (Lugo 7, Ourense 16, Pontevedra 31); 6.159 lugares de 1 a 5 hab. (3.041 en Lugo); porcentaxe a cero por provincia (Pontevedra 171/6.262 = 2,7 %; Lugo 928/9.846 = 9,4 %) | INE, Nomenclátor 2025 | Cálculo FGS sobre as entidades singulares. |
| Entidades por concello, a cero, de 1 a 5 hab., suma de habitantes (p. ex. Folgoso do Courel: 47 entidades, 924 hab.) | Capa `aldeas-baleiras` (cifras do Nomenclátor 2025) | Agrupación polas 5 primeiras cifras do código. |
| Poboación dos concellos nos censos 1900–2021 (p. ex. Ortigueira 23.845 en 1940 e 5.629 en 2021) | Capa `poboacion-seculo` (INE, *Alteraciones de los municipios en los Censos de Población desde 1842*, `https://www.ine.es/intercensal/`, harmonizado aos concellos actuais pola FGS), CC BY 4.0 | Lectura directa. Celanova −46 % (10.393 → 5.646) e Folgoso do Courel −85 % (6.749 → 988), 1940–2021: cálculo FGS. |
| Nacementos e defuncións 2015–2024 por concello | IGE, `https://www.ige.gal/igebdt/igeapi/csv/datos/57` (nacementos por concello de residencia da nai) e `.../datos/30` (defuncións por concello de residencia), fila «Total» | Suma de 2015 a 2024 (2025 é provisional). Coinciden coa capa `nacementos-mortes`. |
| Distancia ao centro de saúde (p. ex. Peliceira 14 km) | Capa `distancia-servizos` (cálculo FGS: liña recta, haversine, ao centro de saúde ou consultorio do SERGAS máis próximo; SERGAS conxunto 0253 e IET), CC BY-SA 4.0 | Unión polo código de 11 cifras. Non é distancia por estrada. |
| Altitude de cada aldea (p. ex. Peliceira 1.154 m) | IGN, MDT de 25 m (PNOA-LiDAR), WCS INSPIRE `Elevacion4258_25`, en `fontes/terreo/data/raw/`, CC BY 4.0 | Valor da cela que contén o punto IET da aldea. |

## Capas da peza (`v/aldeas-que-quedaron/capas/`)

- `baleiras.geojson`: dous MultiPoint, `t = despois` (con veciños en 2000, a 0 en 2025; 1.030
  puntos) e `t = antes` (xa a 0 en 2000 e aínda en 2025; 624 puntos dos 645).
- `quedan.geojson`: MultiPoint das entidades con 1–5 habitantes en 2025 que teñen posición.
- `aldeas.geojson`: as oito aldeas destacadas.
- `concellos.geojson`: contornos simplificados (Douglas-Peucker, 0,0006°) dos concellos das paradas,
  da capa `concellos-parroquias` (IET).

## Licenza

CC BY-SA 4.0: a peza usa capas CC BY-SA de Mapas Galicia Sustentable (`aldeas-baleiras`,
`distancia-servizos`, `concellos-parroquias`, posicións do IET).

## Advertencias

- Desde 2024 o INE dá as cifras do Nomenclátor a partir do Censo anual, non do Padrón. Algúns
  lugares pasan a 0 en 2025 dun salto (p. ex. A Barreira e Os Canedos, en Carballo, con 51 e 43 habitantes en 2000 e o seu único cero en 2025);
  por iso as aldeas destacadas son das que baixaron pouco a pouco e levan anos a cero.
- Un «lugar a cero» é unha entidade singular sen habitantes empadroados/recensados: pode ter
  casas de segunda residencia ou uso agrario.

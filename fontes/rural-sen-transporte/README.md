# Ata onde chega o bus (`rural-sen-transporte`)

Voo de cámara (scrollytelling 3D) sobre o transporte público en Galicia: todos os
autobuses da Xunta e todos os trens de Renfe dun **mércores laborable (4/11/2026)** e
dun **domingo (8/11/2026)**, as comarcas sen tren e os lugares que quedan lonxe dun
hospital. Motor común: `assets/js/voo.js`.

## Rexenerar

```bash
pip install shapely numpy tifffile          # ou o venv con estes paquetes
python3 fontes/rural-sen-transporte/prep.py  # capas en v/rural-sen-transporte/capas/ e cifras.json
python3 fontes/rural-sen-transporte/render.py  # index.html e datos.json
python3 fontes/rural-sen-transporte/thumb.py   # thumb.svg (precisa shapely)
```

`prep.py` le a copia local de Mapas Galicia Sustentable (`~/Proxectos/mapasgs/site/public/data/`)
e descarga `pulso-bus` da web pública se non está en `data/raw/` (en local non hai
`data.geojson` desa capa: a súa descarga do NAP precisa chave). `data/raw/` non vai ao git.
`cifras.json` garda todas as cifras calculadas que cita o texto.

## Datos de entrada (consultados o 4/11/2026)

| Capa / fonte | Que se usa | Licenza |
|---|---|---|
| `pulso-bus` — https://mapas.galiciasustentable.org/data/pulso-bus/data.geojson (publicada o 30/10/2026, descargada o 3/11/2026) | 11.963 viaxes de bus da Xunta: 10.258 o mércores 4/11 e 1.705 o domingo 8/11, como liña recta entre paradas coa hora en cada unha | Licenza de datos abertos do MITRAMS (NAP, conxunto 1386); «Powered by MITRAMS» |
| `buses-xunta` (local, publicada o 23/10/2026) | 25.118 paradas | Idem |
| `pulso-tren` e `estacions-tren` (local, 1/11/2026) | 178 viaxes de tren o mércores e 122 o domingo; 137 estacións con `servizos_dia` (mércores 4/11) | Renfe Operadora, CC BY 4.0 |
| `concellos-parroquias` (IET) | Límites dos 313 concellos | CC BY-SA 4.0 |
| `perfil-concellos` | Superficie de cada concello | CC BY-SA 4.0 |
| `distancia-servizos` (1/11/2026) | Distancia en liña recta ao hospital do SERGAS máis próximo desde 36.190 lugares (IET; poboación do padrón 2024) | CC BY-SA 4.0 |
| INE, Padrón a 1/1/2025 (táboas 2868, 2880, 2885, 2890), tal como está en `fontes/poboacion-galicia/data/datos.json` | Poboación por concello (Galicia 2.713.169) | INE |
| MDT 25 m do IGN, `fontes/terreo/data/raw/*.tif` | Alturas de lugares | CC BY 4.0 |
| Ogacli, a partir do inventario do MITECO (2024), vía `fontes/galicia-cero-neto/README.md` | Transporte: 5,03 de 16,59 Mt CO₂eq brutas (30,3 %), o primeiro sector | — |

## De onde sae cada cifra (todas en `cifras.json`, cálculo FGS salvo indicación)

- **10.258 / 1.705 viaxes de bus; 178 / 122 de tren**: número de elementos de `pulso-bus` e
  `pulso-tren` con `data` = 2026-11-04 / 2026-11-08. −83 % = 1 − 1.705/10.258.
- **58 concellos sen bus o domingo, 75.795 habitantes, 43 en Ourense**: concellos onde
  ningunha viaxe do domingo ten un vértice (parada) dentro do polígono do concello;
  poboación INE 2025. O mércores só Folgoso do Courel e Negueira de Muñiz quedan a 0.
- **Viaxes por concello** (Santiago 829, Ames 451, Ramirás 12, Navia de Suarna 5…): viaxes
  con algunha parada dentro do concello.
- **Corredores de tren** (A Coruña–Santiago 57, Santiago–Vigo Urzaiz 32, Lugo–Monforte 10,
  Monforte–Ourense 16, A Coruña–Lugo 4): viaxes do mércores que paran nas dúas estacións
  (vértice a menos de 0,003° da estación), contando unha vez os pares coa mesma hora nas
  dúas (o GTFS publica algúns trens acoplados como dúas viaxes, p. ex. Alvia + MD).
  Lugo–Monforte: 5 por sentido. Non se usan os `servizos_dia` da capa para as cifras do
  texto (non desduplican eses pares); só para o tamaño das estacións no mapa.
- **30,3 paradas por 1.000 hab.** = 4.375 paradas / 144.594 hab. nos 121 concellos de
  menos de 2.000 habitantes; **1,7** = 1.711 / 1.000.592 nos 7 de máis de 50.000 (estes
  teñen bus urbano, que non está no GTFS da Xunta).
- **Comarca da Fonsagrada** (A Fonsagrada, Negueira de Muñiz, A Ribeira de Piquín; Decreto
  65/1997): 3.858 hab., 582,7 km² (suma de `superficie_km2`), 23 viaxes distintas o mércores
  e 4 o domingo con algunha parada na comarca. A Ribeira de Piquín: 2 viaxes, liña «IES
  Pedregal de Irimia-Barangón», 8:24 e 15:58.
- **Negueira de Muñiz**: 236 hab., 3 paradas, 0 viaxes os dous días; 26 lugares, mediana
  53,1 km ao hospital; Escanlar 58,7 km, o máximo dos 36.190 lugares (1 habitante no
  padrón 2024).
- **Navia de Suarna**: liña «Navia de Suarna-Hospital HULA»: sae da parada A Pobra de Navia
  ás 7:15 e chega ao HULA ás 8:55 (1 h 40 min); do HULA saen viaxes ás 12:15 e 18:15.
  Murias de Rao (26 hab. en 2024): 727 m no MDT; a Pobra (parada), 296 m; 11,7 km en liña
  recta entre os dous puntos.
- **Folgoso do Courel**: 921 hab., 6 paradas (liñas Quiroga–Seoane do Courel e Seoane do
  Courel–Pedrafita do Cebreiro segundo `buses-xunta`), 0 viaxes o mércores e o domingo;
  50 lugares, mediana 26,05 km ao hospital; Teixeira 34,2 km e 1.141 m no MDT.
- **4.533 lugares a máis de 30 km** do hospital (517 a máis de 40), mediana galega 16,4 km;
  2.501 na provincia de Lugo (Vilalba 586, Ortigueira 581, A Fonsagrada 262…), máis A
  Caniza, Arbo, Crecente (Paradanta) e Lobios, Bande (Baixa Limia).
- **Alturas**: valor do píxel do MDT de 25 m no punto do lugar.

## Capas da peza (`v/rural-sen-transporte/capas/`)

- `bus.geojson`, `bus-domingo.geojson`: rede xeneralizada. As paradas axústanse a unha
  grella de 0,025° (~2–3 km) para que a capa pese < 200 KB; cada tramo entre celas veciñas
  leva as viaxes distintas que o percorren e fúndense en MultiLineString por clase
  (`c` 0–4: 1–3, 4–10, 11–30, 31–100, >100 viaxes).
- `tren.geojson`: tramos entre estacións consecutivas co número de trens distintos (`n`).
- `estacions.geojson`: `s` = servizos ao día (capa `estacions-tren`).
- `concellos.geojson`: polígonos simplificados con `b` (viaxes de bus do mércores), `d`
  (do domingo) e `p` (paradas por 1.000 hab.).
- `lonxe.geojson`: lugares a máis de 30 km do hospital, en tres MultiPoint (`c` 0–2).
- `paradas-montana.geojson`: paradas das comarcas da Fonsagrada, Os Ancares e Quiroga con
  `v` = viaxes do mércores.

## Advertencias

- Horarios programados (GTFS), non circulacións reais. Non inclúen buses urbanos nin
  servizos á demanda sen horario publicado; as liñas son rectas entre paradas.
- As distancias son en liña recta: por estrada son maiores, moito na montaña.
- As rutas escolares integradas na rede da Xunta aparecen como viaxes (p. ex. Cervantes,
  A Ribeira de Piquín).
- A cifra de emisións non se reverificou na fonte: tómase da peza `galicia-cero-neto`.

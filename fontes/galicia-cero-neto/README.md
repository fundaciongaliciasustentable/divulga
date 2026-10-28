# Galicia cero neto

Adaptación galega de «How to get the USA to Net Zero Carbon» (David McCandless,
Information is Beautiful, 2022). Os datos van no propio
`v/galicia-cero-neto/index.html` (constantes `SECTORS`, `SINK`, `ROADMAP`);
para actualizalos edítanse alí a man. A miniatura `thumb.svg` debúxase cos
mesmos valores de 2024.

`datos.json` nesta carpeta é unha **instantánea sincronizada** dese bloque —
para ter unha fonte lexible e versionada á parte do HTML, non para rexenerar a
páxina (non hai script que a lea). Ao editar os datos na páxina, actualiza
tamén este ficheiro a man (ou cun script curto que o extraia do `<script>` con
Node, como se fixo para crealo).

## Datos de partida (2024)

- Emisións brutas 16,59 Mt CO2eq e netas 7,02 Mt: Ogacli (ogacli.org), a partir
  do inventario do MITECO. Sumidoiro LULUCF = brutas − netas ≈ 9,58 Mt.
- Sectores: transporte 30,3 % (5,03 Mt); enerxía 11,1 % (1,84 Mt: térmicas
  0,82 + refino 1,01 segundo EU ETS 2024); industria non enerxética 2,44 Mt;
  agricultura 3,69 Mt (1990 × 1,178); residuos 0,58 Mt (1990 × 0,778);
  edificios e sector primario calculado por diferenza (3,02 Mt).
- Lumes de 2025 ≈ 9,6 Mt (Copernicus, citado polo Ogacli).
- Potencia: REE balance Galicia 2025 (82 % renovable) e INEGA xuño 2026
  (eólica 3.987 MW).
- Turismos eléctricos 2025: 3.564 (11,7 % das vendas), DGT vía
  autonomiacocheselectricos.es. Recarga pública: 2.040 puntos (barómetro, out. 2025).
- Lei 1/2026, do 5 de febreiro, do clima de Galicia: neutralidade en 2040 e
  −75 % de emisións netas en 2030 respecto de 1990 (1990 netas = 23,69 Mt).

## Estimacións FGS (2030 e 2040)

Parte proporcional galega (5,6 % da poboación española) dos obxectivos do
PNIEC 2023-2030 (5,5 M eléctricos; 1,38 M vivendas rehabilitadas) e senda
lineal cara á neutralidade de 2040. Non son previsións oficiais e na páxina
van subliñadas con punteado.

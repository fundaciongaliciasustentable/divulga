# solo-galicia · O solo galego en detalle

Cartograma deseñado para o sitio vello de AGADER (maio de 2026), trasladado a Divulga e corrixido con datos oficiais o 6 de novembro de 2026. O deseño (silueta, zonas en onda, provincias, cadro de gráficas con Chart.js 4.4.1 incrustado) é o orixinal; as cifras e os textos que dependían delas cambiaron.

| Ficheiro | Que é |
|---|---|
| `orixinal.html` | Copia exacta de `AGADER/web_v1/cartograma-solo.html`, coas cifras antigas |
| `datos_oficiais.json` | Os datos oficiais, coa fonte e a URL de cada bloque |
| `corrixir.py` | Aplica os datos: zonas dos mapas, lendas, textos, gráficas e nota metodolóxica. Se o orixinal cambia e unha frase xa non se atopa, para |
| `xeometria.py` | Reparte cada silueta en zonas de área exacta con fronteiras en onda (precisa `shapely`) |
| `adaptar.py` | Xera `v/solo-galicia/index.html`, `thumb.svg` e `datos.json`: chama a `corrixir.py` e pon a cabeceira e o pé de Divulga |
| `_chrome_bar.html`, `_chrome_foot.html` | Barra e pé comúns de Divulga, copiados de `v/vacas-persoas/` |
| `datos.json` | As cifras que mostra a peza xerada |

```bash
pip install shapely
python3 fontes/solo-galicia/adaptar.py
python3 scripts/og_pezas.py <PlayfairDisplay-VariableFont_wght.ttf> <Lato-Regular.ttf> solo-galicia   # Pillow e cairosvg
python3 build.py
```

## Fontes

- **Usos do solo, Galicia e provincias:** MAPA, Anuario de Estatística 2025, táboa 3.3 (datos de 2024). É a única fonte oficial coas mesmas categorías para Galicia e as catro provincias. «Artificial e auga» é a súa categoría «outras superficies»: usos urbanos e artificiais, augas e humidais. A comparación con España sae da táboa 3.2.
- **Artificial por si só (2,76 %) e monte arborado (máis do 67 %):** 4º Inventario Forestal Nacional e IFCG 2024, na memoria do PLADIGA 2026 (Xunta), táboa 5, p. 39.
- **Cortas de madeira 2025 por provincia:** Xunta e Universidade de Vigo, *A cadea forestal-madeira de Galicia 2025*. Os metros cúbicos por hectárea de monte son cálculo da FGS con esas cortas e a superficie forestal do MAPA.
- **Peso do sector (1,7 % do PIB, máis de 19.400 afiliados en 2025):** nota da Xunta do 19/05/2026 sobre ese informe.
- **Terra abandonada (máis de 500.000 ha):** AGADER, presentación xeral da Lei 11/2021.

## Que cambiou respecto do orixinal

| Orixinal | Agora | Por que |
|---|---|---|
| Forestal 73 %, agrario 22 %, artificial 3 %, auga ~1,5 % | Forestal 61,9 %, agrario 28,3 %, artificial e auga 9,8 % | O orixinal mesturaba IFN, ESYRCE e SIOSE e repartía a man un residuo do 5,5 % |
| 35,7 % do agrario sen aproveitamento (297.170 ha), 7,9 % en España | 5,4 % non utilizado (44.825 ha), 4,1 % en España; máis de 500.000 ha abandonadas segundo AGADER | A cifra vía dun informe privado (Cocampo 2025) e non cadraba co mapa. O texto explica agora por que a estatística só ve unha parte do abandono: o resto xa conta como monte |
| Provincias «estimación FGS» | Provincias do MAPA | Lugo resulta a provincia máis agraria (34 %), non A Coruña |
| Cortas: A Coruña 44,1 %, Lugo 37,4 %, Pontevedra 13,4 %, Ourense 5,1 % | 39,7 / 35,3 / 12,2 / 12,7 %, e m³ por hectárea de monte | Ourense corta máis volume ca Pontevedra, pero é a que menos corta por hectárea (2,6 m³ fronte a 9,5 na Coruña): o paradoxo mantense medido así |
| 32,4 % de importación de alimentos e déficit de 302 M€ | Retirado | Sen fonte localizable |
| Monte que rende 1 m³/ha fronte a 8-9 | Retirado | Lectura errada do Plan Forestal (1,3 m³/ha só en montes en convenio, 2018) |
| 1,6 % do PIB e 25.000 empregos | 1,7 % do PIB e máis de 19.400 afiliados (2025) | Dato oficial máis recente |

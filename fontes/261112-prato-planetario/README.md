# O prato planetario

Os datos van no propio `v/261112-prato-planetario/index.html` (constante
`D`); para actualizalos edítanse alí a man. A miniatura `thumb.svg` é un
debuxo á parte, non xerado desde `D`.

`datos.json` nesta carpeta é unha **instantánea sincronizada** dese bloque —
para ter unha fonte lexible e versionada á parte do HTML, non para
rexenerar a páxina. Ao editar os datos na páxina, actualiza tamén este
ficheiro a man.

## Fontes

- **Dieta de saúde planetaria**: Comisión EAT-Lancet 2025, resumo, figura 1
  (gramos ao día e rango por grupo para un adulto medio, ~2.400 kcal).
  <https://eatforum.org/eat-lancet/summary-report/>
- **Consumo dos fogares**: MAPA, Panel de consumo alimentario nos fogares,
  series anuais 2025 por comunidade autónoma (quilos por persoa e ano,
  pasados aquí a gramos ao día).
  <https://www.mapa.gob.es/es/alimentacion/temas/consumo-tendencias/panel-de-consumo-alimentario/series-anuales>

`D.consumo` ten, por grupo, `gal` e `esp` (gramos/día), `posto` (posto de
Galicia entre as 17 comunidades, de máis a menos consumo) e as comunidades
`primeira`/`ultima`. Non son magnitudes idénticas ao obxectivo: o panel mide
o que se merca, co seu óso/pel/casca, deixa fóra a hostalaría e reparte
entre toda a poboación — ver a nota ao pé da propia peza para o detalle
completo (cereais integrais, azucre e equivalencias de lácteos/legumes
quedan fóra da comparación directa).

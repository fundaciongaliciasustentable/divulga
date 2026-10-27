# habelos-hainos

Esta peza non ten `prep.py`/`render.py`: os 17 mitos (array `MITOS`, cos
identificadores estables `IDS`) viven embebidos e edítanse a man en
`v/habelos-hainos/index.html`.

`datos.json` nesta carpeta é unha **instantánea sincronizada** dese bloque
(cada mito xa co seu `id`) — para ter unha fonte lexible e versionada á parte
do HTML, non para rexenerar a páxina. Ao editar ou engadir un mito na páxina,
actualiza tamén este ficheiro a man.

Os identificadores (`id`) teñen que coincidir sempre cos de `api/votos.php`,
que é onde se gardan os votos «Críaste este mito?».

Fontes: AEMET, MeteoGalicia, IGE, INEGA, Xunta de Galicia, ICCT e outras,
enlazadas en cada mito (campo `src`).

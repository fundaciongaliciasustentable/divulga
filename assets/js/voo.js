/* Divulga · motor común dos voos de cámara (scrollytelling sobre relevo 3D)
 *
 * Instrucións completas: mapasgs/docs/divulga-voos-de-camara.md
 *
 * Na peza:
 *   <main class="voo"><div class="voo-mapa" aria-hidden="true"></div>
 *     <div class="voo-pasos">
 *       <section class="paso" data-centro="lon,lat" data-zoom="11" data-inclinacion="60"
 *                data-rumbo="-20" data-capa="focos,perimetros"
 *                data-marca="-9.27,42.88|Monte Facho;-9.20,42.90|Fisterra">…</section>
 *   …
 *   <script src="../../assets/vendor/pmtiles-4.5.0/pmtiles.js"></script>
 *   <script type="module">
 *     import { iniciarVoo } from '../../assets/js/voo.js';
 *     iniciarVoo({ capas: [{ id: 'focos', fonte: 'capas/focos.geojson',
 *                            estilos: [{ type: 'circle', paint: { 'circle-color': '#e4572e' } }] }] });
 *   </script>
 *
 * Opcións de iniciarVoo:
 *   capas        [{ id, fonte (URL ou obxecto GeoJSON), estilos: [especificación de capa
 *                  MapLibre sen id nin source], atribucion? }]
 *   atribucion   texto extra para o control de atribución
 *   exaxeracion  relevo (1.5 por defecto)
 *   mascara      true: escurece o que queda fóra de Galicia (por defecto true)
 *   contorno     true: liña do límite de Galicia (por defecto true)
 *   relevo       { cores: [altura, cor, …] } para cambiar a cor por altitude
 *   aoCargar(map)        tras cargar o estilo e as capas
 *   aoPaso(paso, map)    cada vez que entra un paso (despois de mover a cámara)
 *
 * Cada paso acende só as capas de data-capa (fundido de 0,8 s) e as etiquetas de
 * data-marca. Co movemento reducido a cámara salta sen voar e sen xiro.
 */
import * as maplibregl from '../vendor/maplibre-gl-6.14.0/maplibre-gl.mjs';

const RAIZ = new URL('../../', import.meta.url).href;
const OPACIDADE = {
  circle: ['circle-opacity', 'circle-stroke-opacity'],
  line: ['line-opacity'],
  fill: ['fill-opacity'],
  'fill-extrusion': ['fill-extrusion-opacity'],
  heatmap: ['heatmap-opacity'],
  raster: ['raster-opacity'],
};
const CORES_RELEVO = [0, '#0e1418', 1, '#1f2a22', 200, '#2c3a2b', 500, '#3f4a33',
  900, '#5a5a3e', 1300, '#7a6e52', 1700, '#a39478'];

let protocolo = false;

export function iniciarVoo(op = {}) {
  if (!protocolo) {
    maplibregl.setWorkerUrl(`${RAIZ}assets/vendor/maplibre-gl-6.14.0/maplibre-gl-worker.mjs`);
    maplibregl.addProtocol('pmtiles', new pmtiles.Protocol().tile);
    protocolo = true;
  }
  const contedor = document.querySelector('.voo-mapa');
  const pasos = [...document.querySelectorAll('.paso')];
  const terreo = `pmtiles://${RAIZ}assets/terreo/galicia-terreo.pmtiles`;
  const quieto = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const atribs = ['© Instituto Geográfico Nacional, MDT (PNOA-LiDAR) e contorno, CC BY 4.0'];
  if (op.atribucion) atribs.push(op.atribucion);

  const marxe = () => (innerWidth > 700
    ? { left: Math.min(460, innerWidth * 0.4), right: 0, top: 0, bottom: 0 }
    : { left: 0, right: 0, top: 0, bottom: Math.round(innerHeight * 0.42) });
  const camara = (d) => ({
    center: d.centro.split(',').map(Number),
    // data-zoom-movil (opcional): zoom propio en pantallas estreitas, para vistas xerais
    zoom: innerWidth <= 700 && d.zoomMovil ? +d.zoomMovil : +d.zoom,
    pitch: +(d.inclinacion ?? 55),
    bearing: +(d.rumbo ?? 0),
    padding: marxe(),
  });

  const map = new maplibregl.Map({
    container: contedor,
    style: {
      version: 8,
      sources: {
        terreo: { type: 'raster-dem', url: terreo, encoding: 'mapbox', tileSize: 256, attribution: atribs.join(' · ') },
        sombra: { type: 'raster-dem', url: terreo, encoding: 'mapbox', tileSize: 256 },
        contorno: { type: 'geojson', data: `${RAIZ}assets/terreo/galicia-contorno.geojson` },
        fora: { type: 'geojson', data: `${RAIZ}assets/terreo/galicia-fora.geojson` },
      },
      layers: [
        { id: 'fondo', type: 'background', paint: { 'background-color': '#0e1012' } },
        { id: 'altitude', type: 'color-relief', source: 'sombra', paint: {
          'color-relief-color': ['interpolate', ['linear'], ['elevation'], ...(op.relevo?.cores ?? CORES_RELEVO)] } },
        { id: 'relevo', type: 'hillshade', source: 'sombra', paint: {
          'hillshade-exaggeration': 0.55, 'hillshade-shadow-color': '#000000',
          'hillshade-highlight-color': '#f2f0e8', 'hillshade-accent-color': '#0e1012' } },
        ...(op.mascara === false ? [] : [{ id: 'fora', type: 'fill', source: 'fora',
          paint: { 'fill-color': '#0e1012', 'fill-opacity': 0.55 } }]),
        ...(op.contorno === false ? [] : [{ id: 'contorno', type: 'line', source: 'contorno',
          paint: { 'line-color': '#f2f0e8', 'line-opacity': 0.35, 'line-width': 1 } }]),
      ],
    },
    ...camara(pasos[0].dataset),
    interactive: false,
    maxPitch: 80,
    pixelRatio: Math.min(2, devicePixelRatio),
    attributionControl: { compact: true },
  });

  // capas da peza: engádense escondidas (opacidade 0) e acéndense por paso
  const obxectivo = new Map();   // id de capa MapLibre → [[propiedade, valor], …]
  const grupos = new Map();      // id da capa da peza → [ids MapLibre]
  map.on('load', () => {
    map.setTerrain({ source: 'terreo', exaggeration: op.exaxeracion ?? 1.5 });
    // créditos pechados (botón «i»): abertos tapaban a parte baixa dos cadros
    const attrib = contedor.querySelector('.maplibregl-ctrl-attrib');
    attrib?.classList.remove('maplibregl-compact-show');
    attrib?.removeAttribute('open');
    for (const c of op.capas ?? []) {
      const datos = typeof c.fonte === 'string' ? new URL(c.fonte, location.href).href : c.fonte;
      map.addSource(c.id, { type: 'geojson', data: datos, attribution: c.atribucion });
      const ids = [];
      (c.estilos ?? []).forEach((e, i) => {
        const id = `${c.id}-${i}`;
        const paint = { ...(e.paint ?? {}) };
        const props = (OPACIDADE[e.type] ?? []).map((p) => [p, paint[p] ?? 1]);
        for (const [p] of props) { paint[p] = 0; paint[`${p}-transition`] = { duration: 800 }; }
        map.addLayer({ ...e, id, source: c.id, paint });
        obxectivo.set(id, props);
        ids.push(id);
      });
      grupos.set(c.id, ids);
    }
    op.aoCargar?.(map);
    if (actual) acender(actual.dataset.capa);
  });

  function acender(lista) {
    const on = new Set((lista ?? '').split(',').map((s) => s.trim()).filter(Boolean));
    for (const [g, ids] of grupos) {
      for (const id of ids) {
        for (const [p, v] of obxectivo.get(id)) map.setPaintProperty(id, p, on.has(g) ? v : 0);
      }
    }
  }

  let marcas = [];
  function etiquetas(texto) {
    marcas.forEach((m) => m.remove());
    marcas = (texto ?? '').split(';').map((s) => s.trim()).filter(Boolean).map((s) => {
      const [pos, nome] = s.split('|');
      const el = document.createElement('div');
      el.className = 'voo-marca';
      el.textContent = nome;
      return new maplibregl.Marker({ element: el, anchor: 'bottom' })
        .setLngLat(pos.split(',').map(Number)).addTo(map);
    });
  }

  let actual = null;
  let xiro = null;
  function ir(paso) {
    if (paso === actual) return;
    actual = paso;
    const d = paso.dataset;
    const c = camara(d);
    if (xiro) { map.off('moveend', xiro); xiro = null; }
    if (map.loaded()) acender(d.capa);
    etiquetas(d.marca);
    if (quieto) map.jumpTo(c);
    else {
      map.flyTo({ ...c, duration: +(d.duracion ?? 4000), curve: 1.2, essential: false });
      if (d.xiro !== '0') {
        xiro = () => { xiro = null; map.easeTo({ bearing: c.bearing + +(d.xiro ?? 16), duration: 14000, easing: (t) => t }); };
        map.once('moveend', xiro);
      }
    }
    op.aoPaso?.(paso, map);
  }

  const obs = new IntersectionObserver(
    (ent) => ent.filter((e) => e.isIntersecting).forEach((e) => ir(e.target)),
    { rootMargin: '-45% 0px -45% 0px' },
  );
  pasos.forEach((p) => obs.observe(p));
  addEventListener('resize', () => { if (actual) map.jumpTo(camara(actual.dataset)); });

  // ?paso=N abre directamente a parada N (0 = primeira), sen voo: para ligar
  // unha parada concreta e para as capturas de proba
  const n = Number(new URLSearchParams(location.search).get('paso'));
  if (n > 0 && pasos[n]) {
    const p = pasos[n];
    scrollTo(0, p.getBoundingClientRect().top + scrollY + p.offsetHeight / 2 - innerHeight / 2);
    actual = p;
    map.jumpTo(camara(p.dataset));
    etiquetas(p.dataset.marca);
    op.aoPaso?.(p, map);
  }
  window.__voo = map;
  return map;
}

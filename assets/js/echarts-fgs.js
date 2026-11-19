/* Envoltorio mínimo arredor de ECharts (assets/vendor/echarts-*) para as
 * pezas de Divulga que o precisan. Carga este script DESPOIS do propio
 * echarts.min.js e despois de divulga.css + viz-base.css.
 *
 * dvECharts.fontes()  → Promise que resolve cando as fontes web xa cargaron,
 *                       para que ECharts non calcule anchos de etiqueta coa
 *                       fonte de recambio e logo salte ao redimensionar.
 * dvECharts.init(el, opcions) → echarts.init(el, null, opcions); devolve a
 *                       instancia normal de ECharts (setOption, on, etc.),
 *                       coa propiedade extra `.dv` (ink, paper, muted,
 *                       display, num): os tokens de cor e tipografía que xa
 *                       define o :root da propia peza (--ink, --paper,
 *                       --muted, --gs-font-chart-display/num en viz-base.css),
 *                       lidos coa fonte resolta, para que a función option()
 *                       da peza non repita cores a man nin perda o tema
 *                       escuro/claro que cada peza xa escolleu.
 */
(function () {
  function fontes() {
    if (!('fonts' in document)) return Promise.resolve();
    return document.fonts.ready;
  }
  function tema(el) {
    const cs = getComputedStyle(el || document.documentElement);
    const v = (nome, respaldo) => cs.getPropertyValue(nome).trim() || respaldo;
    return {
      ink: v('--ink', '#1f2328'),
      paper: v('--paper', '#fbfaf7'),
      muted: v('--muted', '#5f636b'),
      display: v('--display', v('--gs-font-chart-display', 'sans-serif')),
      num: v('--num', v('--gs-font-chart-num', 'sans-serif')),
    };
  }
  function init(el, opcions) {
    const g = echarts.init(el, null, Object.assign({ renderer: 'svg' }, opcions));
    g.dv = tema(el);
    return g;
  }
  window.dvECharts = { fontes: fontes, init: init };
})();

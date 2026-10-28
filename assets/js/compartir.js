// Compartir/incrustar: engade un botón "Compartir" á barra (.dv-bar nav)
// de cada peza, cun panel con ligazón, código <iframe> e redes sociais.
// Un só ficheiro compartido por todas as pezas — nada que manter á man
// en cada unha.
(() => {
  const nav = document.querySelector('.dv-bar nav');
  if (!nav) return;

  const meta = (nome) => document.querySelector(`meta[property="${nome}"]`)?.content || '';
  const url = location.href.split(/[?#]/)[0];
  const titulo = meta('og:title') || document.title;
  const descricion = meta('og:description') || '';
  const embed = `<iframe src="${url}" width="100%" height="820" style="border:0;max-width:980px" loading="lazy" title="${titulo.replace(/"/g, '&quot;')}"></iframe>`;

  const redes = [
    ['X', `https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}&text=${encodeURIComponent(titulo)}`],
    ['Facebook', `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`],
    ['WhatsApp', `https://wa.me/?text=${encodeURIComponent(titulo + ' ' + url)}`],
    ['LinkedIn', `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`],
    ['Bluesky', `https://bsky.app/intent/compose?text=${encodeURIComponent(titulo + ' ' + url)}`],
  ];

  const caixa = document.createElement('div');
  caixa.className = 'dv-share-caixa';
  caixa.innerHTML = `
    <button type="button" class="dv-share" aria-haspopup="true" aria-expanded="false">Compartir</button>
    <div class="dv-share__panel" hidden>
      <h3>Ligazón</h3>
      <div class="dv-share__fila">
        <input type="text" readonly value="${url}" aria-label="Ligazón da peza">
        <button type="button" data-copiar="url">Copiar</button>
      </div>
      <h3>Incrustar nunha web</h3>
      <div class="dv-share__fila">
        <textarea readonly rows="3" aria-label="Código para incrustar">${embed}</textarea>
        <button type="button" data-copiar="embed">Copiar</button>
      </div>
      <h3>Redes sociais</h3>
      <p class="dv-share__redes">
        ${redes.map(([nome, href]) => `<a href="${href}" target="_blank" rel="noopener">${nome}</a>`).join('')}
      </p>
    </div>`;
  nav.appendChild(caixa);

  const boton = caixa.querySelector('.dv-share');
  const panel = caixa.querySelector('.dv-share__panel');

  function pechar() {
    panel.hidden = true;
    boton.setAttribute('aria-expanded', 'false');
  }
  boton.addEventListener('click', (ev) => {
    ev.stopPropagation();
    const abrir = panel.hidden;
    panel.hidden = !abrir;
    boton.setAttribute('aria-expanded', String(abrir));
  });
  document.addEventListener('click', (ev) => {
    if (!caixa.contains(ev.target)) pechar();
  });
  document.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape') pechar();
  });

  caixa.querySelectorAll('[data-copiar]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const campo = btn.previousElementSibling;
      const texto = campo.value;
      try {
        await navigator.clipboard.writeText(texto);
      } catch {
        campo.select();
        document.execCommand('copy');
      }
      const orixinal = btn.textContent;
      btn.textContent = 'Copiado';
      setTimeout(() => { btn.textContent = orixinal; }, 1500);
    });
  });
})();

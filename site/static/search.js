(function () {
  const input = document.getElementById('search-input');
  const resultsEl = document.getElementById('search-results');
  if (!input || !resultsEl) return;

  let index = null;
  let ready = false;
  let debounceTimer = null;

  const indexUrl = resultsEl.dataset.index || 'search_index.json';

  input.addEventListener('input', () => {
    if (!ready) return;
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      const query = input.value.trim().toLowerCase();
      if (!query) {
        resultsEl.innerHTML = '';
        return;
      }
      const terms = query.split(/\s+/);
      const hits = index.filter(item => {
        const text = ((item.title || '') + ' ' + (item.snippet || '')).toLowerCase();
        return terms.every(term => text.includes(term));
      }).slice(0, 20);

      if (!hits.length) {
        resultsEl.innerHTML = '<p>No results found.</p>';
        return;
      }

      const html = hits.map(hit => `
        <div class="search-result">
          <h3>${escapeHtml(hit.title || 'Untitled')}</h3>
          ${hit.table_name && hit.row_id != null ? `<p class="source-link">${escapeHtml(hit.table_name)} #${escapeHtml(String(hit.row_id))}</p>` : ''}
          <p>${escapeHtml(hit.snippet || '')}</p>
        </div>
      `).join('');
      resultsEl.innerHTML = html;
    }, 150);
  });

  (async function loadIndex() {
    try {
      const res = await fetch(indexUrl);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      index = await res.json();
      ready = true;
    } catch (err) {
      ready = false;
      resultsEl.innerHTML = '<p>Could not load search index.</p>';
    }
  })();

  function escapeHtml(str) {
    return str.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }
})();

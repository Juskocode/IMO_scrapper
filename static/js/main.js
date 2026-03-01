import { getListings, getStats } from './apiClient.js';
import { on, emit } from './eventBus.js';
import * as marksRepo from './marksRepository.js';
import { renderTable, wireTableActions } from './render/table.js';
import { renderCharts, renderInsights } from './render/charts.js';
import { renderSummary } from './render/summary.js';

let LAST_DATA = null;

function selectedSources() {
  return Array.from(document.querySelectorAll('.source:checked')).map(x => x.value);
}

function saveUIState() {
  const s = {
    hide_discarded: document.getElementById('hide_discarded').checked ? 1 : 0,
    only_loved: document.getElementById('only_loved').checked ? 1 : 0,
  };
  try { localStorage.setItem('imo_ui', JSON.stringify(s)); } catch (_) {}
}

function restoreUIState() {
  try {
    const s = JSON.parse(localStorage.getItem('imo_ui') || '{}') || {};
    if (typeof s.hide_discarded !== 'undefined') document.getElementById('hide_discarded').checked = !!s.hide_discarded;
    if (typeof s.only_loved !== 'undefined') document.getElementById('only_loved').checked = !!s.only_loved;
  } catch (_) {}
}

async function refresh() {
  const btn = document.getElementById('btnRefresh');
  const oldBtnHTML = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>A carregar…';

  const widgets = document.getElementById('summary-widgets');
  if (widgets) {
    widgets.innerHTML = `
      <div class="card stat-card border-0 shadow-none bg-transparent py-0">
        <div class="spinner-border spinner-border-sm text-secondary" role="status"></div>
      </div>
    `;
  }

  try {
    const params = {
      district: document.getElementById('district').value,
      pages: document.getElementById('pages').value,
      limit: document.getElementById('limit').value,
      sort: document.getElementById('sort').value,
      typology: document.getElementById('typology').value,
      search_type: document.getElementById('search_type').value,
      only_with_eurm2: document.getElementById('only_with_eurm2').checked ? '1' : '0',
      exclude_temporary: document.getElementById('exclude_temporary').checked ? '1' : '0',
      sources: selectedSources(),
    };

    const min_price = document.getElementById('min_price').value.trim();
    const max_price = document.getElementById('max_price').value.trim();
    const min_area  = document.getElementById('min_area').value.trim();
    const max_area  = document.getElementById('max_area').value.trim();
    if (min_price) params.min_price = min_price;
    if (max_price) params.max_price = max_price;
    if (min_area) params.min_area = min_area;
    if (max_area) params.max_area = max_area;

    const data = await getListings(params);
    LAST_DATA = data;
    // Render pipeline
    renderTable(LAST_DATA);
    const visible = renderSummary(LAST_DATA);
    renderCharts(visible);
    
    // Fetch and render global insights
    getStats().then(renderInsights).catch(console.error);
  } catch (err) {
    console.error(err);
    // You could add a toast or alert here
  } finally {
    btn.disabled = false;
    btn.innerHTML = oldBtnHTML;
  }
}

function wireControls() {
  document.getElementById('btnRefresh').addEventListener('click', refresh);
  document.getElementById('typology').addEventListener('change', refresh);
  document.getElementById('search_type').addEventListener('change', refresh);
  document.getElementById('hide_discarded').addEventListener('change', () => { saveUIState(); if (LAST_DATA) { renderTable(LAST_DATA); const visible = renderSummary(LAST_DATA); renderCharts(visible); getStats().then(renderInsights).catch(console.error); } });
  document.getElementById('only_loved').addEventListener('change', () => { saveUIState(); if (LAST_DATA) { renderTable(LAST_DATA); const visible = renderSummary(LAST_DATA); renderCharts(visible); getStats().then(renderInsights).catch(console.error); } });
}

function wireSourcesAutoRefresh() {
  document.querySelectorAll('.source').forEach(cb => cb.addEventListener('change', refresh));
}

function init() {
  restoreUIState();
  wireControls();
  wireSourcesAutoRefresh();
  wireTableActions(() => {
    if (LAST_DATA) {
      renderTable(LAST_DATA);
      const visible = renderSummary(LAST_DATA);
      renderCharts(visible);
      getStats().then(renderInsights).catch(console.error);
    }
  });

  on('marksChanged', () => {
    if (LAST_DATA) {
      renderTable(LAST_DATA);
      const visible = renderSummary(LAST_DATA);
      renderCharts(visible);
      getStats().then(renderInsights).catch(console.error);
    }
  });

  marksRepo.load().then(refresh);
}

window.addEventListener('load', init);

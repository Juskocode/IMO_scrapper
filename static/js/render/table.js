import { money, num } from '../utils/format.js';
import { get as getMark, set as setMark } from '../marksRepository.js';

function sourceBadge(src) {
  const s = (src || '').toLowerCase();
  const cls = `bg-${s}`;
  return `<span class="badge-source ${cls}">${src}</span>`;
}

function badgesFor(url) {
  const st = getMark(url);
  let html = '';
  if (st === 'loved') html += '<span class="badge badge-pink ms-2 animate-fade-in">Favorito</span>';
  if (st === 'discarded') html += '<span class="badge text-bg-dark ms-2 animate-fade-in">Descartado</span>';
  return html;
}

function applyLocalFilters(arr) {
  const hideDiscarded = document.getElementById('hide_discarded').checked;
  const onlyLoved = document.getElementById('only_loved').checked;
  return arr.filter(x => {
    const m = getMark(x.url);
    if (onlyLoved) return m === 'loved';
    if (hideDiscarded && m === 'discarded') return false;
    return true;
  });
}

let currentSortField = null;
let currentSortDir = 1; // 1 for asc, -1 for desc

export function renderTable(data) {
  let all = [...(data.results || [])];
  
  // Apply sorting if needed
  if (currentSortField) {
    all.sort((a, b) => {
      let v1 = a[currentSortField];
      let v2 = b[currentSortField];
      
      // Handle nulls
      if (v1 === null || v1 === undefined) return 1;
      if (v2 === null || v2 === undefined) return -1;
      
      if (typeof v1 === 'string') {
        return v1.localeCompare(v2) * currentSortDir;
      }
      return (v1 - v2) * currentSortDir;
    });
  }

  const filtered = applyLocalFilters(all);
  const tbody = document.getElementById('tbody');
  tbody.innerHTML = '';

  if (filtered.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="text-center py-5">
          <div class="text-secondary">
            <svg width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" class="mb-3 opacity-25"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
            <p class="mb-0">Nenhum anúncio encontrado com os filtros atuais.</p>
          </div>
        </td>
      </tr>
    `;
    return { filteredCount: 0 };
  }

  for (const x of filtered) {
    const discarded = getMark(x.url) === 'discarded';
    const loved = getMark(x.url) === 'loved';
    const tr = document.createElement('tr');
    if (discarded) tr.classList.add('row-discarded');
    tr.innerHTML = `
      <td style="width: 100px;">${sourceBadge(x.source)}</td>
      <td class="title-cell">
        <div class="d-flex align-items-center">
          <span class="fw-medium text-dark">${(x.title || 'Sem título')}</span>
          <div class="status-badges">${badgesFor(x.url)}</div>
        </div>
        <div class="text-secondary small mt-1 text-truncate" style="max-width: 400px;">${x.snippet || ''}</div>
      </td>
      <td class="text-end mono">${money(x.price_eur)}</td>
      <td class="text-end mono">${x.area_m2 ? num(x.area_m2) + ' m²' : '—'}</td>
      <td class="text-end mono">${x.eur_m2 ? num(x.eur_m2) : '—'}</td>
      <td>
        <a href="${x.url}" target="_blank" rel="noopener" class="btn btn-sm btn-outline-primary d-inline-flex align-items-center gap-1">
          <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
          Abrir
        </a>
      </td>
      <td class="actions text-nowrap">
        <div class="d-flex gap-2">
          <button type="button" class="btn btn-outline-secondary btn-action btn-love ${loved ? 'active' : ''}" title="${loved ? 'Remover favorito' : 'Marcar favorito'}" data-url="${x.url}">
            <svg width="18" height="18" fill="${loved ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path></svg>
          </button>
          <button type="button" class="btn btn-outline-secondary btn-action btn-discard ${discarded ? 'active' : ''}" title="${discarded ? 'Repor' : 'Descartar'}" data-url="${x.url}">
            <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
          </button>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  }
  
  // Update sort icons
  updateSortIcons();

  return { filteredCount: filtered.length };
}

function updateSortIcons() {
  document.querySelectorAll('#resultsTable thead th[data-sort]').forEach(th => {
    const icon = th.querySelector('.sort-icon');
    if (!icon) return;
    const field = th.getAttribute('data-sort');
    if (field === currentSortField) {
      icon.textContent = currentSortDir === 1 ? ' ↑' : ' ↓';
    } else {
      icon.textContent = '';
    }
  });
}

export function wireTableActions(onRefreshRequested) {
  // Existing row actions
  document.getElementById('tbody').addEventListener('click', async (ev) => {
    const btn = ev.target.closest('.btn-love, .btn-discard');
    if (!btn) return;
    const url = btn.getAttribute('data-url');
    if (!url) return;
    const isLove = btn.classList.contains('btn-love');
    const current = getMark(url);
    const next = isLove
      ? (current === 'loved' ? null : 'loved')
      : (current === 'discarded' ? null : 'discarded');
    await setMark(url, next || '');
  });

  // New sorting actions
  document.querySelectorAll('#resultsTable thead th[data-sort]').forEach(th => {
    th.addEventListener('click', () => {
      const field = th.getAttribute('data-sort');
      if (currentSortField === field) {
        currentSortDir *= -1;
      } else {
        currentSortField = field;
        currentSortDir = 1;
      }
      if (onRefreshRequested) onRefreshRequested();
    });
  });
}

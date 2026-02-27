import { median, num } from '../utils/format.js';
import { get as getMark } from '../marksRepository.js';

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

function createWidget(label, value, iconPath) {
  return `
    <div class="card stat-card animate-fade-in">
      <div class="d-flex align-items-center gap-3">
        <div class="bg-light p-2 rounded-3 text-primary">
          <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="${iconPath}"></path></svg>
        </div>
        <div>
          <div class="label">${label}</div>
          <div class="value" style="font-size: 1.25rem; margin-top: 0;">${value}</div>
        </div>
      </div>
    </div>
  `;
}

export function renderSummary(data) {
  const all = data.results || [];
  const filtered = applyLocalFilters(all);
  const el = document.getElementById('summary-widgets');
  if (el) {
    const rentItems = filtered.filter(x => x.price_eur < 10000);
    const buyItems = filtered.filter(x => x.price_eur >= 10000);
    
    const rentMed = median(rentItems.filter(x => x.eur_m2 !== null && x.eur_m2 !== undefined).map(x => x.eur_m2));
    const buyMed = median(buyItems.filter(x => x.eur_m2 !== null && x.eur_m2 !== undefined).map(x => x.eur_m2));

    let html = '';
    
    // Total Widget
    html += createWidget('Listagens', `${filtered.length} / ${data.stats.count}`, 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10');

    if (rentItems.length > 0) {
      html += createWidget('Média Arrendar', (rentMed ? num(rentMed) + ' €/m²' : '—'), 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6');
    }
    if (buyItems.length > 0) {
      html += createWidget('Média Comprar', (buyMed ? num(buyMed) + ' €/m²' : '—'), 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.407 2.67 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.407-2.67-1M12 16c-1.11 0-2.08-.407-2.67-1m2.67 1v1m0-1V8');
    }
    
    el.innerHTML = html;
  }
  
  // Also update old summary if it exists (for compatibility or other views)
  const oldSummary = document.getElementById('summary');
  if (oldSummary) {
    oldSummary.innerHTML = `<span class="badge text-bg-light border">${filtered.length} visíveis</span>`;
  }

  return filtered; // return visible to feed charts
}

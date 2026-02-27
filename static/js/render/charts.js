import { median, linearRegression } from '../utils/format.js';

let charts = {
  rent: { bySource: null, median: null, priceArea: null },
  buy: { bySource: null, median: null, priceArea: null }
};

const SOURCE_COLORS = {
  'idealista': '#ffc107',
  'imovirtual': '#0dcaf0',
  'supercasa': '#0d6efd',
  'casasapo': '#64748b',
  'remax': '#ef4444',
  'olx': '#22c55e',
  'default': '#1e293b'
};

// Global Chart defaults
if (window.Chart) {
  Chart.defaults.font.family = "'Inter', sans-serif";
  Chart.defaults.color = '#64748b';
  Chart.defaults.plugins.tooltip.padding = 12;
  Chart.defaults.plugins.tooltip.borderRadius = 8;
  Chart.defaults.plugins.tooltip.backgroundColor = '#0f172a';
}

function getSourceColor(src) {
  return SOURCE_COLORS[(src || '').toLowerCase()] || SOURCE_COLORS.default;
}

function renderSection(visible, type) {
  const suffix = type.charAt(0).toUpperCase() + type.slice(1);
  const container = document.getElementById('charts' + suffix);
  if (!container) return;

  if (visible.length === 0) {
    container.style.display = 'none';
    return;
  }
  container.style.display = 'block';

  const titles = container.getElementsByClassName('chart-section-title');
  if (titles.length > 0) {
    const searchType = document.getElementById('search_type').value;
    titles[0].style.display = searchType === 'all' ? 'block' : 'none';
  }

  // 1. By source counts
  const bySource = {};
  for (const x of visible) bySource[x.source] = (bySource[x.source] || 0) + 1;
  const labels = Object.keys(bySource);
  const counts = labels.map(k => bySource[k]);
  const colors = labels.map(k => getSourceColor(k));

  if (charts[type].bySource) charts[type].bySource.destroy();
  const ctx1 = document.getElementById('chartBySource' + suffix);
  if (ctx1) {
    charts[type].bySource = new Chart(ctx1, {
      type: 'bar',
      data: { 
        labels, 
        datasets: [{ 
          label: 'Anúncios', 
          data: counts,
          backgroundColor: colors,
          borderRadius: 6
        }] 
      },
      options: { 
        responsive: true,
        plugins: { 
          title: { display: true, text: 'Distribuição por Fonte', font: { weight: 'bold', size: 14 }, color: '#1e293b' },
          legend: { display: false }
        },
        scales: {
          y: { beginAtZero: true, grid: { display: false } },
          x: { grid: { display: false } }
        }
      }
    });
  }

  // 2. Median €/m2 per source
  const groups = {};
  for (const x of visible) {
    if (x.eur_m2 === null || x.eur_m2 === undefined) continue;
    (groups[x.source] = groups[x.source] || []).push(x.eur_m2);
  }
  const mLabels = Object.keys(groups);
  const medians = mLabels.map(k => median(groups[k]));
  const mColors = mLabels.map(k => getSourceColor(k));

  if (charts[type].median) charts[type].median.destroy();
  const ctx2 = document.getElementById('chartMedian' + suffix);
  if (ctx2) {
    charts[type].median = new Chart(ctx2, {
      type: 'bar',
      data: { 
        labels: mLabels, 
        datasets: [{ 
          label: 'Mediana €/m²', 
          data: medians,
          backgroundColor: mColors,
          borderRadius: 6
        }] 
      },
      options: { 
        responsive: true,
        plugins: { 
          title: { display: true, text: 'Mediana Preço/m²', font: { weight: 'bold', size: 14 }, color: '#1e293b' },
          legend: { display: false }
        },
        scales: {
          y: { beginAtZero: true, grid: { display: false } },
          x: { grid: { display: false } }
        }
      }
    });
  }

  // 3. Price vs Area Scatter Plot
  const scatterData = visible
    .filter(x => x.price_eur && x.area_m2)
    .map(x => ({
      x: x.area_m2,
      y: x.price_eur,
      source: x.source,
      title: x.title
    }));

  if (charts[type].priceArea) charts[type].priceArea.destroy();
  const ctx3 = document.getElementById('chartPriceArea' + suffix);
  if (ctx3) {
    const datasets = labels.map(src => ({
      label: src,
      data: scatterData.filter(d => d.source === src).map(d => ({ x: d.x, y: d.y, title: d.title, source: d.source })),
      backgroundColor: getSourceColor(src),
      pointRadius: 5,
      pointHoverRadius: 8,
      borderWidth: 2,
      borderColor: '#fff'
    }));

    // Trend line
    const reg = linearRegression(scatterData);
    if (reg) {
      const minX = Math.min(...scatterData.map(d => d.x));
      const maxX = Math.max(...scatterData.map(d => d.x));
      datasets.push({
        label: 'Tendência (Linear)',
        data: [
          { x: minX, y: reg.m * minX + reg.b },
          { x: maxX, y: reg.m * maxX + reg.b }
        ],
        type: 'line',
        borderColor: 'rgba(15, 23, 42, 0.4)',
        borderWidth: 3,
        borderDash: [8, 4],
        pointRadius: 0,
        fill: false,
        order: -1
      });
    }

    charts[type].priceArea = new Chart(ctx3, {
      type: 'scatter',
      data: { datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { title: { display: true, text: 'Área (m²)', font: { weight: 500 } }, grid: { borderDash: [4, 4] } },
          y: { title: { display: true, text: 'Preço (€)', font: { weight: 500 } }, grid: { borderDash: [4, 4] } }
        },
        plugins: {
          title: { display: true, text: 'Preço vs Área', font: { weight: 'bold', size: 14 }, color: '#1e293b' },
          tooltip: {
            callbacks: {
              label: (context) => {
                const d = context.raw;
                if (context.dataset.type === 'line') return 'Linha de Tendência';
                const label = d.source || context.dataset.label;
                return `${label}: ${d.y}€, ${d.x}m² - ${d.title}`;
              }
            }
          }
        }
      }
    });
  }
}

export function renderCharts(visible) {
  // Use a heuristic to separate rent and buy if they are mixed
  const rentItems = visible.filter(x => x.price_eur < 10000);
  const buyItems = visible.filter(x => x.price_eur >= 10000);

  renderSection(rentItems, 'rent');
  renderSection(buyItems, 'buy');
}

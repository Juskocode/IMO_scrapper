export function money(v) {
  if (v === null || v === undefined) return '—';
  return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(v);
}

export function num(v) {
  if (v === null || v === undefined) return '—';
  return new Intl.NumberFormat('pt-PT', { maximumFractionDigits: 2 }).format(v);
}

export function median(values) {
  const nums = values.slice().sort((a,b)=>a-b);
  const n = nums.length; if (!n) return null;
  const mid = Math.floor(n/2);
  return n % 2 ? nums[mid] : (nums[mid-1] + nums[mid]) / 2;
}

export function linearRegression(data) {
  const n = data.length;
  if (n < 2) return null;
  let sx = 0, sy = 0, sxy = 0, sxx = 0;
  for (const d of data) {
    sx += d.x;
    sy += d.y;
    sxy += d.x * d.y;
    sxx += d.x * d.x;
  }
  const den = (n * sxx - sx * sx);
  if (den === 0) return null;
  const m = (n * sxy - sx * sy) / den;
  const b = (sy - m * sx) / n;
  return { m, b };
}

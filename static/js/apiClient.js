// Facade for API calls

function buildQuery(params) {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "") continue;
    if (Array.isArray(v)) {
      for (const it of v) q.append(k, String(it));
    } else {
      q.set(k, String(v));
    }
  }
  return q.toString();
}

export async function getListings(params) {
  const qs = buildQuery(params);
  const res = await fetch(`/api/listings?${qs}`);
  if (!res.ok) throw new Error("Falha a carregar listagem");
  return res.json();
}

export async function getMarks() {
  const res = await fetch('/api/marks');
  if (!res.ok) return {};
  return res.json();
}

export async function postMark(url, state) {
  try {
    await fetch('/api/marks', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, state })
    });
  } catch (_) { /* ignore network errors for marks */ }
}

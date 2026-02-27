// Repository for Loved/Discarded marks with localStorage + server sync
import { emit } from './eventBus.js';
import { getMarks as apiGetMarks, postMark as apiPostMark } from './apiClient.js';

const LS_KEY = 'imo_marks';
let MARKS = {};

function loadLocal() {
  try { MARKS = JSON.parse(localStorage.getItem(LS_KEY) || '{}') || {}; }
  catch (_) { MARKS = {}; }
}

function saveLocal() {
  try { localStorage.setItem(LS_KEY, JSON.stringify(MARKS)); } catch (_) {}
}

export async function load() {
  loadLocal();
  try {
    const remote = await apiGetMarks();
    if (remote && typeof remote === 'object') {
      MARKS = Object.assign({}, MARKS, remote);
      saveLocal();
    }
  } catch (_) { /* offline */ }
  emit('marksChanged', MARKS);
}

export function get(url) { return MARKS[url] || null; }
export function all() { return { ...MARKS }; }

export async function set(url, state) {
  if (!url) return;
  if (state === 'loved' || state === 'discarded') {
    MARKS[url] = state;
  } else {
    delete MARKS[url];
  }
  saveLocal();
  emit('marksChanged', MARKS);
  try { await apiPostMark(url, state || ''); } catch (_) {}
}

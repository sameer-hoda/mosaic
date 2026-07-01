// App-level route controller. Owns the global phase state and the persistent shell.
import { renderPairing } from './components/Pairing.js';
import { renderClassifier } from './components/Classifier.js';
import { renderExtracting } from './components/Extracting.js';
import { renderKanban } from './components/Kanban.js';
import { renderHeader } from './components/Header.js';
import { setLastSynced } from './components/Header.js';
import { renderApiKey } from './components/ApiKey.js';
import { renderWhitelist } from './components/Whitelist.js';
import { renderDashboard } from './components/Dashboard.js';
import { api } from './api.js';

// Phase constants — v2 adds APIKEY, WHITELIST, DASHBOARD, DEEPDIVE
export const PHASE = {
  APIKEY: 'apikey',
  PAIRING: 'pairing',
  WHITELIST: 'whitelist',
  CLASSIFY: 'classify',
  EXTRACT: 'extract',
  KANBAN: 'kanban',
  DASHBOARD: 'dashboard',
};

// In-memory state shared across phases
const state = {
  phase: PHASE.APIKEY,
  selectedChats: [],
  activeCategory: 'all',
  lastSynced: null,
  error: null,
  health: null,
};

export function getState() {
  return state;
}

export function setPhase(phase, extras = {}) {
  state.phase = phase;
  Object.assign(state, extras);
  renderInternal();
}

export function setActiveCategory(cat) {
  state.activeCategory = cat;
  window.dispatchEvent(new CustomEvent('taskdog:setCategory', { detail: cat }));
  renderInternal();
}

export function setError(err) {
  state.error = err;
  renderInternal();
}

function renderShell(root) {
  root.innerHTML = '';

  const shell = document.createElement('div');
  shell.className = 'app-shell';
  root.appendChild(shell);

  // Single column: top bar + main (no side nav)
  const right = document.createElement('div');
  right.className = 'app-main';
  shell.appendChild(right);

  // Top bar — shown in all phases except APIKEY and PAIRING
  if (state.phase !== PHASE.PAIRING && state.phase !== PHASE.APIKEY) {
    renderHeader(right, state);
  }

  // Main
  const main = document.createElement('main');
  main.className = 'main';
  right.appendChild(main);

  return main;
}

function formatLastSynced(iso) {
  if (!iso) return 'Last Synced: just now';
  try {
    const d = new Date(iso);
    if (isNaN(d.getTime())) return 'Last Synced: just now';
    const diffMs = Date.now() - d.getTime();
    const mins = Math.floor(diffMs / 60000);
    if (mins < 1) return 'Last Synced: just now';
    if (mins < 60) return `Last Synced: ${mins} min ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `Last Synced: ${hrs} hr ago`;
    return `Last Synced: ${d.toLocaleDateString()}`;
  } catch {
    return 'Last Synced: just now';
  }
}

export { formatLastSynced };

function renderInternal() {
  const app = document.getElementById('app');
  if (!app) return;

  const main = renderShell(app);

  switch (state.phase) {
    case PHASE.APIKEY:
      renderApiKey(main, state);
      break;
    case PHASE.PAIRING:
      renderPairing(main, state);
      break;
    case PHASE.WHITELIST:
      renderWhitelist(main, state);
      break;
    case PHASE.CLASSIFY:
      renderClassifier(main, state);
      break;
    case PHASE.EXTRACT:
      renderExtracting(main, state);
      break;
    case PHASE.KANBAN:
      renderKanban(main, state);
      break;
    case PHASE.DASHBOARD:
      renderDashboard(main, state);
      break;
  }
}

export function renderApp(root) {
  // Check health to determine initial phase (Gate A → Gate B → etc.)
  console.log('[app] renderApp() — calling healthV2()');
  api.healthV2().then((res) => {
    console.log('[app] health response:', res);
    state.health = res;
    if (!res.gemini_key_set) {
      console.log('[app] no key set → APIKEY phase');
      state.phase = PHASE.APIKEY;
    } else if (res.bridge_status !== 'connected') {
      console.log(`[app] bridge_status=${res.bridge_status} → PAIRING phase`);
      state.phase = PHASE.PAIRING;
    } else {
      // Key set + bridge connected → go to dashboard or whitelist
      api.getGroupsV2().then((gres) => {
        if (gres.ok && gres.groups && gres.groups.length > 0) {
          state.phase = PHASE.DASHBOARD;
        } else {
          state.phase = PHASE.WHITELIST;
        }
        renderInternal();
      }).catch(() => {
        state.phase = PHASE.WHITELIST;
        renderInternal();
      });
    }
    renderInternal();
  }).catch(() => {
    // Health check failed — show API key gate as fallback
    state.phase = PHASE.APIKEY;
    renderInternal();
  });

  // Pull "last synced" timestamp
  api.bridgeStatus().then((res) => {
    if (res && res.connected_at) {
      state.lastSynced = res.connected_at;
      const label = document.querySelector('[data-sync-label]');
      if (label) label.textContent = formatLastSynced(res.connected_at);
    }
  }).catch(() => { /* keep default label */ });
}

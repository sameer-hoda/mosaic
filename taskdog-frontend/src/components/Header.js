// Top bar shown in all phases except pairing and API key.
// Minimal nav: Dashboard / Groups, plus settings + logout.
import { PHASE, getState, setPhase, setActiveCategory } from '../app.js';

export function renderHeader(root, state) {
  const NAV_TABS = [
    { phase: PHASE.DASHBOARD, label: 'Dashboard' },
    { phase: PHASE.WHITELIST,  label: 'Groups' },
  ];

  const bar = document.createElement('header');
  bar.className = 'topbar';

  const brand = document.createElement('div');
  brand.className = 'topbar-brand';
  brand.innerHTML = `
    <div class="topbar-brand-mark">
      <img src="/mosaic-logo-mark.svg" alt="Mosaic" width="24" height="24" />
    </div>
    <div class="topbar-brand-text">
      <h1>Mosaic</h1>
      <p class="topbar-subtext">Your life, pieced together.</p>
      <div class="topbar-sync">
        <span class="topbar-sync-dot" data-sync-dot></span>
        <span data-sync-label>${formatLastSynced(state.lastSynced)}</span>
      </div>
    </div>
  `;
  bar.appendChild(brand);

  const nav = document.createElement('nav');
  nav.className = 'topbar-tabs';
  NAV_TABS.forEach((t) => {
    const btn = document.createElement('button');
    btn.className = 'topbar-tab' + (state.phase === t.phase ? ' is-active' : '');
    btn.textContent = t.label;
    btn.addEventListener('click', () => setPhase(t.phase));
    nav.appendChild(btn);
  });
  bar.appendChild(nav);

  const right = document.createElement('div');
  right.className = 'topbar-right';

  const settingsBtn = document.createElement('button');
  settingsBtn.className = 'topbar-icon';
  settingsBtn.title = 'API Key Settings';
  settingsBtn.innerHTML = `<span class="material-symbols-outlined">key</span>`;
  settingsBtn.addEventListener('click', () => setPhase(PHASE.APIKEY));
  right.appendChild(settingsBtn);

  const logoutBtn = document.createElement('button');
  logoutBtn.className = 'topbar-icon topbar-logout';
  logoutBtn.title = 'Logout';
  logoutBtn.innerHTML = `
    <span class="material-symbols-outlined">logout</span>
    <span class="topbar-logout-label">Logout</span>
  `;
  logoutBtn.addEventListener('click', () => setPhase(PHASE.PAIRING));
  right.appendChild(logoutBtn);

  // Theme toggle
  const themeBtn = document.createElement('button');
  themeBtn.className = 'theme-toggle';
  const currentTheme = localStorage.getItem('taskdog-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', currentTheme);
  themeBtn.innerHTML = `<span class="material-symbols-outlined">${currentTheme === 'light' ? 'dark_mode' : 'light_mode'}</span>`;
  themeBtn.title = currentTheme === 'light' ? 'Switch to dark mode' : 'Switch to light mode';
  themeBtn.addEventListener('click', () => {
    const next = document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('taskdog-theme', next);
    themeBtn.querySelector('.material-symbols-outlined').textContent = next === 'light' ? 'dark_mode' : 'light_mode';
    themeBtn.title = next === 'light' ? 'Switch to dark mode' : 'Switch to light mode';
  });
  right.appendChild(themeBtn);

  bar.appendChild(right);
  root.appendChild(bar);
}

export function setLastSynced(_iso) { /* sync label rendered by shell in app.js */ }

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

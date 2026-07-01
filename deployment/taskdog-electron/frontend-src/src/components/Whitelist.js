// Gate C: Group whitelisting — simplified flat list.
// Fetches chats directly from the bridge (no Gemini), shows a single
// selectable list sorted by most recent message first.
import { api } from '../api.js';
import { PHASE, setPhase } from '../app.js';

function escapeHtml(s) {
  return String(s || '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function initials(name) {
  const parts = String(name || '').split(/\s+/).filter(Boolean).slice(0, 2);
  return parts.map((p) => p[0]).join('').toUpperCase() || '?';
}

export function renderWhitelist(root, _state) {
  const wrap = document.createElement('section');
  wrap.className = 'phase dash-v2 fade-in';
  wrap.innerHTML = `
    <div class="dash-v2-container">
      <div class="wl-page-head">
        <div>
          <h2>Select Groups to Monitor</h2>
          <p data-subtitle>Loading your WhatsApp chats\u2026</p>
        </div>
        <div class="wl-model-pill">
          <span class="material-symbols-outlined">group_work</span>
          Step 3 of 3
        </div>
      </div>

      <div class="wl-stats-row" data-stats-row>
        <div data-stats>Loading\u2026</div>
      </div>

      <div class="wl-list" data-list>
        <div class="dash-v2-empty" data-loading>
          <span class="spinner"></span>
          <h3>Fetching chats\u2026</h3>
          <p>Reading your WhatsApp conversations from the bridge.</p>
        </div>
      </div>

      <div class="wl-actionbar" data-actionbar>
        <div class="wl-actionbar-inner">
          <div class="wl-ab-count" data-selected-count>0</div>
          <div class="wl-ab-text">
            <strong>Groups Selected</strong>
            <span data-selected-breakdown>Select at least 1 group to proceed</span>
          </div>
          <button class="btn btn-primary" data-proceed disabled>
            Save & Discover Tasks
            <span class="material-symbols-outlined" style="font-size:18px">arrow_forward</span>
          </button>
        </div>
      </div>
    </div>
  `;
  root.appendChild(wrap);

  const $ = (s) => wrap.querySelector(s);
  const els = {
    subtitle: $('[data-subtitle]'),
    stats: $('[data-stats]'),
    list: $('[data-list]'),
    loading: $('[data-loading]'),
    selectedCount: $('[data-selected-count]'),
    selectedBreakdown: $('[data-selected-breakdown]'),
    proceedBtn: $('[data-proceed]'),
  };

  const selected = new Set();

  function updateActionBar() {
    const count = selected.size;
    els.selectedCount.textContent = String(count);
    els.selectedCount.classList.toggle('is-active', count > 0);
    els.proceedBtn.disabled = count < 1;
    els.selectedBreakdown.textContent = count < 1
      ? 'Select at least 1 group to proceed'
      : `${count} group${count === 1 ? '' : 's'} selected`;
  }

  function buildRow(chat) {
    const isSel = selected.has(chat.jid);
    const row = document.createElement('div');
    row.className = 'wl-row' + (isSel ? ' is-selected' : '');
    row.dataset.jid = chat.jid;
    row.innerHTML = `
      <div class="wl-avatar">${escapeHtml(initials(chat.name))}</div>
      <div class="wl-name">${escapeHtml(chat.name)}</div>
      <button class="wl-tick-btn" data-tick type="button">
        <span class="material-symbols-outlined">check</span>
      </button>
    `;
    row.addEventListener('click', (e) => {
      if (e.target.closest('[data-tick]')) return;
      const tickBtn = row.querySelector('[data-tick]');
      tickBtn.click();
    });
    row.querySelector('[data-tick]').addEventListener('click', (e) => {
      e.stopPropagation();
      if (selected.has(chat.jid)) {
        selected.delete(chat.jid);
        row.classList.remove('is-selected');
      } else {
        selected.add(chat.jid);
        row.classList.add('is-selected');
      }
      updateActionBar();
    });
    return row;
  }

  async function load() {
    els.loading.style.display = '';
    els.stats.textContent = 'Loading\u2026';

    let chats = [];
    let retries = 0;
    const maxRetries = 15;  // up to ~45s of retrying for history sync to populate

    while (retries < maxRetries) {
      const res = await api.getChats();
      if (!res.ok) {
        els.list.innerHTML = `<div class="dash-v2-empty">
          <span class="material-symbols-outlined">error</span>
          <h3>Error</h3><p>${escapeHtml(res.error || 'Failed to fetch chats')}</p>
          <button class="btn" onclick="location.reload()">Retry</button>
        </div>`;
        return;
      }
      chats = res.chats || [];
      if (chats.length > 0) break;

      // Chats empty — bridge may still be syncing history
      els.subtitle.textContent = 'Syncing WhatsApp messages\u2026';
      els.stats.textContent = 'Syncing\u2026';
      els.list.innerHTML = `<div class="dash-v2-empty">
        <span class="spinner"></span>
        <h3>Syncing WhatsApp data\u2026</h3>
        <p>Importing your conversations. This may take a minute after first pairing.</p>
        <p style="font-size:12px;color:var(--on-surface-muted);margin-top:8px">Retry ${retries + 1}/${maxRetries}</p>
      </div>`;
      await new Promise((r) => setTimeout(r, 3000));
      retries++;
    }

    if (chats.length === 0) {
      els.list.innerHTML = `<div class="dash-v2-empty">
        <span class="material-symbols-outlined">chat</span>
        <h3>No chats found</h3>
        <p>Make sure your WhatsApp bridge is paired and has received messages.</p>
        <button class="btn" onclick="location.reload()">Retry</button>
      </div>`;
      return;
    }

    els.stats.innerHTML = `<strong>${chats.length}</strong> chats <span class="sep"></span> sorted by recent activity`;
    els.subtitle.textContent = 'Select groups you want to monitor for tasks';

    const listEl = document.createElement('div');
    listEl.className = 'wl-rows';

    for (const chat of chats) {
      if (chat.is_whitelisted) selected.add(chat.jid);
      listEl.appendChild(buildRow(chat));
    }
    els.loading.style.display = 'none';
    els.list.appendChild(listEl);
    updateActionBar();
  }

  els.proceedBtn.addEventListener('click', async () => {
    const jids = [...selected];
    if (jids.length < 1) return;

    els.proceedBtn.disabled = true;
    els.proceedBtn.innerHTML = '<span class="spinner"></span> Saving\u2026';

    const res = await api.whitelistGroups(jids);
    if (res.ok) {
      setPhase(PHASE.DASHBOARD, { autoDiscover: true });
    } else {
      els.proceedBtn.disabled = false;
      els.proceedBtn.innerHTML = 'Save & Discover Tasks <span class="material-symbols-outlined" style="font-size:18px">arrow_forward</span>';
      els.selectedBreakdown.innerHTML = `<span style="color:var(--error)">Error: ${escapeHtml(res.error || 'Failed to save')}</span>`;
    }
  });

  load();
}
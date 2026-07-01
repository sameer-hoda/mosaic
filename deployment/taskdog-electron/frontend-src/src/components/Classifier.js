// Phase 1 · Classifier (v4 — streaming + drag-and-drop).
// Loads classifications from the server's chat_classifications cache via
// Server-Sent Events. Only uncached chats hit Gemini, and cards render as
// they arrive so the progress bar fills smoothly. Users can drag a card
// between Work and Personal — the new category is persisted to the cache.

import { api } from '../api.js';
import { PHASE, setPhase } from '../app.js';

const CATS = ['work', 'personal'];
const CAT_LABEL = { work: 'Work', personal: 'Personal' };
const CAT_ICON  = { work: 'work', personal: 'home' };

const catKey = (c) => {
  const k = String(c || '').toLowerCase();
  return k === 'work' ? 'work' : 'personal';
};
const catTitle = (k) => CAT_LABEL[catKey(k)];

const initials = (name) => {
  const parts = String(name || '').split(/\s+/).filter(Boolean).slice(0, 2);
  return parts.map((p) => p[0]).join('').toUpperCase() || '?';
};

const DRAG_MIME = 'application/x-taskdog-jid';

export function renderClassifier(root, _state) {
  // --- Outer shell ---
  const wrap = document.createElement('section');
  wrap.className = 'phase phase-classifier fade-in';
  wrap.innerHTML = `
    <div class="cls-page-head">
      <div>
        <h2>Intelligence Engine</h2>
        <p data-subtitle>Categorizing your top 100 active WhatsApp threads…</p>
      </div>
      <div class="cls-model-pill">
        <span class="material-symbols-outlined">psychology</span>
        Model: Mosaic-v2.1
      </div>
    </div>

    <div class="cls-toolbar">
      <button class="cls-toolbar-btn" data-recat>
        <span class="material-symbols-outlined">refresh</span>
        Re-categorize all
      </button>
      <div class="cls-meter"><div class="cls-meter-fill" data-meter></div></div>
      <div class="cls-meter-text">
        <span data-classified>0</span> / <span data-total>0</span> classified
      </div>
    </div>

    <div class="cls-engine cls-engine-direct" data-playfield>
      <div class="cls-tray cls-tray-direct" data-tray="work">
        <div class="cls-tray-head">
          <span class="cls-tray-ico cls-tray-ico-work">
            <span class="material-symbols-outlined fill">${CAT_ICON.work}</span>
          </span>
          <span class="cls-tray-name">${CAT_LABEL.work}</span>
          <span class="cls-tray-count" data-count="work">0 items</span>
        </div>
        <div class="cls-tray-body cls-tray-body-direct" data-tray-body="work" data-dropzone="work">
          <div class="cls-tray-empty" data-empty="work">No work groups yet.</div>
        </div>
      </div>

      <div class="cls-tray cls-tray-direct" data-tray="personal">
        <div class="cls-tray-head">
          <span class="cls-tray-ico cls-tray-ico-personal">
            <span class="material-symbols-outlined fill">${CAT_ICON.personal}</span>
          </span>
          <span class="cls-tray-name">${CAT_LABEL.personal}</span>
          <span class="cls-tray-count" data-count="personal">0 items</span>
        </div>
        <div class="cls-tray-body cls-tray-body-direct" data-tray-body="personal" data-dropzone="personal">
          <div class="cls-tray-empty" data-empty="personal">No personal groups yet.</div>
        </div>
      </div>
    </div>

    <p class="cls-hint">
      <span class="material-symbols-outlined">drag_indicator</span>
      Drag a card to move it between Work and Personal.
    </p>

    <div class="cls-actionbar is-show" data-actionbar>
      <div class="cls-actionbar-inner">
        <div class="cls-ab-count" data-selected-count>0</div>
        <div class="cls-ab-text">
          <strong>Groups Whitelisted</strong>
          <span data-selected-breakdown>Select at least 1 group to proceed</span>
        </div>
        <button class="btn btn-primary" data-proceed>
          Extract tasks
          <span class="material-symbols-outlined" style="font-size:18px">arrow_forward</span>
        </button>
      </div>
    </div>

    <div class="cls-overlay" data-overlay>
      <div class="cls-success">
        <div class="cls-success-mark">
          <span class="material-symbols-outlined">check_circle</span>
        </div>
        <h3>All set.</h3>
        <p>Mosaic will dig through <b data-success-n>0</b> groups and fetch your action items.</p>
        <div class="cls-success-chips" data-success-chips></div>
        <div class="cls-success-actions">
          <button class="btn" data-success-back>Back to sorting</button>
          <button class="btn btn-primary" data-success-go>
            Start extraction
            <span class="material-symbols-outlined" style="font-size:18px">arrow_forward</span>
          </button>
        </div>
      </div>
    </div>
  `;
  root.appendChild(wrap);

  // --- Element handles ---
  const $ = (s) => wrap.querySelector(s);
  const els = {
    subtitle: $('[data-subtitle]'),
    classified: $('[data-classified]'),
    total: $('[data-total]'),
    meter: $('[data-meter]'),
    actionbar: $('[data-actionbar]'),
    abCount: $('[data-selected-count]'),
    abText: $('[data-selected-breakdown]'),
    overlay: $('[data-overlay]'),
    successN: $('[data-success-n]'),
    successChips: $('[data-success-chips]'),
  };

  // --- State ---
  // blocks: Map<jid, {jid, name, category, tldr, selected, fromCache, el}>
  const blocks = new Map();
  let total = 0;
  let classified = 0;
  let loading = false;

  // --- Card builder ---
  function buildCardEl(b) {
    const el = document.createElement('div');
    el.className = 'cls-block cls-block-direct';
    el.dataset.id = b.jid;
    el.dataset.cat = b.category;
    el.draggable = true;
    if (b.selected) el.classList.add('is-selected');
    el.title = b.tldr || b.name;
    el.innerHTML = `
      <div class="cls-avatar">${escapeHtml(initials(b.name))}</div>
      <div class="cls-block-main">
        <div class="cls-block-name">${escapeHtml(b.name)}</div>
        <div class="cls-block-tldr">${escapeHtml(b.tldr || 'No summary available.')}</div>
      </div>
      <button class="cls-tick-btn" data-tick aria-label="${b.selected ? 'Unselect' : 'Select'} group" type="button">
        <span class="material-symbols-outlined">check</span>
      </button>
    `;

    // Tick button: select / deselect (no drag).
    el.querySelector('[data-tick]').addEventListener('click', (e) => {
      e.stopPropagation();
      b.selected = !b.selected;
      el.classList.toggle('is-selected', b.selected);
      el.querySelector('[data-tick]').setAttribute(
        'aria-label', `${b.selected ? 'Unselect' : 'Select'} group`
      );
      updateSelected();
    });

    // Drag-and-drop wiring (HTML5 DnD). The whole card is draggable; the
    // tick button stops propagation above so it won't fire a drag start.
    el.addEventListener('dragstart', (e) => {
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData(DRAG_MIME, b.jid);
      // Some browsers need text/plain to actually start the drag.
      e.dataTransfer.setData('text/plain', b.jid);
      el.classList.add('is-dragging');
    });
    el.addEventListener('dragend', () => {
      el.classList.remove('is-dragging');
      // Clear any drop-zone highlights left behind.
      wrap.querySelectorAll('.cls-tray-body-direct.is-drop-target')
        .forEach((n) => n.classList.remove('is-drop-target'));
    });

    return el;
  }

  function addCard(chat) {
    const jid = chat.jid;
    if (blocks.has(jid)) return;  // dedupe (defensive)
    const k = catKey(chat.category);
    const block = {
      jid,
      name: chat.name || jid,
      category: k,
      tldr: chat.tldr || '',
      selected: !!chat.is_whitelisted,
      fromCache: !!chat.from_cache,
      el: null,
    };
    block.el = buildCardEl(block);
    blocks.set(jid, block);
    const body = wrap.querySelector(`[data-tray-body="${k}"]`);
    body.appendChild(block.el);
    // Hide the empty placeholder if this is the first card in the column.
    if (body.querySelectorAll('.cls-block-direct').length > 0) {
      const empty = body.querySelector('.cls-tray-empty');
      if (empty) empty.style.display = 'none';
    }
    classified++;
  }

  function updateCounts() {
    const counts = { work: 0, personal: 0 };
    blocks.forEach((b) => { counts[b.category] = (counts[b.category] || 0) + 1; });
    CATS.forEach((c) => {
      const el = wrap.querySelector(`[data-count="${c}"]`);
      const n = counts[c];
      el.textContent = `${n} ${n === 1 ? 'item' : 'items'}`;
      const body = wrap.querySelector(`[data-tray-body="${c}"]`);
      const empty = body.querySelector('.cls-tray-empty');
      empty.style.display = n === 0 ? '' : 'none';
    });
    els.classified.textContent = String(classified);
    els.total.textContent = String(total);
    els.meter.style.transform = `scaleX(${total ? classified / total : 0})`;
  }

  function updateSelected() {
    const sel = [...blocks.values()].filter((b) => b.selected);
    els.abCount.textContent = String(sel.length);
    els.abCount.classList.toggle('is-active', sel.length > 0);
    if (sel.length < 1) {
      els.abText.innerHTML = 'Select at least 1 group to proceed';
    } else {
      const sc = { work: 0, personal: 0 };
      sel.forEach((b) => { sc[b.category] = (sc[b.category] || 0) + 1; });
      const parts = [];
      if (sc.work)     parts.push(`<b>${sc.work}</b> ${CAT_LABEL.work}`);
      if (sc.personal) parts.push(`<b>${sc.personal}</b> ${CAT_LABEL.personal}`);
      els.abText.innerHTML = parts.join(' · ') || `<b>${sel.length}</b> groups selected`;
    }
  }

  // --- Drop-zone wiring (HTML5 DnD target) ---
  function wireDropzones() {
    CATS.forEach((c) => {
      const zone = wrap.querySelector(`[data-dropzone="${c}"]`);
      if (!zone) return;
      zone.addEventListener('dragover', (e) => {
        // Only accept our own drag type.
        if (![...e.dataTransfer.types].some((t) => t === DRAG_MIME || t === 'text/plain')) return;
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        zone.classList.add('is-drop-target');
      });
      zone.addEventListener('dragleave', (e) => {
        // dragleave fires when crossing into a child — ignore those.
        if (e.relatedTarget && zone.contains(e.relatedTarget)) return;
        zone.classList.remove('is-drop-target');
      });
      zone.addEventListener('drop', async (e) => {
        e.preventDefault();
        zone.classList.remove('is-drop-target');
        const jid = e.dataTransfer.getData(DRAG_MIME) || e.dataTransfer.getData('text/plain');
        if (!jid) return;
        await moveCardTo(jid, c);
      });
    });
  }

  async function moveCardTo(jid, newCatKey) {
    const b = blocks.get(jid);
    if (!b) return;
    const newCatTitle = catTitle(newCatKey);
    if (b.category === newCatKey) return;  // no-op

    // Optimistic UI: detach, re-append in new column, update category.
    const oldBody = wrap.querySelector(`[data-tray-body="${b.category}"]`);
    const newBody = wrap.querySelector(`[data-tray-body="${newCatKey}"]`);
    if (!oldBody || !newBody) return;

    oldBody.removeChild(b.el);
    newBody.appendChild(b.el);
    b.category = newCatKey;
    b.el.dataset.cat = newCatKey;
    updateCounts();
    updateSelected();

    // Persist to the server. Fire-and-forget; if it fails we just log
    // — the next visit will hit the cache and Gemini will be re-run
    // for this JID only.
    try {
      const res = await api.updateChatCategory(jid, newCatTitle);
      if (!res.ok) {
        console.warn('updateChatCategory failed', res);
      }
    } catch (e) {
      console.warn('updateChatCategory error', e);
    }
  }

  // --- Stream loader ---
  async function load(force = false) {
    if (loading) return;
    loading = true;

    // Clear any previous cards.
    blocks.forEach((b) => { if (b.el && b.el.parentNode) b.el.parentNode.removeChild(b.el); });
    blocks.clear();
    classified = 0;
    total = 0;
    els.subtitle.textContent = force ? 'Re-classifying all groups…' : 'Loading…';
    updateCounts();
    updateSelected();

    await api.classifyChatsStream({
      force,
      onMeta: (m) => {
        total = m.total || 0;
        els.total.textContent = String(total);
      },
      onChat: (c) => {
        addCard(c);
        updateCounts();
        updateSelected();
      },
      onError: (e) => {
        els.subtitle.textContent = `Error: ${e.error || 'Unknown error'}`;
        loading = false;
      },
      onDone: () => {
        // Subtitle summary.
        let cached = 0, fresh = 0;
        blocks.forEach((b) => { if (b.fromCache) cached++; else fresh++; });
        els.subtitle.textContent = fresh === 0
          ? `All ${cached} groups loaded from cache`
          : `${cached} cached · ${fresh} freshly classified`;
        els.meter.style.transform = 'scaleX(1)';
        loading = false;
      },
    });
  }

  // --- Wire up controls ---
  $('[data-recat]').addEventListener('click', () => {
    if (loading) return;
    load(true);
  });

  $('[data-proceed]').addEventListener('click', () => {
    const sel = [...blocks.values()].filter((b) => b.selected);
    if (sel.length < 1) return;
    els.successN.textContent = String(sel.length);
    els.successChips.innerHTML = sel.slice(0, 6).map((b) =>
      `<span class="cls-success-chip" data-cat="${b.category}"><span class="dot"></span>${escapeHtml(b.name)}</span>`
    ).join('') + (sel.length > 6 ? `<span class="cls-success-chip">+${sel.length - 6} more</span>` : '');
    els.overlay.classList.add('is-show');
  });

  $('[data-success-back]').addEventListener('click', () => els.overlay.classList.remove('is-show'));
  els.overlay.addEventListener('click', (e) => {
    if (e.target === els.overlay) els.overlay.classList.remove('is-show');
  });

  $('[data-success-go]').addEventListener('click', () => {
    const sel = [...blocks.values()].filter((b) => b.selected).map((b) => ({
      jid: b.jid,
      name: b.name,
      category: catTitle(b.category),
      tldr: b.tldr,
    }));
    setPhase(PHASE.EXTRACT, { selectedChats: sel });
  });

  wireDropzones();
  load(false);
}

function escapeHtml(s) {
  return String(s || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

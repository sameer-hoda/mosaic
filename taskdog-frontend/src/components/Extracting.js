// Phase 2 · Extracting
// Light gradient with concentric pulsing rings + group processing queue.
// Per-group status updates arrive via SSE so the user sees real progress
// as each chat finishes (not a single flash at the end).
import { api } from '../api.js';
import { PHASE, setPhase } from '../app.js';

const MESSAGES = [
  'Reading 30 days of conversations…',
  'Clustering messages into themes…',
  'Identifying action items…',
  'Drafting concise follow-ups…',
  'Drafting moderate follow-ups…',
  'Adding context-rich variants…',
  'Finalising task cards…',
];

export function renderExtracting(root, state) {
  const chats = state.selectedChats || [];
  const wrap = document.createElement('section');
  wrap.className = 'phase phase-extract fade-in';
  wrap.innerHTML = `
    <div class="extract-stage">
      <div class="extract-rings">
        <div class="extract-ring-outer"></div>
        <div class="extract-ring-mid"></div>
        <div class="extract-ring-inner">
          <span class="material-symbols-outlined">data_usage</span>
        </div>
      </div>

      <h1 class="extract-headline">Analyzing 30 days of conversation…</h1>
      <div class="extract-mono" data-mono>Running Gemini Map-Reduce pipeline</div>
      <div class="extract-msg" data-msg>${MESSAGES[0]}</div>

      <div class="extract-queue">
        <div class="extract-queue-head">
          <span class="label">Group Processing Queue</span>
          <span class="progress" data-progress>0 / ${chats.length} Complete</span>
        </div>
        <div data-queue>
          ${chats.map((c, i) => `
            <div class="extract-queue-item ${i === 0 ? 'is-active' : 'is-pending'}" data-queue-idx="${i}" data-jid="${escapeAttr(c.jid)}">
              <span class="material-symbols-outlined">${i === 0 ? 'sync' : 'schedule'}</span>
              <span class="extract-queue-item-name">${escapeHtml(c.name)}</span>
              <span class="extract-queue-item-status">${i === 0 ? 'Processing' : 'Pending'}</span>
            </div>
          `).join('')}
        </div>
      </div>
    </div>
  `;
  root.appendChild(wrap);

  const msgEl = wrap.querySelector('[data-msg]');
  const monoEl = wrap.querySelector('[data-mono]');
  const progressEl = wrap.querySelector('[data-progress]');
  const queueItems = Array.from(wrap.querySelectorAll('.extract-queue-item'));

  // Index queue items by jid so SSE chat events can find them O(1).
  const itemByJid = new Map(
    queueItems.map((q) => [q.dataset.jid, q])
  );

  // Counts updated from the stream.
  const counts = {
    ok: 0, no_messages: 0, gemini_failed: 0, save_failed: 0, total: chats.length,
  };

  // Smooth pseudo-progress for the rotating messages (purely visual).
  const totalMs = 17000;
  const start = Date.now();
  let lastDisplayedIdx = -1;
  const tick = setInterval(() => {
    const elapsed = Date.now() - start;
    const t = Math.min(1, elapsed / totalMs);
    const idx = Math.min(MESSAGES.length - 1, Math.floor(t * MESSAGES.length));
    if (idx !== lastDisplayedIdx) {
      msgEl.textContent = MESSAGES[idx];
      lastDisplayedIdx = idx;
    }
  }, 200);

  // While we wait for SSE events, walk the queue visually so it doesn't
  // feel frozen. The real status overrides this when an event arrives.
  const visualTick = setInterval(() => {
    const doneCount = counts.ok + counts.no_messages + counts.gemini_failed + counts.save_failed;
    queueItems.forEach((q) => {
      // Skip items that have already been resolved by a chat event.
      if (q.classList.contains('is-done') || q.classList.contains('is-warn') || q.classList.contains('is-fail')) return;
    });
    progressEl.textContent = `${doneCount} / ${counts.total} Complete`;
  }, 300);

  // Mark a queue item as resolved based on a chat event.
  function applyChatEvent(ev) {
    const q = itemByJid.get(ev.jid);
    if (!q) return;
    const status = q.querySelector('.extract-queue-item-status');
    const icon = q.querySelector('.material-symbols-outlined');
    const s = ev.status;
    q.classList.remove('is-active', 'is-pending');
    if (s === 'ok') {
      counts.ok += 1;
      q.classList.add('is-done');
      icon.textContent = 'check_circle';
      const tc = ev.task_count || 0;
      const themes = ev.theme_count || 0;
      status.textContent = tc
        ? `Done · ${tc} task${tc === 1 ? '' : 's'}${themes ? ` · ${themes} theme${themes === 1 ? '' : 's'}` : ''}`
        : 'Done';
    } else if (s === 'no_messages') {
      counts.no_messages += 1;
      q.classList.add('is-warn');
      icon.textContent = 'chat_off';
      status.textContent = 'No 30-day history';
    } else if (s === 'save_failed') {
      counts.save_failed += 1;
      q.classList.add('is-fail');
      icon.textContent = 'error';
      status.textContent = 'Save failed';
    } else {
      counts.gemini_failed += 1;
      q.classList.add('is-fail');
      icon.textContent = 'error';
      status.textContent = 'Gemini failed';
    }
    // Update headline + progress + the headline spinner rotation.
    refreshHeadline();
    progressEl.textContent = `${counts.ok + counts.no_messages + counts.gemini_failed + counts.save_failed} / ${counts.total} Complete`;
  }

  function refreshHeadline() {
    const done = counts.ok + counts.no_messages + counts.gemini_failed + counts.save_failed;
    if (done === 0) return;
    if (counts.gemini_failed === 0 && counts.save_failed === 0 && counts.no_messages === 0) {
      monoEl.textContent = `${counts.ok} group${counts.ok === 1 ? '' : 's'} processed`;
    } else {
      const parts = [`${counts.ok} ok`];
      if (counts.no_messages) parts.push(`${counts.no_messages} no history`);
      if (counts.gemini_failed) parts.push(`${counts.gemini_failed} failed`);
      if (counts.save_failed) parts.push(`${counts.save_failed} save err`);
      monoEl.textContent = parts.join(' · ');
    }
  }

  // Open the streaming connection. Falls back to the non-streaming
  // endpoint if the stream errors (e.g. older proxy without buffering off).
  (async () => {
    let usedStream = true;
    let result = await api.extractTasksStream({
      chats,
      onMeta: (m) => { counts.total = m.total || counts.total; },
      onChat: applyChatEvent,
      onError: async (err) => {
        console.warn('extract stream errored, falling back:', err);
        usedStream = false;
        const res = await api.extractTasks(chats);
        if (!res.ok) {
          finalizeWithError(res.error || 'Failed to extract tasks');
          return;
        }
        // Build a per-jid map and replay all events at once.
        const detailByJid = new Map(
          (res.details || []).map((d) => [d.jid, d])
        );
        queueItems.forEach((q) => {
          const jid = q.dataset.jid;
          const d = detailByJid.get(jid);
          if (d) applyChatEvent(d);
        });
        finalize();
      },
      onDone: () => finalize(),
    });

    if (usedStream && !result.ok) {
      finalizeWithError(result.error || 'Stream interrupted');
    }
  })();

  function finalize() {
    clearInterval(tick);
    clearInterval(visualTick);
    refreshHeadline();
    const done = counts.ok + counts.no_messages + counts.gemini_failed + counts.save_failed;
    if (done >= counts.total) {
      msgEl.textContent = counts.gemini_failed === 0 && counts.save_failed === 0
        ? 'Done — opening Kanban…'
        : 'Done with issues — opening Kanban…';
      progressEl.textContent = `${done} / ${counts.total} Complete`;
    }
    setTimeout(() => setPhase(PHASE.KANBAN), 900);
  }

  function finalizeWithError(errMsg) {
    clearInterval(tick);
    clearInterval(visualTick);
    msgEl.textContent = `Error: ${errMsg}`;
    monoEl.textContent = 'Pipeline aborted';
    queueItems.forEach((q) => {
      if (q.classList.contains('is-done') || q.classList.contains('is-warn') || q.classList.contains('is-fail')) return;
      const status = q.querySelector('.extract-queue-item-status');
      const icon = q.querySelector('.material-symbols-outlined');
      q.classList.remove('is-active', 'is-pending');
      icon.textContent = 'error';
      status.textContent = 'Failed';
    });
  }
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function escapeAttr(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

// History drawer — shows recent sent messages.
export function renderHistoryDrawer(drawer, history, onClose) {
  drawer.innerHTML = `
    <div class="drawer-head">
      <div class="drawer-eyebrow">
        <span class="material-symbols-outlined" style="color:var(--primary)">history</span>
        <span style="color:var(--on-surface-muted)">Nudge history</span>
      </div>
      <h2 class="drawer-title">Sent messages</h2>
      <button class="drawer-close" data-close aria-label="Close">
        <span class="material-symbols-outlined">close</span>
      </button>
    </div>
    <div class="drawer-body">
      ${
        history.length === 0
          ? `<div class="empty-state">
               <span class="material-symbols-outlined">forum</span>
               No messages sent yet.
             </div>`
          : history
              .map(
                (h) => `
          <div class="history-item">
            <div class="history-meta">
              <span class="material-symbols-outlined">schedule</span>
              <span class="history-time">${formatTime(h.sent_at)}</span>
              <span style="color:var(--outline-variant)">·</span>
              <span class="history-group">${escapeHtml(h.group_name || '')}</span>
            </div>
            <div class="history-task">${escapeHtml(h.task_title || '')}</div>
            <div class="history-text">${escapeHtml(h.sent_text || '')}</div>
          </div>
        `
              )
              .join('')
      }
    </div>
  `;
  drawer.querySelector('[data-close]').addEventListener('click', onClose);
}

function formatTime(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    if (isNaN(d.getTime())) return iso;
    return d.toLocaleString();
  } catch {
    return iso;
  }
}

function escapeHtml(s) {
  return String(s || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

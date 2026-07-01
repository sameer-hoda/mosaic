// Task detail drawer — sectioned layout with stacked variant cards
// (Concise / Moderate / Contextual) and per-card Send button.
import { api } from '../api.js';

const VARIANTS = [
  { key: 'concise',      label: 'Concise',     tagline: 'Quick check-in' },
  { key: 'moderate',     label: 'Moderate',    tagline: 'Polite follow-up' },
  { key: 'with_context', label: 'Contextual',  tagline: 'Detailed, references chat' },
];

const STATUS_FLOW = [
  { key: 'not started', label: 'Not Started' },
  { key: 'pending',     label: 'Pending' },
  { key: 'done',        label: 'Done' },
];

export function renderTaskDrawer(drawer, task, opts) {
  const { onClose, onUpdateStatus, onSend } = opts;
  const responses = task.suggested_responses || {};
  const status = taskStatusBadge(task.status);

  drawer.innerHTML = `
    <div class="drawer-head">
      <div class="drawer-eyebrow">
        <span class="badge ${status.cls}">
          <span class="dot"></span>${status.label}
        </span>
        <span class="material-symbols-outlined">forum</span>
        <span style="color:var(--on-surface-muted)">${escapeHtml(task.group_name || 'Group')}</span>
      </div>
      <h2 class="drawer-title">${escapeHtml(task.title)}</h2>
      <button class="drawer-close" data-close aria-label="Close">
        <span class="material-symbols-outlined">close</span>
      </button>
    </div>

    <div class="drawer-body">
      <section class="drawer-section">
        <div class="section-label"><span>Details</span></div>
        ${task.assignee ? `
          <div class="drawer-kv">
            <span class="drawer-kv-label">Assignee</span>
            <span class="assignee-pill">@${escapeHtml(task.assignee)}</span>
          </div>
        ` : ''}
        ${task.theme_name ? `
          <div class="drawer-kv">
            <span class="drawer-kv-label">Theme</span>
            <span class="badge badge-work">${escapeHtml(task.theme_name)}</span>
          </div>
        ` : ''}
        <div class="drawer-kv">
          <span class="drawer-kv-label">Source</span>
          <span class="drawer-kv-val">
            <span class="material-symbols-outlined" style="font-size:16px;color:var(--on-surface-muted)">groups</span>
            ${escapeHtml(task.group_name || '—')}
          </span>
        </div>
      </section>

      <div class="drawer-divider"></div>

      <section class="drawer-section">
        <div class="section-label"><span>Conversation Context</span></div>
        <div class="context-text">${escapeHtml(task.context || 'No context available.')}</div>
      </section>

      <div class="drawer-divider"></div>

      <section class="drawer-section">
        <div class="section-label"><span>Move to</span></div>
        <div class="status-flow" data-status-flow>
          ${STATUS_FLOW.map(
            (s) => `
              <button class="status-flow-btn ${s.key === task.status ? 'is-active' : ''}" data-status="${s.key}">
                ${s.label}
              </button>
            `
          ).join('')}
        </div>
      </section>

      <div class="drawer-divider"></div>

      <section class="drawer-section" data-suggest-section>
        <div class="section-label">
          <span>Suggested Actions</span>
          <span class="section-hint">Sent as you to the group</span>
        </div>
        <div class="response-stack" data-response-stack>
          ${VARIANTS.map((v) => {
            const text = responses[v.key] || '';
            return `
              <div class="response-card" data-variant="${v.key}">
                <div class="response-card-head">
                  <div class="response-card-titles">
                    <div class="response-card-label">${v.label}</div>
                    <div class="response-card-tagline">${v.tagline}</div>
                  </div>
                  <button class="btn btn-primary response-send-btn" data-send-variant="${v.key}" ${text ? '' : 'disabled'}>
                    <span class="material-symbols-outlined" style="font-size:16px">send</span>
                    Send
                  </button>
                </div>
                <div class="response-text">${escapeHtml(text) || '<span class="response-empty">No suggestion available.</span>'}</div>
              </div>
            `;
          }).join('')}
        </div>
      </section>
    </div>
  `;

  drawer.querySelector('[data-close]').addEventListener('click', onClose);

  drawer.querySelectorAll('[data-status]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const newStatus = btn.dataset.status;
      if (newStatus === task.status) return;
      await onUpdateStatus(newStatus);
      renderTaskDrawer(drawer, { ...task, status: newStatus }, opts);
    });
  });

  drawer.querySelectorAll('[data-send-variant]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const variant = btn.dataset.sendVariant;
      const text = responses[variant];
      if (!text) return;

      const stack = drawer.querySelectorAll('[data-send-variant]');
      stack.forEach((b) => { b.disabled = true; });
      const original = btn.innerHTML;
      btn.innerHTML = '<span class="spinner"></span> Sending…';

      const ok = await onSend(text);

      if (ok) {
        btn.innerHTML = '<span class="material-symbols-outlined" style="font-size:16px">check_circle</span> Sent!';
        setTimeout(onClose, 700);
      } else {
        btn.innerHTML = original;
        stack.forEach((b) => { b.disabled = false; });
      }
    });
  });
}

function taskStatusBadge(s) {
  if (s === 'done')        return { cls: 'badge-done',        label: 'Done' };
  if (s === 'pending')     return { cls: 'badge-pending',     label: 'Pending' };
  return                          { cls: 'badge-not-started', label: 'Not Started' };
}

function escapeHtml(s) {
  return String(s || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

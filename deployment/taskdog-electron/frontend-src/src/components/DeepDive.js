// DeepDive drawer — full task detail with wiki, people, timeline, blockers, decisions.
// Shows loading state while Stage 3 runs, then renders the full knowledge page.
import { api } from '../api.js';

const ROLE_LABELS = {
  assignee: 'Assignee',
  requestor: 'Requestor',
  reviewer: 'Reviewer',
  stakeholder: 'Stakeholder',
};

export function renderDeepDive(drawer, taskId, opts = {}) {
  const { onClose, onTaskUpdated } = opts;

  drawer.innerHTML = `
    <div class="dd-loading">
      <div class="dd-loading-head">
        <button class="dd-close" data-close>
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      <div class="dd-loading-body">
        <span class="spinner dd-spinner"></span>
        <h3>Analysing task…</h3>
        <p>Reading the full group transcript and building a knowledge page. This takes 5-20 seconds.</p>
      </div>
    </div>
  `;

  drawer.querySelector('[data-close]').addEventListener('click', onClose);

  // Load the task first, then trigger deep-dive if needed
  loadAndRender(drawer, taskId, onClose, onTaskUpdated);
}

async function loadAndRender(drawer, taskId, onClose, onTaskUpdated) {
  // First fetch the task
  const taskRes = await api.getTask(taskId);
  if (!taskRes.ok) {
    drawer.innerHTML = `
      <div class="dd-error">
        <button class="dd-close" data-close><span class="material-symbols-outlined">close</span></button>
        <div class="dd-error-body">
          <span class="material-symbols-outlined">error</span>
          <h3>Task not found</h3>
          <p>${escapeHtml(taskRes.error || '')}</p>
        </div>
      </div>
    `;
    drawer.querySelector('[data-close]').addEventListener('click', onClose);
    return;
  }

  const task = taskRes.task;

  // If task already has a deep-dive, show it immediately
  if (task.wiki) {
    renderFullTask(drawer, task, onClose, onTaskUpdated);
    return;
  }

  // Otherwise, trigger deep-dive
  const ddRes = await api.deepDive(taskId);
  if (ddRes.ok && ddRes.task) {
    renderFullTask(drawer, ddRes.task, onClose, onTaskUpdated);
  } else {
    drawer.innerHTML = `
      <div class="dd-error">
        <button class="dd-close" data-close><span class="material-symbols-outlined">close</span></button>
        <div class="dd-error-body">
          <span class="material-symbols-outlined">error</span>
          <h3>Deep-dive failed</h3>
          <p>${escapeHtml(ddRes.error || 'Unknown error')}</p>
          <button class="btn" data-retry>Retry</button>
        </div>
      </div>
    `;
    drawer.querySelector('[data-close]').addEventListener('click', onClose);
    drawer.querySelector('[data-retry]')?.addEventListener('click', () => {
      renderDeepDive(drawer, taskId, { onClose, onTaskUpdated });
    });
  }
}

function renderFullTask(drawer, task, onClose, onTaskUpdated) {
  const people = task.people || [];
  const progressLog = task.progress_log || [];
  const blockers = task.blockers || [];
  const decisions = task.decisions || [];
  const impDots = '⬤'.repeat(task.importance) + '◯'.repeat(5 - task.importance);

  drawer.innerHTML = `
    <div class="dd-drawer">
      <div class="dd-head">
        <div class="dd-head-top">
          <div class="dd-badges">
            <span class="badge badge-${task.status}">
              <span class="dot"></span>${task.status}
            </span>
            <span class="dd-importance" title="${task.importance}/5">${impDots}</span>
          </div>
          <button class="dd-close" data-close>
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        <h2 class="dd-title">${escapeHtml(task.title)}</h2>
        <div class="dd-meta">
          ${task.assignee ? `<span class="dd-assignee"><span class="material-symbols-outlined" style="font-size:14px">person</span>${escapeHtml(task.assignee)}</span>` : ''}
          ${task.group_name ? `<span class="dd-group"><span class="material-symbols-outlined" style="font-size:14px">groups</span>${escapeHtml(task.group_name)}</span>` : ''}
        </div>
      </div>

      <div class="dd-body">
        ${task.context ? `
          <section class="dd-section">
            <div class="section-label"><span>Context</span></div>
            <div class="dd-context">${escapeHtml(task.context)}</div>
          </section>
        ` : ''}

        ${task.wiki ? `
          <section class="dd-section">
            <div class="section-label"><span>Knowledge Page</span></div>
            <div class="dd-wiki">${renderMarkdown(task.wiki)}</div>
          </section>
        ` : ''}

        ${people.length > 0 ? `
          <section class="dd-section">
            <div class="section-label"><span>People (${people.length})</span></div>
            <div class="dd-people">
              ${people.map((p) => `
                <div class="dd-person">
                  <div class="dd-person-avatar">${escapeHtml((p.name || '?')[0])}</div>
                  <div class="dd-person-info">
                    <div class="dd-person-name">${escapeHtml(p.name || 'Unknown')}</div>
                    <div class="dd-person-role">${ROLE_LABELS[p.role] || p.role || ''}</div>
                  </div>
                </div>
              `).join('')}
            </div>
          </section>
        ` : ''}

        ${progressLog.length > 0 ? `
          <section class="dd-section">
            <div class="section-label"><span>Progress Timeline (${progressLog.length})</span></div>
            <div class="dd-timeline">
              ${progressLog.map((e) => `
                <div class="dd-timeline-item">
                  <div class="dd-timeline-dot"></div>
                  <div class="dd-timeline-content">
                    <div class="dd-timeline-date">${escapeHtml(e.date)}</div>
                    <div class="dd-timeline-summary">${escapeHtml(e.summary)}</div>
                  </div>
                </div>
              `).join('')}
            </div>
          </section>
        ` : ''}

        ${blockers.length > 0 ? `
          <section class="dd-section">
            <div class="section-label"><span>Blockers (${blockers.length})</span></div>
            <div class="dd-cards">
              ${blockers.map((b) => `
                <div class="dd-card dd-card-blocker">
                  <div class="dd-card-desc">${escapeHtml(b.description)}</div>
                  <div class="dd-card-meta">
                    <span>${escapeHtml(b.raised_by || 'Unknown')}</span>
                    <span>${escapeHtml(b.date || '')}</span>
                  </div>
                </div>
              `).join('')}
            </div>
          </section>
        ` : ''}

        ${decisions.length > 0 ? `
          <section class="dd-section">
            <div class="section-label"><span>Decisions (${decisions.length})</span></div>
            <div class="dd-cards">
              ${decisions.map((d) => `
                <div class="dd-card dd-card-decision">
                  <div class="dd-card-desc">${escapeHtml(d.description)}</div>
                  <div class="dd-card-meta">
                    <span>${escapeHtml(d.made_by || 'Unknown')}</span>
                    <span>${escapeHtml(d.date || '')}</span>
                  </div>
                </div>
              `).join('')}
            </div>
          </section>
        ` : ''}

        <section class="dd-section">
          <div class="section-label"><span>Actions</span></div>
          <div class="dd-actions">
            <button class="btn" data-rerun-dd>
              <span class="material-symbols-outlined" style="font-size:16px">refresh</span>
              Re-run Deep Dive
            </button>
            <select class="dd-status-select" data-status-select>
              <option value="">Change status…</option>
              <option value="active" ${task.status === 'active' ? 'selected' : ''}>Active</option>
              <option value="completed" ${task.status === 'completed' ? 'selected' : ''}>Completed</option>
              <option value="archived" ${task.status === 'archived' ? 'selected' : ''}>Archived</option>
            </select>
            <select class="dd-importance-select" data-importance-select>
              <option value="">Change importance…</option>
              ${[1,2,3,4,5].map((i) => `<option value="${i}" ${task.importance === i ? 'selected' : ''}>${i} — ${['','Trivial','Minor','Normal','Important','Critical'][i]}</option>`).join('')}
            </select>
          </div>
        </section>
      </div>
    </div>
  `;

  drawer.querySelector('[data-close]').addEventListener('click', onClose);

  drawer.querySelector('[data-rerun-dd]')?.addEventListener('click', async () => {
    drawer.innerHTML = `
      <div class="dd-loading">
        <div class="dd-loading-head">
          <button class="dd-close" data-close><span class="material-symbols-outlined">close</span></button>
        </div>
        <div class="dd-loading-body">
          <span class="spinner dd-spinner"></span>
          <h3>Re-analysing task…</h3>
        </div>
      </div>
    `;
    drawer.querySelector('[data-close]').addEventListener('click', onClose);
    const ddRes = await api.deepDive(taskId);
    if (ddRes.ok && ddRes.task) {
      renderFullTask(drawer, ddRes.task, onClose, onTaskUpdated);
      if (onTaskUpdated) onTaskUpdated();
    }
  });

  drawer.querySelector('[data-status-select]')?.addEventListener('change', async (e) => {
    const status = e.target.value;
    if (!status) return;
    await api.updateTask(taskId, { status });
    if (onTaskUpdated) onTaskUpdated();
  });

  drawer.querySelector('[data-importance-select]')?.addEventListener('change', async (e) => {
    const importance = parseInt(e.target.value);
    if (!importance) return;
    await api.updateTask(taskId, { importance });
    if (onTaskUpdated) onTaskUpdated();
  });
}

// Minimal Markdown renderer (headings, bold, bullet lists, paragraphs)
function renderMarkdown(md) {
  if (!md) return '';
  let html = escapeHtml(md);
  // Headings
  html = html.replace(/^### (.+)$/gm, '<h4>$1</h4>');
  html = html.replace(/^## (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^# (.+)$/gm, '<h2>$1</h2>');
  // Bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  // Bullet lists
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
  // Paragraphs (split on double newline)
  html = html.split(/\n\n+/).map((block) => {
    if (block.startsWith('<h') || block.startsWith('<ul')) return block;
    return `<p>${block.replace(/\n/g, '<br>')}</p>`;
  }).join('\n');
  return html;
}

function escapeHtml(s) {
  return String(s || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

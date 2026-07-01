// v2 Dashboard — Light + Dark mode. List layout, collapsible modal, nudge panel.
import { api } from '../api.js';

const IMP_LABEL = { 1: '\u2B50', 2: '\u2B50', 3: '\u2B50', 4: '\u2B50\u2B50', 5: '\u2B50\u2B50\u2B50' };
const IMP_CLS = { 1: 'is-imp1', 2: 'is-imp2', 3: 'is-imp3', 4: 'is-imp4', 5: 'is-imp5' };

const ROLE_LABELS = {
  assignee: 'Assignee', requestor: 'Requestor', reviewer: 'Reviewer', stakeholder: 'Stakeholder',
};

const STATUS_CHIP_CLASS = {
  active: 'is-active', completed: 'is-completed', archived: 'is-archived',
};

function escapeHtml(s) {
  return String(s || '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function initials(name) {
  if (!name) return '??';
  const clean = name.replace(/@.*$/, '');
  const parts = clean.trim().split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  return clean.substring(0, 2).toUpperCase();
}

function timeAgo(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    if (isNaN(d.getTime())) return '';
    const diffMs = Date.now() - d.getTime();
    const mins = Math.floor(diffMs / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  } catch { return ''; }
}

function formatDate(iso) {
  if (!iso) return '';
  try { return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }); }
  catch { return ''; }
}

function formatRelativeDate(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    const now = new Date();
    const diffDays = Math.floor((now - d) / 86400000);
    if (diffDays === 0) return 'Created today';
    if (diffDays === 1) return 'Created yesterday';
    if (diffDays < 7) return `Created ${diffDays}d ago`;
    return `Created ${d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
  } catch { return ''; }
}

function formatDateTime(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
      + ' \u00b7 ' + d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  } catch { return ''; }
}

// ─── Main render ──────────────────────────────────────────────────

export function renderDashboard(root, state) {
  const wrap = document.createElement('section');
  wrap.className = 'phase dash-v2 fade-in';
  root.appendChild(wrap);

  let tasks = [], groups = [], stats = null, activeFilter = 'all', searchQuery = '';
  let adminJids = [];

  wrap.innerHTML = `
    <div class="dash-v2-container">
      <div class="dash-v2-stats" data-stats></div>
      <div class="dash-v2-search" data-search-row>
        <div class="dash-v2-search-input-wrap">
          <span class="material-symbols-outlined dash-v2-search-icon">search</span>
          <input class="dash-v2-search-input" placeholder="Search tasks\u2026" data-search-input type="text" />
        </div>
      </div>
      <div class="dash-v2-filters" data-filters></div>
      <div class="dash-v2-progress" data-progress style="display:none"></div>
      <div data-task-area>
        <div class="dash-v2-empty"><span class="spinner"></span> Loading\u2026</div>
      </div>
    </div>
  `;

  const $ = (s) => wrap.querySelector(s);
  const els = {
    stats: $('[data-stats]'),
    searchInput: $('[data-search-input]'),
    filters: $('[data-filters]'),
    progress: $('[data-progress]'),
    taskArea: $('[data-task-area]'),
  };

  async function load() {
    const [dashRes, groupsRes] = await Promise.all([
      api.getDashboard(), api.getGroupsV2(),
    ]);
    if (!dashRes.ok) {
      els.taskArea.innerHTML = `<div class="dash-v2-empty"><h3>Error</h3><p>${escapeHtml(dashRes.error || 'Failed')}</p></div>`;
      return;
    }
    tasks = dashRes.tasks || [];
    stats = dashRes.stats || null;
    groups = (groupsRes.ok && groupsRes.groups) ? groupsRes.groups : [];
    renderStats();
    renderFilters();
    renderAll();

    if (state.autoDiscover && tasks.length === 0 && groups.length > 0) {
      state.autoDiscover = false;
      await runDiscover();
      await load();
    }
  }

  function renderStats() {
    if (!stats) return;
    const parts = [];
    parts.push(`<strong>${stats.total}</strong> tasks`);
    if (stats.importance_5) parts.push(`<strong>${stats.importance_5}</strong> critical`);
    if (stats.completed) parts.push(`<strong>${stats.completed}</strong> done`);
    if (stats.last_refreshed) parts.push(`refreshed ${timeAgo(stats.last_refreshed)}`);
    els.stats.innerHTML = parts.map((p, i) =>
      `${p}${i < parts.length - 1 ? ' <span class="sep"></span> ' : ''}`
    ).join('')
      + `<span style="margin-left:auto;display:flex;gap:8px">
          <button class="dash-v2-header-btn" data-action="discover"><span class="material-symbols-outlined">search</span> Discover</button>
          <button class="dash-v2-header-btn" data-action="refresh"><span class="material-symbols-outlined">refresh</span> Refresh</button>
        </span>`;
    els.stats.querySelector('[data-action="discover"]').addEventListener('click', runDiscover);
    els.stats.querySelector('[data-action="refresh"]').addEventListener('click', runRefresh);
  }

  function renderFilters() {
    const groups = [
      { id: 'all', label: 'All' },
      { id: 'critical', label: 'Critical' },
      { id: 'high', label: 'High' },
      null, // separator
      { id: 'active', label: 'Active' },
      null, // separator
      { id: 'work', label: 'Work' },
      { id: 'personal', label: 'Personal' },
    ];
    els.filters.innerHTML = groups.map((g) => {
      if (!g) return '<span class="dash-v2-filter-sep"></span>';
      return `<button class="dash-v2-filter-pill${activeFilter === g.id ? ' is-active' : ''}" data-filter="${g.id}">${g.label}</button>`;
    }).join('');
    els.filters.querySelectorAll('[data-filter]').forEach((btn) => {
      btn.addEventListener('click', () => { activeFilter = btn.dataset.filter; renderFilters(); renderAll(); });
    });
  }

  function filteredTasks() {
    let f = [...tasks];
    if (activeFilter === 'critical') f = f.filter((t) => t.importance === 5);
    if (activeFilter === 'high') f = f.filter((t) => t.importance >= 4);
    if (activeFilter === 'active') f = f.filter((t) => t.status === 'active');
    if (activeFilter === 'work') {
      const jids = groups.filter((g) => g.category === 'Work').map((g) => g.jid);
      f = f.filter((t) => jids.includes(t.group_jid));
    }
    if (activeFilter === 'personal') {
      const jids = groups.filter((g) => g.category === 'Personal').map((g) => g.jid);
      f = f.filter((t) => jids.includes(t.group_jid));
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      f = f.filter((t) =>
        t.title.toLowerCase().includes(q) ||
        (t.context || '').toLowerCase().includes(q) ||
        (t.assignee || '').toLowerCase().includes(q) ||
        (t.group_name || '').toLowerCase().includes(q));
    }
    return f;
  }

  function renderAll() {
    const ft = filteredTasks();
    if (tasks.length === 0) {
      els.taskArea.innerHTML = `<div class="dash-v2-empty">
        <span class="material-symbols-outlined">inbox</span>
        <h3>No tasks discovered yet</h3>
        <p>Click Discover Tasks to scan your WhatsApp chats for action items.</p>
        <button class="btn btn-primary" data-discover-cta><span class="material-symbols-outlined">search</span> Discover Tasks</button>
      </div>`;
      els.taskArea.querySelector('[data-discover-cta]').addEventListener('click', runDiscover);
      return;
    }
    if (ft.length === 0) {
      els.taskArea.innerHTML = `<div class="dash-v2-empty">
        <span class="material-symbols-outlined">filter_alt_off</span>
        <h3>No matching tasks</h3><p>Try another filter or search term.</p></div>`;
      return;
    }

    const grouped = new Map();
    for (const t of ft) {
      if (!grouped.has(t.group_jid)) grouped.set(t.group_jid, []);
      grouped.get(t.group_jid).push(t);
    }

    // Sort tasks within each group: active first, then completed, then archived; higher imp first
    for (const [, groupTasks] of grouped) {
      groupTasks.sort((a, b) => {
        if (a.status !== 'active' && b.status === 'active') return 1;
        if (a.status === 'active' && b.status !== 'active') return -1;
        if (a.status === 'archived' && b.status === 'completed') return 1;
        if (a.status === 'completed' && b.status === 'archived') return -1;
        return (b.importance || 0) - (a.importance || 0);
      });
    }
    const entries = [...grouped.entries()];
    entries.sort((a, b) => {
      const a5 = a[1].some((t) => t.importance === 5);
      const b5 = b[1].some((t) => t.importance === 5);
      if (a5 !== b5) return a5 ? -1 : 1;
      return b[1].length - a[1].length;
    });

    const taskGroupJids = new Set(entries.map(([jid]) => jid));
    for (const g of groups) {
      if (!taskGroupJids.has(g.jid)) entries.push([g.jid, []]);
    }

    // Identify top-priority tasks (first 2 active IMP 5)
    const topPriorityIds = new Set();
    let topCount = 0;
    for (const [, groupTasks] of entries) {
      for (const t of groupTasks) {
        if (t.importance === 5 && t.status === 'active' && topCount < 2) {
          topPriorityIds.add(t.id);
          topCount++;
        }
      }
    }

    let html = '';
    for (const [jid, groupTasks] of entries) {
      const g = groups.find((x) => x.jid === jid);
      const name = g ? g.name : (groupTasks[0]?.group_name || jid);
      const cat = g ? g.category : 'Work';
      const count = groupTasks.length;

      html += `<div class="dash-v2-group" data-group-jid="${escapeHtml(jid)}">`;
      html += `<div class="dash-v2-group-head" data-group-toggle="${escapeHtml(jid)}">
        <span class="dash-v2-group-dot ${cat === 'Personal' ? 'is-personal' : 'is-work'}"></span>
        <span class="dash-v2-group-name">${escapeHtml(name)}</span>
        <span class="dash-v2-group-count">${count} ${count === 1 ? 'TASK' : 'TASKS'}</span>
        <span class="material-symbols-outlined dash-v2-group-chevron" style="font-size:18px">expand_more</span>
      </div>`;

      if (groupTasks.length === 0) {
        html += `<div class="dash-v2-group-empty">No active tasks. All clear!</div>`;
      } else {
        html += `<div class="dash-v2-tasks" data-group-body="${escapeHtml(jid)}">`;
        let taskIdx = 0;
        for (const t of groupTasks) {
          const isImp5 = t.importance === 5;
          const isImp4 = t.importance === 4;
          const impCls = IMP_CLS[t.importance] || 'is-imp3';
          const ago = timeAgo(t.updated_at || t.created_at);
          const date = formatDate(t.created_at);
          const av = initials(t.assignee);
          const isTop = topPriorityIds.has(t.id);
          const impRowCls = (isImp5 ? ' is-imp5' : isImp4 ? ' is-imp4' : (t.importance === 3 ? ' is-imp3' : ''))
            + (isTop ? ' is-top-priority' : '');
          const statusCls = t.status === 'active' ? 'is-active' : t.status === 'completed' ? 'is-completed' : 'is-archived';

          html += `<div class="task-row${impRowCls}" data-task-id="${escapeHtml(t.id)}">
            <div class="task-row-left">
              <div class="task-row-checkbox-wrap">
                <input type="checkbox" class="task-row-checkbox"
                  ${t.status === 'completed' ? 'checked' : ''}
                  ${t.status === 'archived' ? 'disabled' : ''}
                  data-checkbox-id="${escapeHtml(t.id)}"
                />
              </div>
              <div class="task-row-title-wrap">
                <div class="task-row-title-line">
                  <span class="task-row-title${t.status !== 'active' ? ' is-' + t.status : ''}">${escapeHtml(t.title)}</span>
                  <span class="task-row-imp-tag ${impCls}">${IMP_LABEL[t.importance]}</span>
                </div>
                <div class="task-row-meta">
                  <span class="task-row-meta-item">Updated ${ago || 'recently'}</span>
                  ${date ? `<span class="task-row-meta-sep"></span><span class="task-row-meta-item">${formatRelativeDate(t.created_at)}</span>` : ''}
                </div>
              </div>
            </div>
            <div class="task-row-right">
              <div class="task-row-status">
                <span class="task-row-status-dot ${statusCls}"></span>${t.status}
              </div>
              ${t.message_count > 0 ? `<div class="task-row-msg-count"><span class="material-symbols-outlined">chat_bubble</span>${t.message_count}</div>` : ''}
              <div class="task-row-avatar" title="${escapeHtml(t.assignee)}">${av}</div>
              <button class="task-row-deep-dive" data-deep-dive="${escapeHtml(t.id)}">
                ${t.has_deep_dive ? 'WIKI' : 'DEEP DIVE'}
              </button>
            </div>
          </div>`;
          taskIdx++;
        }
        html += `</div>`;
      }
      html += `</div>`;
    }
    els.taskArea.innerHTML = html;

    els.taskArea.querySelectorAll('.task-row').forEach((row) => {
      row.addEventListener('click', (e) => {
        if (e.target.closest('.task-row-deep-dive')) return;
        if (e.target.closest('.task-row-checkbox')) return;
        openModal(row.dataset.taskId);
      });
    });
    els.taskArea.querySelectorAll('.task-row-checkbox').forEach((cb) => {
      cb.addEventListener('change', async (e) => {
        e.stopPropagation();
        const taskId = cb.dataset.checkboxId;
        const newStatus = cb.checked ? 'completed' : 'active';
        const row = cb.closest('.task-row');
        try {
          await api.updateTask(taskId, { status: newStatus });
          if (newStatus === 'completed' && row) {
            row.classList.add('is-completing');
            row.addEventListener('animationend', () => load(), { once: true });
          } else {
            load();
          }
        } catch {
          cb.checked = !cb.checked;
        }
      });
    });
    els.taskArea.querySelectorAll('[data-deep-dive]').forEach((btn) => {
      btn.addEventListener('click', (e) => { e.stopPropagation(); openModal(btn.dataset.deepDive); });
    });
    els.taskArea.querySelectorAll('[data-group-toggle]').forEach((head) => {
      head.addEventListener('click', () => {
        const jid = head.dataset.groupToggle;
        const body = els.taskArea.querySelector(`[data-group-body="${jid}"]`);
        const chev = head.querySelector('.dash-v2-group-chevron');
        if (body) {
          body.style.display = body.style.display === 'none' ? '' : 'none';
          if (chev) chev.classList.toggle('is-open', body.style.display !== 'none');
        }
      });
    });
  }

  let searchTimer;
  els.searchInput.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => { searchQuery = els.searchInput.value; renderAll(); }, 200);
  });
  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); els.searchInput.focus(); }
  });

  // ════════════════════════════════════════════════════════════════
  // MODAL — single column, collapsible sections, nudge panel
  // ════════════════════════════════════════════════════════════════

  function openModal(taskId) {
    const existing = document.querySelector('.task-modal-overlay');
    if (existing) existing.remove();
    const overlay = document.createElement('div');
    overlay.className = 'task-modal-overlay';
    overlay.innerHTML = `<div class="task-modal">
      <div class="task-modal-loading"><span class="spinner"></span><h3>Loading task\u2026</h3></div>
    </div>`;
    document.body.appendChild(overlay);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) closeModal(); });

    loadTaskDetail(taskId)
      .then(({ task, messages }) => renderModalContent(overlay, task, messages))
      .catch((err) => {
        const m = overlay.querySelector('.task-modal');
        m.innerHTML = `<div class="task-modal-loading"><h3>Error</h3><p>${escapeHtml(err.message)}</p>
          <button class="btn" onclick="this.closest('.task-modal-overlay').remove()">Close</button></div>`;
      });
  }

  function closeModal() {
    const o = document.querySelector('.task-modal-overlay');
    if (o) o.remove();
  }

  async function loadTaskDetail(taskId) {
    const [taskRes, msgRes] = await Promise.all([
      api.getTask(taskId), api.getTaskMessages(taskId),
    ]);
    if (!taskRes.ok) throw new Error(taskRes.error || 'Task not found');
    return { task: taskRes.task, messages: (msgRes.ok && msgRes.messages) ? msgRes.messages : [] };
  }

  function renderModalContent(overlay, task, messages) {
    const impCls = IMP_CLS[task.importance] || 'is-imp3';
    const people = task.people || [];
    const progressLog = task.progress_log || [];
    const blockers = task.blockers || [];
    const decisions = task.decisions || [];
    const hasWiki = !!task.wiki;
    const hasDeepDiveData = hasWiki || people.length > 0 || progressLog.length > 0;
    const av = initials(task.assignee);
    const statusCls = STATUS_CHIP_CLASS[task.status] || 'is-active';

    const modal = overlay.querySelector('.task-modal');
    modal.innerHTML = `
      <div class="task-modal-head">
        <div class="task-modal-head-left">
          <span class="task-modal-imp-tag ${impCls}">${IMP_LABEL[task.importance]}</span>
          <span class="task-modal-title">${escapeHtml(task.title)}</span>
        </div>
        <div class="task-modal-head-right">
          <button class="task-modal-close" data-close><span class="material-symbols-outlined">close</span></button>
        </div>
      </div>
      <div class="task-modal-meta">
        <div class="task-modal-meta-group">
          <span class="task-modal-meta-label">ASSIGNEE</span>
          <div class="task-modal-meta-value">
            ${task.assignee ? `<div class="task-row-avatar">${av}</div>` : ''}
            <span>${escapeHtml(task.assignee || 'Unassigned')}</span>
          </div>
        </div>
        <div class="task-modal-meta-sep"></div>
        <div class="task-modal-meta-group">
          <span class="task-modal-meta-label">STATUS</span>
          <div class="task-modal-meta-value">
            <span class="task-row-chip-dot ${statusCls}"></span>
            <span>${task.status}</span>
          </div>
        </div>
        <div class="task-modal-meta-sep"></div>
        <div class="task-modal-meta-group">
          <span class="task-modal-meta-label">GROUP</span>
          <div class="task-modal-meta-value">
            <span class="material-symbols-outlined">groups</span>
            <span>${escapeHtml(task.group_name || 'Unknown')}</span>
          </div>
        </div>
      </div>

      <div class="task-modal-body">
        ${task.context ? `
          <div class="task-modal-overview">
            <div class="task-modal-overview-text">${escapeHtml(task.context)}</div>
          </div>
        ` : ''}

        ${hasDeepDiveData ? `
          ${hasWiki ? `
            <div class="task-modal-collapse">
              <div class="task-modal-collapse-head" data-toggle="wiki">
                <div class="task-modal-collapse-head-left">
                  <span class="material-symbols-outlined" style="font-size:16px;color:var(--primary-container)">auto_awesome</span>
                  <span class="task-modal-collapse-label">Wiki (Deep-dive)</span>
                </div>
                <span class="material-symbols-outlined task-modal-collapse-chevron is-open" style="font-size:18px">expand_more</span>
              </div>
              <div class="task-modal-collapse-body" data-section="wiki">
                <div class="task-modal-wiki">${renderMarkdown(task.wiki)}</div>
              </div>
            </div>
          ` : ''}

          ${people.length > 0 ? `
            <div class="task-modal-collapse">
              <div class="task-modal-collapse-head" data-toggle="people">
                <div class="task-modal-collapse-head-left">
                  <span class="material-symbols-outlined" style="font-size:16px;color:var(--on-surface-variant)">group</span>
                  <span class="task-modal-collapse-label">People</span>
                  <span class="task-modal-collapse-count">(${people.length})</span>
                </div>
                <span class="material-symbols-outlined task-modal-collapse-chevron is-open" style="font-size:18px">expand_more</span>
              </div>
              <div class="task-modal-collapse-body" data-section="people">
                <div class="task-modal-people">
                  ${people.map((p) => `
                    <div class="task-modal-person">
                      <div class="task-modal-person-left">
                        <div class="task-modal-person-avatar">${initials(p.name)}</div>
                        <span class="task-modal-person-name">${escapeHtml(p.name || 'Unknown')}</span>
                      </div>
                      <span class="task-modal-person-role">${ROLE_LABELS[p.role] || p.role || ''}</span>
                    </div>
                  `).join('')}
                </div>
              </div>
            </div>
          ` : ''}

          ${progressLog.length > 0 ? `
            <div class="task-modal-collapse">
              <div class="task-modal-collapse-head" data-toggle="timeline">
                <div class="task-modal-collapse-head-left">
                  <span class="material-symbols-outlined" style="font-size:16px;color:var(--on-surface-variant)">timeline</span>
                  <span class="task-modal-collapse-label">Timeline</span>
                  <span class="task-modal-collapse-count">(${progressLog.length})</span>
                </div>
                <span class="material-symbols-outlined task-modal-collapse-chevron is-open" style="font-size:18px">expand_more</span>
              </div>
              <div class="task-modal-collapse-body" data-section="timeline">
                <div class="task-modal-timeline">
                  ${progressLog.map((e, i) => `
                    <div class="task-modal-tl-item">
                      <div class="task-modal-tl-dot${i === progressLog.length - 1 ? ' is-active' : ''}"></div>
                      <div class="task-modal-tl-date">${escapeHtml(e.date || '')}</div>
                      <div class="task-modal-tl-text">${escapeHtml(e.summary || '')}</div>
                    </div>
                  `).join('')}
                </div>
              </div>
            </div>
          ` : ''}

          ${blockers.length > 0 ? `
            <div class="task-modal-collapse">
              <div class="task-modal-collapse-head" data-toggle="blockers">
                <div class="task-modal-collapse-head-left">
                  <span class="material-symbols-outlined" style="font-size:16px;color:var(--st-pending)">block</span>
                  <span class="task-modal-collapse-label">Blockers</span>
                  <span class="task-modal-collapse-count">(${blockers.length})</span>
                </div>
                <span class="material-symbols-outlined task-modal-collapse-chevron is-open" style="font-size:18px">expand_more</span>
              </div>
              <div class="task-modal-collapse-body" data-section="blockers">
                ${blockers.map((b) => `
                  <div class="task-modal-info-card is-blocker" style="margin-bottom:8px">
                    <div class="task-modal-info-card-text">${escapeHtml(b.description)}</div>
                    <div class="task-modal-info-card-meta">
                      <span>${escapeHtml(b.raised_by || '')}</span>
                      <span>${escapeHtml(b.date || '')}</span>
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>
          ` : ''}

          ${decisions.length > 0 ? `
            <div class="task-modal-collapse">
              <div class="task-modal-collapse-head" data-toggle="decisions">
                <div class="task-modal-collapse-head-left">
                  <span class="material-symbols-outlined" style="font-size:16px;color:var(--on-surface-variant)">gavel</span>
                  <span class="task-modal-collapse-label">Decisions</span>
                  <span class="task-modal-collapse-count">(${decisions.length})</span>
                </div>
                <span class="material-symbols-outlined task-modal-collapse-chevron is-open" style="font-size:18px">expand_more</span>
              </div>
              <div class="task-modal-collapse-body" data-section="decisions">
                ${decisions.map((d) => `
                  <div class="task-modal-info-card" style="margin-bottom:8px">
                    <div class="task-modal-info-card-text">${escapeHtml(d.description)}</div>
                    <div class="task-modal-info-card-meta">
                      <span>${escapeHtml(d.made_by || '')}</span>
                      <span>${escapeHtml(d.date || '')}</span>
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>
          ` : ''}

          ${messages.length > 0 ? `
            <div class="task-modal-collapse">
              <div class="task-modal-collapse-head" data-toggle="evidence">
                <div class="task-modal-collapse-head-left">
                  <span class="material-symbols-outlined" style="font-size:16px;color:var(--on-surface-variant)">chat</span>
                  <span class="task-modal-collapse-label">Evidence Trail</span>
                  <span class="task-modal-collapse-count">(${messages.length})</span>
                </div>
                <span class="material-symbols-outlined task-modal-collapse-chevron" style="font-size:18px">expand_more</span>
              </div>
              <div class="task-modal-collapse-body is-hidden" data-section="evidence">
                ${messages.map((m) => {
                  const isSelf = (m.sender_name || '').toLowerCase().includes('you');
                  return `
                    <div class="evidence-item">
                      <div class="evidence-item-header">
                        <div class="evidence-avatar">${initials(m.sender_name || '?')}</div>
                        <span class="evidence-sender">${escapeHtml(m.sender_name || 'Unknown')}</span>
                        <span class="evidence-time">${formatDateTime(m.message_time)}</span>
                      </div>
                      <div class="evidence-bubble ${isSelf ? 'is-self' : 'is-other'}">${escapeHtml(m.message_content || '')}</div>
                    </div>
                  `;
                }).join('')}
              </div>
            </div>
          ` : ''}
        ` : `
          <div class="task-modal-dd-placeholder">
            <span class="material-symbols-outlined">auto_awesome</span>
            <p>Run a deep-dive to generate a knowledge page with timeline, people, and decisions.</p>
            <button class="btn btn-primary" data-run-dd>
              <span class="material-symbols-outlined">analytics</span> Run Deep Dive
            </button>
          </div>
        `}

        ${messages.length > 0 && !hasDeepDiveData ? `
          <div class="task-modal-collapse" style="margin-top:var(--s-md)">
            <div class="task-modal-collapse-head" data-toggle="evidence">
              <div class="task-modal-collapse-head-left">
                <span class="material-symbols-outlined" style="font-size:16px">chat</span>
                <span class="task-modal-collapse-label">Evidence Trail</span>
                <span class="task-modal-collapse-count">(${messages.length})</span>
              </div>
              <span class="material-symbols-outlined task-modal-collapse-chevron is-open" style="font-size:18px">expand_more</span>
            </div>
            <div class="task-modal-collapse-body" data-section="evidence">
              ${messages.map((m) => {
                const isSelf = (m.sender_name || '').toLowerCase().includes('you');
                return `
                  <div class="evidence-item">
                    <div class="evidence-item-header">
                      <div class="evidence-avatar">${initials(m.sender_name || '?')}</div>
                      <span class="evidence-sender">${escapeHtml(m.sender_name || 'Unknown')}</span>
                      <span class="evidence-time">${formatDateTime(m.message_time)}</span>
                    </div>
                    <div class="evidence-bubble ${isSelf ? 'is-self' : 'is-other'}">${escapeHtml(m.message_content || '')}</div>
                  </div>
                `;
              }).join('')}
            </div>
          </div>
        ` : ''}

        <!-- Nudge Panel -->
        <div class="nudge-panel">
          <div class="nudge-panel-head">
            <span class="material-symbols-outlined">send</span> Send Nudge via WhatsApp
          </div>
          <div class="nudge-options" data-nudge-options>
            <div class="nudge-loading"><span class="spinner"></span> Generating nudge options\u2026</div>
          </div>
        </div>
      </div>

      <div class="task-modal-footer">
        <div class="task-modal-status-pills">
          <button class="task-modal-status-pill${task.status === 'active' ? ' is-active' : ''}" data-status="active">Active</button>
          <button class="task-modal-status-pill${task.status === 'completed' ? ' is-active' : ''}" data-status="completed">Completed</button>
          <button class="task-modal-status-pill${task.status === 'archived' ? ' is-active' : ''}" data-status="archived">Archived</button>
        </div>
        ${!hasWiki ? `<button class="btn btn-primary" data-modal-dd>Run Deep Dive</button>` : ''}
      </div>
    `;

    modal.querySelector('[data-close]').addEventListener('click', closeModal);
    modal.querySelectorAll('[data-status]').forEach((pill) => {
      pill.addEventListener('click', async () => {
        const newStatus = pill.dataset.status;
        if (newStatus === task.status) return;
        await api.updateTask(task.id, { status: newStatus });
        closeModal();
        if (newStatus === 'completed' || newStatus === 'archived') {
          const row = document.querySelector(`.task-row[data-task-id="${task.id}"]`);
          if (row) {
            row.classList.add('is-completing');
            row.addEventListener('animationend', () => load(), { once: true });
          } else {
            load();
          }
        } else {
          load();
        }
      });
    });
    modal.querySelector('[data-modal-dd]')?.addEventListener('click', () => runDeepDiveInModal(overlay, task.id));
    modal.querySelector('[data-run-dd]')?.addEventListener('click', () => runDeepDiveInModal(overlay, task.id));

    // Wire collapsible sections
    modal.querySelectorAll('[data-toggle]').forEach((head) => {
      head.addEventListener('click', () => {
        const section = head.dataset.toggle;
        const body = modal.querySelector(`[data-section="${section}"]`);
        const chev = head.querySelector('.task-modal-collapse-chevron');
        if (body) {
          body.classList.toggle('is-hidden');
          if (chev) chev.classList.toggle('is-open', !body.classList.contains('is-hidden'));
        }
      });
    });

    // Generate nudges
    loadNudges(task.id, modal.querySelector('[data-nudge-options]'));
  }

  // ════════════════════════════════════════════════════════════════
  // NUDGES
  // ════════════════════════════════════════════════════════════════

  async function loadNudges(taskId, container) {
    try {
      const res = await api.generateNudges(taskId);
      if (!res.ok) throw new Error(res.error || 'Failed');
      const nudges = res.nudges || [];
      container.innerHTML = nudges.map((n, i) => `
        <div class="nudge-option" data-nudge-idx="${i}">
          <div class="nudge-option-head">
            <span class="nudge-option-tone ${n.tone === 'gentle' ? 'is-gentle' : n.tone === 'passive' ? 'is-passive' : 'is-aggressive'}">${n.tone || 'follow-up'}</span>
            <button class="nudge-option-send" data-send="${i}">
              <span class="material-symbols-outlined" style="font-size:14px">send</span> Send
            </button>
          </div>
          <div class="nudge-option-text">${escapeHtml(n.text || '')}</div>
        </div>
      `).join('');
      container.querySelectorAll('[data-send]').forEach((btn) => {
        btn.addEventListener('click', async (e) => {
          e.stopPropagation();
          const idx = parseInt(btn.dataset.send);
          const nudge = nudges[idx];
          if (!nudge) return;
          btn.disabled = true;
          btn.textContent = 'Sending\u2026';
          try {
            const sendRes = await api.sendNudge(taskId, nudge.text);
            if (sendRes.ok) {
              btn.textContent = 'Sent!';
              btn.style.color = 'var(--tertiary)';
              btn.style.borderColor = 'var(--tertiary)';
            } else {
              btn.textContent = 'Failed';
              btn.style.color = 'var(--error)';
              btn.style.borderColor = 'var(--error)';
            }
          } catch {
            btn.textContent = 'Error';
            btn.style.color = 'var(--error)';
          }
          setTimeout(() => { btn.disabled = false; }, 3000);
        });
      });
    } catch (err) {
      container.innerHTML = `<div style="padding:var(--s-md);font-size:13px;color:var(--on-surface-muted)">
        Could not generate nudges. ${escapeHtml(err.message)}</div>`;
    }
  }

  async function updateAndReload(taskId, data) {
    await api.updateTask(taskId, data);
    closeModal();
    load();
  }

  async function runDeepDiveInModal(overlay, taskId) {
    const modal = overlay.querySelector('.task-modal');
    modal.innerHTML = `<div class="task-modal-loading">
      <span class="spinner"></span><h3>Running Deep Dive</h3>
      <p>Reading the full transcript and building a knowledge page. 5\u201320 seconds.</p>
    </div>`;
    try {
      const res = await api.deepDive(taskId);
      if (!res.ok) throw new Error(res.error || 'Deep-dive failed');
      const [msgRes] = await Promise.all([api.getTaskMessages(taskId)]);
      const messages = (msgRes.ok && msgRes.messages) ? msgRes.messages : [];
      renderModalContent(overlay, res.task, messages);
    } catch (err) {
      modal.innerHTML = `<div class="task-modal-loading">
        <span class="material-symbols-outlined" style="font-size:36px;color:var(--error)">error</span>
        <h3>Deep-dive failed</h3><p>${escapeHtml(err.message)}</p>
        <button class="btn" onclick="this.closest('.task-modal-overlay').remove()">Close</button>
      </div>`;
    }
  }

  function renderMarkdown(md) {
    if (!md) return '';
    let html = escapeHtml(md);
    html = html.replace(/^### (.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^## (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^# (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    html = html.split(/\n\n+/).map((block) => {
      if (block.startsWith('<h') || block.startsWith('<ul')) return block;
      return `<p>${block.replace(/\n/g, '<br>')}</p>`;
    }).join('\n');
    return html;
  }

  async function runDiscover() {
    if (groups.length === 0) {
      els.progress.style.display = '';
      els.progress.innerHTML = '<div class="dash-v2-progress-inner dash-v2-progress-error">No groups whitelisted.</div>';
      return;
    }
    els.progress.style.display = '';
    els.progress.innerHTML = `<div class="dash-v2-progress-inner">
      <div class="dash-v2-progress-head"><span class="spinner"></span> Discovering tasks across ${groups.length} groups\u2026</div>
      <div data-stream-list></div></div>`;
    const sl = els.progress.querySelector('[data-stream-list]');
    await api.discoverTasksStream({
      jids: groups.map((g) => g.jid),
      onMeta: (m) => { els.progress.querySelector('.dash-v2-progress-head').innerHTML = `<span class="spinner"></span> Discovering across ${m.total} groups\u2026`; },
      onGroup: (g) => {
        const cls = g.status === 'ok' ? 'dash-v2-progress-ok' : g.status === 'no_messages' ? 'dash-v2-progress-warn' : 'dash-v2-progress-error';
        sl.innerHTML += `<div class="dash-v2-progress-item ${cls}"><span class="material-symbols-outlined">${g.status === 'ok' ? 'check_circle' : 'error'}</span> ${escapeHtml(g.name)} — ${g.task_count} tasks</div>`;
      },
      onDone: (d) => {
        els.progress.innerHTML = `<div class="dash-v2-progress-inner"><div class="dash-v2-progress-done"><span class="material-symbols-outlined">check_circle</span> Discovery: ${d.total_tasks_found} tasks in ${d.groups_with_tasks} groups.</div></div>`;
        setTimeout(() => { els.progress.style.display = 'none'; }, 5000);
        load();
      },
      onError: (e) => { els.progress.innerHTML = `<div class="dash-v2-progress-inner dash-v2-progress-error">Error: ${escapeHtml(e.error)}</div>`; },
    });
  }

  async function runRefresh() {
    if (groups.length === 0) return;
    els.progress.style.display = '';
    els.progress.innerHTML = `<div class="dash-v2-progress-inner">
      <div class="dash-v2-progress-head"><span class="spinner"></span> Refreshing tasks\u2026</div>
      <div data-stream-list></div></div>`;
    const sl = els.progress.querySelector('[data-stream-list]');
    await api.refreshTasksStream({
      jids: groups.map((g) => g.jid),
      onMeta: (m) => { els.progress.querySelector('.dash-v2-progress-head').innerHTML = `<span class="spinner"></span> Refreshing ${m.total_known_tasks} tasks\u2026`; },
      onTask: (t) => { sl.innerHTML += `<div class="dash-v2-progress-item dash-v2-progress-ok"><span class="material-symbols-outlined">update</span> ${escapeHtml(t.progress_note || t.status_update)}</div>`; },
      onNewTask: (nt) => { sl.innerHTML += `<div class="dash-v2-progress-item dash-v2-progress-ok"><span class="material-symbols-outlined">add_circle</span> New: ${escapeHtml(nt.title)}</div>`; },
      onDone: (d) => {
        els.progress.innerHTML = `<div class="dash-v2-progress-inner"><div class="dash-v2-progress-done"><span class="material-symbols-outlined">check_circle</span> Refresh: ${d.updated} updated, ${d.completed} done, ${d.new} new.</div></div>`;
        setTimeout(() => { els.progress.style.display = 'none'; }, 5000);
        load();
      },
      onError: (e) => { els.progress.innerHTML = `<div class="dash-v2-progress-inner dash-v2-progress-error">Error: ${escapeHtml(e.error)}</div>`; },
    });
  }

  load();
}
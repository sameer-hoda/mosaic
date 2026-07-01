// Phase 3 · Kanban
// 3-column board with sidebar group filter, task drawer, drag-and-drop.
// Stays in sync with the top-bar category tabs via the taskdog:setCategory event.
import { api } from '../api.js';
import { renderTaskDrawer } from './TaskDrawer.js';
import { renderHistoryDrawer } from './HistoryDrawer.js';
import { getState } from '../app.js';

const STATUSES = [
  { key: 'not started', label: 'Not Started', cls: 'st-not-started' },
  { key: 'pending',     label: 'Pending',     cls: 'st-pending' },
  { key: 'done',        label: 'Done',        cls: 'st-done' },
];

const CATEGORY_BADGE = {
  Work: 'badge-work',
  Personal: 'badge-personal',
  Others: 'badge-others',
};

export function renderKanban(root, state) {
  const wrap = document.createElement('section');
  wrap.className = 'phase phase-kanban fade-in';
  wrap.innerHTML = `
    <aside class="kanban-sidebar">
      <div>
        <div class="section-label">Category</div>
        <div class="chip-row" data-category-chips>
          <span class="chip" data-cat="all">All</span>
          <span class="chip" data-cat="Work">Work</span>
          <span class="chip" data-cat="Personal">Personal</span>
          <span class="chip" data-cat="Others">Others</span>
        </div>
      </div>
      <div>
        <div class="group-section-head">
          <div class="section-label">Groups</div>
          <div class="group-bulk">
            <button class="group-bulk-btn" data-bulk="all">All</button>
            <button class="group-bulk-btn" data-bulk="none">None</button>
            <button class="group-bulk-btn" data-bulk="invert">Invert</button>
          </div>
        </div>
        <div class="group-list" data-group-list>
          <div class="empty-mini">Loading…</div>
        </div>
      </div>
    </aside>

    <div class="kanban-main">
      <div class="kanban-head">
        <h2>Your Kanban</h2>
        <div class="kanban-meta" data-meta></div>
      </div>
      <div class="kanban-board" data-board>
        ${STATUSES.map(
          (s) => `
            <div class="kanban-col" data-col="${s.key}">
              <div class="kanban-col-head">
                <span class="col-dot ${s.cls}"></span>
                <span class="col-label">${s.label}</span>
                <span class="col-count" data-count="${s.key}">0</span>
              </div>
              <div class="col-body" data-drop="${s.key}"></div>
            </div>
          `
        ).join('')}
      </div>
    </div>
  `;
  root.appendChild(wrap);

  // Local state
  const allTasks = [];
  const allGroups = [];
  const visibleGroupJids = new Set();
  let activeCategory = (state.activeCategory && state.activeCategory !== 'all')
    ? state.activeCategory.charAt(0).toUpperCase() + state.activeCategory.slice(1)
    : 'all';

  // Sidebar chips reflect the top-bar tabs
  function refreshSidebarChips() {
    wrap.querySelectorAll('[data-cat]').forEach((c) => {
      c.classList.toggle('is-active', c.dataset.cat === activeCategory);
    });
  }
  refreshSidebarChips();

  // --- Data loading
  async function loadAll() {
    const [tasksRes, groupsRes] = await Promise.all([api.getTasks(), api.getGroups()]);
    if (tasksRes.ok) {
      allTasks.length = 0;
      allTasks.push(...tasksRes.tasks);
    }
    if (groupsRes.ok) {
      allGroups.length = 0;
      allGroups.push(...groupsRes.groups);
    }
    if (visibleGroupJids.size === 0 && allGroups.length > 0) {
      allGroups.forEach((g) => visibleGroupJids.add(g.jid));
    }
    renderGroups();
    renderBoard();
  }

  function renderGroups() {
    const list = wrap.querySelector('[data-group-list]');
    if (allGroups.length === 0) {
      list.innerHTML = '<div class="empty-mini">No groups yet.</div>';
      return;
    }
    list.innerHTML = allGroups
      .map(
        (g) => `
        <label class="group-item" data-jid="${escapeAttr(g.jid)}">
          <input type="checkbox" ${visibleGroupJids.has(g.jid) ? 'checked' : ''} />
          <span class="group-dot cat-${g.category}"></span>
          <span class="group-name">${escapeHtml(g.name)}</span>
          <span class="group-tldr">${escapeHtml(g.tldr || '')}</span>
        </label>
      `
      )
      .join('');

    list.querySelectorAll('.group-item').forEach((el) => {
      el.addEventListener('click', (ev) => {
        if (ev.target.tagName !== 'INPUT') {
          const cb = el.querySelector('input');
          cb.checked = !cb.checked;
        }
        const jid = el.dataset.jid;
        if (el.querySelector('input').checked) visibleGroupJids.add(jid);
        else visibleGroupJids.delete(jid);
        renderBoard();
      });
    });
  }

  function renderBoard() {
    const board = wrap.querySelector('[data-board]');
    const meta = wrap.querySelector('[data-meta]');

    const noGroupsSelected = visibleGroupJids.size === 0;
    const allGroupsSelected = visibleGroupJids.size === allGroups.length && allGroups.length > 0;

    const filtered = allTasks.filter((t) => {
      if (noGroupsSelected) return false;
      if (!allGroupsSelected) {
        if (!visibleGroupJids.has(t.group_jid)) return false;
      }
      if (activeCategory !== 'all') {
        const group = allGroups.find((g) => g.jid === t.group_jid);
        if (!group || group.category !== activeCategory) return false;
      }
      return true;
    });

    if (noGroupsSelected) {
      meta.textContent = 'No groups selected';
    } else if (allGroupsSelected) {
      meta.textContent = `${filtered.length} task${filtered.length === 1 ? '' : 's'} visible`;
    } else {
      meta.textContent = `${filtered.length} of ${allTasks.length} tasks visible · ${visibleGroupJids.size} of ${allGroups.length} groups`;
    }

    const byStatus = { 'not started': [], pending: [], done: [] };
    filtered.forEach((t) => byStatus[t.status]?.push(t));

    STATUSES.forEach((s) => {
      try {
        const col = board.querySelector(`[data-col="${s.key}"]`);
        if (!col) return;
        const body = col.querySelector(`[data-drop="${s.key}"]`);
        const countEl = col.querySelector(`[data-count="${s.key}"]`);
        body.innerHTML = '';
        const tasks = byStatus[s.key] || [];
        countEl.textContent = tasks.length;
        if (tasks.length === 0) {
          const empty = document.createElement('div');
          empty.className = 'col-empty';
          if (noGroupsSelected) {
            empty.innerHTML = `<span class="material-symbols-outlined">folder_off</span><p>Select a group on the left.</p>`;
          } else if (s.key === 'done') {
            empty.innerHTML = `<span class="material-symbols-outlined">check_circle</span><p>No completed tasks yet.</p>`;
          } else {
            empty.innerHTML = `<span class="material-symbols-outlined">inbox</span><p>Nothing here.</p>`;
          }
          body.appendChild(empty);
        } else {
          tasks.forEach((t) => body.appendChild(buildCard(t)));
        }
      } catch (err) {
        console.error(`[Kanban] failed to render column ${s.key}:`, err);
      }
    });

    enableDragAndDrop();
  }

  function buildCard(task) {
    const card = document.createElement('div');
    card.className = 'task-card';
    card.dataset.taskId = task.id;
    card.draggable = true;

    const status = STATUSES.find((s) => s.key === task.status) || STATUSES[0];
    const group = allGroups.find((g) => g.jid === task.group_jid);
    const groupCategory = group?.category || 'Others';

    card.innerHTML = `
      <div class="card-accent ${status.cls}"></div>
      <div class="card-row-1">
        <span class="badge ${CATEGORY_BADGE[groupCategory] || 'badge-others'}">${escapeHtml(groupCategory)}</span>
        ${task.assignee ? `<span class="assignee">@${escapeHtml(task.assignee)}</span>` : ''}
      </div>
      <div class="card-title">${escapeHtml(task.title)}</div>
      <div class="card-meta">
        <span class="card-theme">
          <span class="material-symbols-outlined" style="font-size:12px">${themeIcon(task.theme_name)}</span>
          ${escapeHtml(task.theme_name || 'Untitled')}
        </span>
        <span class="card-group">
          <span class="dot cat-${groupCategory}"></span>
          ${escapeHtml(task.group_name || '')}
        </span>
      </div>
    `;

    card.addEventListener('click', () => openDrawer(task));
    return card;
  }

  function themeIcon(theme) {
    const t = String(theme || '').toLowerCase();
    if (t.includes('review'))   return 'rate_review';
    if (t.includes('deploy'))   return 'rocket_launch';
    if (t.includes('plan'))     return 'event';
    if (t.includes('contact'))  return 'contact_page';
    if (t.includes('design'))   return 'palette';
    if (t.includes('marketing'))return 'campaign';
    if (t.includes('sales'))    return 'trending_up';
    if (t.includes('meeting'))  return 'groups';
    return 'topic';
  }

  function enableDragAndDrop() {
    const cards = wrap.querySelectorAll('.task-card');
    const cols = wrap.querySelectorAll('[data-drop]');
    let draggedId = null;

    cards.forEach((c) => {
      c.addEventListener('dragstart', (e) => {
        draggedId = c.dataset.taskId;
        c.classList.add('is-dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', draggedId);
      });
      c.addEventListener('dragend', () => {
        c.classList.remove('is-dragging');
        draggedId = null;
      });
    });

    cols.forEach((col) => {
      col.addEventListener('dragover', (e) => {
        e.preventDefault();
        col.classList.add('is-drag-over');
      });
      col.addEventListener('dragleave', () => col.classList.remove('is-drag-over'));
      col.addEventListener('drop', async (e) => {
        e.preventDefault();
        col.classList.remove('is-drag-over');
        const id = e.dataTransfer.getData('text/plain') || draggedId;
        const status = col.dataset.drop;
        if (!id) return;
        const t = allTasks.find((x) => x.id === id);
        if (!t || t.status === status) return;
        const prev = t.status;
        t.status = status;
        renderBoard();
        const res = await api.updateTaskStatus(id, status);
        if (!res.ok) {
          t.status = prev;
          renderBoard();
          alert(`Failed to update: ${res.error}`);
        }
      });
    });
  }

  function openDrawer(task) {
    const overlay = document.createElement('div');
    overlay.className = 'drawer-overlay';
    document.body.appendChild(overlay);
    const drawer = document.createElement('div');
    drawer.className = 'drawer';
    document.body.appendChild(drawer);

    function close() {
      overlay.remove();
      drawer.remove();
    }
    overlay.addEventListener('click', close);
    window.addEventListener('keydown', function esc(ev) {
      if (ev.key === 'Escape') { close(); window.removeEventListener('keydown', esc); }
    });

    renderTaskDrawer(drawer, task, {
      onClose: close,
      onUpdateStatus: async (newStatus) => {
        const prev = task.status;
        task.status = newStatus;
        const t = allTasks.find((x) => x.id === task.id);
        if (t) t.status = newStatus;
        renderBoard();
        const res = await api.updateTaskStatus(task.id, newStatus);
        if (!res.ok) {
          task.status = prev;
          if (t) t.status = prev;
          renderBoard();
          alert(`Failed to update: ${res.error}`);
        }
      },
      onSend: async (message) => {
        const res = await api.sendNudge(task.id, message, task.group_jid);
        if (!res.ok) {
          alert(`Send failed: ${res.error}`);
          return false;
        }
        task.status = 'pending';
        const t = allTasks.find((x) => x.id === task.id);
        if (t) t.status = 'pending';
        renderBoard();
        return true;
      },
    });
  }

  // --- History drawer
  const showHistory = async () => {
    const overlay = document.createElement('div');
    overlay.className = 'drawer-overlay';
    document.body.appendChild(overlay);
    const drawer = document.createElement('div');
    drawer.className = 'drawer drawer-wide';
    document.body.appendChild(drawer);
    function close() { overlay.remove(); drawer.remove(); }
    overlay.addEventListener('click', close);
    const res = await api.getHistory();
    renderHistoryDrawer(drawer, res.ok ? res.history : [], close);
  };
  window.addEventListener('taskdog:showHistory', showHistory);

  // --- Bulk group actions (All / None / Invert)
  wrap.querySelectorAll('[data-bulk]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const action = btn.dataset.bulk;
      if (action === 'all') {
        allGroups.forEach((g) => visibleGroupJids.add(g.jid));
      } else if (action === 'none') {
        visibleGroupJids.clear();
      } else if (action === 'invert') {
        allGroups.forEach((g) => {
          if (visibleGroupJids.has(g.jid)) visibleGroupJids.delete(g.jid);
          else visibleGroupJids.add(g.jid);
        });
      }
      renderGroups();
      renderBoard();
    });
  });

  // --- Category chips
  wrap.querySelectorAll('[data-cat]').forEach((chip) => {
    chip.addEventListener('click', () => {
      activeCategory = chip.dataset.cat;
      const s = getState();
      s.activeCategory = activeCategory === 'all' ? 'all' : activeCategory.toLowerCase();
      refreshSidebarChips();
      renderBoard();
    });
  });

  // --- Top bar tab sync
  window.addEventListener('taskdog:setCategory', (e) => {
    const cat = e.detail;
    activeCategory = cat === 'all' ? 'all' : cat.charAt(0).toUpperCase() + cat.slice(1);
    refreshSidebarChips();
    renderBoard();
  });

  loadAll();
}

function escapeHtml(s) {
  return String(s || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
function escapeAttr(s) {
  return String(s || '').replace(/"/g, '&quot;');
}

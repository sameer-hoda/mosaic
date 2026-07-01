// Centralised API client for the Mosaic backend.
// The Vite dev server proxies /api -> http://localhost:3001.

const BASE = '/api';

async function request(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  let data;
  try {
    data = await res.json();
  } catch {
    data = { ok: false, error: `Non-JSON response (${res.status})` };
  }
  if (!res.ok && data.ok !== false) {
    data = { ok: false, error: `HTTP ${res.status}` };
  }
  return data;
}

export const api = {
  health: () => request('/../health'),
  reset: () => request('/setup/reset', { method: 'POST' }),
  bridgeStatus: () => request('/bridge/status'),
  bridgeQR: () => request('/bridge/qr'),
  bridgeStart: () => request('/bridge/start', { method: 'POST' }),
  bridgeStop: () => request('/bridge/stop', { method: 'POST' }),
  getChats: () => request('/chats/list'),
  classifyChats: ({ force = false, limit } = {}) => {
    const qs = new URLSearchParams();
    if (force) qs.set('force', 'true');
    if (limit) qs.set('limit', String(limit));
    const suffix = qs.toString() ? `?${qs.toString()}` : '';
    return request('/chats/classify' + suffix, {
      method: 'POST',
      body: JSON.stringify({ force, limit }),
    });
  },

  // ─── v2 endpoints ────────────────────────────────────────────────
  healthV2: () => request('/health'),
  validateKey: (key) =>
    request('/setup/validate-key', { method: 'POST', body: JSON.stringify({ key }) }),
  whitelistGroups: (jids) =>
    request('/groups/whitelist', { method: 'POST', body: JSON.stringify({ jids }) }),
  getGroupsV2: () => request('/groups'),
  getDashboard: (groupJid) =>
    request(`/dashboard${groupJid ? `?group_jid=${encodeURIComponent(groupJid)}` : ''}`),
  getTask: (id) => request(`/tasks/${id}`),
  getTaskMessages: (id) => request(`/tasks/${id}/messages`),
  updateTask: (id, data) =>
    request(`/tasks/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  discoverTasks: (jids) =>
    request('/pipeline/discover', { method: 'POST', body: JSON.stringify({ group_jids: jids }) }),
  refreshTasks: (jids) =>
    request('/pipeline/refresh', { method: 'POST', body: JSON.stringify({ group_jids: jids }) }),
  deepDive: (taskId) =>
    request('/pipeline/deep-dive', { method: 'POST', body: JSON.stringify({ task_id: taskId }) }),

  // Streaming discover (Stage 1 SSE)
  discoverTasksStream: async ({ jids, onMeta, onGroup, onDone, onError } = {}) => {
    let res;
    try {
      res = await fetch(BASE + '/pipeline/discover/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ group_jids: jids }),
      });
    } catch (e) {
      if (onError) onError({ error: String(e) });
      return { ok: false, error: String(e) };
    }
    return _streamSSE(res, { meta: onMeta, group: onGroup, done: onDone, error: onError });
  },

  // Streaming refresh (Stage 2 SSE)
  refreshTasksStream: async ({ jids, onMeta, onTask, onNewTask, onDone, onError } = {}) => {
    let res;
    try {
      res = await fetch(BASE + '/pipeline/refresh/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ group_jids: jids }),
      });
    } catch (e) {
      if (onError) onError({ error: String(e) });
      return { ok: false, error: String(e) };
    }
    return _streamSSE(res, { meta: onMeta, task: onTask, new_task: onNewTask, done: onDone, error: onError });
  },
  // ─── end v2 endpoints ────────────────────────────────────────────

  // Streaming variant of classifyChats. Opens a fetch+ReadableStream and
  // invokes the provided callbacks as Server-Sent Events arrive.
  //   onMeta({total, cached_count, new_count})   — once, before chat events
  //   onChat({jid, name, category, tldr, is_whitelisted, from_cache})  — many
  //   onDone()                                    — once at the end
  //   onError({error})                            — fatal stream error
  classifyChatsStream: async ({ force = false, limit, onMeta, onChat, onDone, onError } = {}) => {
    let res;
    try {
      res = await fetch(BASE + '/chats/classify/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ force, limit }),
      });
    } catch (e) {
      if (onError) onError({ error: String(e) });
      return { ok: false, error: String(e) };
    }
    if (!res.ok) {
      if (onError) onError({ error: `HTTP ${res.status}` });
      return { ok: false, error: `HTTP ${res.status}` };
    }
    if (!res.body || !res.body.getReader) {
      if (onError) onError({ error: 'Streaming not supported in this browser.' });
      return { ok: false, error: 'Streaming not supported' };
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    try {
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        // Parse SSE events separated by blank lines.
        let idx;
        while ((idx = buffer.indexOf('\n\n')) >= 0) {
          const rawEvent = buffer.slice(0, idx);
          buffer = buffer.slice(idx + 2);
          let eventName = 'message';
          let dataStr = '';
          for (const line of rawEvent.split('\n')) {
            if (line.startsWith('event:')) eventName = line.slice(6).trim();
            else if (line.startsWith('data:')) dataStr += line.slice(5).trim();
          }
          if (!dataStr) continue;
          let data;
          try { data = JSON.parse(dataStr); } catch { data = null; }
          if (!data) continue;
          if (eventName === 'meta' && onMeta) onMeta(data);
          else if (eventName === 'chat' && onChat) onChat(data);
          else if (eventName === 'done' && onDone) onDone(data);
          else if (eventName === 'error' && onError) onError(data);
        }
      }
    } catch (e) {
      if (onError) onError({ error: String(e) });
      return { ok: false, error: String(e) };
    }
    return { ok: true };
  },

  updateChatCategory: (jid, category) =>
    request('/chats/classify/update_category', {
      method: 'POST',
      body: JSON.stringify({ jid, category }),
    }),
  extractTasks: (chats) =>
    request('/tasks/extract', { method: 'POST', body: JSON.stringify({ chats }) }),

  // Streaming variant of extractTasks. Emits one event per group as it
  // finishes so the UI can show real-time progress. Falls back to the
  // non-streaming endpoint if the browser doesn't support ReadableStream.
  //   onMeta({total})                                        — once
  //   onChat({jid, name, status, theme_count, task_count})  — many
  //   onDone({ok, total, processed, no_messages, gemini_empty, gemini_failed, save_failed})
  //   onError({error})                                       — fatal
  extractTasksStream: async ({ chats, onMeta, onChat, onDone, onError } = {}) => {
    let res;
    try {
      res = await fetch(BASE + '/tasks/extract/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chats }),
      });
    } catch (e) {
      if (onError) onError({ error: String(e) });
      return { ok: false, error: String(e) };
    }
    if (!res.ok) {
      if (onError) onError({ error: `HTTP ${res.status}` });
      return { ok: false, error: `HTTP ${res.status}` };
    }
    if (!res.body || !res.body.getReader) {
      if (onError) onError({ error: 'Streaming not supported in this browser.' });
      return { ok: false, error: 'Streaming not supported' };
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    try {
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        let idx;
        while ((idx = buffer.indexOf('\n\n')) >= 0) {
          const rawEvent = buffer.slice(0, idx);
          buffer = buffer.slice(idx + 2);
          let eventName = 'message';
          let dataStr = '';
          for (const line of rawEvent.split('\n')) {
            if (line.startsWith('event:')) eventName = line.slice(6).trim();
            else if (line.startsWith('data:')) dataStr += line.slice(5).trim();
          }
          if (!dataStr) continue;
          let data;
          try { data = JSON.parse(dataStr); } catch { data = null; }
          if (!data) continue;
          if (eventName === 'meta' && onMeta) onMeta(data);
          else if (eventName === 'chat' && onChat) onChat(data);
          else if (eventName === 'done' && onDone) onDone(data);
          else if (eventName === 'error' && onError) onError(data);
        }
      }
    } catch (e) {
      if (onError) onError({ error: String(e) });
      return { ok: false, error: String(e) };
    }
    return { ok: true };
  },
  getTasks: (groupJid) =>
    request(`/tasks${groupJid ? `?group_jid=${encodeURIComponent(groupJid)}` : ''}`),
  updateTaskStatus: (taskId, status) =>
    request('/tasks/update_status', {
      method: 'POST',
      body: JSON.stringify({ task_id: taskId, status }),
    }),
  sendNudge: (taskId, message) =>
    request('/send', {
      method: 'POST',
      body: JSON.stringify({ task_id: taskId, message }),
    }),
  getGroups: () => request('/groups'),
  getHistory: () => request('/history'),

  // ─── Nudge generation ─────────────────────────────────────────
  generateNudges: (taskId) =>
    request('/nudge/generate', { method: 'POST', body: JSON.stringify({ task_id: taskId }) }),

  // ─── Persona ──────────────────────────────────────────────────
  getPersona: () => request('/persona'),
  savePersona: (personaText) =>
    request('/persona', { method: 'POST', body: JSON.stringify({ persona: personaText }) }),
  generatePersona: () =>
    request('/persona/generate', { method: 'POST' }),
};

// ─── SSE stream parser (shared by v2 streaming endpoints) ───────────
async function _streamSSE(res, handlers = {}) {
  if (!res.ok) {
    if (handlers.error) handlers.error({ error: `HTTP ${res.status}` });
    return { ok: false, error: `HTTP ${res.status}` };
  }
  if (!res.body || !res.body.getReader) {
    if (handlers.error) handlers.error({ error: 'Streaming not supported in this browser.' });
    return { ok: false, error: 'Streaming not supported' };
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let idx;
      while ((idx = buffer.indexOf('\n\n')) >= 0) {
        const rawEvent = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 2);
        let eventName = 'message';
        let dataStr = '';
        for (const line of rawEvent.split('\n')) {
          if (line.startsWith('event:')) eventName = line.slice(6).trim();
          else if (line.startsWith('data:')) dataStr += line.slice(5).trim();
        }
        if (!dataStr) continue;
        let data;
        try { data = JSON.parse(dataStr); } catch { data = null; }
        if (!data) continue;
        const fn = handlers[eventName];
        if (fn) fn(data);
      }
    }
  } catch (e) {
    if (handlers.error) handlers.error({ error: String(e) });
    return { ok: false, error: String(e) };
  }
  return { ok: true };
}

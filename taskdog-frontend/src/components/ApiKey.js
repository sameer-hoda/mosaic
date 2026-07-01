// Gate A: Gemini API Key entry.
// Checks health, validates key against Gemini, then moves to Pairing.
import { api } from '../api.js';
import { PHASE, setPhase } from '../app.js';

export function renderApiKey(root, _state) {
  const wrap = document.createElement('section');
  wrap.className = 'phase phase-apikey fade-in';
  wrap.innerHTML = `
    <div class="apikey-card">
      <div class="apikey-brand">
        <div class="apikey-brand-mark">
          <img src="/mosaic-logo-mark.svg" alt="Mosaic" width="40" height="40" />
        </div>
        <div class="apikey-brand-text">
          <h2>Mosaic</h2>
          <p>Your life, pieced together.</p>
        </div>
      </div>

      <div class="apikey-body">
        <div class="apikey-step-label">Step 1 of 3 · API Key</div>
        <h3>Enter your Gemini API key</h3>
        <p class="apikey-desc">
          Mosaic uses Google Gemini to analyze your WhatsApp chats and extract tasks.
          Your key is stored securely in macOS Keychain and never sent to any server except Google.
        </p>

        <div class="apikey-input-row">
          <input
            type="password"
            class="apikey-input"
            placeholder="AIzaSy..."
            data-key-input
            autocomplete="off"
            spellcheck="false"
          />
          <button class="btn btn-primary" data-validate disabled>
            <span class="material-symbols-outlined" style="font-size:18px">key</span>
            Validate
          </button>
        </div>

        <div class="apikey-status" data-status></div>

        <div class="apikey-hint">
          <span class="material-symbols-outlined" style="font-size:16px">open_in_new</span>
          <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener">
            Get a free API key from Google AI Studio
          </a>
        </div>

        <div class="apikey-steps">
          <div class="apikey-step is-active">
            <div class="apikey-step-num">1</div>
            <span>API Key</span>
          </div>
          <div class="apikey-step">
            <div class="apikey-step-num">2</div>
            <span>WhatsApp Bridge</span>
          </div>
          <div class="apikey-step">
            <div class="apikey-step-num">3</div>
            <span>Select Groups</span>
          </div>
        </div>
      </div>
    </div>
  `;
  root.appendChild(wrap);

  const input = wrap.querySelector('[data-key-input]');
  const validateBtn = wrap.querySelector('[data-validate]');
  const status = wrap.querySelector('[data-status]');

  input.addEventListener('input', () => {
    validateBtn.disabled = input.value.trim().length < 10;
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !validateBtn.disabled) {
      validateBtn.click();
    }
  });

  validateBtn.addEventListener('click', async () => {
    const key = input.value.trim();
    if (!key) return;

    validateBtn.disabled = true;
    validateBtn.innerHTML = '<span class="spinner"></span> Validating…';
    status.innerHTML = '';

    const res = await api.validateKey(key);

    if (res.ok) {
      validateBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size:18px">check_circle</span> Valid!';
      status.innerHTML = `
        <div class="apikey-success">
          <span class="material-symbols-outlined">check_circle</span>
          Key validated successfully. Continuing to WhatsApp bridge…
        </div>
      `;

      // Persist key to Electron config.json (so it survives app restart)
      if (window.taskdog && window.taskdog.saveConfig) {
        window.taskdog.saveConfig({ geminiApiKey: key });
      }

      setTimeout(() => setPhase(PHASE.PAIRING), 1200);
    } else {
      validateBtn.disabled = false;
      validateBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size:18px">key</span> Validate';
      status.innerHTML = `
        <div class="apikey-error">
          <span class="material-symbols-outlined">error</span>
          ${escapeHtml(res.error || 'Validation failed')}
        </div>
      `;
    }
  });

  // If key is already set (from health check), show a "proceed" state
  if (_state.health && _state.health.gemini_key_set) {
    input.value = '';
    input.placeholder = `Key set (${_state.health.gemini_key_preview || '•••'})`;
    validateBtn.disabled = false;
    validateBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size:18px">arrow_forward</span> Continue';
    validateBtn.addEventListener('click', () => setPhase(PHASE.PAIRING), { once: true });
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

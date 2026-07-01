// Phase 1 · Pairing
// Polls /api/bridge/status + /api/bridge/qr and renders QR as SVG on screen.
import QRCode from 'qrcode';
import { api } from '../api.js';
import { PHASE, setPhase } from '../app.js';

export function renderPairing(root, state) {
  const wrap = document.createElement('section');
  wrap.className = 'phase phase-pairing fade-in';
  wrap.innerHTML = `
    <div class="pairing-card">
      <div class="pairing-brand">
        <div class="pairing-brand-mark">
          <img src="/mosaic-logo-mark.svg" alt="Mosaic" width="40" height="40" />
        </div>
        <div class="pairing-brand-text">
          <h2>Mosaic</h2>
          <p>Your life, pieced together.</p>
        </div>
      </div>

      <div class="pairing-status">
        <div class="pairing-status-dot" data-status-dot></div>
        <div class="pairing-status-text">
          <strong data-status-headline>Checking bridge…</strong>
          <span data-status-sub>Looking for a running wa-bridge process.</span>
        </div>
      </div>

      <div class="pairing-qr-wrap" data-qr-wrap style="display:none;">
        <p class="pairing-qr-hint">
          Scan from <em>WhatsApp → Settings → Linked Devices</em>
        </p>
        <div class="pairing-qr-canvas" data-qr-canvas></div>
      </div>

      <div class="pairing-qr-pending" data-qr-pending style="display:none;">
        <div class="pairing-spinner"></div>
        <p class="pairing-qr-hint">Waiting for QR code from WhatsApp servers…</p>
      </div>

      <div class="pairing-logout">
        <button class="btn-outline" data-logout-btn>Log out &amp; start over</button>
      </div>

      <div class="pairing-debug" data-debug-log></div>
    </div>
  `;
  root.appendChild(wrap);

  const dot = wrap.querySelector('[data-status-dot]');
  const headline = wrap.querySelector('[data-status-headline]');
  const sub = wrap.querySelector('[data-status-sub]');
  const qrWrap = wrap.querySelector('[data-qr-wrap]');
  const qrCanvas = wrap.querySelector('[data-qr-canvas]');
  const qrPending = wrap.querySelector('[data-qr-pending]');
  const logoutBtn = wrap.querySelector('[data-logout-btn]');
  const debugLog = wrap.querySelector('[data-debug-log]');

  function dbg(msg) {
    const ts = new Date().toLocaleTimeString();
    const line = document.createElement('div');
    line.className = 'pairing-debug-line';
    line.textContent = `[${ts}] ${msg}`;
    debugLog.appendChild(line);
    console.log(`[Pairing] ${msg}`);
    // Keep only last 15 lines
    while (debugLog.children.length > 15) {
      debugLog.removeChild(debugLog.firstChild);
    }
  }

  let lastQR = '';
  let bridgeStartAttempted = false;

  async function startBridge() {
    if (bridgeStartAttempted) return;
    bridgeStartAttempted = true;
    dbg('startBridge() called');
    try {
      const res = await api.bridgeStart();
      dbg(`bridgeStart response: ${JSON.stringify(res)}`);
      if (!res.ok && res.error) {
        headline.textContent = 'Cannot start bridge';
        sub.textContent = res.error;
        dot.classList.add('is-offline');
      }
    } catch (e) {
      dbg(`bridgeStart error: ${e}`);
    }
  }

  async function restartBridge() {
    dbg('restartBridge() called (bridge went offline, retrying)');
    try {
      const res = await api.bridgeStart();
      dbg(`restartBridge response: ${JSON.stringify(res)}`);
    } catch (e) {
      dbg(`restartBridge error: ${e}`);
    }
  }

  function paintStatus(status, qrReady) {
    dot.classList.remove('is-offline', 'is-pairing', 'is-connected');
    if (status === 'offline') {
      dot.classList.add('is-offline');
      headline.textContent = 'Bridge is offline';
      sub.textContent = 'Waiting for the WhatsApp bridge to start…';
      qrWrap.style.display = 'none';
      qrPending.style.display = 'none';
    } else if (status === 'pairing') {
      dot.classList.add('is-pairing');
      if (qrReady) {
        headline.textContent = 'Waiting for QR scan…';
        sub.textContent = 'Bridge is running. Scan the QR code below with your phone.';
        qrPending.style.display = 'none';
      } else {
        headline.textContent = 'Starting bridge…';
        sub.textContent = 'Waiting for QR code from WhatsApp servers…';
        qrWrap.style.display = 'none';
        qrPending.style.display = 'block';
      }
    } else if (status === 'connected') {
      dot.classList.add('is-connected');
      headline.textContent = 'Connected';
      sub.textContent = 'WhatsApp is ready. Continuing…';
      qrWrap.style.display = 'none';
      qrPending.style.display = 'none';
    }
  }

  async function renderQR(qrRaw) {
    if (!qrRaw || qrRaw === lastQR) return;
    lastQR = qrRaw;

    const size = 320;
    try {
      const svg = await QRCode.toString(qrRaw, {
        type: 'svg',
        width: size,
        margin: 4,
        color: { dark: '#000000', light: '#ffffff' },
      });
      qrCanvas.innerHTML = svg;
      const svgEl = qrCanvas.querySelector('svg');
      if (svgEl) {
        svgEl.setAttribute('width', String(size));
        svgEl.setAttribute('height', String(size));
        svgEl.style.display = 'block';
        svgEl.style.shapeRendering = 'crispEdges';
      }
    } catch {
      qrCanvas.innerHTML = '';
    }
  }

  let stopped = false;
  const pollDelay = 2000;

  let pollCount = 0;
  let offlineStreak = 0;

  async function poll() {
    // Trigger bridge start on first poll
    dbg('poll() started, calling startBridge()');
    startBridge();

    while (!stopped) {
      pollCount++;
      try {
        const [statusRes, qrRes] = await Promise.all([
          api.bridgeStatus(),
          api.bridgeQR().catch((e) => {
            dbg(`bridgeQR error: ${e}`);
            return { qr_raw: '', event: 'error' };
          }),
        ]);

        const status = statusRes.status || 'offline';
        const qrReady = !!(qrRes.qr_raw && qrRes.event === 'code');
        dbg(`poll #${pollCount} | status=${status} | qrEvent=${qrRes.event} | qrReady=${qrReady} | qrRawLen=${(qrRes.qr_raw||'').length}`);

        paintStatus(status, qrReady);

        if (status === 'connected') {
          await new Promise((r) => setTimeout(r, 900));
          setPhase(PHASE.WHITELIST);
          return;
        }

        if (status === 'offline') {
          offlineStreak++;
          // Bridge died (likely 3-min QR timeout). Re-start it.
          if (offlineStreak >= 2) {
            dbg(`offline for ${offlineStreak} polls, restarting bridge`);
            bridgeStartAttempted = false;  // allow restart
            startBridge();
            offlineStreak = 0;
          }
        } else {
          offlineStreak = 0;
        }

        if (qrReady) {
          qrWrap.style.display = 'block';
          await renderQR(qrRes.qr_raw);
        }
      } catch (err) {
        dbg(`poll #${pollCount} caught error: ${err}`);
        paintStatus('offline');
      }
      await new Promise((r) => setTimeout(r, pollDelay));
    }
    dbg('poll loop stopped');
  }

  logoutBtn.addEventListener('click', async () => {
    if (confirm(
      'This will erase all data and disconnect WhatsApp.\n\n' +
      'You will need to enter your Gemini key again and scan a new QR code.\n\n' +
      'Continue?',
    )) {
      try {
        await api.reset();
      } catch { /* reset may fail if bridge is down */ }
      window.location.reload();
    }
  });

  paintStatus('offline');
  poll();

  const observer = new MutationObserver(() => {
    if (!document.contains(wrap)) {
      stopped = true;
      observer.disconnect();
    }
  });
  observer.observe(document.getElementById('app'), { childList: true });
}
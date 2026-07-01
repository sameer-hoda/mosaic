/**
 * TaskDog Electron — Main process.
 *
 * On startup:
 *   1. Bootstrap Python venv + dependencies (first run only)
 *   2. Start the Go WhatsApp bridge subprocess
 *   3. Start the Flask backend subprocess
 *   4. Open a BrowserWindow loading the Flask-served frontend
 *
 * All persistent state (databases, WhatsApp session, config) lives in
 * app.getPath('userData'), never in the app bundle.
 */

// ── V8 memory tuning (fixes "Failed to reserve virtual memory for CodeRange"
//    on machines with limited RAM) ──────────────────────────────────────────
const { app, BrowserWindow, dialog } = require('electron');

app.commandLine.appendSwitch('js-flags', '--max-old-space-size=512,--max-semi-space-size=4');

const { spawn, execSync, exec } = require('child_process');
const path = require('path');
const fs = require('fs');
const net = require('net');

// -- Resolve paths -----------------------------------------------------------
const isDev = !app.isPackaged;
const userDataDir = app.getPath('userData');

// -- Logging to file ---------------------------------------------------------
const LOG_FILE = path.join(userDataDir, 'taskdog-electron.log');
if (!fs.existsSync(userDataDir)) fs.mkdirSync(userDataDir, { recursive: true });
const logStream = fs.createWriteStream(LOG_FILE, { flags: 'a' });
const origLog = console.log;
const origErr = console.error;
console.log = (...args) => { origLog(...args); logStream.write(args.map(String).join(' ') + '\n'); };
console.error = (...args) => { origErr(...args); logStream.write('[ERROR] ' + args.map(String).join(' ') + '\n'); };

// In packaged app, extraResources goes into Contents/Resources (NOT asar)
// Resolve paths — asar:false means everything is flat on disk under __dirname
const backendDir = path.join(__dirname, 'backend');
const bridgeDir = path.join(__dirname, 'bridge');
const requirementsFile = path.join(backendDir, 'requirements.txt');

// Architecture-aware Go binary
const isArm64 = process.arch === 'arm64';
const bridgeBinary = path.join(bridgeDir, isArm64 ? 'wa-bridge-arm64' : 'wa-bridge-x86_64');

// -- Config management -------------------------------------------------------
const CONFIG_FILE = path.join(userDataDir, 'config.json');

function getConfig() {
  try {
    if (fs.existsSync(CONFIG_FILE)) {
      return JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf-8'));
    }
  } catch (_) { /* corrupted config — start fresh */ }
  return {};
}

function saveConfig(updates) {
  const current = getConfig();
  const merged = { ...current, ...updates };
  if (!fs.existsSync(userDataDir)) fs.mkdirSync(userDataDir, { recursive: true });
  fs.writeFileSync(CONFIG_FILE, JSON.stringify(merged, null, 2));
}

// -- Subprocess management ---------------------------------------------------
let flaskProcess = null;
let bridgeProcess = null;

function waitForPort(port, timeoutMs = 30000) {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    const tryConnect = () => {
      const sock = new net.Socket();
      sock.once('connect', () => { sock.destroy(); resolve(); });
      sock.once('error', () => {
        sock.destroy();
        if (Date.now() - start > timeoutMs) return reject(new Error(`Port ${port} timeout`));
        setTimeout(tryConnect, 300);
      });
      sock.connect(port, '127.0.0.1');
    };
    tryConnect();
  });
}

function isPortInUse(port) {
  return new Promise((resolve) => {
    const sock = new net.Socket();
    sock.setTimeout(1000);
    sock.once('connect', () => { sock.destroy(); resolve(true); });
    sock.once('error', () => { sock.destroy(); resolve(false); });
    sock.once('timeout', () => { sock.destroy(); resolve(false); });
    sock.connect(port, '127.0.0.1');
  });
}

async function killProcessOnPort(port) {
  return new Promise((resolve) => {
    exec(`lsof -ti:${port}`, (err, stdout) => {
      if (err || !stdout.trim()) return resolve(false);
      const pids = stdout.trim().split('\n');
      console.log(`[Boot] Killing stale process(es) on port ${port}: ${pids.join(', ')}`);
      for (const pid of pids) {
        try { process.kill(parseInt(pid), 'SIGTERM'); } catch (_) {}
      }
      setTimeout(() => resolve(true), 1000);
    });
  });
}

// -- Bootstrap Python environment (first run) --------------------------------
async function bootstrapPython() {
  const venvDir = path.join(userDataDir, 'venv');
  const pipPath = path.join(venvDir, 'bin', 'pip');
  const pythonPath = path.join(venvDir, 'bin', 'python3');

  // Check if venv is already set up
  if (fs.existsSync(pythonPath) && fs.existsSync(pipPath)) {
    console.log('[Boot] Python venv already exists at', venvDir);
    return { python: pythonPath, pip: pipPath, venv: venvDir, fresh: false };
  }

  console.log('[Boot] Creating Python venv…');
  try {
    execSync(`python3 -m venv "${venvDir}"`, { stdio: 'pipe' });
  } catch (e) {
    throw new Error(
      'python3 not found on your system.\n\n' +
      'Please install Python 3 from https://www.python.org/downloads/\n' +
      'or run: xcode-select --install\n\n' +
      'After installing, restart TaskDog.'
    );
  }

  console.log('[Boot] Installing Python dependencies from', requirementsFile);
  try {
    execSync(`"${pipPath}" install -r "${requirementsFile}" --quiet`, {
      stdio: 'pipe',
      timeout: 120000, // 2 min for first pip install
    });
  } catch (e) {
    const stderr = e.stderr ? e.stderr.toString() : '';
    throw new Error(`Failed to install Python dependencies:\n${stderr}`);
  }

  console.log('[Boot] Python environment ready');
  return { python: pythonPath, pip: pipPath, venv: venvDir, fresh: true };
}

// -- Start backend services --------------------------------------------------
async function startFlask(pythonPath) {
  const config = getConfig();
  const env = {
    ...process.env,
    GEMINI_API_KEY: config.geminiApiKey || '',
    CONFIG_FILE: CONFIG_FILE,
    DATABASE_PATH: path.join(userDataDir, 'taskdog.db'),
    DATABASE_PATH_V2: path.join(userDataDir, 'taskdog_v2.db'),
    FLASK_PORT: '3001',
    PYTHONUNBUFFERED: '1',
  };

  // Kill any stale process on port 3001 (e.g. dev Flask left running)
  const portBusy = await isPortInUse(3001);
  if (portBusy) {
    console.log('[Flask] Port 3001 already in use — killing stale process…');
    await killProcessOnPort(3001);
  }

  console.log('[Flask] Starting on port 3001…');
  console.log('[Flask] backendDir:', backendDir);
  console.log('[Flask] pythonPath:', pythonPath);
  console.log('[Flask] static dir exists:', fs.existsSync(path.join(backendDir, 'static', 'index.html')));
  flaskProcess = spawn(pythonPath, ['app.py'], {
    cwd: backendDir,
    env,
    stdio: ['pipe', 'pipe', 'pipe'],
  });

  flaskProcess.stdout.on('data', (d) => {
    for (const line of d.toString().trim().split('\n')) {
      if (line) console.log('[Flask]', line);
    }
  });
  flaskProcess.stderr.on('data', (d) => {
    for (const line of d.toString().trim().split('\n')) {
      if (line) console.log('[Flask]', line);
    }
  });
  flaskProcess.on('error', (err) => console.error('[Flask] Process error:', err));
  flaskProcess.on('exit', (code) => console.log('[Flask] Exited with code', code));

  await waitForPort(3001);

  // Verify this is OUR Flask by checking the response
  const http = require('http');
  const verifyFlask = () => new Promise((resolve, reject) => {
    const req = http.get('http://localhost:3001/api/health', (res) => {
      let body = '';
      res.on('data', (c) => body += c);
      res.on('end', () => {
        console.log('[Flask] Health check response:', res.statusCode, body.substring(0, 200));
        resolve();
      });
    });
    req.on('error', reject);
    req.setTimeout(5000, () => { req.destroy(); reject(new Error('Health check timeout')); });
  });

  try {
    await verifyFlask();
    console.log('[Flask] Ready on http://localhost:3001');
  } catch (e) {
    console.error('[Flask] Health check failed:', e.message);
    console.error('[Flask] The port may be held by a stale process. Check log file:', LOG_FILE);
    throw new Error('Flask started but health check failed. Another process may be on port 3001.');
  }
}

async function startBridge() {
  // Kill stale bridge on port 8080
  const portBusy = await isPortInUse(8080);
  if (portBusy) {
    console.log('[Bridge] Port 8080 already in use — killing stale process…');
    await killProcessOnPort(8080);
  }

  console.log('[Bridge] Starting on port 8080…');
  console.log('[Bridge] bridgeBinary:', bridgeBinary);
  console.log('[Bridge] cwd:', userDataDir);

  bridgeProcess = spawn(bridgeBinary, [], {
    cwd: userDataDir,   // store/ dir and DBs created under userDataDir
    env: { ...process.env },
    stdio: ['pipe', 'pipe', 'pipe'],
  });

  bridgeProcess.stdout.on('data', (d) => {
    for (const line of d.toString().trim().split('\n')) {
      if (line) console.log('[Bridge]', line);
    }
  });
  bridgeProcess.stderr.on('data', (d) => {
    for (const line of d.toString().trim().split('\n')) {
      if (line) console.log('[Bridge]', line);
    }
  });
  bridgeProcess.on('error', (err) => console.error('[Bridge] Process error:', err));
  bridgeProcess.on('exit', (code) => console.log('[Bridge] Exited with code', code));

  // Bridge may take a while to connect to WhatsApp; don't block startup.
  // The frontend polls /api/bridge/status to detect when it's ready.
  console.log('[Bridge] Running — waiting for WhatsApp connection…');
}

// -- Electron app lifecycle --------------------------------------------------
let mainWindow = null;

async function createWindow() {
  console.log('\n=== TaskDog v2 Electron ===');
  console.log('User data:', userDataDir);
  console.log('Architecture:', process.arch, '→ bridge:', bridgeBinary);
  console.log('');

  try {
    // 1. Bootstrap Python
    const { python } = await bootstrapPython();

    // 2. Start Flask backend first (required for health checks)
    await startFlask(python);

    // 3. Start Go bridge (non-blocking — frontend polls for connection)
    await startBridge();

    // 4. Create the window
    mainWindow = new BrowserWindow({
      width: 1280,
      height: 860,
      minWidth: 900,
      minHeight: 600,
      title: 'TaskDog',
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, 'preload.js'),
      },
      show: false,
      titleBarStyle: 'hiddenInset',
      trafficLightPosition: { x: 16, y: 16 },
    });

    // Load the Flask-served frontend
    mainWindow.loadURL('http://localhost:3001');

    mainWindow.once('ready-to-show', () => {
      mainWindow.show();
    });

    mainWindow.on('closed', () => {
      mainWindow = null;
    });

    // Open DevTools in dev mode
    if (isDev) {
      mainWindow.webContents.openDevTools({ mode: 'detach' });
    }
  } catch (err) {
    console.error('[Boot] Fatal error:', err.message);
    dialog.showErrorBox(
      'TaskDog Failed to Start',
      err.message + '\n\nLog file: ' + LOG_FILE
    );
    app.quit();
  }
}

// -- Graceful shutdown -------------------------------------------------------
function shutdown() {
  console.log('[Shutdown] Stopping all services…');

  if (bridgeProcess) {
    bridgeProcess.kill('SIGTERM');
    bridgeProcess = null;
  }
  if (flaskProcess) {
    flaskProcess.kill('SIGTERM');
    flaskProcess = null;
  }
}

// -- App events --------------------------------------------------------------
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  shutdown();
  app.quit();
});

app.on('before-quit', shutdown);

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// -- IPC handlers ------------------------------------------------------------
const { ipcMain } = require('electron');

ipcMain.handle('get-config', () => getConfig());

ipcMain.handle('save-config', (_event, updates) => {
  saveConfig(updates);
  // If the API key changed, restart Flask to pick up the new key
  if (updates.geminiApiKey !== undefined && flaskProcess) {
    console.log('[Config] API key changed — restarting Flask…');
    flaskProcess.kill('SIGTERM');
    flaskProcess = null;
    // The frontend will detect the restart and reload
  }
  return { ok: true };
});

ipcMain.handle('get-user-data-path', () => userDataDir);

ipcMain.handle('restart-services', async () => {
  console.log('[IPC] Restarting services…');
  if (bridgeProcess) { bridgeProcess.kill('SIGTERM'); bridgeProcess = null; }
  if (flaskProcess) { flaskProcess.kill('SIGTERM'); flaskProcess = null; }

  const { python } = await bootstrapPython();
  await startFlask(python);
  await startBridge();
  return { ok: true };
});

ipcMain.handle('get-app-info', () => ({
  version: app.getVersion(),
  userDataDir,
  isArm64,
  isPackaged: app.isPackaged,
}));
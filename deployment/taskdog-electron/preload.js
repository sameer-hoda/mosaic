/**
 * TaskDog Electron — Preload script.
 * Exposes a minimal, secure API to the renderer process via contextBridge.
 */
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('taskdog', {
  getConfig: () => ipcRenderer.invoke('get-config'),
  saveConfig: (updates) => ipcRenderer.invoke('save-config', updates),
  getUserDataPath: () => ipcRenderer.invoke('get-user-data-path'),
  restartServices: () => ipcRenderer.invoke('restart-services'),
  getAppInfo: () => ipcRenderer.invoke('get-app-info'),
});
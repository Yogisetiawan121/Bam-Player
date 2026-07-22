const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // File dialogs
  openFileDialog: () => ipcRenderer.invoke('dialog:openFile'),
  openFolderDialog: () => ipcRenderer.invoke('dialog:openFolder'),

  // File operations
  readFile: (filePath) => ipcRenderer.invoke('file:read', filePath),
  scanFolder: (folderPath) => ipcRenderer.invoke('folder:scan', folderPath),

  // App paths
  getPath: (name) => ipcRenderer.invoke('app:getPath', name),

  // Window controls
  minimize: () => ipcRenderer.send('window:minimize'),
  maximize: () => ipcRenderer.send('window:maximize'),
  close: () => ipcRenderer.send('window:close'),
  fullscreen: () => ipcRenderer.send('window:fullscreen'),
  isMaximized: () => ipcRenderer.invoke('window:isMaximized'),

  // Window state listeners
  onMaximizeChange: (callback) => {
    ipcRenderer.on('window:maximize-change', (event, isMaximized) => callback(isMaximized));
  }
});

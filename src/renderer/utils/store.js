/* ============================================================
   NeonWave Player - Data Persistence Store
   ============================================================ */

// Global toast notification system (defined early so components can use it)
function showToast(message, duration = 2500) {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = message;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('out');
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

class Store {
  constructor() {
    this._cache = {};
    this._ready = false;
    this._initPromise = this._init();
  }

  async _init() {
    try {
      // Try to get user data path from Electron
      if (window.electronAPI) {
        this.userDataPath = await window.electronAPI.getPath('userData');
      } else {
        this.userDataPath = 'neonwave-data';
      }
    } catch (e) {
      this.userDataPath = 'neonwave-data';
    }

    // Load saved data
    this._cache = this._load();
    this._ready = true;
  }

  _getStorageKey() {
    return 'neonwave-player-data';
  }

  _load() {
    try {
      const raw = localStorage.getItem(this._getStorageKey());
      if (raw) {
        return JSON.parse(raw);
      }
    } catch (e) {
      console.warn('Store: Failed to load data', e);
    }
    return this._defaults();
  }

  _save() {
    try {
      localStorage.setItem(this._getStorageKey(), JSON.stringify(this._cache));
    } catch (e) {
      console.warn('Store: Failed to save data', e);
    }
  }

  _defaults() {
    return {
      settings: {
        volume: 0.8,
        muted: false,
        visualizer: 'spectrum',
        fullscreen: false,
        winampMode: false,
        shuffle: false,
        repeat: 'none' // 'none', 'all', 'one'
      },
      playlist: [],
      lastPlayed: null,
      lastPosition: 0
    };
  }

  async ready() {
    await this._initPromise;
    return this;
  }

  get(key) {
    const keys = key.split('.');
    let val = this._cache;
    for (const k of keys) {
      if (val && typeof val === 'object' && k in val) {
        val = val[k];
      } else {
        return undefined;
      }
    }
    return val;
  }

  set(key, value) {
    const keys = key.split('.');
    let obj = this._cache;
    for (let i = 0; i < keys.length - 1; i++) {
      if (!(keys[i] in obj)) {
        obj[keys[i]] = {};
      }
      obj = obj[keys[i]];
    }
    obj[keys[keys.length - 1]] = value;
    this._save();
  }

  getAll() {
    return JSON.parse(JSON.stringify(this._cache));
  }

  // Playlist-specific helpers
  savePlaylist(tracks) {
    // Only save file paths, not full data
    const paths = tracks.map(t => ({
      path: t.path,
      name: t.name,
      duration: t.duration || 0,
      artist: t.artist || ''
    }));
    this.set('playlist', paths);
  }

  loadPlaylist() {
    return this.get('playlist') || [];
  }

  saveLastPlayed(track, position) {
    this.set('lastPlayed', track ? { path: track.path, name: track.name } : null);
    this.set('lastPosition', position || 0);
  }

  clear() {
    this._cache = this._defaults();
    this._save();
  }
}

// Global instance
const store = new Store();

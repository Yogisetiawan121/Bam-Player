/* ============================================================
   NeonWave Player - Custom Title Bar
   ============================================================ */

class TitleBar {
  constructor() {
    this.elements = {
      titlebar: document.getElementById('titlebar'),
      text: document.getElementById('titlebar-text'),
      minimize: document.getElementById('btn-minimize'),
      maximize: document.getElementById('btn-maximize'),
      close: document.getElementById('btn-close'),
      classic: document.getElementById('btn-classic')
    };

    this._maximized = false;
    this._onMaximizeChange = null;

    this._init();
  }

  _init() {
    // Window controls
    this.elements.minimize.addEventListener('click', () => {
      if (window.electronAPI) {
        window.electronAPI.minimize();
      }
    });

    this.elements.maximize.addEventListener('click', () => {
      if (window.electronAPI) {
        window.electronAPI.maximize();
      }
    });

    this.elements.close.addEventListener('click', () => {
      if (window.electronAPI) {
        window.electronAPI.close();
      }
    });

    // Classic mode toggle
    this.elements.classic.addEventListener('click', () => {
      this.toggleClassicMode();
    });

    // Double-click titlebar to maximize
    this.elements.titlebar.addEventListener('dblclick', (e) => {
      if (!e.target.closest('.titlebar-controls') && !e.target.closest('.titlebar-btn')) {
        if (window.electronAPI) {
          window.electronAPI.maximize();
        }
      }
    });

    // Update maximize icon when state changes
    if (window.electronAPI) {
      window.electronAPI.onMaximizeChange((isMaximized) => {
        this._maximized = isMaximized;
        this._updateMaximizeIcon();
      });
    }

    // Check initial maximize state
    this._checkMaximized();
  }

  async _checkMaximized() {
    if (window.electronAPI) {
      try {
        this._maximized = await window.electronAPI.isMaximized();
        this._updateMaximizeIcon();
      } catch (e) {}
    }
  }

  _updateMaximizeIcon() {
    const btn = this.elements.maximize;
    if (this._maximized) {
      btn.innerHTML = `<svg viewBox="0 0 16 16" width="14" height="14">
        <rect x="5" y="2" width="9" height="9" rx="1" fill="none" stroke="currentColor" stroke-width="1.2"/>
        <path d="M2,5 L2,14 L11,14" fill="none" stroke="currentColor" stroke-width="1.2"/>
      </svg>`;
    } else {
      btn.innerHTML = `<svg viewBox="0 0 16 16" width="14" height="14">
        <rect x="3" y="3" width="10" height="10" rx="1" fill="none" stroke="currentColor" stroke-width="1.3"/>
      </svg>`;
    }
  }

  toggleClassicMode() {
    document.body.classList.toggle('winamp-mode');
    const isClassic = document.body.classList.contains('winamp-mode');
    store.set('settings.winampMode', isClassic);

    // Show toast
    showToast(isClassic ? 'Winamp Classic Mode' : 'NeonWave Modern Mode');

    // Dispatch event
    document.dispatchEvent(new CustomEvent('classic-mode-change', { detail: { enabled: isClassic } }));
  }

  setTitle(text) {
    this.elements.text.textContent = text || 'NeonWave Player';
  }
}

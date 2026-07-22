/* ============================================================
   NeonWave Player - Keyboard Shortcuts
   ============================================================ */

class Keybindings {
  constructor() {
    this.bindings = new Map();
    this._handler = this._handleKeyDown.bind(this);
    this._enabled = true;

    // Default shortcuts
    this._registerDefaults();
  }

  _registerDefaults() {
    // Playback
    this.register('space', 'play-pause');
    this.register('escape', 'stop');

    // Seek
    this.register('arrowleft', 'seek-backward');
    this.register('arrowright', 'seek-forward');
    this.register('ctrl+arrowleft', 'seek-backward-large');
    this.register('ctrl+arrowright', 'seek-forward-large');

    // Volume
    this.register('arrowup', 'volume-up');
    this.register('arrowdown', 'volume-down');
    this.register('m', 'toggle-mute');

    // Navigation
    this.register('n', 'next-track');
    this.register('p', 'previous-track');
    this.register('ctrl+o', 'open-file');
    this.register('ctrl+l', 'toggle-playlist');

    // Visualizers
    this.register('1', 'viz-spectrum');
    this.register('2', 'viz-waveform');
    this.register('3', 'viz-circular');
    this.register('4', 'viz-particles');

    // Fullscreen
    this.register('f11', 'toggle-fullscreen');
    this.register('escape', 'exit-fullscreen');

    // Misc
    this.register('delete', 'remove-selected');
    this.register('ctrl+a', 'select-all');
    this.register('f5', 'shuffle');
    this.register('r', 'toggle-repeat');
  }

  register(combo, action) {
    this.bindings.set(action, combo);
  }

  enable() {
    if (!this._enabled) {
      document.addEventListener('keydown', this._handler);
      this._enabled = true;
    }
  }

  disable() {
    if (this._enabled) {
      document.removeEventListener('keydown', this._handler);
      this._enabled = false;
    }
  }

  setCallback(action, callback) {
    this[`_cb_${action}`] = callback;
  }

  _handleKeyDown(e) {
    // Don't handle if in input field
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
      // Still allow Ctrl+O and Ctrl+L in inputs
      if (!e.ctrlKey) return;
    }

    const key = e.key.toLowerCase();
    let combo = '';

    if (e.ctrlKey) combo += 'ctrl+';
    if (e.shiftKey) combo += 'shift+';
    if (e.altKey) combo += 'alt+';

    combo += key;

    // Map special keys
    const keyMap = {
      ' ': 'space',
      'arrowleft': 'arrowleft',
      'arrowright': 'arrowright',
      'arrowup': 'arrowup',
      'arrowdown': 'arrowdown',
      'escape': 'escape',
      'delete': 'delete',
      'f11': 'f11',
      'f5': 'f5'
    };

    const normalizedKey = keyMap[key] || key;

    // Check all registered actions
    for (const [action, binding] of this.bindings) {
      const normalizedCombo = (e.ctrlKey ? 'ctrl+' : '') +
                              (e.shiftKey ? 'shift+' : '') +
                              (e.altKey ? 'alt+' : '') +
                              normalizedKey;

      if (normalizedCombo === binding) {
        e.preventDefault();
        e.stopPropagation();

        const callback = this[`_cb_${action}`];
        if (callback) {
          callback(e);
        }
        return;
      }
    }
  }

  start() {
    this.enable();
  }

  destroy() {
    this.disable();
    this.bindings.clear();
  }
}

// Keyboard action constants
const KB_ACTIONS = {
  PLAY_PAUSE: 'play-pause',
  STOP: 'stop',
  NEXT_TRACK: 'next-track',
  PREVIOUS_TRACK: 'previous-track',
  SEEK_FORWARD: 'seek-forward',
  SEEK_BACKWARD: 'seek-backward',
  SEEK_FORWARD_LARGE: 'seek-forward-large',
  SEEK_BACKWARD_LARGE: 'seek-backward-large',
  VOLUME_UP: 'volume-up',
  VOLUME_DOWN: 'volume-down',
  TOGGLE_MUTE: 'toggle-mute',
  OPEN_FILE: 'open-file',
  TOGGLE_PLAYLIST: 'toggle-playlist',
  VIZ_SPECTRUM: 'viz-spectrum',
  VIZ_WAVEFORM: 'viz-waveform',
  VIZ_CIRCULAR: 'viz-circular',
  VIZ_PARTICLES: 'viz-particles',
  TOGGLE_FULLSCREEN: 'toggle-fullscreen',
  EXIT_FULLSCREEN: 'exit-fullscreen',
  TOGGLE_SHUFFLE: 'shuffle',
  TOGGLE_REPEAT: 'toggle-repeat',
  REMOVE_SELECTED: 'remove-selected'
};

// Global instance
const keybindings = new Keybindings();

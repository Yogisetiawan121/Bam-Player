/* ============================================================
   NeonWave Player - Playback Controls
   ============================================================ */

class PlaybackControls {
  constructor() {
    this.elements = {
      play: document.getElementById('btn-play'),
      pause: document.getElementById('pause-icon'),
      playIcon: document.getElementById('play-icon'),
      prev: document.getElementById('btn-prev'),
      next: document.getElementById('btn-next'),
      stop: document.getElementById('btn-stop'),
      mute: document.getElementById('btn-mute'),
      shuffle: document.getElementById('btn-shuffle'),
      repeat: document.getElementById('btn-repeat'),
      seekTrack: document.getElementById('seek-bar-track'),
      seekProgress: document.getElementById('seek-bar-progress'),
      seekBuffer: document.getElementById('seek-bar-buffer'),
      seekThumb: document.getElementById('seek-bar-thumb'),
      seekHover: document.getElementById('seek-bar-hover'),
      seekHoverTime: document.getElementById('seek-hover-time'),
      seekContainer: document.getElementById('seek-bar-container'),
      timeCurrent: document.getElementById('time-current'),
      timeTotal: document.getElementById('time-total'),
      volumeSlider: document.getElementById('volume-slider'),
      volumeFill: document.getElementById('volume-fill'),
      volumeThumb: document.getElementById('volume-thumb'),
      volumePercent: document.getElementById('volume-percent'),
      volumeContainer: null,
      volumeIcon: document.getElementById('volume-icon'),
      fullscreen: document.getElementById('btn-fullscreen'),
      playlistToggle: document.getElementById('btn-playlist-toggle')
    };

    this._isSeeking = false;
    this._isDraggingVolume = false;
    this._volume = 0.8;
    this._muted = false;
    this._shuffle = false;
    this._repeat = 'none'; // 'none', 'all', 'one'
    this._fullscreenActive = false;

    // Resolve volume container safely after DOM is ready
    const volSlider = document.getElementById('volume-slider');
    this.elements.volumeContainer = volSlider ? volSlider.parentElement : null;

    this._init();
  }

  _init() {
    // Play/Pause
    this.elements.play.addEventListener('click', () => this._togglePlay());

    // Previous track
    this.elements.prev.addEventListener('click', () => {
      document.dispatchEvent(new CustomEvent('track:prev'));
    });

    // Next track
    this.elements.next.addEventListener('click', () => {
      document.dispatchEvent(new CustomEvent('track:next'));
    });

    // Stop
    this.elements.stop.addEventListener('click', () => {
      audioEngine.stop();
      this._updatePlayButton(false);
    });

    // Mute
    this.elements.mute.addEventListener('click', () => {
      this._muted = audioEngine.toggleMute();
      this._updateVolumeDisplay();
    });

    // Shuffle
    this.elements.shuffle.addEventListener('click', () => {
      this._shuffle = !this._shuffle;
      this.elements.shuffle.classList.toggle('active', this._shuffle);
      store.set('settings.shuffle', this._shuffle);
      document.dispatchEvent(new CustomEvent('shuffle-change', { detail: { enabled: this._shuffle } }));
    });

    // Repeat
    this.elements.repeat.addEventListener('click', () => {
      const modes = ['none', 'all', 'one'];
      const idx = modes.indexOf(this._repeat);
      this._repeat = modes[(idx + 1) % modes.length];
      this._updateRepeatDisplay();
      store.set('settings.repeat', this._repeat);
      document.dispatchEvent(new CustomEvent('repeat-change', { detail: { mode: this._repeat } }));
    });

    // Seek bar
    this.elements.seekContainer.addEventListener('mousedown', (e) => this._startSeek(e));
    this.elements.seekContainer.addEventListener('mousemove', (e) => this._updateSeekHover(e));
    this.elements.seekContainer.addEventListener('mouseleave', () => {
      this.elements.seekHover.style.opacity = '0';
    });

    // Global mouse events for seek drag
    document.addEventListener('mousemove', (e) => {
      if (this._isSeeking) this._doSeek(e);
    });
    document.addEventListener('mouseup', () => {
      if (this._isSeeking) {
        this._isSeeking = false;
      }
    });

    // Volume slider
    this.elements.volumeContainer.addEventListener('mousedown', (e) => {
      this._isDraggingVolume = true;
      this._setVolume(e);
    });

    document.addEventListener('mousemove', (e) => {
      if (this._isDraggingVolume) {
        this._setVolume(e);
      }
    });

    document.addEventListener('mouseup', () => {
      this._isDraggingVolume = false;
    });

    // Fullscreen
    this.elements.fullscreen.addEventListener('click', () => {
      this._toggleFullscreen();
    });

    // Playlist toggle
    this.elements.playlistToggle.addEventListener('click', () => {
      document.dispatchEvent(new CustomEvent('playlist:toggle'));
    });

    // Listen for audio engine events
    audioEngine.onPlayStateChange = (playing) => {
      this._updatePlayButton(playing);
    };

    audioEngine.onTimeUpdate = (currentTime, duration) => {
      this._updateTimeDisplay(currentTime, duration);
      this._updateSeekBar(currentTime, duration);
    };

    audioEngine.onTrackEnd = () => {
      this._updatePlayButton(false);
      document.dispatchEvent(new CustomEvent('track:ended'));
    };

    // Restore settings
    this._restoreSettings();
  }

  _restoreSettings() {
    const settings = store.getAll().settings;
    this._volume = settings.volume ?? 0.8;
    this._muted = settings.muted ?? false;
    this._shuffle = settings.shuffle ?? false;
    this._repeat = settings.repeat || 'none';

    audioEngine.setVolume(this._volume);
    if (this._muted) {
      audioEngine.toggleMute();
    }

    this.elements.shuffle.classList.toggle('active', this._shuffle);
    this._updateRepeatDisplay();
    this._updateVolumeDisplay();
  }

  _togglePlay() {
    if (audioEngine.isPlaying) {
      audioEngine.pause();
    } else if (audioEngine.isPaused) {
      audioEngine.play();
    } else if (audioEngine.audioElement && audioEngine.audioElement.src) {
      audioEngine.play();
    } else {
      // No track loaded, try to play first in playlist
      document.dispatchEvent(new CustomEvent('playlist:play-first'));
    }
  }

  _updatePlayButton(playing) {
    if (playing) {
      this.elements.playIcon.classList.add('hidden');
      this.elements.pause.classList.remove('hidden');
    } else {
      this.elements.playIcon.classList.remove('hidden');
      this.elements.pause.classList.add('hidden');
    }
  }

  _startSeek(e) {
    this._isSeeking = true;
    this._doSeek(e);
  }

  _doSeek(e) {
    const rect = this.elements.seekTrack.getBoundingClientRect();
    const x = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const duration = audioEngine.duration || 0;
    const time = x * duration;
    audioEngine.seek(time);
  }

  _updateSeekHover(e) {
    const rect = this.elements.seekTrack.getBoundingClientRect();
    const x = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const duration = audioEngine.duration || 0;
    const time = x * duration;

    this.elements.seekHover.style.left = (x * 100) + '%';
    this.elements.seekHoverTime.textContent = this._formatTime(time);
    this.elements.seekHover.style.opacity = '1';
  }

  _updateSeekBar(currentTime, duration) {
    const progress = duration > 0 ? (currentTime / duration) * 100 : 0;
    this.elements.seekProgress.style.width = progress + '%';
    this.elements.seekThumb.style.left = progress + '%';

    // Buffer
    const buffer = audioEngine.bufferProgress || 0;
    this.elements.seekBuffer.style.width = (buffer * 100) + '%';
  }

  _updateTimeDisplay(currentTime, duration) {
    this.elements.timeCurrent.textContent = this._formatTime(currentTime);
    this.elements.timeTotal.textContent = this._formatTime(duration);
  }

  _formatTime(seconds) {
    if (!seconds || isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  _setVolume(e) {
    const rect = this.elements.volumeSlider.getBoundingClientRect();
    const x = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    this._volume = x;
    audioEngine.setVolume(x);
    this._updateVolumeDisplay();
    store.set('settings.volume', x);
  }

  _updateVolumeDisplay() {
    const displayVolume = this._muted ? 0 : this._volume;
    const percent = Math.round(displayVolume * 100);

    this.elements.volumeFill.style.width = (displayVolume * 100) + '%';
    this.elements.volumeThumb.style.left = (displayVolume * 100) + '%';
    this.elements.volumePercent.textContent = percent + '%';

    // Update volume icon
    const icon = this.elements.volumeIcon;
    if (this._muted || displayVolume === 0) {
      icon.innerHTML = `<svg viewBox="0 0 20 20" width="16" height="16">
        <polygon points="4,7 8,7 13,3 13,17 8,13 4,13" fill="currentColor"/>
        <line x1="15" y1="7" x2="18" y2="13" stroke="currentColor" stroke-width="1.2"/>
        <line x1="18" y1="7" x2="15" y2="13" stroke="currentColor" stroke-width="1.2"/>
      </svg>`;
    } else if (displayVolume < 0.3) {
      icon.innerHTML = `<svg viewBox="0 0 20 20" width="16" height="16">
        <polygon points="4,7 8,7 13,3 13,17 8,13 4,13" fill="currentColor"/>
        <path d="M15,9 Q17,10 15,11" fill="none" stroke="currentColor" stroke-width="1.2"/>
      </svg>`;
    } else {
      icon.innerHTML = `<svg viewBox="0 0 20 20" width="16" height="16">
        <polygon points="4,7 8,7 13,3 13,17 8,13 4,13" fill="currentColor"/>
        <path d="M15,7 Q18,10 15,13" fill="none" stroke="currentColor" stroke-width="1.2"/>
        <path d="M16,5 Q20,10 16,15" fill="none" stroke="currentColor" stroke-width="1"/>
      </svg>`;
    }
  }

  _updateRepeatDisplay() {
    const btn = this.elements.repeat;
    btn.classList.remove('repeat-one');
    btn.classList.remove('active');

    if (this._repeat === 'one') {
      btn.classList.add('repeat-one');
      btn.title = 'Repeat One';
    } else if (this._repeat === 'all') {
      btn.classList.add('active');
      btn.title = 'Repeat All';
    } else {
      btn.title = 'Repeat';
    }
  }

  _toggleFullscreen() {
    const isFull = document.body.classList.contains('fullscreen-mode');
    if (isFull) {
      this._exitFullscreen();
    } else {
      this._enterFullscreen();
    }
  }

  _enterFullscreen() {
    if (this._fullscreenActive) return;
    this._fullscreenActive = true;

    document.body.classList.add('fullscreen-mode');
    store.set('settings.fullscreen', true);

    // Show cursor on mouse move
    const showCursor = () => {
      document.body.classList.add('mouse-moved');
      clearTimeout(this._cursorTimeout);
      this._cursorTimeout = setTimeout(() => {
        document.body.classList.remove('mouse-moved');
      }, 2000);
    };

    // Remove old listener before adding new one to prevent leaks
    if (this._fullscreenCursorHandler) {
      document.removeEventListener('mousemove', this._fullscreenCursorHandler);
      document.removeEventListener('mousedown', this._fullscreenCursorHandler);
    }

    document.addEventListener('mousemove', showCursor);
    document.addEventListener('mousedown', showCursor);
    this._fullscreenCursorHandler = showCursor;
  }

  _exitFullscreen() {
    if (!this._fullscreenActive) return;
    this._fullscreenActive = false;

    document.body.classList.remove('fullscreen-mode');
    document.body.classList.remove('mouse-moved');
    store.set('settings.fullscreen', false);

    if (this._fullscreenCursorHandler) {
      document.removeEventListener('mousemove', this._fullscreenCursorHandler);
      document.removeEventListener('mousedown', this._fullscreenCursorHandler);
      this._fullscreenCursorHandler = null;
    }
  }

  // Keyboard shortcuts integration
  seekForward(seconds = 5) {
    const newTime = (audioEngine.currentTime || 0) + seconds;
    audioEngine.seek(newTime);
  }

  seekBackward(seconds = 5) {
    const newTime = (audioEngine.currentTime || 0) - seconds;
    audioEngine.seek(newTime);
  }

  volumeUp(amount = 0.05) {
    this._volume = Math.min(1, this._volume + amount);
    audioEngine.setVolume(this._volume);
    if (this._muted) {
      this._muted = false;
      audioEngine.toggleMute();
    }
    this._updateVolumeDisplay();
    store.set('settings.volume', this._volume);
  }

  volumeDown(amount = 0.05) {
    this._volume = Math.max(0, this._volume - amount);
    audioEngine.setVolume(this._volume);
    this._updateVolumeDisplay();
    store.set('settings.volume', this._volume);
  }
}

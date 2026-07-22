/* ============================================================
   NeonWave Player - Playlist Panel
   ============================================================ */

class Playlist {
  constructor() {
    this.elements = {
      panel: document.getElementById('playlist-panel'),
      items: document.getElementById('playlist-items'),
      count: document.getElementById('playlist-count'),
      searchInput: document.getElementById('playlist-search-input'),
      addFiles: document.getElementById('btn-add-files'),
      addFolder: document.getElementById('btn-add-folder'),
      clearPlaylist: document.getElementById('btn-clear-playlist'),
      toggleBtn: document.getElementById('btn-playlist-toggle')
    };

    this.tracks = [];
    this.currentIndex = -1;
    this._isVisible = false;
    this._filterText = '';
    this._dragIndex = -1;
    this._shuffleEnabled = false;
    this._repeatMode = 'none';
    this._shuffleOrder = [];
    this._shuffleIndex = 0;

    // Load persisted tracks
    this._init();
  }

  async _init() {
    await store.ready();

    // Load saved playlist
    const saved = store.loadPlaylist();
    if (saved.length > 0) {
      this.tracks = saved;
    }

    // Event listeners
    this.elements.addFiles.addEventListener('click', () => this._addFiles());
    this.elements.addFolder.addEventListener('click', () => this._addFolder());
    this.elements.clearPlaylist.addEventListener('click', () => this._clearPlaylist());
    this.elements.searchInput.addEventListener('input', () => {
      this._filterText = this.elements.searchInput.value.toLowerCase();
      this._render();
    });

    // Listen for playlist toggle
    document.addEventListener('playlist:toggle', () => this.toggle());

    // Listen for track navigation
    document.addEventListener('track:next', () => this.next());
    document.addEventListener('track:prev', () => this.previous());
    document.addEventListener('track:ended', () => this._onTrackEnded());
    document.addEventListener('playlist:play-first', () => this._playFirst());

    // Listen for shuffle/repeat changes
    document.addEventListener('shuffle-change', (e) => {
      this._shuffleEnabled = e.detail.enabled;
      if (this._shuffleEnabled) this._generateShuffleOrder();
    });
    document.addEventListener('repeat-change', (e) => {
      this._repeatMode = e.detail.mode;
    });

    // Drag and drop directly on playlist (visualizer area drops handled by app.js drag counter)
    this.elements.items.addEventListener('dragover', (e) => {
      e.preventDefault();
      if (this._dragIndex >= 0) {
        const itemEl = e.target.closest('.playlist-item');
        if (itemEl) {
          const items = this.elements.items.querySelectorAll('.playlist-item');
          const dropIdx = Array.from(items).indexOf(itemEl);
          // Determine if drop is above or below
          const rect = itemEl.getBoundingClientRect();
          const midY = rect.top + rect.height / 2;
          items.forEach(el => {
            el.classList.remove('drag-over-top', 'drag-over-bottom');
          });
          if (e.clientY < midY) {
            itemEl.classList.add('drag-over-top');
          } else {
            itemEl.classList.add('drag-over-bottom');
          }
        }
      }
    });

    this.elements.items.addEventListener('dragleave', (e) => {
      const items = this.elements.items.querySelectorAll('.playlist-item');
      items.forEach(el => el.classList.remove('drag-over-top', 'drag-over-bottom'));
    });

    this.elements.items.addEventListener('drop', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const items = this.elements.items.querySelectorAll('.playlist-item');
      items.forEach(el => el.classList.remove('drag-over-top', 'drag-over-bottom'));

      if (this._dragIndex >= 0) {
        const targetEl = e.target.closest('.playlist-item');
        if (targetEl) {
          const dropIdx = Array.from(items).indexOf(targetEl);
          if (dropIdx >= 0 && dropIdx !== this._dragIndex) {
            this._moveTrack(this._dragIndex, dropIdx);
          }
        }
        this._dragIndex = -1;
      }

      // Also handle file drops (only if there are files — prevents duplicate calls)
      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        this._handleDrop(e);
      }
    });

    // Context menu
    this.elements.items.addEventListener('contextmenu', (e) => {
      const itemEl = e.target.closest('.playlist-item');
      if (itemEl) {
        const items = Array.from(this.elements.items.querySelectorAll('.playlist-item'));
        const idx = items.indexOf(itemEl);
        this._showContextMenu(e, idx);
      }
    });

    document.addEventListener('click', () => {
      document.getElementById('context-menu').classList.add('hidden');
    });

    // Initial render
    this._render();

    // Load last played if available
    const lastPlayed = store.get('lastPlayed');
    if (lastPlayed && lastPlayed.path) {
      const idx = this.tracks.findIndex(t => t.path === lastPlayed.path);
      if (idx >= 0) {
        this.currentIndex = idx;
      }
    }
  }

  async _addFiles() {
    if (!window.electronAPI) return;

    const filePaths = await window.electronAPI.openFileDialog();
    if (!filePaths) return;

    showToast(`Loading ${filePaths.length} file(s)...`);

    for (const filePath of filePaths) {
      const result = await window.electronAPI.readFile(filePath);
      if (result) {
        this.tracks.push({
          path: result.path,
          name: result.name,
          data: result.data,
          duration: 0,
          artist: ''
        });
      }
    }

    this._save();
    this._render();

    // If nothing is playing, start the first track
    if (this.currentIndex < 0 && this.tracks.length > 0) {
      this._playTrack(0);
    }

    showToast(`Added ${filePaths.length} track(s)`);
  }

  async _addFolder() {
    if (!window.electronAPI) return;

    const folderPath = await window.electronAPI.openFolderDialog();
    if (!folderPath) return;

    showToast('Scanning folder...');

    const files = await window.electronAPI.scanFolder(folderPath);
    if (files.length === 0) {
      showToast('No audio files found');
      return;
    }

    for (const filePath of files) {
      const result = await window.electronAPI.readFile(filePath);
      if (result) {
        this.tracks.push({
          path: result.path,
          name: result.name,
          data: result.data,
          duration: 0,
          artist: ''
        });
      }
    }

    this._save();
    this._render();

    if (this.currentIndex < 0 && this.tracks.length > 0) {
      this._playTrack(0);
    }

    showToast(`Added ${files.length} track(s) from folder`);
  }

  _handleDrop(e) {
    // Resume AudioContext synchronously during user gesture for reliable playback
    if (audioEngine.audioContext && audioEngine.audioContext.state === 'suspended') {
      audioEngine.audioContext.resume();
    }

    const files = Array.from(e.dataTransfer.files);
    const audioFiles = files.filter(f => {
      const ext = f.name.split('.').pop().toLowerCase();
      return ['mp3', 'wav', 'flac', 'ogg', 'm4a', 'aac', 'wma'].includes(ext);
    });

    if (audioFiles.length === 0) return;

    showToast(`Loading ${audioFiles.length} dropped file(s)...`);

    for (const file of audioFiles) {
      const reader = new FileReader();
      reader.onload = (event) => {
        this.tracks.push({
          path: file.path || file.name,
          name: file.name,
          data: event.target.result,
          duration: 0,
          artist: ''
        });

        if (this.currentIndex < 0 && this.tracks.length > 0) {
          this._playTrack(0);
        }

        this._save();
        this._render();
      };
      reader.readAsDataURL(file);
    }
  }

  _clearPlaylist() {
    if (this.tracks.length === 0) return;
    this.tracks = [];
    this.currentIndex = -1;
    audioEngine.stop();
    this._save();
    this._render();
    showToast('Playlist cleared');
  }

  _playTrack(index) {
    if (index < 0 || index >= this.tracks.length) return;

    const track = this.tracks[index];
    if (!track.data && track.path && window.electronAPI) {
      // Need to load the file
      window.electronAPI.readFile(track.path).then(result => {
        if (result) {
          track.data = result.data;
          this._doPlay(index);
        }
      });
    } else if (track.data) {
      this._doPlay(index);
    }
  }

  _doPlay(index) {
    const track = this.tracks[index];
    if (!track || !track.data) return;

    this.currentIndex = index;

    // Check if this is the last played track to restore position
    const lastPlayed = store.get('lastPlayed');
    const savedPosition = store.get('lastPosition') || 0;
    const shouldRestorePos = lastPlayed && lastPlayed.path === track.path && savedPosition > 3;

    audioEngine.load(track.data, true);

    // Restore last position after the track metadata loads
    if (shouldRestorePos) {
      const onLoaded = () => {
        audioEngine.seek(savedPosition);
        audioEngine.onLoad = null;
      };
      audioEngine.onLoad = onLoaded;
    }

    // Update UI
    this._render();
    document.getElementById('now-playing').classList.remove('hidden');
    document.getElementById('album-art-overlay').classList.add('hidden');
    document.getElementById('now-playing-title').textContent = this._getDisplayName(track.name);
    document.getElementById('now-playing-artist').textContent = track.artist || 'Unknown Artist';

    // Update title bar
    const titleBar = document.querySelector('.titlebar-text');
    if (titleBar) {
      titleBar.textContent = `♪ ${this._getDisplayName(track.name)}`;
    }

    // Save state
    store.saveLastPlayed(track, 0);
  }

  _getDisplayName(filename) {
    // Remove extension
    const name = filename.replace(/\.[^/.]+$/, '');
    // Try to clean up common patterns
    return name
      .replace(/_/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  _playFirst() {
    if (this.tracks.length > 0) {
      this._playTrack(0);
    }
  }

  next() {
    if (this.tracks.length === 0) return;

    if (this._shuffleEnabled) {
      this._shuffleIndex = (this._shuffleIndex + 1) % this._shuffleOrder.length;
      this._playTrack(this._shuffleOrder[this._shuffleIndex]);
    } else {
      const nextIdx = this.currentIndex + 1;
      if (nextIdx < this.tracks.length) {
        this._playTrack(nextIdx);
      } else if (this._repeatMode === 'all') {
        this._playTrack(0);
      } else {
        audioEngine.stop();
      }
    }
  }

  previous() {
    if (this.tracks.length === 0) return;

    // If more than 3 seconds in, restart current track
    if (audioEngine.currentTime > 3) {
      audioEngine.seek(0);
      return;
    }

    if (this._shuffleEnabled) {
      this._shuffleIndex = (this._shuffleIndex - 1 + this._shuffleOrder.length) % this._shuffleOrder.length;
      this._playTrack(this._shuffleOrder[this._shuffleIndex]);
    } else {
      const prevIdx = this.currentIndex - 1;
      if (prevIdx >= 0) {
        this._playTrack(prevIdx);
      } else {
        audioEngine.seek(0);
      }
    }
  }

  _onTrackEnded() {
    if (this._repeatMode === 'one') {
      this._playTrack(this.currentIndex);
    } else {
      this.next();
    }
  }

  _moveTrack(from, to) {
    const [track] = this.tracks.splice(from, 1);
    this.tracks.splice(to, 0, track);

    // Update current index
    if (this.currentIndex === from) {
      this.currentIndex = to;
    } else if (from < this.currentIndex && to >= this.currentIndex) {
      this.currentIndex--;
    } else if (from > this.currentIndex && to <= this.currentIndex) {
      this.currentIndex++;
    }

    this._save();
    this._render();
  }

  _generateShuffleOrder() {
    this._shuffleOrder = Array.from({ length: this.tracks.length }, (_, i) => i);
    // Fisher-Yates shuffle, but ensure current track is first
    const currentTrack = this.currentIndex >= 0 ? this.currentIndex : 0;
    for (let i = this._shuffleOrder.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [this._shuffleOrder[i], this._shuffleOrder[j]] = [this._shuffleOrder[j], this._shuffleOrder[i]];
    }
    // Move current track to front
    const idx = this._shuffleOrder.indexOf(currentTrack);
    if (idx >= 0) {
      this._shuffleOrder.splice(idx, 1);
      this._shuffleOrder.unshift(currentTrack);
    }
    this._shuffleIndex = 0;
  }

  _removeTrack(index) {
    if (index < 0 || index >= this.tracks.length) return;

    const wasPlaying = index === this.currentIndex;
    this.tracks.splice(index, 1);

    if (wasPlaying) {
      if (index < this.tracks.length) {
        this._playTrack(index);
      } else if (this.tracks.length > 0) {
        this._playTrack(this.tracks.length - 1);
      } else {
        audioEngine.stop();
        this.currentIndex = -1;
        document.getElementById('now-playing').classList.add('hidden');
        document.getElementById('album-art-overlay').classList.remove('hidden');
      }
    } else if (index < this.currentIndex) {
      this.currentIndex--;
    }

    this._save();
    this._render();
  }

  _showContextMenu(e, index) {
    const menu = document.getElementById('context-menu');
    const items = menu.querySelectorAll('.context-menu-item');

    items.forEach(item => {
      const action = item.dataset.action;
      item.onclick = () => {
        menu.classList.add('hidden');
        switch (action) {
          case 'play':
            this._playTrack(index);
            break;
          case 'remove':
            this._removeTrack(index);
            break;
          case 'reveal':
            // Would need shell.openPath in main process
            break;
          case 'properties':
            const track = this.tracks[index];
            showToast(`Track: ${track.name}`);
            break;
        }
      };
    });

    menu.style.left = e.clientX + 'px';
    menu.style.top = e.clientY + 'px';
    menu.classList.remove('hidden');
  }

  _save() {
    store.savePlaylist(this.tracks);
  }

  _render() {
    const container = this.elements.items;
    const filter = this._filterText;

    // Filter tracks if search is active
    const filteredTracks = filter
      ? this.tracks.filter(t => t.name.toLowerCase().includes(filter))
      : this.tracks;

    // Update count
    this.elements.count.textContent = `${this.tracks.length} track${this.tracks.length !== 1 ? 's' : ''}`;

    if (this.tracks.length === 0) {
      container.innerHTML = `
        <div class="playlist-empty">
          <svg viewBox="0 0 40 40" width="32" height="32">
            <circle cx="20" cy="20" r="16" fill="none" stroke="#ffffff15" stroke-width="1.5"/>
            <text x="20" y="25" text-anchor="middle" fill="#ffffff20" font-size="16">♪</text>
          </svg>
          <span>No tracks in playlist</span>
          <span class="playlist-empty-hint">Drop audio files or click + to add</span>
        </div>
      `;
      return;
    }

    let html = '';
    for (let i = 0; i < filteredTracks.length; i++) {
      const track = filteredTracks[i];
      // Find real index in the main array
      const realIndex = this.tracks.indexOf(track);
      const isActive = realIndex === this.currentIndex;
      const isPlaying = isActive && audioEngine.isPlaying;

      html += `
        <div class="playlist-item ${isActive ? 'active' : ''} ${isPlaying ? 'playing' : ''}"
             data-index="${realIndex}"
             draggable="true">
          <span class="playlist-item-indicator"></span>
          <span class="playlist-item-index">${realIndex + 1}</span>
          <div class="playlist-item-info">
            <span class="playlist-item-title">${this._escapeHtml(this._getDisplayName(track.name))}</span>
            <span class="playlist-item-artist">${track.artist || 'Unknown Artist'}</span>
          </div>
          <span class="playlist-item-duration">${this._formatDuration(track.duration)}</span>
          <button class="playlist-item-remove" data-remove="${realIndex}" title="Remove">
            <svg viewBox="0 0 12 12" width="10" height="10">
              <line x1="2" y1="2" x2="10" y2="10" stroke="currentColor" stroke-width="1.5"/>
              <line x1="10" y1="2" x2="2" y2="10" stroke="currentColor" stroke-width="1.5"/>
            </svg>
          </button>
        </div>
      `;
    }

    container.innerHTML = html;

    // Add event listeners to rendered items
    container.querySelectorAll('.playlist-item').forEach(el => {
      const idx = parseInt(el.dataset.index);

      // Click to play
      el.addEventListener('click', (e) => {
        if (!e.target.closest('.playlist-item-remove')) {
          this._playTrack(idx);
        }
      });

      // Double-click to play
      el.addEventListener('dblclick', (e) => {
        if (!e.target.closest('.playlist-item-remove')) {
          this._playTrack(idx);
        }
      });

      // Remove button
      const removeBtn = el.querySelector('.playlist-item-remove');
      if (removeBtn) {
        removeBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          this._removeTrack(idx);
        });
      }

      // Drag
      el.addEventListener('dragstart', (e) => {
        this._dragIndex = idx;
        el.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', idx.toString());
      });

      el.addEventListener('dragend', () => {
        el.classList.remove('dragging');
        container.querySelectorAll('.playlist-item').forEach(item => {
          item.classList.remove('drag-over-top', 'drag-over-bottom');
        });
      });
    });
  }

  toggle() {
    this._isVisible = !this._isVisible;
    this.elements.panel.classList.toggle('hidden', !this._isVisible);
  }

  show() {
    this._isVisible = true;
    this.elements.panel.classList.remove('hidden');
  }

  hide() {
    this._isVisible = false;
    this.elements.panel.classList.add('hidden');
  }

  _formatDuration(seconds) {
    if (!seconds || isNaN(seconds)) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  _escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
}

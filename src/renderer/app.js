/* ============================================================
   NeonWave Player - Main Application
   ============================================================ */

// Global splash screen / init
(async function init() {
  'use strict';

  // Wait for store to be ready
  await store.ready();

  // --- Init Components ---
  const titleBar = new TitleBar();
  const controls = new PlaybackControls();
  const playlist = new Playlist();

  // --- Init Visualizers ---
  const visualizers = {
    spectrum: new SpectrumVisualizer('visualizer-canvas'),
    waveform: new WaveformVisualizer('visualizer-canvas'),
    circular: new CircularVisualizer('visualizer-canvas'),
    particles: new ParticleVisualizer('visualizer-canvas')
  };

  // Active visualizer
  let activeViz = store.get('settings.visualizer') || 'spectrum';

  // Start default visualizer
  if (visualizers[activeViz]) {
    visualizers[activeViz].start();
  }

  // --- Visualizer Switcher ---
  const vizButtons = document.querySelectorAll('.viz-btn');

  function switchVisualizer(name) {
    if (!visualizers[name]) return;

    // Stop current
    Object.values(visualizers).forEach(v => v.stop());

    // Update active
    activeViz = name;
    visualizers[name].start();

    // Update buttons
    vizButtons.forEach(btn => {
      btn.classList.toggle('active', btn.dataset.viz === name);
    });

    // Save preference
    store.set('settings.visualizer', name);
  }

  vizButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      switchVisualizer(btn.dataset.viz);
    });
  });

  // --- Keyboard Shortcuts ---
  keybindings.setCallback('play-pause', () => controls._togglePlay());
  keybindings.setCallback('stop', () => {
    if (document.body.classList.contains('fullscreen-mode')) {
      controls._exitFullscreen();
      return;
    }
    audioEngine.stop();
    controls._updatePlayButton(false);
  });
  keybindings.setCallback('next-track', () => playlist.next());
  keybindings.setCallback('previous-track', () => playlist.previous());
  keybindings.setCallback('seek-forward', () => controls.seekForward(5));
  keybindings.setCallback('seek-backward', () => controls.seekBackward(5));
  keybindings.setCallback('seek-forward-large', () => controls.seekForward(30));
  keybindings.setCallback('seek-backward-large', () => controls.seekBackward(30));
  keybindings.setCallback('volume-up', () => controls.volumeUp());
  keybindings.setCallback('volume-down', () => controls.volumeDown());
  keybindings.setCallback('toggle-mute', () => {
    controls._muted = audioEngine.toggleMute();
    controls._updateVolumeDisplay();
  });
  keybindings.setCallback('open-file', () => {
    const addBtn = document.getElementById('btn-add-files');
    if (addBtn) addBtn.click();
  });
  keybindings.setCallback('toggle-playlist', () => playlist.toggle());
  keybindings.setCallback('viz-spectrum', () => switchVisualizer('spectrum'));
  keybindings.setCallback('viz-waveform', () => switchVisualizer('waveform'));
  keybindings.setCallback('viz-circular', () => switchVisualizer('circular'));
  keybindings.setCallback('viz-particles', () => switchVisualizer('particles'));
  keybindings.setCallback('toggle-fullscreen', () => controls._toggleFullscreen());
  keybindings.setCallback('shuffle', () => {
    controls.elements.shuffle.click();
  });
  keybindings.setCallback('toggle-repeat', () => {
    controls.elements.repeat.click();
  });

  // Start keyboard handling
  keybindings.start();

  // --- Restore Settings ---
  // Winamp mode
  if (store.get('settings.winampMode')) {
    document.body.classList.add('winamp-mode');
  }

  // Fullscreen
  if (store.get('settings.fullscreen')) {
    controls._enterFullscreen();
  }

  // Visualizer buttons
  vizButtons.forEach(btn => {
    btn.classList.toggle('active', btn.dataset.viz === activeViz);
  });

  // --- Drag & Drop on body (drag counter to prevent flicker) ---
  let dragCounter = 0;

  document.addEventListener('dragenter', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter++;
    if (dragCounter === 1) {
      const overlay = document.getElementById('drop-overlay');
      if (overlay) overlay.classList.remove('hidden');
    }
  });

  document.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.stopPropagation();
  });

  document.addEventListener('dragleave', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter--;
    if (dragCounter <= 0) {
      dragCounter = 0;
      const overlay = document.getElementById('drop-overlay');
      if (overlay) overlay.classList.add('hidden');
    }
  });

  document.addEventListener('drop', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter = 0;
    const overlay = document.getElementById('drop-overlay');
    if (overlay) overlay.classList.add('hidden');

    // Resume AudioContext synchronously during user gesture
    if (audioEngine.audioContext && audioEngine.audioContext.state === 'suspended') {
      audioEngine.audioContext.resume();
    }

    // Let the playlist handle the drop
    const dt = e.dataTransfer;
    if (dt.files && dt.files.length > 0) {
      playlist._handleDrop(e);
    }
  });

  // --- Double-click visualization for fullscreen toggle ---
  const vizCanvas = document.getElementById('visualizer-canvas');
  vizCanvas.addEventListener('dblclick', () => {
    controls._toggleFullscreen();
  });

  // --- Window resize handler (re-centers things) ---
  window.addEventListener('resize', () => {
    // Visualizers handle their own resize in BaseVisualizer
  });

  // --- Show initial state ---
  if (audioEngine.audioElement && audioEngine.audioElement.src) {
    document.getElementById('now-playing').classList.remove('hidden');
    document.getElementById('album-art-overlay').classList.add('hidden');
  }

  console.log('NeonWave Player initialized');
  console.log(`Active visualizer: ${activeViz}`);
  console.log(`Tracks in playlist: ${playlist.tracks.length}`);

  // --- Show welcome toast after a moment ---
  setTimeout(() => {
    showToast('♪ Welcome to NeonWave Player — drop your music!', 3000);
  }, 500);

})();

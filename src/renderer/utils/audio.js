/* ============================================================
   NeonWave Player - Audio Engine
   ============================================================ */

class AudioEngine {
  constructor() {
    this.audioContext = null;
    this.audioElement = null;
    this.source = null;
    this.analyser = null;
    this.gainNode = null;

    this.isPlaying = false;
    this.isPaused = false;
    this.volume = 0.8;
    this.muted = false;
    this.duration = 0;
    this.currentTime = 0;
    this.bufferProgress = 0;

    // Callbacks
    this.onTimeUpdate = null;
    this.onPlayStateChange = null;
    this.onTrackEnd = null;
    this.onLoad = null;
    this.onError = null;

    // FFT data
    this.fftSize = 256;
    this.frequencyData = new Uint8Array(this.fftSize / 2);
    this.timeDomainData = new Uint8Array(this.fftSize);

    // Animation frame handling
    this._animationId = null;
    this._boundUpdate = this._update.bind(this);

    // Bass/Mid/Treble averaged values
    this.bass = 0;
    this.mid = 0;
    this.treble = 0;

    // Smooth values for animation
    this.smoothBass = 0;
    this.smoothMid = 0;
    this.smoothTreble = 0;

    // Audio element event handlers
    this._boundTimeUpdate = this._onTimeUpdate.bind(this);
    this._boundLoaded = this._onLoaded.bind(this);
    this._boundEnded = this._onEnded.bind(this);
    this._boundError = this._onError.bind(this);
    this._boundProgress = this._onProgress.bind(this);

    this._init();
  }

  _init() {
    // Create audio element
    this.audioElement = new Audio();
    this.audioElement.crossOrigin = 'anonymous';
    this.audioElement.preload = 'auto';

    this.audioElement.addEventListener('timeupdate', this._boundTimeUpdate);
    this.audioElement.addEventListener('loadedmetadata', this._boundLoaded);
    this.audioElement.addEventListener('ended', this._boundEnded);
    this.audioElement.addEventListener('error', this._boundError);
    this.audioElement.addEventListener('progress', this._boundProgress);
    // Create AudioContext
    this._createContext();
  }

  _createContext() {
    try {
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    } catch (e) {
      console.error('AudioEngine: Failed to create AudioContext', e);
      return;
    }

    // Create analyser
    this.analyser = this.audioContext.createAnalyser();
    this.analyser.fftSize = this.fftSize;
    this.analyser.smoothingTimeConstant = 0.7;

    // Create gain node
    this.gainNode = this.audioContext.createGain();
    this.gainNode.gain.value = this.volume;

    // Connect: audio element -> source -> analyser -> gain -> destination
    this.source = this.audioContext.createMediaElementSource(this.audioElement);
    this.source.connect(this.analyser);
    this.analyser.connect(this.gainNode);
    this.gainNode.connect(this.audioContext.destination);
  }

  _onTimeUpdate() {
    if (this.audioElement) {
      this.currentTime = this.audioElement.currentTime;
      if (this.onTimeUpdate) {
        this.onTimeUpdate(this.currentTime, this.duration);
      }
    }
  }

  _onLoaded() {
    if (this.audioElement) {
      this.duration = this.audioElement.duration || 0;
      if (this.onLoad) {
        this.onLoad(this.duration);
      }
    }
  }

  _onEnded() {
    this.isPlaying = false;
    this.isPaused = false;
    if (this.onPlayStateChange) {
      this.onPlayStateChange(false);
    }
    if (this.onTrackEnd) {
      this.onTrackEnd();
    }
    this._stopAnimation();
  }

  _onError(e) {
    console.error('AudioEngine: Playback error', e);
    if (this.onError) {
      this.onError('Playback error occurred');
    }
  }

  _onProgress() {
    if (this.audioElement && this.audioElement.buffered.length > 0) {
      const buffered = this.audioElement.buffered;
      const currentTime = this.audioElement.currentTime;
      for (let i = 0; i < buffered.length; i++) {
        if (buffered.start(i) <= currentTime && buffered.end(i) >= currentTime) {
          this.bufferProgress = buffered.end(i) / this.duration;
          break;
        }
      }
    }
  }

  // Load a track from a data URL or file path
  async load(url, autoplay = false) {
    try {
      // Resume AudioContext if suspended
      if (this.audioContext && this.audioContext.state === 'suspended') {
        await this.audioContext.resume();
      }

      this.audioElement.src = url;

      if (autoplay) {
        // Wait for the audio source to load before attempting playback
        const isAlreadyLoaded = this.audioElement.readyState >= 2; // HAVE_CURRENT_DATA
        if (!isAlreadyLoaded) {
          await new Promise((resolve) => {
            const onReady = () => {
              this.audioElement.removeEventListener('loadedmetadata', onReady);
              this.audioElement.removeEventListener('canplay', onReady);
              resolve();
            };
            this.audioElement.addEventListener('loadedmetadata', onReady);
            this.audioElement.addEventListener('canplay', onReady);
            // Safety timeout — resolve anyway after 5s so playback isn't stuck
            setTimeout(onReady, 5000);
          });
        }
        await this.play();
      }
    } catch (e) {
      console.error('AudioEngine: Load error', e);
      if (this.onError) {
        this.onError('Failed to load audio');
      }
    }
  }

  async play() {
    if (!this.audioElement || !this.audioElement.src) return;

    try {
      if (this.audioContext && this.audioContext.state === 'suspended') {
        await this.audioContext.resume();
      }

      await this.audioElement.play();
      this.isPlaying = true;
      this.isPaused = false;
      if (this.onPlayStateChange) {
        this.onPlayStateChange(true);
      }
      this._startAnimation();
    } catch (e) {
      console.error('AudioEngine: Play error', e);
    }
  }

  pause() {
    if (this.audioElement) {
      this.audioElement.pause();
      this.isPlaying = false;
      this.isPaused = true;
      if (this.onPlayStateChange) {
        this.onPlayStateChange(false);
      }
      this._stopAnimation();
    }
  }

  stop() {
    if (this.audioElement) {
      this.audioElement.pause();
      this.audioElement.currentTime = 0;
      this.isPlaying = false;
      this.isPaused = false;
      this.currentTime = 0;
      if (this.onPlayStateChange) {
        this.onPlayStateChange(false);
      }
      this._stopAnimation();
    }
  }

  seek(time) {
    if (this.audioElement) {
      this.audioElement.currentTime = Math.max(0, Math.min(time, this.duration));
    }
  }

  setVolume(value) {
    this.volume = Math.max(0, Math.min(1, value));
    if (this.gainNode) {
      this.gainNode.gain.value = this.muted ? 0 : this.volume;
    }
  }

  toggleMute() {
    this.muted = !this.muted;
    if (this.gainNode) {
      this.gainNode.gain.value = this.muted ? 0 : this.volume;
    }
    return this.muted;
  }

  // Get current FFT frequency data
  getFrequencyData() {
    if (this.analyser && this.isPlaying) {
      this.analyser.getByteFrequencyData(this.frequencyData);
    } else {
      this.frequencyData.fill(0);
    }
    return this.frequencyData;
  }

  // Get current time-domain waveform data
  getTimeDomainData() {
    if (this.analyser && this.isPlaying) {
      this.analyser.getByteTimeDomainData(this.timeDomainData);
    } else {
      // Generate a flat line at 128 (center) when not playing
      this.timeDomainData.fill(128);
    }
    return this.timeDomainData;
  }

  // Calculate bass/mid/treble averages
  getBands() {
    this.getFrequencyData();

    const data = this.frequencyData;
    const len = data.length;

    // Bass: 0-20% of frequency range
    let bassSum = 0, bassCount = Math.floor(len * 0.2);
    for (let i = 0; i < bassCount; i++) bassSum += data[i];

    // Mid: 20-60%
    let midSum = 0, midCount = Math.floor(len * 0.4);
    for (let i = bassCount; i < bassCount + midCount; i++) midSum += data[i];

    // Treble: 60-100%
    let trebSum = 0, trebCount = len - bassCount - midCount;
    for (let i = bassCount + midCount; i < len; i++) trebSum += data[i];

    this.bass = bassSum / (bassCount || 1) / 255;
    this.mid = midSum / (midCount || 1) / 255;
    this.treble = trebSum / (trebCount || 1) / 255;

    // Smooth values (faster response for beat sync)
    this.smoothBass += (this.bass - this.smoothBass) * 0.25;
    this.smoothMid += (this.mid - this.smoothMid) * 0.25;
    this.smoothTreble += (this.treble - this.smoothTreble) * 0.25;

    return {
      bass: this.smoothBass,
      mid: this.smoothMid,
      treble: this.smoothTreble,
      rawBass: this.bass,
      rawMid: this.mid,
      rawTreble: this.treble
    };
  }

  // Animation loop for visualizers
  _startAnimation() {
    if (!this._animationId) {
      this._animationId = requestAnimationFrame(this._boundUpdate);
    }
  }

  _stopAnimation() {
    if (this._animationId) {
      cancelAnimationFrame(this._animationId);
      this._animationId = null;
    }
  }

  _update() {
    if (this.isPlaying) {
      // Get audio data - visualizers will read from here
      this.getFrequencyData();
      this.getTimeDomainData();
      this.getBands();
    }
    this._animationId = requestAnimationFrame(this._boundUpdate);
  }

  // Clean up
  destroy() {
    this._stopAnimation();
    if (this.audioElement) {
      this.audioElement.pause();
      this.audioElement.removeEventListener('timeupdate', this._boundTimeUpdate);
      this.audioElement.removeEventListener('loadedmetadata', this._boundLoaded);
      this.audioElement.removeEventListener('ended', this._boundEnded);
      this.audioElement.removeEventListener('error', this._boundError);
      this.audioElement.removeEventListener('progress', this._boundProgress);
      this.audioElement.src = '';
    }
    if (this.audioContext) {
      this.audioContext.close();
    }
  }
}

// Global instance
const audioEngine = new AudioEngine();

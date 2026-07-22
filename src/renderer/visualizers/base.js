/* ============================================================
   NeonWave Player - Base Visualizer
   All visualizers extend this class.
   ============================================================ */

class BaseVisualizer {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.width = 0;
    this.height = 0;
    this.name = 'base';
    this._animationId = null;
    this._running = false;

    // Time tracking
    this._lastTime = 0;
    this._elapsed = 0;

    // Color scheme
    this.colors = {
      primary: '#00f0ff',
      secondary: '#ff00aa',
      tertiary: '#39ff14',
      accent: '#a855f7',
      background: 'rgba(10, 10, 15, 0)'
    };

    // Resize observer
    this._resizeHandler = this._onResize.bind(this);
    window.addEventListener('resize', this._resizeHandler);

    // Initial size
    this._updateSize();
  }

  _updateSize() {
    const rect = this.canvas.parentElement.getBoundingClientRect();
    this.width = rect.width;
    this.height = rect.height;

    // Use device pixel ratio for crisp rendering
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = this.width * dpr;
    this.canvas.height = this.height * dpr;
    this.ctx.scale(dpr, dpr);
  }

  _onResize() {
    this._updateSize();
    this.onResize(this.width, this.height);
  }

  // Override in subclasses
  onResize(w, h) {}

  // Main draw loop - override in subclasses
  draw(ctx, width, height, frequencyData, timeDomainData, audioEngine) {
    // Subclasses implement this
  }

  // Start the animation loop
  start() {
    if (this._running) return;
    this._running = true;
    this._lastTime = performance.now();
    this._loop(this._lastTime);
  }

  // Stop the animation loop
  stop() {
    this._running = false;
    if (this._animationId) {
      cancelAnimationFrame(this._animationId);
      this._animationId = null;
    }
  }

  _loop(timestamp) {
    if (!this._running) return;

    const dt = timestamp - this._lastTime;
    this._lastTime = timestamp;
    this._elapsed += dt;

    // Clear canvas
    this.ctx.clearRect(0, 0, this.width, this.height);

    // Get audio data from global audio engine
    const freqData = audioEngine.getFrequencyData();
    const timeData = audioEngine.getTimeDomainData();

    // Draw
    this.draw(this.ctx, this.width, this.height, freqData, timeData, audioEngine);

    this._animationId = requestAnimationFrame((t) => this._loop(t));
  }

  // Clean up
  destroy() {
    this.stop();
    window.removeEventListener('resize', this._resizeHandler);
  }
}

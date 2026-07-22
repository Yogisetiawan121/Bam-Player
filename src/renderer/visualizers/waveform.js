/* ============================================================
   NeonWave Player - Waveform/Oscilloscope Visualizer
   Classic oscilloscope style line waveform.
   ============================================================ */

class WaveformVisualizer extends BaseVisualizer {
  constructor(canvasId) {
    super(canvasId);
    this.name = 'waveform';

    // Line smoothing
    this.smoothFactor = 0.3;

    // Trail effect
    this.trailAlpha = 0.3;

    // Grid
    this.showGrid = true;

    // Color cycling
    this.hue = 180;

    // Second waveform (for stereo effect)
    this.showMirror = true;
  }

  onResize(w, h) {}

  draw(ctx, width, height, freqData, timeData, audioEngine) {
    const isPlaying = audioEngine.isPlaying;
    const bands = audioEngine.getBands();

    // Fade background for trail effect
    ctx.fillStyle = `rgba(10, 10, 15, ${this.trailAlpha})`;
    ctx.fillRect(0, 0, width, height);

    // Grid
    if (this.showGrid) {
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
      ctx.lineWidth = 1;

      // Horizontal grid lines
      for (let i = 0; i <= 8; i++) {
        const y = (height / 8) * i;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      // Vertical grid lines
      for (let i = 0; i <= 16; i++) {
        const x = (width / 16) * i;
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
    }

    // Draw center cross
    ctx.strokeStyle = `rgba(255, 255, 255, ${0.02 + bands.bass * 0.04})`;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, height / 2);
    ctx.lineTo(width, height / 2);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(width / 2, 0);
    ctx.lineTo(width / 2, height);
    ctx.stroke();

    // Color shifts with audio
    this.hue = (180 + bands.bass * 30 - bands.treble * 20) % 360;
    const primaryHue = this.hue;
    const secondaryHue = (primaryHue + 60) % 360;

    // Draw waveform
    const data = timeData;
    const dataLen = data.length;
    // Map data samples across full canvas width — step < 1 when width > dataLen
    const step = dataLen / width;
    const centerY = height / 2;
    const scale = height * 0.4;

    // Primary waveform (cyan-ish)
    ctx.strokeStyle = `hsla(${primaryHue}, 100%, 60%, ${0.6 + bands.bass * 0.3})`;
    ctx.lineWidth = 2.5;
    ctx.shadowColor = `hsla(${primaryHue}, 100%, 60%, 0.3)`;
    ctx.shadowBlur = 10;
    ctx.beginPath();

    let firstPoint = true;
    for (let x = 0; x < width; x += 1) {
      const idx = Math.min(Math.floor(x * step), dataLen - 1);
      const val = data[idx] || 128;
      const normalized = (val - 128) / 128; // -1 to 1

      if (!isPlaying) {
        // Draw a flat-ish line when not playing
        const t = x / width;
        const wave = Math.sin(t * Math.PI * 2 + this._elapsed * 0.002) * 0.1;
        const y = centerY + wave * scale;

        if (firstPoint) {
          ctx.moveTo(x, y);
          firstPoint = false;
        } else {
          ctx.lineTo(x, y);
        }
      } else {
        const y = centerY + normalized * scale;

        if (firstPoint) {
          ctx.moveTo(x, y);
          firstPoint = false;
        } else {
          ctx.lineTo(x, y);
        }
      }
    }
    ctx.stroke();
    ctx.shadowBlur = 0;

    // Secondary waveform (magenta, offset slightly)
    if (this.showMirror && isPlaying) {
      ctx.strokeStyle = `hsla(${secondaryHue}, 100%, 60%, ${0.2 + bands.mid * 0.2})`;
      ctx.lineWidth = 1.5;
      ctx.shadowColor = `hsla(${secondaryHue}, 100%, 60%, 0.2)`;
      ctx.shadowBlur = 6;
      ctx.beginPath();

      firstPoint = true;
      for (let x = 0; x < width; x += 1) {
        const idx = Math.min(Math.floor(x * step), dataLen - 1);
        const val = data[idx] || 128;
        const normalized = (val - 128) / 128;
        const phase = normalized * 0.5;

        const y = centerY + phase * scale;

        if (firstPoint) {
          ctx.moveTo(x, y);
          firstPoint = false;
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();
      ctx.shadowBlur = 0;
    }

    // Fill waveform (subtle gradient)
    if (isPlaying) {
      const gradient = ctx.createLinearGradient(0, centerY - scale, 0, centerY + scale);
      gradient.addColorStop(0, `hsla(${primaryHue}, 100%, 60%, 0)`);
      gradient.addColorStop(0.5, `hsla(${primaryHue}, 100%, 60%, ${0.02 + bands.bass * 0.04})`);
      gradient.addColorStop(1, `hsla(${primaryHue}, 100%, 60%, 0)`);

      ctx.fillStyle = gradient;
      ctx.beginPath();

      ctx.moveTo(0, centerY);
      for (let x = 0; x < width; x += 1) {
        const idx = Math.min(Math.floor(x * step), dataLen - 1);
        const val = data[idx] || 128;
        const normalized = (val - 128) / 128;
        const y = centerY + normalized * scale;
        ctx.lineTo(x, y);
      }
      ctx.lineTo(width, centerY);
      ctx.closePath();
      ctx.fill();
    }

    // VU Meter corners (bass/mid/treble indicators)
    const vuSize = 40;
    const vuY = height - 20;
    const vuSpacing = 50;

    // Bass VU (left)
    this._drawVUMeter(ctx, 20, vuY, vuSize, 6, bands.bass, '#00f0ff');
    // Mid VU (center)
    this._drawVUMeter(ctx, 20 + vuSpacing, vuY, vuSize, 6, bands.mid, '#a855f7');
    // Treble VU (right)
    this._drawVUMeter(ctx, 20 + vuSpacing * 2, vuY, vuSize, 6, bands.treble, '#39ff14');
  }

  _drawVUMeter(ctx, x, y, width, height, value, color) {
    const fillWidth = width * Math.min(1, value * 1.2);

    ctx.fillStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.fillRect(x, y, width, height);

    ctx.fillStyle = color;
    ctx.globalAlpha = 0.6;
    ctx.fillRect(x, y, fillWidth, height);
    ctx.globalAlpha = 1;

    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.lineWidth = 1;
    ctx.strokeRect(x, y, width, height);
  }
}

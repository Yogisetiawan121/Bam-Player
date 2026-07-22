/* ============================================================
   NeonWave Player - Spectrum Analyzer Visualizer
   Classic frequency bars with smooth falling peak effect.
   ============================================================ */

class SpectrumVisualizer extends BaseVisualizer {
  constructor(canvasId) {
    super(canvasId);
    this.name = 'spectrum';

    // Number of bars to display
    this.barCount = 64;

    // Smooth values for bar heights
    this.smoothBars = new Float32Array(this.barCount);

    // Peak values and their fall-off
    this.peakValues = new Float32Array(this.barCount);
    this.peakVelocities = new Float32Array(this.barCount);
    this.peakFallSpeed = 0.03;

    // Colors
    this.colorStops = [
      { pos: 0.0, color: { r: 0, g: 240, b: 255 } },   // Cyan
      { pos: 0.33, color: { r: 168, g: 85, b: 247 } },  // Purple
      { pos: 0.66, color: { r: 255, g: 0, b: 170 } },   // Magenta
      { pos: 1.0, color: { r: 57, g: 255, b: 20 } }     // Lime
    ];

    // Background particles
    this.particles = [];
    for (let i = 0; i < 30; i++) {
      this.particles.push({
        x: Math.random(),
        y: Math.random(),
        speed: 0.002 + Math.random() * 0.004,
        size: 1 + Math.random() * 2
      });
    }

    // Mirror mode
    this.mirrored = true;
  }

  lerpColor(c1, c2, t) {
    return {
      r: Math.round(c1.r + (c2.r - c1.r) * t),
      g: Math.round(c1.g + (c2.g - c1.g) * t),
      b: Math.round(c1.b + (c2.b - c1.b) * t)
    };
  }

  getColor(t) {
    t = Math.max(0, Math.min(1, t));
    for (let i = 0; i < this.colorStops.length - 1; i++) {
      if (t >= this.colorStops[i].pos && t <= this.colorStops[i + 1].pos) {
        const localT = (t - this.colorStops[i].pos) / (this.colorStops[i + 1].pos - this.colorStops[i].pos);
        return this.lerpColor(this.colorStops[i].color, this.colorStops[i + 1].color, localT);
      }
    }
    return this.colorStops[this.colorStops.length - 1].color;
  }

  onResize(w, h) {
    // No special handling needed
  }

  draw(ctx, width, height, freqData, timeData, audioEngine) {
    const isPlaying = audioEngine.isPlaying;
    const bands = audioEngine.getBands();

    // Background
    ctx.fillStyle = 'rgba(10, 10, 15, 0.15)';
    ctx.fillRect(0, 0, width, height);

    // Draw background particles (subtle floating dots)
    ctx.fillStyle = `rgba(0, 240, 255, ${0.08 + bands.bass * 0.08})`;
    for (const p of this.particles) {
      p.y -= p.speed * (1 + bands.bass * 2);
      if (p.y < -0.05) p.y = 1.05;
      p.x += Math.sin(this._elapsed * 0.001 + p.y * 10) * 0.003;
      ctx.beginPath();
      ctx.arc(p.x * width, p.y * height, p.size * (0.5 + bands.bass * 0.5), 0, Math.PI * 2);
      ctx.fill();
    }

    // Calculate bar dimensions
    const barSpacing = 2;
    const displayBars = this.mirrored ? Math.floor(this.barCount / 2) : this.barCount;
    const barWidth = (width - (displayBars + 1) * barSpacing) / displayBars;

    // Center Y
    const centerY = this.mirrored ? height / 2 : height;
    const maxHeight = this.mirrored ? height / 2 - 20 : height - 20;

    // Map frequency data to display bars
    const freqStep = freqData.length / displayBars;

    for (let i = 0; i < displayBars; i++) {
      // Average frequency values for this bar
      const startIdx = Math.floor(i * freqStep);
      const endIdx = Math.floor((i + 1) * freqStep);
      let sum = 0;
      for (let j = startIdx; j < endIdx; j++) {
        sum += freqData[j] || 0;
      }
      const avg = sum / (endIdx - startIdx || 1);

      // Normalize
      const rawValue = avg / 255;

      // Smooth
      const targetSmooth = isPlaying ? rawValue : 0;
      this.smoothBars[i] += (targetSmooth - this.smoothBars[i]) * 0.35;

      const barHeight = this.smoothBars[i] * maxHeight;
      const barValue = this.smoothBars[i];

      // Peak handling
      if (barValue > this.peakValues[i]) {
        this.peakValues[i] = barValue;
        this.peakVelocities[i] = 0;
      } else {
        // Fall off
        this.peakValues[i] -= this.peakFallSpeed * (0.5 + this.peakValues[i] * 0.5);
        if (this.peakValues[i] < 0) this.peakValues[i] = 0;
      }

      const peakHeight = this.peakValues[i] * maxHeight;

      if (this.mirrored) {
        // Top bar
        const x = i * (barWidth + barSpacing) + barSpacing;
        const barY = centerY - barHeight;
        const barH = barHeight;

        if (barH > 1) {
          // Gradient color based on height
          const c = this.getColor(barValue);
          ctx.fillStyle = `rgba(${c.r}, ${c.g}, ${c.b}, 0.9)`;
          ctx.fillRect(x, barY, barWidth, barH);

          // Glow
          ctx.shadowColor = `rgba(${c.r}, ${c.g}, ${c.b}, 0.4)`;
          ctx.shadowBlur = 8;
          ctx.fillRect(x, barY, barWidth, barH);
          ctx.shadowBlur = 0;

          // Peak dot
          if (this.peakValues[i] > 0.02) {
            ctx.fillStyle = `rgba(${c.r}, ${c.g}, ${c.b}, 0.8)`;
            ctx.shadowColor = `rgba(${c.r}, ${c.g}, ${c.b}, 0.6)`;
            ctx.shadowBlur = 6;
            ctx.fillRect(x, centerY - peakHeight, barWidth, 2);
            ctx.shadowBlur = 0;
          }
        }

        // Bottom bar (mirrored)
        const bottomBarY = centerY;
        const bottomBarH = barHeight;

        if (bottomBarH > 1) {
          const c = this.getColor(barValue);
          ctx.fillStyle = `rgba(${c.r}, ${c.g}, ${c.b}, 0.4)`;
          ctx.fillRect(x, bottomBarY, barWidth, bottomBarH);

          // Bottom peak (mirrored from top)
          if (this.peakValues[i] > 0.02) {
            ctx.fillStyle = `rgba(${c.r}, ${c.g}, ${c.b}, 0.5)`;
            ctx.fillRect(x, centerY + peakHeight, barWidth, 2);
          }
        }
      } else {
        // Single direction (upward)
        const x = i * (barWidth + barSpacing) + barSpacing;
        const barY = height - barHeight;
        const barH = barHeight;

        if (barH > 1) {
          const c = this.getColor(barValue);
          ctx.fillStyle = `rgba(${c.r}, ${c.g}, ${c.b}, 0.9)`;
          ctx.fillRect(x, barY, barWidth, barH);

          // Glow
          ctx.shadowColor = `rgba(${c.r}, ${c.g}, ${c.b}, 0.3)`;
          ctx.shadowBlur = 6;
          ctx.fillRect(x, barY, barWidth, barH);
          ctx.shadowBlur = 0;

          // Peak
          if (this.peakValues[i] > 0.02) {
            ctx.fillStyle = `rgba(${c.r}, ${c.g}, ${c.b}, 0.9)`;
            ctx.shadowColor = `rgba(${c.r}, ${c.g}, ${c.b}, 0.7)`;
            ctx.shadowBlur = 8;
            ctx.fillRect(x, height - peakHeight, barWidth, 2);
            ctx.shadowBlur = 0;
          }
        }
      }
    }

    // Center line (for mirrored mode)
    if (this.mirrored) {
      ctx.strokeStyle = `rgba(255, 255, 255, ${0.02 + bands.bass * 0.04})`;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, centerY);
      ctx.lineTo(width, centerY);
      ctx.stroke();
    }
  }
}

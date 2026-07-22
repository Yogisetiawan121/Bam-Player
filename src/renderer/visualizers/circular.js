/* ============================================================
   NeonWave Player - Circular Visualizer
   Radial frequency bars that pulse from center outward.
   ============================================================ */

class CircularVisualizer extends BaseVisualizer {
  constructor(canvasId) {
    super(canvasId);
    this.name = 'circular';

    // Number of radial bars
    this.barCount = 72;

    // Smooth values
    this.smoothBars = new Float32Array(this.barCount);
    this.peakValues = new Float32Array(this.barCount);

    // Rotation
    this.rotation = 0;
    this.rotationSpeed = 0.003;

    // Rings
    this.ringCount = 4;
    this.ringValues = new Float32Array(this.ringCount);

    // Center glow
    this.centerGlow = 0;

    // Color
    this.hueOffset = 0;

    // Background stars
    this.stars = [];
    for (let i = 0; i < 80; i++) {
      this.stars.push({
        angle: Math.random() * Math.PI * 2,
        radius: 0.1 + Math.random() * 0.9,
        size: 0.5 + Math.random() * 1.5,
        speed: 0.0002 + Math.random() * 0.0006,
        twinkle: Math.random() * Math.PI * 2
      });
    }
  }

  onResize(w, h) {}

  draw(ctx, width, height, freqData, timeData, audioEngine) {
    const isPlaying = audioEngine.isPlaying;
    const bands = audioEngine.getBands();

    // Background
    ctx.fillStyle = 'rgba(10, 10, 15, 0.2)';
    ctx.fillRect(0, 0, width, height);

    // Center of canvas
    const cx = width / 2;
    const cy = height / 2;
    const maxRadius = Math.min(cx, cy) * 0.85;

    // Update rotation
    this.rotation += this.rotationSpeed * (1 + bands.bass * 0.5);
    this.hueOffset += 0.3 + bands.bass * 2;

    // Draw background stars
    for (const star of this.stars) {
      star.twinkle += 0.02;
      const alpha = 0.15 + Math.sin(star.twinkle) * 0.1;
      const r = star.radius * maxRadius;
      const a = star.angle + this._elapsed * star.speed;
      const x = cx + Math.cos(a) * r;
      const y = cy + Math.sin(a) * r;

      ctx.fillStyle = `rgba(200, 200, 255, ${alpha})`;
      ctx.beginPath();
      ctx.arc(x, y, star.size, 0, Math.PI * 2);
      ctx.fill();
    }

    // Map frequency data to bars (circular distribution)
    const freqStep = freqData.length / this.barCount;

    for (let i = 0; i < this.barCount; i++) {
      const startIdx = Math.floor(i * freqStep);
      const endIdx = Math.floor((i + 1) * freqStep);
      let sum = 0;
      for (let j = startIdx; j < endIdx; j++) {
        sum += freqData[j] || 0;
      }
      const avg = sum / (endIdx - startIdx || 1);
      const target = isPlaying ? avg / 255 : 0;

      this.smoothBars[i] += (target - this.smoothBars[i]) * 0.3;

      if (target > this.peakValues[i]) {
        this.peakValues[i] = target;
      } else {
        this.peakValues[i] -= 0.008;
        if (this.peakValues[i] < 0) this.peakValues[i] = 0;
      }
    }

    // Calculate ring values (smoothed averages of frequency ranges)
    for (let ring = 0; ring < this.ringCount; ring++) {
      const ringStart = Math.floor((ring / this.ringCount) * freqData.length);
      const ringEnd = Math.floor(((ring + 1) / this.ringCount) * freqData.length);
      let sum = 0;
      for (let j = ringStart; j < ringEnd; j++) {
        sum += freqData[j] || 0;
      }
      const target = sum / (ringEnd - ringStart || 1) / 255;
      this.ringValues[ring] += (target - this.ringValues[ring]) * 0.25;
    }

    // Draw outer glow rings
    for (let ring = 0; ring < this.ringCount; ring++) {
      const ringRadius = maxRadius * (0.3 + ring * 0.18);
      const ringAlpha = 0.05 + this.ringValues[ring] * 0.15;
      const ringHue = (this.hueOffset + ring * 30) % 360;

      ctx.strokeStyle = `hsla(${ringHue}, 100%, 60%, ${ringAlpha})`;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(cx, cy, ringRadius, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Draw the radial bars
    const innerRadius = maxRadius * 0.2;
    const outerRadius = maxRadius * 0.95;
    const barWidth = (2 * Math.PI * innerRadius) / this.barCount * 0.8;

    for (let i = 0; i < this.barCount; i++) {
      const angle = (i / this.barCount) * Math.PI * 2 + this.rotation;
      const barHeight = this.smoothBars[i] * (outerRadius - innerRadius);
      const peakBar = this.peakValues[i] * (outerRadius - innerRadius);

      const startR = innerRadius;
      const barValue = this.smoothBars[i];

      if (barHeight > 1) {
        // Color based on angle and height
        const hue = (this.hueOffset + i * (360 / this.barCount)) % 360;
        const saturation = 80 + barValue * 20;
        const lightness = 40 + barValue * 30;

        // Calculate bar corners
        const x1 = cx + Math.cos(angle) * startR;
        const y1 = cy + Math.sin(angle) * startR;
        const x2 = cx + Math.cos(angle) * (startR + barHeight);
        const y2 = cy + Math.sin(angle) * (startR + barHeight);

        // Wider at ends for perspective
        const endWidth = barWidth * (1 + barValue * 2);
        const perpAngle = angle + Math.PI / 2;

        // Draw bar as a rotated rectangle (or just a line)
        ctx.strokeStyle = `hsla(${hue}, ${saturation}%, ${lightness}%, ${0.6 + barValue * 0.4})`;
        ctx.lineWidth = Math.max(1.5, barWidth * (0.5 + barValue) * (startR + barHeight / 2) / innerRadius);
        ctx.shadowColor = `hsla(${hue}, 100%, 60%, ${0.2 + barValue * 0.3})`;
        ctx.shadowBlur = 6 + barValue * 10;

        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();

        // End cap (brighter dot at the tip)
        if (barValue > 0.05) {
          ctx.shadowBlur = 0;
          ctx.fillStyle = `hsla(${hue}, 100%, 80%, ${0.5 + barValue * 0.5})`;
          ctx.beginPath();
          ctx.arc(x2, y2, Math.max(2, barWidth * barValue * 0.8), 0, Math.PI * 2);
          ctx.fill();
        }

        // Peak dot
        if (this.peakValues[i] > 0.05) {
          const px = cx + Math.cos(angle) * (startR + peakBar);
          const py = cy + Math.sin(angle) * (startR + peakBar);
          ctx.shadowBlur = 0;
          ctx.fillStyle = `hsla(${hue}, 100%, 90%, 0.8)`;
          ctx.beginPath();
          ctx.arc(px, py, 2.5, 0, Math.PI * 2);
          ctx.fill();
        }

        ctx.shadowBlur = 0;
      }
    }

    // Center circle (pulsing glow)
    const centerRadius = maxRadius * 0.15 * (0.8 + bands.bass * 0.4);
    this.centerGlow += (bands.bass - this.centerGlow) * 0.25;

    // Center gradient
    const gradient = ctx.createRadialGradient(
      cx, cy, 0,
      cx, cy, centerRadius * 2
    );
    gradient.addColorStop(0, `hsla(${this.hueOffset % 360}, 100%, 80%, ${0.4 + this.centerGlow * 0.4})`);
    gradient.addColorStop(0.3, `hsla(${(this.hueOffset + 60) % 360}, 100%, 60%, ${0.2 + this.centerGlow * 0.3})`);
    gradient.addColorStop(0.7, `hsla(${(this.hueOffset + 120) % 360}, 100%, 40%, ${0.05 + this.centerGlow * 0.1})`);
    gradient.addColorStop(1, 'rgba(10, 10, 15, 0)');

    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(cx, cy, centerRadius * 2, 0, Math.PI * 2);
    ctx.fill();

    // Center dot
    ctx.fillStyle = `rgba(255, 255, 255, ${0.6 + this.centerGlow * 0.4})`;
    ctx.shadowColor = `rgba(0, 240, 255, ${0.3 + this.centerGlow * 0.5})`;
    ctx.shadowBlur = 20 + this.centerGlow * 20;
    ctx.beginPath();
    ctx.arc(cx, cy, centerRadius * 0.3, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;
  }
}

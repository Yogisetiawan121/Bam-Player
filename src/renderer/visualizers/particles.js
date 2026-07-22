/* ============================================================
   NeonWave Player - Particle System Visualizer
   Hundreds of dancing particles reacting to audio.
   ============================================================ */

class ParticleVisualizer extends BaseVisualizer {
  constructor(canvasId) {
    super(canvasId);
    this.name = 'particles';

    // Particle count
    this.particleCount = 250;
    this.particles = [];

    // Attractor/repulsor points
    this.attractors = [];

    // Connection distance
    this.maxConnectionDist = 120;

    // Color palette
    this.palette = [
      { r: 0, g: 240, b: 255 },    // Cyan
      { r: 255, g: 0, b: 170 },    // Magenta
      { r: 57, g: 255, b: 20 },    // Lime
      { r: 168, g: 85, b: 247 },   // Purple
      { r: 255, g: 200, b: 0 }     // Gold
    ];

    this._initParticles();
  }

  _initParticles() {
    this.particles = [];
    for (let i = 0; i < this.particleCount; i++) {
      this.particles.push(this._createParticle());
    }
  }

  _createParticle() {
    return {
      x: Math.random(),
      y: Math.random(),
      vx: (Math.random() - 0.5) * 0.002,
      vy: (Math.random() - 0.5) * 0.002,
      size: 1 + Math.random() * 3,
      targetSize: 1 + Math.random() * 3,
      alpha: 0.3 + Math.random() * 0.7,
      targetAlpha: 0.3 + Math.random() * 0.7,
      hue: Math.random() * 360,
      hueSpeed: 0.1 + Math.random() * 0.3,
      life: 1,
      pulsePhase: Math.random() * Math.PI * 2,
      trail: [],
      maxTrail: 5,
      // Random attractor affinity
      attractorAffinity: Math.floor(Math.random() * 3) // 0, 1, or 2
    };
  }

  _resetParticle(p) {
    const margin = 0.1;
    p.x = Math.random();
    p.y = Math.random();
    p.vx = (Math.random() - 0.5) * 0.004;
    p.vy = (Math.random() - 0.5) * 0.004;
    p.life = 1;
    p.trail = [];
  }

  onResize(w, h) {
    // Reposition particles to new dimensions
    // Nothing needed as we use normalized coordinates
  }

  draw(ctx, width, height, freqData, timeData, audioEngine) {
    const isPlaying = audioEngine.isPlaying;
    const bands = audioEngine.getBands();

    // Semi-transparent background for trail effect
    ctx.fillStyle = 'rgba(10, 10, 15, 0.15)';
    ctx.fillRect(0, 0, width, height);

    // Update attractors based on audio bands
    this.attractors = [
      { x: 0.5, y: 0.5, strength: 0.0001 * (1 + bands.bass * 3) },
      { x: 0.3 + bands.mid * 0.2, y: 0.3 + bands.treble * 0.2, strength: 0.00008 * (1 + bands.mid * 2) },
      { x: 0.7 - bands.bass * 0.2, y: 0.7 - bands.mid * 0.2, strength: 0.00006 * (1 + bands.treble * 2) }
    ];

    // Update particles
    for (let i = 0; i < this.particles.length; i++) {
      const p = this.particles[i];

      // Decay life when not playing
      if (!isPlaying) {
        p.life -= 0.002;
        if (p.life <= 0) {
          this._resetParticle(p);
        }
      } else {
        p.life = Math.min(1, p.life + 0.005);
      }

      // Apply attractor forces
      for (const attr of this.attractors) {
        const dx = attr.x - p.x;
        const dy = attr.y - p.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 0.001;
        const force = attr.strength / dist;

        p.vx += (dx / dist) * force * p.life;
        p.vy += (dy / dist) * force * p.life;
      }

      // Audio-reactive forces
      if (isPlaying) {
        // Bass burst (radial push from center)
        if (bands.bass > 0.3) {
          const cx = 0.5;
          const cy = 0.5;
          const dx = p.x - cx;
          const dy = p.y - cy;
          const dist = Math.sqrt(dx * dx + dy * dy) || 0.001;
          const burstForce = bands.bass * 0.003;
          p.vx += (dx / dist) * burstForce;
          p.vy += (dy / dist) * burstForce;
        }

        // Mid swirl
        const swirlAngle = bands.mid * 0.2;
        const sx = p.vx * Math.cos(swirlAngle) - p.vy * Math.sin(swirlAngle);
        const sy = p.vx * Math.sin(swirlAngle) + p.vy * Math.cos(swirlAngle);
        p.vx += (sx - p.vx) * 0.1;
        p.vy += (sy - p.vy) * 0.1;
      }

      // Damping
      p.vx *= 0.98;
      p.vy *= 0.98;

      // Clamp velocity (higher limit = more responsive to bass hits)
      const speed = Math.sqrt(p.vx * p.vx + p.vy * p.vy);
      if (speed > 0.02) {
        p.vx = (p.vx / speed) * 0.02;
        p.vy = (p.vy / speed) * 0.02;
      }

      // Update position
      p.x += p.vx;
      p.y += p.vy;

      // Wrap around edges
      if (p.x < -0.1) p.x = 1.1;
      if (p.x > 1.1) p.x = -0.1;
      if (p.y < -0.1) p.y = 1.1;
      if (p.y > 1.1) p.y = -0.1;

      // Trail
      if (isPlaying) {
        p.trail.push({ x: p.x, y: p.y });
        if (p.trail.length > p.maxTrail) {
          p.trail.shift();
        }
      } else {
        p.trail = [];
      }

      // Size pulsing (faster response to bass hits)
      p.targetSize = 1 + bands.bass * 3 + bands.mid * 1.5;
      p.size += (p.targetSize - p.size) * 0.15;

      // Alpha based on speed and audio
      const spd = Math.sqrt(p.vx * p.vx + p.vy * p.vy);
      p.targetAlpha = Math.min(1, 0.2 + spd * 80 + bands.bass * 0.5 + bands.treble * 0.3);
      p.alpha += (p.targetAlpha - p.alpha) * 0.15;

      // Hue cycling
      p.hue += p.hueSpeed + bands.mid * 2;
      if (p.hue > 360) p.hue -= 360;
    }

    // Sort particles by alpha (draw brighter ones on top)
    const sorted = [...this.particles].sort((a, b) => b.alpha - a.alpha);

    // Draw connections between nearby particles
    ctx.lineWidth = 0.5;
    for (let i = 0; i < sorted.length; i++) {
      for (let j = i + 1; j < Math.min(i + 15, sorted.length); j++) {
        const a = sorted[i];
        const b = sorted[j];
        const dx = (a.x - b.x) * width;
        const dy = (a.y - b.y) * height;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < this.maxConnectionDist) {
          const alpha = (1 - dist / this.maxConnectionDist) * 0.15 * a.alpha * b.alpha * (0.3 + bands.mid);
          if (alpha > 0.01) {
            const hue = (a.hue + b.hue) / 2;
            ctx.strokeStyle = `hsla(${hue}, 100%, 60%, ${alpha})`;
            ctx.beginPath();
            ctx.moveTo(a.x * width, a.y * height);
            ctx.lineTo(b.x * width, b.y * height);
            ctx.stroke();
          }
        }
      }
    }

    // Draw particles
    for (const p of sorted) {
      const screenX = p.x * width;
      const screenY = p.y * height;
      const alpha = p.alpha * p.life;

      if (alpha < 0.01) continue;

      // Glow shadow
      ctx.shadowColor = `hsla(${p.hue}, 100%, 60%, ${alpha * 0.4})`;
      ctx.shadowBlur = 8 + p.size * 2;

      // Main particle
      ctx.fillStyle = `hsla(${p.hue}, 100%, 70%, ${alpha})`;
      ctx.beginPath();
      ctx.arc(screenX, screenY, p.size, 0, Math.PI * 2);
      ctx.fill();

      // Bright center
      ctx.shadowBlur = 0;
      ctx.fillStyle = `hsla(${p.hue}, 80%, 90%, ${alpha * 0.6})`;
      ctx.beginPath();
      ctx.arc(screenX, screenY, p.size * 0.4, 0, Math.PI * 2);
      ctx.fill();

      // Draw trail
      if (p.trail.length > 1) {
        ctx.lineWidth = p.size * 0.5;
        for (let t = 1; t < p.trail.length; t++) {
          const trailAlpha = (t / p.trail.length) * alpha * 0.3;
          ctx.strokeStyle = `hsla(${p.hue}, 100%, 60%, ${trailAlpha})`;
          ctx.beginPath();
          ctx.moveTo(p.trail[t - 1].x * width, p.trail[t - 1].y * height);
          ctx.lineTo(p.trail[t].x * width, p.trail[t].y * height);
          ctx.stroke();
        }
      }
    }

    ctx.shadowBlur = 0;

    // Draw bass pulse ring
    if (bands.bass > 0.1) {
      const ringRadius = Math.min(width, height) * 0.4 * bands.bass;
      const ringAlpha = bands.bass * 0.15;

      ctx.strokeStyle = `rgba(0, 240, 255, ${ringAlpha})`;
      ctx.lineWidth = 1 + bands.bass * 3;
      ctx.shadowColor = `rgba(0, 240, 255, ${ringAlpha * 0.5})`;
      ctx.shadowBlur = 10;
      ctx.beginPath();
      ctx.arc(width / 2, height / 2, ringRadius, 0, Math.PI * 2);
      ctx.stroke();
      ctx.shadowBlur = 0;
    }
  }
}

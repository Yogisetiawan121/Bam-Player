# NeonWave Player 🎵

A stunning modern music player inspired by Winamp/Milkdrop, built with **Electron**, **Web Audio API**, and **Canvas 2D**. Dark neon aesthetics with four real-time audio visualizations.

## Features

### 🎶 Music Playback
- Play, pause, stop, previous, next controls
- Volume slider with mute toggle
- Progress bar with seek functionality
- Support for MP3, WAV, FLAC, OGG, M4A, AAC
- Drag-and-drop file loading or file picker
- Playlist with add, remove, reorder, shuffle, repeat

### ✨ Audio Visualizations
1. **Spectrum Analyzer** — 64-band frequency bars with smooth falling peak effect
2. **Waveform/Oscilloscope** — Classic line waveform with grid overlay and VU meters
3. **Circular Analyzer** — Radial frequency bars pulsing from center with rotating glow
4. **Particle System** — 250+ particles dancing to bass/mid/treble with connection lines

Switch with buttons or keyboard shortcuts (1-4).

### 🎨 UI/UX
- Dark theme (#0a0a0f) with neon cyan, magenta, and lime accents
- Frameless Electron window with custom title bar
- Collapsible playlist sidebar
- Fullscreen visualization mode (double-click or F11)
- Smooth transitions and micro-animations

### 🕹️ Winamp Nostalgia
- **Classic Mode** toggle that switches to retro Winamp 2.x aesthetic
- Keyboard shortcuts: Space (play/pause), Arrows (seek/volume), Ctrl+O (open), Ctrl+L (playlist)
- "Falling peak" spectrum effect, VU meters, playlist with track numbers

### 💾 Persistence
- Playlist state saved between sessions
- Remembers last played track
- Stores preferences (volume, visualizer, theme)

## Getting Started

### Prerequisites
- Node.js 18+ (LTS recommended)
- npm or yarn

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd neonwave-player

# Install dependencies
npm install

# Start the app
npm start

# Dev mode (with DevTools open)
npm run dev
```

## Controls

### Playback
| Action | Control |
|--------|---------|
| Play/Pause | Space or Click play button |
| Stop | Escape |
| Previous | Click ◀ or P |
| Next | Click ▶ or N |
| Seek | Click/drag on seek bar |
| Volume | Drag volume slider or Up/Down arrows |

### Visualizers
| Key | Visualizer |
|-----|-----------|
| 1 | Spectrum Analyzer |
| 2 | Waveform |
| 3 | Circular |
| 4 | Particles |

### Window
| Action | Control |
|--------|---------|
| Fullscreen | F11 or double-click visualization |
| Toggle Playlist | Ctrl+L |
| Open Files | Ctrl+O |
| Classic Mode | Click cassette icon in title bar |

## Project Structure

```
/src
  /main
    main.js        # Electron main process
    preload.js     # Secure IPC bridge
  /renderer
    index.html     # Main HTML shell
    app.js         # Application orchestrator
    /components
      titlebar.js  # Custom frameless title bar
      controls.js  # Playback controls UI
      playlist.js  # Playlist panel
    /visualizers
      base.js      # Base visualizer class
      spectrum.js  # Spectrum analyzer
      waveform.js  # Waveform oscilloscope
      circular.js  # Circular radial analyzer
      particles.js # Particle system
    /styles
      main.css     # Dark neon theme
      animations.css
      winamp.css   # Classic Winamp mode
    /utils
      audio.js     # Web Audio API engine
      store.js     # Data persistence
      keybindings.js # Keyboard shortcuts
```

## Tech Stack

- **Electron** — Desktop app wrapper
- **Web Audio API** — Audio playback and real-time analysis (AnalyserNode)
- **Canvas 2D** — All visualizations rendered at 60fps
- **Vanilla JavaScript** — No frameworks, lightweight and performant

## License

MIT License
